from pydantic import BaseModel, Field
from typing import List, Optional

class SceneIntelligenceSchema(BaseModel):
    scene_id: str
    location: str
    time_of_day: str
    characters: List[str]
    story_beat: Optional[str] = None
    mood: Optional[str] = None
    props: List[str] = Field(default_factory=list)
    visual_context: Optional[str] = None
    continuity_notes: List[str] = Field(default_factory=list)
    ai_inferred_fields: List[str] = Field(default_factory=list, description="Fields that were inferred by AI rather than explicitly stated.")

class CharacterExtractionSchema(BaseModel):
    name: str
    description: Optional[str] = None
    appearance: Optional[str] = None
    hair: Optional[str] = None
    clothing: Optional[str] = None
    accessories: List[str] = Field(default_factory=list)
    continuity_notes: List[str] = Field(default_factory=list)
    ai_inferred_fields: List[str] = Field(default_factory=list)

class WorldExtractionSchema(BaseModel):
    name: str
    description: Optional[str] = None
    architecture_environment: Optional[str] = None
    lighting_characteristics: Optional[str] = None
    recurring_props: List[str] = Field(default_factory=list)
    continuity_notes: List[str] = Field(default_factory=list)
    ai_inferred_fields: List[str] = Field(default_factory=list)

class GlobalExtractionResult(BaseModel):
    characters: List[CharacterExtractionSchema] = Field(default_factory=list)
    locations: List[WorldExtractionSchema] = Field(default_factory=list)
