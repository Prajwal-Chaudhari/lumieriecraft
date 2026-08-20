import pytest
import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["SCRIPT_WRITER_PROVIDER"] = "mock"

def test_create_project(client):
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

def test_get_projects(client):
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

def test_get_project(client):
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

def test_get_nonexistent_project(client):
    response = client.get("/api/projects/nonexistent-id")
    assert response.status_code == 404

def test_analyze_and_propose(client):
    # Setup project
    create_response = client.post("/api/projects", json={
        "name": "Test Project",
        "story_idea": "A test idea",
        "source_material": "Rough draft text",
        "genre": "Sci-Fi",
        "duration": "Feature",
        "tone": "Dark",
        "visual_style": "Cyberpunk"
    })
    project_id = create_response.json()["id"]
    
    # Propose script standardization
    proposal_response = client.post(f"/api/projects/{project_id}/script/propose-standardization")
    assert proposal_response.status_code == 200
    proposal_id = proposal_response.json()["id"]
    
    # Apply standard script
    script_response = client.post(f"/api/projects/{project_id}/script/proposals/{proposal_id}/apply")
    assert script_response.status_code == 200
    script_data = script_response.json()
    assert script_data["version"] == 1
    
    # Check scenes
    scenes = script_data.get("scenes", [])
    assert len(scenes) > 0
    scene_id = scenes[0]["id"]
    
    # Propose scene fix
    regen_response = client.post(
        f"/api/projects/{project_id}/script/scenes/{scene_id}/propose-fix",
        json={"base_version": 1, "instructions": "Make it rain"}
    )
    assert regen_response.status_code == 200, regen_response.text
    regen_data = regen_response.json()
    
    scene_proposal_id = regen_data["id"]
    proposed_script = regen_data.get("proposed_script", {})
    assert proposed_script is not None
    
    proposed_scenes = proposed_script.get("scenes", [])
    proposed_scene = next((s for s in proposed_scenes if s["id"] == scene_id), None)
    
    # We are using MockLLMProvider which returns a hardcoded Space Station scene
    # But ScriptDoctorService must preserve the original scene ID and scene_number.
    assert proposed_scene["heading"] == "INT. SPACE STATION - NIGHT"
    assert proposed_scene["scene_number"] == scenes[0]["scene_number"]
    
    # Apply scene fix
    apply_response = client.post(
        f"/api/projects/{project_id}/script/proposals/{scene_proposal_id}/apply"
    )
    assert apply_response.status_code == 200
    apply_data = apply_response.json()
    assert apply_data["version"] == 2
    
    updated_scenes = apply_data.get("scenes", [])
    updated_scene = next((s for s in updated_scenes if s["id"] == scene_id), None)
    assert updated_scene is not None
    assert updated_scene["heading"] == "INT. SPACE STATION - NIGHT"

