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

        # Production Intelligence - Cinematography
        if "scenes" in schema.get("properties", {}) and "visual_goal" in schema.get("properties", {}).get("scenes", {}).get("items", {}).get("properties", {}):
            return {
                "scenes": [
                    {
                        "scene_id": "scene_1",
                        "visual_goal": "Establish isolation",
                        "overall_mood": "Lonely",
                        "color_plan": {
                            "palette": [
                                {"hex": "#0000FF", "role": "Key Light", "description": "Cold blue"}
                            ],
                            "temperature_kelvin": 6500,
                            "contrast": 1.5,
                            "saturation": 0.8,
                            "mood": "Cold",
                            "film_look": "Kodak Vision3",
                            "lut": {
                                "name": "SciFi Blue",
                                "type": "Creative",
                                "reason": "Enhance coldness"
                            }
                        },
                        "shots": [
                            {
                                "shot_id": "scene_1_shot_1",
                                "purpose": "Show isolation",
                                "story_beat": "Establishes isolation",
                                "shot_size": "Wide",
                                "camera": {
                                    "angle": "High",
                                    "focal_length_mm": 24,
                                    "lens_type": "Spherical",
                                    "movement": "Slow push in"
                                },
                                "blocking": {
                                    "subject_position": "Center",
                                    "gaze_direction": "Down",
                                    "character_interaction": "None"
                                },
                                "composition": {
                                    "rule_of_thirds": True,
                                    "symmetry": True
                                },
                                "lighting": {
                                    "setup": "Top lit",
                                    "direction": "Overhead",
                                    "intensity": "Low"
                                },
                                "subject": "Astronaut at console",
                                "emotion": "Lonely"
                            }
                        ]
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
