import os
import sys
from dotenv import load_dotenv
load_dotenv()
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("backend"))
from app.main import app

client = TestClient(app)

print("Running Pixazo Integrity Test...")
os.environ["IMAGE_GENERATION_PROVIDER"] = "pixazo"

req = {
    "project_id": "test_p",
    "scene_id": "test_s",
    "shot_id": "test_shot",
    "prompt": "LUMIERECRAFT_API_INTEGRITY_TEST_UNIQUE_2026",
    "mode": "storyboard_sketch"
}

resp = client.post("/api/generations", json=req)
print(resp.json())
