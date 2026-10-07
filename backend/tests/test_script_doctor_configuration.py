import pytest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock

from app.providers.llm.registry import get_llm_provider
from app.providers.llm.mock_provider import MockLLMProvider
from app.providers.llm.gemini_provider import GeminiLLMProvider
from app.services.script_doctor import ScriptDoctorService
from app.models.project import Project
from fastapi import HTTPException

@pytest.fixture
def clean_env():
    keys_to_remove = ["SCRIPT_WRITER_PROVIDER", "LLM_PROVIDER", "GEMINI_API_KEY", "OLLAMA_TEMPERATURE", "OLLAMA_MAX_TOKENS", "OLLAMA_DISABLE_THINKING"]
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

def test_explicit_mock_resolves(clean_env):
    os.environ["SCRIPT_WRITER_PROVIDER"] = "mock"
    provider = get_llm_provider()
    assert isinstance(provider, MockLLMProvider)

@pytest.mark.asyncio
async def test_regex_scene_detection():
    service = ScriptDoctorService()
    text = "Some intro text.\n\nINT. ROOM - DAY\nAction.\nEXT. HOUSE - NIGHT\nMore action."
    scenes = service._split_by_regex(text)
    
    assert len(scenes) == 3
    assert scenes[0] == "Some intro text.\n\n"
    assert scenes[1].startswith("INT. ROOM")
    assert scenes[2].startswith("EXT. HOUSE")
    assert "".join(scenes) == text

@pytest.mark.asyncio
@patch("app.services.script_doctor.get_llm_provider")
async def test_script_doctor_sequential_processing(mock_get_provider, clean_env):
    class TrackingMockProvider:
        def __init__(self):
            self.prompts = []
            
        async def generate_json(self, prompt, schema):
            self.prompts.append(prompt)
            # Return valid mock schema so validation passes
            return {
                "id": "mock",
                "scene_number": 1,
                "heading": "int. room - day",
                "location": "ROOM",
                "time_of_day": "DAY",
                "description": "desc",
                "characters": [{"name": "john"}],
                "actions": [{"text": "He enters"}],
                "dialogue": [{"character": "john", "text": "Hello"}],
                "metadata": {}
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
        source_material="TITLE: THE SILENT TRAIN\n\nINT. ABANDONED TRAIN STATION - DAWN\n\nMIRA stands alone.\n\nEXT. OUTSIDE - DAY\nShe looks."
    )
    
    service = ScriptDoctorService()
    result = await service.standardize_screenplay(project)
    
    # We should have 3 raw scenes (intro, INT., EXT.)
    # The empty ones are ignored, but intro has text, INT has text, EXT has text.
    assert len(tracker.prompts) == 3
    assert len(result["scenes"]) == 3
    
    # Test formatting normalization
    assert result["scenes"][1]["heading"] == "INT. ROOM - DAY"
    assert result["scenes"][1]["characters"][0]["name"] == "JOHN"
    
    # Test exact source text is preserved
    assert result["scenes"][0]["metadata"]["source_scene_text"] == "TITLE: THE SILENT TRAIN\n\n"
    
@pytest.mark.asyncio
@patch("app.services.script_doctor.get_llm_provider")
async def test_failed_scene_aborts_process(mock_get_provider, clean_env):
    class FailingProvider:
        async def generate_json(self, prompt, schema):
            raise Exception("LLM generation failed")
            
    mock_get_provider.return_value = FailingProvider()
    
    project = Project(
        id="test-id",
        name="Test Project",
        genre="Drama",
        tone="Serious",
        visual_style="Dark",
        story_idea="Old idea",
        source_material="INT. ROOM - DAY\nAction."
    )
    
    service = ScriptDoctorService()
    
    with pytest.raises(HTTPException) as excinfo:
        await service.standardize_screenplay(project)
        
    assert excinfo.value.status_code == 422
    assert "Failed to process Scene 1" in excinfo.value.detail

@pytest.mark.asyncio
@patch("app.services.script_doctor.get_llm_provider")
async def test_fallback_segmentation(mock_get_provider, clean_env):
    class SegmentationMockProvider:
        async def generate_json(self, prompt, schema):
            # If the prompt is for segmentation
            if "find scene boundaries" in prompt:
                return {
                    "boundaries": [
                        {"exact_text_before_boundary": "He walked away."}
                    ]
                }
            # Otherwise return single scene
            return {
                "id": "mock",
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
            
    mock_get_provider.return_value = SegmentationMockProvider()
    
    text = "This is a story without headings. He walked away. Then it was night time."
    project = Project(
        id="test", name="test", genre="test", tone="test", visual_style="test", story_idea="",
        source_material=text
    )
    
    service = ScriptDoctorService()
    result = await service.standardize_screenplay(project)
    
    # Should have split into 2 scenes
    assert len(result["scenes"]) == 2
    assert result["scenes"][0]["metadata"]["source_scene_text"] == "This is a story without headings. He walked away."
    assert result["scenes"][1]["metadata"]["source_scene_text"] == " Then it was night time."
