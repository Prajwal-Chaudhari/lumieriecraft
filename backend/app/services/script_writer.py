from app.models.project import Project
from app.providers.llm.registry import get_llm_provider
import json
import uuid

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "scenes": {
            "type": "array",
            "items": {
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
        for i, scene in enumerate(result.get("scenes", [])):
            if "id" not in scene or not scene["id"]:
                scene["id"] = f"scene_{uuid.uuid4().hex[:8]}"
            if "scene_number" not in scene:
                scene["scene_number"] = i + 1
        return result
