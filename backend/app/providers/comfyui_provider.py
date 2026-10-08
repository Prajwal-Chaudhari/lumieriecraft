import os
import uuid
import json
import asyncio
import httpx
import base64
import mimetypes
from typing import Optional, Dict, Any
from app.providers.base import ImageGenerationProvider
from app.schemas.generation import GenerationRequest, GenerationResult
from app.schemas.capabilities import ModelCapabilities

class ComfyUIProvider(ImageGenerationProvider):
    def __init__(self):
        self.base_url = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188")
        self.model_name = os.getenv("COMFYUI_MODEL", "v1-5-pruned-emaonly.safetensors") # Default to standard SD 1.5

    @classmethod
    def get_capabilities(cls) -> ModelCapabilities:
        return ModelCapabilities(
            supports_seed=True,
            supports_negative_prompt=True,
            supports_reference_images=True, # IPAdapter workflow added
            supports_control_images=False,   # Could be added with ControlNet workflow
            supports_img2img=False
        )

    async def _upload_image_to_comfyui(self, image_path_or_url: str) -> str:
        """Uploads an image to ComfyUI and returns the filename."""
        import tempfile
        
        file_data = None
        filename = f"lumiere_{uuid.uuid4().hex[:8]}.png"
        
        if image_path_or_url.startswith("data:"):
            # It's a Data URI
            header, encoded = image_path_or_url.split(",", 1)
            file_data = base64.b64decode(encoded)
        elif image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
            # It's a remote URL
            async with httpx.AsyncClient() as client:
                resp = await client.get(image_path_or_url)
                resp.raise_for_status()
                file_data = resp.content
        else:
            # It's a local file path
            if os.path.exists(image_path_or_url):
                with open(image_path_or_url, "rb") as f:
                    file_data = f.read()
            else:
                # If it's just a filename that might already exist in ComfyUI, just return it
                return image_path_or_url
                
        if not file_data:
            raise Exception("Failed to read image data for IP-Adapter reference.")
            
        async with httpx.AsyncClient() as client:
            files = {"image": (filename, file_data, "image/png")}
            resp = await client.post(f"{self.base_url}/upload/image", files=files)
            resp.raise_for_status()
            result = resp.json()
            return result.get("name", filename)

    def _build_workflow(self, prompt: str, negative_prompt: str, seed: int, width: int, height: int, uploaded_ref_image: Optional[str] = None) -> Dict[str, Any]:
        """Builds a basic SD 1.5 / SDXL ComfyUI workflow, optionally with IPAdapter"""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 7,
                    "denoise": 1,
                    "latent_image": [ "5", 0 ],
                    "model": [ "4", 0 ], # Default directly from CheckpointLoader
                    "negative": [ "7", 0 ],
                    "positive": [ "6", 0 ],
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "seed": seed,
                    "steps": 25
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": self.model_name
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": height,
                    "width": width
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": [ "4", 1 ],
                    "text": prompt
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": [ "4", 1 ],
                    "text": negative_prompt if negative_prompt else "text, watermark, ugly, deformed"
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": [ "3", 0 ],
                    "vae": [ "4", 2 ]
                }
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "Lumierecraft",
                    "images": [ "8", 0 ]
                }
            }
        }
        
        # Inject IP-Adapter nodes if reference image exists
        if uploaded_ref_image:
            workflow["10"] = {
                "class_type": "IPAdapterUnifiedLoader",
                "inputs": {
                    "model": ["4", 0],
                    "preset": "LIGHT - SD1.5 only (low strength)"
                }
            }
            workflow["11"] = {
                "class_type": "LoadImage",
                "inputs": {
                    "image": uploaded_ref_image
                }
            }
            workflow["12"] = {
                "class_type": "IPAdapter",
                "inputs": {
                    "model": ["10", 0],
                    "ipadapter": ["10", 1],
                    "image": ["11", 0],
                    "weight": 0.7,
                    "noise": 0.1,
                    "start_at": 0.0,
                    "end_at": 1.0,
                    "weight_type": "linear"
                }
            }
            # Change KSampler to use IP-Adapter model output
            workflow["3"]["inputs"]["model"] = ["12", 0]
            
        return workflow

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        seed = request.seed if request.seed is not None else 42
        width = request.width or 512
        height = request.height or 512
        
        uploaded_ref = None
        if request.reference_images and len(request.reference_images) > 0:
            uploaded_ref = await self._upload_image_to_comfyui(request.reference_images[0])
        
        workflow = self._build_workflow(request.prompt, request.negative_prompt or "", seed, width, height, uploaded_ref)
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 1. Submit the prompt
            payload = {"prompt": workflow}
            try:
                response = await client.post(f"{self.base_url}/prompt", json=payload)
                response.raise_for_status()
            except httpx.RequestError as e:
                raise Exception(f"Failed to connect to ComfyUI at {self.base_url}. Is it running? Error: {e}")
            
            prompt_id = response.json().get("prompt_id")
            if not prompt_id:
                raise Exception("ComfyUI did not return a prompt_id")
                
            # 2. Poll for completion
            while True:
                await asyncio.sleep(2)
                hist_response = await client.get(f"{self.base_url}/history/{prompt_id}")
                hist_data = hist_response.json()
                
                if prompt_id in hist_data:
                    # Job finished!
                    outputs = hist_data[prompt_id].get("outputs", {})
                    # Find the SaveImage node output (node "9")
                    if "9" in outputs and "images" in outputs["9"]:
                        image_info = outputs["9"]["images"][0]
                        filename = image_info["filename"]
                        subfolder = image_info.get("subfolder", "")
                        folder_type = image_info.get("type", "output")
                        
                        image_url = f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
                        
                        return GenerationResult(
                            provider="comfyui",
                            model=self.model_name,
                            generation_id=prompt_id,
                            image_urls=[image_url],
                            seed=seed,
                            metadata={"prompt": request.prompt, "prompt_id": prompt_id}
                        )
                    else:
                        raise Exception("ComfyUI finished but no image output was found in node 9.")
