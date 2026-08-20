from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
import uuid
from datetime import datetime

class ProjectBase(SQLModel):
    name: str
    story_idea: str
    source_material: Optional[str] = None
    genre: str
    duration: str
    tone: str
    visual_style: str

class Project(ProjectBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(SQLModel):
    name: Optional[str] = None
    story_idea: Optional[str] = None
    source_material: Optional[str] = None
    genre: Optional[str] = None
    duration: Optional[str] = None
    tone: Optional[str] = None
    visual_style: Optional[str] = None

class CharacterAssetBase(SQLModel):
    project_id: str = Field(foreign_key="project.id")
    character_id: Optional[str] = None
    character_name: str
    asset_type: str = Field(default="image")
    file_path: str
    source: str = Field(description="'user_upload' or 'ai_generated'")
    description: Optional[str] = None
    continuity_notes: Optional[str] = None

class CharacterAsset(CharacterAssetBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
