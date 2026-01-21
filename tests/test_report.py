import pytest
from io import StringIO
import sys
from src.report import generate_report

def test_report_output(capsys):
    functions = [
        {"name": "f1", "docstring": "Present"},
        {"name": "f2", "docstring": None}
    ]
    classes = [
        {"name": "c1", "docstring": "Present"}
    ]
    
    generate_report(functions, classes)
    
    captured = capsys.readouterr()
    
    assert "Total Functions + Classes: 3" in captured.out
    assert "With Docstrings: 2" in captured.out
    assert "Coverage: 66.67%" in captured.out

def test_report_empty(capsys):
    generate_report([], [])
    captured = capsys.readouterr()
    assert "Total Functions + Classes: 0" in captured.out
    assert "Coverage: 0.00%" in captured.out
