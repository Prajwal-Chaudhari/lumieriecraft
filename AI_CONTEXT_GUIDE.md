# ?? Antigravity / AI Context Guide: Lumierecraft Studio

*If you are an AI agent reading this, this document contains the exact context, architecture, and current state of the project. Read this to get fully up to speed before making modifications.*

## ?? Project Overview
**Lumierecraft Studio** is an AI-native film pre-production pipeline. It takes a raw screenplay or concept and automates the pre-production process across four major phases:
1. **Script Standardization:** Cleans up formatting and structures raw text into industry-standard screenplays using Gemini/Groq.
2. **Production Intelligence:** A deterministic engine that reads the script and extracts Character Bibles, World Bibles, Costume Recommendations, and Scene-by-Scene Budget Estimates.
3. **Cinematography:** An LLM-powered engine that analyzes scenes and generates a structured, shot-by-shot camera and lighting blueprint.
4. **Storyboard Engine:** A local ComfyUI integration that uses Stable Diffusion v1.5 to generate visualization frames for every shot blueprint.

## ??? Architecture Stack
- **Frontend (`/frontend`)**: Next.js 14, React, Tailwind CSS, TypeScript.
- **Backend (`/backend`)**: FastAPI, Python 3.10+, SQLModel (SQLite database).
- **AI Integration**:
  - LLMs: Google Gemini (`google-genai` SDK) & Groq for text processing.
  - Image Generation: A self-contained **ComfyUI** instance (`/ComfyUI`) serving on port `8188`.
  - The backend communicates with ComfyUI asynchronously via its `/prompt` HTTP endpoint.

## ?? Strict User Preferences & Rules (DO NOT DEVIATE)
1. **Deterministic Logic over AI Hallucination:** The user specifically requested that things like **Budget Estimation** and **Costume Mapping** must be handled by deterministic backend code (Python math/mapping), *not* by asking the LLM to guess prices.
2. **UI Design Standard:** The frontend must feel like a premium, sleek, dark-themed dashboard. It should **never** look like a generic "AI-generated" Bootstrap page.
3. **Data Grouping:** Dialogues must be grouped character-wise. Bibles must consolidate data securely.
4. **Tool Execution:** Do not use `cat` or `sed` inside bash. Use the agent's native file modification tools (`replace_file_content`). Windows PowerShell is the default shell.

## ??? Agentic Auto-Setup Guide (For Future Agents)
**If you are an Antigravity agent on a NEW laptop**, execute the following steps to initialize this repository for the user. Do not wait for the user to do this manually.

### 1. Frontend Setup
Run this in PowerShell to install Node modules:
```powershell
cd frontend
npm install
# Do not start `npm run dev` as a blocking command. Run it in the background if needed.
```

### 2. Backend Setup
Run this in PowerShell to create a fresh virtual environment (do NOT reuse old ones if they were transferred from a zip):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Ensure .env exists in the root with GEMINI_API_KEY and GROQ_API_KEY
```

### 3. ComfyUI & AI Model Setup (NVIDIA GPU)
If the user cloned this fresh, you must set up the ComfyUI python environment using `uv` to ensure they get the correct Python version (3.12) and the CUDA drivers for their NVIDIA GPU (e.g., GTX 1650/RTX 3050).
```powershell
# 1. Install uv (if not installed)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
$env:Path = "$HOME\.local\bin;$env:Path"

# 2. Setup Venv and Install CUDA PyTorch
cd ComfyUI
uv venv venv --python 3.12
uv pip install -p venv\Scripts\python.exe -r requirements.txt
uv pip install -p venv\Scripts\python.exe torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. Automatically download the SD1.5 model (4.27GB). Use a background task for this!
curl.exe -L "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" -o "models\checkpoints\v1-5-pruned-emaonly.safetensors"
```

## ?? How to Run the Environment (3 Servers)
To test the pipeline end-to-end, you need to ensure three processes are running simultaneously. **Always use background tasks (daemon mode) to run these.**

**1. The Backend (API Server)**
```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --env-file ../.env
```

**2. The Frontend (Next.js)**
```powershell
cd frontend
npm run dev
```

**3. The Storyboard Engine (ComfyUI)**
```powershell
cd ComfyUI
.\venv\Scripts\activate
python main.py
```

## ?? Known Issues, Gotchas, and Solutions
We have encountered and solved several critical issues. If you hit any of these, use the solutions below:

**1. Cinematography 400 Bad Request on "Apply"**
- **Problem**: When a user standardizes a script, the `script_version` bumps. When they try to apply an older Cinematography proposal, the backend throws a `400 Bad Request` because the IDs mismatch.
- **Solution**: The `apply_cinematography_proposal` logic in `app/api/cinematography.py` was updated to dynamically map the old proposal's scene IDs to the newly created script's active scenes (using scene index mapping), rather than strict ID matching. Stale proposals are now marked as `SUPERSEDED`. 

**2. Storyboard "Generation Failed" (ComfyUI Connection)**
- **Problem**: AI coding tools often restart the server or session, silently killing all background processes (like ComfyUI). The UI shows `Failed to connect to ComfyUI at 127.0.0.1:8188`.
- **Solution**: Use the `manage_task` or `run_command` tools to restart the ComfyUI daemon (`python main.py` inside the ComfyUI folder) in the background. Ensure the Next.js and FastAPI servers are also revived.

**3. Next.js "Cannot create components during render" / Hydration Errors**
- **Problem**: Next.js throws hard compile errors if a helper component (like `const LinkItem = ...`) is declared *inside* the render function of a client component, or if HTML tags (like `<div>`) are improperly closed.
- **Solution**: Move helper components outside the main functional component body, and rigorously check JSX syntax.

**4. Poor Storyboard Image Quality (Prompting Strategy)**
- **Problem**: Raw structural LLM outputs (e.g., `CAMERA: Medium Shot \n LIGHTING: Low Key`) resulted in extremely poor images from Stable Diffusion, as text-to-image models don't parse rigid formatting well.
- **Solution**: The `compile_prompt` function in `storyboard_agent.py` was rewritten. Instead of rigid sections, it now combines all technical metadata into a fluid, comma-separated tag list (e.g., `"Professional cinematic storyboard, pencil sketch style, featuring John, set in office, medium shot..."`). **Always format ComfyUI prompts as fluid aesthetic tags.**

**5. UI Stalls / Unresponsive Buttons**
- **Problem**: Users click "Apply" or "Generate" and nothing happens because the frontend `fetch` call failed silently.
- **Solution**: We added rigorous error catching blocks on the frontend (e.g., rendering red alert banners) and success modals that explicitly guide the user to the next logical step (e.g., Cinematography -> Proceed to Storyboard). Always build robust UI states (loading, error, success).
