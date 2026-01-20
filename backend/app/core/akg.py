"""
Architectural Knowledge Graph (AKG) - Core Data Structure

Evidence-anchored knowledge representation for architecture analysis.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional
from datetime import datetime
import json
import hashlib


@dataclass
class Evidence:
    """
    Evidence anchoring for a claim.
    Every architectural assertion must be backed by specific file/line evidence.
    """
    claim_id: str
    file_path: str
    line_start: int
    line_end: int
    quote: str  # Relevant code snippet
    confidence: Literal["high", "medium", "low"] = "high"
    
    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "file_path": self.file_path,
            "line_range": f"{self.line_start}-{self.line_end}",
            "quote": self.quote[:200] + "..." if len(self.quote) > 200 else self.quote,
            "confidence": self.confidence,
        }


@dataclass
class AKGNode:
    """
    A node in the Architectural Knowledge Graph.
    Represents a module, class, function, service, or external system.
    """
    id: str
    type: Literal["module", "class", "function", "service", "database", "external", "config"]
    name: str
    file_path: Optional[str] = None
    line_range: Optional[tuple[int, int]] = None
    description: Optional[str] = None
    evidence: list[Evidence] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "file_path": self.file_path,
            "line_range": f"{self.line_range[0]}-{self.line_range[1]}" if self.line_range else None,
            "description": self.description,
            "evidence": [e.to_dict() for e in self.evidence],
            "metadata": self.metadata,
        }


@dataclass
class AKGEdge:
    """
    An edge in the Architectural Knowledge Graph.
    Represents relationships between nodes.
    """
    source_id: str
    target_id: str
    relation: Literal["imports", "calls", "inherits", "depends_on", "contains", "uses", "produces", "consumes"]
    evidence: Optional[Evidence] = None
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "relation": self.relation,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "weight": self.weight,
        }


@dataclass
class BoundedContext:
    """
    A Domain-Driven Design bounded context.
    Groups related modules/services.
    """
    name: str
    purpose: str = ""
    description: str = ""
    primary_files: list[str] = field(default_factory=list)
    key_entities: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    node_ids: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "description": self.description,
            "primary_files": self.primary_files,
            "key_entities": self.key_entities,
            "interfaces": self.interfaces,
            "dependencies": self.dependencies,
            "responsibilities": self.responsibilities,
            "evidence": [e.to_dict() for e in self.evidence],
        }


@dataclass
class ArchitecturalLayer:
    """A layer in the architecture (presentation, domain, infrastructure, etc.)."""
    name: str
    purpose: str = ""
    description: str = ""
    modules: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "description": self.description,
            "modules": self.modules,
            "components": self.components,
        }


@dataclass
class DesignPattern:
    """An identified design pattern with evidence."""
    pattern: str
    description: str
    evidence_files: list[str]
    confidence: Literal["high", "medium", "low"]
    evidence: list[Evidence] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "pattern": self.pattern,
            "description": self.description,
            "evidence_files": self.evidence_files,
            "confidence": self.confidence,
            "evidence": [e.to_dict() for e in self.evidence],
        }


class ArchitecturalKnowledgeGraph:
    """
    The core AKG data structure.
    
    Maintains nodes, edges, and architectural metadata with full evidence anchoring.
    """
    
    def __init__(
        self, 
        system_name: str = "",
        repo_url: str = "", 
        commit_hash: Optional[str] = None
    ):
        # Determine system name with proper fallback logic
        if system_name:
            self.system_name = system_name
        elif repo_url:
            self.system_name = repo_url.split("/")[-1].replace(".git", "")
        else:
            self.system_name = "System"
        self.repo_url = repo_url
        self.commit_hash = commit_hash
        self.created_at = datetime.utcnow()
        
        # Core graph structure
        self.nodes: dict[str, AKGNode] = {}
        self.edges: list[AKGEdge] = []
        
        # Architectural metadata
        self.architecture_style: Optional[str] = None
        self.bounded_contexts: list[BoundedContext] = []
        self.layers: list[ArchitecturalLayer] = []
        self.design_patterns: list[DesignPattern] = []
        
        # Assessment scores
        self.coupling_score: Optional[float] = None  # 1-10
        self.cohesion_score: Optional[float] = None  # 1-10
        self.assessment_explanation: Optional[str] = None
        
        # Evidence map
        self._evidence_map: dict[str, Evidence] = {}
        self._claim_counter = 0
    
    def generate_claim_id(self) -> str:
        """Generate a unique claim ID for evidence anchoring."""
        self._claim_counter += 1
        return f"claim_{self._claim_counter:04d}"
    
    def add_node(self, node: AKGNode) -> str:
        """Add a node to the graph. Returns the node ID."""
        if not node.id:
            node.id = self._generate_node_id(node.name, node.type)
        self.nodes[node.id] = node
        return node.id
    
    def add_edge(self, edge: AKGEdge):
        """Add an edge to the graph."""
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node {edge.source_id} not found")
        if edge.target_id not in self.nodes:
            # Create placeholder for external dependencies
            self.add_node(AKGNode(
                id=edge.target_id,
                type="external",
                name=edge.target_id,
            ))
        self.edges.append(edge)
    
    def add_bounded_context(self, context: BoundedContext):
        """Add a bounded context to the AKG."""
        self.bounded_contexts.append(context)
    
    def add_layer(self, layer: ArchitecturalLayer):
        """Add an architectural layer to the AKG."""
        self.layers.append(layer)
    
    def add_evidence(self, evidence: Evidence):
        """Register evidence in the global map."""
        self._evidence_map[evidence.claim_id] = evidence
    
    def get_evidence(self, claim_id: str) -> Optional[Evidence]:
        """Retrieve evidence by claim ID."""
        return self._evidence_map.get(claim_id)
    
    def _generate_node_id(self, name: str, node_type: str) -> str:
        """Generate a unique node ID."""
        content = f"{node_type}:{name}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def get_nodes_by_type(self, node_type: str) -> list[AKGNode]:
        """Get all nodes of a specific type."""
        return [n for n in self.nodes.values() if n.type == node_type]
    
    def get_outgoing_edges(self, node_id: str) -> list[AKGEdge]:
        """Get all edges originating from a node."""
        return [e for e in self.edges if e.source_id == node_id]
    
    def get_incoming_edges(self, node_id: str) -> list[AKGEdge]:
        """Get all edges targeting a node."""
        return [e for e in self.edges if e.target_id == node_id]
    
    def to_mermaid_flowchart(self, max_nodes: int = 30) -> str:
        """
        Generate a Mermaid flowchart representation.
        
        Returns:
            Mermaid.js flowchart code
        """
        lines = ["flowchart TD"]
        
        # Add nodes (limited for readability)
        shown_nodes = list(self.nodes.values())[:max_nodes]
        node_ids = {n.id for n in shown_nodes}
        
        type_shapes = {
            "module": ("[[", "]]"),
            "class": ("[", "]"),
            "function": ("([", "])"),
            "service": ("{{", "}}"),
            "database": ("[(", ")]"),
            "external": (">", "]"),
            "config": ("[/", "/]"),
        }
        
        for node in shown_nodes:
            start, end = type_shapes.get(node.type, ("[", "]"))
            safe_name = node.name.replace('"', "'")
            lines.append(f'    {node.id}{start}"{safe_name}"{end}')
        
        # Add edges
        relation_arrows = {
            "imports": "-->",
            "calls": "-.->",
            "inherits": "==>",
            "depends_on": "-->",
            "contains": "--o",
            "uses": "-.->",
            "produces": "-->",
            "consumes": "<--",
        }
        
        for edge in self.edges:
            if edge.source_id in node_ids and edge.target_id in node_ids:
                arrow = relation_arrows.get(edge.relation, "-->")
                lines.append(f"    {edge.source_id} {arrow}|{edge.relation}| {edge.target_id}")
        
        return "\n".join(lines)
    
    def to_c4_context(self) -> str:
        """Generate C4 Context diagram in Mermaid."""
        lines = ["C4Context"]
        lines.append('    title System Context Diagram')
        
        # Main system
        lines.append(f'    System(main, "{self.repo_url.split("/")[-1]}", "The analyzed system")')
        
        # External systems
        externals = self.get_nodes_by_type("external")
        for ext in externals[:5]:  # Limit
            safe_name = ext.name.replace('"', "'")
            lines.append(f'    System_Ext({ext.id}, "{safe_name}", "External dependency")')
            lines.append(f'    Rel(main, {ext.id}, "uses")')
        
        return "\n".join(lines)
    
    def to_c4_container(self) -> str:
        """Generate C4 Container diagram in Mermaid."""
        lines = ["C4Container"]
        lines.append('    title Container Diagram')
        
        # Bounded contexts as containers
        for ctx in self.bounded_contexts[:6]:
            safe_name = ctx.name.replace('"', "'").replace(" ", "_")
            desc = ctx.description[:50] if ctx.description else "Container"
            lines.append(f'    Container({safe_name}, "{ctx.name}", "{desc}")')
        
        # Add relationships between contexts
        for ctx in self.bounded_contexts:
            ctx_name = ctx.name.replace('"', "'").replace(" ", "_")
            for node_id in ctx.node_ids[:3]:
                if node_id in self.nodes:
                    node = self.nodes[node_id]
                    for edge in self.get_outgoing_edges(node_id):
                        target = self.nodes.get(edge.target_id)
                        if target:
                            for other_ctx in self.bounded_contexts:
                                if edge.target_id in other_ctx.node_ids and other_ctx.name != ctx.name:
                                    other_name = other_ctx.name.replace('"', "'").replace(" ", "_")
                                    lines.append(f'    Rel({ctx_name}, {other_name}, "{edge.relation}")')
                                    break
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Serialize the entire AKG to a dictionary."""
        return {
            "repo_url": self.repo_url,
            "commit_hash": self.commit_hash,
            "created_at": self.created_at.isoformat(),
            "architecture_style": self.architecture_style,
            "bounded_contexts": [bc.to_dict() for bc in self.bounded_contexts],
            "layers": [l.to_dict() for l in self.layers],
            "design_patterns": [dp.to_dict() for dp in self.design_patterns],
            "coupling_cohesion_assessment": {
                "coupling_score": self.coupling_score,
                "cohesion_score": self.cohesion_score,
                "explanation": self.assessment_explanation,
            },
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "evidence_map": {k: v.to_dict() for k, v in self._evidence_map.items()},
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "total_evidence": len(self._evidence_map),
            },
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
