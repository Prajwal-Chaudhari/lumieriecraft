import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["SCRIPT_WRITER_PROVIDER"] = "mock"

def test_cinematography_pipeline(client):
    # 1. Setup project
    create_response = client.post("/api/projects", json={
        "name": "Cinematography Test Project",
        "story_idea": "A test idea",
        "source_material": "Rough draft text",
        "genre": "Sci-Fi",
        "duration": "Feature",
        "tone": "Dark",
        "visual_style": "Cyberpunk"
    })
    project_id = create_response.json()["id"]

    # 2. Analyze script
    proposal_response = client.post(f"/api/projects/{project_id}/script/propose-standardization")
    print("422 RESPONSE:", proposal_response.text)
    assert proposal_response.status_code == 200
    proposal_id = proposal_response.json()["id"]
    
    script_response = client.post(f"/api/projects/{project_id}/script/proposals/{proposal_id}/apply")
    assert script_response.status_code == 200

    # 3. Propose Cinematography
    cine_propose_response = client.post(f"/api/projects/{project_id}/cinematography/propose")
    assert cine_propose_response.status_code == 200
    cine_proposal_id = cine_propose_response.json()["id"]
    
    # 4. Apply Cinematography Proposal
    cine_apply_response = client.post(f"/api/projects/{project_id}/cinematography/proposals/{cine_proposal_id}/apply")
    assert cine_apply_response.status_code == 200
    
    # Verify that the plan was created
    cine_get_response = client.get(f"/api/projects/{project_id}/cinematography")
    assert cine_get_response.status_code == 200
    cine_data = cine_get_response.json()
    
    assert "plan" in cine_data
    assert cine_data["plan"]["status"] == "approved"
    assert "scenes_data" in cine_data["plan"]
    
    scenes = cine_data["plan"]["scenes_data"]["scenes"]
    assert len(scenes) > 0
    
    # Verify the structure we mocked
    scene = scenes[0]
    assert scene["scene_id"] == "scene_1"
    assert scene["color_plan"]["temperature_kelvin"] == 6500
    assert len(scene["color_plan"]["palette"]) > 0
    
    assert "shots" in cine_data
    assert len(cine_data["shots"]) > 0
    
    shot = cine_data["shots"][0]
    assert shot["shot_size"] == "Wide"
    assert shot["camera"]["angle"] == "High"
    assert shot["composition"]["symmetry"] is True
