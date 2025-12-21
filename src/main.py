import streamlit as st
import sys
import os
import json

# ---------------- PATH SETUP ----------------
# Allow imports from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parser import parse_python_file
from docstring_generator import generate_docstring
from report import generate_report
from core.review_engine.ai_review import review_file


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Code Reviewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- HEADER ----------------
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #1e88e5, #1565c0);
                padding: 25px;
                border-radius: 10px;">
        <h1 style="color:white;">AI Code Reviewer</h1>
        <p style="color:white;">AST-based Docstring Generator & AI Code Review</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("")

# ---------------- SIDEBAR: PROJECT FILES ----------------
st.sidebar.header("📁 Project Files (examples/)")

EXAMPLES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "examples")
)

example_files = []
if os.path.exists(EXAMPLES_DIR):
    example_files = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".py")]

if example_files:
    selected_file = st.sidebar.radio(
        "Select a Python file:",
        example_files
    )
    selected_path = os.path.join(EXAMPLES_DIR, selected_file)
else:
    st.sidebar.warning("No Python files found in examples folder.")
    selected_path = None

st.sidebar.markdown("---")
generate_docstrings_flag = st.sidebar.checkbox(
    "Generate baseline docstrings",
    value=True
)

st.sidebar.markdown("---")
st.sidebar.metric("Coverage %", "0%")
st.sidebar.metric("Functions", "0")

# ---------------- MAIN CONTROLS ----------------
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("🛠️ AST Parsing Controls")

    path_to_scan = st.text_input(
        "Path to scan",
        selected_path if selected_path else "examples"
    )

    output_json_path = st.text_input(
        "Output JSON path",
        "storage/review_logs.json"
    )

with col2:
    scan_btn = st.button("🔍 Scan")

# ---------------- VIEW SELECTION ----------------
view = st.radio(
    "View",
    ["Generated Docstrings", "Coverage Report", "🤖 AI Code Review"],
    horizontal=True
)

# ---------------- OUTPUT SECTION ----------------
if scan_btn:
    try:
        functions, classes, imports = parse_python_file(path_to_scan)

        # -------- DOCSTRING GENERATION --------
        results = []

        for f in functions:
            if not f.get("docstring") and generate_docstrings_flag:
                doc = generate_docstring(f["name"], "Function")
            else:
                doc = f.get("docstring", "Already documented")

            results.append({
                "file": f.get("file", "unknown"),
                "function": f["name"],
                "docstring": doc
            })

        # -------- COVERAGE CALCULATION --------
        total = len(functions)

        if generate_docstrings_flag:
            missing = 0
        else:
            missing = sum(1 for f in functions if not f.get("docstring"))

        coverage = 100 if total == 0 else round(((total - missing) / total) * 100, 2)

        st.sidebar.metric("Coverage %", f"{coverage}%")
        st.sidebar.metric("Functions", total)

        # -------- SAVE JSON REPORT --------
        report_data = {
            "coverage": coverage,
            "total_functions": total,
            "missing_docstrings": missing,
            "results": results
        }

        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

        with open(output_json_path, "w") as f:
            json.dump(report_data, f, indent=2)

        # -------- VIEW HANDLING --------
        if view == "Generated Docstrings":
            st.subheader("📘 Generated Docstrings")

            for item in results:
                st.markdown(f"### `{item['function']}`")
                st.code(item["docstring"], language="python")

        elif view == "Coverage Report":
            st.subheader("📊 Coverage Report")
            st.json(report_data)

        elif view == "🤖 AI Code Review":
            st.subheader("🤖 AI-Powered Code Review")

            ai_reviews = review_file(functions)

            for review in ai_reviews:
                with st.expander(f"Function: {review['function']}"):
                    st.markdown(f"**Verdict:** `{review['verdict']}`")
                    st.markdown(f"**Complexity:** {review['complexity']}")

                    if review["issues"]:
                        st.markdown("### ⚠ Issues Detected")
                        for issue in review["issues"]:
                            st.write(f"- {issue}")
                    else:
                        st.success("No issues detected 🎉")

                    if review["suggestions"]:
                        st.markdown("### 💡 AI Suggestions")
                        for suggestion in review["suggestions"]:
                            st.write(f"- {suggestion}")

        st.success("✅ Scan completed successfully")

    except Exception as e:
        st.error(f"❌ Error during scan: {e}")

else:
    st.info("No scan run yet. Select a file and click Scan.")
