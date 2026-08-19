from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.project import Project, ProjectCreate
from app.models.script import Script, ScriptCreate
from app.services.script_writer import ScriptWriterService

router = APIRouter(tags=["projects"])

@router.post("/projects", response_model=Project)
def create_project(project: ProjectCreate, session: Session = Depends(get_session)):
    db_project = Project.model_validate(project)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("/projects", response_model=list[Project])
def get_projects(session: Session = Depends(get_session)):
    return session.exec(select(Project)).all()

@router.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: str, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.get("/projects/{project_id}/script", response_model=Script)
def get_script(project_id: str, session: Session = Depends(get_session)):
    script = session.exec(select(Script).where(Script.project_id == project_id)).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@router.post("/projects/{project_id}/script/generate", response_model=Script)
async def generate_script(project_id: str, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    script_writer = ScriptWriterService()
    script_data = await script_writer.generate_script(project)
    
    script = session.exec(select(Script).where(Script.project_id == project_id)).first()
    if script:
        script.scenes = script_data.get("scenes", [])
        script.title = script_data.get("title", project.name)
    else:
        script = Script(
            project_id=project_id,
            title=script_data.get("title", project.name),
            scenes=script_data.get("scenes", [])
        )
        session.add(script)
    session.commit()
    session.refresh(script)
    return script

@router.post("/projects/{project_id}/script/scenes/{scene_id}/regenerate", response_model=Script)
async def regenerate_scene(project_id: str, scene_id: str, session: Session = Depends(get_session)):
    # For now, we mock the regeneration of a single scene
    script = session.exec(select(Script).where(Script.project_id == project_id)).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Just a placeholder for actual LLM call to rewrite one scene
    for s in script.scenes:
        if s.get("id") == scene_id:
            s["description"] += " (Regenerated)"
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(script, "scenes")
    session.add(script)
    session.commit()
    session.refresh(script)
    return script
