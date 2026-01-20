"""
Tests for Knowledge Graph Query Engine

Verifies query classification and result generation.
"""

import pytest

from app.core.query_engine import (
    KnowledgeGraphQueryEngine,
    QueryType,
    QueryResult,
)
from app.core.akg import (
    ArchitecturalKnowledgeGraph,
    AKGNode,
    AKGEdge,
    BoundedContext,
    ArchitecturalLayer,
)


class TestQueryEngine:
    """Test cases for the query engine."""
    
    @pytest.fixture
    def sample_akg(self):
        """Create a sample AKG for testing."""
        akg = ArchitecturalKnowledgeGraph(system_name="TestSystem")
        
        # Add nodes
        akg.add_node(AKGNode(id="node1", name="UserService", type="class", file_path="services/user.py"))
        akg.add_node(AKGNode(id="node2", name="OrderService", type="class", file_path="services/order.py"))
        akg.add_node(AKGNode(id="node3", name="Database", type="database"))
        akg.add_node(AKGNode(id="node4", name="UserController", type="class", file_path="api/users.py"))
        akg.add_node(AKGNode(id="node5", name="AuthHandler", type="function", file_path="auth/handler.py"))
        
        # Add edges
        akg.add_edge(AKGEdge(source_id="node1", target_id="node3", relation="uses"))
        akg.add_edge(AKGEdge(source_id="node2", target_id="node3", relation="uses"))
        akg.add_edge(AKGEdge(source_id="node4", target_id="node1", relation="calls"))
        
        # Add layers
        akg.add_layer(ArchitecturalLayer(name="Presentation", components=["api/users.py"]))
        akg.add_layer(ArchitecturalLayer(name="Business", components=["services/user.py", "services/order.py"]))
        
        # Add contexts
        akg.add_bounded_context(BoundedContext(name="Users", key_entities=["User", "Profile"]))
        
        return akg
    
    def test_engine_initialization(self):
        """Test that engine initializes correctly."""
        engine = KnowledgeGraphQueryEngine()
        assert engine is not None
    
    def test_engine_with_akg(self, sample_akg):
        """Test engine with AKG attached."""
        engine = KnowledgeGraphQueryEngine(sample_akg)
        assert engine.akg is not None
    
    def test_classify_find_component(self):
        """Test query classification for component search."""
        engine = KnowledgeGraphQueryEngine()
        
        assert engine.classify_query("Find class UserService") == QueryType.FIND_COMPONENT
        assert engine.classify_query("Where is the authentication module?") == QueryType.FIND_COMPONENT
        assert engine.classify_query("Show me the UserController") == QueryType.FIND_COMPONENT
    
    def test_classify_dependencies(self):
        """Test query classification for dependencies."""
        engine = KnowledgeGraphQueryEngine()
        
        assert engine.classify_query("What depends on Database?") == QueryType.LIST_DEPENDENCIES
        assert engine.classify_query("List all imports") == QueryType.LIST_DEPENDENCIES
        assert engine.classify_query("Show dependencies of UserService") == QueryType.LIST_DEPENDENCIES
    
    def test_classify_patterns(self):
        """Test query classification for patterns."""
        engine = KnowledgeGraphQueryEngine()
        
        assert engine.classify_query("What design patterns are used?") == QueryType.FIND_PATTERN
        assert engine.classify_query("Find factory pattern") == QueryType.FIND_PATTERN
        assert engine.classify_query("Is there a repository pattern?") == QueryType.FIND_PATTERN
    
    def test_classify_layers(self):
        """Test query classification for layers."""
        engine = KnowledgeGraphQueryEngine()
        
        assert engine.classify_query("Analyze architectural layers") == QueryType.ANALYZE_LAYER
        assert engine.classify_query("What's in the presentation layer?") == QueryType.ANALYZE_LAYER
        assert engine.classify_query("Show all layers") == QueryType.ANALYZE_LAYER
    
    def test_classify_hotspots(self):
        """Test query classification for hotspots."""
        engine = KnowledgeGraphQueryEngine()
        
        assert engine.classify_query("Find coupling hotspots") == QueryType.FIND_HOTSPOTS
        assert engine.classify_query("Most connected components") == QueryType.FIND_HOTSPOTS
        assert engine.classify_query("What are the highly coupled modules?") == QueryType.FIND_HOTSPOTS
    
    def test_classify_general(self):
        """Test general query classification."""
        engine = KnowledgeGraphQueryEngine()
        
        assert engine.classify_query("Hello") == QueryType.GENERAL
        assert engine.classify_query("What is this system?") == QueryType.GENERAL
    
    def test_query_find_component(self, sample_akg):
        """Test finding components."""
        engine = KnowledgeGraphQueryEngine(sample_akg)
        
        result = engine.query("Find class UserService")
        
        assert result is not None
        assert result.query_type == QueryType.FIND_COMPONENT
        assert "UserService" in result.answer
        assert len(result.nodes) >= 1
    
    def test_query_dependencies(self, sample_akg):
        """Test listing dependencies."""
        engine = KnowledgeGraphQueryEngine(sample_akg)
        
        result = engine.query("What depends on Database?")
        
        assert result is not None
        assert result.query_type == QueryType.LIST_DEPENDENCIES
        assert len(result.edges) > 0
    
    def test_query_hotspots(self, sample_akg):
        """Test finding hotspots."""
        engine = KnowledgeGraphQueryEngine(sample_akg)
        
        result = engine.query("Find coupling hotspots")
        
        assert result is not None
        assert result.query_type == QueryType.FIND_HOTSPOTS
        assert "Database" in result.answer  # Most connected
    
    def test_query_layers(self, sample_akg):
        """Test layer analysis."""
        engine = KnowledgeGraphQueryEngine(sample_akg)
        
        result = engine.query("Analyze architectural layers")
        
        assert result is not None
        assert result.query_type == QueryType.ANALYZE_LAYER
        assert "Presentation" in result.answer or "Business" in result.answer
    
    def test_query_general(self, sample_akg):
        """Test general query."""
        engine = KnowledgeGraphQueryEngine(sample_akg)
        
        result = engine.query("Tell me about this system")
        
        assert result is not None
        assert "TestSystem" in result.answer
        assert "Components" in result.answer
    
    def test_query_no_akg(self):
        """Test query without AKG loaded."""
        engine = KnowledgeGraphQueryEngine()
        
        result = engine.query("Find something")
        
        assert result.confidence == 0.0
        assert "No architecture" in result.answer
    
    def test_get_suggestions(self, sample_akg):
        """Test getting query suggestions."""
        engine = KnowledgeGraphQueryEngine(sample_akg)
        
        suggestions = engine.get_suggestions()
        
        assert len(suggestions) > 0
        assert any("UserService" in s for s in suggestions) or len(suggestions) >= 3
    
    def test_result_to_dict(self, sample_akg):
        """Test result serialization."""
        engine = KnowledgeGraphQueryEngine(sample_akg)
        result = engine.query("Find UserService")
        
        result_dict = result.to_dict()
        
        assert "query" in result_dict
        assert "query_type" in result_dict
        assert "answer" in result_dict
        assert "confidence" in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
