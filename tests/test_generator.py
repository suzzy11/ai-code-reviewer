import pytest
from unittest.mock import patch, MagicMock
from core.docstring_engine.generator import (
    generate_docstring, 
    generate_module_docstring, 
    insert_module_docstring, 
    clean_docstring,
    analyze_code_metadata,
    _IMPERATIVE_FIXES
)

@pytest.fixture
def mock_groq():
    """Mock the Groq client used in groq_review module."""
    with patch("groq.Groq") as mock:
        yield mock

def test_gen_google(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "Google Style Docstring"
    
    result = generate_docstring("def foo(): pass", style="google")
    assert result == "Google Style Docstring"
    
    # Verify call arguments
    call_args = mock_client.chat.completions.create.call_args
    assert call_args.kwargs['model'] == "llama-3.1-8b-instant"
    assert "google" in call_args.kwargs['messages'][1]['content']

def test_gen_caching(mock_groq):
    """Verify that repeated calls use the cache."""
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "Cached Docstring"
    
    # First call
    generate_docstring("def cache_me(): pass", style="google")
    # Second call (should be cached)
    generate_docstring("def cache_me(): pass", style="google")
    
    # Should only be called once
    assert mock_client.chat.completions.create.call_count == 1

def test_gen_cleaning(mock_groq):
    """Verify that markdown code blocks are stripped."""
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "```python\nClean me\n```"
    
    result = generate_docstring("def clean_me(): pass", style="google")
    assert result == "Clean me"

def test_gen_numpy(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "Numpy Style Docstring"
    
    result = generate_docstring("def foo(): pass", style="numpy")
    assert result == "Numpy Style Docstring"
    
    call_args = mock_client.chat.completions.create.call_args
    assert "numpy" in call_args.kwargs['messages'][1]['content']

def test_gen_rest(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "ReST Style Docstring"
    
    result = generate_docstring("def foo(): pass", style="rest")
    assert result == "ReST Style Docstring"
    
    call_args = mock_client.chat.completions.create.call_args
    assert "rest" in call_args.kwargs['messages'][1]['content']

def test_gen_fallback_on_error():
    with patch("core.review_engine.groq_review.Groq", side_effect=Exception("API Error")):
        result = generate_docstring("def foo(): pass", style="google")
        assert "Error: API Error" in result
        assert "Summary." in result # Fallback content

def test_gen_module_doc(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "Module summary."
    
    result = generate_module_docstring("import os", style="google")
    assert result == "Module summary."

def test_insert_docstring(tmp_path):
    # Create dummy file
    f = tmp_path / "test_mod.py"
    f.write_text("import os\n\ndef foo(): pass", encoding="utf-8")
    
    insert_module_docstring(str(f), "Docs.")
    
    content = f.read_text(encoding="utf-8")
    assert '"""\nDocs.\n"""' in content
    assert "import os" in content

def test_cleaning_pep257():
    """Verify cleanup enforces capitalization and punctuation."""
    raw = "lower case summary"
    cleaned = clean_docstring(raw)
    assert cleaned == "Lower case summary."

def test_cleaning_chatter():
    """Verify AI chatter is removed."""
    raw = "Sure! Here is the docstring:\nSummary."
    cleaned = clean_docstring(raw)
    assert cleaned == "Summary."

def test_metadata_analysis():
    """Verify code analysis detects returns, yields, raises correctly."""
    
    code = "def foo(): return 1"
    meta = analyze_code_metadata(code)
    assert meta["has_return"] is True
    
    code_void = "def foo(): print('hi')"
    meta = analyze_code_metadata(code_void)
    assert meta["has_return"] is False

def test_hallucination_control():
    """Verify that Returns is stripped if function does not return."""
    raw_doc = """Summary.
    
    Returns:
        int: Value.
    """
    # Simulate void function
    meta = {"has_return": False, "has_yield": False, "raised_exceptions": set()}
    
    cleaned = clean_docstring(raw_doc, metadata=meta)
    assert "Returns:" not in cleaned
    assert "Summary." in cleaned

def test_pep257_imperative_mood():
    """Verify comprehensive imperative mood fixes (D401)."""
    from core.docstring_engine.generator import _IMPERATIVE_FIXES
    
    # Test multiple verbs from the dictionary
    test_cases = [
        ("Calculates the sum.", "Calculate the sum."),
        ("Returns a value.", "Return a value."),
        ("Generates a docstring.", "Generate a docstring."),
        ("Validates input data.", "Validate input data."),
        ("Processes the request.", "Process the request."),
        ("Provides helper methods.", "Provide helper methods."),
    ]
    
    for raw, expected in test_cases:
        cleaned = clean_docstring(raw)
        assert cleaned == expected, f"Expected '{expected}', got '{cleaned}'"
    
    # Verify dictionary coverage
    assert len(_IMPERATIVE_FIXES) >= 40, "Should have at least 40 verb mappings"

def test_forbidden_sections():
    """Verify Examples/Notes are stripped."""
    raw = """Summary.

    Examples:
        foo()
        
    Notes:
        Some note.
    """
    cleaned = clean_docstring(raw)
    assert "Examples:" not in cleaned
    assert "Notes:" not in cleaned
    assert "Summary." in cleaned

def test_strict_hallucination():
    """Verify detailed metadata support for raises detection."""
    code = "def foo(): raise ValueError('bad')"
    meta = analyze_code_metadata(code)
    assert "ValueError" in meta["raised_exceptions"]
    
    doc = """Summary.

    Raises:
        ValueError: Bad value.
    """
    cleaned = clean_docstring(doc, metadata=meta)
    assert "Raises:" in cleaned
    assert "ValueError" in cleaned
    
    # Case: No raise in code, but doc has it -> strip
    code_safe = "def foo(): pass"
    meta_safe = analyze_code_metadata(code_safe)
    cleaned_safe = clean_docstring(doc, metadata=meta_safe)
    assert "Raises:" not in cleaned_safe

