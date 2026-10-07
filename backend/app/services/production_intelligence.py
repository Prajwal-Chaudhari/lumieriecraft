import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from app.models.production import (
    CharacterBible, WorldBible, SceneBreakdown
)
from app.models.script import Script, Scene
from app.providers.registry import ProviderRegistry
from app.providers.llm.registry import get_llm_provider

# --- Pydantic Schemas for Structured Output ---

class CharacterExtraction(BaseModel):
    name: str
    description: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    clothing: Optional[str] = None
    hair: Optional[str] = None
    accessories: Optional[str] = None
    established_facts: List[str] = Field(default_factory=list)
    inferred_facts: List[str] = Field(default_factory=list)
    continuity_notes: Optional[str] = None
    source_scene_ids: List[str] = Field(default_factory=list)

class WorldExtraction(BaseModel):
    name: str
    description: Optional[str] = None
    architecture: Optional[str] = None
    lighting_characteristics: Optional[str] = None
    time_variants: Optional[str] = None
    recurring_props: Optional[str] = None
    established_facts: List[str] = Field(default_factory=list)
    inferred_facts: List[str] = Field(default_factory=list)
    continuity_notes: Optional[str] = None
    source_scene_ids: List[str] = Field(default_factory=list)

class GlobalExtractionResult(BaseModel):
    characters: List[CharacterExtraction] = Field(default_factory=list)
    locations: List[WorldExtraction] = Field(default_factory=list)

class SceneBreakdownExtraction(BaseModel):
    summary: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    story_beat: Optional[str] = None
    emotional_beat: Optional[str] = None
    narrative_purpose: Optional[str] = None
    props: List[str] = Field(default_factory=list)
    visual_context: Optional[str] = None
    continuity_notes: Optional[str] = None
    inference_provenance: Dict[str, Any] = Field(default_factory=dict)

# --- Service Class ---

import asyncio
import logging

async def _generate_with_retry(provider, prompt: str, response_schema: dict) -> dict:
    max_retries = 3
    base_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            return await provider.generate_json(prompt, response_schema)
        except Exception as e:
            error_msg = str(e)
            
            # Check for transient errors
            is_transient = any(code in error_msg for code in ["429", "500", "502", "503", "504"])
            
            if not is_transient or attempt == max_retries - 1:
                raise ValueError(f"LLM Provider Error: {error_msg}")
            
            delay = base_delay * (2 ** attempt)
            logging.warning(f"Transient LLM error. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
            await asyncio.sleep(delay)

class ProductionIntelligenceService:
    def __init__(self, provider_registry: ProviderRegistry = None):
        self.get_llm = get_llm_provider

    async def extract_global_bibles(self, db: Session, script: Script) -> GlobalExtractionResult:
        """
        Extracts Character and World bibles from the script and upserts them into the database.
        Returns the extracted Pydantic models.
        """
        if script.status != "approved":
            raise ValueError("Script must be approved before global bible extraction.")

        provider = self.get_llm(purpose="PRODUCTION_INTELLIGENCE")
        
        extraction = GlobalExtractionResult(characters=[], locations=[])

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "characters": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "description": {"type": "STRING", "nullable": True},
                            "appearance": {"type": "STRING", "nullable": True},
                            "personality": {"type": "STRING", "nullable": True},
                            "clothing": {"type": "STRING", "nullable": True},
                            "hair": {"type": "STRING", "nullable": True},
                            "accessories": {"type": "STRING", "nullable": True},
                            "established_facts": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "inferred_facts": {"type": "ARRAY", "items": {"type": "STRING"}},
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
                            "lighting_characteristics": {"type": "STRING", "nullable": True},
                            "time_variants": {"type": "STRING", "nullable": True},
                            "recurring_props": {"type": "STRING", "nullable": True},
                            "established_facts": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "inferred_facts": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "continuity_notes": {"type": "STRING", "nullable": True},
                            "source_scene_ids": {"type": "ARRAY", "items": {"type": "STRING"}}
                        },
                        "required": ["name"]
                    }
                }
            }
        }
        
        chunk_size = 20
        for i in range(0, len(script.scenes), chunk_size):
            chunk_scenes = script.scenes[i:i + chunk_size]
            script_text = ""
            for scene_dict in chunk_scenes:
                scene = Scene.model_validate(scene_dict)
                script_text += f"\n\nSCENE {scene.scene_number}: {scene.heading}\n"
                script_text += f"ID: {scene.id}\n"
                script_text += f"Location: {scene.location}\n"
                script_text += f"Time of Day: {scene.time_of_day}\n"
                script_text += f"Description: {scene.description}\n"
                chars = ", ".join([c.name for c in scene.characters]) if scene.characters else "None explicit"
                script_text += f"Characters in Scene: {chars}\n"

            prompt = f"""You are a professional production breakdown agent.
Analyze the following section of an approved screenplay. Extract all significant characters and locations to form the Character Bible and World Bible.
For each, clearly separate 'established_facts' (explicitly stated in the screenplay text) from 'inferred_facts' (your logical inferences/suggestions for production).
DO NOT treat AI inference as established canon. DO NOT fabricate characters or locations not present in this text.
Strictly ensure continuity constraints are extracted and placed into 'continuity_notes' as a single string paragraph (NOT a list/array).
Track 'source_scene_ids' as a list of strings for where they appear using the provided ID.

Screenplay Section:
{script_text}
"""
            
            result = await _generate_with_retry(provider, prompt, response_schema)
            try:
                chunk_extraction = GlobalExtractionResult.model_validate(result)
                
                # Merge Characters
                for char in chunk_extraction.characters:
                    existing = next((c for c in extraction.characters if c.name.upper() == char.name.upper()), None)
                    if existing:
                        existing.established_facts = list(set(existing.established_facts + char.established_facts))
                        existing.inferred_facts = list(set(existing.inferred_facts + char.inferred_facts))
                        existing.source_scene_ids = list(set(existing.source_scene_ids + char.source_scene_ids))
                        if not existing.description and char.description: existing.description = char.description
                        if not existing.appearance and char.appearance: existing.appearance = char.appearance
                        if not existing.personality and char.personality: existing.personality = char.personality
                        if not existing.clothing and char.clothing: existing.clothing = char.clothing
                        if not existing.hair and char.hair: existing.hair = char.hair
                        if not existing.accessories and char.accessories: existing.accessories = char.accessories
                        if not existing.continuity_notes and char.continuity_notes: existing.continuity_notes = char.continuity_notes
                    else:
                        extraction.characters.append(char)

                # Merge Locations
                for loc in chunk_extraction.locations:
                    existing = next((l for l in extraction.locations if l.name.upper() == loc.name.upper()), None)
                    if existing:
                        existing.established_facts = list(set(existing.established_facts + loc.established_facts))
                        existing.inferred_facts = list(set(existing.inferred_facts + loc.inferred_facts))
                        existing.source_scene_ids = list(set(existing.source_scene_ids + loc.source_scene_ids))
                        if not existing.description and loc.description: existing.description = loc.description
                        if not existing.architecture and loc.architecture: existing.architecture = loc.architecture
                        if not existing.lighting_characteristics and loc.lighting_characteristics: existing.lighting_characteristics = loc.lighting_characteristics
                        if not existing.time_variants and loc.time_variants: existing.time_variants = loc.time_variants
                        if not existing.recurring_props and loc.recurring_props: existing.recurring_props = loc.recurring_props
                        if not existing.continuity_notes and loc.continuity_notes: existing.continuity_notes = loc.continuity_notes
                    else:
                        extraction.locations.append(loc)
            except Exception as e:
                raise ValueError(f"Failed to parse LLM global extraction for chunk: {e}")

        # Upsert Characters
        for char_data in extraction.characters:
            normalized_name = char_data.name.strip().upper()
            existing_char = db.exec(
                select(CharacterBible).where(
                    CharacterBible.project_id == script.project_id,
                    CharacterBible.name == normalized_name
                )
            ).first()

            if existing_char:
                for k, v in char_data.model_dump().items():
                    setattr(existing_char, k, v)
                existing_char.name = normalized_name # ensure normalization
                db.add(existing_char)
            else:
                new_char = CharacterBible(project_id=script.project_id, **char_data.model_dump())
                new_char.name = normalized_name
                db.add(new_char)

        # Upsert Locations (World)
        for loc_data in extraction.locations:
            normalized_name = loc_data.name.strip().upper()
            existing_loc = db.exec(
                select(WorldBible).where(
                    WorldBible.project_id == script.project_id,
                    WorldBible.name == normalized_name
                )
            ).first()

            if existing_loc:
                for k, v in loc_data.model_dump().items():
                    setattr(existing_loc, k, v)
                existing_loc.name = normalized_name
                db.add(existing_loc)
            else:
                new_loc = WorldBible(project_id=script.project_id, **loc_data.model_dump())
                new_loc.name = normalized_name
                db.add(new_loc)

        db.commit()
        return extraction

    async def analyze_scene_for_production(self, db: Session, script: Script, scene: Scene, global_bibles: GlobalExtractionResult) -> SceneBreakdownExtraction:
        """
        Analyzes a scene for production intelligence (derived information) and upserts it.
        """
        if script.status != "approved":
            raise ValueError("Script must be approved before scene breakdown extraction.")

        provider = self.get_llm(purpose="PRODUCTION_INTELLIGENCE")
        
        scene_text = f"SCENE {scene.scene_number}: {scene.heading}\nDescription: {scene.description}\n"
        for action in scene.actions:
            scene_text += f"Action: {action.text}\n"
        for dialogue in scene.dialogue:
            scene_text += f"{dialogue.character}: {dialogue.text}\n"

        prompt = f"""You are a professional production breakdown agent.
Analyze the following scene from the approved screenplay. 
DO NOT duplicate the actions, dialogue, or scene description. Provide derived production intelligence: 
summary of the scene, location context, time of day, story beat, emotional beat, narrative purpose, visual context, props, and continuity notes.
Use the global context (Character & World Bibles) to ensure consistency.
DO NOT fabricate characters, locations, props, or story events that are not supported by the scene text.
Strictly ensure continuity constraints are extracted and placed into 'continuity_notes' as a single string paragraph (NOT a list/array).
If something is not present, omit it rather than hallucinating.

Global Context:
{global_bibles.model_dump_json(indent=2)}

Scene to Analyze:
{scene_text}
"""
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "summary": {"type": "STRING", "description": "A concise summary of the scene.", "nullable": True},
                "location": {"type": "STRING", "nullable": True},
                "time_of_day": {"type": "STRING", "nullable": True},
                "story_beat": {"type": "STRING", "nullable": True},
                "emotional_beat": {"type": "STRING", "nullable": True},
                "narrative_purpose": {"type": "STRING", "nullable": True},
                "props": {"type": "ARRAY", "items": {"type": "STRING"}},
                "visual_context": {"type": "STRING", "nullable": True},
                "continuity_notes": {"type": "STRING", "nullable": True},
                "inference_provenance": {"type": "OBJECT", "nullable": True}
            }
        }

        result = await _generate_with_retry(provider, prompt, response_schema)
        try:
            extraction = SceneBreakdownExtraction.model_validate(result)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM scene breakdown: {e}")

        # Upsert SceneBreakdown
        existing_breakdown = db.exec(
            select(SceneBreakdown).where(
                SceneBreakdown.project_id == script.project_id,
                SceneBreakdown.script_id == script.id,
                SceneBreakdown.scene_id == scene.id
            )
        ).first()

        if existing_breakdown:
            for k, v in extraction.model_dump().items():
                setattr(existing_breakdown, k, v)
            db.add(existing_breakdown)
        else:
            new_breakdown = SceneBreakdown(
                project_id=script.project_id,
                script_id=script.id,
                scene_id=scene.id,
                **extraction.model_dump()
            )
            db.add(new_breakdown)

        db.commit()
        return extraction

    async def generate_costume_recommendation(self, db: Session, script: Script, character: CharacterBible) -> dict:
        provider = self.get_llm(purpose="PRODUCTION_INTELLIGENCE")
        
        scene_appearances = []
        for scene_dict in script.scenes:
            scene = Scene.model_validate(scene_dict)
            
            # Check if character is in the scene explicitly by character list or dialogue
            in_scene = False
            if scene.characters and any(c.name.upper() == character.name.upper() for c in scene.characters):
                in_scene = True
            elif scene.dialogue and any(d.character.upper() == character.name.upper() for d in scene.dialogue):
                in_scene = True
                
            if in_scene:
                breakdown = db.exec(select(SceneBreakdown).where(SceneBreakdown.scene_id == scene.id)).first()
                scene_info = {
                    "scene_id": scene.id,
                    "scene_number": scene.scene_number,
                    "heading": scene.heading,
                    "summary": breakdown.summary if breakdown else scene.description
                }
                scene_appearances.append(scene_info)

        prompt = f"""You are an expert film costume designer.
Provide a costume recommendation for the character '{character.name}'.

ESTABLISHED CHARACTER FACTS:
Description: {character.description or 'None'}
Appearance: {character.appearance or 'None'}
Personality: {character.personality or 'None'}
Established Clothing (From Screenplay): {character.clothing or 'None'}
Accessories: {character.accessories or 'None'}

The character appears in {len(scene_appearances)} scenes.
Scenes Context: {json.dumps(scene_appearances, indent=2)}

Generate a detailed costume recommendation.
IMPORTANT CONTINUITY RULE: Base your recommendation on the established clothing if provided. Do NOT overwrite established facts.
Provide variations for specific scenes ONLY if the story/summary implies a necessary costume change (e.g., getting dirty, changing for an event).
"""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "recommended_costume": {
                    "type": "OBJECT",
                    "properties": {
                        "top": {"type": "STRING", "nullable": True},
                        "bottom": {"type": "STRING", "nullable": True},
                        "outerwear": {"type": "STRING", "nullable": True},
                        "footwear": {"type": "STRING", "nullable": True},
                        "accessories": {"type": "ARRAY", "items": {"type": "STRING"}}
                    }
                },
                "color_palette": {"type": "ARRAY", "items": {"type": "STRING"}},
                "styling_notes": {"type": "STRING"},
                "continuity_notes": {"type": "STRING"},
                "scene_variations": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "scene_id": {"type": "STRING"},
                            "scene_heading": {"type": "STRING"},
                            "costume_change": {"type": "STRING"}
                        },
                        "required": ["scene_id", "costume_change"]
                    }
                }
            },
            "required": ["recommended_costume", "styling_notes"]
        }

        result = await _generate_with_retry(provider, prompt, response_schema)
        
        character.costume_recommendation = result
        db.add(character)
        db.commit()
        db.refresh(character)
        
        return result
