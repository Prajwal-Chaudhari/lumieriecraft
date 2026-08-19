import pytest
import os
from unittest.mock import patch, AsyncMock
from app.providers.llm.gemini_provider import GeminiLLMProvider

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key", "GEMINI_MODEL": "test-model"}):
        yield

@pytest.mark.asyncio
async def test_gemini_generate_json(mock_env):
    with patch("app.providers.llm.gemini_provider.genai.Client") as MockClient:
        # Create a mock response
        mock_response = AsyncMock()
        mock_response.text = '{"scenes": [{"heading": "EXT. MOUNTAIN - DAY", "description": "Snowy peak.", "scene_number": 1, "actions": [], "dialogue": []}]}'
        
        # Setup the mock client
        mock_client_instance = MockClient.return_value
        mock_client_instance.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        provider = GeminiLLMProvider()
        
        schema = {"type": "object", "properties": {"scenes": {"type": "array"}}}
        
        result = await provider.generate_json("Write a scene about a mountain.", schema)
        
        assert "scenes" in result
        assert len(result["scenes"]) == 1
        assert result["scenes"][0]["heading"] == "EXT. MOUNTAIN - DAY"
        
        # Verify the generate_content call
        mock_client_instance.aio.models.generate_content.assert_called_once()
        kwargs = mock_client_instance.aio.models.generate_content.call_args.kwargs
        assert kwargs["model"] == "test-model"
        assert kwargs["contents"] == "Write a scene about a mountain."
        assert kwargs["config"].response_mime_type == "application/json"
        assert "You are a master screenwriter" in kwargs["config"].system_instruction

@pytest.mark.asyncio
async def test_gemini_missing_api_key():
    with patch.dict(os.environ, clear=True):
        # We need to catch it on initialization or generate_json
        # The constructor does not raise, but generate_json checks os.getenv again (or fails if client creation fails)
        # Actually, genai.Client() without api_key and without GOOGLE_API_KEY env might raise an error during init.
        # Let's test that it handles missing key gracefully.
        
        with pytest.raises(Exception):
            provider = GeminiLLMProvider()
            await provider.generate_json("test", {})
