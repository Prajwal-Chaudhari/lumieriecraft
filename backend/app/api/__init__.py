from fastapi import APIRouter

from .health import router as health_router
from .system import router as system_router
from .providers import router as providers_router
from .generations import router as generations_router
from .production import router as production_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(system_router, tags=["System"])
api_router.include_router(providers_router, tags=["Providers"])
api_router.include_router(generations_router, tags=["Generations"])
api_router.include_router(production_router, prefix="/projects", tags=["Production"])
