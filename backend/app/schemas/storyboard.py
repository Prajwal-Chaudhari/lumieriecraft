from pydantic import BaseModel
from typing import Optional, List

class StoryboardGenerationContext(BaseModel):
    shot_id: str
    scene_id: str

    character_context: List[str]
    environment_context: str
    continuity_context: str

    visual_style: str
    lighting: str
    composition: str
    camera: str

    final_prompt: str
    negative_prompt: Optional[str] = None
