import os
import sys
from dotenv import load_dotenv
load_dotenv()
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("backend"))
from app.main import app

client = TestClient(app)

print("--- 1. Health ---")
print(client.get("/api/health").json())

print("--- 2. System Status ---")
print(client.get("/api/system/status").json())

print("--- 3. Providers ---")
print(client.get("/api/providers").json())

print("--- 4. Mock Generation ---")
mock_req = {
    "project_id": "test_p",
    "scene_id": "test_s",
    "shot_id": "test_shot",
    "prompt": "Mock test",
    "mode": "storyboard_sketch"
}
os.environ["IMAGE_GENERATION_PROVIDER"] = "mock"
print(client.post("/api/generations", json=mock_req).json())

print("--- 5. Static Asset ---")
svg_resp = client.get("/static/mock/storyboard-placeholder.svg")
print(f"Status: {svg_resp.status_code}, SVG Length: {len(svg_resp.text)}")

print("--- 6. Pixazo Generation ---")
if os.getenv("PIXAZO_API_KEY"):
    os.environ["IMAGE_GENERATION_PROVIDER"] = "pixazo"
    pixazo_req = mock_req.copy()
    pixazo_resp = client.post("/api/generations", json=pixazo_req)
    print(pixazo_resp.json())
else:
    print("Skipped (no key)")
