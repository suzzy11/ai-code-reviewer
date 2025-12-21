"""
Groq-based AI Code Review (Placeholder)

This module simulates AI-based code review using Groq.
Later, this can be replaced with real Groq API integration.
"""

def groq_review_placeholder(function_name: str, source_code: str) -> dict:
    """
    Generate a placeholder AI review for a function.

    Parameters
    ----------
    function_name : str
        Name of the function being reviewed
    source_code : str
        Source code of the function

    Returns
    -------
    dict
        AI-generated review feedback
    """
    return {
        "function": function_name,
        "summary": f"AI review for `{function_name}` using Groq.",
        "issues": [
            "Consider adding type hints",
            "Docstring could be more descriptive"
        ],
        "score": "8/10"
    }
