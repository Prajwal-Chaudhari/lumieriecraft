import pytest
import uuid
from sqlmodel import Session, create_engine, SQLModel
from app.models.project import Project
from app.models.script import Script
from app.models.production import CharacterBible, WorldBible, SceneBreakdown
from app.services.production_intelligence import ProductionIntelligenceService, GlobalExtractionResult
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="prod_service")
def prod_service_fixture():
    service = ProductionIntelligenceService()
    # Mock the LLM provider
    mock_provider = MagicMock()
    mock_provider.generate_json = AsyncMock()
    service.get_llm = lambda: mock_provider
    return service

@pytest.fixture(name="approved_script")
def approved_script_fixture(session):
    project = Project(name="Test Project", story_idea="Test idea", genre="Drama", duration="Short", tone="Dark", visual_style="Gritty")
    session.add(project)
    session.commit()
    session.refresh(project)
    
    script = Script(
        project_id=project.id,
        version=1,
        title="Test Script",
        status="approved",
        scenes=[
            {
                "id": str(uuid.uuid4()),
                "scene_number": 1,
                "heading": "EXT. RURAL TRAIN STATION - DAWN",
                "location": "RURAL TRAIN STATION",
                "time_of_day": "DAWN",
                "description": "MIRA waits beside a broken station clock. A red suitcase rests on the bench.",
                "actions": [
                    {"text": "Mira checks her watch."}
                ],
                "dialogue": []
            }
        ]
    )
    session.add(script)
    session.commit()
    session.refresh(script)
    return script

@pytest.mark.asyncio
async def test_extract_global_bibles_approved_script(session, prod_service, approved_script):
    # Setup mock LLM response
    prod_service.get_llm().generate_json.return_value = {
        "characters": [
            {
                "name": "MIRA",
                "description": "A woman waiting at a station.",
                "established_facts": ["Has a red suitcase"],
                "inferred_facts": ["She is nervous"],
                "source_scene_ids": [approved_script.scenes[0]["id"]]
            }
        ],
        "locations": [
            {
                "name": "RURAL TRAIN STATION",
                "established_facts": ["Has a broken clock"],
                "inferred_facts": ["Old, neglected"],
                "source_scene_ids": [approved_script.scenes[0]["id"]]
            }
        ]
    }
    
    result = await prod_service.extract_global_bibles(session, approved_script)
    
    assert len(result.characters) == 1
    assert result.characters[0].name == "MIRA"
    
    # Verify DB persistence
    from sqlmodel import select
    chars = session.exec(select(CharacterBible).where(CharacterBible.project_id == approved_script.project_id)).all()
    assert len(chars) == 1
    assert chars[0].name == "MIRA"

@pytest.mark.asyncio
async def test_extract_global_bibles_unapproved_script_raises_error(session, prod_service):
    project = Project(name="Test", story_idea="Test", genre="Drama", duration="Short", tone="Dark", visual_style="Gritty")
    session.add(project)
    session.commit()
    
    script = Script(
        project_id=project.id,
        version=1,
        title="Test",
        status="draft", # Not approved
        scenes=[]
    )
    session.add(script)
    session.commit()
    
    import pytest
    with pytest.raises(ValueError, match="Script must be approved"):
        await prod_service.extract_global_bibles(session, script)

@pytest.mark.asyncio
async def test_analyze_scene_for_production(session, prod_service, approved_script):
    prod_service.get_llm().generate_json.return_value = {
        "location": "RURAL TRAIN STATION",
        "time_of_day": "DAWN",
        "story_beat": "Waiting for the train",
        "props": ["Red suitcase", "Broken clock"]
    }
    
    global_bibles = GlobalExtractionResult() # Empty for test
    from app.models.script import Scene
    scene = Scene.model_validate(approved_script.scenes[0])
    
    result = await prod_service.analyze_scene_for_production(session, approved_script, scene, global_bibles)
    
    assert result.location == "RURAL TRAIN STATION"
    assert "Red suitcase" in result.props
    
    from sqlmodel import select
    breakdowns = session.exec(select(SceneBreakdown).where(SceneBreakdown.project_id == approved_script.project_id)).all()
    assert len(breakdowns) == 1
    assert breakdowns[0].time_of_day == "DAWN"
