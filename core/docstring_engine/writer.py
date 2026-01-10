import re

def apply_docstring(source_code: str, func_name: str, docstring: str) -> str:
    """
    Insert docstring above the given function definition.
    """
    pattern = rf"(def {func_name}\s*\(.*?\):)"
    replacement = f'{docstring}\n\\1'
    return re.sub(pattern, replacement, source_code, count=1)


def restore_backup(original_code: str) -> str:
    """
    Restore original source code.
    """
    return original_code
