"""
Tests for Export Engine

Verifies Markdown, HTML, and JSON export generation.
"""

import pytest
import json
from datetime import datetime

from app.core.export_engine import ExportEngine, ExportOptions


class TestExportEngine:
    """Test cases for the export engine."""
    
    @pytest.fixture
    def sample_analysis(self):
        """Sample analysis result for testing."""
        return {
            "repo_url": "https://github.com/example/repo",
            "branch": "main",
            "audience": "engineer",
            "architecture": {
                "architecture_style": "Microservices",
                "bounded_contexts": [
                    {
                        "name": "User Management",
                        "purpose": "Handles user authentication and profiles",
                        "key_entities": ["User", "Profile", "Session"],
                    },
                    {
                        "name": "Orders",
                        "purpose": "Manages order processing",
                        "key_entities": ["Order", "OrderItem"],
                    },
                ],
                "key_design_patterns": [
                    {"pattern": "Repository Pattern", "description": "Data access abstraction"},
                    {"pattern": "CQRS", "description": "Command Query Separation"},
                ],
                "coupling_cohesion_assessment": {
                    "coupling_score": 7,
                    "cohesion_score": 8,
                },
                "evidence_map": {
                    "claim_001": {
                        "file_path": "src/users/service.py",
                        "line_range": "10-50",
                        "confidence": "high",
                    },
                },
            },
            "documentation": {
                "executive_summary": "A well-structured microservices application.",
                "key_findings": [
                    {"finding": "Good separation of concerns", "importance": "High"},
                    {"finding": "Could improve error handling", "importance": "Medium"},
                ],
                "recommendations": [
                    {"recommendation": "Add centralized logging", "priority": "High"},
                ],
                "generated_adrs": [
                    {
                        "title": "ADR-001: Use PostgreSQL",
                        "status": "Accepted",
                        "context": "Need reliable ACID database",
                        "decision": "Use PostgreSQL for all data storage",
                        "consequences": "May need additional infrastructure",
                    },
                ],
            },
            "diagrams": {
                "c4_context": "flowchart TD\n  A[User] --> B[System]",
                "dependency_graph": "flowchart LR\n  UserService --> Database",
            },
            "stats": {
                "total_files": 150,
                "critical_files": 12,
                "parsed_files": 145,
            },
        }
    
    def test_engine_initialization(self):
        """Test that engine initializes correctly."""
        engine = ExportEngine()
        assert engine is not None
    
    def test_export_markdown_basic(self, sample_analysis):
        """Test basic Markdown export."""
        engine = ExportEngine()
        md = engine.export_markdown(sample_analysis)
        
        assert md is not None
        assert "# Architecture Analysis" in md
        assert "repo" in md.lower()
    
    def test_export_markdown_includes_architecture(self, sample_analysis):
        """Test that Markdown includes architecture details."""
        engine = ExportEngine()
        md = engine.export_markdown(sample_analysis)
        
        assert "Microservices" in md
        assert "User Management" in md
        assert "Repository Pattern" in md
    
    def test_export_markdown_includes_diagrams(self, sample_analysis):
        """Test that Markdown includes Mermaid diagrams."""
        engine = ExportEngine()
        md = engine.export_markdown(sample_analysis)
        
        assert "```mermaid" in md
        assert "flowchart" in md
    
    def test_export_markdown_excludes_diagrams(self, sample_analysis):
        """Test that diagrams can be excluded."""
        engine = ExportEngine()
        options = ExportOptions(include_diagrams=False)
        md = engine.export_markdown(sample_analysis, options)
        
        assert "```mermaid" not in md
    
    def test_export_markdown_includes_documentation(self, sample_analysis):
        """Test that Markdown includes documentation."""
        engine = ExportEngine()
        md = engine.export_markdown(sample_analysis)
        
        assert "Executive Summary" in md
        assert "Key Findings" in md
        assert "Recommendations" in md
    
    def test_export_markdown_includes_adrs(self, sample_analysis):
        """Test that Markdown includes ADRs."""
        engine = ExportEngine()
        md = engine.export_markdown(sample_analysis)
        
        assert "Architecture Decision Records" in md
        assert "ADR-001" in md
        assert "PostgreSQL" in md
    
    def test_export_html_basic(self, sample_analysis):
        """Test basic HTML export."""
        engine = ExportEngine()
        html = engine.export_html(sample_analysis)
        
        assert html is not None
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "mermaid" in html.lower()
    
    def test_export_html_includes_styles(self, sample_analysis):
        """Test that HTML includes embedded styles."""
        engine = ExportEngine()
        html = engine.export_html(sample_analysis)
        
        assert "<style>" in html
        assert "font-family" in html
    
    def test_export_html_includes_mermaid_script(self, sample_analysis):
        """Test that HTML includes Mermaid.js."""
        engine = ExportEngine()
        html = engine.export_html(sample_analysis)
        
        assert "mermaid" in html
        assert "<script" in html
    
    def test_export_json_basic(self, sample_analysis):
        """Test basic JSON export."""
        engine = ExportEngine()
        json_str = engine.export_json(sample_analysis)
        
        assert json_str is not None
        data = json.loads(json_str)
        assert "meta" in data
        assert "architecture" in data
    
    def test_export_json_includes_meta(self, sample_analysis):
        """Test that JSON includes metadata."""
        engine = ExportEngine()
        json_str = engine.export_json(sample_analysis)
        
        data = json.loads(json_str)
        assert data["meta"]["version"] == "3.0"
        assert "exported_at" in data["meta"]
    
    def test_export_json_valid_structure(self, sample_analysis):
        """Test that JSON has valid structure."""
        engine = ExportEngine()
        json_str = engine.export_json(sample_analysis)
        
        data = json.loads(json_str)
        assert data["repo_url"] == sample_analysis["repo_url"]
        assert "bounded_contexts" in data["architecture"]
    
    def test_export_options_title(self, sample_analysis):
        """Test custom title option."""
        engine = ExportEngine()
        options = ExportOptions(title="My Custom Report")
        md = engine.export_markdown(sample_analysis, options)
        
        assert "# My Custom Report" in md
    
    def test_export_empty_analysis(self):
        """Test export with minimal data."""
        engine = ExportEngine()
        empty = {"repo_url": "https://example.com/repo"}
        
        md = engine.export_markdown(empty)
        assert md is not None
        assert "example.com" in md or "repo" in md


class TestDiffExport:
    """Test diff export functionality."""
    
    @pytest.fixture
    def sample_diff(self):
        """Sample diff result for testing."""
        return {
            "base_ref": "main",
            "target_ref": "feature-xyz",
            "summary": "5 components added, 2 removed",
            "risk_level": "medium",
            "breaking_changes": ["Removed UserAPI endpoint"],
            "stats": {
                "total_changes": 8,
                "added": 5,
                "removed": 2,
                "modified": 1,
            },
            "node_changes": [
                {
                    "change_type": "added",
                    "node_name": "NewService",
                    "node_type": "class",
                },
                {
                    "change_type": "removed",
                    "node_name": "OldService",
                    "node_type": "class",
                },
            ],
        }
    
    def test_export_diff_markdown(self, sample_diff):
        """Test diff Markdown export."""
        engine = ExportEngine()
        md = engine.export_diff_markdown(sample_diff)
        
        assert md is not None
        assert "# Architecture Diff Report" in md
        assert "main" in md
        assert "feature-xyz" in md
    
    def test_export_diff_includes_stats(self, sample_diff):
        """Test that diff export includes stats."""
        engine = ExportEngine()
        md = engine.export_diff_markdown(sample_diff)
        
        assert "+5" in md
        assert "-2" in md
    
    def test_export_diff_includes_breaking_changes(self, sample_diff):
        """Test that diff export includes breaking changes."""
        engine = ExportEngine()
        md = engine.export_diff_markdown(sample_diff)
        
        assert "Breaking Changes" in md
        assert "UserAPI" in md
    
    def test_export_diff_includes_risk(self, sample_diff):
        """Test that diff export includes risk level."""
        engine = ExportEngine()
        md = engine.export_diff_markdown(sample_diff)
        
        assert "Medium" in md or "medium" in md


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
