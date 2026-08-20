from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
import uuid
from datetime import datetime

# Schemas removed from direct import since fields are now JSON dicts
class ProductionStatus:
    NOT_PLANNED = "not_planned"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"

class ShotStatus:
    PLANNED = "planned"
    EDITED = "edited"
    APPROVED = "approved"

class ProductionPlanBase(SQLModel):
    project_id: str = Field(foreign_key="project.id")
    script_id: str = Field(foreign_key="script.id")
    script_version: int
    status: str = Field(default=ProductionStatus.NOT_PLANNED)
    scenes_data: dict = Field(default={}, sa_column=Column(JSON)) # Stores SceneVisualPlans minus the shots

class ProductionPlan(ProductionPlanBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)

class CinematographyProposal(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    script_id: str = Field(foreign_key="script.id")
    script_version: int
    proposed_plan: dict = Field(default={}, sa_column=Column(JSON)) # CinematographyPlanSchema
    status: str = Field(default="PENDING")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ShotBlueprintBase(SQLModel):
    production_plan_id: str = Field(foreign_key="productionplan.id")
    scene_id: str
    shot_id: str
    purpose: str
    story_beat: str
    shot_size: Optional[str] = None
    camera: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    blocking: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    composition: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    lighting: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    subject: Optional[str] = None
    character_actions: Optional[str] = None
    emotion: Optional[str] = None
    status: str = Field(default=ShotStatus.PLANNED)

class ShotBlueprint(ShotBlueprintBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
class StoryboardFrameBase(SQLModel):
    project_id: str = Field(foreign_key="project.id")
    production_plan_id: str = Field(foreign_key="productionplan.id")
    script_id: str = Field(foreign_key="script.id")
    script_version: int
    scene_id: str
    shot_id: str = Field(foreign_key="shotblueprint.id")

    generation_id: str
    provider: str
    model: str
    image_url: str

    prompt: Optional[str] = None
    generation_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    status: str
    error_message: Optional[str] = None

class StoryboardFrame(StoryboardFrameBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
