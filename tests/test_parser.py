import pytest
import os
import tempfile
from src.py_parser import parse_python_file

@pytest.fixture
def temp_py_file():
    content = """
import os

class TestClass:
    '''Class docstring'''
    def method(self):
        pass

def global_func(a, b):
    '''Function docstring'''
    return a + b

async def async_func():
    pass
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(content)
        path = f.name
    
    yield path
    
    if os.path.exists(path):
        os.remove(path)

def test_parse_func(temp_py_file):
    funcs, classes, imports = parse_python_file(temp_py_file)
    
    # Verify global function
    g_func = next((f for f in funcs if f['name'] == 'global_func'), None)
    assert g_func is not None
    assert g_func['parent'] is None
    assert g_func['docstring'] == 'Function docstring'
    # args is now a list of dicts
    assert any(arg['name'] == 'a' for arg in g_func['args'])

def test_ast_analysis(temp_py_file):
    """Test complexity, return detection, and exceptions."""
    code = """
def complex_func(x):
    if x > 0:
        return x
    elif x < 0:
        raise ValueError("Negative")
    else:
        return None

def generator_func():
    yield 1
"""
    with open(temp_py_file, "w") as f:
        f.write(code)
        
    funcs, _, _ = parse_python_file(temp_py_file)
    
    # Check Complex Func
    c_func = next(f for f in funcs if f["name"] == "complex_func")
    assert c_func["returns_value"] is True # 'return x'
    assert "ValueError" in c_func["raises"]
    assert c_func["complexity"] >= 2 # if + elif
    
    # Check Generator
    g_func = next(f for f in funcs if f["name"] == "generator_func")
    assert g_func["is_generator"] is True
    assert g_func["returns_value"] is False

def test_parse_class(temp_py_file):
    funcs, classes, imports = parse_python_file(temp_py_file)
    
    # Verify class
    cls = next((c for c in classes if c['name'] == 'TestClass'), None)
    assert cls is not None
    assert cls['docstring'] == 'Class docstring'

def test_parse_nested(temp_py_file):
    funcs, classes, imports = parse_python_file(temp_py_file)
    
    # Verify method inside class
    method = next((f for f in funcs if f['name'] == 'method'), None)
    assert method is not None
    assert method['parent'] == 'TestClass'

def test_parse_async(temp_py_file):
    funcs, classes, imports = parse_python_file(temp_py_file)
    
    # Verify async function
    a_func = next((f for f in funcs if f['name'] == 'async_func'), None)
    assert a_func is not None

def test_parse_imports(temp_py_file):
    funcs, classes, imports = parse_python_file(temp_py_file)
    assert 'os' in imports

def test_parse_malformed_fail():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def broken(")
        path = f.name
        
    try:
        # Expect empty list, not crash
        from core.parser.python_parser import extract_functions_from_file
        functions = extract_functions_from_file(path)
        assert functions == []
    finally:
        if os.path.exists(path):
            os.remove(path)
