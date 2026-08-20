from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import re

class CameraSchema(BaseModel):
    angle: str = Field(..., description="Camera angle, e.g., EYE_LEVEL, HIGH_ANGLE, LOW_ANGLE")
    focal_length_mm: Optional[int] = Field(None, ge=8, le=800, description="Focal length in mm")
    lens_type: Optional[str] = Field(None, description="e.g., SPHERICAL, ANAMORPHIC, MACRO")
    movement: Optional[str] = Field(None, description="e.g., STATIC, PAN, TILT, DOLLY, STEADICAM")

class BlockingSchema(BaseModel):
    subject_position: Optional[str] = None
    gaze_direction: Optional[str] = None
    character_interaction: Optional[str] = None

class CompositionSchema(BaseModel):
    rule_of_thirds: bool = Field(default=False)
    leading_lines: Optional[str] = None
    symmetry: bool = Field(default=False)
    negative_space: Optional[str] = Field(None, description="e.g., LEFT, RIGHT, TOP, NONE")
    foreground: Optional[str] = None
    background: Optional[str] = None
    subject_priority: Optional[str] = None
    character_placement: Optional[str] = None
    horizon_placement: Optional[str] = Field(None, description="e.g., UPPER_THIRD, CENTER, LOWER_THIRD")
    spatial_relationships: Optional[str] = None

class LightingSchema(BaseModel):
    setup: str = Field(..., description="e.g., THREE_POINT, REMBRANDT, PRACTICAL, NATURAL")
    direction: Optional[str] = Field(None, description="e.g., FRONT, SIDE, BACK, TOP")
    key_fill_ratio: Optional[str] = Field(None, description="e.g., 2:1, 4:1, 8:1")
    time_of_day: Optional[str] = None
    practical_sources: Optional[str] = None
    intensity: Optional[str] = Field(None, description="Relative strength")

class PaletteColor(BaseModel):
    hex: str = Field(..., description="Hex color code")
    role: str = Field(..., description="e.g., SHADOW, HIGHLIGHT, PRACTICAL")
    description: Optional[str] = None

    @field_validator("hex")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        if not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", v):
            raise ValueError(f"Invalid hex color format: {v}")
        return v

class LUTRecommendation(BaseModel):
    name: str
    type: str
    reason: str

class ColorPlan(BaseModel):
    palette: List[PaletteColor] = Field(default_factory=list)
    temperature_kelvin: Optional[int] = Field(None, ge=1000, le=12000)
    contrast: Optional[float] = Field(None, ge=0.0, le=2.0)
    saturation: Optional[float] = Field(None, ge=0.0, le=2.0)
    mood: Optional[str] = None
    film_look: Optional[str] = None
    lut: Optional[LUTRecommendation] = None

class ShotBlueprintSchema(BaseModel):
    shot_id: str
    purpose: str
    story_beat: str
    shot_size: Optional[str] = None
    camera: Optional[CameraSchema] = None
    blocking: Optional[BlockingSchema] = None
    composition: Optional[CompositionSchema] = None
    lighting: Optional[LightingSchema] = None
    subject: Optional[str] = None
    character_actions: Optional[str] = None
    emotion: Optional[str] = None

class SceneVisualPlanSchema(BaseModel):
    scene_id: str
    visual_goal: str
    overall_mood: str
    color_plan: ColorPlan
    shots: List[ShotBlueprintSchema] = Field(default_factory=list)

class CinematographyPlanSchema(BaseModel):
    project_id: str
    script_id: str
    script_version: int
    scenes: List[SceneVisualPlanSchema] = Field(default_factory=list)
