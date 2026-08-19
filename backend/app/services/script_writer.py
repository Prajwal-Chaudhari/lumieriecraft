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

class ScriptWriterService:
    def __init__(self):
        self.llm_provider = get_llm_provider()

    async def analyze_script(self, project: Project) -> dict:
        prompt = f"""
You are a professional filmmaking assistant. The director has provided a rough script or story concept.
Your task is to analyze it, extract characters and locations, improve its structure into professional screenplay format, and return it as a structured JSON script.
DO NOT completely change the story or intent. ENHANCE it cinematically.

Project Name: {project.name}
Genre: {project.genre}
Tone: {project.tone}
Visual Style: {project.visual_style}

Director's Rough Script / Source Material:
{project.source_material or project.story_idea}

Make sure every scene gets a unique string 'id' like 'scene_xyz'.
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

    async def propose_scene_enhancement(self, project: Project, scene_data: dict, instruction: str) -> dict:
        prompt = f"""
You are a professional filmmaking assistant. The director wants to enhance a specific scene.
Preserve the core story, emotional intent, and character identities. ENHANCE the scene cinematically based on the instruction.

Project Genre: {project.genre}
Tone: {project.tone}

Current Scene:
{json.dumps(scene_data, indent=2)}

Director's Instruction:
{instruction}

Return ONLY the proposed enhanced scene matching the JSON schema.
"""
        result = await self.llm_provider.generate_json(prompt, SINGLE_SCENE_SCHEMA)
        
        # Identity Preservation
        result["id"] = scene_data["id"]
        result["scene_number"] = scene_data.get("scene_number", 0)
        
        try:
            valid_scene = Scene.model_validate(result)
            return valid_scene.model_dump()
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=f"LLM generated invalid scene data: {str(e)}")

