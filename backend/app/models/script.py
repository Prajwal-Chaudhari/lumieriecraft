from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON
from pydantic import BaseModel
import uuid
from datetime import datetime

# Deep nested schemas for structured screenplay
class DialogueLine(BaseModel):
    character: str
    parenthetical: Optional[str] = None
    text: str

class SceneAction(BaseModel):
    text: str

class CharacterRef(BaseModel):
    name: str
    description: Optional[str] = None

class Scene(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scene_number: int
    heading: str
    location: str
    time_of_day: str
    description: str
    characters: List[CharacterRef] = []
    actions: List[SceneAction] = []
    dialogue: List[DialogueLine] = []
    metadata: dict = {}

class ScriptBase(SQLModel):
    title: str
    version: int = 1
    status: str = "draft"
    project_id: str = Field(foreign_key="project.id")

class Script(ScriptBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    scenes: List[dict] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ScriptCreate(ScriptBase):
    pass
