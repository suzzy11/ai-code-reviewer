def generate_docstring(name, kind, style="google"):
    """
    Generate docstrings in different styles.
    Supported styles: google, numpy, rest
    """

    if style == "google":
        return f'''"""
{name} {kind.lower()}.

Args:
    TODO: Describe parameters.

Returns:
    TODO: Describe return value.
"""'''

    elif style == "numpy":
        return f'''"""
{name} {kind.lower()}.

Parameters
----------
TODO
    Describe parameters.

Returns
-------
TODO
    Describe return value.
"""'''

    elif style == "rest":
        return f'''"""
{name} {kind.lower()}.

:param TODO: Describe parameters
:return: Describe return value
"""'''

    else:
        return f'''"""
{name} {kind.lower()}.
"""'''
