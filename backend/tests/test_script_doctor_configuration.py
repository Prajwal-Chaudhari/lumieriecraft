import pytest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock

from app.providers.llm.registry import get_llm_provider
from app.providers.llm.mock_provider import MockLLMProvider
from app.providers.llm.gemini_provider import GeminiLLMProvider
from app.services.script_doctor import ScriptDoctorService
from app.models.project import Project

@pytest.fixture
def clean_env():
    # Remove relevant environment variables for tests
    keys_to_remove = ["SCRIPT_WRITER_PROVIDER", "LLM_PROVIDER", "GEMINI_API_KEY"]
    old_env = {k: os.environ.get(k) for k in keys_to_remove}
    
    with patch("app.providers.llm.registry.load_dotenv"):
        for k in keys_to_remove:
            if k in os.environ:
                del os.environ[k]
        yield
        for k, v in old_env.items():
            if v is not None:
                os.environ[k] = v
            elif k in os.environ:
                del os.environ[k]

def test_missing_provider_raises_error(clean_env):
    with pytest.raises(ValueError, match="SCRIPT_WRITER_PROVIDER environment variable is not set"):
        get_llm_provider()

def test_invalid_provider_raises_error(clean_env):
    os.environ["SCRIPT_WRITER_PROVIDER"] = "invalid"
    with pytest.raises(ValueError, match="Invalid SCRIPT_WRITER_PROVIDER 'invalid'"):
        get_llm_provider()

def test_explicit_mock_resolves(clean_env):
    os.environ["SCRIPT_WRITER_PROVIDER"] = "mock"
    provider = get_llm_provider()
    assert isinstance(provider, MockLLMProvider)

def test_explicit_gemini_resolves(clean_env):
    os.environ["SCRIPT_WRITER_PROVIDER"] = "gemini"
    os.environ["GEMINI_API_KEY"] = "fake-key"
    provider = get_llm_provider()
    assert isinstance(provider, GeminiLLMProvider)

@pytest.mark.asyncio
async def test_gemini_missing_credentials_raises_error(clean_env):
    os.environ["SCRIPT_WRITER_PROVIDER"] = "gemini"
    # Do not set GEMINI_API_KEY
    provider = get_llm_provider()
    
    with pytest.raises(Exception, match="GEMINI_API_KEY environment variable is missing"):
        await provider.generate_json("test prompt", {})

@pytest.mark.asyncio
@patch("app.services.script_doctor.get_llm_provider")
async def test_script_doctor_passes_actual_source_material(mock_get_provider, clean_env):
    # Setup mock provider that tracks prompt
    class TrackingMockProvider:
        def __init__(self):
            self.received_prompt = None
            
        async def generate_json(self, prompt, schema):
            self.received_prompt = prompt
            # Return valid mock schema so validation passes
            return {
                "title": "A Title",
                "scenes": [
                    {
                        "id": "scene_1",
                        "scene_number": 1,
                        "heading": "INT. ROOM - DAY",
                        "location": "ROOM",
                        "time_of_day": "DAY",
                        "description": "desc",
                        "characters": [{"name": "JOHN"}],
                        "actions": [{"text": "He enters"}],
                        "dialogue": [{"character": "JOHN", "text": "Hello"}],
                        "metadata": {}
                    }
                ]
            }
            
    tracker = TrackingMockProvider()
    mock_get_provider.return_value = tracker
    
    project = Project(
        id="test-id",
        name="Test Project",
        genre="Drama",
        tone="Serious",
        visual_style="Dark",
        story_idea="Old idea",
        source_material="TITLE: THE SILENT TRAIN\n\nINT. ABANDONED TRAIN STATION - DAWN\n\nMIRA stands alone beside a broken clock.\n\nMIRA\nThe train should have arrived yesterday."
    )
    
    service = ScriptDoctorService()
    await service.standardize_screenplay(project)
    
    assert "THE SILENT TRAIN" in tracker.received_prompt
    assert "MIRA stands alone" in tracker.received_prompt

@pytest.mark.asyncio
@patch("app.services.script_doctor.get_llm_provider")
async def test_invalid_gemini_json_rejected(mock_get_provider, clean_env):
    class BadJSONProvider:
        async def generate_json(self, prompt, schema):
            return {"title": "Title", "scenes": [{"id": "scene_1"}]}
            
    mock_get_provider.return_value = BadJSONProvider()
    
    project = Project(
        id="test-id",
        name="Test",
        genre="Drama",
        tone="Serious",
        visual_style="Dark",
        story_idea="Idea"
    )
    
    service = ScriptDoctorService()
    
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        await service.standardize_screenplay(project)
        
    assert excinfo.value.status_code == 422
    assert "LLM generated invalid scene data" in excinfo.value.detail

@pytest.mark.asyncio
async def test_no_hardcoded_mock_for_gemini(clean_env):
    os.environ["SCRIPT_WRITER_PROVIDER"] = "gemini"
    os.environ["GEMINI_API_KEY"] = "fake-key"
    
    project = Project(
        id="test-id",
        name="Test",
        genre="Drama",
        tone="Serious",
        visual_style="Dark",
        story_idea="Idea",
        source_material="Some unique script"
    )
    
    with patch("app.providers.llm.gemini_provider.GeminiLLMProvider.generate_json", new_callable=AsyncMock) as mock_generate_json:
        # Simulate a real response
        mock_generate_json.return_value = {
            "title": "REAL GEMINI OUTPUT",
            "scenes": [
                {
                    "id": "s1",
                    "scene_number": 1,
                    "heading": "INT. ROOM - DAY",
                    "location": "ROOM",
                    "time_of_day": "DAY",
                    "description": "desc",
                    "characters": [{"name": "A"}],
                    "actions": [{"text": "acts"}],
                    "dialogue": [{"character": "A", "text": "says"}],
                    "metadata": {}
                }
            ]
        }
        
        service = ScriptDoctorService()
        result = await service.standardize_screenplay(project)
        
        assert result["title"] != "THE LAST LIGHT (MOCK)"
        assert result["title"] == "REAL GEMINI OUTPUT"
