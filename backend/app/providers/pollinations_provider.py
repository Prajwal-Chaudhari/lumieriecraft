import uuid
import urllib.parse
from app.providers.base import ImageGenerationProvider
from app.schemas.generation import GenerationRequest, GenerationResult
from app.schemas.capabilities import ModelCapabilities

class PollinationsProvider(ImageGenerationProvider):
    def __init__(self):
        self.model_name = "pollinations-free"

    @classmethod
    def get_capabilities(cls) -> ModelCapabilities:
        return ModelCapabilities(
            supports_seed=True,
            supports_negative_prompt=False,
            supports_reference_images=False,
            supports_control_images=False,
            supports_img2img=False
        )

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        encoded_prompt = urllib.parse.quote(request.prompt)
        
        # Build the pollinations URL with optional seed and dimensions
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        params = ["nologo=true"]
        if request.seed is not None:
            params.append(f"seed={request.seed}")
        if request.width:
            params.append(f"width={request.width}")
        if request.height:
            params.append(f"height={request.height}")
            
        if params:
            url += "?" + "&".join(params)

        return GenerationResult(
            provider="pollinations",
            model=self.model_name,
            generation_id=str(uuid.uuid4()),
            image_urls=[url],
            seed=request.seed or 42,
            metadata={"prompt": request.prompt}
        )
