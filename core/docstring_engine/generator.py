"""
Docstring Generator
Supports Google, NumPy, reST, and pydoc styles.
"""

def generate_docstring(name: str, kind: str, style: str = "google") -> str:
    """
    Generate a baseline docstring for a function or class.

    Parameters
    ----------
    name : str
        Name of the function or class
    kind : str
        "Function" or "Class"
    style : str
        google | numpy | rest | pydoc
    """

    style = style.lower()

    if style == "numpy":
        return f'''"""
{name}

Parameters
----------
None

Returns
-------
None
"""
'''

    elif style == "rest":
        return f'''"""
{name}

:returns: None
:rtype: None
"""
'''

    elif style == "pydoc":
        return f'''"""
{name}.

@return: None
"""
'''

    # Default → Google style
    return f'''"""
{name}.

Args:
    None

Returns:
    None
"""
'''
