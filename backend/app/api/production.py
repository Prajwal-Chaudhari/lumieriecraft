from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from app.db import get_session
from app.models.project import Project
from app.models.script import Script, Scene
from app.models.production import (
    ProductionPlan, CharacterBible, WorldBible, SceneBreakdown, ShotBlueprint,
    ProductionStatus, ShotStatus
)
from app.services.production_intelligence import ProductionIntelligenceService

router = APIRouter(tags=["production"])

def get_production_service(request: Request) -> ProductionIntelligenceService:
    registry = request.app.state.provider_registry
    return ProductionIntelligenceService(registry)

async def _analyze_production_background(project_id: str, script_id: str, script_version: int, production_plan_id: str, db: Session, service: ProductionIntelligenceService):
    try:
        # Load script
        script = db.get(Script, script_id)
        if not script:
            raise Exception("Script not found")

        # Pass A: Global Extraction
        global_result = await service.extract_global_bibles(script)

        # Save Bibles
        for char in global_result.characters:
            char_bible = CharacterBible(
                production_plan_id=production_plan_id,
                name=char.name,
                appearance=char.appearance,
                age_range=char.age_range,
                hair=char.hair,
                clothing=char.clothing,
                accessories=char.accessories,
                personality=char.personality,
                relationships=char.relationships,
                established_facts=char.established_facts,
                proposed_facts=char.proposed_facts,
                continuity_notes=char.continuity_notes,
                source_scene_ids=char.source_scene_ids
            )
            db.add(char_bible)
        
        for loc in global_result.locations:
            world_bible = WorldBible(
                production_plan_id=production_plan_id,
                name=loc.name,
                description=loc.description,
                architecture=loc.architecture,
                environment=loc.environment,
                lighting_characteristics=loc.lighting_characteristics,
                time_variants=loc.time_variants,
                important_props=loc.important_props,
                established_facts=loc.established_facts,
                proposed_facts=loc.proposed_facts,
                continuity_notes=loc.continuity_notes,
                source_scene_ids=loc.source_scene_ids
            )
            db.add(world_bible)
        
        db.commit()

        # Pass B: Scene Breakdown
        for scene_dict in script.scenes:
            scene = Scene.model_validate(scene_dict)
            breakdown_ext = await service.analyze_scene_for_production(scene, global_result)
            
            breakdown = SceneBreakdown(
                production_plan_id=production_plan_id,
                scene_id=scene.id,
                scene_number=scene.scene_number,
                location=breakdown_ext.location,
                time_of_day=breakdown_ext.time_of_day,
                characters=breakdown_ext.characters,
                actions=breakdown_ext.actions,
                dialogue_summary=breakdown_ext.dialogue_summary,
                props=breakdown_ext.props,
                emotional_beat=breakdown_ext.emotional_beat,
                narrative_purpose=breakdown_ext.narrative_purpose,
                continuity_notes=breakdown_ext.continuity_notes
            )
            db.add(breakdown)
        
        # Update plan status
        plan = db.get(ProductionPlan, production_plan_id)
        if plan:
            plan.status = ProductionStatus.ANALYZED
            db.commit()

    except Exception as e:
        print(f"Error in production analysis background task: {e}")
        plan = db.get(ProductionPlan, production_plan_id)
        if plan:
            plan.status = "error"
            db.commit()

@router.post("/projects/{project_id}/production/analyze")
async def analyze_production(project_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_session), service: ProductionIntelligenceService = Depends(get_production_service)):
    # Get active script
    script = db.exec(select(Script).where(Script.project_id == project_id).order_by(Script.version.desc())).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found for project")

    # Check if a production plan already exists for this script version
    existing_plan = db.exec(select(ProductionPlan).where(
        ProductionPlan.project_id == project_id,
        ProductionPlan.script_id == script.id,
        ProductionPlan.script_version == script.version
    )).first()

    if existing_plan:
        return {"message": "Production plan already exists for this script version", "plan_id": existing_plan.id}

    # Create new plan
    plan = ProductionPlan(
        project_id=project_id,
        script_id=script.id,
        script_version=script.version,
        status=ProductionStatus.ANALYZING
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    background_tasks.add_task(_analyze_production_background, project_id, script.id, script.version, plan.id, db, service)
    
    return {"message": "Started production analysis", "plan_id": plan.id}

@router.get("/projects/{project_id}/production")
async def get_production_plan(project_id: str, db: Session = Depends(get_session)):
    script = db.exec(select(Script).where(Script.project_id == project_id).order_by(Script.version.desc())).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    plan = db.exec(select(ProductionPlan).where(
        ProductionPlan.project_id == project_id,
        ProductionPlan.script_version == script.version
    )).first()

    if not plan:
        return {"status": ProductionStatus.NOT_ANALYZED}

    characters = db.exec(select(CharacterBible).where(CharacterBible.production_plan_id == plan.id)).all()
    worlds = db.exec(select(WorldBible).where(WorldBible.production_plan_id == plan.id)).all()
    breakdowns = db.exec(select(SceneBreakdown).where(SceneBreakdown.production_plan_id == plan.id)).all()

    return {
        "plan": plan,
        "characters": characters,
        "worlds": worlds,
        "scene_breakdowns": breakdowns
    }

@router.get("/projects/{project_id}/production/scenes/{scene_id}")
async def get_scene_production(project_id: str, scene_id: str, db: Session = Depends(get_session)):
    script = db.exec(select(Script).where(Script.project_id == project_id).order_by(Script.version.desc())).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    plan = db.exec(select(ProductionPlan).where(
        ProductionPlan.project_id == project_id,
        ProductionPlan.script_version == script.version
    )).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Production plan not found")

    breakdown = db.exec(select(SceneBreakdown).where(
        SceneBreakdown.production_plan_id == plan.id,
        SceneBreakdown.scene_id == scene_id
    )).first()

    if not breakdown:
        raise HTTPException(status_code=404, detail="Scene breakdown not found")

    shots = db.exec(select(ShotBlueprint).where(ShotBlueprint.scene_breakdown_id == breakdown.id)).all()

    return {
        "breakdown": breakdown,
        "shots": shots
    }

@router.post("/projects/{project_id}/cinematography/generate")
async def generate_cinematography(project_id: str, scene_id: str, db: Session = Depends(get_session), service: ProductionIntelligenceService = Depends(get_production_service)):
    script = db.exec(select(Script).where(Script.project_id == project_id).order_by(Script.version.desc())).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    plan = db.exec(select(ProductionPlan).where(
        ProductionPlan.project_id == project_id,
        ProductionPlan.script_version == script.version
    )).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Production plan not found")

    breakdown = db.exec(select(SceneBreakdown).where(
        SceneBreakdown.production_plan_id == plan.id,
        SceneBreakdown.scene_id == scene_id
    )).first()
    if not breakdown:
        raise HTTPException(status_code=404, detail="Scene breakdown not found")

    characters = db.exec(select(CharacterBible).where(CharacterBible.production_plan_id == plan.id)).all()
    worlds = db.exec(select(WorldBible).where(WorldBible.production_plan_id == plan.id)).all()

    # Reconstruct GlobalExtractionResult for the service
    from app.services.production_intelligence import GlobalExtractionResult, CharacterExtraction, WorldExtraction
    global_bibles = GlobalExtractionResult(
        characters=[CharacterExtraction(**c.model_dump()) for c in characters],
        locations=[WorldExtraction(**w.model_dump()) for w in worlds]
    )

    shot_result = await service.generate_cinematography(breakdown, global_bibles)

    new_shots = []
    # Optionally delete existing shots for this scene to regenerate cleanly
    existing_shots = db.exec(select(ShotBlueprint).where(ShotBlueprint.scene_breakdown_id == breakdown.id)).all()
    for s in existing_shots:
        db.delete(s)

    for shot_ext in shot_result.shots:
        shot = ShotBlueprint(
            production_plan_id=plan.id,
            scene_breakdown_id=breakdown.id,
            scene_id=scene_id,
            shot_id=shot_ext.shot_id,
            purpose=shot_ext.purpose,
            story_beat=shot_ext.story_beat,
            shot_size=shot_ext.shot_size,
            camera_angle=shot_ext.camera_angle,
            lens=shot_ext.lens,
            composition=shot_ext.composition,
            lighting=shot_ext.lighting,
            camera_movement=shot_ext.camera_movement,
            subject=shot_ext.subject,
            character_actions=shot_ext.character_actions,
            emotion=shot_ext.emotion,
            visual_prompt=shot_ext.visual_prompt
        )
        db.add(shot)
        new_shots.append(shot)
    
    db.commit()

    return {"message": "Cinematography generated", "shots": new_shots}

class ShotBlueprintUpdate(BaseModel):
    shot_size: Optional[str] = None
    camera_angle: Optional[str] = None
    lens: Optional[str] = None
    composition: Optional[str] = None
    lighting: Optional[str] = None
    camera_movement: Optional[str] = None
    subject: Optional[str] = None
    character_actions: Optional[str] = None
    emotion: Optional[str] = None
    visual_prompt: Optional[str] = None
    purpose: Optional[str] = None
    story_beat: Optional[str] = None

@router.patch("/projects/{project_id}/production/shots/{shot_id}")
async def update_shot_blueprint(project_id: str, shot_id: str, update_data: ShotBlueprintUpdate, db: Session = Depends(get_session)):
    shot = db.get(ShotBlueprint, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
        
    # Verify the shot belongs to a production plan for this project
    plan = db.get(ProductionPlan, shot.production_plan_id)
    if not plan or plan.project_id != project_id:
        raise HTTPException(status_code=404, detail="Shot not found for this project")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(shot, key, value)
        
    shot.status = ShotStatus.EDITED
    db.add(shot)
    db.commit()
    db.refresh(shot)
    
    return shot
