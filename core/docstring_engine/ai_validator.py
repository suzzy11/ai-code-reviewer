"""
AI Output Validator for AI Code Reviewer.

Validates AI-generated docstrings to prevent hallucinations and ensure accuracy.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    severity: str  # "error", "warning", "info"
    code: str  # e.g., "MISSING_PARAM", "EXTRA_PARAM"
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validating an AI-generated docstring."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    corrected_docstring: Optional[str] = None
    confidence_score: float = 1.0


class AIOutputValidator:
    """
    Validate AI-generated docstrings against function metadata.
    
    Checks for:
    - All parameters documented
    - No extra/fake parameters
    - Return type accuracy
    - Raised exceptions accuracy
    - PEP 257 compliance
    """
    
    # Common false positive exception patterns
    FALSE_POSITIVE_EXCEPTIONS = {
        "TypeError", "AttributeError", "KeyError", "IndexError",
        "RuntimeError", "Exception"  # Generic exceptions
    }
    
    @classmethod
    def validate_docstring(
        cls, 
        docstring: str, 
        func_meta: Dict[str, Any],
        style: str = "google"
    ) -> ValidationResult:
        """
        Validate an AI-generated docstring against function metadata.
        
        Args:
            docstring: The generated docstring content.
            func_meta: Function metadata from parser.
            style: Docstring style (google, numpy, rest).
        
        Returns:
            ValidationResult with issues and optional corrections.
        """
        issues = []
        
        if not docstring:
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    severity="error",
                    code="EMPTY_DOCSTRING",
                    message="Docstring is empty"
                )]
            )
        
        # 1. Validate parameters
        param_issues = cls._validate_parameters(docstring, func_meta, style)
        issues.extend(param_issues)
        
        # 2. Validate return documentation
        return_issues = cls._validate_returns(docstring, func_meta, style)
        issues.extend(return_issues)
        
        # 3. Validate exceptions
        exception_issues = cls._validate_exceptions(docstring, func_meta, style)
        issues.extend(exception_issues)
        
        # 4. Validate first line (PEP 257)
        pep_issues = cls._validate_pep257(docstring)
        issues.extend(pep_issues)
        
        # Calculate confidence score
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        confidence = max(0, 1.0 - (error_count * 0.2) - (warning_count * 0.05))
        
        # Try to auto-correct if there are issues
        corrected = None
        if issues:
            corrected = cls.auto_correct(docstring, issues, func_meta, style)
        
        return ValidationResult(
            is_valid=len([i for i in issues if i.severity == "error"]) == 0,
            issues=issues,
            corrected_docstring=corrected,
            confidence_score=round(confidence, 2)
        )
    
    @classmethod
    def _validate_parameters(
        cls, 
        docstring: str, 
        func_meta: Dict[str, Any],
        style: str
    ) -> List[ValidationIssue]:
        """Check that all parameters are documented correctly."""
        issues = []
        
        # Get expected parameters (excluding self/cls)
        expected_params = set()
        for arg in func_meta.get("args", []):
            name = arg.get("name", "")
            # Remove * and ** prefixes for varargs
            name = name.lstrip("*")
            if name and name not in ("self", "cls"):
                expected_params.add(name)
        
        # Extract documented parameters based on style
        documented_params = cls._extract_documented_params(docstring, style)
        
        # Find missing parameters
        missing = expected_params - documented_params
        for param in missing:
            issues.append(ValidationIssue(
                severity="warning",
                code="MISSING_PARAM",
                message=f"Parameter '{param}' is not documented",
                suggestion=f"Add documentation for parameter '{param}'"
            ))
        
        # Find extra/fake parameters (hallucinations)
        extra = documented_params - expected_params
        for param in extra:
            issues.append(ValidationIssue(
                severity="error",
                code="EXTRA_PARAM",
                message=f"Parameter '{param}' does not exist in function signature",
                suggestion=f"Remove documentation for non-existent parameter '{param}'"
            ))
        
        return issues
    
    @classmethod
    def _extract_documented_params(cls, docstring: str, style: str) -> set:
        """Extract parameter names from docstring using robust multi-style detection."""
        params = set()
        doc = docstring.strip()
        
        # 1. Google Style Strategy
        # Look for Args: section
        match = re.search(r"Args:\s*(.+?)(\n\s*[A-Z]|$)", doc, re.DOTALL)
        if match:
            content = match.group(1)
            # Matches: param_name (type): description
            # or: param_name: description
            # Use robust regex with flexible indentation
            arg_matches = re.findall(r"^\s*(\w+)(?:\s*\(.*?\))?\s*:", content, re.MULTILINE)
            params.update(arg_matches)
        
        # 2. NumPy Style Strategy
        # Look for Parameters section
        match = re.search(r"Parameters\n\s*-+\s*\n(.+?)(\n\s*\n|\n\s*[A-Z]|$)", doc, re.DOTALL)
        if match:
            content = match.group(1)
            # Matches: param : type
            arg_matches = re.findall(r"^\s*(\w+)\s*:", content, re.MULTILINE)
            if not arg_matches:
                 # Looser match for non-strict formatting
                 candidates = re.findall(r"^\s*(\w+)(?:\s*:\s*.*)?$", content, re.MULTILINE)
                 for cand in candidates:
                     if cand and not cand.startswith(" "):
                         params.add(cand)
            else:
                 params.update(arg_matches)
        
        # 3. ReST Style Strategy
        # Matches: :param name: description
        arg_matches = re.findall(r":param\s+(?:\w+\s+)?(\w+):", doc)
        params.update(arg_matches)
        
        return params
    
    @classmethod
    def _validate_returns(
        cls, 
        docstring: str, 
        func_meta: Dict[str, Any],
        style: str
    ) -> List[ValidationIssue]:
        """Validate return documentation accuracy."""
        issues = []
        
        has_return = func_meta.get("returns_value", False)
        is_generator = func_meta.get("is_generator", False)
        
        # Check for Returns section
        has_returns_doc = any(
            pattern in docstring 
            for pattern in ["Returns:", "Returns\n", ":returns:", ":return:"]
        )
        
        # Check for Yields section
        has_yields_doc = any(
            pattern in docstring 
            for pattern in ["Yields:", "Yields\n", ":yields:"]
        )
        
        if has_return and not has_returns_doc and not is_generator:
            issues.append(ValidationIssue(
                severity="warning",
                code="MISSING_RETURN",
                message="Function returns a value but return is not documented"
            ))
        
        if not has_return and has_returns_doc and not is_generator:
            issues.append(ValidationIssue(
                severity="warning",
                code="UNNECESSARY_RETURN",
                message="Function does not return a value but Returns section exists",
                suggestion="Remove Returns section"
            ))
        
        if is_generator and not has_yields_doc:
            issues.append(ValidationIssue(
                severity="warning",
                code="MISSING_YIELDS",
                message="Generator function should document Yields"
            ))
        
        return issues
    
    @classmethod
    def _validate_exceptions(
        cls, 
        docstring: str, 
        func_meta: Dict[str, Any],
        style: str
    ) -> List[ValidationIssue]:
        """Validate exception documentation accuracy."""
        issues = []
        
        # Get actually raised exceptions
        actual_raises = set(func_meta.get("raises", []))
        
        # Extract documented exceptions
        documented_raises = set()
        
        # Google style: "    ExceptionType: description"
        if style == "google" and "Raises:" in docstring:
            raises_section = docstring.split("Raises:")[1].split("\n\n")[0] if "Raises:" in docstring else ""
            pattern = r"^\s{4}(\w+(?:Error|Exception)?)\s*:"
            documented_raises.update(re.findall(pattern, raises_section, re.MULTILINE))
        
        # NumPy style
        elif style == "numpy" and "Raises\n" in docstring:
            raises_section = docstring.split("Raises\n")[1].split("\n\n")[0] if "Raises\n" in docstring else ""
            pattern = r"^(\w+(?:Error|Exception)?)\s*$"
            documented_raises.update(re.findall(pattern, raises_section, re.MULTILINE))
        
        # reST style
        elif style == "rest":
            pattern = r":raises\s+(\w+):"
            documented_raises.update(re.findall(pattern, docstring))
        
        # Check for hallucinated exceptions (not in actual raises)
        for exc in documented_raises:
            if exc not in actual_raises:
                # Only flag if it's not a common false positive
                if exc not in cls.FALSE_POSITIVE_EXCEPTIONS:
                    issues.append(ValidationIssue(
                        severity="warning",
                        code="EXTRA_EXCEPTION",
                        message=f"Exception '{exc}' is documented but not explicitly raised",
                        suggestion=f"Verify that '{exc}' is actually raised"
                    ))
        
        return issues
    
    @classmethod
    def _validate_pep257(cls, docstring: str) -> List[ValidationIssue]:
        """Validate basic PEP 257 compliance."""
        issues = []
        
        lines = docstring.split('\n')
        if not lines:
            return issues
        
        first_line = lines[0].strip()
        
        # D400: First line should end with a period
        if first_line and not first_line.endswith('.') and not first_line.endswith('!') and not first_line.endswith('?'):
            issues.append(ValidationIssue(
                severity="info",
                code="D400",
                message="First line should end with a period",
                suggestion="Add a period at the end of the first line"
            ))
        
        # D403: First word should be capitalized
        if first_line and first_line[0].islower():
            issues.append(ValidationIssue(
                severity="info",
                code="D403",
                message="First word should be capitalized",
                suggestion=f"Capitalize '{first_line.split()[0]}'"
            ))
        
        # D404: First word should not be "This"
        if first_line.lower().startswith("this "):
            issues.append(ValidationIssue(
                severity="info",
                code="D404",
                message="First word should not be 'This'",
                suggestion="Rephrase to start with an imperative verb"
            ))
        
        return issues
    
    @classmethod
    def auto_correct(
        cls, 
        docstring: str, 
        issues: List[ValidationIssue],
        func_meta: Dict[str, Any],
        style: str
    ) -> str:
        """
        Attempt to auto-correct common issues.
        
        Currently handles:
        - D400: Add period
        - D403: Capitalize first word
        - D404: Remove "This"
        """
        corrected = docstring
        
        for issue in issues:
            if issue.code == "D400":
                # Add period to first line
                lines = corrected.split('\n')
                if lines:
                    first = lines[0].rstrip()
                    if first and first[-1] not in '.!?':
                        lines[0] = first + '.'
                    corrected = '\n'.join(lines)
            
            elif issue.code == "D403":
                # Capitalize first word
                if corrected and corrected[0].islower():
                    corrected = corrected[0].upper() + corrected[1:]
            
            elif issue.code == "D404":
                # Remove "This function/method/class"
                patterns = [
                    r"^This function\s+",
                    r"^This method\s+",
                    r"^This class\s+",
                    r"^This module\s+",
                    r"^This\s+"
                ]
                for pattern in patterns:
                    corrected = re.sub(pattern, "", corrected, flags=re.IGNORECASE)
                # Capitalize after removal
                if corrected and corrected[0].islower():
                    corrected = corrected[0].upper() + corrected[1:]
        
        return corrected
