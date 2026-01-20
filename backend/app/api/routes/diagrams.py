"""
Diagram Endpoints - Mermaid Diagram Generation API
"""

from typing import Literal
from fastapi import APIRouter, HTTPException

from app.api.routes.analyze import analysis_store

router = APIRouter()

DiagramType = Literal[
    "c4_context",
    "c4_container", 
    "c4_component",
    "sequence",
    "data_lineage",
    "dependency_graph",
]


@router.get("/diagrams/{analysis_id}/{diagram_type}")
async def get_diagram(
    analysis_id: str,
    diagram_type: DiagramType,
):
    """
    Get a specific Mermaid diagram from an analysis.
    
    Diagram types:
    - c4_context: System context diagram
    - c4_container: Container diagram
    - c4_component: Component diagram
    - sequence: Critical flow sequence diagrams
    - data_lineage: Data flow diagram
    - dependency_graph: Module dependency graph
    """
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_store[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not complete. Current status: {analysis['status']}"
        )
    
    architecture = analysis.get("architecture", {})
    runtime = analysis.get("runtime", {})
    
    diagram_map = {
        "c4_context": architecture.get("c4_context_diagram"),
        "c4_container": architecture.get("c4_container_diagram"),
        "c4_component": architecture.get("c4_component_diagram"),
        "sequence": runtime.get("critical_flows", []),
        "data_lineage": runtime.get("data_lineage_diagram"),
        "dependency_graph": architecture.get("dependency_graph"),
    }
    
    diagram = diagram_map.get(diagram_type)
    
    if not diagram:
        raise HTTPException(
            status_code=404,
            detail=f"Diagram '{diagram_type}' not available for this analysis"
        )
    
    # For sequence diagrams, return list of flow diagrams
    if diagram_type == "sequence":
        return {
            "type": diagram_type,
            "diagrams": [
                {
                    "name": flow.get("name"),
                    "description": flow.get("description"),
                    "mermaid": flow.get("sequence_diagram_mermaid"),
                }
                for flow in diagram
            ]
        }
    
    return {
        "type": diagram_type,
        "mermaid": diagram,
    }


@router.get("/diagrams/{analysis_id}")
async def list_diagrams(analysis_id: str):
    """List all available diagrams for an analysis."""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_store[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not complete. Current status: {analysis['status']}"
        )
    
    architecture = analysis.get("architecture", {})
    runtime = analysis.get("runtime", {})
    
    available = []
    
    if architecture.get("c4_context_diagram"):
        available.append({"type": "c4_context", "name": "C4 Context Diagram"})
    if architecture.get("c4_container_diagram"):
        available.append({"type": "c4_container", "name": "C4 Container Diagram"})
    if architecture.get("c4_component_diagram"):
        available.append({"type": "c4_component", "name": "C4 Component Diagram"})
    if runtime.get("critical_flows"):
        available.append({"type": "sequence", "name": "Sequence Diagrams", "count": len(runtime["critical_flows"])})
    if runtime.get("data_lineage_diagram"):
        available.append({"type": "data_lineage", "name": "Data Lineage Diagram"})
    if architecture.get("dependency_graph"):
        available.append({"type": "dependency_graph", "name": "Dependency Graph"})
    
    return {
        "analysis_id": analysis_id,
        "available_diagrams": available,
    }
