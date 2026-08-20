import os
import json
from typing import Optional, Dict, Any
from app.schemas.generation import GenerationRequest, GenerationResult
from app.schemas.capabilities import ModelCapabilities
from app.providers.base import ImageGenerationProvider

class FalProvider(ImageGenerationProvider):
    """
    Provider for Fal.ai models.
    Supports both `fal-ai/flux-pulid` and `fal-ai/pulid`.
    Expects reference images as provider-accessible URLs or data URIs.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FAL_KEY")
        
    @classmethod
    def get_capabilities(cls) -> ModelCapabilities:
        # Since we use this provider for our consistency experiments, 
        # it advertises support for reference images and face identity.
        return ModelCapabilities(
            supports_seed=True,
            supports_negative_prompt=False, # Generally not supported on FLUX without special pipelines
            supports_reference_images=True,
            supports_multiple_reference_images=True,
            supports_face_identity=True,
            supports_control_images=False,
            supports_ip_adapter=True,
            supports_controlnet=True,
            supports_img2img=True
        )

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.api_key:
            raise ValueError("FAL_KEY is not set.")
            
        import httpx
        
        # Decide which Fal endpoint to call based on the number of references or explicit config.
        # If the user specifically wants pulid vs flux-pulid, we could inspect request.metadata or 
        # assume flux-pulid for 1 reference and pulid for multiple.
        # But for the experiment framework, we might have it configured externally.
        # We will assume a default mapping for this stub.
        
        # We'll use a specific model name if passed, otherwise default to fal-ai/flux-pulid
        model_endpoint = getattr(request, "model", None) or "fal-ai/flux-pulid"
        
        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if model_endpoint == "fal-ai/flux-pulid":
            # flux-pulid payload
            # Requires `prompt` and `reference_image_url`
            payload = {
                "prompt": request.prompt,
                "reference_image_url": request.reference_images[0] if request.reference_images else None,
                "image_size": {
                    "width": request.width,
                    "height": request.height
                },
                "num_images": 1
            }
            if request.seed is not None:
                payload["seed"] = request.seed
                
        elif model_endpoint == "fal-ai/pulid":
            # pulid payload
            # Expects multiple reference images
            payload = {
                "prompt": request.prompt,
                "reference_images": [{"image_url": img} for img in request.reference_images],
                "image_size": {
                    "width": request.width,
                    "height": request.height
                },
                "num_images": 1
            }
            if request.seed is not None:
                payload["seed"] = request.seed
        else:
            raise ValueError(f"Unsupported model endpoint for FalProvider: {model_endpoint}")

        # The actual API call is stubbed out for now to prevent accidental credit spend.
        # When ready for real experiments, we will enable this.
        
        # Stub response:
        # return GenerationResult(
        #     provider="fal",
        #     model=model_endpoint,
        #     generation_id="stub_id",
        #     image_urls=["http://example.com/stub.png"],
        #     seed=request.seed
        # )
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"https://queue.fal.run/{model_endpoint}",
                headers=headers,
                json=payload
            )
            
            if resp.status_code != 200:
                raise Exception(f"Fal.ai API error ({resp.status_code}): {resp.text}")
                
            data = resp.json()
            images = data.get("images", [])
            image_urls = [img.get("url") for img in images]
            seed = data.get("seed", request.seed)
            
            return GenerationResult(
                provider="fal",
                model=model_endpoint,
                generation_id=data.get("request_id", "unknown"),
                image_urls=image_urls,
                seed=seed,
                metadata={"fal_raw": data}
            )
