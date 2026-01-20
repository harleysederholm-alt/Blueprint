"""
Blueprint Diff API Routes

Endpoints for comparing architecture between commits/branches.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.config import get_settings
from app.core.repository import RepositoryAnalyzer
from app.core.git_navigator import GitHistoryNavigator, CommitInfo, BranchInfo
from app.core.diff_engine import BlueprintDiffEngine, BlueprintDiff

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/diff", tags=["diff"])

# In-memory store for diff results
_diff_results: dict[str, dict] = {}


class DiffRequest(BaseModel):
    """Request to create a diff between two versions."""
    repo_url: str
    base_ref: str  # commit hash or branch name
    target_ref: str  # commit hash or branch name


class DiffResponse(BaseModel):
    """Response with diff ID."""
    diff_id: str
    status: str
    message: str


class CommitListRequest(BaseModel):
    """Request to list commits."""
    repo_url: str
    branch: Optional[str] = None
    max_count: int = 30


@router.post("/create", response_model=DiffResponse)
async def create_diff(
    request: DiffRequest,
    background_tasks: BackgroundTasks,
):
    """
    Create a diff between two versions of a repository.
    
    This initiates an async comparison process.
    """
    import uuid
    
    diff_id = str(uuid.uuid4())[:8]
    
    # Initialize result
    _diff_results[diff_id] = {
        "status": "processing",
        "repo_url": request.repo_url,
        "base_ref": request.base_ref,
        "target_ref": request.target_ref,
        "result": None,
        "error": None,
    }
    
    # Run diff in background
    background_tasks.add_task(
        _run_diff,
        diff_id,
        request.repo_url,
        request.base_ref,
        request.target_ref,
    )
    
    return DiffResponse(
        diff_id=diff_id,
        status="processing",
        message=f"Diff started: {request.base_ref} → {request.target_ref}",
    )


async def _run_diff(
    diff_id: str,
    repo_url: str,
    base_ref: str,
    target_ref: str,
):
    """Background task to run the diff."""
    repo_analyzer = RepositoryAnalyzer()
    navigator = None
    
    try:
        # Clone repository
        repo_path = await repo_analyzer.clone(repo_url)
        
        # Create navigator
        navigator = GitHistoryNavigator(Path(repo_path))
        navigator.open()
        
        # Build AKG for both versions
        logger.info(f"Building AKG for base: {base_ref}")
        base_akg = await navigator.build_akg_for_ref(base_ref)
        
        logger.info(f"Building AKG for target: {target_ref}")
        target_akg = await navigator.build_akg_for_ref(target_ref)
        
        # Run diff
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(base_akg, target_akg, base_ref, target_ref)
        
        # Get changed files for context
        changed_files = navigator.get_changed_files(base_ref, target_ref)
        
        # Store result
        _diff_results[diff_id] = {
            "status": "completed",
            "repo_url": repo_url,
            "base_ref": base_ref,
            "target_ref": target_ref,
            "result": diff.to_dict(),
            "changed_files": changed_files,
            "mermaid_diff": diff.to_mermaid_diff(),
            "error": None,
        }
        
        logger.info(f"Diff {diff_id} completed: {diff.total_changes} changes")
        
    except Exception as e:
        logger.exception(f"Diff {diff_id} failed: {e}")
        _diff_results[diff_id] = {
            "status": "failed",
            "repo_url": repo_url,
            "base_ref": base_ref,
            "target_ref": target_ref,
            "result": None,
            "error": str(e),
        }
    
    finally:
        if navigator:
            navigator.close()
        repo_analyzer.cleanup()


@router.get("/{diff_id}")
async def get_diff(diff_id: str):
    """
    Get the result of a diff operation.
    """
    if diff_id not in _diff_results:
        raise HTTPException(status_code=404, detail="Diff not found")
    
    return _diff_results[diff_id]


@router.get("/{diff_id}/diagram")
async def get_diff_diagram(diff_id: str):
    """
    Get the Mermaid diff diagram.
    """
    if diff_id not in _diff_results:
        raise HTTPException(status_code=404, detail="Diff not found")
    
    result = _diff_results[diff_id]
    
    if result["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Diff not ready: {result['status']}"
        )
    
    return {
        "diff_id": diff_id,
        "mermaid": result.get("mermaid_diff", ""),
    }


@router.post("/commits")
async def list_commits(request: CommitListRequest):
    """
    List commits for a repository.
    """
    repo_analyzer = RepositoryAnalyzer()
    navigator = None
    
    try:
        repo_path = await repo_analyzer.clone(request.repo_url)
        navigator = GitHistoryNavigator(Path(repo_path))
        navigator.open()
        
        commits = navigator.list_commits(
            max_count=request.max_count,
            branch=request.branch,
        )
        
        return {
            "repo_url": request.repo_url,
            "branch": request.branch,
            "commits": [c.to_dict() for c in commits],
        }
        
    finally:
        if navigator:
            navigator.close()
        repo_analyzer.cleanup()


@router.post("/branches")
async def list_branches(repo_url: str):
    """
    List branches for a repository.
    """
    repo_analyzer = RepositoryAnalyzer()
    navigator = None
    
    try:
        repo_path = await repo_analyzer.clone(repo_url)
        navigator = GitHistoryNavigator(Path(repo_path))
        navigator.open()
        
        branches = navigator.list_branches()
        
        return {
            "repo_url": repo_url,
            "branches": [b.to_dict() for b in branches],
        }
        
    finally:
        if navigator:
            navigator.close()
        repo_analyzer.cleanup()


@router.post("/quick")
async def quick_diff(request: DiffRequest):
    """
    Perform a quick diff and return results immediately.
    
    For smaller repositories, this returns the diff synchronously.
    """
    repo_analyzer = RepositoryAnalyzer()
    navigator = None
    
    try:
        repo_path = await repo_analyzer.clone(request.repo_url)
        navigator = GitHistoryNavigator(Path(repo_path))
        navigator.open()
        
        # Build AKGs
        base_akg = await navigator.build_akg_for_ref(request.base_ref)
        target_akg = await navigator.build_akg_for_ref(request.target_ref)
        
        # Run diff
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(
            base_akg, 
            target_akg, 
            request.base_ref, 
            request.target_ref
        )
        
        return {
            "status": "completed",
            "result": diff.to_dict(),
            "mermaid_diff": diff.to_mermaid_diff(),
        }
        
    except Exception as e:
        logger.exception(f"Quick diff failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if navigator:
            navigator.close()
        repo_analyzer.cleanup()


@router.delete("/{diff_id}")
async def delete_diff(diff_id: str):
    """
    Delete a diff result.
    """
    if diff_id not in _diff_results:
        raise HTTPException(status_code=404, detail="Diff not found")
    
    del _diff_results[diff_id]
    
    return {"message": "Diff deleted"}
