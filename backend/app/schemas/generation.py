from pydantic import BaseModel, Field
from typing import Literal

class GenerationRequest(BaseModel):
    project_id: str
    scene_id: str
    shot_id: str

    prompt: str
    negative_prompt: str | None = None

    reference_images: list[str] = Field(default_factory=list)
    control_images: list[str] = Field(default_factory=list)

    width: int = 1024
    height: int = 1024

    seed: int | None = None

    style: str | None = None

    mode: Literal[
        "storyboard_sketch",
        "variation",
        "cinematic_final"
    ]

class GenerationResult(BaseModel):
    provider: str
    model: str

    generation_id: str

    image_urls: list[str]

    seed: int | None = None

    metadata: dict = Field(default_factory=dict)
