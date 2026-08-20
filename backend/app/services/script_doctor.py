from app.models.project import Project
from app.models.script import Scene
from app.providers.llm.registry import get_llm_provider
from pydantic import ValidationError
from fastapi import HTTPException
import json
import uuid

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
        self.llm_provider = get_llm_provider()

    async def standardize_screenplay(self, project: Project) -> dict:
        prompt = f"""
You are an expert Script Doctor. The director has provided raw source material (rough script or story treatment).
Your sole task is to STANDARDIZE this material into a professional screenplay format.

RULES:
- Normalize sluglines, INT/EXT formatting, location, and time of day.
- Standardize action blocks and dialogue formatting.
- Correct grammar, spelling, and improve screenplay readability.
- Maintain character name consistency.
- DO NOT invent new plot events or characters.
- DO NOT change the story structure unnecessarily or alter dialogue intent.
- DO NOT add cinematic directions (no camera angles, lenses, movement, lighting, or color grading).
- Preserve the exact sequence of events the director provided.

Project Name: {project.name}
Genre: {project.genre}
Tone: {project.tone}

Director's Raw Material:
{project.source_material or project.story_idea}

Make sure every scene gets a unique string 'id' like 'scene_xyz'.
Return a structured JSON script.
"""
        result = await self.llm_provider.generate_json(prompt, SCRIPT_SCHEMA)
        
        # Ensure all scenes have IDs and sequential numbers
        validated_scenes = []
        for i, scene_raw in enumerate(result.get("scenes", [])):
            if "id" not in scene_raw or not scene_raw["id"]:
                scene_raw["id"] = f"scene_{uuid.uuid4().hex[:8]}"
            if "scene_number" not in scene_raw:
                scene_raw["scene_number"] = i + 1
            
            try:
                # Strictly validate through Pydantic model
                valid_scene = Scene.model_validate(scene_raw)
                validated_scenes.append(valid_scene.model_dump())
            except ValidationError as e:
                raise HTTPException(status_code=422, detail=f"LLM generated invalid scene data: {str(e)}")
        
        result["scenes"] = validated_scenes
        return result

    async def propose_scene_standardization(self, project: Project, base_version: int, target_scene: dict, instructions: str) -> dict:
        prompt = f"""
You are an expert Script Doctor. The director wants to standardize or fix a specific scene from a professional screenplay (Base Version: {base_version}).
Your task is to apply the requested formatting or standardization fixes.

RULES:
- Apply the requested fix (e.g., standardizing dialogue, formatting action blocks, fixing grammar).
- Preserve all story events, emotional intent, and character identities.
- DO NOT invent new plot events, new characters, or delete essential events.
- DO NOT add cinematic directions (no camera angles, lenses, lighting, etc).
- Return ONLY the proposed standardized scene in JSON format.

Current Scene:
{json.dumps(target_scene, indent=2)}

Director's Fix Instruction:
{instructions}
"""
        result = await self.llm_provider.generate_json(prompt, SINGLE_SCENE_SCHEMA)
        
        # Identity Preservation
        result["id"] = target_scene["id"]
        result["scene_number"] = target_scene.get("scene_number", 0)
        
        try:
            valid_scene = Scene.model_validate(result)
            return valid_scene.model_dump()
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=f"LLM generated invalid scene data: {str(e)}")
