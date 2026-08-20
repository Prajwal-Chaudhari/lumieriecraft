from pydantic import BaseModel

class ModelCapabilities(BaseModel):
    supports_seed: bool = False
    supports_negative_prompt: bool = False
    supports_reference_images: bool = False
    supports_multiple_reference_images: bool = False
    supports_face_identity: bool = False
    supports_control_images: bool = False
    supports_ip_adapter: bool = False
    supports_controlnet: bool = False
    supports_img2img: bool = False
