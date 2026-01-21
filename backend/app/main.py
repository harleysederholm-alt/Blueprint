"""
RepoBlueprint AI - FastAPI Application Entry Point.

This module configures and launches the FastAPI application, serving as the
central entry point for the backend services. It orchestrates middleware
configuration, router registration, and lifecycle management including
initialization of critical resources like cache directories.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

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
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler for startup and shutdown events.

    This context manager handles the initialization and cleanup of resources
    during the application's lifecycle. It ensures that necessary configurations
    are loaded, cache directories are created, and logs important startup information.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Yields control back to the application.
    """
    try:
        # Startup
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Ollama model: {settings.ollama_model}")
        logger.info(f"Ollama URL: {settings.ollama_base_url}")
        
        # Ensure cache directories exist - critical for operation
        start_up_errors = []
        try:
            settings.get_repos_path()
        except Exception as e:
            start_up_errors.append(f"Failed to create repos path: {e}")
            
        try:
            settings.get_analysis_path()
        except Exception as e:
            start_up_errors.append(f"Failed to create analysis path: {e}")
            
        if start_up_errors:
            for error in start_up_errors:
                logger.error(error)
            # We might want to raise here depending on strictness, but logging allows debugging
            logger.critical("Application started with storage initialization errors.")
            
    except Exception as e:
        logger.critical(f"Critical error during startup: {e}")
        # In a real scenario, re-raising might be appropriate to stop deployment
        
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
async def root() -> Dict[str, str]:
    """
    Root endpoint providing API information and health check paths.

    Returns:
        Dict[str, str]: A dictionary containing application name, version,
        and paths to documentation and health check endpoints.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
