import json
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from app.models.production import CinematographyProposal, ProductionPlan, ShotBlueprint, ProductionStatus, SceneBreakdown
from app.models.script import Script, Scene
from app.schemas.cinematography import CinematographyPlanSchema, SceneVisualPlanSchema, ColorPlan, PaletteColor, LUTRecommendation, ShotBlueprintSchema
from app.providers.llm.registry import get_llm_provider

class CinematographerService:
    def __init__(self):
        self.get_llm = get_llm_provider

    async def propose_cinematography(self, project_id: str, script: Script, session: Session) -> CinematographyPlanSchema:
        provider = self.get_llm(purpose="CINEMATOGRAPHY")
        
        scenes_visual_plans = []
        
        for scene_dict in script.scenes:
            scene = Scene.model_validate(scene_dict)
            
            # Fetch corresponding production intelligence data
            scene_breakdown = session.exec(
                select(SceneBreakdown).where(
                    SceneBreakdown.script_id == script.id,
                    SceneBreakdown.scene_id == scene.id
                )
            ).first()
            
            prod_info = ""
            if scene_breakdown:
                prod_info += f"Location context: {scene_breakdown.location}\n"
                prod_info += f"Time of Day: {scene_breakdown.time_of_day}\n"
                prod_info += f"Story Beat: {scene_breakdown.story_beat}\n"
                prod_info += f"Emotional Beat: {scene_breakdown.emotional_beat}\n"
                prod_info += f"Narrative Purpose: {scene_breakdown.narrative_purpose}\n"
                prod_info += f"Props: {', '.join(scene_breakdown.props) if scene_breakdown.props else 'None'}\n"
                prod_info += f"Visual Context: {scene_breakdown.visual_context}\n"
                prod_info += f"Continuity Notes: {scene_breakdown.continuity_notes}\n"
                
            script_text = f"SCENE {scene.scene_number}: {scene.heading}\n"
            script_text += f"ID: {scene.id}\n"
            script_text += f"Description: {scene.description}\n"
            for action in scene.actions:
                script_text += f"Action: {action.text}\n"
            for dialogue in scene.dialogue:
                script_text += f"{dialogue.character}: {dialogue.text}\n"

            prompt = f"""You are a professional Cinematographer and Colorist.
Your task is to generate a strict, machine-readable Cinematography Plan for ONE scene of the approved screenplay.
DO NOT rewrite the screenplay. DO NOT invent characters, actions, locations, events, or dialogue that do not exist.
The screenplay remains the single source of truth. Your job is to decide HOW it is photographed and color-treated.
Each shot must correspond to an actual moment/action/beat supported by the scene.

Production Intelligence Data for this scene:
{prod_info}

Reasoning passes (execute these conceptually before outputting):
Pass A: Scene & Story Analysis. Understand the narrative and emotional beats of the scene.
Pass B: Shot Planning. Decide the number of shots. For each shot, define the purpose, story beat, size, camera, blocking, composition, lighting.
Pass C: Lighting & Color. Define the overall color plan for the scene (palette, temperature, contrast, saturation, mood, film look, LUT).

Color Plan constraints:
- palette: Must be exactly formatted hex codes like "#FFFFFF", role, and description. Provide a usable color direction.
- temperature_kelvin: integer between 1000 and 12000.
- contrast: float between 0.0 and 2.0 (1.0 is neutral).
- saturation: float between 0.0 and 2.0 (1.0 is neutral).
- mood: descriptive string of lighting/color mood.

Shot constraints:
- Every shot must have a unique ID within the scene.
- Explain WHY each shot is necessary using 'purpose' and 'story_beat'.

Script (Scene {scene.scene_number}):
{script_text}
"""
            # Define the exact JSON schema matching SceneVisualPlanSchema
            response_schema = {
                "type": "OBJECT",
                "properties": {
                    "scene_id": {"type": "STRING"},
                    "visual_goal": {"type": "STRING"},
                    "overall_mood": {"type": "STRING"},
                    "color_plan": {
                        "type": "OBJECT",
                        "properties": {
                            "palette": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "hex": {"type": "STRING"},
                                        "role": {"type": "STRING"},
                                        "description": {"type": "STRING", "nullable": True}
                                    },
                                    "required": ["hex", "role"]
                                }
                            },
                            "temperature_kelvin": {"type": "INTEGER", "nullable": True},
                            "contrast": {"type": "NUMBER", "nullable": True},
                            "saturation": {"type": "NUMBER", "nullable": True},
                            "mood": {"type": "STRING", "nullable": True},
                            "film_look": {"type": "STRING", "nullable": True},
                            "lut": {
                                "type": "OBJECT",
                                "nullable": True,
                                "properties": {
                                    "name": {"type": "STRING"},
                                    "type": {"type": "STRING"},
                                    "reason": {"type": "STRING"}
                                },
                                "required": ["name", "type", "reason"]
                            }
                        },
                        "required": ["palette"]
                    },
                    "shots": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "shot_id": {"type": "STRING"},
                                "purpose": {"type": "STRING"},
                                "story_beat": {"type": "STRING"},
                                "shot_size": {"type": "STRING", "nullable": True},
                                "camera": {
                                    "type": "OBJECT",
                                    "nullable": True,
                                    "properties": {
                                        "angle": {"type": "STRING"},
                                        "focal_length_mm": {"type": "INTEGER", "nullable": True},
                                        "lens_type": {"type": "STRING", "nullable": True},
                                        "movement": {"type": "STRING", "nullable": True}
                                    },
                                    "required": ["angle"]
                                },
                                "blocking": {
                                    "type": "OBJECT",
                                    "nullable": True,
                                    "properties": {
                                        "subject_position": {"type": "STRING", "nullable": True},
                                        "gaze_direction": {"type": "STRING", "nullable": True},
                                        "character_interaction": {"type": "STRING", "nullable": True}
                                    }
                                },
                                "composition": {
                                    "type": "OBJECT",
                                    "nullable": True,
                                    "properties": {
                                        "rule_of_thirds": {"type": "BOOLEAN"},
                                        "leading_lines": {"type": "STRING", "nullable": True},
                                        "symmetry": {"type": "BOOLEAN"},
                                        "negative_space": {"type": "STRING", "nullable": True},
                                        "foreground": {"type": "STRING", "nullable": True},
                                        "background": {"type": "STRING", "nullable": True},
                                        "subject_priority": {"type": "STRING", "nullable": True},
                                        "character_placement": {"type": "STRING", "nullable": True},
                                        "horizon_placement": {"type": "STRING", "nullable": True},
                                        "spatial_relationships": {"type": "STRING", "nullable": True}
                                    }
                                },
                                "lighting": {
                                    "type": "OBJECT",
                                    "nullable": True,
                                    "properties": {
                                        "setup": {"type": "STRING"},
                                        "direction": {"type": "STRING", "nullable": True},
                                        "key_fill_ratio": {"type": "STRING", "nullable": True},
                                        "time_of_day": {"type": "STRING", "nullable": True},
                                        "practical_sources": {"type": "STRING", "nullable": True},
                                        "intensity": {"type": "STRING", "nullable": True}
                                    },
                                    "required": ["setup"]
                                },
                                "subject": {"type": "STRING", "nullable": True},
                                "character_actions": {"type": "STRING", "nullable": True},
                                "emotion": {"type": "STRING", "nullable": True}
                            },
                            "required": ["shot_id", "purpose", "story_beat"]
                        }
                    }
                },
                "required": ["scene_id", "visual_goal", "overall_mood", "color_plan", "shots"]
            }

            try:
                result = await provider.generate_json(prompt, response_schema)
                # Ensure the scene ID matches the current scene
                result['scene_id'] = scene.id
                scene_plan = SceneVisualPlanSchema.model_validate(result)
                scenes_visual_plans.append(scene_plan)
            except Exception as e:
                raise ValueError(f"Failed to parse LLM cinematography plan for scene {scene.scene_number}: {e}")

        cinematography_plan = CinematographyPlanSchema(
            project_id=project_id,
            script_id=script.id,
            script_version=script.version,
            scenes=scenes_visual_plans
        )
        return cinematography_plan
