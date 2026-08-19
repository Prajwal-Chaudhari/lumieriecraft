import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from app.models.production import (
    ProductionPlan, CharacterBible, WorldBible, SceneBreakdown, ShotBlueprint,
    ProductionStatus, ShotStatus
)
from app.models.script import Script, Scene
from app.providers.registry import ProviderRegistry

# --- Pydantic Schemas for Structured Output ---

class CharacterExtraction(BaseModel):
    name: str
    appearance: Optional[str] = None
    age_range: Optional[str] = None
    hair: Optional[str] = None
    clothing: Optional[str] = None
    accessories: Optional[str] = None
    personality: Optional[str] = None
    relationships: Optional[str] = None
    established_facts: List[str] = Field(default_factory=list)
    proposed_facts: List[str] = Field(default_factory=list)
    continuity_notes: Optional[str] = None
    source_scene_ids: List[str] = Field(default_factory=list)

class WorldExtraction(BaseModel):
    name: str
    description: Optional[str] = None
    architecture: Optional[str] = None
    environment: Optional[str] = None
    lighting_characteristics: Optional[str] = None
    time_variants: Optional[str] = None
    important_props: Optional[str] = None
    established_facts: List[str] = Field(default_factory=list)
    proposed_facts: List[str] = Field(default_factory=list)
    continuity_notes: Optional[str] = None
    source_scene_ids: List[str] = Field(default_factory=list)

class GlobalExtractionResult(BaseModel):
    characters: List[CharacterExtraction] = Field(default_factory=list)
    locations: List[WorldExtraction] = Field(default_factory=list)

class SceneBreakdownExtraction(BaseModel):
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    characters: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    dialogue_summary: Optional[str] = None
    props: List[str] = Field(default_factory=list)
    emotional_beat: Optional[str] = None
    narrative_purpose: Optional[str] = None
    continuity_notes: Optional[str] = None

class ShotExtraction(BaseModel):
    shot_id: str
    purpose: str
    story_beat: str
    shot_size: Optional[str] = None
    camera_angle: Optional[str] = None
    lens: Optional[str] = None
    composition: Optional[str] = None
    lighting: Optional[str] = None
    camera_movement: Optional[str] = None
    subject: Optional[str] = None
    character_actions: Optional[str] = None
    emotion: Optional[str] = None
    visual_prompt: Optional[str] = None

class CinematographyResult(BaseModel):
    shots: List[ShotExtraction] = Field(default_factory=list)

from app.providers.llm.registry import get_llm_provider

# --- Service Class ---

class ProductionIntelligenceService:
    def __init__(self, provider_registry: ProviderRegistry = None):
        # We don't actually need ProviderRegistry for LLM since we use get_llm_provider()
        self.get_llm = get_llm_provider

    async def extract_global_bibles(self, script: Script) -> GlobalExtractionResult:
        provider = self.get_llm()
        
        # Serialize the entire script to pass to Gemini
        script_text = ""
        for scene_dict in script.scenes:
            scene = Scene.model_validate(scene_dict)
            script_text += f"\n\nSCENE {scene.scene_number}: {scene.heading}\n"
            script_text += f"ID: {scene.id}\n"
            script_text += f"Description: {scene.description}\n"
            for action in scene.actions:
                script_text += f"Action: {action.text}\n"
            for dialogue in scene.dialogue:
                script_text += f"{dialogue.character}: {dialogue.text}\n"

        prompt = f"""You are a professional production breakdown agent.
Analyze the following script globally. Extract all significant characters and locations to form the Character Bible and World Bible.
For each, clearly separate 'established_facts' (explicitly stated in the script) from 'proposed_facts' (your logical inferences/suggestions for production).
Track 'source_scene_ids' for where they appear.

Script:
{script_text}
"""
        # Note: We need a manual response_schema for Gemini. Since Pydantic nested schemas
        # with Gemini SDK can be tricky, we define the raw dict format matching the Pydantic schema.
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "characters": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "appearance": {"type": "STRING", "nullable": True},
                            "age_range": {"type": "STRING", "nullable": True},
                            "hair": {"type": "STRING", "nullable": True},
                            "clothing": {"type": "STRING", "nullable": True},
                            "accessories": {"type": "STRING", "nullable": True},
                            "personality": {"type": "STRING", "nullable": True},
                            "relationships": {"type": "STRING", "nullable": True},
                            "established_facts": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "proposed_facts": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "continuity_notes": {"type": "STRING", "nullable": True},
                            "source_scene_ids": {"type": "ARRAY", "items": {"type": "STRING"}}
                        },
                        "required": ["name"]
                    }
                },
                "locations": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "description": {"type": "STRING", "nullable": True},
                            "architecture": {"type": "STRING", "nullable": True},
                            "environment": {"type": "STRING", "nullable": True},
                            "lighting_characteristics": {"type": "STRING", "nullable": True},
                            "time_variants": {"type": "STRING", "nullable": True},
                            "important_props": {"type": "STRING", "nullable": True},
                            "established_facts": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "proposed_facts": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "continuity_notes": {"type": "STRING", "nullable": True},
                            "source_scene_ids": {"type": "ARRAY", "items": {"type": "STRING"}}
                        },
                        "required": ["name"]
                    }
                }
            }
        }
        
        result = await provider.generate_json(prompt, response_schema)
        try:
            return GlobalExtractionResult.model_validate(result)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM global extraction: {e}")

    async def analyze_scene_for_production(self, scene: Scene, global_bibles: GlobalExtractionResult) -> SceneBreakdownExtraction:
        provider = self.get_llm()
        
        scene_text = f"SCENE {scene.scene_number}: {scene.heading}\nDescription: {scene.description}\n"
        for action in scene.actions:
            scene_text += f"Action: {action.text}\n"
        for dialogue in scene.dialogue:
            scene_text += f"{dialogue.character}: {dialogue.text}\n"

        prompt = f"""You are a professional production breakdown agent.
Analyze the following scene. Provide a scene breakdown (location, characters, props, actions, emotional beat, narrative purpose, continuity notes).
Use the following global context (Character & World Bibles) to ensure consistency and pull relevant continuity facts.

Global Context:
{global_bibles.model_dump_json(indent=2)}

Scene to Analyze:
{scene_text}
"""
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "location": {"type": "STRING", "nullable": True},
                "time_of_day": {"type": "STRING", "nullable": True},
                "characters": {"type": "ARRAY", "items": {"type": "STRING"}},
                "actions": {"type": "ARRAY", "items": {"type": "STRING"}},
                "dialogue_summary": {"type": "STRING", "nullable": True},
                "props": {"type": "ARRAY", "items": {"type": "STRING"}},
                "emotional_beat": {"type": "STRING", "nullable": True},
                "narrative_purpose": {"type": "STRING", "nullable": True},
                "continuity_notes": {"type": "STRING", "nullable": True}
            }
        }

        result = await provider.generate_json(prompt, response_schema)
        try:
            return SceneBreakdownExtraction.model_validate(result)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM scene breakdown: {e}")

    async def generate_cinematography(self, scene_breakdown: SceneBreakdown, global_bibles: GlobalExtractionResult) -> CinematographyResult:
        provider = self.get_llm()
        
        prompt = f"""You are a professional Director of Photography.
Generate a cinematic Shot Blueprint for the following scene.
Explain WHY each shot is necessary using 'purpose' and 'story_beat'.
Provide shot sizes, angles, lenses, composition, lighting, camera movement, and visual prompts for each shot.

Scene Breakdown:
Location: {scene_breakdown.location}
Time: {scene_breakdown.time_of_day}
Characters: {scene_breakdown.characters}
Actions: {scene_breakdown.actions}
Emotional Beat: {scene_breakdown.emotional_beat}
Narrative Purpose: {scene_breakdown.narrative_purpose}
Continuity Notes: {scene_breakdown.continuity_notes}

Global Context (Characters & Worlds):
{global_bibles.model_dump_json(indent=2)}
"""
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "shots": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "shot_id": {"type": "STRING"},
                            "purpose": {"type": "STRING"},
                            "story_beat": {"type": "STRING"},
                            "shot_size": {"type": "STRING", "nullable": True},
                            "camera_angle": {"type": "STRING", "nullable": True},
                            "lens": {"type": "STRING", "nullable": True},
                            "composition": {"type": "STRING", "nullable": True},
                            "lighting": {"type": "STRING", "nullable": True},
                            "camera_movement": {"type": "STRING", "nullable": True},
                            "subject": {"type": "STRING", "nullable": True},
                            "character_actions": {"type": "STRING", "nullable": True},
                            "emotion": {"type": "STRING", "nullable": True},
                            "visual_prompt": {"type": "STRING", "nullable": True}
                        },
                        "required": ["shot_id", "purpose", "story_beat"]
                    }
                }
            }
        }

        result = await provider.generate_json(prompt, response_schema)
        try:
            return CinematographyResult.model_validate(result)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM cinematography shot plan: {e}")
