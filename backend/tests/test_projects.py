import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.db import get_session
from app.models.project import Project
from app.models.script import Script
from sqlalchemy.pool import StaticPool
# Use an in-memory database for testing
sqlite_url = "sqlite://"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

def test_create_project():
    response = client.post("/api/projects", json={
        "name": "Test Project",
        "story_idea": "A test idea",
        "genre": "Sci-Fi",
        "duration": "Feature",
        "tone": "Dark",
        "visual_style": "Cyberpunk"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data

def test_get_projects():
    client.post("/api/projects", json={
        "name": "Test Project",
        "story_idea": "A test idea",
        "genre": "Sci-Fi",
        "duration": "Feature",
        "tone": "Dark",
        "visual_style": "Cyberpunk"
    })
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test Project"

def test_get_project():
    create_response = client.post("/api/projects", json={
        "name": "Test Project",
        "story_idea": "A test idea",
        "genre": "Sci-Fi",
        "duration": "Feature",
        "tone": "Dark",
        "visual_style": "Cyberpunk"
    })
    project_id = create_response.json()["id"]
    
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["id"] == project_id

def test_get_nonexistent_project():
    response = client.get("/api/projects/nonexistent-id")
    assert response.status_code == 404

def test_regeneration_placeholder():
    # Setup project
    create_response = client.post("/api/projects", json={
        "name": "Test Project",
        "story_idea": "A test idea",
        "genre": "Sci-Fi",
        "duration": "Feature",
        "tone": "Dark",
        "visual_style": "Cyberpunk"
    })
    project_id = create_response.json()["id"]
    
    # Generate script
    script_response = client.post(f"/api/projects/{project_id}/script/generate")
    assert script_response.status_code == 200
    script_data = script_response.json()
    
    # Check scenes
    scenes = script_data.get("scenes", [])
    assert len(scenes) > 0
    scene_id = scenes[0]["id"]
    original_desc = scenes[0]["description"]
    
    # Regenerate scene
    regen_response = client.post(f"/api/projects/{project_id}/script/scenes/{scene_id}/regenerate")
    assert regen_response.status_code == 200
    regen_data = regen_response.json()
    
    regen_scenes = regen_data.get("scenes", [])
    regen_scene = next((s for s in regen_scenes if s["id"] == scene_id), None)
    assert regen_scene is not None
    assert regen_scene["description"] == original_desc + " (Regenerated)"
