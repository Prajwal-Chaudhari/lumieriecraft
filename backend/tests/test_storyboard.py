import pytest
from httpx import AsyncClient
from sqlmodel import Session
from app.models.project import Project
from app.models.production import (
    ProductionPlan, ShotBlueprint, SceneBreakdown,
    CharacterBible, WorldBible, StoryboardFrame
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
        visual_style="Gritty, cinematic",
        lighting="Warm lighting",
        composition="Wide shot showing the counter",
        camera="24mm lens",
        final_prompt=""
    )
    
    prompt = service.compile_prompt(context)
    
    assert "CAMERA:" in prompt
    assert "24mm lens" in prompt
    assert "Warm lighting" in prompt
    assert "ENVIRONMENT:" in prompt
    assert "Rahul's Cafe - Morning" in prompt
    assert "SUBJECT:" in prompt
    assert "Rahul, wearing apron" in prompt
    assert "STYLE:" in prompt
    assert "Gritty, cinematic" in prompt
    assert "CONTEXT:" in prompt
    assert "Establish location" in prompt

from tests.conftest import get_session_override

def test_api_patch_shot(client, setup_db):
    session = next(get_session_override())
    # Setup data
    project = Project(
        name="Test Proj",
        story_idea="Idea",
        genre="Sci-Fi",
        duration="Feature",
        tone="Dark",
        visual_style="Cyberpunk"
    )
    session.add(project)
    session.commit()
    
    plan = ProductionPlan(project_id=project.id, script_id="fake", script_version=1)
    session.add(plan)
    session.commit()
    
    breakdown = SceneBreakdown(production_plan_id=plan.id, scene_id="scene_1", scene_number=1)
    session.add(breakdown)
    session.commit()
    
    shot = ShotBlueprint(
        production_plan_id=plan.id,
        scene_breakdown_id=breakdown.id,
        scene_id="scene_1",
        shot_id="shot_1",
        purpose="Purpose",
        story_beat="Beat"
    )
    session.add(shot)
    session.commit()
    session.refresh(shot)
    
    response = client.patch(f"/api/projects/{project.id}/production/shots/{shot.id}", json={
        "camera_angle": "Low Angle",
        "lens": "35mm"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["camera_angle"] == "Low Angle"
    assert data["lens"] == "35mm"
    assert data["status"] == "edited"
