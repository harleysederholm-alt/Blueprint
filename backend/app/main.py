"""
RepoBlueprint AI - FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import analyze, diagrams, health, diff, export, query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Ollama model: {settings.ollama_model}")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")
    
    # Ensure cache directories exist
    settings.get_repos_path()
    settings.get_analysis_path()
    
    yield
    
    # Shutdown
    logger.info("Shutting down RepoBlueprint AI")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Architectural Intelligence Engine - Evidence-based architecture understanding",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, tags=["Health"])
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(diagrams.router, prefix="/api", tags=["Diagrams"])
app.include_router(diff.router, prefix="/api", tags=["Diff"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(query.router, prefix="/api", tags=["Query"])


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
