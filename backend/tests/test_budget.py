import pytest
from sqlmodel import Session, select
from app.db import get_session
from app.models.project import Project
from app.models.script import Script
from app.models.production import SceneBreakdown

def test_budget_empty_project(client):
    # Setup project
    create_response = client.post("/api/projects", json={
        "name": "Test Budget Project Empty",
        "story_idea": "A test idea",
        "genre": "Sci-Fi",
        "duration": "Feature",
        "tone": "Dark",
        "visual_style": "Cyberpunk"
    })
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]

    # Call budget endpoint directly
    budget_response = client.get(f"/api/projects/{project_id}/budget")
    assert budget_response.status_code == 200
    data = budget_response.json()
    assert data["total"] == 0
    assert len(data["scenes"]) == 0

def test_budget_calculation(client, session: Session):
    # Setup project
    create_response = client.post("/api/projects", json={
        "name": "Test Budget Project Full",
        "story_idea": "A test idea",
        "genre": "Sci-Fi",
        "duration": "Feature",
        "tone": "Dark",
        "visual_style": "Cyberpunk"
    })
    project_id = create_response.json()["id"]
    
    # Create a script with 2 scenes
    script = Script(
        project_id=project_id,
        title="Test Script",
        version=1,
        status="approved",
        scenes=[
            {
                "id": "scene_1",
                "scene_number": 1,
                "heading": "EXT. CAFE - DAY",
                "time_of_day": "DAY",
                "location": "Cafe",
                "description": "A sunny day.",
                "characters": [{"name": "ALICE"}],
                "dialogue": [{"character": "ALICE", "text": "Hello."}]
            },
            {
                "id": "scene_2",
                "scene_number": 2,
                "heading": "INT. WAREHOUSE - NIGHT",
                "time_of_day": "NIGHT",
                "location": "Warehouse",
                "description": "A dark night.",
                "characters": [{"name": "ALICE"}, {"name": "BOB"}],
                "dialogue": []
            }
        ]
    )
    session.add(script)
    session.commit()
    session.refresh(script)
    
    # Add SceneBreakdowns
    sb1 = SceneBreakdown(
        project_id=project_id,
        script_id=script.id,
        scene_id="scene_1",
        props=["Coffee Cup", "Newspaper"]
    )
    sb2 = SceneBreakdown(
        project_id=project_id,
        script_id=script.id,
        scene_id="scene_2",
        props=["Gun"]
    )
    session.add(sb1)
    session.add(sb2)
    session.commit()

    # Call budget endpoint
    budget_response = client.get(f"/api/projects/{project_id}/budget")
    assert budget_response.status_code == 200
    data = budget_response.json()
    
    # Verify overall deterministic nature
    assert len(data["scenes"]) == 2
    
    # Scene 1: EXT. CAFE - DAY
    # Characters: ALICE (1) => Cast = 5000, New Costume = 1 => 1500
    # Location: EXT => 8000 * 1.5 = 12000
    # Lighting: DAY => 2500
    # Equipment: 4000
    # Props: 2 items => 2000
    # Crew, Makeup, Transport, Misc: 5000+1000+2000+1000 = 9000
    # Total Scene 1: 5000 + 1500 + 12000 + 2500 + 4000 + 2000 + 9000 = 36000
    scene1 = next(s for s in data["scenes"] if s["scene_id"] == "scene_1")
    assert scene1["breakdown"]["cast"] == 5000
    assert scene1["breakdown"]["costumes"] == 1500
    assert scene1["breakdown"]["location"] == 12000
    assert scene1["breakdown"]["props"] == 2000
    assert scene1["breakdown"]["lighting"] == 2500
    assert scene1["total"] == 36000
    
    # Scene 2: INT. WAREHOUSE - NIGHT
    # Characters: ALICE, BOB (2) => Cast = 10000
    # New Costumes: BOB is new (1) => 1500
    # Location: INT => 8000
    # Lighting: NIGHT => 2500 * 1.2 = 3000
    # Equipment: 4000
    # Props: 1 item => 1000
    # Crew, Makeup, Transport, Misc: 9000
    # Total Scene 2: 10000 + 1500 + 8000 + 3000 + 4000 + 1000 + 9000 = 36500
    scene2 = next(s for s in data["scenes"] if s["scene_id"] == "scene_2")
    assert scene2["breakdown"]["cast"] == 10000
    assert scene2["breakdown"]["costumes"] == 1500
    assert scene2["breakdown"]["location"] == 8000
    assert scene2["breakdown"]["props"] == 1000
    assert scene2["breakdown"]["lighting"] == 3000
    assert scene2["total"] == 36500
    
    # Total Project Budget = 36000 + 36500 = 72500
    assert data["total"] == 72500
    assert data["category_totals"]["cast"] == 15000
    assert data["category_totals"]["costumes"] == 3000
    assert data["category_totals"]["location"] == 20000
    assert data["category_totals"]["props"] == 3000
    assert data["category_totals"]["lighting"] == 5500
