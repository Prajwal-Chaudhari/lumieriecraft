import re
import uuid
import json
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.project import Project
from app.models.script import Scene
from app.providers.llm.registry import get_llm_provider

SINGLE_SCENE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "id": {"type": "STRING"},
        "scene_number": {"type": "INTEGER"},
        "heading": {"type": "STRING"},
        "location": {"type": "STRING"},
        "time_of_day": {"type": "STRING"},
        "description": {"type": "STRING"},
        "characters": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING", "nullable": True}
                },
                "required": ["name"]
            }
        },
        "actions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"text": {"type": "STRING"}},
                "required": ["text"]
            }
        },
        "dialogue": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "character": {"type": "STRING"},
                    "parenthetical": {"type": "STRING", "nullable": True},
                    "text": {"type": "STRING"}
                },
                "required": ["character", "text"]
            }
        },
        "metadata": {"type": "OBJECT", "nullable": True}
    },
    "required": ["id", "scene_number", "heading", "location", "time_of_day", "description", "characters", "actions", "dialogue"]
}

SCRIPT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "scenes": {
            "type": "ARRAY",
            "items": SINGLE_SCENE_SCHEMA
        }
    },
    "required": ["title", "scenes"]
}

class ScriptDoctorService:
    def __init__(self):
        self.llm_provider = get_llm_provider(purpose="SCRIPT_WRITER")

    def _split_by_regex(self, text: str) -> list[str]:
        # Split using lookahead for INT., EXT., INT./EXT. (case-insensitive)
        # This keeps the heading attached to its content and preserves 100% of text.
        parts = re.split(r"(?im)(?=^[ \t]*(?:INT\.|EXT\.|INT\./EXT\.))", text)
        return [p for p in parts if p]

    async def _segment_with_llm(self, text: str) -> list[str]:
        # Chunk text keeping paragraph delimiters to avoid exceeding context
        parts = re.split(r'(\n\n+)', text)
        chunks = []
        curr = ""
        for i in range(0, len(parts), 2):
            p = parts[i]
            delim = parts[i+1] if i+1 < len(parts) else ""
            if len(curr) + len(p) + len(delim) > 4000 and curr:
                chunks.append(curr)
                curr = p + delim
            else:
                curr += p + delim
        if curr:
            chunks.append(curr)
            
        all_scenes = []
        
        for chunk in chunks:
            prompt = f"""
You are a screenplay formatting expert. Analyze the following text and find scene boundaries (where location or time changes).
For each boundary, provide an exact, verbatim snippet of text (at least 10 words) that occurs IMMEDIATELY BEFORE the boundary.
The snippet MUST be an exact character-for-character substring of the text. Do not guess or modify words.

Text:
{chunk}
"""
            schema = {
                "type": "OBJECT",
                "properties": {
                    "boundaries": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "exact_text_before_boundary": {"type": "STRING"}
                            },
                            "required": ["exact_text_before_boundary"]
                        }
                    }
                },
                "required": ["boundaries"]
            }
            
            try:
                result = await self.llm_provider.generate_json(prompt, schema)
                boundaries = result.get("boundaries", [])
            except Exception:
                boundaries = []
                
            current_text = chunk
            chunk_scenes = []
            for b in boundaries:
                anchor = b.get("exact_text_before_boundary", "")
                if not anchor or len(anchor) < 10:
                    continue
                
                # Verify exact and unique occurrence in remaining text
                if current_text.count(anchor) == 1:
                    idx = current_text.find(anchor) + len(anchor)
                    scene_text = current_text[:idx]
                    chunk_scenes.append(scene_text)
                    current_text = current_text[idx:]
            
            if current_text:
                chunk_scenes.append(current_text)
                
            all_scenes.extend(chunk_scenes)
            
        return all_scenes

    async def standardize_screenplay(self, project: Project) -> dict:
        source_text = project.source_material or project.story_idea or ""
        if not source_text.strip():
            return {"title": project.name, "scenes": []}

        # 1. Deterministic Scene Detection
        raw_scenes = self._split_by_regex(source_text)
        
        # 2. Fallback LLM Segmentation if no explicit headings are found
        # (A single chunk without headings means len([s]) is 1)
        valid_raw_scenes = [s for s in raw_scenes if s.strip()]
        if len(valid_raw_scenes) <= 1:
            raw_scenes = await self._segment_with_llm(source_text)
            valid_raw_scenes = [s for s in raw_scenes if s.strip()]
            
        # Verify concatenation reproduces exact source text
        reconstructed = "".join(raw_scenes)
        if reconstructed != source_text:
            raise HTTPException(status_code=500, detail="Fatal error: Scene segmentation lost source text.")
            
        source_scene_count = len(valid_raw_scenes)
        
        # 3. Sequential Scene Processing
        validated_scenes = []
        for i, raw_scene_text in enumerate(raw_scenes):
            if not raw_scene_text.strip():
                continue
                
            prompt = f"""
You are an expert Script Doctor. STANDARDIZE the following raw scene into a professional screenplay format.

RULES:
- Normalize sluglines, INT/EXT formatting, location, and time of day.
- Standardize action blocks and dialogue formatting.
- Correct grammar and spelling.
- DO NOT invent new plot events or characters.
- DO NOT add cinematic directions.
- Preserve the exact sequence of events.
- If the scene has a valid heading, normalize it (e.g., capitalize).
- If the scene lacks an INT./EXT. heading, DO NOT invent one unless you are highly confident.
- Return structured JSON for this single scene.

Raw Scene Text:
{raw_scene_text}
"""
            try:
                result = await self.llm_provider.generate_json(prompt, SINGLE_SCENE_SCHEMA)
                
                # Format normalization in Python
                if "heading" in result and result["heading"]:
                    h = result["heading"].upper().strip()
                    if h.startswith("INT ") or h.startswith("INT-"):
                        h = "INT. " + h[4:].strip()
                    elif h.startswith("EXT ") or h.startswith("EXT-"):
                        h = "EXT. " + h[4:].strip()
                    result["heading"] = h
                    
                if "characters" in result:
                    for c in result["characters"]:
                        if "name" in c and c["name"]:
                            c["name"] = c["name"].upper()
                            
                if "dialogue" in result:
                    for d in result["dialogue"]:
                        if "character" in d and d["character"]:
                            d["character"] = d["character"].upper()
                            
                # Ensure actions list of objects
                if "actions" in result and isinstance(result["actions"], list):
                    sanitized_actions = []
                    for action in result["actions"]:
                        if isinstance(action, str):
                            sanitized_actions.append({"text": action})
                        else:
                            sanitized_actions.append(action)
                    result["actions"] = sanitized_actions
                            
                result["id"] = f"scene_{uuid.uuid4().hex[:8]}"
                result["scene_number"] = len(validated_scenes) + 1
                
                if "metadata" not in result or not isinstance(result["metadata"], dict):
                    result["metadata"] = {}
                result["metadata"]["source_scene_text"] = raw_scene_text
                
                valid_scene = Scene.model_validate(result)
                validated_scenes.append(valid_scene.model_dump())
            except Exception as e:
                # Failed scenes MUST NOT become dummy successful scenes.
                raise HTTPException(
                    status_code=422, 
                    detail=f"Failed to process Scene {len(validated_scenes)+1}: {str(e)}\nRaw Text snippet: {raw_scene_text[:100]}..."
                )

        if len(validated_scenes) != source_scene_count:
            raise HTTPException(status_code=500, detail="Mismatch between source scene count and successfully processed scene count.")
            
        return {
            "title": project.name,
            "scenes": validated_scenes
        }

    async def propose_scene_standardization(self, project: Project, base_version: int, target_scene: dict, instructions: str) -> dict:
        prompt = f"""
You are an expert Script Doctor. The director wants to standardize or fix a specific scene from a professional screenplay (Base Version: {base_version}).
Your task is to apply the requested formatting or standardization fixes.

RULES:
- Apply the requested fix.
- Preserve all story events, emotional intent, and character identities.
- DO NOT invent new plot events, new characters, or delete essential events.
- DO NOT add cinematic directions.
- Return ONLY the proposed standardized scene in JSON format.

Current Scene:
{json.dumps(target_scene, indent=2)}

Director's Fix Instruction:
{instructions}
"""
        result = await self.llm_provider.generate_json(prompt, SINGLE_SCENE_SCHEMA)
        
        result["id"] = target_scene["id"]
        result["scene_number"] = target_scene.get("scene_number", 0)
        
        if "actions" in result and isinstance(result["actions"], list):
            sanitized_actions = []
            for action in result["actions"]:
                if isinstance(action, str):
                    sanitized_actions.append({"text": action})
                else:
                    sanitized_actions.append(action)
            result["actions"] = sanitized_actions
        
        try:
            valid_scene = Scene.model_validate(result)
            return valid_scene.model_dump()
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=f"LLM generated invalid scene data: {str(e)}")
