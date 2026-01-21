import pytest
from src.main import clean_docstring

def test_clean_docstring_basic():
    raw = '"""Docstring content"""'
    assert clean_docstring(raw) == "Docstring content"

def test_clean_docstring_markdown():
    raw = '```python\n"""Docstring"""\n```'
    assert clean_docstring(raw) == "Docstring"

def test_clean_docstring_function_def():
    # LLM sometimes returns the whole function
    raw = '''def foo():
    """Docstring inside"""
    pass'''
    assert clean_docstring(raw) == "Docstring inside"

def test_clean_docstring_no_quotes():
    raw = "Just text"
    assert clean_docstring(raw) == "Just text"
