from typing import List, Dict, Any
import statistics

class MetricsEngine:
    """
    AI-Independent Metrics Calculation Engine.
    Computes/Classifies complexity, LOC, coverage, and aggregation.
    """
    
    # Severity Thresholds
    COMPLEXITY_THRESHOLDS = {"warning": 6, "critical": 10}
    LOC_THRESHOLDS = {"warning": 50, "critical": 100}
    PARAM_THRESHOLDS = {"warning": 5, "critical": 10}

    @staticmethod
    def classify_metric(value: int, thresholds: Dict[str, int]) -> str:
        """Returns 'Good', 'Warning', or 'Critical' based on thresholds."""
        if value > thresholds["critical"]:
            return "Critical"
        elif value >= thresholds["warning"]:
            return "Warning"
        return "Good"

    @classmethod
    def compute_function_metrics(cls, func_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches function data with computed metrics and severity."""
        
        complexity = func_data.get("complexity", 1)
        loc = func_data.get("loc", 0)
        param_count = len(func_data.get("args", []))
        
        # Radon Integration (Grading)
        try:
            from radon.complexity import cc_rank
            grade = cc_rank(complexity) # Returns A, B, C, D, E, or F
            # Map Radon Grade to our Severity
            if grade in ['A', 'B']:
                rating = "Good"
            elif grade == 'C':
                rating = "Warning"
            else: # D, E, F
                rating = "Critical"
        except ImportError:
            # Fallback
            grade = "N/A"
            rating = cls.classify_metric(complexity, cls.COMPLEXITY_THRESHOLDS)

        metrics = {
            "complexity_score": complexity,
            "complexity_rating": rating,
            "complexity_grade": grade, # New field for Radon Grade
            "loc": loc,
            "loc_rating": cls.classify_metric(loc, cls.LOC_THRESHOLDS),
            "param_count": param_count,
            "param_rating": cls.classify_metric(param_count, cls.PARAM_THRESHOLDS),
            "exception_count": len(func_data.get("raises", [])),
            "is_generator": func_data.get("is_generator", False)
        }
        return metrics

    @classmethod
    def aggregate_metrics(cls, functions: List[Dict[str, Any]], classes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates project-level aggregated statistics."""
        
        total_funcs = len(functions)
        total_classes = len(classes)
        total_items = total_funcs + total_classes
        
        if total_items == 0:
            return {
                "total_functions": 0,
                "coverage_pct": 0,
                "avg_complexity": 0,
                "avg_loc": 0,
                "generator_count": 0,
                "total_exceptions": 0
            }

        # Coverage
        doc_funcs = sum(1 for f in functions if f.get("docstring"))
        doc_classes = sum(1 for c in classes if c.get("docstring"))
        coverage_pct = ((doc_funcs + doc_classes) / total_items) * 100

        # Complexity & LOC Stats
        complexities = [f.get("complexity", 1) for f in functions]
        locs = [f.get("loc", 0) for f in functions]
        
        avg_complexity = statistics.mean(complexities) if complexities else 0
        avg_loc = statistics.mean(locs) if locs else 0
        
        # Specific Counts
        generator_count = sum(1 for f in functions if f.get("is_generator"))
        total_exceptions = sum(len(f.get("raises", [])) for f in functions)
        
        return {
            "total_functions": total_funcs,
            "total_classes": total_classes,
            "coverage_pct": round(coverage_pct, 2),
            "avg_complexity": round(avg_complexity, 2),
            "avg_loc": round(avg_loc, 1),
            "generator_count": generator_count,
            "total_exceptions": total_exceptions,
            "max_complexity": max(complexities) if complexities else 0
        }
