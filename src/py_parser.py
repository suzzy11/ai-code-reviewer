import ast

def parse_python_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read())

    functions = []
    classes = []
    imports = []

    def visit_nodes(node, parent_class=None):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            functions.append({
                "name": node.name,
                "parent": parent_class,
                "lineno": node.lineno,
                "docstring": docstring,
                "args": [a.arg for a in node.args.args]
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "docstring": ast.get_docstring(node)
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
