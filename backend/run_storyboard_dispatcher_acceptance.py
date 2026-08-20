import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.storyboard_agent import StoryboardAgentService
from app.models.production import ShotBlueprint, ProductionPlan
from app.models.project import Project, CharacterAsset

async def main():
    load_dotenv()
    if not os.environ.get("PIXAZO_API_KEY"):
        print("PIXAZO_API_KEY is not set. Please set it in .env to run this test.")
        return

    print("\n--- PHASE 4: STORYBOARD DISPATCHER ACCEPTANCE TEST ---\n")

    # 1. Setup Mock Data (simulating approved upstream data)
    project = Project(id="proj_1", name="Acceptance Project", story_idea="Acceptance test", genre="Drama", duration="Short", tone="Emotional", visual_style="Cinematic")
    
    scene = {
        "id": "scene_1",
        "scene_number": 1,
        "heading": "INT. CAFE - NIGHT",
        "location": "CAFE",
        "time_of_day": "NIGHT",
        "description": "Rahul sits alone.",
        "characters": [{"name": "RAHUL"}],
        "actions": [{"text": "Rahul stares out the window."}],
        "dialogue": [
            {"character": "FATHER", "parenthetical": "V.O.", "text": "Come home, beta."},
            {"character": "RAHUL", "text": "I can't."}
        ]
    }
    
    shot = ShotBlueprint(
        id="shot_1",
        production_plan_id="plan_1",
        scene_id="scene_1",
        shot_id="shot_1",
        purpose="Establish location and isolation",
        story_beat="Rahul replies 'I can't.'",
        shot_size="Medium Close-Up",
        camera={
            "angle": "Eye Level",
            "focal_length_mm": 50,
            "movement": "Static"
        },
        blocking={
            "subject_position": "Center right",
            "gaze_direction": "Looking away"
        },
        composition={
            "rule_of_thirds": True,
            "negative_space": "Left side"
        },
        lighting={
            "setup": "Rembrandt",
            "direction": "Side lighting",
            "intensity": "High contrast"
        },
        subject="Rahul",
        emotion="Melancholy"
    )
    
    characters = [
        CharacterAsset(
            id="char_1",
            project_id="proj_1",
            character_name="RAHUL",
            file_path="https://example.com/rahul.jpg", # Fake reference
            source="user_upload"
        )
    ]
    
    script_version = 2
    
    # 2. Instantiate Dispatcher
    service = StoryboardAgentService()
    
    # 3. Generation 1
    print("Dispatching Generation 1...")
    frame_1 = await service.generate_storyboard(shot, scene, characters, project, script_version)
    
    print("\n[Variant 1]")
    print(f"Status: {frame_1.status}")
    print(f"Image URL: {frame_1.image_url}")
    print(f"Prompt Used:\n{frame_1.prompt}\n")
    
    assert "Black-and-white storyboard sketch" in frame_1.prompt, "Failed to include B&W style"
    assert frame_1.image_url.startswith("http"), "Failed to generate image URL"
    assert frame_1.scene_id == "scene_1"
    assert frame_1.shot_id == "shot_1"
    
    # 4. Generation 2 (Regenerate)
    print("Dispatching Generation 2 (Regenerate)...")
    frame_2 = await service.generate_storyboard(shot, scene, characters, project, script_version)
    
    print("\n[Variant 2]")
    print(f"Status: {frame_2.status}")
    print(f"Image URL: {frame_2.image_url}")
    print(f"Prompt Used:\n{frame_2.prompt}\n")
    
    assert frame_1.generation_id != frame_2.generation_id, "Regeneration did not create a new variant ID"
    assert frame_2.image_url.startswith("http"), "Failed to generate second image URL"
    
    print("\n✅ Verification Successful: Storyboard Dispatcher created valid, independent B&W variants while preserving authoritative lineage.")

if __name__ == "__main__":
    asyncio.run(main())
