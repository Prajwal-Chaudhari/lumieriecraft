import os
import sys
import json
import asyncio
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Make sure we're using the actual environment vars which use Gemini
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.db import get_session
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

# Use real test DB for isolated testing
sqlite_url = "sqlite:///test_acceptance.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
SQLModel.metadata.create_all(engine)

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

client = TestClient(app)

def run_test():
    print("--- 1. CREATING PROJECT ---")
    source_material = """
    Rahul is sitting in a cafe at night.
    It is raining outside.
    His father calls him.
    His father tells Rahul to come home.
    Rahul becomes emotional but does not answer.
    He looks outside and remembers something from his childhood.
    """
    
    project_payload = {
        "name": "Acceptance Test",
        "story_idea": "",
        "source_material": source_material.strip(),
        "genre": "Drama",
        "duration": "Short Film",
        "tone": "Emotional",
        "visual_style": "Cinematic, dark, rainy"
    }
    
    res = client.post("/api/projects", json=project_payload)
    assert res.status_code == 200, res.text
    project = res.json()
    project_id = project["id"]
    print(f"Project created with ID: {project_id}")
    
    print("--- 2. ANALYZING SCRIPT (Calling Gemini) ---")
    res = client.post(f"/api/projects/{project_id}/script/analyze")
    assert res.status_code == 200, res.text
    script = res.json()
    
    print(f"Script title: {script['title']}")
    scenes = script["scenes"]
    print(f"Generated {len(scenes)} scenes.")
    
    for i, s in enumerate(scenes):
        print(f"Scene {i+1}: {s['heading']} (ID: {s['id']})")
        print(f"Desc: {s['description']}")
        
    scene_id = scenes[0]["id"]
    original_scene = scenes[0]
    
    print("--- 3. PROPOSING ENHANCEMENT (Calling Gemini) ---")
    instruction = "Make the scene more emotionally tense and cinematic while preserving the existing story."
    res = client.post(f"/api/projects/{project_id}/script/scenes/{scene_id}/propose", json={"instructions": instruction})
    assert res.status_code == 200, res.text
    proposal = res.json()["proposed_scene"]
    
    print(f"Proposed Scene ID: {proposal['id']}")
    print(f"Proposed Desc: {proposal['description']}")
    
    assert proposal["id"] == original_scene["id"], "Scene ID must be preserved"
    assert proposal["scene_number"] == original_scene["scene_number"], "Scene number must be preserved"
    
    # Verify DB is unchanged
    res = client.get(f"/api/projects/{project_id}/script")
    current_script = res.json()
    assert current_script["scenes"][0]["description"] == original_scene["description"], "DB should not be modified on propose"
    
    print("--- 4. APPLYING ENHANCEMENT ---")
    res = client.post(f"/api/projects/{project_id}/script/scenes/{scene_id}/apply", json={"scene": proposal})
    assert res.status_code == 200, res.text
    
    res = client.get(f"/api/projects/{project_id}/script")
    current_script = res.json()
    assert current_script["scenes"][0]["description"] == proposal["description"], "DB should be updated after apply"
    
    print("--- 5. REJECTING ENHANCEMENT (Propose without apply) ---")
    instruction2 = "Add a random alien invasion."
    res = client.post(f"/api/projects/{project_id}/script/scenes/{scene_id}/propose", json={"instructions": instruction2})
    assert res.status_code == 200, res.text
    
    res = client.get(f"/api/projects/{project_id}/script")
    current_script2 = res.json()
    assert current_script2["scenes"][0]["description"] == proposal["description"], "DB should not change if proposal is rejected (not applied)"
    
    print("--- ALL TESTS COMPLETED SUCCESSFULLY ---")

if __name__ == "__main__":
    run_test()
