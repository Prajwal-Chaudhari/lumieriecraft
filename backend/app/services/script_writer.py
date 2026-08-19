from app.models.project import Project
from app.models.script import Scene
from app.providers.llm.registry import get_llm_provider
from pydantic import ValidationError
from fastapi import HTTPException
import json
import uuid

SINGLE_SCENE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "scene_number": {"type": "integer"},
        "heading": {"type": "string"},
        "location": {"type": "string"},
        "time_of_day": {"type": "string"},
        "description": {"type": "string"},
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": ["string", "null"]}
                },
                "required": ["name"]
            }
        },
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"]
            }
        },
        "dialogue": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "character": {"type": "string"},
                    "parenthetical": {"type": ["string", "null"]},
                    "text": {"type": "string"}
                },
                "required": ["character", "text"]
            }
        },
        "metadata": {"type": "object"}
    },
    "required": ["id", "scene_number", "heading", "location", "time_of_day", "description", "characters", "actions", "dialogue", "metadata"]
}

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "scenes": {
            "type": "array",
            "items": SINGLE_SCENE_SCHEMA
        }
    },
    "required": ["title", "scenes"]
}

class ScriptWriterService:
    def __init__(self):
        self.llm_provider = get_llm_provider()

    async def generate_script(self, project: Project) -> dict:
        prompt = f"""
Write a short screenplay for the following project:
Name: {project.name}
Idea: {project.story_idea}
Genre: {project.genre}
Duration: {project.duration}
Tone: {project.tone}
Visual Style: {project.visual_style}

Make sure every scene gets a unique string 'id' like 'scene_xyz'.
"""
        result = await self.llm_provider.generate_json(prompt, SCRIPT_SCHEMA)
        # Ensure all scenes have IDs just in case the LLM misses it
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
                # Log error or raise safe exception
                raise HTTPException(status_code=422, detail=f"LLM generated invalid scene data: {str(e)}")
        
        result["scenes"] = validated_scenes
        return result

    async def regenerate_scene(self, project: Project, scene_data: dict, instructions: str = None) -> dict:
        prompt = f"""
Rewrite the following scene for the project '{project.name}'.
Project Idea: {project.story_idea}
Genre: {project.genre}
Tone: {project.tone}
Visual Style: {project.visual_style}

Here is the current scene (Scene {scene_data.get('scene_number')}):
{json.dumps(scene_data, indent=2)}
"""
        if instructions:
            prompt += f"\n\nUser Instructions for rewriting this scene:\n{instructions}\n\nPlease apply these instructions and return the fully rewritten scene."
        else:
            prompt += f"\n\nPlease improve and rewrite this scene to fit the project better, returning the fully rewritten scene."

        result = await self.llm_provider.generate_json(prompt, SINGLE_SCENE_SCHEMA)
        
        # Ensure we keep the original ID and scene_number (Identity Preservation)
        result["id"] = scene_data["id"]
        result["scene_number"] = scene_data.get("scene_number", 0)
        
        try:
            # Strictly validate through Pydantic model
            valid_scene = Scene.model_validate(result)
            return valid_scene.model_dump()
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=f"LLM generated invalid scene data: {str(e)}")
