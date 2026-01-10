def calculate_coverage(total_functions: int, missing_docstrings: int) -> float:
    """
    Calculate docstring coverage percentage.
    """
    if total_functions == 0:
        return 100.0

    covered = total_functions - missing_docstrings
    return round((covered / total_functions) * 100, 2)
