"""
Tests for Tree-sitter Parser and AKG Builder

Verifies that the Tree-sitter based parsing works correctly.
"""

import pytest
from pathlib import Path
import tempfile
import os

from app.core.tree_sitter_parser import TreeSitterParser, get_parser, ParsedFile
from app.core.akg_builder import AKGBuilder
from app.core.akg import ArchitecturalKnowledgeGraph


class TestTreeSitterParser:
    """Test cases for the Tree-sitter parser."""
    
    def test_parser_initialization(self):
        """Test that parser initializes correctly."""
        parser = get_parser()
        assert parser is not None
        # Note: may or may not have tree-sitter available
        assert isinstance(parser.is_available, bool)
    
    def test_language_detection(self):
        """Test file extension to language mapping."""
        parser = get_parser()
        
        assert parser.get_language_for_file("test.py") == "python"
        assert parser.get_language_for_file("test.ts") == "typescript"
        assert parser.get_language_for_file("test.tsx") == "tsx"
        assert parser.get_language_for_file("test.js") == "javascript"
        assert parser.get_language_for_file("test.go") == "go"
        assert parser.get_language_for_file("test.txt") is None
        assert parser.get_language_for_file("test.md") is None
    
    def test_parse_python_file(self, tmp_path):
        """Test parsing a Python file."""
        parser = get_parser()
        
        # Create a test Python file
        test_file = tmp_path / "test_module.py"
        test_file.write_text('''
import os
from typing import List, Optional

class MyClass:
    """A test class."""
    
    def __init__(self, name: str):
        self.name = name
    
    def greet(self) -> str:
        return f"Hello, {self.name}"

def standalone_function(x: int, y: int) -> int:
    """A standalone function."""
    return x + y

async def async_function():
    """An async function."""
    pass
''')
        
        result = parser.parse_file(test_file)
        
        assert result is not None
        assert result.language == "python"
        assert len(result.errors) == 0
        
        # Check imports
        assert len(result.imports) >= 1
        import_modules = [i.module for i in result.imports]
        assert "os" in import_modules or "typing" in " ".join(import_modules)
        
        # Check classes
        classes = [s for s in result.symbols if s.type == "class"]
        assert len(classes) >= 1
        class_names = [c.name for c in classes]
        assert "MyClass" in class_names
        
        # Check functions
        functions = [s for s in result.symbols if s.type == "function"]
        func_names = [f.name for f in functions]
        assert "standalone_function" in func_names
    
    def test_parse_typescript_file(self, tmp_path):
        """Test parsing a TypeScript file."""
        parser = get_parser()
        
        test_file = tmp_path / "test_module.ts"
        test_file.write_text('''
import { useState, useEffect } from 'react';
import axios from 'axios';

interface User {
    id: number;
    name: string;
}

class UserService {
    async getUser(id: number): Promise<User> {
        return { id, name: 'Test' };
    }
}

export function fetchData(): void {
    console.log('fetching');
}

const arrowFunc = (x: number): number => x * 2;
''')
        
        result = parser.parse_file(test_file)
        
        assert result is not None
        assert result.language == "typescript"
        
        # Check imports
        assert len(result.imports) >= 1
        
        # Check for class or interface
        class_and_interfaces = [s for s in result.symbols if s.type in ("class", "interface")]
        names = [s.name for s in class_and_interfaces]
        # Should find at least UserService or User
        assert len(names) >= 1
    
    def test_parse_go_file(self, tmp_path):
        """Test parsing a Go file."""
        parser = get_parser()
        
        test_file = tmp_path / "test_module.go"
        test_file.write_text('''
package main

import (
    "fmt"
    "net/http"
)

type Server struct {
    Port int
    Name string
}

func (s *Server) Start() error {
    return nil
}

func NewServer(port int) *Server {
    return &Server{Port: port}
}
''')
        
        result = parser.parse_file(test_file)
        
        assert result is not None
        assert result.language == "go"
        
        # Check imports
        import_modules = [i.module for i in result.imports]
        assert any("fmt" in m for m in import_modules)


class TestAKGBuilder:
    """Test cases for the AKG Builder."""
    
    def test_builder_initialization(self, tmp_path):
        """Test AKG Builder initialization."""
        builder = AKGBuilder(tmp_path)
        assert builder.repo_path == tmp_path
        assert builder.parser is not None
    
    def test_layer_detection(self, tmp_path):
        """Test layer detection from file paths."""
        builder = AKGBuilder(tmp_path)
        
        # Create mock module structure
        builder.modules = {
            "app/api/routes/users.py": type('Module', (), {'path': 'app/api/routes/users.py', 'language': 'python', 'classes': [], 'functions': [], 'imports': [], 'exports': []})(),
            "app/services/user_service.py": type('Module', (), {'path': 'app/services/user_service.py', 'language': 'python', 'classes': [], 'functions': [], 'imports': [], 'exports': []})(),
            "app/models/user.py": type('Module', (), {'path': 'app/models/user.py', 'language': 'python', 'classes': [], 'functions': [], 'imports': [], 'exports': []})(),
            "app/config/settings.py": type('Module', (), {'path': 'app/config/settings.py', 'language': 'python', 'classes': [], 'functions': [], 'imports': [], 'exports': []})(),
        }
        
        layers = builder.detect_layers()
        
        assert layers["app/api/routes/users.py"] == "presentation"
        assert layers["app/services/user_service.py"] == "business"
        assert layers["app/models/user.py"] == "data"
        assert layers["app/config/settings.py"] == "infrastructure"
    
    def test_build_akg(self, tmp_path):
        """Test building a complete AKG."""
        # Create test files
        (tmp_path / "main.py").write_text('''
class MainApp:
    def run(self):
        pass
''')
        (tmp_path / "utils.py").write_text('''
def helper():
    return True
''')
        
        builder = AKGBuilder(tmp_path)
        files = list(tmp_path.glob("*.py"))
        builder.parse_directory(files)
        
        akg = builder.build_akg(repo_name="TestRepo")
        
        assert akg is not None
        assert akg.system_name == "TestRepo"
        
        stats = builder.get_parsing_stats()
        assert stats["files_parsed"] >= 1


class TestAKGIntegration:
    """Integration tests for AKG with Tree-sitter parser."""
    
    def test_evidence_anchoring(self, tmp_path):
        """Test that evidence is properly anchored to source lines."""
        test_file = tmp_path / "service.py"
        test_file.write_text('''
class UserService:
    """Handles user operations."""
    
    def get_user(self, user_id: int):
        return {"id": user_id}
    
    def create_user(self, data: dict):
        return data
''')
        
        builder = AKGBuilder(tmp_path)
        builder.parse_directory([test_file])
        akg = builder.build_akg(repo_name="TestRepo")
        
        # Check that we have nodes
        assert len(akg.nodes) >= 1
        
        # Check evidence map
        evidence_items = list(akg._evidence_map.values())
        for ev in evidence_items:
            assert ev.file_path is not None
            assert ev.line_start > 0
            assert ev.line_end >= ev.line_start


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
