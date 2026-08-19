import asyncio
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
import json
from sqlmodel import SQLModel, Session, create_engine
from app.db import engine, get_session
from app.models.project import Project
from app.models.script import Script
from app.models.production import SceneBreakdown, ProductionPlan, CharacterBible, WorldBible, ShotBlueprint
from app.services.script_writer import ScriptWriterService
from app.services.production_intelligence import ProductionIntelligenceService
from app.services.storyboard_agent import StoryboardAgentService
from app.services.image_generation_service import ImageGenerationService
from app.providers.registry import ProviderRegistry

# Ensure we use Gemini instead of Mock
os.environ["SCRIPT_WRITER_PROVIDER"] = "gemini"
os.environ["IMAGE_GENERATION_PROVIDER"] = "pixazo"
os.environ["PIXAZO_API_KEY"] = os.getenv("PIXAZO_API_KEY", "test-key-just-in-case")

# Using a test DB for safety
sqlite_url = "sqlite:///acceptance_storyboard_test.db"
test_engine = create_engine(sqlite_url)

def setup_db():
    SQLModel.metadata.create_all(test_engine)

async def run_test():
    setup_db()
    
    registry = ProviderRegistry()
    image_service = ImageGenerationService(registry)
    storyboard_service = StoryboardAgentService(image_service)
    
    with Session(test_engine) as session:
        # Create a test project using Rahul Cafe scenario
        project = Project(
            name="Rahul Cafe Storyboard Test",
            story_idea="Rahul is a stressed cafe owner in Mumbai. His espresso machine breaks during the morning rush. He tries to fix it but fails. A mysterious customer helps him.",
            genre="Drama",
            duration="Short",
            tone="Realistic",
            visual_style="Gritty, warm lighting, cinematic depth of field, anamorphic lenses"
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        
        print("1. Bypassing Gemini (503s) - Creating Mock Script and Production Data...")
        script = Script(
            project_id=project.id,
            version=1,
            title="Rahul Cafe Script",
            scenes=[
                {
                    "scene_number": 1,
                    "heading": "INT. RAHUL'S CAFE - MORNING",
                    "location": "RAHUL'S CAFE",
                    "time_of_day": "MORNING",
                    "description": "A bustling cafe in Bandra.",
                    "actions": [{"text": "Rahul struggles with the espresso machine."}],
                    "dialogue": []
                }
            ]
        )
        session.add(script)
        
        plan = ProductionPlan(
            project_id=project.id,
            script_id=script.id,
            script_version=script.version
        )
        session.add(plan)
        session.commit()
        session.refresh(script)
        session.refresh(plan)
        
        char = CharacterBible(
            production_plan_id=plan.id,
            name="Rahul",
            appearance="Sweaty forehead, shaking hands, burnt hand from hot pipe.",
            clothing="Casual cafe owner / barista attire"
        )
        session.add(char)
        chars = [char]
            
        world = WorldBible(
            production_plan_id=plan.id,
            name="Rahul's Cafe",
            environment="Bandra, Mumbai; ambient roar of city traffic combined with ceramic cup clatter and steam."
        )
        session.add(world)
        worlds = [world]
            
        session.commit()

        from app.models.script import Scene
        first_scene = Scene.model_validate(script.scenes[0])
        
        breakdown = SceneBreakdown(
            production_plan_id=plan.id,
            scene_id=first_scene.id,
            scene_number=first_scene.scene_number,
            location="Rahul's Cafe - Morning",
            time_of_day="Morning",
            characters=["Rahul"],
            actions=["Rahul struggles with the espresso machine."],
            dialogue_summary="",
            props=["espresso machine"],
            emotional_beat="Frantic, energetic",
            narrative_purpose="Establish the bustling environment",
            continuity_notes=""
        )
        session.add(breakdown)
        session.commit()
        session.refresh(breakdown)
        
        print("4. Generating Mock Shot Blueprint for Scene 1...")
        s = ShotBlueprint(
            production_plan_id=plan.id,
            scene_breakdown_id=breakdown.id,
            scene_id=first_scene.id,
            shot_id="shot_1",
            purpose="Establish the bustling, high-volume environment",
            story_beat="Frantic, energetic",
            shot_size="Wide Shot",
            camera_angle="Eye Level",
            lens="24mm Anamorphic",
            composition="Foreground blurred cafe customers, midground wooden counter with vintage brass espresso machine, background dust-moted windows with sunlight.",
            lighting="Golden morning sunlight streaming through windows, rich warm shadows, bright anamorphic lens flares.",
            camera_movement="Slow handheld drift across the counter",
            subject="Rahul and cafe interior",
            character_actions="Wide cinematic angle of a bustling Bandra cafe interior in morning sunlight, wooden counter, golden dust motes, vintage brass espresso machine smoking steam, crowds blurred in foreground, high dynamic range, warm photorealistic film look.",
            emotion="Frantic",
            visual_prompt=None
        )
        session.add(s)
        shots = [s]
        
        session.commit()
        
        print(f"5. Generated {len(shots)} shots. Taking Shot 1 to Storyboard Agent...")
        if shots:
            first_shot = shots[0]
            print(f"   Shot 1 details:")
            print(f"     Subject: {first_shot.subject}")
            print(f"     Size: {first_shot.shot_size}")
            print(f"     Angle: {first_shot.camera_angle}")
            print(f"     Lens: {first_shot.lens}")
            
            # Print the compiled prompt to inspect deterministic compilation
            context = storyboard_service.create_generation_context(
                shot=first_shot,
                scene=breakdown,
                characters=chars,
                world=worlds[0] if worlds else None,
                project=project
            )
            print("\n--- Compiled Prompt ---")
            print(context.final_prompt)
            print("-----------------------\n")
            
            print("6. Calling ImageGenerationService (Pixazo)...")
            try:
                frame = await storyboard_service.generate_storyboard(
                    shot=first_shot,
                    scene=breakdown,
                    characters=chars,
                    world=worlds[0] if worlds else None,
                    project=project,
                    script_version=script.version
                )
                print("   Success! Storyboard Frame generated.")
                print(f"   Provider: {frame.provider}")
                print(f"   Model: {frame.model}")
                print(f"   Status: {frame.status}")
                print(f"   Image URL: {frame.image_url}")
                print(f"   Prompt sent to model: {frame.prompt}")
            except Exception as e:
                print(f"   Error calling ImageGenerationService: {e}")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY must be set to run acceptance test.")
    else:
        asyncio.run(run_test())
