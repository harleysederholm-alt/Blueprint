"""
Knowledge Graph Query Engine - Natural language queries over AKG

Enables:
- Natural language questions about architecture
- Pattern-based graph queries
- AI-powered answer generation with evidence
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from app.core.akg import (
    ArchitecturalKnowledgeGraph,
    AKGNode,
    AKGEdge,
    Evidence,
)

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Types of queries."""
    FIND_COMPONENT = "find_component"
    LIST_DEPENDENCIES = "list_dependencies"
    FIND_PATTERN = "find_pattern"
    ANALYZE_LAYER = "analyze_layer"
    FIND_HOTSPOTS = "find_hotspots"
    GENERAL = "general"


@dataclass
class QueryResult:
    """Result of a knowledge graph query."""
    query: str
    query_type: QueryType
    answer: str
    nodes: List[Dict] = field(default_factory=list)
    edges: List[Dict] = field(default_factory=list)
    evidence: List[Dict] = field(default_factory=list)
    confidence: float = 0.8
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "query_type": self.query_type.value,
            "answer": self.answer,
            "nodes": self.nodes,
            "edges": self.edges,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "suggestions": self.suggestions,
        }


class KnowledgeGraphQueryEngine:
    """
    Query engine for the Architectural Knowledge Graph.
    
    Supports:
    - Natural language questions
    - Pattern matching queries
    - AI-enhanced answer generation
    """
    
    # Query patterns for classification
    QUERY_PATTERNS = {
        QueryType.LIST_DEPENDENCIES: [
            r"\b(what|which|list|show)\b.*\b(depend\w*|import\w*|us(e|es|ing)|call\w*|relationship\w*|link\w*|connect\w*)\b",
            r"\b(dependenc\w+|import\w*)\b.*\b(of|for)\b",
        ],
        QueryType.FIND_PATTERN: [
            r"\b(find|detect|show|which|what|list)\b.*\b(pattern\w*|architecture\w*|style\w*)\b",
            r"\b(is there|does it use)\b.*\b(pattern\w*|singleton|factory|repository|observer|strategy)\b",
        ],
        QueryType.ANALYZE_LAYER: [
            r"\b(what|which|show|analyze|describe)\b.*\b(layer\w*|tier\w*)\b",
            r"\b(presentation|business|data|infrastructure|service|domain)\b.*\b(layer\w*|component\w*)\b",
        ],
        QueryType.FIND_HOTSPOTS: [
            r"\b(find|show|what)\b.*\b(coupling|cohesion|hotspot\w*|problem\w*|issue\w*|complexity)\b",
            r"\b(most connected|highly coupled|complex|critical|hard to maintain)\b",
        ],
        QueryType.FIND_COMPONENT: [
            r"\b(find|show|where|what|which|describe)\b.*\b(class\w*|\w*service\w*|\w*module\w*|\w*component\w*|\w*function\w*|\w*controller\w*|\w*route\w*|\w*endpoint\w*)\b",
            r"\b(tell me about|explain|describe|search for)\b.*\b(class\w*|\w*service\w*|\w*module\w*|\w*component\w*|\w*function\w*)\b",
        ],
    }
    
    def __init__(self, akg: Optional[ArchitecturalKnowledgeGraph] = None):
        self.akg = akg
    
    def set_akg(self, akg: ArchitecturalKnowledgeGraph):
        """Set the AKG to query."""
        self.akg = akg
    
    def classify_query(self, query: str) -> QueryType:
        """Classify query into a type."""
        query_lower = query.lower()
        
        for query_type, patterns in self.QUERY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return query_type
        
        return QueryType.GENERAL
    
    def query(self, question: str) -> QueryResult:
        """
        Process a natural language query.
        
        Args:
            question: Natural language question
            
        Returns:
            QueryResult with answer and supporting data
        """
        if not self.akg:
            return QueryResult(
                query=question,
                query_type=QueryType.GENERAL,
                answer="No architecture knowledge graph loaded. Please run an analysis first.",
                confidence=0.0,
            )
        
        query_type = self.classify_query(question)
        
        # Route to appropriate handler
        handlers = {
            QueryType.FIND_COMPONENT: self._handle_find_component,
            QueryType.LIST_DEPENDENCIES: self._handle_list_dependencies,
            QueryType.FIND_PATTERN: self._handle_find_pattern,
            QueryType.ANALYZE_LAYER: self._handle_analyze_layer,
            QueryType.FIND_HOTSPOTS: self._handle_find_hotspots,
            QueryType.GENERAL: self._handle_general,
        }
        
        handler = handlers.get(query_type, self._handle_general)
        return handler(question)
    
    def _handle_find_component(self, question: str) -> QueryResult:
        """Handle component search queries."""
        # Extract component name from question
        words = question.lower().split()
        search_terms = []
        
        # Look for quoted terms or capitalized words
        quoted = re.findall(r'"([^"]+)"', question)
        if quoted:
            search_terms.extend(quoted)
        else:
            # Use significant words
            skip_words = {"find", "show", "where", "what", "which", "is", "the", "a", "an", 
                         "class", "service", "module", "component", "function", "tell", "me", "about"}
            search_terms = [w for w in words if w not in skip_words and len(w) > 2]
        
        # Search nodes
        matching_nodes = []
        for node_id, node in self.akg.nodes.items():
            name_lower = node.name.lower()
            for term in search_terms:
                if term.lower() in name_lower:
                    matching_nodes.append(node)
                    break
        
        if matching_nodes:
            nodes_data = [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.type,
                    "file": n.file_path,
                    "lines": f"{n.line_range[0]}-{n.line_range[1]}" if n.line_range else None,
                }
                for n in matching_nodes[:10]
            ]
            
            answer = f"Found {len(matching_nodes)} component(s):\n\n"
            for n in matching_nodes[:5]:
                answer += f"• **{n.name}** ({n.type})"
                if n.file_path:
                    answer += f" in `{n.file_path}`"
                answer += "\n"
            
            if len(matching_nodes) > 5:
                answer += f"\n...and {len(matching_nodes) - 5} more."
        else:
            nodes_data = []
            answer = f"No components found matching your search. The system contains {len(self.akg.nodes)} components."
        
        return QueryResult(
            query=question,
            query_type=QueryType.FIND_COMPONENT,
            answer=answer,
            nodes=nodes_data,
            confidence=0.9 if matching_nodes else 0.5,
            suggestions=["Try searching for a specific class or service name"],
        )
    
    def _handle_list_dependencies(self, question: str) -> QueryResult:
        """Handle dependency listing queries."""
        # Try to extract component name
        words = question.split()
        target_name = None
        
        # Look for component name
        for word in words:
            if word[0].isupper() and len(word) > 2:
                target_name = word
                break
        
        if target_name:
            # Find incoming and outgoing dependencies
            incoming = []
            outgoing = []
            
            for edge in self.akg.edges:
                if target_name.lower() in edge.source_id.lower():
                    outgoing.append(edge)
                if target_name.lower() in edge.target_id.lower():
                    incoming.append(edge)
            
            edges_data = [
                {"source": e.source_id, "target": e.target_id, "relation": e.relation}
                for e in outgoing + incoming
            ]
            
            answer = f"Dependencies for components matching '{target_name}':\n\n"
            
            if outgoing:
                answer += f"**Outgoing** ({len(outgoing)}):\n"
                for e in outgoing[:5]:
                    answer += f"  → {e.target_id.split(':')[-1]}\n"
            
            if incoming:
                answer += f"\n**Incoming** ({len(incoming)}):\n"
                for e in incoming[:5]:
                    answer += f"  ← {e.source_id.split(':')[-1]}\n"
            
            if not outgoing and not incoming:
                answer = f"No dependencies found for '{target_name}'."
        else:
            # General dependency stats
            edges_data = []
            dep_counts = {}
            for edge in self.akg.edges:
                target = edge.target_id.split(":")[-1]
                dep_counts[target] = dep_counts.get(target, 0) + 1
            
            sorted_deps = sorted(dep_counts.items(), key=lambda x: -x[1])[:10]
            
            answer = f"**Most depended-upon components**:\n\n"
            for name, count in sorted_deps:
                answer += f"• {name}: {count} dependents\n"
        
        return QueryResult(
            query=question,
            query_type=QueryType.LIST_DEPENDENCIES,
            answer=answer,
            edges=[{"source": e.source_id, "target": e.target_id, "relation": e.relation} 
                   for e in self.akg.edges[:20]],
            confidence=0.85,
        )
    
    def _handle_find_pattern(self, question: str) -> QueryResult:
        """Handle design pattern queries."""
        patterns = self.akg.design_patterns if hasattr(self.akg, 'design_patterns') else []
        
        if patterns:
            answer = f"**Design Patterns Detected** ({len(patterns)}):\n\n"
            for p in patterns:
                if isinstance(p, dict):
                    answer += f"• **{p.get('pattern', 'Unknown')}**: {p.get('description', '')}\n"
                else:
                    answer += f"• {p.pattern}: {p.description}\n"
        else:
            answer = "No design patterns have been explicitly detected in this codebase."
            
            # Try to infer from structure
            inferred = []
            for node in self.akg.nodes.values():
                name_lower = node.name.lower()
                if "factory" in name_lower:
                    inferred.append(("Factory Pattern", node.name))
                elif "repository" in name_lower:
                    inferred.append(("Repository Pattern", node.name))
                elif "service" in name_lower:
                    inferred.append(("Service Pattern", node.name))
                elif "handler" in name_lower:
                    inferred.append(("Handler Pattern", node.name))
            
            if inferred:
                answer += "\n\n**Possible patterns (inferred from naming)**:\n"
                for pattern, component in inferred[:5]:
                    answer += f"• {pattern} → `{component}`\n"
        
        return QueryResult(
            query=question,
            query_type=QueryType.FIND_PATTERN,
            answer=answer,
            confidence=0.7,
        )
    
    def _handle_analyze_layer(self, question: str) -> QueryResult:
        """Handle layer analysis queries."""
        layers = self.akg.layers if hasattr(self.akg, 'layers') else []
        
        if layers:
            answer = f"**Architectural Layers** ({len(layers)}):\n\n"
            for layer in layers:
                answer += f"### {layer.name}\n"
                if hasattr(layer, 'purpose') and layer.purpose:
                    answer += f"{layer.purpose}\n"
                components = layer.components if hasattr(layer, 'components') else []
                if components:
                    answer += f"Components: {len(components)}\n"
                    for c in components[:3]:
                        answer += f"  • `{c}`\n"
                    if len(components) > 3:
                        answer += f"  • ...and {len(components) - 3} more\n"
                answer += "\n"
        else:
            # Infer layers from file paths
            layers_inferred = {"presentation": [], "business": [], "data": [], "other": []}
            
            for node in self.akg.nodes.values():
                path = (node.file_path or "").lower()
                if any(x in path for x in ["api", "route", "controller", "view", "component"]):
                    layers_inferred["presentation"].append(node.name)
                elif any(x in path for x in ["service", "domain", "core", "usecase"]):
                    layers_inferred["business"].append(node.name)
                elif any(x in path for x in ["model", "repository", "db", "database"]):
                    layers_inferred["data"].append(node.name)
                else:
                    layers_inferred["other"].append(node.name)
            
            answer = "**Inferred Architectural Layers**:\n\n"
            for layer, components in layers_inferred.items():
                if components:
                    answer += f"• **{layer.title()}**: {len(components)} components\n"
        
        return QueryResult(
            query=question,
            query_type=QueryType.ANALYZE_LAYER,
            answer=answer,
            confidence=0.75,
        )
    
    def _handle_find_hotspots(self, question: str) -> QueryResult:
        """Handle hotspot/complexity queries."""
        # Calculate connectivity for each node
        connectivity = {}
        for edge in self.akg.edges:
            connectivity[edge.source_id] = connectivity.get(edge.source_id, 0) + 1
            connectivity[edge.target_id] = connectivity.get(edge.target_id, 0) + 1
        
        sorted_nodes = sorted(connectivity.items(), key=lambda x: -x[1])[:10]
        
        answer = "**Architectural Hotspots** (most connected components):\n\n"
        
        nodes_data = []
        for node_id, conn_count in sorted_nodes:
            node = self.akg.nodes.get(node_id)
            name = node.name if node else node_id.split(":")[-1]
            answer += f"• **{name}**: {conn_count} connections\n"
            nodes_data.append({
                "id": node_id,
                "name": name,
                "connections": conn_count,
            })
        
        # Add coupling assessment
        if hasattr(self.akg, 'coupling_score') and self.akg.coupling_score:
            answer += f"\n**Coupling Score**: {self.akg.coupling_score}/10\n"
        if hasattr(self.akg, 'cohesion_score') and self.akg.cohesion_score:
            answer += f"**Cohesion Score**: {self.akg.cohesion_score}/10\n"
        
        return QueryResult(
            query=question,
            query_type=QueryType.FIND_HOTSPOTS,
            answer=answer,
            nodes=nodes_data,
            confidence=0.85,
        )
    
    def _handle_general(self, question: str) -> QueryResult:
        """Handle general queries with system overview."""
        # Provide system overview
        node_count = len(self.akg.nodes)
        edge_count = len(self.akg.edges)
        layer_count = len(self.akg.layers) if hasattr(self.akg, 'layers') else 0
        context_count = len(self.akg.bounded_contexts) if hasattr(self.akg, 'bounded_contexts') else 0
        
        # Count by type
        type_counts = {}
        for node in self.akg.nodes.values():
            type_counts[node.type] = type_counts.get(node.type, 0) + 1
        
        answer = f"**{self.akg.system_name}** Architecture Overview:\n\n"
        answer += f"• **Components**: {node_count}\n"
        answer += f"• **Relationships**: {edge_count}\n"
        
        if type_counts:
            answer += "\n**By Type**:\n"
            for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                answer += f"  • {t}: {count}\n"
        
        if layer_count:
            answer += f"\n• **Layers**: {layer_count}\n"
        if context_count:
            answer += f"• **Bounded Contexts**: {context_count}\n"
        
        answer += "\n**Try asking**:\n"
        answer += "• 'Find class UserService'\n"
        answer += "• 'What depends on Database?'\n"
        answer += "• 'Show design patterns'\n"
        answer += "• 'Analyze layers'\n"
        
        return QueryResult(
            query=question,
            query_type=QueryType.GENERAL,
            answer=answer,
            confidence=0.6,
            suggestions=[
                "Find class <name>",
                "What depends on <component>?",
                "Show design patterns",
                "Analyze architectural layers",
                "Find coupling hotspots",
            ],
        )
    
    def get_suggestions(self) -> List[str]:
        """Get query suggestions based on current AKG."""
        suggestions = []
        
        if not self.akg:
            return ["Load an analysis first"]
        
        # Add suggestions based on what's in the graph
        if self.akg.nodes:
            sample_node = list(self.akg.nodes.values())[0]
            suggestions.append(f"Find class {sample_node.name}")
        
        suggestions.extend([
            "Show all dependencies",
            "What design patterns are used?",
            "Analyze architectural layers",
            "Find coupling hotspots",
            "List bounded contexts",
        ])
        
        return suggestions[:5]
