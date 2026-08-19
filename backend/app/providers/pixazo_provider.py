import os
import uuid
import httpx
import asyncio
import time
from app.providers.base import ImageGenerationProvider
from app.schemas.generation import GenerationRequest, GenerationResult
from app.schemas.capabilities import ModelCapabilities

class PixazoProvider(ImageGenerationProvider):
    def __init__(self):
        self.api_key = os.getenv("PIXAZO_API_KEY")
        if not self.api_key:
            raise ValueError("PIXAZO_API_KEY is not set")
        
        self.model_name = "flux-1-schnell"
        self.submit_url = f"https://gateway.pixazo.ai/{self.model_name}/v1/getData"
        self.status_url_base = "https://gateway.pixazo.ai/v2/requests/status"

    @classmethod
    def get_capabilities(cls) -> ModelCapabilities:
        return ModelCapabilities(
            supports_seed=False,
            supports_negative_prompt=False,
            supports_reference_images=False,
            supports_control_images=False,
            supports_img2img=False
        )

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if request.reference_images and len(request.reference_images) > 1:
            raise ValueError("Pixazo Provider only supports a maximum of 1 reference image.")

        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": request.prompt
        }
        
        if request.reference_images:
            payload["image_url"] = request.reference_images[0]

        async with httpx.AsyncClient() as client:
            try:
                submit_resp = await client.post(self.submit_url, headers=headers, json=payload, timeout=120.0)
                submit_resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Pixazo submission failed with status {e.response.status_code}") from e
            except httpx.RequestError as e:
                raise RuntimeError(f"Network error during Pixazo submission: {str(e)}") from e

            submit_data = submit_resp.json()
            
            # Check if API returned synchronously
            if "output" in submit_data and isinstance(submit_data["output"], str):
                return GenerationResult(
                    provider="pixazo",
                    model=self.model_name,
                    generation_id=str(uuid.uuid4()),
                    image_urls=[submit_data["output"]],
                    seed=None,
                    metadata={"prompt": request.prompt}
                )

            request_id = submit_data.get("request_id")
            if not request_id:
                raise RuntimeError(f"Pixazo API did not return a request_id. Response: {submit_data}")

            status_url = f"{self.status_url_base}/{request_id}"
            max_attempts = 30
            poll_interval = 2.0
            
            for attempt in range(max_attempts):
                await asyncio.sleep(poll_interval)
                try:
                    status_resp = await client.get(status_url, headers=headers, timeout=120.0)
                    status_resp.raise_for_status()
                except httpx.HTTPError as e:
                    raise RuntimeError(f"Pixazo status polling failed: {str(e)}") from e
                
                status_data = status_resp.json()
                status = status_data.get("status")
                
                if status == "COMPLETED":
                    output = status_data.get("output", {})
                    media_urls = output.get("media_url", [])
                    if not media_urls:
                        raise RuntimeError("Pixazo API returned COMPLETED but no media_url")
                        
                    return GenerationResult(
                        provider="pixazo",
                        model=self.model_name,
                        generation_id=request_id,
                        image_urls=media_urls,
                        seed=None,
                        metadata={"prompt": request.prompt}
                    )
                elif status == "ERROR" or status == "FAILED":
                    err_msg = status_data.get("error", "Unknown Pixazo generation error")
                    raise RuntimeError(f"Pixazo generation failed: {err_msg}")
            
            raise RuntimeError(f"Pixazo generation timed out after {max_attempts * poll_interval} seconds.")
