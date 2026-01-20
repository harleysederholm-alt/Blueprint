"""
Language Configuration - Tree-sitter Queries for Different Languages

Provides language-specific S-expression queries for extracting:
- Imports/dependencies
- Function definitions
- Class definitions
- Function calls
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class LanguageConfig:
    """Configuration for a specific programming language."""
    name: str
    extensions: List[str]
    
    # Tree-sitter queries
    import_query: str
    function_query: str
    class_query: str
    call_query: str
    
    # Optional: Additional queries
    decorator_query: Optional[str] = None
    interface_query: Optional[str] = None
    type_query: Optional[str] = None


# Python configuration
PYTHON_CONFIG = LanguageConfig(
    name="python",
    extensions=[".py", ".pyw"],
    import_query="""
        (import_statement
            name: (dotted_name) @import.name) @import
        
        (import_from_statement
            module_name: (dotted_name)? @import.from
            name: (dotted_name) @import.name) @import
        
        (import_from_statement
            module_name: (dotted_name)? @import.from
            name: (aliased_import
                name: (dotted_name) @import.name
                alias: (identifier) @import.alias)) @import
    """,
    function_query="""
        (function_definition
            name: (identifier) @function.name
            parameters: (parameters) @function.params
            body: (block) @function.body) @function
        
        (decorated_definition
            decorator: (decorator) @function.decorator
            definition: (function_definition
                name: (identifier) @function.name)) @decorated_function
    """,
    class_query="""
        (class_definition
            name: (identifier) @class.name
            superclasses: (argument_list)? @class.bases
            body: (block) @class.body) @class
        
        (decorated_definition
            decorator: (decorator) @class.decorator
            definition: (class_definition
                name: (identifier) @class.name)) @decorated_class
    """,
    call_query="""
        (call
            function: (identifier) @call.name
            arguments: (argument_list) @call.args) @call
        
        (call
            function: (attribute
                object: (_) @call.object
                attribute: (identifier) @call.method)
            arguments: (argument_list) @call.args) @call.method_call
    """,
    decorator_query="""
        (decorator
            (identifier) @decorator.name)
        (decorator
            (call
                function: (identifier) @decorator.name
                arguments: (argument_list) @decorator.args))
    """,
)


# TypeScript configuration
TYPESCRIPT_CONFIG = LanguageConfig(
    name="typescript",
    extensions=[".ts", ".mts", ".cts"],
    import_query="""
        (import_statement
            source: (string) @import.source) @import
        
        (import_clause
            (named_imports
                (import_specifier
                    name: (identifier) @import.name
                    alias: (identifier)? @import.alias))) @import.named
        
        (import_clause
            (identifier) @import.default) @import.default_clause
        
        (import_clause
            (namespace_import
                (identifier) @import.namespace)) @import.namespace_clause
    """,
    function_query="""
        (function_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (statement_block) @function.body) @function
        
        (arrow_function
            parameters: (formal_parameters) @function.params
            body: (_) @function.body) @arrow_function
        
        (method_definition
            name: (property_identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (statement_block) @function.body) @method
        
        (export_statement
            declaration: (function_declaration
                name: (identifier) @function.name)) @exported_function
    """,
    class_query="""
        (class_declaration
            name: (type_identifier) @class.name
            body: (class_body) @class.body) @class
        
        (class_declaration
            name: (type_identifier) @class.name
            (class_heritage
                (extends_clause
                    value: (_) @class.extends))) @class.with_extends
        
        (export_statement
            declaration: (class_declaration
                name: (type_identifier) @class.name)) @exported_class
    """,
    call_query="""
        (call_expression
            function: (identifier) @call.name
            arguments: (arguments) @call.args) @call
        
        (call_expression
            function: (member_expression
                object: (_) @call.object
                property: (property_identifier) @call.method)
            arguments: (arguments) @call.args) @call.method_call
        
        (new_expression
            constructor: (identifier) @call.constructor
            arguments: (arguments) @call.args) @new_call
    """,
    interface_query="""
        (interface_declaration
            name: (type_identifier) @interface.name
            body: (object_type) @interface.body) @interface
    """,
    type_query="""
        (type_alias_declaration
            name: (type_identifier) @type.name
            value: (_) @type.value) @type_alias
    """,
)


# JavaScript configuration (similar to TypeScript but simpler)
JAVASCRIPT_CONFIG = LanguageConfig(
    name="javascript",
    extensions=[".js", ".jsx", ".mjs", ".cjs"],
    import_query="""
        (import_statement
            source: (string) @import.source) @import
        
        (call_expression
            function: (identifier) @require
            arguments: (arguments
                (string) @import.source)) @require_call
            (#eq? @require "require")
    """,
    function_query="""
        (function_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (statement_block) @function.body) @function
        
        (arrow_function
            parameters: (formal_parameters) @function.params
            body: (_) @function.body) @arrow_function
        
        (method_definition
            name: (property_identifier) @function.name
            parameters: (formal_parameters) @function.params) @method
        
        (variable_declarator
            name: (identifier) @function.name
            value: (arrow_function)) @arrow_var
    """,
    class_query="""
        (class_declaration
            name: (identifier) @class.name
            body: (class_body) @class.body) @class
        
        (class_declaration
            (class_heritage
                (identifier) @class.extends)) @class.with_extends
    """,
    call_query="""
        (call_expression
            function: (identifier) @call.name
            arguments: (arguments) @call.args) @call
        
        (call_expression
            function: (member_expression
                object: (_) @call.object
                property: (property_identifier) @call.method)) @call.method_call
    """,
)


# Go configuration
GO_CONFIG = LanguageConfig(
    name="go",
    extensions=[".go"],
    import_query="""
        (import_declaration
            (import_spec
                path: (interpreted_string_literal) @import.path
                name: (package_identifier)? @import.alias)) @import
        
        (import_declaration
            (import_spec_list
                (import_spec
                    path: (interpreted_string_literal) @import.path
                    name: (package_identifier)? @import.alias))) @import.multi
    """,
    function_query="""
        (function_declaration
            name: (identifier) @function.name
            parameters: (parameter_list) @function.params
            body: (block) @function.body) @function
        
        (method_declaration
            receiver: (parameter_list) @method.receiver
            name: (field_identifier) @function.name
            parameters: (parameter_list) @function.params
            body: (block) @function.body) @method
    """,
    class_query="""
        (type_declaration
            (type_spec
                name: (type_identifier) @type.name
                type: (struct_type
                    (field_declaration_list) @type.fields))) @struct
        
        (type_declaration
            (type_spec
                name: (type_identifier) @type.name
                type: (interface_type
                    (method_spec_list)? @type.methods))) @interface
    """,
    call_query="""
        (call_expression
            function: (identifier) @call.name
            arguments: (argument_list) @call.args) @call
        
        (call_expression
            function: (selector_expression
                operand: (_) @call.object
                field: (field_identifier) @call.method)
            arguments: (argument_list) @call.args) @call.method_call
    """,
)


# TSX configuration (extends TypeScript)
TSX_CONFIG = LanguageConfig(
    name="tsx",
    extensions=[".tsx"],
    import_query=TYPESCRIPT_CONFIG.import_query,
    function_query=TYPESCRIPT_CONFIG.function_query + """
        (jsx_element
            open_tag: (jsx_opening_element
                name: (identifier) @jsx.component)) @jsx
    """,
    class_query=TYPESCRIPT_CONFIG.class_query,
    call_query=TYPESCRIPT_CONFIG.call_query,
    interface_query=TYPESCRIPT_CONFIG.interface_query,
    type_query=TYPESCRIPT_CONFIG.type_query,
)


# Registry of all language configs
LANGUAGE_CONFIGS: Dict[str, LanguageConfig] = {
    "python": PYTHON_CONFIG,
    "typescript": TYPESCRIPT_CONFIG,
    "javascript": JAVASCRIPT_CONFIG,
    "tsx": TSX_CONFIG,
    "go": GO_CONFIG,
}


def get_language_for_file(file_path: str) -> Optional[str]:
    """Get the language name for a file based on its extension."""
    import os
    ext = os.path.splitext(file_path)[1].lower()
    
    for lang_name, config in LANGUAGE_CONFIGS.items():
        if ext in config.extensions:
            return lang_name
    
    return None


def get_config_for_language(language: str) -> Optional[LanguageConfig]:
    """Get the configuration for a specific language."""
    return LANGUAGE_CONFIGS.get(language)


def get_config_for_file(file_path: str) -> Optional[LanguageConfig]:
    """Get the configuration for a file based on its extension."""
    language = get_language_for_file(file_path)
    if language:
        return get_config_for_language(language)
    return None
