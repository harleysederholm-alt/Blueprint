"""
AKG Builder - Builds Architectural Knowledge Graph from parsed files

Uses Tree-sitter parser output to construct the AKG with
accurate evidence anchoring.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import networkx as nx

from app.core.tree_sitter_parser import (
    TreeSitterParser, 
    ParsedFile, 
    ParsedSymbol, 
    ParsedImport,
    ParsedCall,
    get_parser
)
from app.core.akg import (
    ArchitecturalKnowledgeGraph,
    AKGNode,
    AKGEdge,
    Evidence,
    BoundedContext,
    ArchitecturalLayer,
)

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a module/file."""
    path: str
    language: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class AKGBuilder:
    """
    Builds an Architectural Knowledge Graph from parsed source files.
    
    Features:
    - Accurate symbol extraction via Tree-sitter
    - Import/dependency graph construction
    - Layer detection (presentation, business, data)
    - Evidence anchoring with line numbers
    """
    
    # Layer detection patterns
    LAYER_PATTERNS = {
        "presentation": [
            "controller", "view", "component", "page", "screen",
            "handler", "route", "api", "endpoint", "ui", "frontend"
        ],
        "business": [
            "service", "usecase", "domain", "business", "core",
            "logic", "manager", "processor", "engine", "workflow"
        ],
        "data": [
            "repository", "dao", "model", "entity", "schema",
            "database", "db", "store", "persistence", "orm"
        ],
        "infrastructure": [
            "config", "util", "helper", "common", "shared",
            "middleware", "adapter", "client", "provider"
        ],
    }
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.parser = get_parser()
        self.parsed_files: Dict[str, ParsedFile] = {}
        self.modules: Dict[str, ModuleInfo] = {}
        self.dependency_graph = nx.DiGraph()
    
    def parse_directory(
        self, 
        files: List[Path],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, ParsedFile]:
        """
        Parse all source files in the given list.
        
        Args:
            files: List of file paths to parse
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary of parsed files
        """
        total = len(files)
        
        for i, file_path in enumerate(files):
            try:
                # Check if file is supported
                if not self.parser.get_language_for_file(str(file_path)):
                    continue
                
                parsed = self.parser.parse_file(file_path)
                rel_path = str(file_path.relative_to(self.repo_path))
                self.parsed_files[rel_path] = parsed
                
                # Build module info
                self._build_module_info(rel_path, parsed)
                
                if progress_callback and i % 10 == 0:
                    progress_callback(f"Parsed {i + 1}/{total} files")
                    
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
        
        return self.parsed_files
    
    def _build_module_info(self, path: str, parsed: ParsedFile):
        """Build module info from parsed file."""
        module = ModuleInfo(
            path=path,
            language=parsed.language,
            imports=[i.module for i in parsed.imports],
            classes=[s.name for s in parsed.classes],
            functions=[s.name for s in parsed.functions],
        )
        
        # Extract exports (public symbols)
        for symbol in parsed.symbols:
            # Python: skip private (underscore prefix)
            if parsed.language == "python":
                if not symbol.name.startswith("_"):
                    module.exports.append(symbol.name)
            # JS/TS: check for export keyword in signature
            elif parsed.language in ("typescript", "javascript", "tsx"):
                module.exports.append(symbol.name)
            else:
                module.exports.append(symbol.name)
        
        self.modules[path] = module
    
    def build_dependency_graph(self) -> nx.DiGraph:
        """
        Build a dependency graph between modules.
        
        Returns:
            NetworkX directed graph of module dependencies
        """
        self.dependency_graph.clear()
        
        # Add all modules as nodes
        for path, module in self.modules.items():
            self.dependency_graph.add_node(
                path,
                language=module.language,
                classes=module.classes,
                functions=module.functions,
            )
        
        # Add edges based on imports
        for path, module in self.modules.items():
            for imp in module.imports:
                # Try to resolve import to a file
                resolved = self._resolve_import(path, imp)
                if resolved and resolved in self.modules:
                    self.dependency_graph.add_edge(path, resolved, import_name=imp)
        
        return self.dependency_graph
    
    def _resolve_import(self, from_path: str, import_name: str) -> Optional[str]:
        """Try to resolve an import to a module path."""
        # Simple resolution strategies
        
        # 1. Try direct match
        for path in self.modules:
            module_name = Path(path).stem
            if module_name == import_name or import_name.endswith(module_name):
                return path
        
        # 2. Try path-based match
        import_path = import_name.replace(".", "/")
        for path in self.modules:
            if import_path in path:
                return path
        
        # 3. Relative imports
        if import_name.startswith("."):
            from_dir = str(Path(from_path).parent)
            rel_path = import_name.lstrip(".")
            possible = f"{from_dir}/{rel_path}"
            for path in self.modules:
                if possible in path:
                    return path
        
        return None
    
    def detect_layers(self) -> Dict[str, str]:
        """
        Detect architectural layers for each module.
        
        Returns:
            Dictionary mapping module paths to layer names
        """
        layer_assignments: Dict[str, str] = {}
        
        for path, module in self.modules.items():
            path_lower = path.lower()
            assigned = False
            
            for layer, patterns in self.LAYER_PATTERNS.items():
                for pattern in patterns:
                    if pattern in path_lower:
                        layer_assignments[path] = layer
                        assigned = True
                        break
                if assigned:
                    break
            
            if not assigned:
                # Default based on file location
                if "/api/" in path or "/routes/" in path:
                    layer_assignments[path] = "presentation"
                elif "/services/" in path or "/domain/" in path:
                    layer_assignments[path] = "business"
                elif "/models/" in path or "/db/" in path:
                    layer_assignments[path] = "data"
                else:
                    layer_assignments[path] = "infrastructure"
        
        return layer_assignments
    
    def detect_bounded_contexts(self) -> List[BoundedContext]:
        """
        Detect bounded contexts based on directory structure.
        
        Returns:
            List of detected bounded contexts
        """
        contexts: Dict[str, BoundedContext] = {}
        
        for path in self.modules:
            parts = Path(path).parts
            
            # Look for top-level directories as contexts
            if len(parts) >= 2:
                context_name = parts[0]
                
                # Skip common non-context directories
                if context_name in ("src", "lib", "pkg", "app", "internal"):
                    if len(parts) >= 3:
                        context_name = parts[1]
                    else:
                        continue
                
                if context_name not in contexts:
                    contexts[context_name] = BoundedContext(
                        name=context_name.title(),
                        purpose=f"Handles {context_name} functionality",
                        key_entities=[],
                        interfaces=[],
                        dependencies=[],
                    )
                
                # Add entities (classes) to context
                module = self.modules[path]
                for cls in module.classes:
                    if cls not in contexts[context_name].key_entities:
                        contexts[context_name].key_entities.append(cls)
        
        return list(contexts.values())
    
    def build_akg(
        self,
        repo_name: str = "Repository",
        progress_callback: Optional[callable] = None
    ) -> ArchitecturalKnowledgeGraph:
        """
        Build the complete Architectural Knowledge Graph.
        
        Args:
            repo_name: Name of the repository
            progress_callback: Optional progress callback
            
        Returns:
            Complete AKG
        """
        akg = ArchitecturalKnowledgeGraph(system_name=repo_name)
        
        if progress_callback:
            progress_callback("Building dependency graph...")
        
        self.build_dependency_graph()
        
        if progress_callback:
            progress_callback("Detecting layers...")
        
        layers = self.detect_layers()
        
        if progress_callback:
            progress_callback("Detecting bounded contexts...")
        
        contexts = self.detect_bounded_contexts()
        for ctx in contexts:
            akg.add_bounded_context(ctx)
        
        if progress_callback:
            progress_callback("Adding nodes and edges...")
        
        # Add layer information
        layer_groups: Dict[str, List[str]] = {}
        for path, layer in layers.items():
            if layer not in layer_groups:
                layer_groups[layer] = []
            layer_groups[layer].append(path)
        
        for layer_name, modules in layer_groups.items():
            akg.add_layer(ArchitecturalLayer(
                name=layer_name.title(),
                purpose=f"{layer_name.title()} layer components",
                components=modules,
            ))
        
        # Add nodes for each class/interface
        for path, module in self.modules.items():
            parsed = self.parsed_files.get(path)
            if not parsed:
                continue
            
            for symbol in parsed.symbols:
                if symbol.type in ("class", "interface"):
                    node = AKGNode(
                        id=f"{path}:{symbol.name}",
                        name=symbol.name,
                        type=symbol.type,
                        file_path=path,
                        line_range=(symbol.line_start, symbol.line_end),
                        description=f"{symbol.type.title()} in {path}",
                    )
                    akg.add_node(node)
                    
                    # Add evidence
                    akg.add_evidence(Evidence(
                        claim_id=f"exists:{symbol.name}",
                        file_path=path,
                        line_start=symbol.line_start,
                        line_end=symbol.line_end,
                        quote=symbol.signature or f"{symbol.type} {symbol.name}",
                    ))
        
        # Add edges from dependencies
        for from_path, to_path, data in self.dependency_graph.edges(data=True):
            # Find the main class/module for each path
            from_classes = self.modules[from_path].classes
            to_classes = self.modules[to_path].classes
            
            from_node = from_classes[0] if from_classes else Path(from_path).stem
            to_node = to_classes[0] if to_classes else Path(to_path).stem
            
            edge = AKGEdge(
                source_id=f"{from_path}:{from_node}",
                target_id=f"{to_path}:{to_node}",
                relation="depends_on",
            )
            akg.add_edge(edge)
        
        return akg
    
    def get_parsing_stats(self) -> Dict:
        """Get statistics about the parsed files."""
        total_files = len(self.parsed_files)
        total_classes = sum(len(m.classes) for m in self.modules.values())
        total_functions = sum(len(m.functions) for m in self.modules.values())
        total_imports = sum(len(m.imports) for m in self.modules.values())
        
        languages = {}
        for m in self.modules.values():
            languages[m.language] = languages.get(m.language, 0) + 1
        
        return {
            "files_parsed": total_files,
            "classes_found": total_classes,
            "functions_found": total_functions,
            "imports_found": total_imports,
            "languages": languages,
            "tree_sitter_available": self.parser.is_available,
        }
