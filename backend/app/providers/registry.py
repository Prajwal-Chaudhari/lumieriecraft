from app.providers.base import ImageGenerationProvider
from app.providers.mock_provider import MockImageGenerationProvider
import os

class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, ImageGenerationProvider] = {}
        self.register("mock", MockImageGenerationProvider())
        
        # Attempt to register HuggingFace if key exists
        if os.getenv("HUGGINGFACE_API_TOKEN"):
            try:
                from app.providers.huggingface_provider import HuggingFaceProvider
                self.register("huggingface", HuggingFaceProvider())
            except Exception:
                pass

        # Attempt to register Pixazo if key exists
        if os.getenv("PIXAZO_API_KEY"):
            try:
                from app.providers.pixazo_provider import PixazoProvider
                self.register("pixazo", PixazoProvider())
            except Exception:
                pass

        # Attempt to register Fal if key exists
        if os.getenv("FAL_KEY"):
            try:
                from app.providers.fal_provider import FalProvider
                self.register("fal", FalProvider())
            except Exception:
                pass

    def register(self, name: str, provider: ImageGenerationProvider):
        self._providers[name] = provider

    def get(self, provider_name: str | None = None) -> ImageGenerationProvider:
        name = provider_name or os.getenv("IMAGE_GENERATION_PROVIDER", "mock")
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not found in registry.")
        return self._providers[name]
