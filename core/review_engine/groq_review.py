import os
from groq import Groq

# Global client for reuse
_GROQ_CLIENT = None

def _get_client():
    global _GROQ_CLIENT
    if _GROQ_CLIENT is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("No API key")
        _GROQ_CLIENT = Groq(api_key=api_key)
    return _GROQ_CLIENT

def fallback_docstring(style: str) -> str:
    if style.lower() == "google":
        return """Summary.

Args:
    param: Description.

Returns:
    Type: Description.
"""
    elif style.lower() == "numpy":
        return """Summary.

Parameters
----------
param : type
    Description.

Returns
-------
type
    Description.
"""
    else:
        return """Summary.

:param param: Description
:return: Description
"""

def _call_groq(prompt: str, source_code: str, style: str) -> str:
    """Helper to handle Groq API calls with common config."""
    try:
        client = _get_client()
        model_id = "llama-3.1-8b-instant" 
        
        response = client.chat.completions.create(
            model=model_id,
            messages=[{
                "role": "system",
                "content": prompt
            }, {
                "role": "user",
                "content": f"Style: {style}\nCode:\n{source_code}"
            }],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}\n\n(Fallback)\n{fallback_docstring(style)}"

def generate_docstring(source_code: str, style: str) -> str:
    """Generates function/class docstring strictly following PEP 257."""
    prompt = (
        "You are a Python expert. Generate a docstring for the provided function/class. "
        "Output ONLY the docstring content (no quotes, no markdown blocks). "
        "Strictly follow PEP 257: Use imperative mood (e.g., 'Return' not 'Returns'), "
        "end summary with a period, and incorrect capitalization/punctuation is forbidden. "
        "Match the requested style."
    )
    return _call_groq(prompt, source_code, style)

def generate_module_docstring(source_code: str, style: str) -> str:
    """Generates a file-level module docstring."""
    prompt = (
        "You are a Python expert. Generate a module-level docstring for the provided file context. "
        "Summarize the purpose of the module and its main components. "
        "Output ONLY the docstring content (no quotes, no markdown blocks). "
        "Strictly follow PEP 257."
    )
    return _call_groq(prompt, source_code, style)
