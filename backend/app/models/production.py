from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON
import uuid
from datetime import datetime

# --- Enums / Constants ---
class ProductionStatus:
    NOT_ANALYZED = "not_analyzed"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"

class ShotStatus:
    PLANNED = "planned"
    EDITED = "edited"
    APPROVED = "approved"

# --- Models ---

class ProductionPlanBase(SQLModel):
    project_id: str = Field(foreign_key="project.id")
    script_id: str = Field(foreign_key="script.id")
    script_version: int
    status: str = Field(default=ProductionStatus.NOT_ANALYZED)

class ProductionPlan(ProductionPlanBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CharacterBibleBase(SQLModel):
    production_plan_id: str = Field(foreign_key="productionplan.id")
    name: str
    appearance: Optional[str] = None
    age_range: Optional[str] = None
    hair: Optional[str] = None
    clothing: Optional[str] = None
    accessories: Optional[str] = None
    personality: Optional[str] = None
    relationships: Optional[str] = None
    established_facts: List[str] = Field(default=[], sa_column=Column(JSON))
    proposed_facts: List[str] = Field(default=[], sa_column=Column(JSON))
    continuity_notes: Optional[str] = None
    source_scene_ids: List[str] = Field(default=[], sa_column=Column(JSON))

class CharacterBible(CharacterBibleBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

class WorldBibleBase(SQLModel):
    production_plan_id: str = Field(foreign_key="productionplan.id")
    name: str
    description: Optional[str] = None
    architecture: Optional[str] = None
    environment: Optional[str] = None
    lighting_characteristics: Optional[str] = None
    time_variants: Optional[str] = None
    important_props: Optional[str] = None
    established_facts: List[str] = Field(default=[], sa_column=Column(JSON))
    proposed_facts: List[str] = Field(default=[], sa_column=Column(JSON))
    continuity_notes: Optional[str] = None
    source_scene_ids: List[str] = Field(default=[], sa_column=Column(JSON))

class WorldBible(WorldBibleBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

class SceneBreakdownBase(SQLModel):
    production_plan_id: str = Field(foreign_key="productionplan.id")
    scene_id: str  # References a scene in the script JSON
    scene_number: int
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    characters: List[str] = Field(default=[], sa_column=Column(JSON))
    actions: List[str] = Field(default=[], sa_column=Column(JSON))
    dialogue_summary: Optional[str] = None
    props: List[str] = Field(default=[], sa_column=Column(JSON))
    emotional_beat: Optional[str] = None
    narrative_purpose: Optional[str] = None
    continuity_notes: Optional[str] = None

class SceneBreakdown(SceneBreakdownBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

class ShotBlueprintBase(SQLModel):
    production_plan_id: str = Field(foreign_key="productionplan.id")
    scene_breakdown_id: str = Field(foreign_key="scenebreakdown.id")
    scene_id: str
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
    status: str = Field(default=ShotStatus.PLANNED)

class ShotBlueprint(ShotBlueprintBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
