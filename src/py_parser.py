import ast
from typing import List, Dict, Any, Optional

def get_annotation(arg):
    """Extract string representation of type annotation."""
    if arg.annotation:
        return ast.unparse(arg.annotation)
    return None

def analyze_function_body(node: ast.FunctionDef) -> Dict[str, Any]:
    """
    Analyzes function body for returns, yields, raises, and complexity.
    """
    metadata = {
        "returns_value": False,
        "is_generator": False,
        "raised_exceptions": set(),
        "complexity": 1
    }
    
    for child in ast.walk(node):
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

        # 4. Complexity Counting
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, 
                              ast.ExceptHandler, ast.With, ast.AsyncWith, 
                              ast.BoolOp, ast.IfExp)): # IfExp = Ternary
             metadata["complexity"] += 1
             
    metadata["raised_exceptions"] = list(metadata["raised_exceptions"])
    return metadata

def parse_python_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read())

    functions = []
    classes = []
    imports = []

    def visit_nodes(node, parent_class=None):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            meta = analyze_function_body(node)
            
            # Extract Parameters
            args_list = []
            for arg in node.args.args:
                if arg.arg == 'self': continue
                args_list.append({
                    "name": arg.arg,
                    "type": get_annotation(arg),
                    "default": None # Simplified for now
                })
            
            # Helper to check method type
            method_type = "instance"
            if len(node.decorator_list) > 0:
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        if dec.id == 'staticmethod': method_type = 'static'
                        elif dec.id == 'classmethod': method_type = 'class'
            
            end_lineno = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            loc = end_lineno - node.lineno + 1

            functions.append({
                "name": node.name,
                "parent": parent_class,
                "lineno": node.lineno,
                "end_lineno": end_lineno,
                "loc": loc,
                "docstring": docstring,
                "args": args_list,
                "returns_value": meta["returns_value"],
                "is_generator": meta["is_generator"],
                "raises": meta["raised_exceptions"],
                "complexity": meta["complexity"],
                "is_method": parent_class is not None,
                "method_type": method_type if parent_class else None
            })
            
        elif isinstance(node, ast.ClassDef):
            end_lineno = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
            classes.append({
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "lineno": node.lineno,
                "end_lineno": end_lineno,
                "loc": end_lineno - node.lineno + 1
            })
            # Visit methods inside class
            for item in node.body:
                visit_nodes(item, parent_class=node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.Module):
            for item in node.body:
                visit_nodes(item)

    visit_nodes(tree)
    return functions, classes, imports
