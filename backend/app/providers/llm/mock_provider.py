from app.providers.llm.base import LLMProvider
import asyncio

class MockLLMProvider(LLMProvider):
    async def generate_json(self, prompt: str, schema: dict) -> dict:
        await asyncio.sleep(1) # simulate latency
        
        # If schema asks for a single scene (e.g. propose_scene_enhancement)
        if "heading" in schema.get("properties", {}) and "actions" in schema.get("properties", {}):
            return {
                "id": "scene_1",
                "scene_number": 1,
                "heading": "INT. SPACE STATION - NIGHT",
                "location": "SPACE STATION",
                "time_of_day": "NIGHT",
                "description": "Cold, blue emergency lights flicker. A console blips rhythmically.",
                "characters": [{"name": "ASTRONAUT", "description": "Tired, wearing a worn-out flight suit."}],
                "actions": [{"text": "The astronaut stares at a blinking incoming message light."}],
                "dialogue": [
                    {"character": "ASTRONAUT", "parenthetical": "whispering", "text": "Not again..."}
                ],
                "metadata": {}
            }

        # Production Intelligence - Global Bibles
        if "characters" in schema.get("properties", {}) and "locations" in schema.get("properties", {}):
            return {
                "characters": [
                    {
                        "name": "ASTRONAUT",
                        "appearance": "Tired",
                        "established_facts": ["Wears a flight suit"],
                        "proposed_facts": ["Has been alone for months"],
                        "source_scene_ids": ["scene_1"]
                    }
                ],
                "locations": [
                    {
                        "name": "SPACE STATION",
                        "description": "Cold, blue emergency lights",
                        "established_facts": ["Emergency lights flicker"],
                        "proposed_facts": ["Power is failing"],
                        "source_scene_ids": ["scene_1"]
                    }
                ]
            }

        # Production Intelligence - Scene Breakdown
        if "location" in schema.get("properties", {}) and "emotional_beat" in schema.get("properties", {}):
            return {
                "location": "SPACE STATION",
                "time_of_day": "NIGHT",
                "characters": ["ASTRONAUT"],
                "actions": ["Stares at blinking light"],
                "dialogue_summary": "Astronaut mutters to himself",
                "props": ["blinking light console"],
                "emotional_beat": "Despair and suspense",
                "narrative_purpose": "Establishes isolation"
            }

        # Production Intelligence - Cinematography
        if "shots" in schema.get("properties", {}):
            return {
                "shots": [
                    {
                        "shot_id": "shot_1",
                        "purpose": "Show isolation",
                        "story_beat": "Establishes isolation",
                        "shot_size": "Wide",
                        "camera_angle": "High",
                        "lens": "24mm",
                        "lighting": "Cold blue",
                        "camera_movement": "Slow push in",
                        "subject": "Astronaut at console",
                        "emotion": "Lonely"
                    }
                ]
            }

        # Script Mock
        return {
            "title": "The Last Light (Mock)",
            "scenes": [
                {
                    "id": "scene_1",
                    "scene_number": 1,
                    "heading": "INT. SPACE STATION - NIGHT",
                    "location": "SPACE STATION",
                    "time_of_day": "NIGHT",
                    "description": "Cold, blue emergency lights flicker. A console blips rhythmically.",
                    "characters": [{"name": "ASTRONAUT", "description": "Tired, wearing a worn-out flight suit."}],
                    "actions": [{"text": "The astronaut stares at a blinking incoming message light."}],
                    "dialogue": [
                        {"character": "ASTRONAUT", "parenthetical": "whispering", "text": "Not again..."}
                    ],
                    "metadata": {}
                }
            ]
        }
