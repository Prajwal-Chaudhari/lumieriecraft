from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.script import Script
from app.models.production import CharacterBible, WorldBible, SceneBreakdown
from app.services.production_intelligence import ProductionIntelligenceService, GlobalExtractionResult
from app.schemas.production import CharacterBibleResponse, WorldBibleResponse, SceneBreakdownResponse, ProductionAnalysisResponse
from typing import List

router = APIRouter()
service = ProductionIntelligenceService()

@router.post("/{project_id}/production/bibles/extract", response_model=ProductionAnalysisResponse)
async def extract_bibles(project_id: str, script_id: str, db: Session = Depends(get_session)):
    script = db.exec(select(Script).where(Script.id == script_id, Script.project_id == project_id)).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    if script.status != "approved":
        raise HTTPException(status_code=400, detail="Script must be approved before production analysis")

    # Extract global bibles
    global_bibles = await service.extract_global_bibles(db=db, script=script)

    # Analyze scenes for production breakdowns
    for scene_dict in script.scenes:
        from app.models.script import Scene
        scene = Scene.model_validate(scene_dict)
        await service.analyze_scene_for_production(db=db, script=script, scene=scene, global_bibles=global_bibles)

    # Fetch the newly created entities to return
    chars = db.exec(select(CharacterBible).where(CharacterBible.project_id == project_id)).all()
    worlds = db.exec(select(WorldBible).where(WorldBible.project_id == project_id)).all()
    breakdowns = db.exec(select(SceneBreakdown).where(SceneBreakdown.project_id == project_id, SceneBreakdown.script_id == script_id)).all()

    return ProductionAnalysisResponse(
        characters=chars,
        world_locations=worlds,
        scene_breakdowns=breakdowns
    )

@router.get("/{project_id}/production/bibles", response_model=ProductionAnalysisResponse)
def get_production_intelligence(project_id: str, script_id: str, db: Session = Depends(get_session)):
    chars = db.exec(select(CharacterBible).where(CharacterBible.project_id == project_id)).all()
    worlds = db.exec(select(WorldBible).where(WorldBible.project_id == project_id)).all()
    breakdowns = db.exec(select(SceneBreakdown).where(SceneBreakdown.project_id == project_id, SceneBreakdown.script_id == script_id)).all()

    return ProductionAnalysisResponse(
        characters=chars,
        world_locations=worlds,
        scene_breakdowns=breakdowns
    )
