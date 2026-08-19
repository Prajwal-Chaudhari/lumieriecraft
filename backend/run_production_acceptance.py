import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
import json
from sqlmodel import SQLModel, Session, create_engine
from app.db import engine, get_session
from app.models.project import Project
from app.models.script import Script
from app.services.script_writer import ScriptWriterService
from app.services.production_intelligence import ProductionIntelligenceService

# Ensure we use Gemini instead of Mock
os.environ["SCRIPT_WRITER_PROVIDER"] = "gemini"

# Using a test DB for safety
sqlite_url = "sqlite:///acceptance_test.db"
test_engine = create_engine(sqlite_url)

def setup_db():
    SQLModel.metadata.create_all(test_engine)

async def run_test():
    setup_db()
    
    with Session(test_engine) as session:
        # Create a test project using Rahul Cafe scenario
        project = Project(
            name="Rahul Cafe Acceptance Test",
            story_idea="Rahul is a stressed cafe owner in Mumbai. His espresso machine breaks during the morning rush. He tries to fix it but fails. A mysterious customer helps him.",
            genre="Drama",
            duration="Short",
            tone="Realistic",
            visual_style="Gritty, warm lighting"
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        
        print("1. Generating Script...")
        script_service = ScriptWriterService()
        script_data = await script_service.analyze_script(project)
        
        script = Script(
            project_id=project.id,
            version=1,
            title=script_data["title"],
            scenes=script_data["scenes"]
        )
        session.add(script)
        session.commit()
        session.refresh(script)
        print(f"-> Script generated with {len(script.scenes)} scenes.")

        print("2. Running Production Intelligence Global Extraction...")
        prod_service = ProductionIntelligenceService()
        global_result = await prod_service.extract_global_bibles(script)
        
        print(f"-> Characters extracted: {len(global_result.characters)}")
        for char in global_result.characters:
            print(f"  - {char.name}: {char.appearance}")
            print(f"    Established: {char.established_facts}")
            print(f"    Proposed: {char.proposed_facts}")
            
        print(f"-> Locations extracted: {len(global_result.locations)}")
        for loc in global_result.locations:
            print(f"  - {loc.name}: {loc.description}")
            print(f"    Lighting: {loc.lighting_characteristics}")

        print("3. Running Scene Breakdown for Scene 1...")
        from app.models.script import Scene
        first_scene = Scene.model_validate(script.scenes[0])
        breakdown_result = await prod_service.analyze_scene_for_production(first_scene, global_result)
        
        print(f"-> Scene Breakdown: {breakdown_result.location} ({breakdown_result.time_of_day})")
        print(f"   Characters: {breakdown_result.characters}")
        print(f"   Emotional Beat: {breakdown_result.emotional_beat}")
        print(f"   Narrative Purpose: {breakdown_result.narrative_purpose}")
        
        print("4. Generating Cinematography Shot Blueprint for Scene 1...")
        from app.models.production import SceneBreakdown
        mock_breakdown = SceneBreakdown(
            production_plan_id="test",
            scene_id=first_scene.id,
            scene_number=first_scene.scene_number,
            location=breakdown_result.location,
            time_of_day=breakdown_result.time_of_day,
            characters=breakdown_result.characters,
            actions=breakdown_result.actions,
            dialogue_summary=breakdown_result.dialogue_summary,
            props=breakdown_result.props,
            emotional_beat=breakdown_result.emotional_beat,
            narrative_purpose=breakdown_result.narrative_purpose,
            continuity_notes=breakdown_result.continuity_notes
        )
        cinematography_result = await prod_service.generate_cinematography(mock_breakdown, global_result)
        
        print(f"-> Shots Generated: {len(cinematography_result.shots)}")
        for shot in cinematography_result.shots:
            print(f"  - {shot.shot_size} | {shot.camera_angle} | {shot.lens}")
            print(f"    Purpose: {shot.purpose}")
            print(f"    Beat: {shot.story_beat}")
            print(f"    Lighting: {shot.lighting}")
            print(f"    Movement: {shot.camera_movement}")
            print(f"    Emotion: {shot.emotion}\n")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY must be set to run acceptance test.")
    else:
        asyncio.run(run_test())
