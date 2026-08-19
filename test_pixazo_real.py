import os
import sys
import asyncio


from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# Allow imports from backend/
sys.path.insert(0, os.path.abspath("backend"))


from app.schemas.generation import GenerationRequest
from app.services.image_generation_service import ImageGenerationService
from app.providers.registry import ProviderRegistry




async def test_real():
    print("Initializing full pipeline...")


    # Ensure Pixazo is selected before resolving the provider
    os.environ["IMAGE_GENERATION_PROVIDER"] = "pixazo"


    registry = ProviderRegistry()
    service = ImageGenerationService(registry)


    print("Creating GenerationRequest...")


    req = GenerationRequest(
        project_id="test_p",
        scene_id="test_s",
        shot_id="test_shot",
        prompt=(
            "A single red apple on a white table, "
            "cinematic studio lighting, highly detailed"
        ),
        mode="storyboard_sketch"
    )


    print("Generating image via ImageGenerationService...")


    result = await service.generate(req)


    print("\nSuccess!")
    print(f"Generation ID: {result.generation_id}")
    print(f"Provider: {result.provider}")
    print(f"Model: {result.model}")
    print(f"Image URLs: {result.image_urls}")


    print("\nPIXAZO REAL PROVIDER VERIFIED")




if __name__ == "__main__":
    asyncio.run(test_real())
