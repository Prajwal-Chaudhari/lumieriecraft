import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from sqlmodel import SQLModel, Session, create_engine, select
from app.models.project import Project
from app.models.script import Script
from app.models.production import CharacterBible, WorldBible, SceneBreakdown
from app.services.production_intelligence import ProductionIntelligenceService
import uuid

# Ensure we use Gemini instead of Mock
os.environ["SCRIPT_WRITER_PROVIDER"] = "gemini"

sqlite_url = "sqlite:///acceptance_test.db"
test_engine = create_engine(sqlite_url)

def setup_db():
    SQLModel.metadata.create_all(test_engine)

async def run_test():
    setup_db()
    
    with Session(test_engine) as session:
        # Create a test project for THE SILENT TRAIN
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            name="THE SILENT TRAIN Acceptance Test",
            story_idea="A silent train station where Mira waits.",
            genre="Drama",
            duration="Short",
            tone="Quiet",
            visual_style="Muted, dawn lighting"
        )
        session.add(project)
        
        # Create an approved test script
        script_id = str(uuid.uuid4())
        scene_1_id = str(uuid.uuid4())
        script = Script(
            id=script_id,
            project_id=project.id,
            version=1,
            title="The Silent Train",
            status="approved",
            scenes=[
                {
                    "id": scene_1_id,
                    "scene_number": 1,
                    "heading": "EXT. RURAL TRAIN STATION - DAWN",
                    "location": "RURAL TRAIN STATION",
                    "time_of_day": "DAWN",
                    "description": "MIRA waits beside a broken station clock. A red suitcase rests on the bench.",
                    "actions": [
                        {"id": str(uuid.uuid4()), "text": "Mira checks her watch."}
                    ],
                    "dialogue": []
                }
            ]
        )
        session.add(script)
        session.commit()
        session.refresh(script)
        
        print("1. Running Production Intelligence Global Extraction...")
        prod_service = ProductionIntelligenceService()
        
        # Verify idempotency by running twice
        for iteration in range(1, 3):
            print(f"   [Iteration {iteration}] Extracting Global Bibles...")
            global_result = await prod_service.extract_global_bibles(session, script)
            
            chars_in_db = session.exec(select(CharacterBible).where(CharacterBible.project_id == project_id)).all()
            worlds_in_db = session.exec(select(WorldBible).where(WorldBible.project_id == project_id)).all()
            
            print(f"   -> Characters extracted: {len(global_result.characters)} (DB count: {len(chars_in_db)})")
            for char in global_result.characters:
                print(f"      - {char.name}")
                print(f"        Established: {char.established_facts}")
                print(f"        Inferred: {char.inferred_facts}")
                
            print(f"   -> Locations extracted: {len(global_result.locations)} (DB count: {len(worlds_in_db)})")
            for loc in global_result.locations:
                print(f"      - {loc.name}")
                print(f"        Established: {loc.established_facts}")
                print(f"        Inferred: {loc.inferred_facts}")

            print(f"   [Iteration {iteration}] Running Scene Breakdown for Scene 1...")
            from app.models.script import Scene
            first_scene = Scene.model_validate(script.scenes[0])
            breakdown_result = await prod_service.analyze_scene_for_production(session, script, first_scene, global_result)
            
            breakdowns_in_db = session.exec(select(SceneBreakdown).where(SceneBreakdown.project_id == project_id)).all()
            
            print(f"   -> Scene Breakdown: {breakdown_result.location} ({breakdown_result.time_of_day}) (DB count: {len(breakdowns_in_db)})")
            print(f"      Props: {breakdown_result.props}")
            print(f"      Emotional Beat: {breakdown_result.emotional_beat}")
            print(f"      Narrative Purpose: {breakdown_result.narrative_purpose}")
            print(f"      Inference Provenance: {breakdown_result.inference_provenance}")

        print("\n2. Verifications:")
        print("   - Idempotency test passed if DB count remained 1 for the relevant entities across iterations.")
        
        # Verify script unchanged
        session.refresh(script)
        scene_heading = script.scenes[0]["heading"]
        print(f"   - Script unchanged verification: Heading is '{scene_heading}' (Expected: EXT. RURAL TRAIN STATION - DAWN)")
        if scene_heading == "EXT. RURAL TRAIN STATION - DAWN":
            print("   - SUCCESS: Script is unchanged.")
        else:
            print("   - FAILURE: Script was changed!")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY must be set to run acceptance test.")
    else:
        asyncio.run(run_test())
