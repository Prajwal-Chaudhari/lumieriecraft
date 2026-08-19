from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

def get_known_providers(registry):
    providers_info = []
    
    # Mock Provider
    from app.providers.mock_provider import MockImageGenerationProvider
    providers_info.append({
        "name": "mock",
        "configured": "mock" in registry._providers,
        "available": True,
        "capabilities": MockImageGenerationProvider.get_capabilities().model_dump()
    })
    
    # Pixazo Provider
    from app.providers.pixazo_provider import PixazoProvider
    is_pixazo_configured = "pixazo" in registry._providers
    providers_info.append({
        "name": "pixazo",
        "configured": is_pixazo_configured,
        "available": is_pixazo_configured,
        "capabilities": PixazoProvider.get_capabilities().model_dump()
    })
            
    # HuggingFace Provider
    from app.providers.huggingface_provider import HuggingFaceProvider
    is_hf_configured = "huggingface" in registry._providers
    providers_info.append({
        "name": "huggingface",
        "configured": is_hf_configured,
        "available": is_hf_configured,
        "capabilities": HuggingFaceProvider.get_capabilities().model_dump()
    })
            
    return providers_info

@router.get("/providers")
async def list_providers(request: Request):
    registry = request.app.state.provider_registry
    return get_known_providers(registry)

@router.get("/providers/{provider_name}")
async def get_provider(provider_name: str, request: Request):
    registry = request.app.state.provider_registry
    providers = get_known_providers(registry)
    for p in providers:
        if p["name"] == provider_name:
            return p
    raise HTTPException(status_code=404, detail="Provider not found")
