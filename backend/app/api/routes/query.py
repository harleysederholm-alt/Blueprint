"""
Query API Routes

Endpoints for querying the Architectural Knowledge Graph.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.query_engine import KnowledgeGraphQueryEngine, QueryResult
from app.api.routes.analyze import analysis_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

# Query engine instance
_query_engines: dict[str, KnowledgeGraphQueryEngine] = {}


class QueryRequest(BaseModel):
    """Request to query the knowledge graph."""
    analysis_id: str
    question: str


class QueryResponse(BaseModel):
    """Response from a query."""
    query: str
    query_type: str
    answer: str
    nodes: list = []
    edges: list = []
    evidence: list = []
    confidence: float
    suggestions: list = []


@router.post("/ask", response_model=QueryResponse)
async def query_knowledge_graph(request: QueryRequest):
    """
    Query the Architectural Knowledge Graph with a natural language question.
    
    Examples:
    - "Find class UserService"
    - "What depends on Database?"
    - "Show design patterns"
    - "Analyze architectural layers"
    - "Find coupling hotspots"
    """
    # Check if analysis exists
    if request.analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_store[request.analysis_id]
    
    if result.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not ready: {result.get('status')}"
        )
    
    # Get or create query engine
    if request.analysis_id not in _query_engines:
        # Create engine with AKG from result
        from app.core.akg import ArchitecturalKnowledgeGraph
        
        analysis_data = result.get("result", {})
        akg_data = analysis_data.get("akg")
        
        if not akg_data:
            # Create minimal AKG from architecture data
            arch = analysis_data.get("architecture", {})
            akg = ArchitecturalKnowledgeGraph(
                system_name=analysis_data.get("repo_url", "System").split("/")[-1]
            )
            
            # Add bounded contexts
            for ctx in arch.get("bounded_contexts", []):
                from app.core.akg import BoundedContext
                akg.add_bounded_context(BoundedContext(
                    name=ctx.get("name", ""),
                    purpose=ctx.get("purpose", ""),
                    key_entities=ctx.get("key_entities", []),
                ))
            
            # Add layers
            for layer in arch.get("layers", []):
                from app.core.akg import ArchitecturalLayer
                akg.add_layer(ArchitecturalLayer(
                    name=layer.get("name", ""),
                    purpose=layer.get("purpose", ""),
                    components=layer.get("components", []),
                ))
        else:
            akg = akg_data
        
        engine = KnowledgeGraphQueryEngine(akg)
        _query_engines[request.analysis_id] = engine
    else:
        engine = _query_engines[request.analysis_id]
    
    # Execute query
    query_result = engine.query(request.question)
    
    return QueryResponse(
        query=query_result.query,
        query_type=query_result.query_type.value,
        answer=query_result.answer,
        nodes=query_result.nodes,
        edges=query_result.edges,
        evidence=query_result.evidence,
        confidence=query_result.confidence,
        suggestions=query_result.suggestions,
    )


@router.get("/suggestions/{analysis_id}")
async def get_query_suggestions(analysis_id: str):
    """
    Get query suggestions for an analysis.
    """
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if analysis_id in _query_engines:
        engine = _query_engines[analysis_id]
        suggestions = engine.get_suggestions()
    else:
        suggestions = [
            "Find class <name>",
            "What depends on <component>?",
            "Show design patterns",
            "Analyze architectural layers",
            "Find coupling hotspots",
        ]
    
    return {"suggestions": suggestions}


@router.get("/examples")
async def get_query_examples():
    """
    Get example queries.
    """
    return {
        "examples": [
            {
                "category": "Component Search",
                "queries": [
                    "Find class UserService",
                    "Show all controllers",
                    "Where is the authentication module?",
                ],
            },
            {
                "category": "Dependencies",
                "queries": [
                    "What depends on Database?",
                    "Show imports for UserService",
                    "List all dependencies",
                ],
            },
            {
                "category": "Patterns",
                "queries": [
                    "What design patterns are used?",
                    "Is there a repository pattern?",
                    "Find factory classes",
                ],
            },
            {
                "category": "Architecture",
                "queries": [
                    "Analyze architectural layers",
                    "Show bounded contexts",
                    "What's in the data layer?",
                ],
            },
            {
                "category": "Quality",
                "queries": [
                    "Find coupling hotspots",
                    "Most connected components",
                    "Show critical dependencies",
                ],
            },
        ]
    }
