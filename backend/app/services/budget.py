from sqlmodel import Session, select
from typing import Dict, Any
from app.models.project import Project
from app.models.script import Script
from app.models.production import SceneBreakdown

# Configurable Default Rates (in INR or chosen currency)
DEFAULT_RATES = {
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
    "exterior_location_multiplier": 1.5,
}

class BudgetService:
    def __init__(self, rates: Dict[str, float] = None):
        """
        Initialize BudgetService with optional custom rates.
        If no rates are provided, uses DEFAULT_RATES.
        """
        self.rates = rates or DEFAULT_RATES

    def calculate_budget(self, session: Session, project_id: str) -> Dict[str, Any]:
        """
        Deterministically calculates the budget for a project based on its script scenes
        and associated production data (e.g. props from SceneBreakdown).
        Does NOT use AI/LLMs.
        """
        project = session.exec(select(Project).where(Project.id == project_id)).first()
        if not project:
            raise ValueError("Project not found")

        # Get latest approved script or highest version script
        script = session.exec(
            select(Script)
            .where(Script.project_id == project_id, Script.status == "approved")
            .order_by(Script.version.desc())
        ).first()

        if not script:
            script = session.exec(
                select(Script)
                .where(Script.project_id == project_id)
                .order_by(Script.version.desc())
            ).first()

        if not script or not script.scenes:
            # Empty project / No script
            return {
                "project_id": project_id,
                "currency": "INR",
                "total": 0,
                "scenes": [],
                "category_totals": {
                    "cast": 0, "location": 0, "equipment": 0, "lighting": 0, 
                    "costumes": 0, "props": 0, "makeup": 0, "crew": 0, 
                    "transport": 0, "misc": 0
                },
                "rates": self.rates
            }

        scene_breakdowns = session.exec(
            select(SceneBreakdown).where(SceneBreakdown.project_id == project_id)
        ).all()
        breakdowns_by_scene_id = {sb.scene_id: sb for sb in scene_breakdowns}

        # We assume one costume cost per character for their first appearance.
        seen_characters = set()

        scenes_result = []
        category_totals = {
            "cast": 0,
            "location": 0,
            "equipment": 0,
            "lighting": 0,
            "costumes": 0,
            "props": 0,
            "makeup": 0,
            "crew": 0,
            "transport": 0,
            "misc": 0
        }
        
        project_total = 0

        for scene_dict in script.scenes:
            scene_id = scene_dict.get("id")
            scene_number = scene_dict.get("scene_number", 0)
            heading = scene_dict.get("heading", "").upper()
            time_of_day = scene_dict.get("time_of_day", "").upper()
            
            # Determine characters in scene from character list and dialogue
            characters_in_scene = set()
            for char_ref in scene_dict.get("characters", []):
                name = char_ref.get("name", "").strip().upper()
                if name: characters_in_scene.add(name)
            for dialogue in scene_dict.get("dialogue", []):
                name = dialogue.get("character", "").strip().upper()
                # Clean up parentheticals in character names like "JOHN (V.O.)"
                name = name.split("(")[0].strip()
                if name: characters_in_scene.add(name)
                
            num_characters = len(characters_in_scene)
            
            # Find new costumes
            new_costumes = 0
            for char_name in characters_in_scene:
                if char_name not in seen_characters:
                    new_costumes += 1
                    seen_characters.add(char_name)

            # Check breakdown for props
            breakdown = breakdowns_by_scene_id.get(scene_id)
            num_props = len(breakdown.props) if breakdown and breakdown.props else 0

            is_night = "NIGHT" in time_of_day or "NIGHT" in heading
            is_ext = "EXT" in heading

            # Calculate deterministic costs (using int for currency precision)
            cast_cost = int(num_characters * self.rates["cast_per_actor"])
            
            # Location logic: base rate * multiplier if EXT
            loc_rate = self.rates["location_per_scene"]
            if is_ext:
                loc_rate *= self.rates["exterior_location_multiplier"]
            loc_cost = int(loc_rate)
            
            equip_cost = int(self.rates["equipment_per_scene"])
            
            # Lighting logic: base rate * multiplier if NIGHT
            light_rate = self.rates["lighting_per_scene"]
            if is_night:
                light_rate *= self.rates["night_lighting_multiplier"]
            lighting_cost = int(light_rate)
            
            # Costume logic: charged only on first appearance
            costume_cost = int(new_costumes * self.rates["costume_per_new"])
            
            # Props logic: per item
            prop_cost = int(num_props * self.rates["prop_per_item"])
            
            # Flat scene costs
            makeup_cost = int(self.rates["makeup_per_scene"])
            crew_cost = int(self.rates["crew_per_scene"])
            transport_cost = int(self.rates["transport_per_scene"])
            misc_cost = int(self.rates["misc_per_scene"])
            
            scene_total = (cast_cost + loc_cost + equip_cost + lighting_cost + 
                           costume_cost + prop_cost + makeup_cost + crew_cost + 
                           transport_cost + misc_cost)
                           
            category_totals["cast"] += cast_cost
            category_totals["location"] += loc_cost
            category_totals["equipment"] += equip_cost
            category_totals["lighting"] += lighting_cost
            category_totals["costumes"] += costume_cost
            category_totals["props"] += prop_cost
            category_totals["makeup"] += makeup_cost
            category_totals["crew"] += crew_cost
            category_totals["transport"] += transport_cost
            category_totals["misc"] += misc_cost
            
            project_total += scene_total
            
            scenes_result.append({
                "scene_id": scene_id,
                "scene_number": scene_number,
                "heading": scene_dict.get("heading", ""),
                "total": scene_total,
                "breakdown": {
                    "cast": cast_cost,
                    "location": loc_cost,
                    "equipment": equip_cost,
                    "lighting": lighting_cost,
                    "costumes": costume_cost,
                    "props": prop_cost,
                    "makeup": makeup_cost,
                    "crew": crew_cost,
                    "transport": transport_cost,
                    "misc": misc_cost
                }
            })

        return {
            "project_id": project_id,
            "currency": "INR",
            "total": project_total,
            "scenes": scenes_result,
            "category_totals": category_totals,
            "rates": self.rates
        }
