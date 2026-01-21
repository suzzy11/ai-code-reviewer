"""
Enhanced Python Parser for AI Code Reviewer.

Provides comprehensive AST-based code analysis including:
- Functions (regular, async, nested)
- Classes (with inheritance, attributes, methods)
- Module-level analysis (docstrings, imports)
- Decorators and type annotations
- Robust error handling
"""

import ast
import os
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DocstringInfo:
    """Information about a docstring."""
    exists: bool = False
    content: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    style: str = "unknown"  # google, numpy, rest, unknown

    @staticmethod
    def detect_style(content: str) -> str:
        """Detect docstring style from content."""
        if not content:
            return "unknown"
        
        # Google style: Uses "Args:", "Returns:", etc.
        if any(section in content for section in ["Args:", "Returns:", "Raises:", "Yields:"]):
            return "google"
        
        # NumPy style: Uses "Parameters\n----------"
        if "Parameters\n" in content or "Returns\n" in content:
            return "numpy"
        
        # reST style: Uses ":param", ":returns:", etc.
        if any(directive in content for directive in [":param", ":returns:", ":rtype:", ":raises:"]):
            return "rest"
        
        return "unknown"


@dataclass
class ParseError:
    """Represents a parsing error."""
    file_path: str
    error_type: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None


@dataclass
class ParseResult:
    """Result of parsing a Python file."""
    success: bool
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    module_docstring: Optional[DocstringInfo] = None
    errors: List[ParseError] = field(default_factory=list)
    file_path: str = ""
    raw_metrics: Dict[str, int] = field(default_factory=dict)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_annotation(node) -> Optional[str]:
    """Extract string representation of type annotation."""
    if node is None:
        return None
    if hasattr(node, 'annotation') and node.annotation:
        try:
            return ast.unparse(node.annotation)
        except Exception:
            return str(node.annotation)
    return None


def get_return_annotation(node: ast.FunctionDef) -> Optional[str]:
    """Extract return type annotation from a function."""
    if node.returns:
        try:
            return ast.unparse(node.returns)
        except Exception:
            return str(node.returns)
    return None


def get_decorators(node) -> List[Dict[str, Any]]:
    """Extract decorator information from a function or class."""
    decorators = []
    for dec in getattr(node, 'decorator_list', []):
        dec_info = {"name": None, "args": []}
        
        if isinstance(dec, ast.Name):
            dec_info["name"] = dec.id
        elif isinstance(dec, ast.Attribute):
            dec_info["name"] = ast.unparse(dec)
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name):
                dec_info["name"] = dec.func.id
            elif isinstance(dec.func, ast.Attribute):
                dec_info["name"] = ast.unparse(dec.func)
            # Extract arguments
            dec_info["args"] = [ast.unparse(arg) for arg in dec.args]
        
        if dec_info["name"]:
            decorators.append(dec_info)
    
    return decorators


def get_base_classes(node: ast.ClassDef) -> List[str]:
    """Extract base class names from a class definition."""
    bases = []
    for base in node.bases:
        try:
            bases.append(ast.unparse(base))
        except Exception:
            bases.append(str(base))
    return bases


def get_class_attributes(node: ast.ClassDef) -> List[Dict[str, Any]]:
    """Extract class-level attributes (not instance attributes)."""
    attributes = []
    
    for item in node.body:
        # Class-level assignments (class attributes)
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    attr_info = {
                        "name": target.id,
                        "type": None,
                        "line": item.lineno,
                        "is_class_attr": True
                    }
                    # Try to infer type from value
                    if isinstance(item.value, ast.Constant):
                        attr_info["type"] = type(item.value.value).__name__
                    attributes.append(attr_info)
        
        # Annotated assignments (Python 3.6+)
        elif isinstance(item, ast.AnnAssign):
            if isinstance(item.target, ast.Name):
                attr_info = {
                    "name": item.target.id,
                    "type": ast.unparse(item.annotation) if item.annotation else None,
                    "line": item.lineno,
                    "is_class_attr": True
                }
                attributes.append(attr_info)
    
    return attributes


def analyze_function_body(node: ast.FunctionDef) -> Dict[str, Any]:
    """
    Analyze function body for returns, yields, raises, and complexity.
    """
    metadata = {
        "returns_value": False,
        "return_type": get_return_annotation(node),
        "is_generator": False,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "raised_exceptions": set(),
        "complexity": 1,
        "nested_functions": [],
        "local_variables": set()
    }
    
    # Direct children analysis (not walking into nested functions)
    for child in ast.walk(node):
        # Skip nested function definitions for some checks
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child != node:
            metadata["nested_functions"].append(child.name)
            continue
        
        # 1. Return Value Detection
        if isinstance(child, ast.Return) and child.value is not None:
            # Ignore 'return None'
            if not (isinstance(child.value, ast.Constant) and child.value.value is None):
                metadata["returns_value"] = True

        # 2. Generator Detection
        if isinstance(child, (ast.Yield, ast.YieldFrom)):
            metadata["is_generator"] = True

        # 3. Exception Detection
        if isinstance(child, ast.Raise):
            if isinstance(child.exc, ast.Call) and isinstance(child.exc.func, ast.Name):
                metadata["raised_exceptions"].add(child.exc.func.id)
            elif isinstance(child.exc, ast.Name):
                metadata["raised_exceptions"].add(child.exc.id)

        # 4. Complexity Counting (McCabe)
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, 
                              ast.ExceptHandler, ast.With, ast.AsyncWith, 
                              ast.BoolOp, ast.IfExp)):  # IfExp = Ternary
             metadata["complexity"] += 1
        
        # 5. Local variable detection
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    metadata["local_variables"].add(target.id)
             
    metadata["raised_exceptions"] = list(metadata["raised_exceptions"])
    metadata["local_variables"] = list(metadata["local_variables"])
    return metadata


def get_docstring_info(node) -> DocstringInfo:
    """Extract comprehensive docstring information from a node."""
    docstring = ast.get_docstring(node)
    
    if not docstring:
        return DocstringInfo(exists=False)
    
    # Find the docstring node to get line numbers
    line_start = None
    line_end = None
    
    if node.body and isinstance(node.body[0], ast.Expr):
        expr = node.body[0]
        if isinstance(expr.value, ast.Constant) and isinstance(expr.value.value, str):
            line_start = expr.lineno
            line_end = getattr(expr, 'end_lineno', expr.lineno)
    
    return DocstringInfo(
        exists=True,
        content=docstring,
        line_start=line_start,
        line_end=line_end,
        style=DocstringInfo.detect_style(docstring)
    )


def calculate_raw_metrics(content: str) -> Dict[str, int]:
    """Calculate raw code metrics (LOC, SLOC, comments, blank lines)."""
    lines = content.split('\n')
    
    total_loc = len(lines)
    blank_lines = sum(1 for line in lines if not line.strip())
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    
    # SLOC = total - blank - pure comments
    sloc = total_loc - blank_lines - comment_lines
    
    return {
        "total_loc": total_loc,
        "sloc": sloc,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines
    }


# ============================================================================
# MAIN PARSER
# ============================================================================

def parse_python_file(file_path: str) -> Tuple[List, List, List]:
    """
    Parse a Python file and extract functions, classes, and imports.
    
    This is the legacy API for backward compatibility.
    Returns: (functions, classes, imports) tuple
    """
    result = parse_python_file_enhanced(file_path)
    
    if not result.success:
        # Return empty on failure for backward compatibility
        return [], [], []
    
    return result.functions, result.classes, result.imports


def parse_python_file_enhanced(file_path: str) -> ParseResult:
    """
    Enhanced Python file parser with comprehensive analysis.
    
    Args:
        file_path: Path to the Python file to parse.
    
    Returns:
        ParseResult with functions, classes, imports, module docstring, and errors.
    """
    result = ParseResult(success=False, file_path=file_path)
    
    # 1. Read file with encoding fallback
    content = None
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                content = file.read()
            break
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            result.errors.append(ParseError(
                file_path=file_path,
                error_type="FileNotFoundError",
                message=f"File not found: {file_path}"
            ))
            return result
        except PermissionError:
            result.errors.append(ParseError(
                file_path=file_path,
                error_type="PermissionError",
                message=f"Permission denied: {file_path}"
            ))
            return result
    
    if content is None:
        result.errors.append(ParseError(
            file_path=file_path,
            error_type="EncodingError",
            message="Could not decode file with any supported encoding"
        ))
        return result
    
    # Handle empty files
    if not content.strip():
        result.success = True
        result.raw_metrics = calculate_raw_metrics(content)
        return result
    
    # 2. Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        result.errors.append(ParseError(
            file_path=file_path,
            error_type="SyntaxError",
            message=str(e.msg) if e.msg else "Syntax error in file",
            line=e.lineno,
            column=e.offset
        ))
        return result
    except Exception as e:
        result.errors.append(ParseError(
            file_path=file_path,
            error_type=type(e).__name__,
            message=str(e)
        ))
        return result
    
    # 3. Extract raw metrics
    result.raw_metrics = calculate_raw_metrics(content)
    
    # 4. Extract module-level docstring
    result.module_docstring = get_docstring_info(tree)
    
    # 5. Visit all nodes
    functions = []
    classes = []
    imports = []
    
    def visit_nodes(node, parent_class=None, nesting_level=0):
        """Recursively visit AST nodes."""
        
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring_info = get_docstring_info(node)
            meta = analyze_function_body(node)
            decorators = get_decorators(node)
            
            # Extract Parameters with defaults
            args_list = []
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            
            for idx, arg in enumerate(node.args.args):
                if arg.arg == 'self' or arg.arg == 'cls':
                    continue
                
                default_value = None
                default_idx = idx - defaults_offset
                if default_idx >= 0 and default_idx < len(node.args.defaults):
                    try:
                        default_value = ast.unparse(node.args.defaults[default_idx])
                    except Exception:
                        default_value = "<default>"
                
                args_list.append({
                    "name": arg.arg,
                    "type": get_annotation(arg),
                    "default": default_value
                })
            
            # Add *args and **kwargs
            if node.args.vararg:
                args_list.append({
                    "name": f"*{node.args.vararg.arg}",
                    "type": get_annotation(node.args.vararg),
                    "default": None
                })
            if node.args.kwarg:
                args_list.append({
                    "name": f"**{node.args.kwarg.arg}",
                    "type": get_annotation(node.args.kwarg),
                    "default": None
                })
            
            # Determine method type
            method_type = "instance"
            is_property = False
            for dec in decorators:
                if dec["name"] == "staticmethod":
                    method_type = "static"
                elif dec["name"] == "classmethod":
                    method_type = "class"
                elif dec["name"] == "property":
                    is_property = True
            
            end_lineno = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            loc = end_lineno - node.lineno + 1

            functions.append({
                "name": node.name,
                "parent": parent_class,
                "lineno": node.lineno,
                "end_lineno": end_lineno,
                "loc": loc,
                "docstring": docstring_info.content,
                "docstring_info": {
                    "exists": docstring_info.exists,
                    "style": docstring_info.style,
                    "line_start": docstring_info.line_start,
                    "line_end": docstring_info.line_end
                },
                "args": args_list,
                "return_type": meta["return_type"],
                "returns_value": meta["returns_value"],
                "is_generator": meta["is_generator"],
                "is_async": meta["is_async"],
                "raises": meta["raised_exceptions"],
                "complexity": meta["complexity"],
                "is_method": parent_class is not None,
                "method_type": method_type if parent_class else None,
                "is_property": is_property,
                "decorators": decorators,
                "nested_functions": meta["nested_functions"],
                "nesting_level": nesting_level
            })
            
            # Visit nested functions
            for item in node.body:
                visit_nodes(item, parent_class=parent_class, nesting_level=nesting_level + 1)
            
        elif isinstance(node, ast.ClassDef):
            docstring_info = get_docstring_info(node)
            decorators = get_decorators(node)
            base_classes = get_base_classes(node)
            attributes = get_class_attributes(node)
            
            end_lineno = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            
            classes.append({
                "name": node.name,
                "docstring": docstring_info.content,
                "docstring_info": {
                    "exists": docstring_info.exists,
                    "style": docstring_info.style,
                    "line_start": docstring_info.line_start,
                    "line_end": docstring_info.line_end
                },
                "lineno": node.lineno,
                "end_lineno": end_lineno,
                "loc": end_lineno - node.lineno + 1,
                "bases": base_classes,
                "decorators": decorators,
                "attributes": attributes,
                "method_count": sum(1 for item in node.body 
                                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
            })
            
            # Visit methods inside class
            for item in node.body:
                visit_nodes(item, parent_class=node.name, nesting_level=0)
                
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)
                
        elif isinstance(node, ast.Module):
            for item in node.body:
                visit_nodes(item, nesting_level=0)
    
    visit_nodes(tree)
    
    result.functions = functions
    result.classes = classes
    result.imports = imports
    result.success = True
    
    return result


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_undocumented_items(result: ParseResult) -> Dict[str, List]:
    """Get lists of undocumented functions and classes."""
    undocumented_functions = [
        f for f in result.functions 
        if not f.get("docstring_info", {}).get("exists", False)
    ]
    undocumented_classes = [
        c for c in result.classes 
        if not c.get("docstring_info", {}).get("exists", False)
    ]
    
    return {
        "functions": undocumented_functions,
        "classes": undocumented_classes,
        "module_missing": not result.module_docstring or not result.module_docstring.exists
    }


def calculate_documentation_coverage(result: ParseResult) -> Dict[str, float]:
    """Calculate documentation coverage percentages."""
    total_functions = len(result.functions)
    total_classes = len(result.classes)
    
    documented_functions = sum(
        1 for f in result.functions 
        if f.get("docstring_info", {}).get("exists", False)
    )
    documented_classes = sum(
        1 for c in result.classes 
        if c.get("docstring_info", {}).get("exists", False)
    )
    
    has_module_doc = 1 if (result.module_docstring and result.module_docstring.exists) else 0
    
    total_items = total_functions + total_classes + 1  # +1 for module
    documented_items = documented_functions + documented_classes + has_module_doc
    
    return {
        "overall": (documented_items / total_items * 100) if total_items > 0 else 100.0,
        "functions": (documented_functions / total_functions * 100) if total_functions > 0 else 100.0,
        "classes": (documented_classes / total_classes * 100) if total_classes > 0 else 100.0,
        "module": 100.0 if has_module_doc else 0.0
    }
