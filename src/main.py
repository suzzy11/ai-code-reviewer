import os
import json
import streamlit as st
import matplotlib.pyplot as plt

# ✅ Correct imports (NO src.)
from parser import parse_python_file
from docstring_generator import generate_docstring

# Optional AI review (safe)
try:
    from core.review_engine.ai_review import ai_review_placeholder
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="AI Code Reviewer – Milestone 2",
    layout="wide"
)

st.title("🤖 AI Code Reviewer – Milestone 2")
st.caption("AST Parsing • Docstring Validation • Coverage Analysis")


# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.header("📁 Project Files")

EXAMPLES_DIR = "examples"
files = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".py")]

selected_file = st.sidebar.radio(
    "Select a Python file:",
    files
)

generate_docs = st.sidebar.checkbox("Generate baseline docstrings", value=True)

docstring_style = st.sidebar.selectbox(
    "Docstring style",
    ["Google", "NumPy", "reST"]
)

use_groq = st.sidebar.checkbox("Use Groq AI Review (Advanced)")


# ----------------------------
# Main UI
# ----------------------------
file_path = os.path.join(EXAMPLES_DIR, selected_file)

st.subheader("🛠️ AST Parsing Controls")
st.text_input("Path to scan", file_path, disabled=True)

output_path = st.text_input(
    "Output JSON path",
    "storage/review_logs.json"
)

view = st.radio(
    "Select View",
    ["Generated Docstrings", "Coverage Report", "AI Code Review"]
)

scan = st.button("🔍 Scan")


# ----------------------------
# Scan Logic
# ----------------------------
if scan:
    try:
        functions, classes, imports = parse_python_file(file_path)

        os.makedirs("storage", exist_ok=True)

        results = {
            "file": selected_file,
            "functions": [],
            "classes": []
        }

        # ----------------------------
        # Docstrings
        # ----------------------------
        if generate_docs:
            for f in functions:
                doc = f["docstring"] or generate_docstring(f["name"], "Function")
                results["functions"].append({
                    "name": f["name"],
                    "docstring": doc
                })

            for c in classes:
                doc = c["docstring"] or generate_docstring(c["name"], "Class")
                results["classes"].append({
                    "name": c["name"],
                    "docstring": doc
                })

        with open(output_path, "w") as fp:
            json.dump(results, fp, indent=2)

        # ----------------------------
        # View: Docstrings
        # ----------------------------
        if view == "Generated Docstrings":
            st.subheader("📄 Generated Docstrings")

            for fn in results["functions"]:
                with st.expander(f"Function: {fn['name']}"):
                    st.code(fn["docstring"])

            for cl in results["classes"]:
                with st.expander(f"Class: {cl['name']}"):
                    st.code(cl["docstring"])

        # ----------------------------
        # View: Coverage
        # ----------------------------
        elif view == "Coverage Report":
            st.subheader("📊 Coverage Report")

            total = len(functions) + len(classes)
            documented = len(results["functions"]) + len(results["classes"])
            coverage = int((documented / total) * 100) if total else 0

            col1, col2 = st.columns(2)
            col1.metric("Total items", total)
            col2.metric("Coverage %", coverage)

            fig, ax = plt.subplots()
            ax.bar(["Documented", "Missing"], [documented, total - documented])
            ax.set_ylabel("Count")
            ax.set_title("Docstring Coverage")
            st.pyplot(fig)

        # ----------------------------
        # View: AI Review
        # ----------------------------
        elif view == "AI Code Review":
            st.subheader("🤖 AI-Powered Code Review")

            if use_groq and GROQ_AVAILABLE:
                for f in functions:
                    review = ai_review_placeholder(f["name"])
                    with st.expander(f"Review: {f['name']}"):
                        st.write(review)
            else:
                st.info("Groq AI review not enabled or not configured.")

        st.success("✅ Scan completed successfully")

    except Exception as e:
        st.error(f"❌ Error during scan: {e}")
