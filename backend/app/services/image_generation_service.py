from app.schemas.generation import GenerationRequest, GenerationResult
from app.providers.registry import ProviderRegistry

class UnsupportedFeatureError(ValueError):
    pass

class ImageGenerationService:
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def _validate_capabilities(self, request: GenerationRequest, capabilities) -> None:
        if request.seed is not None and not capabilities.supports_seed:
            raise UnsupportedFeatureError("The selected provider does not support seeds.")
        
        if request.negative_prompt and not capabilities.supports_negative_prompt:
            raise UnsupportedFeatureError("The selected provider does not support negative prompts.")
            
        if request.reference_images and not capabilities.supports_reference_images:
            raise UnsupportedFeatureError("The selected provider does not support reference images.")
            
        if request.control_images and not capabilities.supports_control_images:
            raise UnsupportedFeatureError("The selected provider does not support control images.")

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            # 1. Provider selection
            provider = self.registry.get()
            
            # 2. Capability validation
            capabilities = provider.get_capabilities()
            self._validate_capabilities(request, capabilities)
            
            # 3. Generate
            result = await provider.generate(request)
            
            # 4. Normalized result returned
            return result
        except UnsupportedFeatureError:
            raise
        except Exception as e:
            # Explicit error normalization
            raise RuntimeError(f"Image generation failed: {str(e)}") from e
