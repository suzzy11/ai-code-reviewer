import streamlit as st
import pandas as pd
import os
import sys
import ast
import inspect
try:
    from streamlit_echarts import st_echarts  # type: ignore
except ImportError:
    st_echarts = None
import matplotlib.pyplot as plt
import json

# Ensure we can import local modules regardless of where the app is run
sys.path.append(os.path.dirname(__file__))
import py_parser as doc_parser
import importlib
importlib.reload(doc_parser) # Force reload to pick up parser changes
try:
    from core.review_engine import groq_review
    from core.validator.code_validator import CodeValidator
    from core.metrics_engine import MetricsEngine
    importlib.reload(groq_review) # Force reload to pick up model changes
    validator = CodeValidator()
except ImportError:
    # Fallback if core path not set
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from core.review_engine import groq_review
    from core.validator.code_validator import CodeValidator
    from core.metrics_engine import MetricsEngine
    importlib.reload(groq_review)
    validator = CodeValidator()

# ---------------- CONFIG & COLORS ----------------
COLOR_MAP = {
    "Home": "#db2777",       # Pink
    "Docstring": "#be185d",  # Pink-Deep
    "Metrics": "#9d174d",    # Pink-Dark
    "Validation": "#ec4899", # Pink-Light
    "Dashboard": "#be185d",
    "Search Result": "#db2777"
}

st.set_page_config(
    page_title="AI Code Reviewer v1.1.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM CSS ----------------
active_page = st.session_state.get('active_nav', 'Home')
active_color = COLOR_MAP.get(active_page, "#4f46e5")

st.markdown(f"""
<style>
/* Design System Tokens */
:root {{
    --primary: #db2777;
    --primary-light: #fce7f3;
    --secondary: #64748b;
    --success: #059669;
    --danger: #ef4444;
    --warning: #f59e0b;
    --violet: #be185d;
    --bg-main: #fff1f2;
    --card-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}}

.stApp {{ background-color: var(--bg-main); }}

/* Sidebar Enhancements */
[data-testid="stSidebar"] {{
    background-color: white !important;
    border-right: 1px solid #e2e8f0 !important;
}}

.sidebar-card {{
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}}

.sidebar-label {{
    font-size: 0.85rem;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 0.5rem;
}}

/* Main Banner Section */
.info-banner {{
    background: linear-gradient(90deg, #db2777 0%, #ec4899 100%);
    padding: 1rem 2rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}}

/* Tab Navigation */
.nav-tabs {{
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    background: white;
    padding: 0.5rem;
    border-radius: 14px;
    box-shadow: var(--card-shadow);
}}

/* Control Card */
.control-card {{
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: var(--card-shadow);
}}

/* Functional Buttons */
.stButton button {{
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}}

.scan-btn button {{
    background: #db2777 !important;
    color: white !important;
    padding: 0.5rem 2rem !important;
    border: none !important;
}}

/* Pink Tools Theme */
[data-testid="stSidebar"] [data-testid="stExpander"] {{
    background-color: #fdf2f8 !important;
    border: 1px solid #fbcfe8 !important;
    border-radius: 10px !important;
}}

/* Sidebar navigate buttons with conditional highlighting */
[data-testid="stSidebar"] button[key^="side_nav_"] {{
    background: #F6A6BB !important;
    color: white !important;
    border: none !important;
}}

/* Active/Dashboard highlight */
[data-testid="stSidebar"] button[key="side_nav_Home"] {{
    background: #be185d !important;
    box-shadow: 0 4px 12px rgba(190, 24, 93, 0.3) !important;
    transform: scale(1.02) !important;
}}

.pytest-btn button {{
    background: #F48FB1 !important;
    color: #880E4F !important;
    border: 1px solid #be185d !important;
}}

/* Dashboard Sub-nav Tabs */
.stButton > button[key^="btn_sub_"] {{
    background: white !important;
    color: #475569 !important;
    border: 1px solid #e2e8f0 !important;
    padding: 0.8rem 0.5rem !important;
    height: auto !important;
    min-height: 3.5rem !important;
    white-space: normal !important;
    word-wrap: break-word !important;
    line-height: 1.1 !important;
    font-size: 0.9rem !important;
}}

div[data-testid="stHorizontalBlock"] .stButton > button {{
    border-radius: 12px !important;
}}

/* Help Cards */
.help-card {{
    height: 100%;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    background: white;
}}

/* Metric Cards */
.metric-box {{
    padding: 1.5rem;
    border-radius: 12px;
    color: white;
    text-align: center;
    box-shadow: var(--card-shadow);
}}

/* Circular Metric Containers */
.circular-metric-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: white;
    border-radius: 50%;
    width: 120px;
    height: 120px;
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
    border: 8px solid #f1f5f9;
    margin: 10px auto;
}}

.circular-value {{ font-size: 1.5rem; font-weight: 800; }}
.circular-label {{ font-size: 0.7rem; color: #64748b; text-transform: uppercase; }}

/* Test Category List */
.test-cat-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.5rem;
    border-radius: 10px;
    margin-bottom: 0.6rem;
    transition: all 0.2s ease;
}}
.test-cat-pass {{ background-color: #f0fdf4; border-left: 5px solid #22c55e; }}
.test-cat-fail {{ background-color: #fef2f2; border-left: 5px solid #ef4444; }}
.test-cat-info {{ display: flex; align-items: center; gap: 1rem; }}
.test-cat-name {{ font-weight: 600; color: #334155; }}
.test-cat-stats {{ font-weight: 700; color: #64748b; }}
.test-cat-pass .test-cat-stats {{ color: #16a34a; }}
.test-cat-fail .test-cat-stats {{ color: #dc2626; }}
.test-cat-icon {{ font-size: 1.2rem; }}

</style>
""", unsafe_allow_html=True)

# ---------------- HELPER FUNCTIONS ----------------
def scan_directory(path):
    """Scans the given directory for python files and parses them."""
    all_functions = []
    all_classes = []
    all_tests = []
    
    if not os.path.exists(path):
         return None, "Path not found!"
    
    # Handle single file scan
    if os.path.isfile(path):
         files_to_scan = [path]
         root_dir = os.path.dirname(path)
    else:
         files_to_scan = []
         root_dir = path
         for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    files_to_scan.append(os.path.join(root, file))

    if not files_to_scan:
        return None, "No Python files found."

    for full_path in files_to_scan:
        try:
            filename = os.path.basename(full_path)
            is_test_file = filename.startswith("test_") or "_test." in filename
            
            funcs, classes, _ = doc_parser.parse_python_file(full_path)
            
            # Add file context
            rel_path = os.path.relpath(full_path, root_dir) if os.path.isdir(path) else os.path.basename(path)
            
            if is_test_file:
                 all_tests.append({"file": rel_path, "full_path": full_path, "count": len(funcs)})
            else:
                for f in funcs:
                    f["file"] = rel_path
                    f["full_path"] = full_path
                    # Enrich with metrics
                    f_metrics = MetricsEngine.compute_function_metrics(f)
                    f.update(f_metrics)
                    all_functions.append(f)
                for c in classes:
                    c["file"] = rel_path
                    c["full_path"] = full_path
                    all_classes.append(c)
        except Exception as e:
            print(f"Error parsing {full_path}: {e}")
            
    # Calculate Project Level Metrics
    agg_stats = MetricsEngine.aggregate_metrics(all_functions, all_classes)
                    
    return all_functions, all_classes, all_tests, agg_stats

def clean_docstring(docstring):
    """Cleans up the LLM-generated docstring."""
    docstring = docstring.strip()
    # 1. Strip Markdown Code Blocks
    if docstring.startswith("```python"):
        docstring = docstring[len("```python"):].strip()
    elif docstring.startswith("```"):
        docstring = docstring[len("```"):].strip()
    if docstring.endswith("```"):
        docstring = docstring[:-3].strip()
        
    # 2. Extract from full function definition if present (common LLM error)
    if docstring.startswith("def ") or docstring.startswith("class "):
        try:
            module = ast.parse(docstring)
            if module.body and isinstance(module.body[0], (ast.FunctionDef, ast.ClassDef)):
                extracted = ast.get_docstring(module.body[0])
                if extracted:
                    docstring = extracted
        except:
            pass 

    # 3. Handle existing quotes
    if (docstring.startswith('"""') and docstring.endswith('"""')) and len(docstring) >= 6:
        docstring = docstring[3:-3]
    elif (docstring.startswith("'''") and docstring.endswith("'''")) and len(docstring) >= 6:
        docstring = docstring[3:-3]
    
    return docstring.strip()

def get_modified_code(file_path, function_name, docstring, parent_class=None):
    """Simulates insertion of docstring and returns the modified code content."""
    try:
        docstring = clean_docstring(docstring)
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        tree = ast.parse("".join(lines))
        target_node = None
        
        for node in ast.walk(tree):
             if parent_class:
                 if isinstance(node, ast.ClassDef) and node.name == parent_class:
                     for sub in node.body:
                         if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name == function_name:
                             target_node = sub
                             break
             else:
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == function_name:
                     target_node = node
                     break
        
        if not target_node:
            return None, f"Item {function_name} not found"

        # Ensure docstring is wrapped in quotes
        wrapped_doc = f'"""\n{docstring}\n"""'
        
        # Analyze with validator
        v_report = validator.analyze_node(target_node)
        
        if isinstance(target_node.body[0], ast.Expr) and isinstance(target_node.body[0].value, ast.Constant) and isinstance(target_node.body[0].value.value, str):
            # Replace existing
            start_line = target_node.body[0].lineno - 1
            end_line = target_node.body[0].end_lineno
            indent = " " * target_node.col_offset + "    "
            doc_lines = wrapped_doc.split('\n')
            indented_lines = [f"{indent}{line}\n" for line in doc_lines]
            lines[start_line:end_line] = indented_lines
        else:
            # Insert new
            indent = " " * target_node.col_offset + "    "
            doc_lines = wrapped_doc.split('\n')
            indented_lines = [f"{indent}{line}\n" for line in doc_lines]
            insert_pos = target_node.body[0].lineno - 1
            lines = lines[:insert_pos] + indented_lines + lines[insert_pos:]

        return "".join(lines), "Success"
    except Exception as e:
        return None, str(e)

def write_docstring_to_file(file_path, function_name, docstring, parent_class=None):
    """Inserts the docstring into the file using a simple AST/Line approach."""
    try:
        modified_code, msg = get_modified_code(file_path, function_name, docstring, parent_class)
        if modified_code is None:
            return False, msg

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_code)
            
        return True, "Success"

    except Exception as e:
        return False, str(e)


# ---------------- SIDEBAR ----------------
if 'active_nav' not in st.session_state:
    st.session_state['active_nav'] = "Home"

def set_nav(p): st.session_state['active_nav'] = p

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("""
        <div style="
            background: #fdf2f8; 
            border: 2px solid #db2777; 
            border-radius: 12px; 
            padding: 1rem; 
            text-align: center;
            margin-bottom: 0.5rem;
        ">
            <div style="color: #db2777; font-weight: bold; font-size: 1.1rem;">AI Code Reviewer</div>
            <div style="color: #be185d; font-size: 0.75rem; margin-top: 0.25rem; font-weight: 500;">Made By Sujana</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")


    # 🧭 Navigate Expander
    # 🧭 Navigation
    st.sidebar.markdown('<div style="font-weight: 600; color: #64748b; margin-bottom: 0.5rem; margin-top: 1rem;">NAVIGATION</div>', unsafe_allow_html=True)
    
    # Map display names to internal names
    NAV_MAP = {
        "🏠 Dashboard": "Home",
        "📄 AI Review": "Docstring", # Renamed for clarity 
        "📊 Metrics": "Metrics",
        "🛡 Validator": "Validation",
        "🧪 Tests": "Tests"
    }
    
    # Reverse map for indexing
    REVERSE_NAV_MAP = {v: k for k, v in NAV_MAP.items()}
    
    # Determine current index
    current_nav = st.session_state.get('active_nav', 'Home')
    current_label = REVERSE_NAV_MAP.get(current_nav, "🏠 Dashboard")
    try:
        nav_index = list(NAV_MAP.keys()).index(current_label)
    except ValueError:
        nav_index = 0

    selected_nav = st.sidebar.radio("Go to:", list(NAV_MAP.keys()), index=nav_index, label_visibility="collapsed", key="nav_radio")
    
    # Update state
    st.session_state['active_nav'] = NAV_MAP[selected_nav]

    # Settings
    with st.sidebar.expander("⚙ Chatbot Settings", expanded=True):
        st.markdown('<div style="font-weight: 600; color: #64748b; margin-bottom: 0.5rem;">CONFIGURATION</div>', unsafe_allow_html=True)
        groq_key_input = st.text_input("Groq API Key", type="password", key="side_groq_key")
        if groq_key_input:
            os.environ["GROQ_API_KEY"] = groq_key_input
        
        doc_style_side = st.selectbox("Docstring style", ["Google", "Numpy", "ReST"], key="side_style_select")
        st.session_state['doc_style'] = doc_style_side
        
        st.divider()
        st.markdown('<div style="font-weight: 600; color: #64748b; margin-bottom: 0.5rem;">SCAN CONTROLS</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Browse Files", accept_multiple_files=True, type=['py'], key="side_file_loader")
        
        st.caption("OR")
        scan_path = st.text_input("Local Path", value=st.session_state.get('active_scan_path', 'examples'), key="side_scan_path")
        
        col_scan1, col_scan2 = st.columns([3, 1])
        with col_scan1:
            if st.button("🚀 Start Scan", type="primary", use_container_width=True):
                # Clear previous results to force refresh
                if 'scan_results' in st.session_state:
                    del st.session_state['scan_results']
                
                with st.spinner("Analyzing..."):
                    # Clear generic cache to ensure fresh read
                    st.cache_data.clear()
                    
                    target_path = scan_path
                    # Check sidebar uploads
                    if uploaded_files:
                        upload_dir = os.path.join(os.path.dirname(__file__), "..", "temp_uploads")
                        os.makedirs(upload_dir, exist_ok=True)
                        # clear old
                        for f in os.listdir(upload_dir): os.remove(os.path.join(upload_dir, f))
                        
                        for uploaded_file in uploaded_files:
                            with open(os.path.join(upload_dir, uploaded_file.name), "wb") as f:
                                f.write(uploaded_file.getbuffer())
                        target_path = upload_dir
                    
                    # DEBUG: Check if file strictly has docstring (for debugging user issue)
                    # st.toast(f"Scanning: {target_path}")
                    
                    # Force reload parser to ensure fresh file reads
                    importlib.reload(doc_parser)

                    f_res, c_res, t_res, agg_stats = scan_directory(target_path)
                    
                    if f_res is not None:
                        st.session_state['scan_results'] = {
                            "functions": f_res, 
                            "classes": c_res, 
                            "tests": t_res,
                            "metrics": agg_stats
                        }
                        st.session_state['active_scan_path'] = target_path
                        st.success(f"Done! {len(f_res)} functions.")
                        st.rerun()
                    else:
                        st.error(f"Failed: {c_res}")
        with col_scan2:
             if st.button("🔄 Reset", use_container_width=True):
                 st.cache_data.clear()
                 if 'scan_results' in st.session_state: del st.session_state['scan_results']
                 st.rerun()

    st.markdown("---")

    # Project Files List
    st.markdown('<div class="sidebar-label" style="margin-bottom: 0;">📂 PROJECT FILES</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="sidebar-card" style="margin-top: 0; padding-top: 0.5rem; background: transparent; border: none;">', unsafe_allow_html=True)
        if 'scan_results' in st.session_state:
            scan_res = st.session_state['scan_results']
            
            # Separate sample/uploaded files from project files
            functions = scan_res.get('functions', [])
            classes = scan_res.get('classes', [])
            tests = scan_res.get('tests', [])
            
            all_files_raw = sorted(list(set(
                [f['file'] for f in functions] + 
                [c['file'] for c in classes] + 
                [t['file'] for t in tests]
            )))
            
            # If scan path contains "temp_uploads" or "examples", we treat them as samples
            active_path = st.session_state.get('active_scan_path', '').lower()
            is_sample_scan = "uploaded" in active_path or "examples" in active_path or "temp_uploads" in active_path
            
            for f in all_files_raw:
                icon = "📦" if is_sample_scan else "📄"
                st.markdown(f"{icon} {f}")
        else:
            st.caption("No files scanned")
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- DATA PREPARATION ----------------
    if 'scan_results' in st.session_state:
        results = st.session_state['scan_results']
        active_funcs = results['functions']
        active_classes = results['classes']
        metrics_agg = results.get('metrics', {})
        
        total_items = len(active_funcs) + len(active_classes)
        documented_items = sum(1 for x in active_funcs + active_classes if x.get('docstring'))
        coverage_score = (documented_items / total_items * 100) if total_items > 0 else 0

        # Unified Clean Data for display
        clean_data = []
        for f in active_funcs:
            display_name = f"{f['parent']}.{f['name']}" if f.get('parent') else f['name']
            # Format complexity: "5 (Good)"
            comp_str = f"{f.get('complexity_score', 1)}"
            if f.get('complexity_rating'): comp_str += f" ({f['complexity_rating']})"
            
            clean_data.append({
                "File": f['file'], "Name": display_name, "InternalName": f['name'],
                "Parent": f.get('parent'), "Type": "Function", 
                "Docstring": "Yes" if f['docstring'] else "No", 
                "Complexity": comp_str,
                "LOC": f.get('loc', 0),
                "Params": f.get('param_count', 0),
                "Exceptions": f.get('exception_count', 0),
                "Full Path": f['full_path'], "Score": 100 if f['docstring'] else 0
            })
        for c in active_classes:
            clean_data.append({
                "File": c['file'], "Name": c['name'], "InternalName": c['name'],
                "Parent": None, "Type": "Class", 
                "Docstring": "Yes" if c['docstring'] else "No", 
                "Complexity": "N/A", "LOC": c.get('loc', 0), "Params": "-", "Exceptions": "-",
                "Full Path": c['full_path'], "Score": 100 if c['docstring'] else 0
            })

# ---------------- MAIN VIEW ----------------
    if st.session_state['active_nav'] == "Home":
        st.markdown('<h1 style="color: #1e293b; margin-bottom: 0.5rem;">🏠 Dashboard</h1>', unsafe_allow_html=True)
        st.caption("AI Code Reviewer - AST Scanning & Analysis")
    
        # Dashboard Results
        if 'scan_results' in st.session_state:
            results = st.session_state['scan_results']
            metrics = results.get('metrics', {})
            
            st.markdown("### 📊 Project Insights")
            
            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Coverage", f"{metrics.get('coverage_pct', 0)}%")
            m2.metric("Functions", metrics.get('total_functions', 0))
            m3.metric("Avg Complexity", f"{metrics.get('avg_complexity', 0):.1f}")
            m4.metric("Exceptions", metrics.get('total_exceptions', 0))
            
            st.markdown("### 🧬 Parsed Structure")
            # Build Rich Table
            rich_data = []
            for f in results['functions']:
                # Use Radon Grade if available
                grade = f.get('complexity_grade', 'N/A')
                comp_score = f.get('complexity_score', 0)
                
                if grade != 'N/A':
                    comp_display = f"{comp_score} (Grade {grade})"
                    severity = "🔴 Critical" if grade in ['C', 'D', 'E', 'F'] else "🟢 Good"
                else:
                    comp = f.get('complexity_rating', 'Good')
                    comp_display = f"{comp_score} ({comp})"
                    loc_rate = f.get('loc_rating', 'Good')
                    severity = "🔴 Critical" if "Critical" in [comp, loc_rate] else "🟡 Warning" if "Warning" in [comp, loc_rate] else "🟢 Good"
                
                rich_data.append({
                    "Function": f['name'],
                    "File": f['file'],
                    "Params": len(f.get('args', [])),
                    "Returns": "✅" if f.get('returns_value') else "❌",
                    "Complexity": comp_display,
                    "Health": severity
                })
            
            st.dataframe(pd.DataFrame(rich_data), use_container_width=True, hide_index=True)
    
        else:
            st.info("👈 **Start Here**: Use the Sidebar to upload files or enter a path, then click 'Start Scan' to see the dashboard.")

    if st.session_state['active_nav'] == "Docstring":
        st.markdown('<h1 style="color: #be185d;">🤖 AI Review</h1>', unsafe_allow_html=True)
        if 'scan_results' not in st.session_state:
            st.warning("⚠️ Please scan a project in the Dashboard first.")
        else:
            results = st.session_state['scan_results']
            funcs = results['functions']
            
            func_options = {f"{f['file']} :: {f['name']}": f for f in funcs}
            selected_label = st.selectbox("Select Function to Review", options=list(func_options.keys()))
            
            if selected_label:
                target = func_options[selected_label]
                
                col_l, col_r = st.columns([1, 1])
                with col_l:
                    st.subheader("Current State")
                    st.code(f"def {target['name']}(...):\n    ...", language="python")
                    st.markdown(f"**Params**: {len(target.get('args', []))} | **Returns**: {target.get('returns_value')}")
                    
                with col_r:
                    st.subheader("AI Generation")
                    style = st.session_state.get('doc_style', 'Google')
                    
                    if st.button("✨ Generate Docstring", key="btn_gen_ai"):
                        with st.spinner("Generating..."):
                            try:
                                with open(target['full_path'], 'r', encoding='utf-8') as f:
                                    all_lines = f.readlines()
                                start = target['lineno'] - 1
                                end = target['end_lineno']
                                func_code = "".join(all_lines[start:end])
                                
                                from core.docstring_engine.generator import generate_docstring
                                gen_doc = generate_docstring(func_code, style=style)
                                
                                st.session_state['last_generated'] = gen_doc
                                st.success("Generated!")
                            except Exception as e:
                                st.error(f"Generation failed: {e}")
    
                    if 'last_generated' in st.session_state:
                        st.text_area("Generated Docstring", st.session_state['last_generated'], height=200)
                        
                        # Apply Logic
                        if st.button("💾 Apply Docstring", type="primary"):
                           success, msg = write_docstring_to_file(target['full_path'], target['name'], st.session_state['last_generated'])
                           if success:
                               st.success(f"Docstring applied to {target['name']}!")
                               # Clear cached docstring to prevent double application
                               del st.session_state['last_generated']
                               st.rerun()
                           else:
                               st.error(f"Failed to apply: {msg}")
    
    if st.session_state['active_nav'] == "Metrics":
        st.markdown('<h1 style="color: #9d174d;">📊 Detailed Metrics</h1>', unsafe_allow_html=True)
        if 'scan_results' in st.session_state:
            results = st.session_state['scan_results']
            metrics = results.get('metrics', {})
            
            # Simple Charts
            if st_echarts:
                 st.caption("Complexity Distribution")
                 # ... (restore chart if needed, or simple placeholders)
                 st.info("Detailed charts enabled.")
            
            st.json(metrics)
        else:
            st.info("Scan project to view metrics.")
    
    if st.session_state['active_nav'] == "Validation":
        st.markdown('<h1 style="color: #ec4899;">🛡 Validator</h1>', unsafe_allow_html=True)
        if 'scan_results' in st.session_state:
            results = st.session_state['scan_results']
            funcs = results['functions']
            
            # 1. High-Level Function Check
            issues = [f for f in funcs if not f['docstring']]
            if issues:
                st.warning(f"Found {len(issues)} undocumented functions.")
            else:
                st.success("All functions documented!")
    
            st.divider()
            st.subheader("Strict PEP 257 Compliance (pydocstyle)")
            
            # 2. Detailed PEP 257 Check per file
            # Get unique files
            unique_files = list(set(f['full_path'] for f in funcs))
            all_violations = []
            
            with st.spinner("Running pydocstyle validation..."):
                for py_file in unique_files:
                    v = validator.validate_file_pep257(py_file)
                    for vio in v:
                        vio['file_name'] = os.path.basename(py_file)
                        all_violations.append(vio)
            
            if all_violations:
                st.error(f"Found {len(all_violations)} style violations.")
                
                # Group by file for cleaner display
                df_vio = pd.DataFrame(all_violations)
                st.dataframe(
                    df_vio[['file_name', 'line', 'code', 'message']], 
                    column_config={
                        "file_name": "File",
                        "line": "Line",
                        "code": "Error Code",
                        "message": "Detail"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No PEP 257 violations found (or pydocstyle not installed).")
    
        else:
            st.info("Scan project to validate.")
    
    if st.session_state['active_nav'] == "Tests":
        st.markdown('<h1 style="color: #6d28d9;">🧪 Test Suite</h1>', unsafe_allow_html=True)
        
        st.info("Run the project's test suite using `pytest`.")
        
        if st.button("▶ Run Tests", type="primary", use_container_width=True):
            with st.spinner("Running tests..."):
                try:
                    import subprocess
                    # Run pytest and capture output
                    # Using sys.executable to ensure we use the same python env
                    cmd = [sys.executable, "-m", "pytest", "--verbose"]
                    # If active scan path is a directory, maybe we should point pytest there?
                    # Usually pytest discovers tests in current dir. Let's just run from current dir or root.
                    
                    # Assuming tests are in 'tests' folder sibling to 'src' or inside 'active_scan_path'
                    # Best effort: Run in current working dir
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        st.success("✅ All Tests Passed!")
                    else:
                        st.error("❌ Some Tests Failed")
                    
                    with st.expander("Detailed Output", expanded=True):
                        st.code(result.stdout + "\n" + result.stderr)
                        
                except Exception as e:
                    st.error(f"Error running tests: {e}")


 