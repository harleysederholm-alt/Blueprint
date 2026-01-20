"""
Export API Routes

Endpoints for exporting analysis results in various formats.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from io import BytesIO

from app.core.export_engine import ExportEngine, ExportOptions
from app.api.routes.analyze import _analysis_results  # Import the results store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])

export_engine = ExportEngine()


class ExportRequest(BaseModel):
    """Request for exporting analysis results."""
    analysis_id: str
    format: str = "markdown"  # markdown, html, json
    include_diagrams: bool = True
    include_evidence: bool = True
    title: Optional[str] = None


@router.post("/analysis")
async def export_analysis(request: ExportRequest):
    """
    Export analysis results in the specified format.
    
    Supported formats:
    - markdown: Markdown with Mermaid diagrams
    - html: Standalone HTML document
    - json: Raw JSON data
    """
    # Get analysis result
    if request.analysis_id not in _analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = _analysis_results[request.analysis_id]
    
    if result.get("status") != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Analysis not ready: {result.get('status')}"
        )
    
    analysis_data = result.get("result", {})
    
    options = ExportOptions(
        include_diagrams=request.include_diagrams,
        include_evidence=request.include_evidence,
        title=request.title,
    )
    
    # Generate export
    if request.format == "markdown":
        content = export_engine.export_markdown(analysis_data, options)
        media_type = "text/markdown"
        filename = f"analysis_{request.analysis_id}.md"
    elif request.format == "html":
        content = export_engine.export_html(analysis_data, options)
        media_type = "text/html"
        filename = f"analysis_{request.analysis_id}.html"
    elif request.format == "json":
        content = export_engine.export_json(analysis_data, options)
        media_type = "application/json"
        filename = f"analysis_{request.analysis_id}.json"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/analysis/{analysis_id}/markdown")
async def export_analysis_markdown(
    analysis_id: str,
    include_diagrams: bool = True,
    include_evidence: bool = True,
):
    """Quick endpoint to export as Markdown."""
    if analysis_id not in _analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = _analysis_results[analysis_id]
    
    if result.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Analysis not ready")
    
    analysis_data = result.get("result", {})
    
    options = ExportOptions(
        include_diagrams=include_diagrams,
        include_evidence=include_evidence,
    )
    
    content = export_engine.export_markdown(analysis_data, options)
    
    return Response(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="analysis_{analysis_id}.md"'
        }
    )


@router.get("/analysis/{analysis_id}/html")
async def export_analysis_html(analysis_id: str):
    """Quick endpoint to export as HTML."""
    if analysis_id not in _analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = _analysis_results[analysis_id]
    
    if result.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Analysis not ready")
    
    analysis_data = result.get("result", {})
    content = export_engine.export_html(analysis_data)
    
    return Response(
        content=content,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="analysis_{analysis_id}.html"'
        }
    )


@router.get("/analysis/{analysis_id}/json")
async def export_analysis_json(analysis_id: str):
    """Quick endpoint to export as JSON."""
    if analysis_id not in _analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = _analysis_results[analysis_id]
    
    if result.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Analysis not ready")
    
    analysis_data = result.get("result", {})
    content = export_engine.export_json(analysis_data)
    
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="analysis_{analysis_id}.json"'
        }
    )


# Diff export endpoints
@router.get("/diff/{diff_id}/markdown")
async def export_diff_markdown(diff_id: str):
    """Export diff results as Markdown."""
    from app.api.routes.diff import _diff_results
    
    if diff_id not in _diff_results:
        raise HTTPException(status_code=404, detail="Diff not found")
    
    result = _diff_results[diff_id]
    
    if result.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Diff not ready")
    
    diff_data = result.get("result", {})
    content = export_engine.export_diff_markdown(diff_data)
    
    return Response(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="diff_{diff_id}.md"'
        }
    )


@router.get("/formats")
async def list_export_formats():
    """List available export formats."""
    return {
        "formats": [
            {
                "id": "markdown",
                "name": "Markdown",
                "extension": ".md",
                "description": "Markdown with embedded Mermaid diagrams",
            },
            {
                "id": "html",
                "name": "HTML",
                "extension": ".html",
                "description": "Standalone HTML document with rendered diagrams",
            },
            {
                "id": "json",
                "name": "JSON",
                "extension": ".json",
                "description": "Raw structured data",
            },
        ]
    }
