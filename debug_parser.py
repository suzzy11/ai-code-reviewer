import sys
import os
import ast

def parse_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)
    
    print(f"--- Parsing {path} ---")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
             doc = ast.get_docstring(node)
             print(f"Function: {node.name}, Docstring: {'YES' if doc else 'NO'}")
             if doc: print(f"  Content: {doc[:30]}...")

parse_file(r"c:\Users\User\OneDrive\ai_code_reviewer\ai_code_reviewer\examples\sample_b.py")
