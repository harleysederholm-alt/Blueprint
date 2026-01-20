"""
Blueprint Diff Engine - Compares architecture between commits/branches

Enables:
- Commit-to-commit comparison
- Branch-to-branch comparison  
- Architecture drift detection
- Change impact analysis
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import json

from app.core.akg import (
    ArchitecturalKnowledgeGraph,
    AKGNode,
    AKGEdge,
    BoundedContext,
    ArchitecturalLayer,
    Evidence,
)
from app.core.akg_builder import AKGBuilder
from app.core.tree_sitter_parser import get_parser

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of architectural changes."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"
    UNCHANGED = "unchanged"


@dataclass
class NodeChange:
    """Represents a change to a node between versions."""
    change_type: ChangeType
    node_id: str
    node_name: str
    node_type: str
    file_path: Optional[str] = None
    
    # For modifications
    old_line_range: Optional[Tuple[int, int]] = None
    new_line_range: Optional[Tuple[int, int]] = None
    
    # Details
    details: str = ""
    impact: str = "low"  # low, medium, high
    
    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type.value,
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": self.node_type,
            "file_path": self.file_path,
            "old_line_range": f"{self.old_line_range[0]}-{self.old_line_range[1]}" if self.old_line_range else None,
            "new_line_range": f"{self.new_line_range[0]}-{self.new_line_range[1]}" if self.new_line_range else None,
            "details": self.details,
            "impact": self.impact,
        }


@dataclass
class EdgeChange:
    """Represents a change to a relationship between versions."""
    change_type: ChangeType
    source_id: str
    target_id: str
    relation: str
    details: str = ""
    
    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type.value,
            "source": self.source_id,
            "target": self.target_id,
            "relation": self.relation,
            "details": self.details,
        }


@dataclass
class LayerChange:
    """Represents changes to architectural layers."""
    change_type: ChangeType
    layer_name: str
    added_components: List[str] = field(default_factory=list)
    removed_components: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type.value,
            "layer_name": self.layer_name,
            "added_components": self.added_components,
            "removed_components": self.removed_components,
        }


@dataclass
class ContextChange:
    """Represents changes to bounded contexts."""
    change_type: ChangeType
    context_name: str
    added_entities: List[str] = field(default_factory=list)
    removed_entities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type.value,
            "context_name": self.context_name,
            "added_entities": self.added_entities,
            "removed_entities": self.removed_entities,
        }


@dataclass
class BlueprintDiff:
    """Complete diff between two architecture snapshots."""
    base_ref: str  # commit hash or branch name
    target_ref: str
    base_timestamp: Optional[datetime] = None
    target_timestamp: Optional[datetime] = None
    
    # Changes
    node_changes: List[NodeChange] = field(default_factory=list)
    edge_changes: List[EdgeChange] = field(default_factory=list)
    layer_changes: List[LayerChange] = field(default_factory=list)
    context_changes: List[ContextChange] = field(default_factory=list)
    
    # Summary
    summary: str = ""
    risk_level: str = "low"  # low, medium, high, critical
    breaking_changes: List[str] = field(default_factory=list)
    
    @property
    def total_changes(self) -> int:
        return (
            len([c for c in self.node_changes if c.change_type != ChangeType.UNCHANGED]) +
            len([c for c in self.edge_changes if c.change_type != ChangeType.UNCHANGED])
        )
    
    @property
    def added_count(self) -> int:
        return len([c for c in self.node_changes if c.change_type == ChangeType.ADDED])
    
    @property
    def removed_count(self) -> int:
        return len([c for c in self.node_changes if c.change_type == ChangeType.REMOVED])
    
    @property
    def modified_count(self) -> int:
        return len([c for c in self.node_changes if c.change_type == ChangeType.MODIFIED])
    
    def to_dict(self) -> dict:
        return {
            "base_ref": self.base_ref,
            "target_ref": self.target_ref,
            "base_timestamp": self.base_timestamp.isoformat() if self.base_timestamp else None,
            "target_timestamp": self.target_timestamp.isoformat() if self.target_timestamp else None,
            "summary": self.summary,
            "risk_level": self.risk_level,
            "breaking_changes": self.breaking_changes,
            "stats": {
                "total_changes": self.total_changes,
                "added": self.added_count,
                "removed": self.removed_count,
                "modified": self.modified_count,
            },
            "node_changes": [c.to_dict() for c in self.node_changes if c.change_type != ChangeType.UNCHANGED],
            "edge_changes": [c.to_dict() for c in self.edge_changes if c.change_type != ChangeType.UNCHANGED],
            "layer_changes": [c.to_dict() for c in self.layer_changes],
            "context_changes": [c.to_dict() for c in self.context_changes],
        }
    
    def to_mermaid_diff(self) -> str:
        """Generate a Mermaid diagram showing the diff."""
        lines = ["flowchart TD"]
        lines.append("    %% Blueprint Diff Visualization")
        lines.append(f"    %% {self.base_ref} → {self.target_ref}")
        lines.append("")
        
        # Style definitions
        lines.append("    classDef added fill:#22c55e,stroke:#16a34a,color:#fff")
        lines.append("    classDef removed fill:#ef4444,stroke:#dc2626,color:#fff")
        lines.append("    classDef modified fill:#f59e0b,stroke:#d97706,color:#fff")
        lines.append("")
        
        added_nodes = []
        removed_nodes = []
        modified_nodes = []
        
        for change in self.node_changes[:30]:  # Limit for readability
            safe_name = change.node_name.replace('"', "'")[:30]
            node_id = f"n_{hash(change.node_id) % 10000:04d}"
            
            if change.change_type == ChangeType.ADDED:
                lines.append(f'    {node_id}["+{safe_name}"]')
                added_nodes.append(node_id)
            elif change.change_type == ChangeType.REMOVED:
                lines.append(f'    {node_id}["-{safe_name}"]')
                removed_nodes.append(node_id)
            elif change.change_type == ChangeType.MODIFIED:
                lines.append(f'    {node_id}["~{safe_name}"]')
                modified_nodes.append(node_id)
        
        # Apply styles
        if added_nodes:
            lines.append(f"    class {','.join(added_nodes)} added")
        if removed_nodes:
            lines.append(f"    class {','.join(removed_nodes)} removed")
        if modified_nodes:
            lines.append(f"    class {','.join(modified_nodes)} modified")
        
        return "\n".join(lines)


class BlueprintDiffEngine:
    """
    Engine for comparing architecture between versions.
    
    Features:
    - Node-level comparison (classes, functions, modules)
    - Edge-level comparison (dependencies, calls)
    - Layer drift detection
    - Breaking change detection
    - Impact analysis
    """
    
    # Patterns that indicate high-impact changes
    HIGH_IMPACT_PATTERNS = [
        "api", "interface", "public", "export", "handler",
        "controller", "endpoint", "route", "schema"
    ]
    
    def __init__(self):
        self.parser = get_parser()
    
    def compare_akgs(
        self,
        base_akg: ArchitecturalKnowledgeGraph,
        target_akg: ArchitecturalKnowledgeGraph,
        base_ref: str = "base",
        target_ref: str = "target",
    ) -> BlueprintDiff:
        """
        Compare two AKGs and generate a diff.
        
        Args:
            base_akg: The baseline AKG (e.g., main branch)
            target_akg: The target AKG (e.g., feature branch)
            base_ref: Reference name for base
            target_ref: Reference name for target
            
        Returns:
            BlueprintDiff with all detected changes
        """
        diff = BlueprintDiff(
            base_ref=base_ref,
            target_ref=target_ref,
            base_timestamp=base_akg.created_at,
            target_timestamp=target_akg.created_at,
        )
        
        # Compare nodes
        diff.node_changes = self._compare_nodes(base_akg, target_akg)
        
        # Compare edges
        diff.edge_changes = self._compare_edges(base_akg, target_akg)
        
        # Compare layers
        diff.layer_changes = self._compare_layers(base_akg, target_akg)
        
        # Compare bounded contexts
        diff.context_changes = self._compare_contexts(base_akg, target_akg)
        
        # Analyze risk and breaking changes
        self._analyze_risk(diff)
        
        # Generate summary
        diff.summary = self._generate_summary(diff)
        
        return diff
    
    def _compare_nodes(
        self,
        base_akg: ArchitecturalKnowledgeGraph,
        target_akg: ArchitecturalKnowledgeGraph,
    ) -> List[NodeChange]:
        """Compare nodes between two AKGs."""
        changes = []
        
        base_nodes = set(base_akg.nodes.keys())
        target_nodes = set(target_akg.nodes.keys())
        
        # Added nodes
        for node_id in target_nodes - base_nodes:
            node = target_akg.nodes[node_id]
            changes.append(NodeChange(
                change_type=ChangeType.ADDED,
                node_id=node_id,
                node_name=node.name,
                node_type=node.type,
                file_path=node.file_path,
                new_line_range=node.line_range,
                details=f"New {node.type} added",
                impact=self._assess_impact(node),
            ))
        
        # Removed nodes
        for node_id in base_nodes - target_nodes:
            node = base_akg.nodes[node_id]
            changes.append(NodeChange(
                change_type=ChangeType.REMOVED,
                node_id=node_id,
                node_name=node.name,
                node_type=node.type,
                file_path=node.file_path,
                old_line_range=node.line_range,
                details=f"{node.type} removed",
                impact=self._assess_impact(node),
            ))
        
        # Modified nodes (same ID, different content)
        for node_id in base_nodes & target_nodes:
            base_node = base_akg.nodes[node_id]
            target_node = target_akg.nodes[node_id]
            
            if self._nodes_differ(base_node, target_node):
                changes.append(NodeChange(
                    change_type=ChangeType.MODIFIED,
                    node_id=node_id,
                    node_name=target_node.name,
                    node_type=target_node.type,
                    file_path=target_node.file_path,
                    old_line_range=base_node.line_range,
                    new_line_range=target_node.line_range,
                    details=self._describe_modification(base_node, target_node),
                    impact=self._assess_impact(target_node),
                ))
        
        return changes
    
    def _compare_edges(
        self,
        base_akg: ArchitecturalKnowledgeGraph,
        target_akg: ArchitecturalKnowledgeGraph,
    ) -> List[EdgeChange]:
        """Compare edges/relationships between two AKGs."""
        changes = []
        
        # Create edge signatures for comparison
        def edge_key(edge: AKGEdge) -> str:
            return f"{edge.source_id}|{edge.target_id}|{edge.relation}"
        
        base_edges = {edge_key(e): e for e in base_akg.edges}
        target_edges = {edge_key(e): e for e in target_akg.edges}
        
        base_keys = set(base_edges.keys())
        target_keys = set(target_edges.keys())
        
        # Added edges
        for key in target_keys - base_keys:
            edge = target_edges[key]
            changes.append(EdgeChange(
                change_type=ChangeType.ADDED,
                source_id=edge.source_id,
                target_id=edge.target_id,
                relation=edge.relation,
                details=f"New {edge.relation} dependency added",
            ))
        
        # Removed edges
        for key in base_keys - target_keys:
            edge = base_edges[key]
            changes.append(EdgeChange(
                change_type=ChangeType.REMOVED,
                source_id=edge.source_id,
                target_id=edge.target_id,
                relation=edge.relation,
                details=f"{edge.relation} dependency removed",
            ))
        
        return changes
    
    def _compare_layers(
        self,
        base_akg: ArchitecturalKnowledgeGraph,
        target_akg: ArchitecturalKnowledgeGraph,
    ) -> List[LayerChange]:
        """Compare architectural layers."""
        changes = []
        
        base_layers = {l.name: set(l.components) for l in base_akg.layers}
        target_layers = {l.name: set(l.components) for l in target_akg.layers}
        
        all_layer_names = set(base_layers.keys()) | set(target_layers.keys())
        
        for name in all_layer_names:
            base_comps = base_layers.get(name, set())
            target_comps = target_layers.get(name, set())
            
            added = list(target_comps - base_comps)
            removed = list(base_comps - target_comps)
            
            if added or removed:
                change_type = ChangeType.MODIFIED
                if name not in base_layers:
                    change_type = ChangeType.ADDED
                elif name not in target_layers:
                    change_type = ChangeType.REMOVED
                
                changes.append(LayerChange(
                    change_type=change_type,
                    layer_name=name,
                    added_components=added[:10],  # Limit
                    removed_components=removed[:10],
                ))
        
        return changes
    
    def _compare_contexts(
        self,
        base_akg: ArchitecturalKnowledgeGraph,
        target_akg: ArchitecturalKnowledgeGraph,
    ) -> List[ContextChange]:
        """Compare bounded contexts."""
        changes = []
        
        base_contexts = {c.name: set(c.key_entities) for c in base_akg.bounded_contexts}
        target_contexts = {c.name: set(c.key_entities) for c in target_akg.bounded_contexts}
        
        all_context_names = set(base_contexts.keys()) | set(target_contexts.keys())
        
        for name in all_context_names:
            base_entities = base_contexts.get(name, set())
            target_entities = target_contexts.get(name, set())
            
            added = list(target_entities - base_entities)
            removed = list(base_entities - target_entities)
            
            if added or removed:
                change_type = ChangeType.MODIFIED
                if name not in base_contexts:
                    change_type = ChangeType.ADDED
                elif name not in target_contexts:
                    change_type = ChangeType.REMOVED
                
                changes.append(ContextChange(
                    change_type=change_type,
                    context_name=name,
                    added_entities=added[:10],
                    removed_entities=removed[:10],
                ))
        
        return changes
    
    def _nodes_differ(self, base: AKGNode, target: AKGNode) -> bool:
        """Check if two nodes are meaningfully different."""
        if base.type != target.type:
            return True
        if base.file_path != target.file_path:
            return True
        if base.line_range != target.line_range:
            return True
        return False
    
    def _describe_modification(self, base: AKGNode, target: AKGNode) -> str:
        """Describe what changed in a modified node."""
        changes = []
        
        if base.file_path != target.file_path:
            changes.append(f"moved from {base.file_path} to {target.file_path}")
        
        if base.line_range != target.line_range:
            if base.line_range and target.line_range:
                size_diff = (target.line_range[1] - target.line_range[0]) - \
                           (base.line_range[1] - base.line_range[0])
                if size_diff > 0:
                    changes.append(f"expanded by {size_diff} lines")
                elif size_diff < 0:
                    changes.append(f"reduced by {abs(size_diff)} lines")
                else:
                    changes.append("position changed")
        
        return "; ".join(changes) if changes else "content modified"
    
    def _assess_impact(self, node: AKGNode) -> str:
        """Assess the impact level of a change to a node."""
        name_lower = node.name.lower()
        path_lower = (node.file_path or "").lower()
        
        # High impact if it's a public/API-facing component
        for pattern in self.HIGH_IMPACT_PATTERNS:
            if pattern in name_lower or pattern in path_lower:
                return "high"
        
        # Medium impact for services and domain logic
        if node.type in ("class", "interface") and "service" in name_lower:
            return "medium"
        
        return "low"
    
    def _analyze_risk(self, diff: BlueprintDiff):
        """Analyze overall risk level and identify breaking changes."""
        high_impact_changes = [
            c for c in diff.node_changes 
            if c.impact == "high" and c.change_type in (ChangeType.REMOVED, ChangeType.MODIFIED)
        ]
        
        # Detect breaking changes
        for change in high_impact_changes:
            if change.change_type == ChangeType.REMOVED:
                diff.breaking_changes.append(
                    f"Removed {change.node_type} '{change.node_name}' (potentially breaking)"
                )
        
        # Removed edges to public APIs
        for edge_change in diff.edge_changes:
            if edge_change.change_type == ChangeType.REMOVED:
                if any(p in edge_change.target_id.lower() for p in ["api", "public", "export"]):
                    diff.breaking_changes.append(
                        f"Removed dependency to '{edge_change.target_id}'"
                    )
        
        # Determine overall risk
        if len(diff.breaking_changes) > 5:
            diff.risk_level = "critical"
        elif len(diff.breaking_changes) > 2:
            diff.risk_level = "high"
        elif len(high_impact_changes) > 3:
            diff.risk_level = "medium"
        else:
            diff.risk_level = "low"
    
    def _generate_summary(self, diff: BlueprintDiff) -> str:
        """Generate a human-readable summary of the diff."""
        parts = []
        
        if diff.added_count > 0:
            parts.append(f"{diff.added_count} components added")
        if diff.removed_count > 0:
            parts.append(f"{diff.removed_count} components removed")
        if diff.modified_count > 0:
            parts.append(f"{diff.modified_count} components modified")
        
        if not parts:
            return "No architectural changes detected"
        
        summary = f"Architecture changes: {', '.join(parts)}."
        
        if diff.breaking_changes:
            summary += f" ⚠️ {len(diff.breaking_changes)} potential breaking change(s)."
        
        if diff.layer_changes:
            summary += f" Layer structure affected."
        
        return summary
