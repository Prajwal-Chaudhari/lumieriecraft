import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from app.main import app
from app.db import get_session
from app.models.project import Project, CharacterAsset
from app.models.script import Script, ScriptProposal
from app.models.production import (
    ProductionPlan, ShotBlueprint, StoryboardFrame,
    CharacterBible, WorldBible, SceneBreakdown, CinematographyProposal
)

from sqlalchemy.pool import StaticPool

sqlite_url = "sqlite:///:memory:"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)

def get_session_override():
    with Session(engine) as session:
        yield session

client = TestClient(app)

@pytest.fixture(autouse=True)
def prepare_database():
    SQLModel.metadata.create_all(engine)
    app.dependency_overrides[get_session] = get_session_override
    yield
    SQLModel.metadata.drop_all(engine)
    app.dependency_overrides.clear()

def test_delete_nonexistent_project():
    response = client.delete("/api/projects/does-not-exist")
    assert response.status_code == 404

def test_delete_project_only():
    response = client.post("/api/projects", json={
        "name": "Test Delete",
        "story_idea": "A test project",
        "genre": "Sci-Fi",
        "duration": "Short",
        "tone": "Dark",
        "visual_style": "Cinematic"
    })
    project_id = response.json()["id"]

    response = client.delete(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Project deleted successfully"}

    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 404

def test_delete_project_with_dependencies():
    with Session(engine) as session:
        project1 = Project(name="Proj 1", story_idea="Idea 1", genre="G1", duration="D1", tone="T1", visual_style="V1")
        project2 = Project(name="Proj 2", story_idea="Idea 2", genre="G2", duration="D2", tone="T2", visual_style="V2")
        session.add(project1)
        session.add(project2)
        session.commit()
        
        p1_id = project1.id
        p2_id = project2.id
        
        s1 = Script(project_id=p1_id, title="Script 1")
        s2 = Script(project_id=p2_id, title="Script 2")
        session.add(s1)
        session.add(s2)
        session.commit()
        
        s1_id = s1.id
        s2_id = s2.id
        
        sp1 = ScriptProposal(project_id=p1_id, proposed_script={"title": "Proposed 1"})
        session.add(sp1)
        session.commit()
        sp1_id = sp1.id
        
        ca1 = CharacterAsset(project_id=p1_id, character_name="Char 1", file_path="test1.jpg", source="user_upload")
        session.add(ca1)
        session.commit()
        ca1_id = ca1.id
        
        cb1 = CharacterBible(project_id=p1_id, name="Char 1")
        wb1 = WorldBible(project_id=p1_id, name="World 1")
        sb1 = SceneBreakdown(project_id=p1_id, script_id=s1_id, scene_id="scene-1")
        session.add_all([cb1, wb1, sb1])
        session.commit()
        cb1_id = cb1.id
        wb1_id = wb1.id
        sb1_id = sb1.id
        
        plan1 = ProductionPlan(project_id=p1_id, script_id=s1_id, script_version=1)
        session.add(plan1)
        session.commit()
        plan1_id = plan1.id
        
        shot1 = ShotBlueprint(production_plan_id=plan1_id, scene_id="scene-1", shot_id="shot-1", purpose="purpose", story_beat="beat")
        session.add(shot1)
        session.commit()
        shot1_id = shot1.id
        
        frame1 = StoryboardFrame(project_id=p1_id, production_plan_id=plan1_id, script_id=s1_id, script_version=1, scene_id="scene-1", shot_id=shot1_id, generation_id="gen-1", provider="prov", model="mod", image_url="img.jpg", status="OK")
        session.add(frame1)
        session.commit()
        frame1_id = frame1.id

    with Session(engine) as session:
        assert len(session.exec(select(Project)).all()) == 2
        assert len(session.exec(select(Script)).all()) == 2
        assert len(session.exec(select(StoryboardFrame)).all()) == 1

    response = client.delete(f"/api/projects/{p1_id}")
    assert response.status_code == 200

    with Session(engine) as session:
        assert session.get(Project, p1_id) is None
        assert session.get(Script, s1_id) is None
        assert session.get(ScriptProposal, sp1_id) is None
        assert session.get(CharacterAsset, ca1_id) is None
        assert session.get(CharacterBible, cb1_id) is None
        assert session.get(WorldBible, wb1_id) is None
        assert session.get(SceneBreakdown, sb1_id) is None
        assert session.get(ProductionPlan, plan1_id) is None
        assert session.get(ShotBlueprint, shot1_id) is None
        assert session.get(StoryboardFrame, frame1_id) is None
        
        assert session.get(Project, p2_id) is not None
        assert session.get(Script, s2_id) is not None
