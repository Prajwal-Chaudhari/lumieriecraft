import json
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.models.production import (
    ProductionPlan,
    ShotBlueprint,
    StoryboardFrame,
    ShotStatus
)
from app.models.project import Project, CharacterAsset
from app.schemas.storyboard import StoryboardGenerationContext
from app.schemas.generation import GenerationRequest, GenerationResult
from app.services.image_generation_service import ImageGenerationService
from app.providers.registry import ProviderRegistry
from app.providers.pixazo_provider import PixazoProvider

class StoryboardAgentService:
    def __init__(self, image_service: ImageGenerationService = None):
        if image_service is None:
            registry = ProviderRegistry()
            registry.register("pixazo", PixazoProvider())
            self.image_service = ImageGenerationService(registry)
        else:
            self.image_service = image_service

    def compile_prompt(self, context: StoryboardGenerationContext) -> str:
        """
        Deterministically compile the prompt from the storyboard context.
        Preserves the cinematographer's technical decisions verbatim.
        Excludes color and LUT to ensure B&W styling.
        """
        prompt_parts = []
        
        # 1. B&W Storyboard Style
        prompt_parts.append("STYLE:")
        prompt_parts.append("Black-and-white storyboard sketch / animated previsualization. High contrast, clear staging.")
        prompt_parts.append("")

        # 2. Cinematography (Camera, Lens, Composition, Blocking, Lighting)
        if context.camera or context.composition or context.lighting:
            prompt_parts.append("CINEMATOGRAPHY:")
            if context.camera:
                prompt_parts.append(context.camera)
            if context.composition:
                prompt_parts.append(context.composition)
            if context.lighting:
                prompt_parts.append(context.lighting)
            prompt_parts.append("")

        # 3. Environment
        if context.environment_context:
            prompt_parts.append("ENVIRONMENT:")
            prompt_parts.append(context.environment_context)
            prompt_parts.append("")

        # 4. Characters
        if context.character_context:
            prompt_parts.append("SUBJECT / BLOCKING:")
            for char_ctx in context.character_context:
                prompt_parts.append(char_ctx)
            prompt_parts.append("")
            
        # 5. Story Beat
        if context.continuity_context:
            prompt_parts.append("ACTION / STORY BEAT:")
            prompt_parts.append(context.continuity_context)
            prompt_parts.append("")

        return "\n".join(prompt_parts).strip()

    def create_generation_context(self, shot: ShotBlueprint, scene: Dict[str, Any], characters: List[CharacterAsset]) -> StoryboardGenerationContext:
        """
        Assemble the technical and narrative decisions from production data.
        """
        # Collect character contexts
        character_contexts = []
        
        # We try to find which character assets are present in the shot.
        shot_text = " ".join(filter(None, [shot.subject, shot.character_actions, shot.story_beat]))
        scene_chars = [c.get("name", "") for c in scene.get("characters", [])]
        
        # For relevant characters
        for asset in characters:
            in_scene = asset.character_name in scene_chars
            in_shot = asset.character_name in shot_text
            
            if in_scene or in_shot:
                char_str = asset.character_name
                if asset.description:
                    char_str += f": {asset.description}"
                if asset.continuity_notes:
                    char_str += f" ({asset.continuity_notes})"
                character_contexts.append(char_str)

        # Assemble camera and technical decisions
        camera_parts = []
        if shot.shot_size: camera_parts.append(shot.shot_size)
        if shot.camera:
            if isinstance(shot.camera, dict):
                camera_parts.extend([f"{k}: {v}" for k, v in shot.camera.items()])
            else:
                camera_parts.append(str(shot.camera))
                
        camera_str = ", ".join(camera_parts)
        
        composition_parts = []
        if shot.blocking:
            if isinstance(shot.blocking, dict):
                composition_parts.append("Blocking: " + ", ".join([f"{k}: {v}" for k, v in shot.blocking.items()]))
            else:
                composition_parts.append("Blocking: " + str(shot.blocking))
                
        if shot.composition:
            if isinstance(shot.composition, dict):
                composition_parts.append("Composition: " + ", ".join([f"{k}: {v}" for k, v in shot.composition.items()]))
            else:
                composition_parts.append("Composition: " + str(shot.composition))
                
        composition_str = " | ".join(composition_parts)
        
        lighting_str = ""
        if shot.lighting:
            if isinstance(shot.lighting, dict):
                lighting_str = "Lighting: " + ", ".join([f"{k}: {v}" for k, v in shot.lighting.items()])
            else:
                lighting_str = "Lighting: " + str(shot.lighting)
        
        # Compile final base context
        location = scene.get("location", "")
        time_of_day = scene.get("time_of_day", "")
        
        context = StoryboardGenerationContext(
            shot_id=shot.id,
            scene_id=shot.scene_id,
            character_context=character_contexts,
            environment_context=f"{location} - {time_of_day}",
            continuity_context=f"{shot.story_beat}\nEmotion: {shot.emotion or ''}\nPurpose: {shot.purpose or ''}",
            visual_style="", # Style is hardcoded to B&W sketch in compile_prompt
            lighting=lighting_str,
            composition=composition_str,
            camera=camera_str,
            final_prompt="",
            negative_prompt=None
        )
        
        # Add visual prompt details to character context if provided
        if shot.subject:
            context.character_context.append(f"Subject Focus: {shot.subject}")
        if shot.character_actions:
            context.character_context.append(f"Action Detail: {shot.character_actions}")
            
        context.final_prompt = self.compile_prompt(context)
        context.negative_prompt = None

        return context

    async def generate_storyboard(self, shot: ShotBlueprint, scene: Dict[str, Any], characters: List[CharacterAsset], project: Project, script_version: int) -> StoryboardFrame:
        # Build Context
        context = self.create_generation_context(shot, scene, characters)
        
        # We filter CharacterAssets that belong to the shot, passing references to GenerationRequest
        # Note: We acknowledge Pixazo FLUX Schnell reference support is currently limited.
        reference_images = []
        shot_text = " ".join(filter(None, [shot.subject, shot.character_actions, shot.story_beat]))
        for asset in characters:
            if asset.character_name in shot_text and asset.file_path:
                # Local paths are expected or URLs. The provider handles them.
                reference_images.append(asset.file_path)

        # Build Request
        gen_request = GenerationRequest(
            project_id=project.id,
            scene_id=shot.scene_id,
            shot_id=shot.id,
            prompt=context.final_prompt,
            negative_prompt=context.negative_prompt,
            reference_image_urls=reference_images,
            mode="storyboard_sketch"
        )
        
        # Call Service (No direct Pixazo call)
        result: GenerationResult = await self.image_service.generate(gen_request)
        
        # Create Frame
        frame = StoryboardFrame(
            project_id=project.id,
            production_plan_id=shot.production_plan_id,
            script_id=project.id, # Using project.id for script_id based on previous comment
            script_version=script_version,
            scene_id=shot.scene_id,
            shot_id=shot.id,
            generation_id=result.generation_id,
            provider=result.provider,
            model=result.model,
            image_url=result.image_urls[0] if result.image_urls else "",
            prompt=context.final_prompt,
            generation_metadata=result.metadata,
            status="COMPLETED" if result.image_urls else "FAILED",
            error_message=None if result.image_urls else "No images returned"
        )
        return frame
