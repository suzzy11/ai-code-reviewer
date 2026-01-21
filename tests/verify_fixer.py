import os
import shutil
from core.utils.ast_modifier import SignatureModifier

def test_signature_modification():
    print("Testing Signature Modification...")
    
    # create a dummy file
    filename = "tests/temp_sig_test.py"
    content = """def my_func():
    print("Hello")

def existing_args(a, b):
    return a + b
"""
    with open(filename, "w") as f:
        f.write(content)
        
    try:
        # Case 1: Add single arg to empty
        print("\n[Case 1] Adding 'x' to 'my_func'...")
        success, msg = SignatureModifier.add_missing_arguments(filename, "my_func", ["x"])
        if not success:
            print(f"FAIL: {msg}")
            return
            
        with open(filename, "r") as f:
            new_content = f.read()
        print("Updated Content:")
        print(new_content)
        
        if "def my_func(x):" in new_content:
            print("PASS: 'x' added correctly.")
        else:
            print("FAIL: 'x' not found in signature.")

        # Case 2: Add arg to existing
        print("\n[Case 2] Adding 'c' to 'existing_args'...")
        success, msg = SignatureModifier.add_missing_arguments(filename, "existing_args", ["c"])
        
        with open(filename, "r") as f:
            new_content = f.read()
        print("Updated Content:")
        print(new_content)
        
        if "def existing_args(a, b, c):" in new_content:
            print("PASS: 'c' added correctly.")
        else:
            print("FAIL: 'c' not found or incorrect.")
            
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_signature_modification()
