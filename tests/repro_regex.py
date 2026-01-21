import re

def _extract_docstring_params(docstring: str, style: str) -> set:
    if not docstring:
        return set()
        
    params = set()
    doc = docstring.strip()
    
    # 1. Google Style Strategy
    match = re.search(r"Args:\s*(.+?)(\n\s*[A-Z]|$)", doc, re.DOTALL)
    if match:
        content = match.group(1)
        arg_matches = re.findall(r"^\s*(\w+)(?:\s*\(.*?\))?\s*:", content, re.MULTILINE)
        params.update(arg_matches)
        
    # 2. NumPy Style Strategy
    match = re.search(r"Parameters\n\s*-+\s*\n(.+?)(\n\s*\n|\n\s*[A-Z]|$)", doc, re.DOTALL)
    if match:
        content = match.group(1)
        arg_matches = re.findall(r"^\s*(\w+)\s*:", content, re.MULTILINE)
        if not arg_matches:
             candidates = re.findall(r"^\s*(\w+)(?:\s*:\s*.*)?$", content, re.MULTILINE)
             for cand in candidates:
                 if cand and not cand.startswith(" "):
                     params.add(cand)
        else:
             params.update(arg_matches)

    # 3. ReST Style Strategy
    arg_matches = re.findall(r":param\s+(\w+):", doc)
    params.update(arg_matches)
    
    return params

def test_regex():
    # Mimic the docstring from the screenshot
    docstring = """Calculate the average of a list of numbers.

Args:
    numbers (list): A list of numbers to calculate the average
    from.
"""
    print(f"Testing Docstring:\n{docstring}")
    
    params = _extract_docstring_params(docstring, "google")
    print(f"Extracted Params: {params}")
    
    if "numbers" not in params:
        print("FAIL: 'numbers' not extracted")
    else:
        print("PASS: 'numbers' extracted")

    # Test Multi-style resilience
    
    # 1. Google Doc, Numpy Style Setting
    print("\nTest Mismatch: Google Doc but Style='numpy'")
    params_mismatch = _extract_docstring_params(docstring, "numpy")
    if "numbers" in params_mismatch:
        print("PASS: Extracted 'numbers' despite wrong style setting")
    else:
        print("FAIL: Failed to extract 'numbers' when style mismatch")

    # 2. Numpy Doc, ReST Style Setting
    numpy_doc = """
    Parameters
    ----------
    x : int
        The value.
    """
    print("\nTest Mismatch: Numpy Doc but Style='rest'")
    params_numpy = _extract_docstring_params(numpy_doc, "rest")
    if "x" in params_numpy:
        print("PASS: Extracted 'x' from Numpy doc")
    else:
        print("FAIL: Failed to extract 'x' from Numpy doc")

if __name__ == "__main__":
    test_regex()
