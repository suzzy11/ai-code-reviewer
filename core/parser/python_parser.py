import ast

def extract_functions_from_code(source_code: str):
    """
    Parses source code and extracts function details including raw source.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    functions = []
    lines = source_code.splitlines(keepends=True)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Extract raw source code for the function
            # AST nodes have 1-based line numbers
            start = node.lineno - 1
            end = node.end_lineno
            if start is not None and end is not None:
                func_source = "".join(lines[start:end])
                
                # Extract metadata
                args = []
                for arg in node.args.args:
                    if arg.arg != 'self':
                        args.append({
                            "name": arg.arg,
                            "type": ast.unparse(arg.annotation) if arg.annotation else None
                        })
                
                return_type = ast.unparse(node.returns) if node.returns else None
                
                # Basic complexity (cyclomatic)
                # Count control flow nodes: If, For, While, With, Try, ExceptHandler, BooleanOp, Raise, Return (approx)
                complexity = 1
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.ExceptHandler, ast.BoolOp, ast.Raise)):
                        complexity += 1
                
                # Raises detection
                raises = []
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Raise):
                        if isinstance(sub.exc, ast.Call) and hasattr(sub.exc.func, 'id'):
                            raises.append(sub.exc.func.id)
                        elif isinstance(sub.exc, ast.Name):
                            raises.append(sub.exc.id)

                functions.append({
                    "name": node.name,
                    "code": func_source,
                    "docstring": ast.get_docstring(node),
                    "lineno": node.lineno,
                    "args": args,
                    "return_type": return_type,
                    "complexity": complexity,
                    "loc": end - start,
                    "raises": list(set(raises)),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "is_generator": any(isinstance(sub, (ast.Yield, ast.YieldFrom)) for sub in ast.walk(node))
                })

    return functions

def extract_functions_from_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return extract_functions_from_code(content)

