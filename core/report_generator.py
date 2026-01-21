"""
Report Generator for AI Code Reviewer.

Generates comprehensive reports in multiple formats:
- JSON: Machine-readable structured data
- CSV: Spreadsheet-compatible tabular data
- Markdown: Human-readable documentation
- HTML: Styled web report
"""

import json
import csv
import io
from typing import Dict, List, Any, Optional
from datetime import datetime


class ReportGenerator:
    """Generate analysis reports in various formats."""
    
    @staticmethod
    def generate_json_report(
        scan_results: Dict[str, Any],
        include_raw_data: bool = True
    ) -> str:
        """
        Generate a comprehensive JSON report.
        
        Args:
            scan_results: Results from scanning (functions, classes, metrics).
            include_raw_data: Whether to include full function/class data.
        
        Returns:
            JSON string with report data.
        """
        report = {
            "report_type": "AI Code Reviewer Analysis",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_functions": len(scan_results.get("functions", [])),
                "total_classes": len(scan_results.get("classes", [])),
                "coverage_pct": scan_results.get("metrics", {}).get("coverage_pct", 0),
                "avg_complexity": scan_results.get("metrics", {}).get("avg_complexity", 0),
                "health_score": scan_results.get("metrics", {}).get("health_score", 0)
            },
            "metrics": scan_results.get("metrics", {}),
        }
        
        if include_raw_data:
            report["functions"] = scan_results.get("functions", [])
            report["classes"] = scan_results.get("classes", [])
        
        # Add undocumented items summary
        undoc_funcs = [
            f["name"] for f in scan_results.get("functions", []) 
            if not f.get("docstring")
        ]
        undoc_classes = [
            c["name"] for c in scan_results.get("classes", []) 
            if not c.get("docstring")
        ]
        
        report["undocumented"] = {
            "functions": undoc_funcs,
            "classes": undoc_classes,
            "count": len(undoc_funcs) + len(undoc_classes)
        }
        
        return json.dumps(report, indent=2, default=str)
    
    @staticmethod
    def generate_csv_report(
        scan_results: Dict[str, Any],
        report_type: str = "functions"
    ) -> str:
        """
        Generate a CSV report for functions or classes.
        
        Args:
            scan_results: Results from scanning.
            report_type: "functions", "classes", or "all".
        
        Returns:
            CSV string with tabular data.
        """
        output = io.StringIO()
        
        if report_type in ("functions", "all"):
            functions = scan_results.get("functions", [])
            
            if functions:
                writer = csv.DictWriter(output, fieldnames=[
                    "name", "file", "parent", "lineno", "loc", 
                    "has_docstring", "complexity", "param_count", 
                    "returns_value", "is_async", "is_generator"
                ])
                writer.writeheader()
                
                for f in functions:
                    writer.writerow({
                        "name": f.get("name", ""),
                        "file": f.get("file", ""),
                        "parent": f.get("parent", ""),
                        "lineno": f.get("lineno", 0),
                        "loc": f.get("loc", 0),
                        "has_docstring": "Yes" if f.get("docstring") else "No",
                        "complexity": f.get("complexity", 1),
                        "param_count": len(f.get("args", [])),
                        "returns_value": "Yes" if f.get("returns_value") else "No",
                        "is_async": "Yes" if f.get("is_async") else "No",
                        "is_generator": "Yes" if f.get("is_generator") else "No"
                    })
        
        if report_type == "all":
            output.write("\n\n")
        
        if report_type in ("classes", "all"):
            classes = scan_results.get("classes", [])
            
            if classes:
                writer = csv.DictWriter(output, fieldnames=[
                    "name", "file", "lineno", "loc", 
                    "has_docstring", "method_count", "base_classes"
                ])
                writer.writeheader()
                
                for c in classes:
                    writer.writerow({
                        "name": c.get("name", ""),
                        "file": c.get("file", ""),
                        "lineno": c.get("lineno", 0),
                        "loc": c.get("loc", 0),
                        "has_docstring": "Yes" if c.get("docstring") else "No",
                        "method_count": c.get("method_count", 0),
                        "base_classes": ", ".join(c.get("bases", []))
                    })
        
        return output.getvalue()
    
    @staticmethod
    def generate_markdown_report(
        scan_results: Dict[str, Any],
        project_name: str = "Project"
    ) -> str:
        """
        Generate a human-readable Markdown report.
        
        Args:
            scan_results: Results from scanning.
            project_name: Name of the project for the report title.
        
        Returns:
            Markdown string.
        """
        metrics = scan_results.get("metrics", {})
        functions = scan_results.get("functions", [])
        classes = scan_results.get("classes", [])
        
        lines = [
            f"# 📊 Code Analysis Report: {project_name}",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            "",
            "## 📈 Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Functions | {len(functions)} |",
            f"| Total Classes | {len(classes)} |",
            f"| Documentation Coverage | {metrics.get('coverage_pct', 0)}% |",
            f"| Average Complexity | {metrics.get('avg_complexity', 0)} |",
            f"| Max Complexity | {metrics.get('max_complexity', 0)} |",
            f"| Health Score | {metrics.get('health_score', 0)}/100 |",
            "",
        ]
        
        # Undocumented items
        undoc_funcs = [f for f in functions if not f.get("docstring")]
        undoc_classes = [c for c in classes if not c.get("docstring")]
        
        if undoc_funcs or undoc_classes:
            lines.extend([
                "## ⚠️ Undocumented Items",
                "",
            ])
            
            if undoc_funcs:
                lines.append("### Functions")
                for f in undoc_funcs:
                    parent = f.get("parent", "")
                    name = f"{parent}.{f['name']}" if parent else f['name']
                    lines.append(f"- `{name}` (line {f.get('lineno', '?')})")
                lines.append("")
            
            if undoc_classes:
                lines.append("### Classes")
                for c in undoc_classes:
                    lines.append(f"- `{c['name']}` (line {c.get('lineno', '?')})")
                lines.append("")
        
        # High complexity functions
        high_complexity = [f for f in functions if f.get("complexity", 1) > 10]
        if high_complexity:
            lines.extend([
                "## 🔴 High Complexity Functions",
                "",
                "| Function | Complexity | File |",
                "|----------|------------|------|",
            ])
            for f in sorted(high_complexity, key=lambda x: x.get("complexity", 0), reverse=True):
                lines.append(f"| `{f['name']}` | {f.get('complexity', 0)} | {f.get('file', '')} |")
            lines.append("")
        
        # Detailed function list
        lines.extend([
            "## 📋 Function Details",
            "",
            "| Function | File | LOC | Complexity | Documented |",
            "|----------|------|-----|------------|------------|",
        ])
        
        for f in functions[:50]:  # Limit to 50 for readability
            doc_icon = "✅" if f.get("docstring") else "❌"
            parent = f.get("parent", "")
            name = f"{parent}.{f['name']}" if parent else f['name']
            lines.append(f"| `{name}` | {f.get('file', '')} | {f.get('loc', 0)} | {f.get('complexity', 1)} | {doc_icon} |")
        
        if len(functions) > 50:
            lines.append(f"\n*... and {len(functions) - 50} more functions*")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Report generated by AI Code Reviewer*")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_html_report(
        scan_results: Dict[str, Any],
        project_name: str = "Project"
    ) -> str:
        """
        Generate a styled HTML report.
        
        Args:
            scan_results: Results from scanning.
            project_name: Name of the project for the report title.
        
        Returns:
            HTML string.
        """
        metrics = scan_results.get("metrics", {})
        functions = scan_results.get("functions", [])
        classes = scan_results.get("classes", [])
        
        # Calculate health color
        health_score = metrics.get("health_score", 0)
        if health_score >= 80:
            health_color = "#10b981"  # Green
        elif health_score >= 50:
            health_color = "#f59e0b"  # Yellow
        else:
            health_color = "#ef4444"  # Red
        
        coverage = metrics.get("coverage_pct", 0)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Analysis Report - {project_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 1rem; margin-bottom: 2rem; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .timestamp {{ opacity: 0.8; font-size: 0.9rem; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .metric-card {{ background: white; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .metric-value {{ font-size: 2rem; font-weight: bold; color: #6366f1; }}
        .metric-label {{ font-size: 0.875rem; color: #64748b; }}
        .section {{ background: white; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }}
        .section-title {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; font-weight: 600; }}
        tr:hover {{ background: #f8fafc; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 500; }}
        .badge-green {{ background: #dcfce7; color: #166534; }}
        .badge-red {{ background: #fee2e2; color: #991b1b; }}
        .badge-yellow {{ background: #fef3c7; color: #92400e; }}
        .health-ring {{ width: 120px; height: 120px; margin: 0 auto; }}
        .progress {{ height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }}
        .progress-bar {{ height: 100%; background: linear-gradient(90deg, #10b981, #34d399); }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Code Analysis Report</h1>
            <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" style="color: {health_color}">{health_score}</div>
                <div class="metric-label">Health Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{coverage}%</div>
                <div class="metric-label">Documentation Coverage</div>
                <div class="progress" style="margin-top: 0.5rem;">
                    <div class="progress-bar" style="width: {coverage}%"></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(functions)}</div>
                <div class="metric-label">Total Functions</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(classes)}</div>
                <div class="metric-label">Total Classes</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.get('avg_complexity', 0):.1f}</div>
                <div class="metric-label">Avg Complexity</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📋 Function Analysis</div>
            <table>
                <thead>
                    <tr>
                        <th>Function</th>
                        <th>File</th>
                        <th>LOC</th>
                        <th>Complexity</th>
                        <th>Documented</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for f in functions[:100]:  # Limit to 100
            parent = f.get("parent", "")
            name = f"{parent}.{f['name']}" if parent else f['name']
            doc_badge = '<span class="badge badge-green">Yes</span>' if f.get("docstring") else '<span class="badge badge-red">No</span>'
            
            complexity = f.get("complexity", 1)
            if complexity > 10:
                complexity_badge = f'<span class="badge badge-red">{complexity}</span>'
            elif complexity > 5:
                complexity_badge = f'<span class="badge badge-yellow">{complexity}</span>'
            else:
                complexity_badge = f'<span class="badge badge-green">{complexity}</span>'
            
            html += f"""
                    <tr>
                        <td><code>{name}</code></td>
                        <td>{f.get('file', '')}</td>
                        <td>{f.get('loc', 0)}</td>
                        <td>{complexity_badge}</td>
                        <td>{doc_badge}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
        
        <footer style="text-align: center; color: #64748b; padding: 2rem;">
            <p>Generated by AI Code Reviewer</p>
        </footer>
    </div>
</body>
</html>
"""
        
        return html
