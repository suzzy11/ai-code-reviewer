def calculate_coverage(functions: list) -> dict:
    """
    Calculate documentation coverage for parsed functions.

    Returns:
        dict with total, documented, undocumented, coverage_percent
    """
    if not functions:
        return {
            "total": 0,
            "documented": 0,
            "undocumented": 0,
            "coverage_percent": 0
        }

    documented = sum(1 for f in functions if f.get("docstring"))
    total = len(functions)
    undocumented = total - documented
    coverage_percent = round((documented / total) * 100, 2)

    return {
        "total": total,
        "documented": documented,
        "undocumented": undocumented,
        "coverage_percent": coverage_percent
    }
