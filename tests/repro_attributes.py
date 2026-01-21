from core.docstring_engine.generator import clean_docstring

def test_attributes_stripped():
    doc = """MyClass.

    Attributes:
        x (int): The x value.
    """
    cleaned = clean_docstring(doc)
    print(f"Original:\n{doc}")
    print(f"Cleaned:\n{cleaned}")
    if "Attributes:" not in cleaned:
        print("FAIL: Attributes section was stripped!")
    else:
        print("PASS: Attributes section preserved.")

if __name__ == "__main__":
    test_attributes_stripped()
