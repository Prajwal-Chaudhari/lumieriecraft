import pytest
import os
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.schemas.generation import GenerationRequest
from app.providers.registry import ProviderRegistry
from app.providers.pixazo_provider import PixazoProvider
from app.providers.fal_provider import FalProvider
from app.services.asset_resolver import LocalToDataURIResolver, URLProviderAsset
from app.models.project import CharacterAsset
from app.services.image_generation_service import ImageGenerationService, UnsupportedFeatureError

@pytest.mark.asyncio
async def test_asset_resolver_url():
    resolver = LocalToDataURIResolver()
    asset = CharacterAsset(
        project_id="test",
        character_name="Test",
        file_path="https://example.com/image.png",
        source="user_upload"
    )
    resolved = await resolver.resolve(asset)
    assert isinstance(resolved, URLProviderAsset)
    assert resolved.get_url() == "https://example.com/image.png"
    
@pytest.mark.asyncio
async def test_provider_capability_routing():
    registry = ProviderRegistry()
    with patch("os.getenv", side_effect=lambda k, d=None: "fake_key" if k in ["PIXAZO_API_KEY", "FAL_KEY"] else d):
        registry.register("pixazo", PixazoProvider())
        registry.register("fal", FalProvider(api_key="fake_key"))
        
    image_service = ImageGenerationService(registry)
    
    # Valid Fal request with references
    req = GenerationRequest(
        project_id="p1", scene_id="s1", shot_id="sh1", prompt="test", mode="storyboard_sketch",
        reference_images=["http://example.com/ref.png"]
    )
    
    # Should not throw validation error because Fal supports references
    with patch.object(registry, 'get', return_value=registry.get("fal")):
        fal_provider = registry.get("fal")
        fal_provider.generate = AsyncMock()
        await image_service.generate(req)
        fal_provider.generate.assert_called_once()
        
@pytest.mark.asyncio
async def test_unsupported_reference_rejected_by_pixazo():
    registry = ProviderRegistry()
    # Mock OS environ if needed
    os.environ["PIXAZO_API_KEY"] = "fake_key"
    pixazo = PixazoProvider()
    registry.register("pixazo", pixazo)
    image_service = ImageGenerationService(registry)
    
    req = GenerationRequest(
        project_id="p1", scene_id="s1", shot_id="sh1", prompt="test", mode="storyboard_sketch",
        reference_images=["http://example.com/ref.png"]
    )
    
    with patch.object(registry, 'get', return_value=registry.get("pixazo")):
        with pytest.raises(UnsupportedFeatureError, match="does not support reference images"):
            await image_service.generate(req)

@pytest.mark.asyncio
async def test_fal_flux_pulid_request_construction():
    with patch("os.getenv", return_value="fake_key"):
        provider = FalProvider(api_key="fake_key")
        
    req = GenerationRequest(
        project_id="p1", scene_id="s1", shot_id="sh1", prompt="A cinematic shot", mode="storyboard_sketch",
        reference_images=["http://example.com/ref1.png"],
        model="fal-ai/flux-pulid",
        seed=1234
    )
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"images": [{"url": "http://example.com/out.png"}], "request_id": "r1", "seed": 1234}
        mock_post.return_value = mock_resp
        
        result = await provider.generate(req)
        
        assert result.provider == "fal"
        assert result.model == "fal-ai/flux-pulid"
        assert result.image_urls == ["http://example.com/out.png"]
        
        # Verify payload construction
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["prompt"] == "A cinematic shot"
        assert call_kwargs["json"]["reference_image_url"] == "http://example.com/ref1.png"
        assert "reference_images" not in call_kwargs["json"] # Ensure it used the single-image payload
        assert call_kwargs["json"]["seed"] == 1234
        
@pytest.mark.asyncio
async def test_fal_pulid_request_construction():
    with patch("os.getenv", return_value="fake_key"):
        provider = FalProvider(api_key="fake_key")
        
    req = GenerationRequest(
        project_id="p1", scene_id="s1", shot_id="sh1", prompt="A cinematic shot", mode="storyboard_sketch",
        reference_images=["http://example.com/ref1.png", "http://example.com/ref2.png"],
        model="fal-ai/pulid"
    )
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"images": [{"url": "http://example.com/out.png"}], "request_id": "r1"}
        mock_post.return_value = mock_resp
        
        result = await provider.generate(req)
        
        assert result.provider == "fal"
        assert result.model == "fal-ai/pulid"
        
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["prompt"] == "A cinematic shot"
        # Ensure it used the multiple-image payload
        assert call_kwargs["json"]["reference_images"] == [
            {"image_url": "http://example.com/ref1.png"}, 
            {"image_url": "http://example.com/ref2.png"}
        ]
        assert "reference_image_url" not in call_kwargs["json"]
