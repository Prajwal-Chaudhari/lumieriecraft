from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

from app.api.health import router as health_router
from app.api.system import router as system_router
from app.api.providers import router as providers_router
from app.api.generations import router as generations_router
from app.api.projects import router as projects_router
from app.api.cinematography import router as cinematography_router
from app.api.storyboard import router as storyboard_router
from app.db import create_db_and_tables
from app.services.image_generation_service import ImageGenerationService
from app.providers.registry import ProviderRegistry
import app.models.production  # Ensure production models are registered

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database
    create_db_and_tables()
    yield

app = FastAPI(
    title="Lumierecraft Backend API",
    description="Development API for Lumierecraft Core Services",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup singleton services
registry = ProviderRegistry()
service = ImageGenerationService(registry)
app.state.provider_registry = registry
app.state.image_generation_service = service

# Mount static files correctly by resolving absolute path
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True) # Ensure it exists just in case
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API routes
app.include_router(health_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(providers_router, prefix="/api")
app.include_router(generations_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(cinematography_router, prefix="/api")
app.include_router(storyboard_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
