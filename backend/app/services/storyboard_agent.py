import json
import uuid
from typing import Optional, List
from pydantic import BaseModel
from app.models.production import (
    ShotBlueprint, SceneBreakdown, CharacterBible, WorldBible, StoryboardFrame
)
from app.models.project import Project
from app.schemas.storyboard import StoryboardGenerationContext
from app.schemas.generation import GenerationRequest, GenerationResult
from app.services.image_generation_service import ImageGenerationService

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
        """
        prompt_parts = []

        if context.camera or context.composition or context.lighting:
            prompt_parts.append("CAMERA:")
            if context.camera:
                prompt_parts.append(context.camera)
            if context.composition:
                prompt_parts.append(context.composition)
            if context.lighting:
                prompt_parts.append(context.lighting)
            prompt_parts.append("")

        if context.environment_context:
            prompt_parts.append("ENVIRONMENT:")
            prompt_parts.append(context.environment_context)
            prompt_parts.append("")

        if context.character_context:
            prompt_parts.append("SUBJECT:")
            for char_ctx in context.character_context:
                prompt_parts.append(char_ctx)
            prompt_parts.append("")

        if context.visual_style:
            prompt_parts.append("STYLE:")
            prompt_parts.append(context.visual_style)
            prompt_parts.append("")
            
        if context.continuity_context:
            prompt_parts.append("CONTEXT:")
            prompt_parts.append(context.continuity_context)
            prompt_parts.append("")

        return "\n".join(prompt_parts).strip()

    def create_generation_context(self, shot: ShotBlueprint, scene: SceneBreakdown, characters: List[CharacterBible], world: Optional[WorldBible], project: Project) -> StoryboardGenerationContext:
        """
        Assemble the technical and narrative decisions from production data.
        """
        # Collect character contexts
        character_contexts = []
        shot_chars = set()
        
        if shot.subject:
            shot_chars.add(shot.subject)
        if shot.character_actions:
            shot_chars.add(shot.character_actions) # Simplistic tracking for now
        
        # Try to find relevant characters based on scene and shot text
        for char in characters:
            in_scene = char.name in scene.characters
            in_shot = (shot.subject and char.name in shot.subject) or (shot.character_actions and char.name in shot.character_actions) or (shot.visual_prompt and char.name in shot.visual_prompt)
            if in_scene or in_shot:
                char_str = f"{char.name}"
                if char.appearance:
                    char_str += f", {char.appearance}"
                if char.clothing:
                    char_str += f", wearing {char.clothing}"
                character_contexts.append(char_str)

        # Assemble camera and technical decisions
        camera_parts = []
        if shot.shot_size: camera_parts.append(shot.shot_size)
        if shot.lens: camera_parts.append(shot.lens)
        if shot.camera_angle: camera_parts.append(shot.camera_angle)
        if shot.camera_movement: camera_parts.append(shot.camera_movement)
        camera_str = ", ".join(camera_parts)
        
        # Compile final base context
        context = StoryboardGenerationContext(
            shot_id=shot.id,
            scene_id=shot.scene_id,
            character_context=character_contexts,
            environment_context=f"{scene.location} - {scene.time_of_day}" + (f"\n{world.environment}" if world and world.environment else ""),
            continuity_context=f"{shot.story_beat}\nEmotion: {shot.emotion}\nPurpose: {shot.purpose}",
            visual_style=project.visual_style or "",
            lighting=shot.lighting or "",
            composition=shot.composition or "",
            camera=camera_str,
            final_prompt="",
            negative_prompt=None
        )
        
        # Add visual prompt details to character context if provided
        if shot.visual_prompt:
            context.character_context.append(f"Action: {shot.visual_prompt}")
        elif shot.character_actions:
            context.character_context.append(f"Action: {shot.character_actions}")
            
        context.final_prompt = self.compile_prompt(context)
        
        # Determine if we should set negative prompt based on provider capabilities
        # We leave it None for Pixazo, since supports_negative_prompt=False.
        context.negative_prompt = None

        return context

    async def generate_storyboard(self, shot: ShotBlueprint, scene: SceneBreakdown, characters: List[CharacterBible], world: Optional[WorldBible], project: Project, script_version: int) -> StoryboardFrame:
        # Build Context
        context = self.create_generation_context(shot, scene, characters, world, project)
        
        # Build Request
        gen_request = GenerationRequest(
            project_id=project.id,
            scene_id=shot.scene_id,
            shot_id=shot.id,
            prompt=context.final_prompt,
            negative_prompt=context.negative_prompt,
            mode="storyboard_sketch"
        )
        
        # Call Service (No direct Pixazo call)
        result: GenerationResult = await self.image_service.generate(gen_request)
        
        # Create Frame
        frame = StoryboardFrame(
            project_id=project.id,
            production_plan_id=shot.production_plan_id,
            script_id=project.id, # Using project.id for now since script.project_id is standard
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
