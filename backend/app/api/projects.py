from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Session, select
from app.db import get_session
from app.models.project import Project, ProjectCreate
from app.models.script import Script, ScriptCreate
from app.services.script_writer import ScriptWriterService

class RegenerateSceneRequest(BaseModel):
    instructions: Optional[str] = None

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

@router.post("/projects/{project_id}/script/analyze", response_model=Script)
async def analyze_script(project_id: str, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    script_writer = ScriptWriterService()
    script_data = await script_writer.analyze_script(project)
    
    script = session.exec(select(Script).where(Script.project_id == project_id)).first()
    if script:
        script.scenes = script_data.get("scenes", [])
        script.title = script_data.get("title", project.name)
        script.status = "ANALYZED"
    else:
        script = Script(
            project_id=project_id,
            title=script_data.get("title", project.name),
            scenes=script_data.get("scenes", []),
            status="ANALYZED"
        )
        session.add(script)
    session.commit()
    session.refresh(script)
    return script

@router.post("/projects/{project_id}/script/scenes/{scene_id}/propose", response_model=dict)
async def propose_scene_enhancement(
    project_id: str, 
    scene_id: str, 
    request: RegenerateSceneRequest,
    session: Session = Depends(get_session)
):
    instructions = request.instructions if request else "Enhance this scene."
    
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    script = session.exec(select(Script).where(Script.project_id == project_id)).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    target_scene = None
    for s in script.scenes:
        if s.get("id") == scene_id:
            target_scene = s
            break
            
    if not target_scene:
        raise HTTPException(status_code=404, detail="Scene not found in script")

    script_writer = ScriptWriterService()
    new_scene = await script_writer.propose_scene_enhancement(project, target_scene, instructions)
    
    return {"proposed_scene": new_scene}

class ApplySceneRequest(BaseModel):
    scene: dict

@router.post("/projects/{project_id}/script/scenes/{scene_id}/apply", response_model=Script)
async def apply_scene_update(
    project_id: str, 
    scene_id: str, 
    request: ApplySceneRequest,
    session: Session = Depends(get_session)
):
    script = session.exec(select(Script).where(Script.project_id == project_id)).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    target_index = -1
    for i, s in enumerate(script.scenes):
        if s.get("id") == scene_id:
            target_index = i
            break
            
    if target_index == -1:
        raise HTTPException(status_code=404, detail="Scene not found in script")

    script.scenes[target_index] = request.scene
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(script, "scenes")
    session.add(script)
    session.commit()
    session.refresh(script)
    return script
