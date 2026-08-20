import asyncio
import httpx
from pprint import pprint
import sys

BASE_URL = "http://localhost:8000/api"

async def main():
    async with httpx.AsyncClient() as client:
        print("1. Creating project with rough screenplay...")
        source_material = """int cafe night

rahul sits alone drinking coffee. rain outside.
his father calls him

RAHUL
hello dad

FATHER
come home beta

Rahul gets emotional. he looks outside.

then he remembers his childhood and his father."""

        # 1. Create a project
        resp = await client.post(f"{BASE_URL}/projects", json={
            "name": "Acceptance Test Project",
            "story_idea": "A short dramatic scene",
            "source_material": source_material,
            "genre": "Drama",
            "duration": "Short",
            "tone": "Emotional",
            "visual_style": "Cinematic"
        }, timeout=10.0)
        
        if resp.status_code != 200:
            print("Failed to create project:", resp.text)
            sys.exit(1)
            
        project = resp.json()
        project_id = project["id"]
        print(f"Project created: {project_id}")
        
        print("\n2. Fetching initial script (should be 404 or empty)...")
        resp = await client.get(f"{BASE_URL}/projects/{project_id}/script")
        initial_script = None
        if resp.status_code == 200:
            initial_script = resp.json()
            print(f"Initial script found, version {initial_script['version']}")
        else:
            print(f"Initial script fetch result: {resp.status_code}")
            
        print("\n3. Proposing standardization...")
        resp = await client.post(f"{BASE_URL}/projects/{project_id}/script/propose-standardization", timeout=60.0)
        if resp.status_code != 200:
            print("Failed to propose standardization:", resp.text)
            sys.exit(1)
            
        proposal = resp.json()
        proposal_id = proposal["id"]
        print(f"Proposal created: {proposal_id}")
        print("Base Version:", proposal["base_script_version"])
        print("Status:", proposal["status"])
        
        print("\n=== PROPOSAL SCRIPT ===")
        proposed = proposal["proposed_script"]
        print("Title:", proposed.get("title"))
        for scene in proposed.get("scenes", []):
            print(f"\nSCENE {scene['scene_number']}: {scene['heading']} - {scene['time_of_day']}")
            print("Desc:", scene['description'])
            for action in scene.get('actions', []):
                print(f"Action: {action['text']}")
            for line in scene.get('dialogue', []):
                print(f"{line['character']}: {line['text']}")
                
        print("\n4. Verifying canonical script is untouched...")
        resp = await client.get(f"{BASE_URL}/projects/{project_id}/script")
        if resp.status_code == 200:
            script_now = resp.json()
            if script_now.get("version", 0) == (initial_script.get("version", 0) if initial_script else 0):
                print("SUCCESS: Canonical script unchanged.")
            else:
                print(f"FAILURE: Canonical script changed to version {script_now.get('version')}")
        else:
            print("SUCCESS: Canonical script still not created/changed.")
            
        print("\n5. Applying the proposal...")
        resp = await client.post(f"{BASE_URL}/projects/{project_id}/script/proposals/{proposal_id}/apply", timeout=10.0)
        if resp.status_code != 200:
            print("Failed to apply proposal:", resp.text)
            sys.exit(1)
            
        applied_script = resp.json()
        print(f"Applied successfully. New version: {applied_script['version']}")
        
        print("\n6. Rejecting a dummy proposal to ensure no crash...")
        # We need another proposal to test reject
        resp = await client.post(f"{BASE_URL}/projects/{project_id}/script/propose-standardization", timeout=60.0)
        prop_2 = resp.json()
        resp = await client.post(f"{BASE_URL}/projects/{project_id}/script/proposals/{prop_2['id']}/reject", timeout=10.0)
        if resp.status_code == 200:
            print("Rejected successfully. Status:", resp.json()["status"])
        else:
            print("Failed to reject:", resp.text)

if __name__ == "__main__":
    asyncio.run(main())
