from core.parser.python_parser import extract_functions_from_code
from core.review_engine.groq_review import generate_docstring

def generate_for_file(source_code: str, style: str):
    functions = extract_functions_from_code(source_code)

    results = []
    for fn in functions:
        results.append({
            "name": fn["name"],
            "docstring": fn["docstring"],
            "generated": generate_docstring(source_code, style)
        })

    return results
