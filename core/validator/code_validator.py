import ast
import re

class CodeValidator:
    """
    Validates Python code for documentation standards.
    """
    
    def __init__(self, style="Google"):
        self.style = style

    def is_documented(self, node):
        """Checks if a function or class node has a docstring."""
        return ast.get_docstring(node) is not None

    def validate_format(self, docstring, style=None):
        """
        Basic structural check against the requested style.
        Returns (is_valid, message)
        """
        if not docstring:
            return False, "Empty docstring"
            
        target_style = style or self.style
        
        if target_style.lower() == "google":
            # Check for common Google sections
            has_summary = len(docstring.split('\n')[0].strip()) > 0
            has_args = "Args:" in docstring
            has_returns = "Returns:" in docstring or "Yields:" in docstring
            
            if not has_summary:
                return False, "Missing summary line"
            if not (has_args or has_returns):
                return False, "Missing Args or Returns section (Google style)"
                
        elif target_style.lower() == "numpy":
            if "Parameters" not in docstring and "Returns" not in docstring:
                return False, "Missing Parameters or Returns section (Numpy style)"
                
        return True, "Valid format"

    def get_score(self, node):
        """
        Returns a quality score (0-100) based on docstring completeness.
        """
        docstring = ast.get_docstring(node)
        if not docstring:
            return 0
            
        score = 20 # Base score for having one
        
        # Length bonus
        if len(docstring) > 50: score += 20
        if len(docstring) > 150: score += 20
        
        # Structural bonus (Google style check)
        if "Args:" in docstring: score += 20
        if "Returns:" in docstring: score += 20
        
        return min(score, 100)

    def analyze_node(self, node):
        """Performs full analysis of a node."""
        documented = self.is_documented(node)
        docstring = ast.get_docstring(node) if documented else None
        
        valid = False
        msg = "No docstring"
        if documented:
            valid, msg = self.validate_format(docstring)
            
        return {
            "name": getattr(node, 'name', 'unknown'),
            "type": "Class" if isinstance(node, ast.ClassDef) else "Function",
            "is_documented": documented,
            "is_valid": valid,
            "validation_message": msg,
            "score": self.get_score(node)
        }
