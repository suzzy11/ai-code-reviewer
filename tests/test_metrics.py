import pytest
from core.metrics_engine import MetricsEngine

def test_classify_metrics():
    # Complexity
    assert MetricsEngine.classify_metric(1, MetricsEngine.COMPLEXITY_THRESHOLDS) == "Good"
    assert MetricsEngine.classify_metric(6, MetricsEngine.COMPLEXITY_THRESHOLDS) == "Warning"
    assert MetricsEngine.classify_metric(11, MetricsEngine.COMPLEXITY_THRESHOLDS) == "Critical"

    # LOC
    assert MetricsEngine.classify_metric(40, MetricsEngine.LOC_THRESHOLDS) == "Good"
    assert MetricsEngine.classify_metric(120, MetricsEngine.LOC_THRESHOLDS) == "Critical"

def test_compute_function_metrics():
    func_data = {
        "complexity": 12,
        "loc": 60,
        "args": [1, 2, 3],
        "raises": ["ValueError"],
        "is_generator": True
    }
    
    metrics = MetricsEngine.compute_function_metrics(func_data)
    
    assert metrics["complexity_score"] == 12
    assert metrics["complexity_rating"] == "Critical"
    assert metrics["loc_rating"] == "Warning"
    assert metrics["param_count"] == 3
    assert metrics["param_rating"] == "Good"
    assert metrics["is_generator"] is True
    assert metrics["exception_count"] == 1

def test_aggregation():
    f1 = {"complexity": 2, "loc": 10, "docstring": "Yes", "is_generator": False, "raises": []}
    f2 = {"complexity": 4, "loc": 20, "docstring": None, "is_generator": True, "raises": ["Error"]}
    
    agg = MetricsEngine.aggregate_metrics([f1, f2], [])
    
    assert agg["total_functions"] == 2
    assert agg["coverage_pct"] == 50.0  # 1/2 documented
    assert agg["avg_complexity"] == 3.0
    assert agg["avg_loc"] == 15.0
    assert agg["generator_count"] == 1
    assert agg["total_exceptions"] == 1
