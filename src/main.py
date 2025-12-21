import streamlit as st
import sys
import os
import json

# --------------------------------------------------
# PATH SETUP
# --------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parser import parse_python_file
from docstring_generator import generate_docstring
from core.review_engine.ai_review import review_file

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="AI Code Reviewer",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #1e88e5, #1565c0);
                padding: 20px;
                border-radius: 10px;">
        <h1 style="color:white;">AI Code Reviewer</h1>
        <p style="color:white;">
            AST-based Docstring Generator • Coverage Analysis • AI Code Review
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("")

# --------------------------------------------------
# SIDEBAR – FILE SELECTION
# --------------------------------------------------
st.sidebar.header("📁 Example Files")

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
    st.sidebar.warning("No Python files found in examples/")
    selected_path = None

st.sidebar.markdown("---")

# --------------------------------------------------
# SIDEBAR – OPTIONS
# --------------------------------------------------
generate_docstrings_flag = st.sidebar.checkbox(
    "Generate baseline docstrings",
    value=True
)

docstring_style = st.sidebar.selectbox(
    "Docstring Style",
    ["google", "numpy", "rest"]
)

use_groq = st.sidebar.checkbox(
    "Use Groq AI Review (Advanced)"
)

st.sidebar.markdown("---")

coverage_placeholder = st.sidebar.empty()
functions_placeholder = st.sidebar.empty()

# --------------------------------------------------
# MAIN CONTROLS
# --------------------------------------------------
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

# --------------------------------------------------
# VIEW SELECTION
# --------------------------------------------------
view = st.radio(
    "Select View",
    ["Generated Docstrings", "Coverage Report", "🤖 AI Code Review"],
    horizontal=True
)

# --------------------------------------------------
# OUTPUT – ONLY AFTER SCAN
# --------------------------------------------------
if scan_btn:
    try:
        functions, classes, imports = parse_python_file(path_to_scan)

        # ---------------- DOCSTRING GENERATION ----------------
        doc_results = []

        for f in functions:
            if not f.get("docstring") and generate_docstrings_flag:
                doc = generate_docstring(
                    f["name"],
                    "Function",
                    style=docstring_style
                )
            else:
                doc = f.get("docstring", "Already documented")

            doc_results.append({
                "function": f["name"],
                "docstring": doc
            })

        # ---------------- COVERAGE ----------------
        total = len(functions)
        missing = sum(1 for f in functions if not f.get("docstring"))
        coverage = 100 if total == 0 else round(((total - missing) / total) * 100, 2)

        coverage_placeholder.metric("Coverage %", f"{coverage}%")
        functions_placeholder.metric("Functions", total)

        report_data = {
            "coverage": coverage,
            "total_functions": total,
            "missing_docstrings": missing,
            "results": doc_results
        }

        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w") as f:
            json.dump(report_data, f, indent=2)

        # --------------------------------------------------
        # VIEW HANDLING
        # --------------------------------------------------
        if view == "Generated Docstrings":
            st.subheader("📘 Generated Docstrings")

            for item in doc_results:
                st.markdown(f"### `{item['function']}`")
                st.code(item["docstring"], language="python")

        elif view == "Coverage Report":
            st.subheader("📊 Documentation Coverage")

            c1, c2, c3 = st.columns(3)
            c1.metric("Coverage", f"{coverage}%")
            c2.metric("Total Functions", total)
            c3.metric("Missing Docstrings", missing)

            with st.expander("📄 Detailed Report (JSON)"):
                st.json(report_data)

        elif view == "🤖 AI Code Review":
            st.subheader("🤖 AI-Powered Code Review")

            if use_groq:
                from core.review_engine.groq_review import groq_review_placeholder

                ai_reviews = [
                    groq_review_placeholder(f["name"], "")
                    for f in functions
                ]
            else:
                ai_reviews = review_file(functions)

            if not ai_reviews:
                st.warning("No functions found to review.")
            else:
                for review in ai_reviews:
                    with st.expander(f"🔍 Function: {review['function']}"):
                        colA, colB = st.columns([2, 1])

                        with colA:
                            st.markdown("### ⚠ Issues")
                            if review["issues"]:
                                for issue in review["issues"]:
                                    st.write(f"- {issue}")
                            else:
                                st.success("No issues detected")

                            st.markdown("### 💡 Suggestions")
                            if review["suggestions"]:
                                for suggestion in review["suggestions"]:
                                    st.write(f"- {suggestion}")
                            else:
                                st.info("No suggestions needed")

                        with colB:
                            st.markdown("### 📊 Summary")
                            st.metric("Verdict", review["verdict"])
                            st.metric("Complexity", review["complexity"])

        st.success("✅ Scan completed successfully")

    except Exception as e:
        st.error(f"❌ Error during scan: {e}")

else:
    st.info("Select a file and click **Scan** to view results.")
