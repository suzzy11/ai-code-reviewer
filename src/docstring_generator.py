def generate_docstring(name, type_):
    return f"""
    {type_} Name: {name}

    Description:
    This {type_.lower()} performs its intended task.

    Returns:
    None
    """
