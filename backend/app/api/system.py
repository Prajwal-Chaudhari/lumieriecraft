from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/system/status")
async def system_status(request: Request):
    registry = request.app.state.provider_registry
    
    configured_providers = list(registry._providers.keys())
    
    return {
        "image_generation": {
            "status": "Online",
            "active_providers": configured_providers
        },
        "agents": {
            "storyboard": {"status": "Not Implemented", "available": False},
            "script": {"status": "Not Implemented", "available": False},
            "cinematography": {"status": "Not Implemented", "available": False},
            "continuity": {"status": "Not Implemented", "available": False}
        }
    }
