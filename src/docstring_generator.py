from core.parser.python_parser import extract_functions_from_code
from core.docstring_engine.generator import generate_docstring

def generate_for_file(source_code: str, style: str):
    functions = extract_functions_from_code(source_code)

    results = []
    for fn in functions:
        # Skip if already documented (optional, but good practice)
        # if fn['docstring']: continue 
        
        doc = generate_docstring(fn['code'], style)
        results.append({
            "name": fn["name"],
            "docstring": fn["docstring"],
            "generated": doc,
            "lineno": fn["lineno"]
        })

    return results

