import ast

def parse_python_file(file_path: str):
    """
    Parse a Python file and extract functions and classes.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "lineno": node.lineno
            })

        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "lineno": node.lineno
            })

    return functions, classes
