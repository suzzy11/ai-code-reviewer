import sys
import os
import ast

output_file = "debug_output.txt"
with open(output_file, "w") as out:
    def log(msg):
        out.write(msg + "\n")
        print(msg)

    path = r"c:\Users\User\OneDrive\ai_code_reviewer\ai_code_reviewer\examples\sample_b.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)
    
    log(f"--- Parsing {path} ---")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
             doc = ast.get_docstring(node)
             log(f"Function: {node.name}, Docstring: {'YES' if doc else 'NO'}")
