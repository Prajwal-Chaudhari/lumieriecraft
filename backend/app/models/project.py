from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field
import uuid

class ProjectBase(SQLModel):
    name: str
    story_idea: str
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
    genre: Optional[str] = None
    duration: Optional[str] = None
    tone: Optional[str] = None
    visual_style: Optional[str] = None
