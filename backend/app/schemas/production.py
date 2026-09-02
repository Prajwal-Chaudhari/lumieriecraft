from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class CharacterBibleResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    clothing: Optional[str] = None
    hair: Optional[str] = None
    accessories: Optional[str] = None
    established_facts: List[str] = []
    inferred_facts: List[str] = []
    continuity_notes: Optional[str] = None
    source_scene_ids: List[str] = []
    reference_images: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WorldBibleResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    architecture: Optional[str] = None
    lighting_characteristics: Optional[str] = None
    time_variants: Optional[str] = None
    recurring_props: Optional[str] = None
    established_facts: List[str] = []
    inferred_facts: List[str] = []
    continuity_notes: Optional[str] = None
    source_scene_ids: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SceneBreakdownResponse(BaseModel):
    id: str
    project_id: str
    script_id: str
    scene_id: str
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    story_beat: Optional[str] = None
    emotional_beat: Optional[str] = None
    narrative_purpose: Optional[str] = None
    props: List[str] = []
    visual_context: Optional[str] = None
    continuity_notes: Optional[str] = None
    inference_provenance: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductionAnalysisResponse(BaseModel):
    characters: List[CharacterBibleResponse]
    world_locations: List[WorldBibleResponse]
    scene_breakdowns: List[SceneBreakdownResponse]
