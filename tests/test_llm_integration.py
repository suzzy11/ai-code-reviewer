import pytest
from unittest.mock import patch, MagicMock
from core.docstring_engine.generator import generate_docstring
from core.validator.code_validator import CodeValidator
import ast

def test_llm_docstring_integration():
    """
    Integration test that mocks the LLM but verifies the full flow:
    Generator -> (Mock LLM) -> Output -> Validator -> Valid/Score
    """
    
    # 1. Setup Source Code
    source_code = "def add(a, b): return a + b"
    
    # 2. Mock LLM Response with a perfect docstring
    perfect_docstring = """Summary of add.

Args:
    a: First number
    b: Second number

Returns:
    Sum of a and b
"""
    
    with patch("core.review_engine.groq_review.Groq") as mock_groq:
        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices[0].message.content = perfect_docstring
        
        # 3. Generate Docstring
        generated = generate_docstring(source_code, style="google")
        
        # 4. Validate Result
        assert generated == perfect_docstring.strip()
        
        # 5. Check Validity with Validator
        validator = CodeValidator(style="Google")
        valid, msg = validator.validate_format(generated)
        assert valid is True, f"Generated docstring was invalid: {msg}"
        
        # 6. Check Score (simulate attaching it to a node)
        # We need to wrap it in a node to test get_score
        code_with_doc = f'def add(a, b):\n    """{generated}"""\n    return a + b'
        tree = ast.parse(code_with_doc)
        node = tree.body[0]
        
        score = validator.get_score(node)
        assert score == 100, f"Score was {score}, expected 100"

def test_llm_docstring_integration_numpy():
    source_code = "def sub(a, b): return a - b"
    numpy_doc = """
Summary.

Parameters
----------
a : int
    First
b : int
    Second

Returns
-------
int
    Result
"""
    with patch("core.review_engine.groq_review.Groq") as mock_groq:
        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices[0].message.content = numpy_doc
        
        generated = generate_docstring(source_code, style="numpy")
        
        validator = CodeValidator(style="Numpy")
        # Note: current validate_format might be simple for numpy, let's check
        valid, msg = validator.validate_format(generated, style="Numpy")
        assert valid is True, f"Numpy docstring invalid: {msg}"
