"""
Analysis Endpoints - Repository Analysis API
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, HttpUrl, Field

from app.config import get_settings
from app.agents.orchestrator import AgentOrchestrator, AnalysisProgress

router = APIRouter()
settings = get_settings()

# In-memory store for analysis results (replace with Redis/DB in production)
analysis_store: dict[str, dict] = {}


class AnalyzeRequest(BaseModel):
    """Request to analyze a repository."""
    repo_url: HttpUrl = Field(..., description="Git repository URL (GitHub, GitLab, etc.)")
    branch: Optional[str] = Field(None, description="Branch to analyze (default: main/master)")
    audience: str = Field("engineer", description="Target audience profile")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "repo_url": "https://github.com/expressjs/express",
                    "branch": "master",
                    "audience": "engineer"
                }
            ]
        }
    }


class AnalyzeResponse(BaseModel):
    """Response after starting analysis."""
    analysis_id: str
    status: str
    message: str
    stream_url: str


class AnalysisResult(BaseModel):
    """Full analysis result."""
    analysis_id: str
    status: str
    repo_url: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # Results from agents
    architecture: Optional[dict] = None
    runtime: Optional[dict] = None
    documentation: Optional[dict] = None
    
    # Error info if failed
    error: Optional[str] = None


@router.post("/analyze", response_model=AnalyzeResponse)
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start repository analysis.
    
    Returns an analysis_id that can be used to:
    - Poll status via GET /api/analyze/{id}
    - Stream progress via WebSocket /api/analyze/{id}/stream
    """
    analysis_id = str(uuid.uuid4())
    
    # Validate audience
    if request.audience not in settings.audience_profiles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audience. Must be one of: {settings.audience_profiles}"
        )
    
    # Initialize analysis record
    analysis_store[analysis_id] = {
        "analysis_id": analysis_id,
        "status": "queued",
        "repo_url": str(request.repo_url),
        "branch": request.branch,
        "audience": request.audience,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "progress": [],
        "architecture": None,
        "runtime": None,
        "documentation": None,
        "error": None,
    }
    
    # Start analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id,
        str(request.repo_url),
        request.branch,
        request.audience,
    )
    
    return AnalyzeResponse(
        analysis_id=analysis_id,
        status="queued",
        message="Analysis started. Use stream_url for live progress.",
        stream_url=f"/api/analyze/{analysis_id}/stream",
    )


async def run_analysis(
    analysis_id: str,
    repo_url: str,
    branch: Optional[str],
    audience: str,
):
    """Background task to run full analysis pipeline."""
    try:
        analysis_store[analysis_id]["status"] = "running"
        
        orchestrator = AgentOrchestrator()
        
        async for progress in orchestrator.run_full_analysis(
            repo_url=repo_url,
            branch=branch,
            audience=audience,
        ):
            # Update progress
            analysis_store[analysis_id]["progress"].append(progress.model_dump())
            analysis_store[analysis_id]["status"] = progress.stage
            
            # Store intermediate results
            if progress.result:
                if progress.stage == "architect_complete":
                    analysis_store[analysis_id]["architecture"] = progress.result
                elif progress.stage == "runtime_complete":
                    analysis_store[analysis_id]["runtime"] = progress.result
                elif progress.stage == "documentation_complete":
                    analysis_store[analysis_id]["documentation"] = progress.result
                elif progress.stage == "completed":
                    # Ensure full result is stored
                    if "architecture" in progress.result:
                        analysis_store[analysis_id]["architecture"] = progress.result["architecture"]
                    if "runtime" in progress.result:
                        analysis_store[analysis_id]["runtime"] = progress.result["runtime"]
                    if "documentation" in progress.result:
                        analysis_store[analysis_id]["documentation"] = progress.result["documentation"]
        
        analysis_store[analysis_id]["status"] = "completed"
        analysis_store[analysis_id]["completed_at"] = datetime.utcnow()
        
    except Exception as e:
        analysis_store[analysis_id]["status"] = "failed"
        analysis_store[analysis_id]["error"] = str(e)
        analysis_store[analysis_id]["completed_at"] = datetime.utcnow()


@router.get("/analyze/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get analysis status and results."""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis_store[analysis_id]


@router.websocket("/analyze/{analysis_id}/stream")
async def stream_analysis(websocket: WebSocket, analysis_id: str):
    """WebSocket endpoint for live analysis progress."""
    await websocket.accept()
    
    if analysis_id not in analysis_store:
        await websocket.send_json({"error": "Analysis not found"})
        await websocket.close()
        return
    
    try:
        last_progress_count = 0
        ping_counter = 0
        
        while True:
            analysis = analysis_store[analysis_id]
            
            # Send any new progress updates
            current_progress = analysis["progress"]
            if len(current_progress) > last_progress_count:
                for progress in current_progress[last_progress_count:]:
                    await websocket.send_json(progress)
                last_progress_count = len(current_progress)
            
            # Check if analysis is complete
            if analysis["status"] in ["completed", "failed"]:
                await websocket.send_json({
                    "stage": analysis["status"],
                    "message": "Analysis complete" if analysis["status"] == "completed" else analysis["error"],
                    "progress_pct": 100 if analysis["status"] == "completed" else 0,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                break
            
            # Send keepalive ping every 10 polls (5 seconds)
            ping_counter += 1
            if ping_counter >= 10:
                await websocket.send_json({
                    "stage": analysis["status"],
                    "message": f"Processing... ({analysis['status']})",
                    "progress_pct": current_progress[-1]["progress_pct"] if current_progress else 5,
                    "timestamp": datetime.utcnow().isoformat(),
                    "keepalive": True,
                })
                ping_counter = 0
            
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()


@router.delete("/analyze/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete an analysis and its cached data."""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    del analysis_store[analysis_id]
    return {"message": "Analysis deleted"}
