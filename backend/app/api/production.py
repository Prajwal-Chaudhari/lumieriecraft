"""
Production API — exposes scene breakdowns, shot blueprints, and batch operations
derived from an approved CinematographyProposal / ProductionPlan.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.db import get_session
from app.models.production import ProductionPlan, ShotBlueprint, ShotStatus, StoryboardFrame
from app.models.script import Script, Scene as SceneModel

router = APIRouter(tags=["production"])


# ─────────────────────────────────────────────
# Response Schemas (lightweight, no table=True)
# ─────────────────────────────────────────────

class ProductionSceneResponse(BaseModel):
    id: str
    project_id: str
    production_plan_id: str
    script_scene_id: str
    scene_number: int
    heading: str
    characters: List[Any] = []
    locations: List[Any] = []
    time: Dict[str, Any] = {}
    props: List[Any] = []
    narrative_beats: List[Any] = []
    color_plan: Optional[Dict[str, Any]] = None
    visual_goal: Optional[str] = None
    overall_mood: Optional[str] = None
    shot_count: int = 0

class ShotApprovalRequest(BaseModel):
    status: str  # 'approved', 'planned', 'edited'

class BatchGenerateRequest(BaseModel):
    shot_ids: Optional[List[str]] = None  # None = all shots in scene


# ─────────────────────────────────────────────
# Scene Breakdown Routes
# ─────────────────────────────────────────────

@router.get("/projects/{project_id}/production/scenes", response_model=List[ProductionSceneResponse])
def get_production_scenes(project_id: str, db: Session = Depends(get_session)):
    """Return all production scenes derived from the approved production plan + script."""
    plan = db.exec(select(ProductionPlan).where(ProductionPlan.project_id == project_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No production plan found. Generate a cinematography proposal first.")

    script = db.get(Script, plan.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found for this plan.")

    scenes_metadata = {s["scene_id"]: s for s in (plan.scenes_data or {}).get("scenes", [])}

    results: List[ProductionSceneResponse] = []
    for i, scene_dict in enumerate(script.scenes):
        scene = SceneModel.model_validate(scene_dict)
        meta = scenes_metadata.get(scene.id, {})

        # Count shots for this scene
        shot_count = db.exec(
            select(ShotBlueprint).where(
                ShotBlueprint.production_plan_id == plan.id,
                ShotBlueprint.scene_id == scene.id
            )
        ).all()

        results.append(ProductionSceneResponse(
            id=scene.id,
            project_id=project_id,
            production_plan_id=plan.id,
            script_scene_id=scene.id,
            scene_number=scene.scene_number,
            heading=scene.heading,
            characters=[c.model_dump() if hasattr(c, "model_dump") else c for c in scene.characters],
            locations=[scene.location] if scene.location else [],
            time={"time_of_day": scene.time_of_day} if scene.time_of_day else {},
            props=[],
            narrative_beats=[],
            color_plan=meta.get("color_plan"),
            visual_goal=meta.get("visual_goal"),
            overall_mood=meta.get("overall_mood"),
            shot_count=len(shot_count),
        ))

    return results


@router.get("/projects/{project_id}/production/scenes/{scene_id}", response_model=ProductionSceneResponse)
def get_production_scene(project_id: str, scene_id: str, db: Session = Depends(get_session)):
    plan = db.exec(select(ProductionPlan).where(ProductionPlan.project_id == project_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No production plan found.")

    script = db.get(Script, plan.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found.")

    target_scene_dict = next((s for s in script.scenes if s.get("id") == scene_id), None)
    if not target_scene_dict:
        raise HTTPException(status_code=404, detail="Scene not found.")

    scene = SceneModel.model_validate(target_scene_dict)
    scenes_metadata = {s["scene_id"]: s for s in (plan.scenes_data or {}).get("scenes", [])}
    meta = scenes_metadata.get(scene.id, {})
    shot_count = db.exec(
        select(ShotBlueprint).where(
            ShotBlueprint.production_plan_id == plan.id,
            ShotBlueprint.scene_id == scene.id
        )
    ).all()

    return ProductionSceneResponse(
        id=scene.id,
        project_id=project_id,
        production_plan_id=plan.id,
        script_scene_id=scene.id,
        scene_number=scene.scene_number,
        heading=scene.heading,
        characters=[c.model_dump() if hasattr(c, "model_dump") else c for c in scene.characters],
        locations=[scene.location] if scene.location else [],
        time={"time_of_day": scene.time_of_day} if scene.time_of_day else {},
        props=[],
        narrative_beats=[],
        color_plan=meta.get("color_plan"),
        visual_goal=meta.get("visual_goal"),
        overall_mood=meta.get("overall_mood"),
        shot_count=len(shot_count),
    )


# ─────────────────────────────────────────────
# Production Intelligence Routes
# ─────────────────────────────────────────────
from sqlalchemy import desc

@router.get("/projects/{project_id}/production/intelligence")
async def get_production_intelligence(project_id: str, db: Session = Depends(get_session)):
    script = db.exec(select(Script).where(Script.project_id == project_id).order_by(desc(Script.version))).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found.")

    characters_map = {}
    locations_map = {}
    scenes_breakdown = []
    dialogues_map = {}
    
    # Base rates for deterministic budget
    RATES = {
        "cast_per_actor": 5000,
        "location_per_scene": 8000,
        "equipment_per_scene": 4000,
        "lighting_per_scene": 2500,
        "costume_per_new": 1500,
        "prop_per_item": 1000,
        "makeup_per_scene": 1000,
        "crew_per_scene": 5000,
        "transport_per_scene": 2000,
        "misc_per_scene": 1000,
        "night_lighting_multiplier": 1.2,
        "exterior_location_multiplier": 1.5
    }

    budget = {
        "cast": 0, "location": 0, "equipment": 0, "lighting": 0,
        "costumes": 0, "props": 0, "makeup": 0, "crew": 0,
        "transport": 0, "misc": 0, "total": 0,
        "scene_budgets": []
    }
    
    # Try to fetch production plan
    plan = db.exec(select(ProductionPlan).where(ProductionPlan.project_id == project_id)).first()

    # --- AI EXTRACTION (New) ---
    try:
        from app.services.production_intelligence import ProductionIntelligenceService
        intel_service = ProductionIntelligenceService()
        bibles = await intel_service.extract_global_bibles(script)
        
        for char in bibles.characters:
            char_name = char.name.upper()
            ai_profile = []
            if char.personality: ai_profile.append(char.personality)
            if char.age_range: ai_profile.append(f"Age: {char.age_range}")
            if char.relationships: ai_profile.append(f"Relationships: {char.relationships}")
            if char.proposed_facts: ai_profile.extend(char.proposed_facts)
            
            clothing_hint = char.clothing if char.clothing else "Not specified in screenplay"
            recommendation = (char.accessories or "") + " " + (char.appearance or "")
            if not recommendation.strip():
                recommendation = f"Standard wardrobe for {char_name}."

            characters_map[char_name] = {
                "name": char_name,
                "established_facts": char.established_facts or [],
                "established_costume": clothing_hint,
                "costume_recommendation": recommendation.strip(),
                "ai_inferred_profile": ai_profile or ["Role inferred from script context"]
            }
            
        for loc in bibles.locations:
            ai_inferences = []
            if loc.description: ai_inferences.append(loc.description)
            if loc.lighting_characteristics: ai_inferences.append(f"Lighting: {loc.lighting_characteristics}")
            if loc.proposed_facts: ai_inferences.extend(loc.proposed_facts)
            
            locations_map[loc.name] = {
                "name": loc.name,
                "established_facts": loc.established_facts or [],
                "ai_inferences": ai_inferences or ["Likely requires standard setup"]
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to generate intelligence via LLM: {e}")
    # ---------------------------

    for scene_dict in script.scenes:
        scene = SceneModel.model_validate(scene_dict)
        scene_name = f"{scene.scene_number} - {scene.heading}"
        
        # 1. Locations
        loc = scene.location
        is_ext = "EXT" in scene.heading.upper()
        if loc not in locations_map:
            locations_map[loc] = {
                "name": loc,
                "established_facts": [f"Set during the {scene.time_of_day}"] + (["Exterior"] if is_ext else ["Interior"]),
                "ai_inferences": [f"Likely requires {'outdoor' if is_ext else 'indoor'} setup"]
            }
        else:
            fact = f"Set during the {scene.time_of_day}"
            if fact not in locations_map[loc]["established_facts"]:
                locations_map[loc]["established_facts"].append(fact)
            
        # 2. Characters & Costumes
        scene_chars = []
        for c in scene.characters:
            name = c.name.upper()
            scene_chars.append(name)
            if name not in characters_map:
                characters_map[name] = {
                    "name": name,
                    "established_facts": [],
                    "established_costume": "Not specified in screenplay",
                    "costume_recommendation": f"Standard wardrobe for {name} based on {scene.time_of_day} setting.",
                    "ai_inferred_profile": ["Role inferred from script context"]
                }
                budget["costumes"] += RATES["costume_per_new"]
            
            # Add scene fact
            if f"Present in {loc}" not in characters_map[name]["established_facts"]:
                characters_map[name]["established_facts"].append(f"Present in {loc}")
                
        # 3. Dialogues
        for line in scene.dialogue:
            char_name = line.character.upper()
            if char_name not in dialogues_map:
                dialogues_map[char_name] = []
            dialogues_map[char_name].append({
                "scene": scene_name,
                "text": line.text
            })

        # 4. Budget per scene
        is_night = "NIGHT" in scene.time_of_day.upper()
        
        loc_cost = RATES["location_per_scene"] * (RATES["exterior_location_multiplier"] if is_ext else 1.0)
        light_cost = RATES["lighting_per_scene"] * (RATES["night_lighting_multiplier"] if is_night else 1.0)
        equip_cost = RATES["equipment_per_scene"]
        cast_cost = len(scene.characters) * RATES["cast_per_actor"]
        makeup_cost = RATES["makeup_per_scene"]
        crew_cost = RATES["crew_per_scene"]
        transport_cost = RATES["transport_per_scene"]
        props_cost = 0 # Deterministic based on props, assuming 0 for now
        misc_cost = RATES["misc_per_scene"]
        
        scene_total = loc_cost + light_cost + equip_cost + cast_cost + makeup_cost + crew_cost + transport_cost + props_cost + misc_cost
        
        budget["location"] += loc_cost
        budget["lighting"] += light_cost
        budget["equipment"] += equip_cost
        budget["cast"] += cast_cost
        budget["makeup"] += makeup_cost
        budget["crew"] += crew_cost
        budget["transport"] += transport_cost
        budget["props"] += props_cost
        budget["misc"] += misc_cost
        
        budget["scene_budgets"].append({
            "scene_id": scene.id,
            "scene_name": scene_name,
            "cast": cast_cost,
            "location": loc_cost,
            "equipment": equip_cost,
            "lighting": light_cost,
            "costumes": len(scene.characters) * 500, # Per scene maintenance
            "props": props_cost,
            "makeup": makeup_cost,
            "crew": crew_cost,
            "transport": transport_cost,
            "misc": misc_cost,
            "total": scene_total + (len(scene.characters) * 500)
        })
        budget["costumes"] += (len(scene.characters) * 500)
        
        # 5. Scene Breakdown summary
        scenes_breakdown.append({
            "scene_id": scene.id,
            "scene_name": scene_name,
            "summary": scene.description[:150] + "..." if len(scene.description) > 150 else scene.description,
            "characters": scene_chars,
            "location": loc,
            "time": scene.time_of_day
        })

    budget["total"] = sum(v for k, v in budget.items() if isinstance(v, (int, float)) and k != "total")

    return {
        "characters": list(characters_map.values()),
        "locations": list(locations_map.values()),
        "scenes": scenes_breakdown,
        "dialogues": [{"character": k, "lines": v} for k, v in dialogues_map.items()],
        "budget": budget,
        "rates": RATES
    }


@router.get("/projects/{project_id}/production/scenes/{scene_id}/shots", response_model=List[ShotBlueprint])
def get_scene_shots(project_id: str, scene_id: str, db: Session = Depends(get_session)):
    plan = db.exec(select(ProductionPlan).where(ProductionPlan.project_id == project_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No production plan found.")

    shots = db.exec(
        select(ShotBlueprint).where(
            ShotBlueprint.production_plan_id == plan.id,
            ShotBlueprint.scene_id == scene_id
        )
    ).all()
    return shots


@router.get("/projects/{project_id}/production/shots/{shot_id}", response_model=ShotBlueprint)
def get_shot(project_id: str, shot_id: str, db: Session = Depends(get_session)):
    shot = db.get(ShotBlueprint, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found.")
    plan = db.get(ProductionPlan, shot.production_plan_id)
    if not plan or plan.project_id != project_id:
        raise HTTPException(status_code=404, detail="Shot does not belong to this project.")
    return shot


@router.patch("/projects/{project_id}/production/shots/{shot_id}", response_model=ShotBlueprint)
def update_shot(project_id: str, shot_id: str, update: dict, db: Session = Depends(get_session)):
    """Director can edit shot blueprint fields (subject, composition, lighting, etc.) before generation."""
    shot = db.get(ShotBlueprint, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found.")
    plan = db.get(ProductionPlan, shot.production_plan_id)
    if not plan or plan.project_id != project_id:
        raise HTTPException(status_code=404, detail="Shot does not belong to this project.")

    allowed_fields = {"subject", "character_actions", "emotion", "purpose", "story_beat",
                      "shot_size", "camera", "blocking", "composition", "lighting", "status"}
    for field, value in update.items():
        if field in allowed_fields:
            setattr(shot, field, value)

    db.add(shot)
    db.commit()
    db.refresh(shot)
    return shot


@router.post("/projects/{project_id}/production/shots/{shot_id}/approve", response_model=ShotBlueprint)
def approve_shot(project_id: str, shot_id: str, db: Session = Depends(get_session)):
    """Mark a shot blueprint as Director-approved, locking it for storyboard generation."""
    shot = db.get(ShotBlueprint, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found.")
    plan = db.get(ProductionPlan, shot.production_plan_id)
    if not plan or plan.project_id != project_id:
        raise HTTPException(status_code=404, detail="Shot does not belong to this project.")

    shot.status = ShotStatus.APPROVED
    db.add(shot)
    db.commit()
    db.refresh(shot)
    return shot


@router.post("/projects/{project_id}/production/scenes/{scene_id}/approve-all", response_model=List[ShotBlueprint])
def approve_all_shots_in_scene(project_id: str, scene_id: str, db: Session = Depends(get_session)):
    """Approve all shot blueprints in a scene in one action."""
    plan = db.exec(select(ProductionPlan).where(ProductionPlan.project_id == project_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No production plan found.")

    shots = db.exec(
        select(ShotBlueprint).where(
            ShotBlueprint.production_plan_id == plan.id,
            ShotBlueprint.scene_id == scene_id
        )
    ).all()
    for shot in shots:
        shot.status = ShotStatus.APPROVED
        db.add(shot)
    db.commit()
    for shot in shots:
        db.refresh(shot)
    return shots


# ─────────────────────────────────────────────
# Shooting Schedule
# ─────────────────────────────────────────────

class ScheduleDay(BaseModel):
    day: int
    location: str
    time_of_day: str
    scene_ids: List[str]
    shot_ids: List[str]
    shot_count: int

@router.get("/projects/{project_id}/production/schedule", response_model=List[ScheduleDay])
def get_shooting_schedule(project_id: str, db: Session = Depends(get_session)):
    """
    Generate an optimal shooting schedule by grouping shots by location + time_of_day.
    This groups shots not by story order but by production efficiency.
    """
    plan = db.exec(select(ProductionPlan).where(ProductionPlan.project_id == project_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No production plan found.")

    script = db.get(Script, plan.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found.")

    shots = db.exec(
        select(ShotBlueprint).where(ShotBlueprint.production_plan_id == plan.id)
    ).all()

    # Build a scene lookup for location/time
    scene_info: Dict[str, Dict] = {}
    for scene_dict in script.scenes:
        sid = scene_dict.get("id", "")
        scene_info[sid] = {
            "location": scene_dict.get("location", "UNKNOWN LOCATION"),
            "time_of_day": scene_dict.get("time_of_day", "DAY"),
        }

    # Group by location + time_of_day
    groups: Dict[str, Dict] = {}
    for shot in shots:
        info = scene_info.get(shot.scene_id, {"location": "UNKNOWN", "time_of_day": "DAY"})
        key = f"{info['location']}|{info['time_of_day']}"
        if key not in groups:
            groups[key] = {
                "location": info["location"],
                "time_of_day": info["time_of_day"],
                "scene_ids": set(),
                "shot_ids": [],
            }
        groups[key]["scene_ids"].add(shot.scene_id)
        groups[key]["shot_ids"].append(shot.id)

    schedule = []
    for day_num, (key, group) in enumerate(sorted(groups.items()), start=1):
        schedule.append(ScheduleDay(
            day=day_num,
            location=group["location"],
            time_of_day=group["time_of_day"],
            scene_ids=list(group["scene_ids"]),
            shot_ids=group["shot_ids"],
            shot_count=len(group["shot_ids"]),
        ))
    return schedule


# ─────────────────────────────────────────────
# Batch Storyboard Generation
# ─────────────────────────────────────────────

@router.post("/projects/{project_id}/production/scenes/{scene_id}/generate-all")
async def batch_generate_scene_storyboards(
    project_id: str,
    scene_id: str,
    req: BatchGenerateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """
    Kick off background storyboard generation for all (or selected) shots in a scene.
    Returns immediately with job metadata; poll /storyboard/shots/{shot_id} to check results.
    """
    from app.services.storyboard_agent import StoryboardAgentService
    from app.services.image_generation_service import ImageGenerationService
    from app.api.storyboard import _generate_storyboard

    plan = db.exec(select(ProductionPlan).where(ProductionPlan.project_id == project_id)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No production plan found.")

    query = select(ShotBlueprint).where(
        ShotBlueprint.production_plan_id == plan.id,
        ShotBlueprint.scene_id == scene_id
    )
    shots = db.exec(query).all()

    if req.shot_ids:
        shots = [s for s in shots if s.id in req.shot_ids]

    if not shots:
        raise HTTPException(status_code=404, detail="No shots found to generate.")

    registry = request.app.state.provider_registry
    service = StoryboardAgentService(ImageGenerationService(registry))

    async def _run_batch():
        for shot in shots:
            try:
                await _generate_storyboard(shot.id, plan.script_version, db, service)
            except Exception as e:
                print(f"[BatchGenerate] Failed shot {shot.id}: {e}")

    background_tasks.add_task(_run_batch)

    return {
        "message": f"Batch generation started for {len(shots)} shots",
        "shot_ids": [s.id for s in shots],
        "scene_id": scene_id,
    }
