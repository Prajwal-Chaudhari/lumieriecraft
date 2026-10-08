$ErrorActionPreference = "Stop"

$comfyDir = "d:\lumieriecraft\ComfyUI"

if (-not (Test-Path $comfyDir)) {
    Write-Host "Cloning ComfyUI..."
    git clone https://github.com/comfyanonymous/ComfyUI.git $comfyDir
} else {
    Write-Host "ComfyUI directory already exists."
}

Set-Location $comfyDir

if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

Write-Host "Installing dependencies..."
# Install PyTorch with CUDA 12.1 support
.\venv\Scripts\python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
.\venv\Scripts\python -m pip install -r requirements.txt

$modelPath = "$comfyDir\models\checkpoints\v1-5-pruned-emaonly.safetensors"
if (-not (Test-Path $modelPath)) {
    Write-Host "Downloading SD 1.5 Model (This may take a while, it's ~4GB)..."
    # Use Invoke-WebRequest to download the model
    Invoke-WebRequest -Uri "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" -OutFile $modelPath
    Write-Host "Model downloaded successfully."
} else {
    Write-Host "Model already exists."
}

Write-Host "Starting ComfyUI..."
.\venv\Scripts\python main.py
