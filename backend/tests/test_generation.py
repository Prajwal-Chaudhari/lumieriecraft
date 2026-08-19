import pytest
import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.schemas.generation import GenerationRequest
from app.schemas.capabilities import ModelCapabilities
from app.providers.registry import ProviderRegistry
from app.providers.mock_provider import MockImageGenerationProvider
from app.services.image_generation_service import ImageGenerationService, UnsupportedFeatureError
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def base_request():
    return GenerationRequest(
        project_id="p1",
        scene_id="s1",
        shot_id="shot1",
        prompt="A cinematic view of a futuristic city",
        mode="storyboard_sketch"
    )

def test_provider_registry():
    registry = ProviderRegistry()
    mock_provider = MockImageGenerationProvider()
    
    registry.register("mock", mock_provider)
    
    # Should resolve "mock" by explicitly requesting it
    assert registry.get("mock") is mock_provider
    
    # Should resolve "mock" by environment variable fallback
    os.environ["IMAGE_GENERATION_PROVIDER"] = "mock"
    assert registry.get() is mock_provider
    
    with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
        registry.get("nonexistent")

def test_capability_validation_success(base_request):
    registry = ProviderRegistry()
    service = ImageGenerationService(registry)
    
    # Mock Provider supports everything
    capabilities = ModelCapabilities(
        supports_seed=True,
        supports_negative_prompt=True,
        supports_reference_images=True,
        supports_control_images=True
    )
    
    base_request.seed = 123
    base_request.negative_prompt = "ugly"
    base_request.reference_images = ["ref.jpg"]
    base_request.control_images = ["ctrl.jpg"]
    
    # Should not raise
    service._validate_capabilities(base_request, capabilities)

def test_capability_validation_failure(base_request):
    registry = ProviderRegistry()
    service = ImageGenerationService(registry)
    
    capabilities = ModelCapabilities(
        supports_seed=False,
        supports_negative_prompt=False,
        supports_reference_images=False,
        supports_control_images=False
    )
    
    base_request.seed = 123
    with pytest.raises(UnsupportedFeatureError, match="not support seeds"):
        service._validate_capabilities(base_request, capabilities)
        
    base_request.seed = None
    base_request.negative_prompt = "bad"
    with pytest.raises(UnsupportedFeatureError, match="not support negative prompts"):
        service._validate_capabilities(base_request, capabilities)

@pytest.mark.asyncio
async def test_image_generation_service_orchestration(base_request):
    registry = ProviderRegistry()
    mock_provider = MockImageGenerationProvider()
    registry.register("mock", mock_provider)
    
    service = ImageGenerationService(registry)
    
    # Test successful generation
    os.environ["IMAGE_GENERATION_PROVIDER"] = "mock"
    result = await service.generate(base_request)
    
    assert result.provider == "mock"
    assert len(result.image_urls) == 1
    assert result.image_urls[0] == "/static/mock/storyboard-placeholder.svg"

@pytest.mark.asyncio
async def test_image_generation_service_error_handling(base_request):
    registry = ProviderRegistry()
    failing_provider = AsyncMock()
    failing_provider.get_capabilities.return_value = ModelCapabilities()
    failing_provider.generate.side_effect = Exception("API Timeout")
    
    registry.register("failing", failing_provider)
    service = ImageGenerationService(registry)
    
    os.environ["IMAGE_GENERATION_PROVIDER"] = "failing"
    
    with pytest.raises(RuntimeError, match="Image generation failed: API Timeout"):
        await service.generate(base_request)

def test_pixazo_missing_key(monkeypatch):
    monkeypatch.delenv("PIXAZO_API_KEY", raising=False)
    from app.providers.pixazo_provider import PixazoProvider
    with pytest.raises(ValueError, match="PIXAZO_API_KEY is not set"):
        PixazoProvider()

def test_pixazo_capabilities(monkeypatch):
    monkeypatch.setenv("PIXAZO_API_KEY", "dummy")
    from app.providers.pixazo_provider import PixazoProvider
    provider = PixazoProvider()
    caps = provider.get_capabilities()
    assert not caps.supports_seed
    assert not caps.supports_negative_prompt
    assert not caps.supports_reference_images
    assert not caps.supports_control_images

@pytest.mark.asyncio
async def test_pixazo_reference_rejection(base_request, monkeypatch):
    monkeypatch.setenv("PIXAZO_API_KEY", "dummy")
    from app.providers.pixazo_provider import PixazoProvider
    from app.providers.registry import ProviderRegistry
    from app.services.image_generation_service import ImageGenerationService, UnsupportedFeatureError
    
    registry = ProviderRegistry()
    service = ImageGenerationService(registry)
    os.environ["IMAGE_GENERATION_PROVIDER"] = "pixazo"
    
    base_request.reference_images = ["ref1.jpg"]
    
    with pytest.raises(UnsupportedFeatureError, match="not support reference images"):
        service._validate_capabilities(base_request, registry.get("pixazo").get_capabilities())

@pytest.mark.asyncio
async def test_pixazo_success_mocked(base_request, monkeypatch):
    monkeypatch.setenv("PIXAZO_API_KEY", "dummy")
    from app.providers.pixazo_provider import PixazoProvider
    provider = PixazoProvider()
    
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json = json_data
            self.status_code = status_code
        def json(self): return self._json
        def raise_for_status(self): pass

    class MockAsyncClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            return MockResponse({"request_id": "test_req_123"})
        async def get(self, url, **kwargs):
            return MockResponse({
                "status": "COMPLETED",
                "output": {"media_url": ["https://pixazo/img.png"]}
            })

    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
    
    import asyncio
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    result = await provider.generate(base_request)
    assert result.provider == "pixazo"
    assert result.model == "flux-1-schnell"
    assert result.image_urls == ["https://pixazo/img.png"]
