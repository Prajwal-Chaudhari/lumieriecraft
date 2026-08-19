import os
import uuid
import httpx
from app.providers.base import ImageGenerationProvider
from app.schemas.generation import GenerationRequest, GenerationResult
from app.schemas.capabilities import ModelCapabilities

class HuggingFaceProvider(ImageGenerationProvider):
    def __init__(self):
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN")
        self.model_name = os.getenv("HF_IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
        if not self.api_token:
            raise ValueError("HUGGINGFACE_API_TOKEN is not set")

    @classmethod
    def get_capabilities(cls) -> ModelCapabilities:
        return ModelCapabilities(
            supports_seed=True,
            supports_negative_prompt=True,
            supports_reference_images=False,
            supports_control_images=False,
            supports_img2img=False
        )

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": request.prompt,
            "parameters": {}
        }
        
        if request.negative_prompt:
            payload["parameters"]["negative_prompt"] = request.negative_prompt
        if request.width:
            payload["parameters"]["width"] = request.width
        if request.height:
            payload["parameters"]["height"] = request.height
        if request.seed is not None:
            payload["parameters"]["seed"] = request.seed

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            
            if response.status_code != 200:
                raise RuntimeError(f"Hugging Face API failed: {response.text}")
                
            import base64
            b64_img = base64.b64encode(response.content).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{b64_img}"

            return GenerationResult(
                provider="huggingface",
                model=self.model_name,
                generation_id=str(uuid.uuid4()),
                image_urls=[data_uri],
                seed=request.seed,
                metadata={
                    "prompt": request.prompt
                }
            )
