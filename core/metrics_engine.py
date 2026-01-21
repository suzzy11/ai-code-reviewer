"""
Enhanced Metrics Engine for AI Code Reviewer.

Provides comprehensive code quality metrics including:
- Cyclomatic complexity (with Radon grading)
- Maintainability Index
- Documentation coverage
- Health scores at function, file, and project levels
"""

from typing import List, Dict, Any, Optional
import statistics


class MetricsEngine:
    """
    AI-Independent Metrics Calculation Engine.
    Computes/Classifies complexity, LOC, coverage, health scores, and aggregation.
    """
    
    # ========================================================================
    # SEVERITY THRESHOLDS
    # ========================================================================
    
    COMPLEXITY_THRESHOLDS = {"warning": 6, "critical": 10}
    LOC_THRESHOLDS = {"warning": 50, "critical": 100}
    PARAM_THRESHOLDS = {"warning": 5, "critical": 10}
    NESTING_THRESHOLDS = {"warning": 3, "critical": 5}
    
    # Health score weights
    HEALTH_WEIGHTS = {
        "documentation": 0.30,
        "complexity": 0.35,
        "size": 0.20,
        "structure": 0.15
    }

    # ========================================================================
    # CLASSIFICATION HELPERS
    # ========================================================================

    @staticmethod
    def classify_metric(value: int, thresholds: Dict[str, int]) -> str:
        """Return 'Good', 'Warning', or 'Critical' based on thresholds."""
        if value > thresholds["critical"]:
            return "Critical"
        elif value >= thresholds["warning"]:
            return "Warning"
        return "Good"
    
    @staticmethod
    def rating_to_score(rating: str) -> float:
        """Convert rating to numeric score (0-100)."""
        return {"Good": 100, "Warning": 60, "Critical": 20}.get(rating, 50)

    # ========================================================================
    # FUNCTION-LEVEL METRICS
    # ========================================================================

    @staticmethod
    def _extract_docstring_params(docstring: str, style: str) -> set:
        """
        Extract parameter names from a docstring.
        Tries to detect parameters using patterns from all supported styles 
        (Google, NumPy, ReST) to be robust against style mismatches.
        """
        if not docstring:
            return set()
            
        import re
        params = set()
        doc = docstring.strip()
        
        # 1. Google Style Strategy
        # Look for Args: section
        match = re.search(r"Args:\s*(.+?)(\n\s*[A-Z]|$)", doc, re.DOTALL)
        if match:
            content = match.group(1)
            # Matches: param_name (type): description
            # or: param_name: description
            # Use robust regex to verify it looks like a param definition
            arg_matches = re.findall(r"^\s*(\w+)(?:\s*\(.*?\))?\s*:", content, re.MULTILINE)
            params.update(arg_matches)
            
        # 2. NumPy Style Strategy
        # Look for Parameters section
        match = re.search(r"Parameters\n\s*-+\s*\n(.+?)(\n\s*\n|\n\s*[A-Z]|$)", doc, re.DOTALL)
        if match:
            content = match.group(1)
            # Matches: param : type
            # Strict mode: require colon
            arg_matches = re.findall(r"^\s*(\w+)\s*:", content, re.MULTILINE)
            
            # If strict match fails, try looser match for badly formatted docs
            if not arg_matches:
                 # Matches line starting with word, optional colon, end of line
                 candidates = re.findall(r"^\s*(\w+)(?:\s*:\s*.*)?$", content, re.MULTILINE)
                 # Filter out obvious non-params (like description continuation lines)
                 # Numpy params usually start at the beginning of the line (or standard indent)
                 for cand in candidates:
                     if cand and not cand.startswith(" "):
                         params.add(cand)
            else:
                 params.update(arg_matches)

        # 3. ReST Style Strategy
        # Matches: :param name: description
        arg_matches = re.findall(r":param\s+(\w+):", doc)
        params.update(arg_matches)
                
        return params


    @classmethod
    def compute_function_metrics(cls, func_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich function data with computed metrics, severity, and health score."""
        
        complexity = func_data.get("complexity", 1)
        loc = func_data.get("loc", 0)
        code_params = [arg['name'] for arg in func_data.get("args", [])]
        param_count = len(code_params)
        nesting_level = func_data.get("nesting_level", 0)
        
        docstring = func_data.get("docstring", "")
        has_docstring = bool(docstring)
        doc_style = func_data.get("docstring_info", {}).get("style", "unknown")
        
        # --- Coverage Correctness Calculation ---
        doc_correctness = 0.0
        if has_docstring:
            # 1. Base score for existence
            doc_correctness = 50.0 
            
            # 2. Parameter Check
            doc_params = cls._extract_docstring_params(docstring, doc_style)
            
            if not code_params and not doc_params:
                # No params, simple docstring -> Perfect
                doc_correctness = 100.0
            elif not code_params and doc_params:
                # Code has no params, but docstring lists them -> Hallucination/Stale
                doc_correctness = 50.0 # Penalty
            elif code_params and not doc_params:
                # Code has params, docstring lists none -> Incomplete
                doc_correctness = 60.0 # Better than nothing
            else:
                # Both have params, check overlap
                code_set = set(code_params)
                common = code_set.intersection(doc_params)
                extra = doc_params - code_set
                missing = code_set - doc_params
                
                # Jaccard-like index for correctness
                # strict_match_ratio = len(common) / (len(code_set) + len(extra))
                
                # Weighted score:
                # + points for matching params
                # - penalty for missing params
                # - small penalty for extra params (stale)
                
                match_score = (len(common) / len(code_set)) * 100.0
                
                # Penalize for extra params (stale docs)
                stale_penalty = len(extra) * 10.0
                
                final_score = match_score - stale_penalty
                doc_correctness = max(0.0, min(100.0, final_score))
        
        # Store for health calc
        doc_score = doc_correctness
        
        # Radon Integration (Grading)
        try:
            from radon.complexity import cc_rank
            grade = cc_rank(complexity)  # Returns A, B, C, D, E, or F
            # Map Radon Grade to our Severity
            if grade in ['A', 'B']:
                complexity_rating = "Good"
            elif grade == 'C':
                complexity_rating = "Warning"
            else:  # D, E, F
                complexity_rating = "Critical"
        except ImportError:
            grade = "N/A"
            complexity_rating = cls.classify_metric(complexity, cls.COMPLEXITY_THRESHOLDS)

        loc_rating = cls.classify_metric(loc, cls.LOC_THRESHOLDS)
        param_rating = cls.classify_metric(param_count, cls.PARAM_THRESHOLDS)
        nesting_rating = cls.classify_metric(nesting_level, cls.NESTING_THRESHOLDS)
        
        # Calculate health score (0-100)
        # doc_score is already calculated above based on correctness
        complexity_score = cls.rating_to_score(complexity_rating)
        size_score = cls.rating_to_score(loc_rating)
        structure_score = (cls.rating_to_score(param_rating) + cls.rating_to_score(nesting_rating)) / 2
        
        health_score = (
            cls.HEALTH_WEIGHTS["documentation"] * doc_score +
            cls.HEALTH_WEIGHTS["complexity"] * complexity_score +
            cls.HEALTH_WEIGHTS["size"] * size_score +
            cls.HEALTH_WEIGHTS["structure"] * structure_score
        )
        
        # Overall health rating
        if health_score >= 80:
            health_rating = "Healthy"
        elif health_score >= 50:
            health_rating = "Needs Attention"
        else:
            health_rating = "Critical"

        metrics = {
            "complexity_score": complexity,
            "complexity_rating": complexity_rating,
            "complexity_grade": grade,
            "loc": loc,
            "loc_rating": loc_rating,
            "param_count": param_count,
            "param_rating": param_rating,
            "nesting_level": nesting_level,
            "nesting_rating": nesting_rating,
            "exception_count": len(func_data.get("raises", [])),
            "is_generator": func_data.get("is_generator", False),
            "is_async": func_data.get("is_async", False),
            "has_docstring": has_docstring,
            "docstring_style": func_data.get("docstring_info", {}).get("style", "unknown"),
            "doc_coverage": round(doc_score, 1), # EXPOSE CORRECTNESS SCORE
            "health_score": round(health_score, 1),
            "health_rating": health_rating,
            # Type annotation coverage
            "has_return_type": func_data.get("return_type") is not None,
            "typed_params": sum(1 for arg in func_data.get("args", []) if arg.get("type")),
            "total_params": param_count
        }
        return metrics

    # ========================================================================
    # CLASS-LEVEL METRICS
    # ========================================================================

    @classmethod
    def compute_class_metrics(cls, class_data: Dict[str, Any], class_methods: List[Dict]) -> Dict[str, Any]:
        """Compute metrics for a class including its methods."""
        
        has_docstring = bool(class_data.get("docstring"))
        method_count = class_data.get("method_count", 0)
        attribute_count = len(class_data.get("attributes", []))
        base_count = len(class_data.get("bases", []))
        loc = class_data.get("loc", 0)
        
        # Calculate method-level aggregates
        if class_methods:
            avg_method_complexity = statistics.mean(m.get("complexity", 1) for m in class_methods)
            documented_methods = sum(1 for m in class_methods if m.get("docstring"))
            method_doc_coverage = (documented_methods / len(class_methods) * 100) if class_methods else 100
        else:
            avg_method_complexity = 0
            method_doc_coverage = 100
        
        # Health score for class
        doc_score = 100 if has_docstring else 0
        method_doc_score = method_doc_coverage
        complexity_score = 100 if avg_method_complexity < 6 else (60 if avg_method_complexity < 10 else 20)
        
        health_score = (
            0.25 * doc_score +
            0.35 * method_doc_score +
            0.25 * complexity_score +
            0.15 * (100 if loc < 200 else (60 if loc < 500 else 20))
        )
        
        return {
            "has_docstring": has_docstring,
            "docstring_style": class_data.get("docstring_info", {}).get("style", "unknown"),
            "method_count": method_count,
            "attribute_count": attribute_count,
            "base_count": base_count,
            "loc": loc,
            "avg_method_complexity": round(avg_method_complexity, 2),
            "method_doc_coverage": round(method_doc_coverage, 1),
            "health_score": round(health_score, 1)
        }

    # ========================================================================
    # FILE-LEVEL METRICS
    # ========================================================================

    @classmethod
    def compute_file_metrics(cls, parse_result) -> Dict[str, Any]:
        """Compute metrics for an entire file from ParseResult."""
        
        functions = parse_result.functions
        classes = parse_result.classes
        raw_metrics = parse_result.raw_metrics
        module_doc = parse_result.module_docstring
        
        total_funcs = len(functions)
        total_classes = len(classes)
        
        # Documentation coverage (Correctness-based)
        # Sum up correctness scores (0-100) instead of binary presence
        func_coverage_sum = sum(f.get("doc_coverage", 100 if f.get("docstring") else 0) for f in functions)
        
        # Classes: For now, use binary existence (100 or 0) + method coverage?
        # Let's keep it simple: Class docstring existence = 100
        class_coverage_sum = sum(100 if c.get("docstring") else 0 for c in classes)
        
        has_module_doc = module_doc.exists if module_doc else False
        module_score = 100 if has_module_doc else 0
        
        total_items = total_funcs + total_classes + 1  # +1 for module
        total_score = func_coverage_sum + class_coverage_sum + module_score
        
        coverage_pct = (total_score / total_items) if total_items > 0 else 100
        
        # Complexity stats
        complexities = [f.get("complexity", 1) for f in functions]
        avg_complexity = statistics.mean(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0
        
        # Type annotation coverage
        typed_params = sum(
            sum(1 for arg in f.get("args", []) if arg.get("type"))
            for f in functions
        )
        total_params = sum(len(f.get("args", [])) for f in functions)
        type_coverage = (typed_params / total_params * 100) if total_params > 0 else 100
        
        # Overall file health
        file_health = (
            0.40 * coverage_pct +
            0.30 * (100 if avg_complexity < 6 else (60 if avg_complexity < 10 else 20)) +
            0.15 * type_coverage +
            0.15 * (100 if has_module_doc else 0)
        )
        
        return {
            "total_functions": total_funcs,
            "total_classes": total_classes,
            "total_loc": raw_metrics.get("total_loc", 0),
            "sloc": raw_metrics.get("sloc", 0),
            "blank_lines": raw_metrics.get("blank_lines", 0),
            "comment_lines": raw_metrics.get("comment_lines", 0),
            "coverage_pct": round(coverage_pct, 1),
            "avg_complexity": round(avg_complexity, 2),
            "max_complexity": max_complexity,
            "type_annotation_coverage": round(type_coverage, 1),
            "has_module_docstring": has_module_doc,
            "health_score": round(file_health, 1)
        }

    # ========================================================================
    # PROJECT-LEVEL AGGREGATION
    # ========================================================================

    @classmethod
    def aggregate_metrics(cls, functions: List[Dict[str, Any]], classes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate project-level aggregated statistics."""
        
        total_funcs = len(functions)
        total_classes = len(classes)
        total_items = total_funcs + total_classes
        
        if total_items == 0:
            return {
                "total_functions": 0,
                "total_classes": 0,
                "coverage_pct": 0,
                "avg_complexity": 0,
                "avg_loc": 0,
                "generator_count": 0,
                "async_count": 0,
                "total_exceptions": 0,
                "max_complexity": 0,
                "health_score": 0
            }

        # Coverage (Correctness-based)
        func_coverage_sum = sum(f.get("doc_coverage", 100 if f.get("docstring") else 0) for f in functions)
        class_coverage_sum = sum(100 if c.get("docstring") else 0 for c in classes)
        
        coverage_pct = (func_coverage_sum + class_coverage_sum) / total_items if total_items > 0 else 0

        # Complexity & LOC Stats
        complexities = [f.get("complexity", 1) for f in functions]
        locs = [f.get("loc", 0) for f in functions]
        
        avg_complexity = statistics.mean(complexities) if complexities else 0
        avg_loc = statistics.mean(locs) if locs else 0
        max_complexity = max(complexities) if complexities else 0
        
        # Specific Counts
        generator_count = sum(1 for f in functions if f.get("is_generator"))
        async_count = sum(1 for f in functions if f.get("is_async"))
        total_exceptions = sum(len(f.get("raises", [])) for f in functions)
        
        # Severity distribution
        severity_dist = {"Good": 0, "Warning": 0, "Critical": 0}
        for f in functions:
            rating = cls.classify_metric(f.get("complexity", 1), cls.COMPLEXITY_THRESHOLDS)
            severity_dist[rating] += 1
        
        # Overall project health
        health_score = (
            0.35 * coverage_pct +
            0.35 * (100 if avg_complexity < 6 else (60 if avg_complexity < 10 else 20)) +
            0.30 * (severity_dist["Good"] / total_funcs * 100 if total_funcs > 0 else 100)
        )
        
        return {
            "total_functions": total_funcs,
            "total_classes": total_classes,
            "coverage_pct": round(coverage_pct, 2),
            "avg_complexity": round(avg_complexity, 2),
            "avg_loc": round(avg_loc, 1),
            "max_complexity": max_complexity,
            "generator_count": generator_count,
            "async_count": async_count,
            "total_exceptions": total_exceptions,
            "severity_distribution": severity_dist,
            "health_score": round(health_score, 1)
        }

    # ========================================================================
    # MAINTAINABILITY INDEX (RADON)
    # ========================================================================

    @staticmethod
    def compute_maintainability_index(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Compute Maintainability Index using Radon.
        
        Returns:
            Dict with 'mi_score' (0-100), 'mi_rank' (A-F), and 'mi_rating'.
        """
        try:
            from radon.metrics import mi_visit, mi_rank
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            mi_score = mi_visit(content, multi=True)
            rank = mi_rank(mi_score)
            
            # Map rank to rating
            if rank in ['A', 'B']:
                rating = "Highly Maintainable"
            elif rank == 'C':
                rating = "Moderately Maintainable"
            else:
                rating = "Difficult to Maintain"
            
            return {
                "mi_score": round(mi_score, 2),
                "mi_rank": rank,
                "mi_rating": rating
            }
        except ImportError:
            return None
        except Exception as e:
            return {"error": str(e)}

    # ========================================================================
    # HALSTEAD METRICS (RADON)
    # ========================================================================

    @staticmethod
    def compute_halstead_metrics(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Compute Halstead complexity metrics using Radon.
        
        Returns:
            Dict with vocabulary, length, volume, difficulty, effort, time, bugs.
        """
        try:
            from radon.metrics import h_visit
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            results = h_visit(content)
            
            if results:
                # Aggregate results
                total = results[0] if results else None
                if total:
                    return {
                        "vocabulary": total.vocabulary,
                        "length": total.length,
                        "volume": round(total.volume, 2),
                        "difficulty": round(total.difficulty, 2),
                        "effort": round(total.effort, 2),
                        "time": round(total.time, 2),
                        "bugs": round(total.bugs, 4)
                    }
            return None
        except ImportError:
            return None
        except Exception as e:
            return {"error": str(e)}
