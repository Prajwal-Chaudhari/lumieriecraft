# Lumierecraft — Image Generation Provider & Rendering Strategy

## Purpose

This document defines the initial image-generation architecture for **Lumierecraft**.

The goal is to build the rendering layer in a way that:

- supports free or very low-cost development and testing,
- does not permanently depend on one provider,
- allows models to be changed without rewriting the Storyboard Agent,
- supports future character consistency and structural controls,
- remains compatible with advanced research pipelines described in the project design.

---

# 1. Important Architecture Decision

**Replicate must not be hard-coded into the Storyboard Agent.**

Replicate is an inference provider, not the core rendering architecture.

The application architecture must be:

```text
Storyboard Agent
        ↓
GenerationRequest
        ↓
ImageGenerationService
        ↓
ImageGenerationProvider Interface
        │
        ├── HuggingFaceProvider
        ├── TogetherProvider
        ├── ReplicateProvider
        └── Future Providers
```

The Storyboard Agent is responsible for deciding **what image should be generated**.

The provider is responsible for deciding **how the selected model is called**.

---

# 2. Initial Provider Strategy

## Development and integration testing

Start with a free or near-free provider where possible.

Initial preference:

```text
Hugging Face Inference Providers
```

Use this primarily for:

- API integration testing,
- provider abstraction testing,
- prompt testing,
- smoke tests,
- generating a small number of storyboard frames.

The free allowance should not be treated as sufficient for large-scale production generation.

---

## Alternative low-cost provider

Support:

```text
TogetherProvider
```

A free model endpoint or provider offer must be verified against the current account and billing requirements before the application depends on it.

Do not hard-code assumptions such as:

> "Together API is always completely free."

Provider availability, account requirements, quotas, and billing policies can change.

---

## Production or higher-quality rendering

Support:

```text
ReplicateProvider
```

Replicate should be treated as a paid or usage-based provider unless the selected model or account explicitly provides free usage.

Replicate is useful because it can provide access to hosted image models and can later support more advanced deployment paths.

---

# 3. Provider-Independent Interface

Create a provider abstraction in the backend.

Example:

```python
from typing import Protocol

class ImageGenerationProvider(Protocol):
    async def generate(
        self,
        request: "GenerationRequest",
    ) -> "GenerationResult":
        ...
```

All providers must implement the same contract.

Do not place provider-specific API calls inside:

- LangGraph nodes,
- Storyboard Agent logic,
- Cinematography Agent logic,
- frontend components.

Provider-specific code belongs only inside:

```text
backend/app/providers/
```

---

# 4. Core Generation Request

Create a normalized request model.

```python
from pydantic import BaseModel, Field
from typing import Literal

class GenerationRequest(BaseModel):
    project_id: str
    scene_id: str
    shot_id: str

    prompt: str
    negative_prompt: str | None = None

    reference_images: list[str] = Field(default_factory=list)

    width: int = 1024
    height: int = 1024

    seed: int | None = None

    style: str | None = None

    mode: Literal[
        "storyboard_sketch",
        "variation",
        "cinematic_final"
    ]
```

This request must remain provider-independent.

For example:

```text
GenerationRequest
        ↓
HuggingFaceProvider
```

or:

```text
GenerationRequest
        ↓
ReplicateProvider
```

The request structure should not need to change.

---

# 5. Generation Result

Normalize provider responses.

```python
class GenerationResult(BaseModel):
    provider: str
    model: str

    generation_id: str

    image_urls: list[str]

    seed: int | None = None

    metadata: dict = Field(default_factory=dict)
```

The rest of Lumierecraft should consume this normalized result instead of raw provider responses.

---

# 6. Initial Generation Modes

Lumierecraft V1 should support three logical generation modes.

## Mode 1 — Storyboard Sketch

```text
storyboard_sketch
```

Purpose:

- previsualization,
- composition checking,
- shot validation,
- quick regeneration,
- human review.

The prompt builder should add a controlled storyboard style instruction.

Example conceptual visual direction:

```text
cinematic storyboard sketch,
production previsualization,
clear subject silhouettes,
readable composition,
strong camera framing,
monochrome or restrained grayscale,
clean linework
```

The exact wording should be configurable and stored in prompt templates rather than hard-coded throughout Python files.

---

## Mode 2 — Variation / Regeneration

```text
variation
```

Purpose:

- regenerate a rejected shot,
- create alternate framing,
- test composition changes,
- preserve as much continuity as possible.

The system should retain:

- shot ID,
- previous generation metadata,
- previous seed when supported,
- reference images,
- character context.

A rejection of one shot must not automatically regenerate the entire project.

---

## Mode 3 — Cinematic Final

```text
cinematic_final
```

This mode is available after storyboard approval.

Purpose:

- final cinematic visual,
- color treatment,
- lighting treatment,
- higher-quality rendering.

---

# 7. Storyboard Agent Responsibilities

The Storyboard Agent must not directly call a provider.

Its responsibilities are:

1. Receive the approved `ShotBlueprint`.
2. Retrieve active character references.
3. Retrieve continuity context.
4. Build a normalized visual-generation request.
5. Send the request to `ImageGenerationService`.
6. Save the normalized generation result.

Architecture:

```text
ShotBlueprint
      +
Character References
      +
Continuity Context
      +
Visual Style
          ↓
    Storyboard Agent
          ↓
   GenerationRequest
          ↓
 ImageGenerationService
          ↓
 ImageGenerationProvider
          ↓
     Provider API
          ↓
   GenerationResult
```

---

# 8. ImageGenerationService

Create:

```text
backend/app/services/image_generation_service.py
```

Responsibilities:

- choose the active provider,
- call the provider,
- handle provider errors,
- normalize results,
- persist generation metadata,
- expose a single application-level generation API.

Example conceptual interface:

```python
class ImageGenerationService:

    def __init__(
        self,
        provider: ImageGenerationProvider,
    ):
        self.provider = provider

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        return await self.provider.generate(request)
```

Do not make the service aware of cinematography reasoning.

Do not make providers aware of project workflow logic.

---

# 9. Provider Implementations

Create:

```text
backend/app/providers/
│
├── base.py
├── huggingface_provider.py
├── replicate_provider.py
├── together_provider.py
└── registry.py
```

## Base

Contains:

```python
ImageGenerationProvider
```

## Hugging Face Provider

Initial provider for:

- development,
- API integration,
- small-scale testing.

Credentials must come from environment variables.

Example:

```text
HUGGINGFACE_API_TOKEN=
```

Do not commit tokens.

---

## Replicate Provider

Used as a supported provider, but not assumed to be free.

Environment variable:

```text
REPLICATE_API_TOKEN=
```

Model identifiers must be configuration-driven.

Do not hard-code model names into agents.

---

## Together Provider

Environment variable:

```text
TOGETHER_API_KEY=
```

Use only after validating the currently available model and account requirements.

---

# 10. Provider Registry

Implement a provider registry.

Example conceptual design:

```python
class ProviderRegistry:

    def get(self, provider_name: str) -> ImageGenerationProvider:
        ...
```

Configuration:

```text
IMAGE_GENERATION_PROVIDER=huggingface
```

Possible values:

```text
huggingface
replicate
together
```

Changing the provider should require configuration changes, not rewriting application logic.

---

# 11. Model Configuration

Do not write code such as:

```python
replicate.run("hardcoded-model-name")
```

Instead:

```text
backend/app/core/config.py
```

Example:

```text
IMAGE_GENERATION_PROVIDER=huggingface

HF_IMAGE_MODEL=
REPLICATE_IMAGE_MODEL=
TOGETHER_IMAGE_MODEL=
```

Model identifiers can change independently of application architecture.

---

# 12. Continuity Strategy for V1

The original Lumierecraft research discusses several advanced techniques, including:

- IP-Adapter identity conditioning,
- StoryDiffusion-style consistent self-attention,
- Story-LDM-style visual memory,
- EMControl,
- structural control modules.

These should **not** be falsely represented as fully implemented in the initial V1 unless they are actually integrated and demonstrated.

For V1, continuity should use an application-level continuity context.

```text
Character Registry
       +
Character References
       +
Appearance Metadata
       +
Location Context
       +
Previous Shot Context
       +
Stable Prompt Fragments
       +
Optional Seed Reuse
            ↓
    Continuity Context
            ↓
      Generation Request
```

Example:

```text
Character:
Prajwal

Appearance:
young engineering student,
short dark hair,
glasses,
blue shirt,
black backpack

Current Location:
engineering college classroom

Previous Shot:
Prajwal entered through the classroom door.

Current Shot:
medium close-up of Prajwal reacting to someone off-camera.
```

This is the initial practical continuity layer.

---

# 13. Future Consistency Engines

The architecture must allow future consistency implementations.

Create an abstraction:

```python
class ConsistencyEngine(Protocol):

    async def prepare_context(
        self,
        ...
    ):
        ...

    async def generate_sequence(
        self,
        ...
    ):
        ...
```

Potential implementations:

```text
BasicConsistencyEngine
ReferenceConditioningEngine
IPAdapterEngine
ControlNetEngine
Story2StoryboardEngine
Story2BoardEngine
```

These are future implementations.

Do not pretend they exist in V1 unless their actual pipelines are implemented.

---

# 14. FLUX / SDXL / Future Model Compatibility

Lumierecraft must not be architecturally tied to one model family.

The system should support the concept:

```text
Agent Output
      ↓
Normalized GenerationRequest
      ↓
Provider
      ↓
Model Adapter / Provider Mapping
      ↓
Selected Model
```

Different model families may support different features.

For example:

```text
Model A:
- text prompt
- seed

Model B:
- text prompt
- reference image
- control image

Model C:
- custom consistency pipeline
```

The provider layer or model adapter must map the normalized request to the capabilities of the selected model.

Unsupported features should fail clearly or degrade predictably.

---

# 15. Color Treatment Architecture

The Cinematography Agent is responsible for recommending the visual look.

It should produce structured color information instead of only vague words such as:

```text
moody
warm
cinematic
```

Use:

```python
class ColorRecommendation(BaseModel):
    palette_hex: list[str] = Field(
        default_factory=list
    )

    temperature: str
    contrast: str
    saturation: str

    lighting_ratio: str | None = None

    film_stock_reference: str | None = None
    lut_reference: str | None = None

    mood: str
    explanation: str
```

This recommendation is descriptive and structured.

It does not automatically mean that a named LUT has actually been applied.

---

# 16. Two-Step Visual Workflow

Lumierecraft should use:

```text
Cinematography Plan
        ↓
Storyboard Sketch Generation
        ↓
Human Review
        │
   ┌────┴─────┐
   │          │
Reject      Approve
   │          │
   ▼          ▼
Regenerate  Color Treatment
                ↓
          Final Rendering
```

This preserves the filmmaker's control.

The user should not spend expensive rendering resources before approving the composition.

---

# 17. Human Approval Rules

Every generation should have a status.

```text
pending
generating
generated
approved
rejected
failed
```

A rejected shot should support:

- regenerate with same instructions,
- regenerate with modified instructions,
- change shot parameters,
- generate variations.

Only affected downstream artifacts should be regenerated when possible.

---

# 18. API Design

Suggested endpoints:

```text
POST /api/shots/{shot_id}/storyboard/generate

POST /api/shots/{shot_id}/storyboard/regenerate

POST /api/shots/{shot_id}/approve

POST /api/shots/{shot_id}/reject

GET /api/generations/{generation_id}

GET /api/shots/{shot_id}/generations
```

For color:

```text
GET  /api/shots/{shot_id}/color

POST /api/shots/{shot_id}/color/apply
```

Long-running generation must use a job/status model.

Do not keep a single HTTP request open indefinitely.

---

# 19. Database Requirements

Persist:

```text
Project
Scene
Shot
ShotBlueprint
Generation
GenerationStatus
Provider
Model
Seed
PromptVersion
ReferenceImages
ApprovalStatus
ColorRecommendation
```

A generation record should contain enough metadata to understand:

```text
What was generated?
With which prompt?
With which provider?
With which model?
Using which references?
With which seed?
When?
Was it approved or rejected?
```

---

# 20. Prompt Management

Prompts must not be scattered through Python functions.

Use:

```text
prompts/
│
├── storyboard/
│   ├── sketch.md
│   ├── variation.md
│   └── cinematic_final.md
│
├── cinematographer/
│   └── system.md
│
└── script_doctor/
    └── system.md
```

The application should support prompt version tracking.

---

# 21. Environment Configuration

Create `.env.example`.

Example:

```env
# Application
ENVIRONMENT=development

# Database
DATABASE_URL=

# LLM
LLM_PROVIDER=
LLM_API_KEY=

# Image generation provider selection
IMAGE_GENERATION_PROVIDER=huggingface

# Hugging Face
HUGGINGFACE_API_TOKEN=
HF_IMAGE_MODEL=

# Replicate
REPLICATE_API_TOKEN=
REPLICATE_IMAGE_MODEL=

# Together
TOGETHER_API_KEY=
TOGETHER_IMAGE_MODEL=

# Storage
STORAGE_PROVIDER=local
```

Never commit real API keys.

---

# 22. Required Error Handling

The application must handle:

```text
Invalid API key
Provider unavailable
Model unavailable
Generation timeout
Rate limit
Unsupported model capability
Invalid reference image
Provider response parsing failure
Generation failure
```

Every error should be saved to the generation job and surfaced clearly to the frontend.

Do not silently mark failed generations as successful.

---

# 23. Initial Implementation Priority

Implement in this exact order.

## Phase 1 — Foundation

Create:

```text
frontend/
backend/
database/
Docker configuration
environment configuration
```

## Phase 2 — Provider Abstraction

Implement:

```text
GenerationRequest
GenerationResult
ImageGenerationProvider
ImageGenerationService
ProviderRegistry
```

Do this before integrating a real provider.

## Phase 3 — Mock Provider

Create:

```text
MockImageGenerationProvider
```

It should return deterministic mock responses.

This allows the complete workflow to be tested without API credits.

## Phase 4 — First Real Provider

Integrate the selected Hugging Face image-generation path for real API testing.

Keep the provider implementation isolated.

## Phase 5 — Storyboard Agent Integration

Connect:

```text
ShotBlueprint
      ↓
Continuity Context
      ↓
GenerationRequest
      ↓
ImageGenerationService
```

## Phase 6 — Approval and Regeneration

Implement shot status transitions.

## Phase 7 — Replicate Provider

Add Replicate as an additional provider.

Do not modify the Storyboard Agent to do this.

## Phase 8 — Advanced Consistency

Only after the basic system works:

- reference conditioning,
- IP-Adapter-compatible paths where applicable,
- ControlNet-compatible structural controls,
- research pipelines,
- custom hosted inference.

---

# 24. Acceptance Criteria

The implementation is complete when the following works:

### Test 1

```text
Create project
        ↓
Create scene
        ↓
Create shot
```

### Test 2

```text
ShotBlueprint
        ↓
GenerationRequest
        ↓
Mock Provider
        ↓
GenerationResult
```

### Test 3

Switch configuration:

```text
IMAGE_GENERATION_PROVIDER=huggingface
```

The same application workflow uses the Hugging Face provider.

### Test 4

Switch configuration:

```text
IMAGE_GENERATION_PROVIDER=replicate
```

No Storyboard Agent code changes are required.

### Test 5

Generate storyboard image.

### Test 6

Reject only one shot.

### Test 7

Regenerate only that shot.

### Test 8

Approve shot.

### Test 9

Generate or apply the selected final visual treatment.

---

# 25. Non-Negotiable Rules for Antigravity

1. **Do not hard-code Replicate into the Storyboard Agent.**
2. **Do not assume any provider is permanently free.**
3. **Do not store API keys in source code.**
4. **Do not implement fake advanced consistency features and claim they work.**
5. **Do not build custom diffusion training in V1.**
6. **Use provider abstractions from the beginning.**
7. **Use a mock provider before spending API credits.**
8. **Persist generation metadata.**
9. **Support shot-level regeneration.**
10. **Keep prompts versioned and outside core business logic.**
11. **Keep model names configurable.**
12. **Make provider failures explicit.**
13. **Do not rewrite the entire project when only one shot changes.**
14. **Keep the user in the approval loop.**

---

# Final Architecture

```text
                    LUMIERECRAFT

                         │
                         ▼

                 CINEMATOGRAPHY AGENT
                         │
                         │ ShotBlueprint
                         ▼

                  STORYBOARD AGENT
                         │
                         ├── Character References
                         ├── Continuity Context
                         └── Visual Style
                         │
                         ▼

                  GenerationRequest
                         │
                         ▼

              IMAGE GENERATION SERVICE
                         │
                         ▼

                  PROVIDER REGISTRY
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼

      HUGGING FACE    REPLICATE    TOGETHER
            │            │            │
            └────────────┼────────────┘
                         │
                         ▼

                  GenerationResult
                         │
                         ▼

                 STORYBOARD SKETCH
                         │
                         ▼

                   HUMAN REVIEW
                    │        │
                 Reject    Approve
                    │        │
                    ▼        ▼
               Regenerate   Color
                              │
                              ▼
                       Final Visual
```

---

# Final Instruction

Build the image-generation layer exactly around this architecture.

Start with:

1. domain models,
2. provider abstraction,
3. provider registry,
4. mock provider,
5. generation service,
6. database persistence,
7. API endpoints,
8. first real provider integration.

Do **not** begin with advanced custom diffusion pipelines.

The first objective is a reliable, provider-independent storyboard generation system that can be tested with mock responses and then connected to free or low-cost real image-generation APIs.
