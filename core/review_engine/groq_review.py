import os

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

def generate_docstring(source_code: str, style: str) -> str:
    """
    Generates docstring using LLM if available,
    otherwise returns a safe fallback.
    """
    try:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("No API key")

        client = Groq(api_key=api_key)

        # Use Llama 3.1 8B (fast & stable)
        model_id = "llama-3.1-8b-instant" 
        
        response = client.chat.completions.create(
            model=model_id,
            messages=[{
                "role": "system",
                "content": "You are a Python expert. Generate a docstring for the provided function/class. Output ONLY the docstring content (no quotes, no markdown blocks). Match the requested style."
            }, {
                "role": "user",
                "content": f"Style: {style}\nCode:\n{source_code}"
            }],
            temperature=0.1
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        # Return error message for UI debugging
        return f"Error: {str(e)}\n\n(Fallback)\n{fallback_docstring(style)}"
