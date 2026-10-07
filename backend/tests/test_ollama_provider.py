import pytest
import os
import json
from unittest.mock import patch, AsyncMock
from openai import APIConnectionError
import httpx
from app.providers.llm.ollama_provider import OllamaLLMProvider

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"OLLAMA_MODEL": "qwen3:8b", "OLLAMA_BASE_URL": "http://localhost:11434"}):
        yield

@pytest.mark.asyncio
async def test_ollama_initialization(mock_env):
    with patch("app.providers.llm.ollama_provider.AsyncOpenAI") as MockClient:
        provider = OllamaLLMProvider()
        assert provider.model == "qwen3:8b"
        assert provider.base_url == "http://localhost:11434/v1"
        assert provider.client == MockClient.return_value

@pytest.mark.asyncio
async def test_ollama_generate_json_valid(mock_env):
    with patch("app.providers.llm.ollama_provider.AsyncOpenAI") as MockClient:
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"scenes": [{"heading": "INT. ROOM - DAY", "description": "A sunny room."}]}'))
        ]
        
        mock_client_instance = MockClient.return_value
        mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        
        provider = OllamaLLMProvider()
        # override client with our mock
        provider.client = mock_client_instance
        
        schema = {"type": "object", "properties": {"scenes": {"type": "array"}}}
        
        result = await provider.generate_json("Write a scene about a room.", schema)
        
        assert "scenes" in result
        assert len(result["scenes"]) == 1
        assert result["scenes"][0]["heading"] == "INT. ROOM - DAY"
        
        mock_client_instance.chat.completions.create.assert_called_once()
        kwargs = mock_client_instance.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "qwen3:8b"
        assert kwargs["response_format"] == {"type": "json_object"}
        assert "Write a scene about a room." in kwargs["messages"][1]["content"]
        assert "You are an expert AI assistant" in kwargs["messages"][0]["content"]
        
        # Test parameters
        assert kwargs["temperature"] == 0.6
        assert kwargs["max_completion_tokens"] == 4096
        assert kwargs["extra_body"] == {"options": {"thinking": False}}

@pytest.mark.asyncio
async def test_ollama_generate_json_malformed(mock_env):
    with patch("app.providers.llm.ollama_provider.AsyncOpenAI") as MockClient:
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='not a json string'))
        ]
        
        mock_client_instance = MockClient.return_value
        mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        
        provider = OllamaLLMProvider()
        provider.client = mock_client_instance
        
        with pytest.raises(Exception, match="Failed to parse JSON from Ollama API response"):
            await provider.generate_json("test", {})

@pytest.mark.asyncio
async def test_ollama_unavailable_error(mock_env):
    with patch("app.providers.llm.ollama_provider.AsyncOpenAI") as MockClient:
        mock_client_instance = MockClient.return_value
        # Simulate connection error
        mock_client_instance.chat.completions.create = AsyncMock(
            side_effect=APIConnectionError(request=httpx.Request("POST", "http://localhost:11434/v1/chat/completions"))
        )
        
        provider = OllamaLLMProvider()
        provider.client = mock_client_instance
        
        with pytest.raises(Exception, match="The local Ollama service could not be reached at http://localhost:11434/v1. Please ensure Ollama is running."):
            await provider.generate_json("test", {})

@pytest.mark.asyncio
async def test_ollama_different_inputs(mock_env):
    with patch("app.providers.llm.ollama_provider.AsyncOpenAI") as MockClient:
        from unittest.mock import MagicMock
        mock_client_instance = MockClient.return_value
        
        async def mock_create(**kwargs):
            prompt = kwargs["messages"][1]["content"]
            response_content = '{"title": "Scene A"}' if "Input A" in prompt else '{"title": "Scene B"}'
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content=response_content))]
            return mock_response
            
        mock_client_instance.chat.completions.create = AsyncMock(side_effect=mock_create)
        
        provider = OllamaLLMProvider()
        provider.client = mock_client_instance
        
        result1 = await provider.generate_json("Input A", {})
        result2 = await provider.generate_json("Input B", {})
        
        assert result1["title"] == "Scene A"
        assert result2["title"] == "Scene B"

# Connectivity Diagnostic Test (can be run with a special marker or just checked)
@pytest.mark.asyncio
@pytest.mark.skipif(os.environ.get("RUN_OLLAMA_DIAGNOSTIC") != "1", reason="Requires local Ollama running")
async def test_ollama_diagnostic_connectivity():
    # Real test against local ollama without mocking
    provider = OllamaLLMProvider()
    schema = {"type": "object", "properties": {"status": {"type": "string"}}}
    
    # We expect this to either succeed or throw the connection error handled in generate_json
    try:
        result = await provider.generate_json("Respond with a JSON object: {\"status\": \"ok\"}", schema)
        assert result.get("status") == "ok"
    except Exception as e:
        pytest.fail(f"Ollama diagnostic failed: {e}")
