import pytest
from httpx import AsyncClient
from sqlmodel import Session
from app.models.project import Project
from app.models.production import (
    ProductionPlan,
    ShotBlueprint,
    StoryboardFrame,
    ShotStatus
)
from app.schemas.storyboard import StoryboardGenerationContext
from app.services.storyboard_agent import StoryboardAgentService
from app.services.image_generation_service import ImageGenerationService, ProviderRegistry

def test_prompt_compilation():
    registry = ProviderRegistry()
    image_service = ImageGenerationService(registry)
    service = StoryboardAgentService(image_service)
    
    context = StoryboardGenerationContext(
        shot_id="shot_1",
        scene_id="scene_1",
        character_context=["Rahul, wearing apron"],
        environment_context="Rahul's Cafe - Morning",
        continuity_context="Establish location\nEmotion: Frantic\nPurpose: Setting the scene",
        visual_style="", # Style is handled internally by compile_prompt in V1
        lighting="Warm lighting",
        composition="Wide shot showing the counter",
        camera="24mm lens",
        final_prompt=""
    )
    
    prompt = service.compile_prompt(context)
    
    # 1. B&W Style enforced
    assert "STYLE:" in prompt
    assert "Black-and-white storyboard sketch" in prompt
    
    # 2. Cinematography preserved
    assert "CINEMATOGRAPHY:" in prompt
    assert "24mm lens" in prompt
    assert "Warm lighting" in prompt
    assert "Wide shot showing the counter" in prompt
    
    # 3. Environment preserved
    assert "ENVIRONMENT:" in prompt
    assert "Rahul's Cafe - Morning" in prompt
    
    # 4. Characters
    assert "SUBJECT / BLOCKING:" in prompt
    assert "Rahul, wearing apron" in prompt
    
    # 5. Story Beat
    assert "ACTION / STORY BEAT:" in prompt
    assert "Establish location" in prompt

from tests.conftest import get_session_override
