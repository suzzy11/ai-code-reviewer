from core.docstring_engine.ai_validator import AIOutputValidator, ValidationResult
import sys

def test_ai_validator_extraction():
    print("Testing AIOutputValidator Robust Extraction...")
    
    # Mock metadata
    func_meta = {
        "args": [{"name": "numbers"}],
        "returns_value": False,
        "is_generator": False,
        "raises": []
    }
    
    # 1. Google style with loose indentation (simulating the user issue)
    docstring_google = """Calculate average.

Args:
  numbers (list): List of nums.
"""
    result = AIOutputValidator.validate_docstring(docstring_google, func_meta, style="google")
    print(f"\nResult Google (loose indent): Valid={result.is_valid}")
    for issue in result.issues:
        print(f"  - {issue.code}: {issue.message}")
        
    if any(i.code == "MISSING_PARAM" for i in result.issues):
        print("FAIL: 'numbers' still marked missing in Google style")
    else:
        print("PASS: 'numbers' correctly found in Google style")

    # 2. Mismatched Style (Numpy style doc, but validating as Google)
    docstring_numpy = """Calculate average.

Parameters
----------
numbers : list
    List of nums.
"""
    result_mismatch = AIOutputValidator.validate_docstring(docstring_numpy, func_meta, style="google")
    print(f"\nResult Mismatch (Numpy doc, Google style): Valid={result_mismatch.is_valid}")
    for issue in result_mismatch.issues:
        print(f"  - {issue.code}: {issue.message}")

    if any(i.code == "MISSING_PARAM" for i in result_mismatch.issues):
        print("FAIL: 'numbers' marked missing in mismatch test")
    else:
        print("PASS: 'numbers' correctly found in mismatch test")

if __name__ == "__main__":
    test_ai_validator_extraction()
