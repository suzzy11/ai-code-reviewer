def generate_docstring(function_name, style="google"):
    if style == "numpy":
        return f"""\"\"\"
{function_name}

Parameters
----------
None

Returns
-------
None
\"\"\""""
    elif style == "rest":
        return f"""\"\"\"
{function_name}

:returns: None
\"\"\""""
    else:
        return f"""\"\"\"
{function_name}

Args:
    None

Returns:
    None
\"\"\""""
