import asyncio
import os
import sys

# Ensure backend directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlmodel import Session
from app.db import engine, create_db_and_tables
from app.models.project import Project
from app.models.script import Script
from app.services.cinematographer import CinematographerService
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Force Gemini instead of mock for this acceptance test
os.environ["LLM_PROVIDER"] = "gemini"

async def run_acceptance():
    print("Running Cinematography Acceptance Test with Gemini...")
    create_db_and_tables()
    
    with Session(engine) as session:
        # Create dummy project
        project = Project(
            name="Cinematography Acceptance",
            story_idea="An acceptance test story idea.",
            genre="Sci-Fi",
            duration="Feature",
            tone="Dark",
            visual_style="Cyberpunk"
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        
        # Create an approved script based on the user's rough prompt (simulated post-Script Doctor)
        script = Script(
            project_id=project.id,
            version=1,
            title="The Last Light",
            scenes=[
                {
                    "id": "scene_1",
                    "scene_number": 1,
                    "heading": "INT. CAFE - NIGHT",
                    "location": "CAFE",
                    "time_of_day": "NIGHT",
                    "description": "Rain hits the window. Rahul sits alone at a corner table, staring into a half-empty coffee cup. His phone buzzes.",
                    "actions": [{"text": "He looks at the caller ID. It says 'Dad'."}],
                    "dialogue": [
                        {"character": "RAHUL", "text": "Hello, Dad."}
                    ]
                },
                {
                    "id": "scene_2",
                    "scene_number": 1, # CONTINUOUS
                    "heading": "INT. CAFE - NIGHT - CONTINUOUS",
                    "location": "CAFE",
                    "time_of_day": "NIGHT",
                    "description": "Through the phone, his father's voice sounds distant and tired.",
                    "actions": [{"text": "Rahul listens."}],
                    "dialogue": [
                        {"character": "FATHER", "parenthetical": "V.O.", "text": "Come home, beta."},
                        {"character": "RAHUL", "text": "I can't."}
                    ],
                    "actions": [{"text": "Rahul gets emotional. He looks outside at the rain, remembering something."}]
                }
            ],
            status="approved"
        )
        session.add(script)
        session.commit()
        session.refresh(script)

        # Initialize the service
        service = CinematographerService()
        
        print("\n--- Sending script to Cinematographer & Colorist Agent ---")
        try:
            plan = await service.propose_cinematography(project.id, script)
            
            print("\n--- CINEMATOGRAPHY PLAN GENERATED ---")
            for scene in plan.scenes:
                print(f"\nSCENE: {scene.scene_id}")
                print(f"Visual Goal: {scene.visual_goal}")
                print(f"Overall Mood: {scene.overall_mood}")
                
                print("\nCOLOR PLAN:")
                print(f"Temp: {scene.color_plan.temperature_kelvin}K, Contrast: {scene.color_plan.contrast}, Saturation: {scene.color_plan.saturation}")
                if scene.color_plan.lut:
                    print(f"LUT: {scene.color_plan.lut.name} ({scene.color_plan.lut.reason})")
                print("Palette:")
                for c in scene.color_plan.palette:
                    print(f"  - {c.role}: {c.hex} ({c.description})")
                
                print("\nSHOTS:")
                for shot in scene.shots:
                    print(f"\n  Shot ID: {shot.shot_id}")
                    print(f"  Size: {shot.shot_size}")
                    print(f"  Camera: Angle {shot.camera.angle if shot.camera else 'N/A'}, Lens {shot.camera.focal_length_mm if shot.camera else 'N/A'}mm, Movement {shot.camera.movement if shot.camera else 'STATIC'}")
                    print(f"  Purpose: {shot.purpose}")
                    print(f"  Beat: {shot.story_beat}")
                    if shot.composition:
                        print(f"  Composition: Rule of thirds {shot.composition.rule_of_thirds}, Symmetry {shot.composition.symmetry}")
                    if shot.lighting:
                        print(f"  Lighting: {shot.lighting.setup}")
            
            print("\n\nAcceptance Test Completed Successfully.")
        except Exception as e:
            print(f"Failed during generation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_acceptance())
