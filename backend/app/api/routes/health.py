"""
Health Check Endpoints
"""

import httpx
from fastapi import APIRouter, HTTPException

from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@router.get("/health/ollama")
async def ollama_health_check():
    """Check Ollama connectivity and model availability."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check if Ollama is running
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            
            # Check if configured model is available
            model_available = any(
                settings.ollama_model in m for m in models
            )
            
            return {
                "status": "healthy" if model_available else "degraded",
                "ollama_url": settings.ollama_base_url,
                "configured_model": settings.ollama_model,
                "model_available": model_available,
                "available_models": models[:10],  # Limit to 10
            }
            
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": "Cannot connect to Ollama",
                "hint": f"Ensure Ollama is running at {settings.ollama_base_url}",
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy", 
                "error": str(e),
            }
        )
