"""
Tests for Blueprint Diff Engine

Verifies diff comparison, change detection, and risk analysis.
"""

import pytest
from datetime import datetime

from app.core.diff_engine import (
    BlueprintDiffEngine,
    BlueprintDiff,
    NodeChange,
    EdgeChange,
    ChangeType,
)
from app.core.akg import (
    ArchitecturalKnowledgeGraph,
    AKGNode,
    AKGEdge,
    BoundedContext,
    ArchitecturalLayer,
)


class TestBlueprintDiffEngine:
    """Test cases for the diff engine."""
    
    def test_engine_initialization(self):
        """Test that engine initializes correctly."""
        engine = BlueprintDiffEngine()
        assert engine is not None
    
    def test_compare_identical_akgs(self):
        """Test comparing two identical AKGs."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_node(AKGNode(id="node1", name="UserService", type="class"))
        akg1.add_node(AKGNode(id="node2", name="OrderService", type="class"))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_node(AKGNode(id="node1", name="UserService", type="class"))
        akg2.add_node(AKGNode(id="node2", name="OrderService", type="class"))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        assert diff.total_changes == 0
        assert diff.added_count == 0
        assert diff.removed_count == 0
    
    def test_detect_added_nodes(self):
        """Test detecting added nodes."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_node(AKGNode(id="node1", name="UserService", type="class"))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_node(AKGNode(id="node1", name="UserService", type="class"))
        akg2.add_node(AKGNode(id="node2", name="OrderService", type="class"))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        assert diff.added_count == 1
        added_nodes = [c for c in diff.node_changes if c.change_type == ChangeType.ADDED]
        assert len(added_nodes) == 1
        assert added_nodes[0].node_name == "OrderService"
    
    def test_detect_removed_nodes(self):
        """Test detecting removed nodes."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_node(AKGNode(id="node1", name="UserService", type="class"))
        akg1.add_node(AKGNode(id="node2", name="LegacyService", type="class"))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_node(AKGNode(id="node1", name="UserService", type="class"))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        assert diff.removed_count == 1
        removed_nodes = [c for c in diff.node_changes if c.change_type == ChangeType.REMOVED]
        assert len(removed_nodes) == 1
        assert removed_nodes[0].node_name == "LegacyService"
    
    def test_detect_modified_nodes(self):
        """Test detecting modified nodes."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_node(AKGNode(
            id="node1", 
            name="UserService", 
            type="class",
            line_range=(10, 50),
        ))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_node(AKGNode(
            id="node1", 
            name="UserService", 
            type="class",
            line_range=(10, 80),  # Expanded
        ))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        assert diff.modified_count == 1
        modified_nodes = [c for c in diff.node_changes if c.change_type == ChangeType.MODIFIED]
        assert len(modified_nodes) == 1
        assert "expanded" in modified_nodes[0].details.lower()
    
    def test_detect_edge_changes(self):
        """Test detecting edge/dependency changes."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_node(AKGNode(id="node1", name="UserService", type="class"))
        akg1.add_node(AKGNode(id="node2", name="Database", type="database"))
        akg1.add_edge(AKGEdge(source_id="node1", target_id="node2", relation="uses"))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_node(AKGNode(id="node1", name="UserService", type="class"))
        akg2.add_node(AKGNode(id="node2", name="Database", type="database"))
        akg2.add_node(AKGNode(id="node3", name="Cache", type="external"))
        akg2.add_edge(AKGEdge(source_id="node1", target_id="node2", relation="uses"))
        akg2.add_edge(AKGEdge(source_id="node1", target_id="node3", relation="uses"))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        added_edges = [c for c in diff.edge_changes if c.change_type == ChangeType.ADDED]
        assert len(added_edges) == 1
    
    def test_risk_analysis_low(self):
        """Test low risk analysis."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_node(AKGNode(id="node1", name="Helper", type="function"))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_node(AKGNode(id="node1", name="Helper", type="function"))
        akg2.add_node(AKGNode(id="node2", name="Utils", type="function"))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        assert diff.risk_level == "low"
        assert len(diff.breaking_changes) == 0
    
    def test_risk_analysis_high(self):
        """Test high risk detection for API changes."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_node(AKGNode(id="api1", name="UserAPIHandler", type="class", file_path="api/users.py"))
        akg1.add_node(AKGNode(id="api2", name="OrderAPIEndpoint", type="class", file_path="api/orders.py"))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_node(AKGNode(id="api1", name="UserAPIHandler", type="class", file_path="api/users.py"))
        # OrderAPIEndpoint removed - potentially breaking
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        # Should detect high impact removal
        removed = [c for c in diff.node_changes if c.change_type == ChangeType.REMOVED]
        assert len(removed) == 1
        assert removed[0].impact == "high"
    
    def test_mermaid_diff_generation(self):
        """Test Mermaid diff diagram generation."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_node(AKGNode(id="node1", name="UserService", type="class"))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_node(AKGNode(id="node1", name="UserService", type="class"))
        akg2.add_node(AKGNode(id="node2", name="NewFeature", type="class"))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        mermaid = diff.to_mermaid_diff()
        
        assert "flowchart TD" in mermaid
        assert "classDef added" in mermaid
    
    def test_summary_generation(self):
        """Test human-readable summary generation."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_node(AKGNode(id="node1", name="Service1", type="class"))
        akg2.add_node(AKGNode(id="node2", name="Service2", type="class"))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        assert "2 components added" in diff.summary
    
    def test_layer_comparison(self):
        """Test layer change detection."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_layer(ArchitecturalLayer(name="Presentation", components=["api.py"]))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_layer(ArchitecturalLayer(name="Presentation", components=["api.py", "routes.py"]))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        assert len(diff.layer_changes) == 1
        assert "routes.py" in diff.layer_changes[0].added_components
    
    def test_context_comparison(self):
        """Test bounded context change detection."""
        akg1 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg1.add_bounded_context(BoundedContext(name="Users", key_entities=["User"]))
        
        akg2 = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        akg2.add_bounded_context(BoundedContext(name="Users", key_entities=["User", "Profile"]))
        
        engine = BlueprintDiffEngine()
        diff = engine.compare_akgs(akg1, akg2, "base", "target")
        
        assert len(diff.context_changes) == 1
        assert "Profile" in diff.context_changes[0].added_entities


class TestBlueprintDiffDataclass:
    """Test the BlueprintDiff dataclass."""
    
    def test_to_dict(self):
        """Test serialization to dict."""
        diff = BlueprintDiff(
            base_ref="abc123",
            target_ref="def456",
        )
        diff.node_changes.append(NodeChange(
            change_type=ChangeType.ADDED,
            node_id="node1",
            node_name="TestNode",
            node_type="class",
        ))
        
        result = diff.to_dict()
        
        assert result["base_ref"] == "abc123"
        assert result["target_ref"] == "def456"
        assert result["stats"]["added"] == 1
        assert len(result["node_changes"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
