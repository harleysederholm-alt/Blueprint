"""
Tree-sitter Based Code Parser

Provides accurate AST-based code analysis for multiple languages.
Replaces the regex-based parser with proper syntax tree parsing.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import os

logger = logging.getLogger(__name__)


@dataclass
class ParsedSymbol:
    """A parsed symbol (function, class, etc.)."""
    name: str
    type: str  # "function", "class", "method", "interface", "type"
    file_path: str
    line_start: int
    line_end: int
    signature: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parent: Optional[str] = None  # For nested classes/methods


@dataclass
class ParsedImport:
    """A parsed import statement."""
    module: str
    names: List[str]  # Imported names (empty for full module import)
    alias: Optional[str] = None
    file_path: str = ""
    line: int = 0
    is_relative: bool = False


@dataclass
class ParsedCall:
    """A parsed function/method call."""
    name: str
    object: Optional[str] = None  # For method calls
    file_path: str = ""
    line: int = 0
    is_method: bool = False


@dataclass
class ParsedFile:
    """Complete parsed representation of a source file."""
    file_path: str
    language: str
    symbols: List[ParsedSymbol] = field(default_factory=list)
    imports: List[ParsedImport] = field(default_factory=list)
    calls: List[ParsedCall] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def functions(self) -> List[ParsedSymbol]:
        return [s for s in self.symbols if s.type in ("function", "method")]
    
    @property
    def classes(self) -> List[ParsedSymbol]:
        return [s for s in self.symbols if s.type == "class"]


class TreeSitterParser:
    """
    AST-based code parser using Tree-sitter.
    
    Provides accurate extraction of:
    - Function and class definitions
    - Import statements  
    - Function calls (for dependency tracing)
    - Line-accurate positions for evidence anchoring
    """
    
    SUPPORTED_LANGUAGES = {
        ".py": "python",
        ".pyw": "python",
        ".ts": "typescript",
        ".mts": "typescript",
        ".cts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".go": "go",
    }
    
    def __init__(self):
        self._parsers: Dict[str, Any] = {}
        self._languages: Dict[str, Any] = {}
        self._initialized = False
        self._tree_sitter_available = False
        
        # Try to import tree-sitter
        try:
            from tree_sitter_languages import get_parser, get_language
            self._get_parser = get_parser
            self._get_language = get_language
            self._tree_sitter_available = True
            self._initialized = True
            logger.info("Tree-sitter initialized successfully")
        except ImportError:
            logger.warning("tree-sitter-languages not available, falling back to regex parser")
            self._tree_sitter_available = False
    
    @property
    def is_available(self) -> bool:
        """Check if Tree-sitter is available."""
        return self._tree_sitter_available
    
    def get_language_for_file(self, file_path: str) -> Optional[str]:
        """Get the language name for a file based on extension."""
        ext = os.path.splitext(file_path)[1].lower()
        return self.SUPPORTED_LANGUAGES.get(ext)
    
    def _get_parser_for_language(self, language: str) -> Optional[Any]:
        """Get or create a parser for a language."""
        if not self._tree_sitter_available:
            return None
            
        if language not in self._parsers:
            try:
                self._parsers[language] = self._get_parser(language)
                self._languages[language] = self._get_language(language)
            except Exception as e:
                logger.warning(f"Failed to load parser for {language}: {e}")
                return None
        
        return self._parsers.get(language)
    
    def parse_file(self, file_path: Path) -> ParsedFile:
        """
        Parse a source code file and extract structural information.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            ParsedFile with extracted symbols, imports, and calls
        """
        str_path = str(file_path)
        language = self.get_language_for_file(str_path)
        
        if not language:
            return ParsedFile(
                file_path=str_path,
                language="unknown",
                errors=["Unsupported file type"]
            )
        
        # Read file content
        try:
            content = file_path.read_bytes()
            content_str = content.decode("utf-8", errors="ignore")
        except Exception as e:
            return ParsedFile(
                file_path=str_path,
                language=language,
                errors=[f"Failed to read file: {e}"]
            )
        
        # Use Tree-sitter if available
        if self._tree_sitter_available:
            return self._parse_with_tree_sitter(str_path, language, content, content_str)
        else:
            # Fallback to regex parsing
            return self._parse_with_regex(str_path, language, content_str)
    
    def _parse_with_tree_sitter(
        self, 
        file_path: str, 
        language: str, 
        content: bytes,
        content_str: str
    ) -> ParsedFile:
        """Parse using Tree-sitter AST."""
        parser = self._get_parser_for_language(language)
        if not parser:
            return self._parse_with_regex(file_path, language, content_str)
        
        try:
            tree = parser.parse(content)
        except Exception as e:
            logger.warning(f"Tree-sitter parse failed for {file_path}: {e}")
            return self._parse_with_regex(file_path, language, content_str)
        
        result = ParsedFile(file_path=file_path, language=language)
        lines = content_str.split("\n")
        
        # Extract based on language
        if language == "python":
            self._extract_python(tree, result, lines, file_path)
        elif language in ("typescript", "tsx"):
            self._extract_typescript(tree, result, lines, file_path)
        elif language == "javascript":
            self._extract_javascript(tree, result, lines, file_path)
        elif language == "go":
            self._extract_go(tree, result, lines, file_path)
        
        return result
    
    def _get_node_text(self, node: Any, lines: List[str]) -> str:
        """Get the text content of a node."""
        try:
            start_line, start_col = node.start_point
            end_line, end_col = node.end_point
            
            if start_line == end_line:
                return lines[start_line][start_col:end_col]
            
            result = [lines[start_line][start_col:]]
            for i in range(start_line + 1, end_line):
                result.append(lines[i])
            result.append(lines[end_line][:end_col])
            
            return "\n".join(result)
        except:
            return node.text.decode("utf-8", errors="ignore") if hasattr(node, "text") else ""
    
    def _extract_python(
        self, 
        tree: Any, 
        result: ParsedFile, 
        lines: List[str],
        file_path: str
    ):
        """Extract Python symbols, imports, and calls."""
        def traverse(node: Any, parent_class: Optional[str] = None):
            # Imports
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        module = self._get_node_text(child, lines)
                        result.imports.append(ParsedImport(
                            module=module,
                            names=[],
                            file_path=file_path,
                            line=node.start_point[0] + 1
                        ))
            
            elif node.type == "import_from_statement":
                module = ""
                names = []
                for child in node.children:
                    if child.type == "dotted_name" and not names:
                        module = self._get_node_text(child, lines)
                    elif child.type == "dotted_name":
                        names.append(self._get_node_text(child, lines))
                    elif child.type == "aliased_import":
                        for sub in child.children:
                            if sub.type == "dotted_name":
                                names.append(self._get_node_text(sub, lines))
                                break
                
                result.imports.append(ParsedImport(
                    module=module,
                    names=names,
                    file_path=file_path,
                    line=node.start_point[0] + 1,
                    is_relative=module.startswith(".")
                ))
            
            # Function definitions
            elif node.type == "function_definition":
                name = ""
                for child in node.children:
                    if child.type == "identifier":
                        name = self._get_node_text(child, lines)
                        break
                
                sig_line = lines[node.start_point[0]] if node.start_point[0] < len(lines) else ""
                
                result.symbols.append(ParsedSymbol(
                    name=name,
                    type="method" if parent_class else "function",
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    signature=sig_line.strip(),
                    parent=parent_class
                ))
            
            # Class definitions
            elif node.type == "class_definition":
                name = ""
                for child in node.children:
                    if child.type == "identifier":
                        name = self._get_node_text(child, lines)
                        break
                
                result.symbols.append(ParsedSymbol(
                    name=name,
                    type="class",
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1
                ))
                
                # Traverse class body for methods
                for child in node.children:
                    if child.type == "block":
                        for sub in child.children:
                            traverse(sub, parent_class=name)
                return  # Don't recurse further
            
            # Function calls
            elif node.type == "call":
                func_node = None
                for child in node.children:
                    if child.type in ("identifier", "attribute"):
                        func_node = child
                        break
                
                if func_node:
                    if func_node.type == "identifier":
                        result.calls.append(ParsedCall(
                            name=self._get_node_text(func_node, lines),
                            file_path=file_path,
                            line=node.start_point[0] + 1
                        ))
                    elif func_node.type == "attribute":
                        obj = method = ""
                        for child in func_node.children:
                            if child.type == "identifier":
                                if not obj:
                                    obj = self._get_node_text(child, lines)
                                else:
                                    method = self._get_node_text(child, lines)
                        result.calls.append(ParsedCall(
                            name=method or obj,
                            object=obj if method else None,
                            file_path=file_path,
                            line=node.start_point[0] + 1,
                            is_method=bool(method)
                        ))
            
            # Recurse
            for child in node.children:
                traverse(child, parent_class)
        
        traverse(tree.root_node)
    
    def _extract_typescript(
        self, 
        tree: Any, 
        result: ParsedFile, 
        lines: List[str],
        file_path: str
    ):
        """Extract TypeScript/TSX symbols, imports, and calls."""
        def traverse(node: Any, parent_class: Optional[str] = None):
            # Imports
            if node.type == "import_statement":
                source = ""
                names = []
                for child in node.children:
                    if child.type == "string":
                        source = self._get_node_text(child, lines).strip("'\"")
                    elif child.type == "import_clause":
                        for sub in child.children:
                            if sub.type == "identifier":
                                names.append(self._get_node_text(sub, lines))
                            elif sub.type == "named_imports":
                                for spec in sub.children:
                                    if spec.type == "import_specifier":
                                        for s in spec.children:
                                            if s.type == "identifier":
                                                names.append(self._get_node_text(s, lines))
                                                break
                
                result.imports.append(ParsedImport(
                    module=source,
                    names=names,
                    file_path=file_path,
                    line=node.start_point[0] + 1
                ))
            
            # Function declarations
            elif node.type == "function_declaration":
                name = ""
                for child in node.children:
                    if child.type == "identifier":
                        name = self._get_node_text(child, lines)
                        break
                
                result.symbols.append(ParsedSymbol(
                    name=name,
                    type="function",
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1
                ))
            
            # Method definitions
            elif node.type == "method_definition":
                name = ""
                for child in node.children:
                    if child.type == "property_identifier":
                        name = self._get_node_text(child, lines)
                        break
                
                result.symbols.append(ParsedSymbol(
                    name=name,
                    type="method",
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    parent=parent_class
                ))
            
            # Class declarations
            elif node.type == "class_declaration":
                name = ""
                for child in node.children:
                    if child.type == "type_identifier":
                        name = self._get_node_text(child, lines)
                        break
                
                result.symbols.append(ParsedSymbol(
                    name=name,
                    type="class",
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1
                ))
                
                # Traverse class body
                for child in node.children:
                    if child.type == "class_body":
                        for sub in child.children:
                            traverse(sub, parent_class=name)
                return
            
            # Interface declarations
            elif node.type == "interface_declaration":
                name = ""
                for child in node.children:
                    if child.type == "type_identifier":
                        name = self._get_node_text(child, lines)
                        break
                
                result.symbols.append(ParsedSymbol(
                    name=name,
                    type="interface",
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1
                ))
            
            # Type alias
            elif node.type == "type_alias_declaration":
                name = ""
                for child in node.children:
                    if child.type == "type_identifier":
                        name = self._get_node_text(child, lines)
                        break
                
                result.symbols.append(ParsedSymbol(
                    name=name,
                    type="type",
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1
                ))
            
            # Arrow functions in variable declarations
            elif node.type == "lexical_declaration" or node.type == "variable_declaration":
                for child in node.children:
                    if child.type == "variable_declarator":
                        name = ""
                        has_arrow = False
                        for sub in child.children:
                            if sub.type == "identifier":
                                name = self._get_node_text(sub, lines)
                            elif sub.type == "arrow_function":
                                has_arrow = True
                        
                        if name and has_arrow:
                            result.symbols.append(ParsedSymbol(
                                name=name,
                                type="function",
                                file_path=file_path,
                                line_start=node.start_point[0] + 1,
                                line_end=node.end_point[0] + 1
                            ))
            
            # Function calls
            elif node.type == "call_expression":
                func_node = None
                for child in node.children:
                    if child.type in ("identifier", "member_expression"):
                        func_node = child
                        break
                
                if func_node:
                    if func_node.type == "identifier":
                        result.calls.append(ParsedCall(
                            name=self._get_node_text(func_node, lines),
                            file_path=file_path,
                            line=node.start_point[0] + 1
                        ))
                    elif func_node.type == "member_expression":
                        obj = method = ""
                        for child in func_node.children:
                            if child.type == "identifier":
                                obj = self._get_node_text(child, lines)
                            elif child.type == "property_identifier":
                                method = self._get_node_text(child, lines)
                        result.calls.append(ParsedCall(
                            name=method or obj,
                            object=obj if method else None,
                            file_path=file_path,
                            line=node.start_point[0] + 1,
                            is_method=bool(method)
                        ))
            
            # Recurse
            for child in node.children:
                traverse(child, parent_class)
        
        traverse(tree.root_node)
    
    def _extract_javascript(
        self, 
        tree: Any, 
        result: ParsedFile, 
        lines: List[str],
        file_path: str
    ):
        """Extract JavaScript symbols (reuses TypeScript extraction)."""
        self._extract_typescript(tree, result, lines, file_path)
    
    def _extract_go(
        self, 
        tree: Any, 
        result: ParsedFile, 
        lines: List[str],
        file_path: str
    ):
        """Extract Go symbols, imports, and calls."""
        def traverse(node: Any):
            # Imports
            if node.type == "import_declaration":
                for child in node.children:
                    if child.type == "import_spec":
                        path = ""
                        alias = None
                        for sub in child.children:
                            if sub.type == "interpreted_string_literal":
                                path = self._get_node_text(sub, lines).strip('"')
                            elif sub.type == "package_identifier":
                                alias = self._get_node_text(sub, lines)
                        
                        if path:
                            result.imports.append(ParsedImport(
                                module=path,
                                names=[],
                                alias=alias,
                                file_path=file_path,
                                line=node.start_point[0] + 1
                            ))
                    elif child.type == "import_spec_list":
                        for spec in child.children:
                            if spec.type == "import_spec":
                                path = ""
                                alias = None
                                for sub in spec.children:
                                    if sub.type == "interpreted_string_literal":
                                        path = self._get_node_text(sub, lines).strip('"')
                                    elif sub.type == "package_identifier":
                                        alias = self._get_node_text(sub, lines)
                                
                                if path:
                                    result.imports.append(ParsedImport(
                                        module=path,
                                        names=[],
                                        alias=alias,
                                        file_path=file_path,
                                        line=spec.start_point[0] + 1
                                    ))
            
            # Function declarations
            elif node.type == "function_declaration":
                name = ""
                for child in node.children:
                    if child.type == "identifier":
                        name = self._get_node_text(child, lines)
                        break
                
                result.symbols.append(ParsedSymbol(
                    name=name,
                    type="function",
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1
                ))
            
            # Method declarations
            elif node.type == "method_declaration":
                name = ""
                receiver = ""
                for child in node.children:
                    if child.type == "field_identifier":
                        name = self._get_node_text(child, lines)
                    elif child.type == "parameter_list" and not receiver:
                        # First param list is receiver
                        for sub in child.children:
                            if sub.type == "parameter_declaration":
                                for s in sub.children:
                                    if s.type == "type_identifier":
                                        receiver = self._get_node_text(s, lines)
                                        break
                
                result.symbols.append(ParsedSymbol(
                    name=name,
                    type="method",
                    file_path=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    parent=receiver
                ))
            
            # Type declarations (structs, interfaces)
            elif node.type == "type_declaration":
                for child in node.children:
                    if child.type == "type_spec":
                        name = ""
                        type_kind = "type"
                        for sub in child.children:
                            if sub.type == "type_identifier":
                                name = self._get_node_text(sub, lines)
                            elif sub.type == "struct_type":
                                type_kind = "class"  # Treat struct as class
                            elif sub.type == "interface_type":
                                type_kind = "interface"
                        
                        if name:
                            result.symbols.append(ParsedSymbol(
                                name=name,
                                type=type_kind,
                                file_path=file_path,
                                line_start=node.start_point[0] + 1,
                                line_end=node.end_point[0] + 1
                            ))
            
            # Function calls
            elif node.type == "call_expression":
                func_node = None
                for child in node.children:
                    if child.type in ("identifier", "selector_expression"):
                        func_node = child
                        break
                
                if func_node:
                    if func_node.type == "identifier":
                        result.calls.append(ParsedCall(
                            name=self._get_node_text(func_node, lines),
                            file_path=file_path,
                            line=node.start_point[0] + 1
                        ))
                    elif func_node.type == "selector_expression":
                        obj = method = ""
                        for child in func_node.children:
                            if child.type == "identifier":
                                obj = self._get_node_text(child, lines)
                            elif child.type == "field_identifier":
                                method = self._get_node_text(child, lines)
                        result.calls.append(ParsedCall(
                            name=method or obj,
                            object=obj if method else None,
                            file_path=file_path,
                            line=node.start_point[0] + 1,
                            is_method=bool(method)
                        ))
            
            # Recurse
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
    
    def _parse_with_regex(
        self, 
        file_path: str, 
        language: str,
        content: str
    ) -> ParsedFile:
        """Fallback regex-based parsing when Tree-sitter is unavailable."""
        import re
        
        result = ParsedFile(file_path=file_path, language=language)
        lines = content.split("\n")
        
        if language == "python":
            # Python imports
            import_pattern = r'^(?:from\s+([\w.]+)\s+)?import\s+(.+)$'
            for i, line in enumerate(lines):
                match = re.match(import_pattern, line.strip())
                if match:
                    module = match.group(1) or match.group(2).split(",")[0].strip()
                    names = []
                    if match.group(1):
                        names = [n.strip().split(" as ")[0] for n in match.group(2).split(",")]
                    result.imports.append(ParsedImport(
                        module=module,
                        names=names,
                        file_path=file_path,
                        line=i + 1
                    ))
            
            # Python functions
            func_pattern = r'^(\s*)def\s+(\w+)\s*\('
            for i, line in enumerate(lines):
                match = re.match(func_pattern, line)
                if match:
                    indent = len(match.group(1))
                    name = match.group(2)
                    result.symbols.append(ParsedSymbol(
                        name=name,
                        type="function" if indent == 0 else "method",
                        file_path=file_path,
                        line_start=i + 1,
                        line_end=i + 1,
                        signature=line.strip()
                    ))
            
            # Python classes
            class_pattern = r'^class\s+(\w+)'
            for i, line in enumerate(lines):
                match = re.match(class_pattern, line.strip())
                if match:
                    result.symbols.append(ParsedSymbol(
                        name=match.group(1),
                        type="class",
                        file_path=file_path,
                        line_start=i + 1,
                        line_end=i + 1
                    ))
        
        elif language in ("typescript", "javascript", "tsx"):
            # JS/TS imports
            import_pattern = r"^import\s+.*?from\s+['\"](.+?)['\"]"
            for i, line in enumerate(lines):
                match = re.search(import_pattern, line)
                if match:
                    result.imports.append(ParsedImport(
                        module=match.group(1),
                        names=[],
                        file_path=file_path,
                        line=i + 1
                    ))
            
            # JS/TS functions
            func_patterns = [
                r'(?:export\s+)?(?:async\s+)?function\s+(\w+)',
                r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(',
                r'(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>',
            ]
            for i, line in enumerate(lines):
                for pattern in func_patterns:
                    match = re.search(pattern, line)
                    if match:
                        result.symbols.append(ParsedSymbol(
                            name=match.group(1),
                            type="function",
                            file_path=file_path,
                            line_start=i + 1,
                            line_end=i + 1
                        ))
                        break
            
            # JS/TS classes
            class_pattern = r'(?:export\s+)?class\s+(\w+)'
            for i, line in enumerate(lines):
                match = re.search(class_pattern, line)
                if match:
                    result.symbols.append(ParsedSymbol(
                        name=match.group(1),
                        type="class",
                        file_path=file_path,
                        line_start=i + 1,
                        line_end=i + 1
                    ))
        
        elif language == "go":
            # Go imports
            import_pattern = r'"([^"]+)"'
            in_import = False
            for i, line in enumerate(lines):
                if "import (" in line:
                    in_import = True
                elif in_import and ")" in line:
                    in_import = False
                elif in_import or "import " in line:
                    match = re.search(import_pattern, line)
                    if match:
                        result.imports.append(ParsedImport(
                            module=match.group(1),
                            names=[],
                            file_path=file_path,
                            line=i + 1
                        ))
            
            # Go functions
            func_pattern = r'^func\s+(?:\([^)]+\)\s*)?(\w+)\s*\('
            for i, line in enumerate(lines):
                match = re.match(func_pattern, line)
                if match:
                    result.symbols.append(ParsedSymbol(
                        name=match.group(1),
                        type="function",
                        file_path=file_path,
                        line_start=i + 1,
                        line_end=i + 1
                    ))
            
            # Go types
            type_pattern = r'^type\s+(\w+)\s+(struct|interface)'
            for i, line in enumerate(lines):
                match = re.match(type_pattern, line)
                if match:
                    result.symbols.append(ParsedSymbol(
                        name=match.group(1),
                        type="class" if match.group(2) == "struct" else "interface",
                        file_path=file_path,
                        line_start=i + 1,
                        line_end=i + 1
                    ))
        
        return result


# Singleton instance
_parser_instance: Optional[TreeSitterParser] = None


def get_parser() -> TreeSitterParser:
    """Get the singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = TreeSitterParser()
    return _parser_instance
