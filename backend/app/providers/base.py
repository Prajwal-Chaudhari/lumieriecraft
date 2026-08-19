from abc import ABC, abstractmethod
from app.schemas.generation import GenerationRequest, GenerationResult
from app.schemas.capabilities import ModelCapabilities

class ImageGenerationProvider(ABC):
    """Base interface for all image generation providers."""
    
    @classmethod
    @abstractmethod
    def get_capabilities(cls) -> ModelCapabilities:
        """Return the capabilities supported by this provider."""
        ...
        
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generates an image based on the request."""
        ...
