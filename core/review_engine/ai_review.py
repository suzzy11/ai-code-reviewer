"""
AI Review Engine
Generates human-like code review feedback using AST metadata.
"""

from typing import Dict, List


def review_function(func_meta: Dict) -> Dict:
    """
    Perform AI-style review on a single function.
    """

    issues = []
    suggestions = []

    name = func_meta.get("name", "")
    args = func_meta.get("args", [])
    docstring = func_meta.get("docstring")
    complexity = func_meta.get("complexity", 0)
    nesting = func_meta.get("nesting_depth", 0)
    lines = func_meta.get("end_line", 0) - func_meta.get("start_line", 0)

    # Rule 1: Missing docstring
    if not docstring:
        issues.append("Missing docstring")
        suggestions.append("Add a clear docstring explaining the function purpose.")

    # Rule 2: Long function
    if lines > 40:
        issues.append("Function is too long")
        suggestions.append("Refactor the function into smaller, reusable components.")

    # Rule 3: Deep nesting
    if nesting > 3:
        issues.append("Deep nesting detected")
        suggestions.append("Reduce nesting by using guard clauses or helper functions.")

    # Rule 4: Too many arguments
    if len(args) > 5:
        issues.append("Too many parameters")
        suggestions.append("Consider grouping related parameters into a data structure.")

    # Rule 5: Poor naming
    if len(name) < 4:
        issues.append("Function name is too short")
        suggestions.append("Use a more descriptive function name.")

    verdict = "Good"
    if issues:
        verdict = "Needs Improvement"
    if len(issues) >= 3:
        verdict = "Poor"

    return {
        "function": name,
        "issues": issues,
        "suggestions": suggestions,
        "complexity": complexity,
        "verdict": verdict
    }


def review_file(functions: List[Dict]) -> List[Dict]:
    """
    Run AI review on all functions in a file.
    """
    return [review_function(f) for f in functions]
