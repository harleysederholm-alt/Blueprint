"""
Code Parser - Tree-sitter based AST extraction
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import re

logger = logging.getLogger(__name__)


@dataclass
class FunctionDef:
    """Extracted function definition."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    parameters: list[str] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    class_name: Optional[str] = None


@dataclass
class ClassDef:
    """Extracted class definition."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    bases: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)


@dataclass
class ImportDef:
    """Extracted import statement."""
    module: str
    names: list[str] = field(default_factory=list)
    alias: Optional[str] = None
    line: int = 0
    is_relative: bool = False


@dataclass
class ParsedFile:
    """Complete parsed file with all extractions."""
    file_path: str
    language: str
    functions: list[FunctionDef] = field(default_factory=list)
    classes: list[ClassDef] = field(default_factory=list)
    imports: list[ImportDef] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    error: Optional[str] = None


class CodeParser:
    """
    Multi-language code parser using regex-based extraction.
    
    Note: For production, use tree-sitter for accurate AST parsing.
    This implementation uses regex for simplicity and broader compatibility.
    """
    
    SUPPORTED_LANGUAGES = ["python", "typescript", "javascript", "go", "rust", "java"]
    
    def __init__(self):
        self.parsed_cache: dict[str, ParsedFile] = {}
    
    def parse_file(self, file_path: Path, language: str) -> ParsedFile:
        """
        Parse a source file and extract structural information.
        
        Args:
            file_path: Path to the source file
            language: Programming language
            
        Returns:
            ParsedFile with functions, classes, and imports
        """
        cache_key = str(file_path)
        if cache_key in self.parsed_cache:
            return self.parsed_cache[cache_key]
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            return ParsedFile(
                file_path=str(file_path),
                language=language,
                error=str(e),
            )
        
        if language == "python":
            result = self._parse_python(content, str(file_path))
        elif language in ("typescript", "javascript"):
            result = self._parse_javascript(content, str(file_path), language)
        elif language == "go":
            result = self._parse_go(content, str(file_path))
        else:
            result = ParsedFile(
                file_path=str(file_path),
                language=language,
                error=f"Unsupported language: {language}",
            )
        
        self.parsed_cache[cache_key] = result
        return result
    
    def _parse_python(self, content: str, file_path: str) -> ParsedFile:
        """Parse Python source code."""
        functions: list[FunctionDef] = []
        classes: list[ClassDef] = []
        imports: list[ImportDef] = []
        
        lines = content.split("\n")
        
        # Parse imports
        import_pattern = re.compile(
            r"^(?:from\s+([\w.]+)\s+)?import\s+(.+)$"
        )
        for i, line in enumerate(lines):
            match = import_pattern.match(line.strip())
            if match:
                module = match.group(1) or ""
                names_str = match.group(2)
                
                # Parse imported names
                names = []
                for part in names_str.split(","):
                    part = part.strip()
                    if " as " in part:
                        name = part.split(" as ")[0].strip()
                    else:
                        name = part
                    if name and name != "*":
                        names.append(name)
                
                if module:
                    imports.append(ImportDef(
                        module=module,
                        names=names,
                        line=i + 1,
                        is_relative=module.startswith("."),
                    ))
                else:
                    for name in names:
                        imports.append(ImportDef(
                            module=name,
                            names=[],
                            line=i + 1,
                        ))
        
        # Parse classes
        class_pattern = re.compile(
            r"^(\s*)class\s+(\w+)(?:\((.*?)\))?\s*:"
        )
        current_class = None
        current_class_indent = 0
        
        for i, line in enumerate(lines):
            match = class_pattern.match(line)
            if match:
                indent = len(match.group(1))
                name = match.group(2)
                bases_str = match.group(3) or ""
                bases = [b.strip() for b in bases_str.split(",") if b.strip()]
                
                # Find class end
                end_line = i + 1
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith(" " * (indent + 1)):
                        break
                    end_line = j + 1
                
                classes.append(ClassDef(
                    name=name,
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=end_line,
                    bases=bases,
                ))
                current_class = name
                current_class_indent = indent
        
        # Parse functions/methods
        func_pattern = re.compile(
            r"^(\s*)(async\s+)?def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*(.+?))?\s*:"
        )
        
        for i, line in enumerate(lines):
            match = func_pattern.match(line)
            if match:
                indent = len(match.group(1))
                is_async = bool(match.group(2))
                name = match.group(3)
                params_str = match.group(4) or ""
                return_type = match.group(5)
                
                # Parse parameters
                params = []
                for p in params_str.split(","):
                    p = p.strip()
                    if p and p != "self" and p != "cls":
                        if ":" in p:
                            p = p.split(":")[0].strip()
                        if "=" in p:
                            p = p.split("=")[0].strip()
                        if p:
                            params.append(p)
                
                # Find function end
                end_line = i + 1
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith(" " * (indent + 1)):
                        break
                    end_line = j + 1
                
                # Check if method
                is_method = False
                class_name = None
                for cls in classes:
                    if cls.line_start <= i + 1 <= cls.line_end:
                        is_method = True
                        class_name = cls.name
                        cls.methods.append(name)
                        break
                
                functions.append(FunctionDef(
                    name=name,
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=end_line,
                    parameters=params,
                    return_type=return_type.strip() if return_type else None,
                    is_async=is_async,
                    is_method=is_method,
                    class_name=class_name,
                ))
        
        return ParsedFile(
            file_path=file_path,
            language="python",
            functions=functions,
            classes=classes,
            imports=imports,
        )
    
    def _parse_javascript(self, content: str, file_path: str, language: str) -> ParsedFile:
        """Parse JavaScript/TypeScript source code."""
        functions: list[FunctionDef] = []
        classes: list[ClassDef] = []
        imports: list[ImportDef] = []
        exports: list[str] = []
        
        lines = content.split("\n")
        
        # Parse imports
        import_pattern = re.compile(
            r"import\s+(?:{([^}]+)}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]"
        )
        for i, line in enumerate(lines):
            for match in import_pattern.finditer(line):
                named = match.group(1)
                default = match.group(2)
                module = match.group(3)
                
                names = []
                if named:
                    names = [n.strip().split(" as ")[0] for n in named.split(",")]
                elif default:
                    names = [default]
                
                imports.append(ImportDef(
                    module=module,
                    names=names,
                    line=i + 1,
                    is_relative=module.startswith("."),
                ))
        
        # Parse exports
        export_pattern = re.compile(r"export\s+(?:default\s+)?(?:const|let|var|function|class|async function)\s+(\w+)")
        for i, line in enumerate(lines):
            match = export_pattern.search(line)
            if match:
                exports.append(match.group(1))
        
        # Parse classes
        class_pattern = re.compile(
            r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{"
        )
        for i, line in enumerate(lines):
            match = class_pattern.search(line)
            if match:
                name = match.group(1)
                base = match.group(2)
                
                classes.append(ClassDef(
                    name=name,
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,  # Simplified
                    bases=[base] if base else [],
                ))
        
        # Parse functions (simplified)
        func_patterns = [
            # Arrow functions
            re.compile(r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>"),
            # Regular functions
            re.compile(r"(?:export\s+)?(async\s+)?function\s+(\w+)\s*\("),
        ]
        
        for i, line in enumerate(lines):
            for pattern in func_patterns:
                match = pattern.search(line)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        # Arrow function pattern
                        name = groups[0]
                        is_async = bool(groups[1])
                    else:
                        # Regular function pattern
                        is_async = bool(groups[0])
                        name = groups[1]
                    
                    if name:
                        functions.append(FunctionDef(
                            name=name,
                            file_path=file_path,
                            line_start=i + 1,
                            line_end=i + 1,
                            is_async=is_async,
                        ))
                    break
        
        return ParsedFile(
            file_path=file_path,
            language=language,
            functions=functions,
            classes=classes,
            imports=imports,
            exports=exports,
        )
    
    def _parse_go(self, content: str, file_path: str) -> ParsedFile:
        """Parse Go source code."""
        functions: list[FunctionDef] = []
        imports: list[ImportDef] = []
        
        lines = content.split("\n")
        
        # Parse imports
        import_pattern = re.compile(r'"([^"]+)"')
        in_import_block = False
        
        for i, line in enumerate(lines):
            if "import (" in line:
                in_import_block = True
                continue
            if in_import_block and ")" in line:
                in_import_block = False
                continue
            if in_import_block or line.strip().startswith("import "):
                match = import_pattern.search(line)
                if match:
                    module = match.group(1)
                    imports.append(ImportDef(
                        module=module,
                        line=i + 1,
                    ))
        
        # Parse functions
        func_pattern = re.compile(
            r"^func\s+(?:\((\w+)\s+\*?(\w+)\)\s+)?(\w+)\s*\("
        )
        
        for i, line in enumerate(lines):
            match = func_pattern.match(line)
            if match:
                receiver_name = match.group(1)
                receiver_type = match.group(2)
                name = match.group(3)
                
                functions.append(FunctionDef(
                    name=name,
                    file_path=file_path,
                    line_start=i + 1,
                    line_end=i + 1,
                    is_method=bool(receiver_type),
                    class_name=receiver_type,
                ))
        
        return ParsedFile(
            file_path=file_path,
            language="go",
            functions=functions,
            imports=imports,
        )
    
    def build_dependency_graph(self, parsed_files: list[ParsedFile]) -> dict:
        """
        Build a module dependency graph from parsed files.
        
        Returns:
            Dictionary with nodes and edges for visualization
        """
        # Group files by directory/module
        modules: dict[str, list[str]] = {}
        
        for pf in parsed_files:
            parts = Path(pf.file_path).parts
            if len(parts) > 1:
                module = parts[0]
            else:
                module = "root"
            
            if module not in modules:
                modules[module] = []
            modules[module].append(pf.file_path)
        
        # Build edges from imports
        edges: list[dict] = []
        
        for pf in parsed_files:
            source_module = Path(pf.file_path).parts[0] if len(Path(pf.file_path).parts) > 1 else "root"
            
            for imp in pf.imports:
                if imp.is_relative:
                    continue  # Skip relative imports for now
                
                # Try to find target module
                target_module = imp.module.split("/")[0].split(".")[0]
                
                if target_module in modules:
                    edges.append({
                        "source": source_module,
                        "target": target_module,
                        "type": "imports",
                    })
        
        return {
            "nodes": list(modules.keys()),
            "edges": edges,
            "file_count": {m: len(files) for m, files in modules.items()},
        }
