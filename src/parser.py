import ast

def parse_python_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read())

    functions = []
    classes = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "docstring": ast.get_docstring(node)
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "docstring": ast.get_docstring(node)
            })
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

    return functions, classes, imports
