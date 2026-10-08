$ErrorActionPreference = "Stop"

$comfyDir = "d:\lumieriecraft\ComfyUI"
$customNodesDir = Join-Path $comfyDir "custom_nodes"
$modelsDir = Join-Path $comfyDir "models"
$ipadapterDir = Join-Path $modelsDir "ipadapter"
$clipVisionDir = Join-Path $modelsDir "clip_vision"

Write-Host "Installing ComfyUI_IPAdapter_plus..."
if (-not (Test-Path (Join-Path $customNodesDir "ComfyUI_IPAdapter_plus"))) {
    git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git (Join-Path $customNodesDir "ComfyUI_IPAdapter_plus")
} else {
    Write-Host "ComfyUI_IPAdapter_plus already exists."
}

Write-Host "Creating model directories..."
if (-not (Test-Path $ipadapterDir)) { New-Item -ItemType Directory -Force -Path $ipadapterDir | Out-Null }
if (-not (Test-Path $clipVisionDir)) { New-Item -ItemType Directory -Force -Path $clipVisionDir | Out-Null }

Write-Host "Downloading SD 1.5 IP-Adapter model..."
$ipadapterModelPath = Join-Path $ipadapterDir "ip-adapter_sd15.safetensors"
if (-not (Test-Path $ipadapterModelPath)) {
    Invoke-WebRequest -Uri "https://huggingface.co/h94/IP-Adapter/resolve/main/models/ip-adapter_sd15.safetensors" -OutFile $ipadapterModelPath
    Write-Host "Downloaded IP-Adapter SD 1.5"
} else {
    Write-Host "IP-Adapter SD 1.5 already exists."
}

Write-Host "Downloading CLIP Vision model (ViT-H)..."
$clipVisionModelPath = Join-Path $clipVisionDir "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
if (-not (Test-Path $clipVisionModelPath)) {
    Invoke-WebRequest -Uri "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors" -OutFile $clipVisionModelPath
    Write-Host "Downloaded CLIP Vision model"
} else {
    Write-Host "CLIP Vision model already exists."
}

Write-Host "IP-Adapter Installation Complete! Please restart your ComfyUI server."
