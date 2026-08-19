from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional

from app.db import get_session
from app.models.project import Project
from app.models.production import (
    ProductionPlan, CharacterBible, WorldBible, SceneBreakdown, ShotBlueprint,
    StoryboardFrame, ShotStatus
)
from app.models.script import Script
from app.services.storyboard_agent import StoryboardAgentService

router = APIRouter(tags=["storyboard"])

def get_storyboard_service(request: Request) -> StoryboardAgentService:
    registry = request.app.state.provider_registry
    from app.services.image_generation_service import ImageGenerationService
    return StoryboardAgentService(ImageGenerationService(registry))

async def _generate_storyboard_background(shot_id: str, script_version: int, db: Session, service: StoryboardAgentService):
    try:
        shot = db.get(ShotBlueprint, shot_id)
        if not shot:
            return

        breakdown = db.get(SceneBreakdown, shot.scene_breakdown_id)
        plan = db.get(ProductionPlan, shot.production_plan_id)
        project = db.get(Project, plan.project_id)

        characters = db.exec(select(CharacterBible).where(CharacterBible.production_plan_id == plan.id)).all()
        world = db.exec(select(WorldBible).where(WorldBible.production_plan_id == plan.id)).first()

        frame = await service.generate_storyboard(
            shot=shot,
            scene=breakdown,
            characters=characters,
            world=world,
            project=project,
            script_version=script_version
        )
        
        db.add(frame)
        db.commit()

    except Exception as e:
        print(f"Error in storyboard generation: {e}")
        # Note: In a production app, we would ideally write a failed StoryboardFrame
        # or update a status field on the shot to reflect failure.
        pass

@router.post("/projects/{project_id}/storyboard/shots/{shot_id}/generate")
async def generate_storyboard(project_id: str, shot_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_session), service: StoryboardAgentService = Depends(get_storyboard_service)):
    shot = db.get(ShotBlueprint, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
        
    plan = db.get(ProductionPlan, shot.production_plan_id)
    if not plan or plan.project_id != project_id:
        raise HTTPException(status_code=404, detail="Shot not found for this project")

    # Start generation in background
    background_tasks.add_task(_generate_storyboard_background, shot.id, plan.script_version, db, service)
    
    return {"message": "Storyboard generation started"}

@router.post("/projects/{project_id}/storyboard/shots/{shot_id}/regenerate")
async def regenerate_storyboard(project_id: str, shot_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_session), service: StoryboardAgentService = Depends(get_storyboard_service)):
    shot = db.get(ShotBlueprint, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
        
    plan = db.get(ProductionPlan, shot.production_plan_id)
    if not plan or plan.project_id != project_id:
        raise HTTPException(status_code=404, detail="Shot not found for this project")

    # Regenerating just creates a new variant instead of destroying previous ones
    background_tasks.add_task(_generate_storyboard_background, shot.id, plan.script_version, db, service)
    
    return {"message": "Storyboard regeneration started"}

@router.get("/projects/{project_id}/storyboard/shots/{shot_id}")
async def get_shot_storyboards(project_id: str, shot_id: str, db: Session = Depends(get_session)):
    frames = db.exec(select(StoryboardFrame).where(
        StoryboardFrame.project_id == project_id,
        StoryboardFrame.shot_id == shot_id
    ).order_by(StoryboardFrame.created_at.desc())).all()
    
    return frames

@router.get("/projects/{project_id}/storyboard")
async def get_project_storyboards(project_id: str, db: Session = Depends(get_session)):
    frames = db.exec(select(StoryboardFrame).where(
        StoryboardFrame.project_id == project_id
    ).order_by(StoryboardFrame.created_at.desc())).all()
    
    return frames
