from core.review_engine.groq_client import generate_docstring


def ai_generate_docstring(func: dict, style: str) -> str:
    """
    Generate docstring for a parsed function using Groq AI.

    Args:
        func (dict): Parsed function metadata.
        style (str): Docstring style.

    Returns:
        str: AI-generated docstring.
    """
    return generate_docstring(
        function_name=func["name"],
        function_code=func["code"],
        style=style
    )
