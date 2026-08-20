from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Session, select, desc
from app.db import get_session
from app.models.project import Project, ProjectCreate, CharacterAsset


from app.models.script import Script, ScriptCreate, ScriptProposal
from app.services.script_doctor import ScriptDoctorService

router = APIRouter(tags=["projects"])

@router.get("/projects/{project_id}/characters")
def get_project_characters(project_id: str, db: Session = Depends(get_session)):
    characters = db.exec(select(CharacterAsset).where(CharacterAsset.project_id == project_id)).all()
    return characters

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
    script = session.exec(select(Script).where(Script.project_id == project_id).order_by(desc(Script.version))).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@router.post("/projects/{project_id}/script/propose-standardization", response_model=ScriptProposal)
async def propose_standardization(project_id: str, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    script_doctor = ScriptDoctorService()
    script_data = await script_doctor.standardize_screenplay(project)
    
    # Check if there is an existing script version
    script = session.exec(select(Script).where(Script.project_id == project_id).order_by(desc(Script.version))).first()
    base_version = script.version if script else 1
    
    proposal = ScriptProposal(
        project_id=project_id,
        base_script_version=base_version,
        proposed_script=script_data,
        status="PENDING"
    )
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    return proposal

@router.post("/projects/{project_id}/script/proposals/{proposal_id}/apply", response_model=Script)
def apply_script_proposal(project_id: str, proposal_id: str, session: Session = Depends(get_session)):
    proposal = session.get(ScriptProposal, proposal_id)
    if not proposal or proposal.project_id != project_id:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != "PENDING":
        raise HTTPException(status_code=400, detail="Proposal is already processed")
        
    script = session.exec(select(Script).where(Script.project_id == project_id).order_by(desc(Script.version))).first()
    
    # Check version match
    if script and script.version != proposal.base_script_version:
        raise HTTPException(status_code=409, detail="Proposal is based on a stale script version")
        
    next_version = (script.version + 1) if script else 1
    
    new_script = Script(
        project_id=project_id,
        title=proposal.proposed_script.get("title", "Untitled"),
        scenes=proposal.proposed_script.get("scenes", []),
        status="approved",
        version=next_version
    )
    
    proposal.status = "APPLIED"
    
    session.add(new_script)
    session.add(proposal)
    session.commit()
    session.refresh(new_script)
    return new_script

@router.post("/projects/{project_id}/script/proposals/{proposal_id}/reject", response_model=ScriptProposal)
def reject_script_proposal(project_id: str, proposal_id: str, session: Session = Depends(get_session)):
    proposal = session.get(ScriptProposal, proposal_id)
    if not proposal or proposal.project_id != project_id:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != "PENDING":
        raise HTTPException(status_code=400, detail="Proposal is already processed")
        
    proposal.status = "REJECTED"
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    return proposal

class SceneFixRequest(BaseModel):
    base_version: int
    instructions: str

@router.post("/projects/{project_id}/script/scenes/{scene_id}/propose-fix", response_model=ScriptProposal)
async def propose_scene_fix(
    project_id: str, 
    scene_id: str, 
    request: SceneFixRequest,
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    script = session.exec(select(Script).where(Script.project_id == project_id).order_by(desc(Script.version))).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
        
    if script.version != request.base_version:
        raise HTTPException(status_code=409, detail="Stale script version")
    
    target_scene = None
    target_index = -1
    for i, s in enumerate(script.scenes):
        if s.get("id") == scene_id:
            target_scene = s
            target_index = i
            break
            
    if not target_scene:
        raise HTTPException(status_code=404, detail="Scene not found in script")

    script_doctor = ScriptDoctorService()
    new_scene = await script_doctor.propose_scene_standardization(
        project, 
        base_version=script.version, 
        target_scene=target_scene, 
        instructions=request.instructions
    )
    
    # Create a full script proposal but with only this scene changed
    import copy
    proposed_scenes = copy.deepcopy(script.scenes)
    proposed_scenes[target_index] = new_scene
    
    proposed_script_data = {
        "title": script.title,
        "scenes": proposed_scenes
    }
    
    proposal = ScriptProposal(
        project_id=project_id,
        base_script_version=script.version,
        proposed_script=proposed_script_data,
        status="PENDING"
    )
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    return proposal
