from fastapi import APIRouter, Request, HTTPException
from app.schemas.generation import GenerationRequest, GenerationResult
from app.services.image_generation_service import UnsupportedFeatureError

router = APIRouter()

@router.post("/generations", response_model=GenerationResult)
async def generate_image(req: GenerationRequest, request: Request):
    service = request.app.state.image_generation_service
    try:
        result = await service.generate(req)
        return result
    except UnsupportedFeatureError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
