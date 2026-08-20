from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Dict, Any
from app.db import get_session
from app.models.project import Project
from app.models.script import Script
from app.models.production import CinematographyProposal, ProductionPlan, ShotBlueprint, ShotStatus, ProductionStatus
from app.services.cinematographer import CinematographerService
from app.schemas.cinematography import CinematographyPlanSchema

router = APIRouter()
cinematographer_service = CinematographerService()

@router.get("/projects/{project_id}/cinematography")
def get_cinematography(project_id: str, session: Session = Depends(get_session)):
    """
    Returns the currently active ProductionPlan and any PENDING CinematographyProposal.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    plan = session.exec(select(ProductionPlan).where(ProductionPlan.project_id == project_id)).first()
    proposal = session.exec(select(CinematographyProposal).where(
        CinematographyProposal.project_id == project_id,
        CinematographyProposal.status == "PENDING"
    )).first()

    shots = []
    if plan:
        shots = session.exec(select(ShotBlueprint).where(ShotBlueprint.production_plan_id == plan.id)).all()

    return {
        "plan": plan,
        "shots": shots,
        "proposal": proposal
    }

@router.post("/projects/{project_id}/cinematography/propose")
async def propose_cinematography(project_id: str, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    script = session.exec(select(Script).where(Script.project_id == project_id).order_by(Script.version.desc())).first()
    if not script:
        raise HTTPException(status_code=404, detail="No script found to analyze")

    try:
        plan_data = await cinematographer_service.propose_cinematography(project_id, script)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    proposal = CinematographyProposal(
        project_id=project_id,
        script_id=script.id,
        script_version=script.version,
        proposed_plan=plan_data.model_dump(),
        status="PENDING"
    )
    session.add(proposal)
    session.commit()
    session.refresh(proposal)

    return proposal

@router.post("/projects/{project_id}/cinematography/proposals/{proposal_id}/apply")
def apply_cinematography_proposal(project_id: str, proposal_id: str, session: Session = Depends(get_session)):
    proposal = session.get(CinematographyProposal, proposal_id)
    if not proposal or proposal.project_id != project_id:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != "PENDING":
        raise HTTPException(status_code=400, detail="Proposal is not pending")

    # Verify script version safety
    current_script = session.exec(select(Script).where(Script.project_id == project_id).order_by(Script.version.desc())).first()
    if current_script.id != proposal.script_id or current_script.version != proposal.script_version:
        raise HTTPException(status_code=400, detail="Stale proposal: current script version has changed")

    # Validate the stored proposed_plan dict back into Pydantic model to be safe
    try:
        plan_data = CinematographyPlanSchema.model_validate(proposal.proposed_plan)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Proposal data invalid: {e}")

    # Check if a production plan already exists
    existing_plan = session.exec(select(ProductionPlan).where(ProductionPlan.project_id == project_id)).first()
    
    new_version = 1
    if existing_plan:
        new_version = existing_plan.version + 1
        # Remove old shots to cleanly apply new ones, or keep them?
        # Usually, when applying a new plan, we replace it, but maybe we just delete the old one or archive it.
        # Let's delete the old plan and its shots for simplicity, and recreate.
        old_shots = session.exec(select(ShotBlueprint).where(ShotBlueprint.production_plan_id == existing_plan.id)).all()
        for shot in old_shots:
            session.delete(shot)
        session.delete(existing_plan)
        session.commit() # commit deletes

    # Create new Production Plan
    new_plan = ProductionPlan(
        project_id=project_id,
        script_id=proposal.script_id,
        script_version=proposal.script_version,
        status=ProductionStatus.APPROVED,
        version=new_version
    )
    
    # Store scenes visual plan data (ColorPlan, Visual goal, etc.) inside the ProductionPlan
    # without duplicating the shots which go to their own table
    scenes_metadata = []
    for scene in plan_data.scenes:
        scenes_metadata.append({
            "scene_id": scene.scene_id,
            "visual_goal": scene.visual_goal,
            "overall_mood": scene.overall_mood,
            "color_plan": scene.color_plan.model_dump()
        })
    new_plan.scenes_data = {"scenes": scenes_metadata}
    
    session.add(new_plan)
    session.commit()
    session.refresh(new_plan)

    # Insert ShotBlueprints
    for scene in plan_data.scenes:
        for shot in scene.shots:
            blueprint = ShotBlueprint(
                production_plan_id=new_plan.id,
                scene_id=scene.scene_id,
                shot_id=shot.shot_id,
                purpose=shot.purpose,
                story_beat=shot.story_beat,
                shot_size=shot.shot_size,
                camera=shot.camera.model_dump() if shot.camera else None,
                blocking=shot.blocking.model_dump() if shot.blocking else None,
                composition=shot.composition.model_dump() if shot.composition else None,
                lighting=shot.lighting.model_dump() if shot.lighting else None,
                subject=shot.subject,
                character_actions=shot.character_actions,
                emotion=shot.emotion,
                status=ShotStatus.PLANNED
            )
            session.add(blueprint)
            
    proposal.status = "APPLIED"
    session.add(proposal)
    session.commit()
    
    return {"status": "success", "plan_id": new_plan.id, "version": new_version}

@router.post("/projects/{project_id}/cinematography/proposals/{proposal_id}/reject")
def reject_cinematography_proposal(project_id: str, proposal_id: str, session: Session = Depends(get_session)):
    proposal = session.get(CinematographyProposal, proposal_id)
    if not proposal or proposal.project_id != project_id:
        raise HTTPException(status_code=404, detail="Proposal not found")
        
    proposal.status = "REJECTED"
    session.add(proposal)
    session.commit()
    
    return {"status": "success", "message": "Proposal rejected"}

@router.patch("/projects/{project_id}/cinematography/proposals/{proposal_id}")
def update_pending_proposal(project_id: str, proposal_id: str, update_data: dict, session: Session = Depends(get_session)):
    """Allows the Director to edit a pending proposal before applying it."""
    proposal = session.get(CinematographyProposal, proposal_id)
    if not proposal or proposal.project_id != project_id:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    if proposal.status != "PENDING":
        raise HTTPException(status_code=400, detail="Can only edit PENDING proposals")

    # In a real app we'd deeply merge, but for now we'll accept the full replaced proposed_plan 
    if "proposed_plan" in update_data:
        try:
            # Re-validate
            plan_data = CinematographyPlanSchema.model_validate(update_data["proposed_plan"])
            proposal.proposed_plan = plan_data.model_dump()
            session.add(proposal)
            session.commit()
            session.refresh(proposal)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid plan format: {e}")
            
    return proposal
