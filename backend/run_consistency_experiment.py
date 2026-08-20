import asyncio
import os
import json
import uuid
from typing import List

# Setup environment before loading app modules
os.environ["IMAGE_GENERATION_PROVIDER"] = "pixazo"

from app.models.project import Project, CharacterAsset
from app.models.production import ProductionPlan, ProductionScene, ShotBlueprint
from app.services.storyboard_agent import StoryboardAgentService
from app.services.asset_resolver import LocalToDataURIResolver
from app.providers.registry import ProviderRegistry
from app.schemas.generation import GenerationRequest

async def run_experiment():
    print("Initializing Phase 5 Consistency Experiment...")
    
    project = Project(
        id=str(uuid.uuid4()),
        name="Consistency Baseline Test",
        story_idea="Testing consistency across methods.",
        genre="Drama",
        duration="Short",
        tone="Serious",
        visual_style="Cinematic"
    )
    
    scene = {
        "id": "scene_1",
        "scene_number": 1,
        "location": "CAFE",
        "time_of_day": "NIGHT",
        "characters": [{"name": "RAHUL"}]
    }
    
    # In a real environment, this file must exist or be passed. 
    # For now, we stub it to a fake file to ensure the resolver logic works.
    char_asset = CharacterAsset(
        project_id=project.id,
        character_name="RAHUL",
        file_path="https://pub-582b7213209642b9b995c96c95a30381.r2.dev/flux-schnell-cf/prompt-1787232071659-670427.png",
        source="user_upload"
    )
    characters = [char_asset]
    
    shots = [
        ShotBlueprint(
            id="shot_1", project_id=project.id, production_plan_id="plan_1", scene_id="scene_1", shot_id="shot_1",
            shot_size="Wide Shot", camera={"angle": "Eye Level"}, blocking={"subject_position": "Center"},
            lighting={"setup": "High contrast", "direction": "Side"}, subject="RAHUL",
            character_actions="Sitting alone", story_beat="Establishing isolation", emotion="Melancholy", purpose="", status="PENDING"
        ),
        ShotBlueprint(
            id="shot_2", project_id=project.id, production_plan_id="plan_1", scene_id="scene_1", shot_id="shot_2",
            shot_size="Medium Shot", camera={"angle": "Slight Low Angle"}, blocking={"subject_position": "Center right"},
            lighting={"setup": "High contrast", "direction": "Side"}, subject="RAHUL",
            character_actions="Looking off camera", story_beat="Reacting to voice", emotion="Surprised", purpose="", status="PENDING"
        ),
        ShotBlueprint(
            id="shot_3", project_id=project.id, production_plan_id="plan_1", scene_id="scene_1", shot_id="shot_3",
            shot_size="Close-up", camera={"angle": "Eye Level"}, blocking={"subject_position": "Center"},
            lighting={"setup": "Soft", "direction": "Frontal"}, subject="RAHUL",
            character_actions="Speaking", story_beat="Dialogue delivery", emotion="Determined", purpose="", status="PENDING"
        ),
        ShotBlueprint(
            id="shot_4", project_id=project.id, production_plan_id="plan_1", scene_id="scene_1", shot_id="shot_4",
            shot_size="Medium Close-Up", camera={"angle": "Profile"}, blocking={"subject_position": "Left side"},
            lighting={"setup": "Silhouette", "direction": "Backlit"}, subject="RAHUL",
            character_actions="Turning away", story_beat="Rejection", emotion="Sad", purpose="", status="PENDING"
        ),
        ShotBlueprint(
            id="shot_5", project_id=project.id, production_plan_id="plan_1", scene_id="scene_1", shot_id="shot_5",
            shot_size="Medium Shot", camera={"angle": "High Angle"}, blocking={"subject_position": "Center"},
            lighting={"setup": "Harsh", "direction": "Top"}, subject="RAHUL",
            character_actions="Looking up", story_beat="Realization", emotion="Shocked", purpose="", status="PENDING"
        )
    ]
    
    methods = [
        {"name": "Method A (Baseline)", "provider": "pixazo", "model": "flux-1-schnell"},
        {"name": "Method B (FLUX-PuLID)", "provider": "fal", "model": "fal-ai/flux-pulid"},
        {"name": "Method C (PuLID)", "provider": "fal", "model": "fal-ai/pulid"}
    ]
    
    registry = ProviderRegistry()
    agent = StoryboardAgentService() # Defaults to using registry
    resolver = LocalToDataURIResolver()
    
    results = {m["name"]: [] for m in methods}
    
    print("Notice: Generation calls are stubbed in the FalProvider.")
    
    for method in methods:
        print(f"\n--- Running {method['name']} ---")
        agent.image_service.registry.get = lambda name=None, m=method: registry.get(m["provider"])
        
        for shot in shots:
            print(f"  Generating {shot.shot_size} ({shot.camera.get('angle', '')})...")
            
            # Resolve character references if this method supports them
            resolved_chars = []
            provider_instance = registry.get(method["provider"])
            capabilities = provider_instance.get_capabilities()
            
            if capabilities.supports_reference_images:
                for c in characters:
                    try:
                        resolved = await resolver.resolve(c)
                        # We temporarily attach the resolved URL to the file_path so the agent picks it up
                        c.file_path = resolved.get_url()
                        resolved_chars.append(c)
                    except Exception as e:
                        print(f"    Warning: Failed to resolve asset {c.file_path}: {e}")
            else:
                # Baseline - no references
                # The agent passes them to GenerationRequest but the provider validates and ignores or errors
                # Wait, our ImageGenerationService raises UnsupportedFeatureError if we pass reference images and it's not supported.
                # So for Method A, we must NOT pass reference images to the agent, or we clear them out.
                pass

            # If Method A, pass empty characters to ensure no references are used
            chars_to_pass = characters if capabilities.supports_reference_images else []

            try:
                # We monkey-patch the agent to force the model name into the GenerationRequest
                original_generate = agent.image_service.generate
                
                async def patched_generate(req: GenerationRequest):
                    req.model = method["model"]
                    return await original_generate(req)
                    
                agent.image_service.generate = patched_generate
                
                frame = await agent.generate_storyboard(shot, scene, chars_to_pass, project, 1)
                results[method["name"]].append(frame.image_url)
                
                agent.image_service.generate = original_generate
                print(f"    Success: {frame.generation_id}")
            except Exception as e:
                print(f"    Error: {e}")
                results[method["name"]].append(f"ERROR: {e}")
                
    # Output markdown grid
    print("\n--- Output Grid ---")
    
    md = "# Phase 5 Consistency Experiment Results\n\n"
    md += "| Method | Shot 1 (Wide) | Shot 2 (Med Low) | Shot 3 (CU) | Shot 4 (Profile Backlit) | Shot 5 (Med High) |\n"
    md += "|---|---|---|---|---|---|\n"
    
    for method in methods:
        row = f"| **{method['name']}** | "
        urls = results[method["name"]]
        for url in urls:
            if url.startswith("ERROR"):
                row += f"`{url}` | "
            else:
                row += f"![]({url}) | "
        md += row + "\n"
        
    with open("experiment_results.md", "w") as f:
        f.write(md)
        
    print("Results saved to experiment_results.md")

if __name__ == "__main__":
    asyncio.run(run_experiment())
