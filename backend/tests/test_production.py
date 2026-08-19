import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["SCRIPT_WRITER_PROVIDER"] = "mock"

def test_production_analysis(client):
    # 1. Setup project
    create_response = client.post("/api/projects", json={
        "name": "Production Test Project",
        "story_idea": "A test idea",
        "source_material": "Rough draft text",
        "genre": "Sci-Fi",
        "duration": "Feature",
        "tone": "Dark",
        "visual_style": "Cyberpunk"
    })
    project_id = create_response.json()["id"]

    # 2. Analyze script
    script_response = client.post(f"/api/projects/{project_id}/script/analyze")
    assert script_response.status_code == 200

    # 3. Analyze for production
    # Wait, Starlette runs BackgroundTasks sequentially in the TestClient after returning the response!
    prod_analyze_response = client.post(f"/api/projects/{project_id}/production/analyze")
    assert prod_analyze_response.status_code == 200

    # Verify that the plan was created and status updated
    prod_response = client.get(f"/api/projects/{project_id}/production")
    assert prod_response.status_code == 200
    prod_data = prod_response.json()
    
    assert "plan" in prod_data
    assert prod_data["plan"]["status"] == "analyzed"
    
    assert len(prod_data["characters"]) > 0
    assert prod_data["characters"][0]["name"] == "ASTRONAUT"
    
    assert len(prod_data["worlds"]) > 0
    assert prod_data["worlds"][0]["name"] == "SPACE STATION"
    
    assert len(prod_data["scene_breakdowns"]) > 0
    breakdown = prod_data["scene_breakdowns"][0]
    assert breakdown["location"] == "SPACE STATION"
    scene_id = breakdown["scene_id"]
    
    # 4. Generate Cinematography
    cine_response = client.post(f"/api/projects/{project_id}/cinematography/generate?scene_id={scene_id}")
    assert cine_response.status_code == 200
    
    # Verify Shots
    shots_response = client.get(f"/api/projects/{project_id}/production/scenes/{scene_id}")
    assert shots_response.status_code == 200
    shots_data = shots_response.json()
    
    assert "shots" in shots_data
    assert len(shots_data["shots"]) > 0
    assert shots_data["shots"][0]["shot_size"] == "Wide"
