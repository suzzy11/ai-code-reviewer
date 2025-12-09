import streamlit as st
import sys
import os
import json

# Allow imports from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parser import parse_python_file
from docstring_generator import generate_docstring
from report import generate_report


# ------------------- PAGE CONFIG -------------------
st.set_page_config(
    page_title="AI Code Reviewer", layout="wide", initial_sidebar_state="expanded"
)

# ------------------- HEADER -------------------
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #1e88e5, #1565c0);
                padding: 25px;
                border-radius: 10px;">
        <h1 style="color:white;">AI Code Reviewer</h1>
        <p style="color:white;">Parser & Baseline Docstrings — scan, preview, export</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

# ------------------- SIDEBAR: EXAMPLES EXPLORER -------------------
st.sidebar.header("📁 Project Files (from examples/)")

EXAMPLES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "examples")
)


example_files = []
if os.path.exists(EXAMPLES_DIR):
    example_files = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".py")]

if example_files:
    selected_file = st.sidebar.radio("Select a Python file:", example_files)
    selected_path = os.path.join(EXAMPLES_DIR, selected_file)
else:
    st.sidebar.warning("No Python files found in examples folder.")
    selected_path = None

st.sidebar.markdown("---")
generate_docstrings_flag = st.sidebar.checkbox(
    "Generate baseline docstrings", value=True
)

st.sidebar.markdown("---")
coverage_placeholder = st.sidebar.metric("Coverage %", "0%")
functions_placeholder = st.sidebar.metric("Functions", "0")

# ------------------- MAIN CONTROLS -------------------

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("🛠️ AST Parsing Controls")

    path_to_scan = st.text_input(
        "Path to scan", selected_path if selected_path else "examples"
    )

    output_json_path = st.text_input("Output JSON path", "storage/review_logs.json")

with col2:
    scan_btn = st.button("🔍 Scan")

# ------------------- VIEW TOGGLE -------------------
view_mode = st.radio(
    "View", ["Generated Docstrings", "Coverage Report"], horizontal=True
)

# ------------------- OUTPUT AREA -------------------
if scan_btn:
    try:
        functions, classes, imports = parse_python_file(path_to_scan)

        results = []

        for f in functions:
            if not f.get("docstring") and generate_docstrings_flag:
                doc = generate_docstring(f["name"], "Function")
            else:
                doc = f.get("docstring", "Already documented")

            results.append(
                {
                    "file": f.get("file", "unknown"),
                    "function": f["name"],
                    "docstring": doc,
                }
            )

        # ------------ Coverage Calculation ------------
        total = len(functions)

        if generate_docstrings_flag:
            missing = 0
        else:
            missing = sum(1 for f in functions if not f.get("docstring"))

        coverage = 100 if total == 0 else round(((total - missing) / total) * 100, 2)

        st.sidebar.metric("Coverage %", f"{coverage}%")
        st.sidebar.metric("Functions", total)

        # ------------ Save JSON ------------
        report_data = {
            "coverage": coverage,
            "total_functions": total,
            "missing_docstrings": missing,
            "results": results,
        }

        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

        with open(output_json_path, "w") as f:
            json.dump(report_data, f, indent=2)

        # ------------ VIEW MODE DISPLAY ------------

        if view_mode == "Generated Docstrings":
            st.subheader("📘 Generated Docstrings")

            for item in results:
                st.markdown(f"### {item['file']} — `{item['function']}`")
                st.code(item["docstring"], language="python")

        elif view_mode == "Coverage Report":
            st.subheader("📊 Coverage Report")
            st.json(report_data)

        st.success("✅ Scan completed successfully")

    except Exception as e:
        st.error(f"❌ Error during scan: {e}")

else:
    st.info("No scan run yet. Select a file and click Scan.")
