import uuid
import asyncio
from app.providers.base import ImageGenerationProvider
from app.schemas.generation import GenerationRequest, GenerationResult
from app.schemas.capabilities import ModelCapabilities

class MockImageGenerationProvider(ImageGenerationProvider):
    def __init__(self, delay: float = 1.0):
        self.delay = delay

    @classmethod
    def get_capabilities(cls) -> ModelCapabilities:
        # Mock provider supports everything for testing
        return ModelCapabilities(
            supports_seed=True,
            supports_negative_prompt=True,
            supports_reference_images=True,
            supports_control_images=True,
            supports_img2img=True
        )

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        generation_id = str(uuid.uuid4())
        
        # Valid frontend-testable static asset
        placeholder_url = "/static/mock/storyboard-placeholder.svg"

        return GenerationResult(
            provider="mock",
            model="mock-diffusion-v1",
            generation_id=generation_id,
            image_urls=[placeholder_url],
            seed=request.seed or 42,
            metadata={
                "mocked": True,
                "prompt": request.prompt
            }
        )
