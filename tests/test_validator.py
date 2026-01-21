import pytest
import ast
from core.validator.code_validator import CodeValidator

@pytest.fixture
def validator():
    return CodeValidator(style="Google")

def parse_func(code):
    """Helper to get function node from string"""
    tree = ast.parse(code)
    return tree.body[0]

def test_val_missing(validator):
    code = "def foo(): pass"
    node = parse_func(code)
    
    assert validator.is_documented(node) is False
    assert validator.get_score(node) == 0
    res = validator.analyze_node(node)
    assert res['is_documented'] is False

def test_val_google(validator):
    code = '''
def foo(a, b):
    """
    Summary of the function which is long enough to pass the length check.
    
    This is a detailed description that adds more characters to safely exceed 
    the fifty character limit and hopefully the one hundred and fifty limit 
    if we are verbose enough in our testing string.
    
    Args:
        a: A param description.
        b: B param description.
        
    Returns:
        C: Return description.
    """
    return a+b
'''
    node = parse_func(code)
    
    assert validator.is_documented(node) is True
    valid, msg = validator.validate_format(ast.get_docstring(node))
    assert valid is True
    assert len(ast.get_docstring(node)) > 150 # Verify length
    assert validator.get_score(node) == 100 

def test_val_numpy(validator):
    # Testing logic handles google style check by default in get_score, but we can check validate_format
    code = '''
def foo():
    """
    Summary.
    
    Parameters
    ----------
    None
    """
    pass
'''
    node = parse_func(code)
    doc = ast.get_docstring(node)
    
    valid, msg = validator.validate_format(doc, style="Numpy")
    assert valid is True
    
    # Check failure for wrong style
    valid, msg = validator.validate_format(doc, style="Google")
    assert valid is False
    assert "Missing Args or Returns" in msg

def test_val_scoring(validator):
    # Partial score check
    code = '''
def foo():
    """Summary only."""
    pass
'''
    node = parse_func(code)
    score = validator.get_score(node)
    assert 0 < score < 100
    assert score == 20 # Base 20, no length bonus (>50), no Args/Returns
