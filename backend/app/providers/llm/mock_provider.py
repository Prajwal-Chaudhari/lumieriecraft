from app.providers.llm.base import LLMProvider
import asyncio

class MockLLMProvider(LLMProvider):
    async def generate_json(self, prompt: str, schema: dict) -> dict:
        await asyncio.sleep(1) # simulate latency
        
        # If schema asks for a single scene (no 'title' or 'scenes' array)
        if "title" not in schema.get("properties", {}):
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

        # Otherwise, full script mock
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
