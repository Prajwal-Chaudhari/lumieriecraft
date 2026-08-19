import asyncio
from sqlmodel import Session, create_engine, SQLModel
from app.models.project import Project
from app.models.script import Script, Scene
from app.models.production import ProductionPlan, SceneBreakdown, ShotBlueprint, CharacterBible, WorldBible, StoryboardFrame
from app.services.storyboard_agent import StoryboardAgentService
from app.services.image_generation_service import ImageGenerationService
from app.providers.registry import ProviderRegistry
from app.schemas.generation import GenerationResult
from unittest.mock import AsyncMock

async def run_e2e():
    engine = create_engine("sqlite:///./test.db")
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # 1. Setup mock data
        project = Project(name="E2E Storyboard Test", story_idea="A space western", genre="Sci-Fi", duration="Feature", tone="Dark", visual_style="Gritty")
        session.add(project)
        session.commit()
        
        script = Script(project_id=project.id, version=1, title="Test Script", content="Ext. MARS - DAY", scenes=[])
        session.add(script)
        session.commit()
        
        plan = ProductionPlan(project_id=project.id, script_id=script.id, script_version=script.version)
        session.add(plan)
        session.commit()
        
        breakdown = SceneBreakdown(
            production_plan_id=plan.id,
            scene_id="scene_1",
            scene_number=1,
            location="Mars Surface",
            time_of_day="DAY"
        )
        session.add(breakdown)
        session.commit()
        
        shot = ShotBlueprint(
            production_plan_id=plan.id,
            scene_breakdown_id=breakdown.id,
            scene_id="scene_1",
            shot_id="shot_1",
            purpose="Establish setting",
            story_beat="Opening",
            shot_size="Wide Shot",
            camera_angle="Eye Level",
            lens="24mm",
            lighting="Harsh sunlight",
            subject="Dust blowing across red rocks",
            visual_prompt="A sweeping wide shot of the martian surface."
        )
        session.add(shot)
        session.commit()
        
        # 2. Run the StoryboardAgentService
        registry = ProviderRegistry()
        mock_pixazo = AsyncMock()
        mock_pixazo.name = "pixazo"
        mock_pixazo.generate.return_value = GenerationResult(
            provider="pixazo",
            model="default",
            generation_id="gen-1234",
            image_urls=["https://pixazo.test/fake.jpg"],
            prompt="A sweeping wide shot of the martian surface.",
            metadata={"seed": 1234}
        )
        
        # Add capabilities
        from app.schemas.capabilities import ModelCapabilities
        mock_pixazo.get_capabilities.return_value = ModelCapabilities(
            supports_negative_prompt=True,
            supports_seed=True,
            supports_reference_images=False,
            supports_control_images=False,
            supports_lora=False
        )
        registry.register("pixazo", mock_pixazo)
        
        image_service = ImageGenerationService(registry)
        storyboard_service = StoryboardAgentService(image_service)
        
        frame = await storyboard_service.generate_storyboard(
            shot=shot,
            scene=breakdown,
            characters=[],
            world=None,
            project=project,
            script_version=1
        )
        
        session.add(frame)
        session.commit()
        
        # 3. Verify
        print(f"Storyboard frame generated: {frame.id}")
        print(f"Image URL: {frame.image_url}")
        print(f"Prompt used:\n{frame.prompt}")
        print(f"Metadata:\n{frame.generation_metadata}")
        
        frames_in_db = session.query(StoryboardFrame).count()
        print(f"Total frames in DB: {frames_in_db}")

if __name__ == "__main__":
    asyncio.run(run_e2e())
