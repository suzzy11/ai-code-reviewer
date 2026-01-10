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
    importlib.reload(groq_review) # Force reload to pick up model changes
    validator = CodeValidator()
except ImportError:
    # Fallback if core path not set
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from core.review_engine import groq_review
    from core.validator.code_validator import CodeValidator
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
                    all_functions.append(f)
                for c in classes:
                    c["file"] = rel_path
                    c["full_path"] = full_path
                    all_classes.append(c)
        except Exception as e:
            print(f"Error parsing {full_path}: {e}")
                    
    return all_functions, all_classes, all_tests

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
    with st.sidebar.expander("🧭 Navigate to", expanded=False):
        nav_items = [
            ("🏠 Dashboard", "Home"),
            ("📄 Generated Docstrings", "Docstring"),
            ("📊 Metrics", "Metrics"),
            ("🛡 Validator", "Validation")
        ]
        for label, page in nav_items:
            # We use the horizontal tabs as primary nav, but keep this for quick jump/compatibility
            if st.button(label, key=f"side_nav_{page}", use_container_width=True):
                st.session_state['active_nav'] = page
                st.rerun()

    # Settings & AST Scan
    with st.sidebar.expander("⚙ Settings & Scan", expanded=False):
        st.markdown('<div style="font-weight: 600; color: #64748b; margin-bottom: 0.5rem;">CONFIGURATION</div>', unsafe_allow_html=True)
        groq_key_input = st.text_input("Groq API Key", type="password", key="side_groq_key")
        if groq_key_input:
            os.environ["GROQ_API_KEY"] = groq_key_input
        
        doc_style_side = st.selectbox("Docstring style", ["Google", "Numpy", "ReST"], key="side_style_select")
        st.session_state['doc_style'] = doc_style_side
        
        st.divider()
        st.markdown('<div style="font-weight: 600; color: #64748b; margin-bottom: 0.5rem;">ENGINE CONTROLS</div>', unsafe_allow_html=True)
        scan_p = st.text_input("Path to scan", value=st.session_state.get('active_scan_path', 'examples'), key="engine_scan_path")
        uploaded_files = st.file_uploader("Browse Files", accept_multiple_files=True, type=['py'], key="side_file_loader")
        
        if st.button("🔍 Start AST Scan", use_container_width=True, type="primary"):
            with st.spinner("Analyzing..."):
                if uploaded_files:
                    upload_dir = os.path.join(os.path.dirname(__file__), "..", "temp_uploads")
                    os.makedirs(upload_dir, exist_ok=True)
                    for uploaded_file in uploaded_files:
                        with open(os.path.join(upload_dir, uploaded_file.name), "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    scan_p = upload_dir
                
                f_res, c_res, t_res = scan_directory(scan_p)
                if f_res is not None:
                    st.session_state['scan_results'] = {"functions": f_res, "classes": c_res, "tests": t_res}
                    st.session_state['active_scan_path'] = scan_p if not uploaded_files else "Uploaded Files"
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
    total_items = len(active_funcs) + len(active_classes)
    documented_items = sum(1 for x in active_funcs + active_classes if x.get('docstring'))
    coverage_score = (documented_items / total_items * 100) if total_items > 0 else 0

    # Unified Clean Data for display
    clean_data = []
    for f in active_funcs:
        display_name = f"{f['parent']}.{f['name']}" if f.get('parent') else f['name']
        clean_data.append({
            "File": f['file'], "Name": display_name, "InternalName": f['name'],
            "Parent": f.get('parent'), "Type": "Function", 
            "Docstring": "Yes" if f['docstring'] else "No", 
            "Full Path": f['full_path'], "Score": 100 if f['docstring'] else 0
        })
    for c in active_classes:
        clean_data.append({
            "File": c['file'], "Name": c['name'], "InternalName": c['name'],
            "Parent": None, "Type": "Class", 
            "Docstring": "Yes" if c['docstring'] else "No", 
            "Full Path": c['full_path'], "Score": 100 if c['docstring'] else 0
        })

# ---------------- MAIN VIEW ----------------
st.markdown('<h1 style="color: #1e293b; margin-bottom: 2rem;">🚀 AI Code Reviewer Chatbot</h1>', unsafe_allow_html=True)

st.markdown("---")

# 2. Horizontal Navigation Tabs (Synced)
tabs_labels = ["⚡ Dashboard", "📄 Generated Docstrings", "📊 Metrics", "🛡 Validator"]
tabs_values = ["Home", "Docstring", "Metrics", "Validation"]

# Get index of current active_nav
try:
    default_tab_idx = tabs_values.index(st.session_state['active_nav'])
except:
    default_tab_idx = 0

# Use a container to hold the tabs
# We can't easily force st.tabs to change from outside, so we use it as a 
# secondary switcher that UPDATES active_nav, or vice versa.
selected_tab = st.radio("Navigation", tabs_labels, index=default_tab_idx, horizontal=True, label_visibility="collapsed")
st.session_state['active_nav'] = tabs_values[tabs_labels.index(selected_tab)]

# Render content based on active_nav
if st.session_state['active_nav'] == "Home":
    # Dashboard Header with Highlight
    st.markdown("""
        <div class="info-banner" style="background: linear-gradient(135deg, #be185d 0%, #db2777 100%); border-left: 8px solid #fce7f3; box-shadow: 0 10px 15px -3px rgba(190, 24, 93, 0.2);">
            <span style="font-size: 1.5rem;">📟</span> 
            <div>
                <div style="font-weight: 800; font-size: 1.2rem;">Dashboard</div>
                <div style="font-size: 0.8rem; opacity: 0.9;">Project Overview & Management</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Relocated Metrics
    me1, me2 = st.columns([1, 1])
    if 'scan_results' in st.session_state:
        with me1:
            st.markdown(f"""
                <div class="circular-metric-container">
                    <div class="circular-value">{coverage_score:.1f}%</div>
                    <div class="circular-label">Coverage</div>
                </div>
            """, unsafe_allow_html=True)
        with me2:
            st.markdown(f"""
                <div class="circular-metric-container">
                    <div class="circular-value">{total_items}</div>
                    <div class="circular-label">Functions</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        with me1: st.markdown('<div class="circular-metric-container"><div class="circular-value">0%</div><div class="circular-label">Coverage</div></div>', unsafe_allow_html=True)
        with me2: st.markdown('<div class="circular-metric-container"><div class="circular-value">0</div><div class="circular-label">Functions</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
    
    # Sub-nav for Dashboard
    sub_col1, sub_col2, sub_col3, sub_col4, sub_col5 = st.columns(5)
    d_mode = st.session_state.get('dashboard_sub', 'Filters')

    with sub_col1:
        if st.button("🔧 Advanced Filters", key="btn_sub_filters", use_container_width=True, type="secondary" if d_mode != "Filters" else "primary"): 
            st.session_state['dashboard_sub'] = 'Filters'
            st.rerun()
    with sub_col2:
        if st.button("🔍 Search", key="btn_sub_search", use_container_width=True, type="secondary" if d_mode != "Search" else "primary"): 
            st.session_state['dashboard_sub'] = 'Search'
            st.rerun()
    with sub_col3:
        if st.button("📤 Export", key="btn_sub_export", use_container_width=True, type="secondary" if d_mode != "Export" else "primary"): 
            st.session_state['dashboard_sub'] = 'Export'
            st.rerun()
    with sub_col4:
        if st.button("🧪 Tests", key="btn_sub_tests", use_container_width=True, type="secondary" if d_mode != "Tests" else "primary"): 
            st.session_state['dashboard_sub'] = 'Tests'
            st.rerun()
    with sub_col5:
        if st.button("💡 Help and Tips", key="btn_sub_help", use_container_width=True, type="secondary" if d_mode != "Help" else "primary"): 
            st.session_state['dashboard_sub'] = 'Help'
            st.rerun()

    st.divider()

    if d_mode == "Filters":
        st.markdown('<div class="info-banner" style="background: var(--primary);"><span>🔧</span> <b>Advanced Filters</b></div>', unsafe_allow_html=True)
        st.info("Filter dynamically by file, function, and documentation status")
        
        if 'scan_results' in st.session_state:
            f1, f2 = st.columns(2)
            with f1:
                sel_file = st.multiselect("Filter by File", options=sorted(list(set(r['File'] for r in clean_data))))
            with f2:
                sel_status = st.selectbox("Documentation Status", ["All", "Documented", "Undocumented"])
            
            filtered_df = pd.DataFrame(clean_data)
            if sel_file:
                filtered_df = filtered_df[filtered_df['File'].isin(sel_file)]
            if sel_status == "Documented":
                filtered_df = filtered_df[filtered_df['Docstring'] == "Yes"]
            elif sel_status == "Undocumented":
                filtered_df = filtered_df[filtered_df['Docstring'] == "No"]
            
            st.dataframe(filtered_df.drop(columns=["Full Path", "InternalName", "Parent"]), use_container_width=True, hide_index=True)
        else:
            st.info("Scan a project to see filters.")
            
    elif d_mode == "Search":
        st.markdown('<div class="info-banner" style="background: #0ea5e9;"><span>🔍</span> <b>Search</b></div>', unsafe_allow_html=True)
        q = st.text_input("Search for functions or classes...", placeholder="e.g. login_user")
        
        if 'scan_results' in st.session_state:
            search_res = [r for r in clean_data if q.lower() in r['Name'].lower() or q.lower() in r['File'].lower()]
            if search_res:
                st.dataframe(pd.DataFrame(search_res).drop(columns=["Full Path", "InternalName", "Parent"]), use_container_width=True, hide_index=True)
            else:
                st.warning("No matches found.")
        else:
            st.info("Scan a project to search.")

    elif d_mode == "Export":
        st.markdown('<div class="info-banner" style="background: #8b5cf6;"><span>📤</span> <b>Export Report</b></div>', unsafe_allow_html=True)
        if 'scan_results' in st.session_state:
            df_exp = pd.DataFrame(clean_data)
            ec1, ec2 = st.columns(2)
            with ec1:
                st.download_button("📊 Export to CSV", df_exp.to_csv(index=False), "ai_review_report.csv", "text/csv", use_container_width=True)
            with ec2:
                st.download_button("📥 Export to JSON", json.dumps(clean_data, indent=2), "ai_review_report.json", "application/json", use_container_width=True)
            
            st.markdown("#### Report Preview")
            st.dataframe(df_exp.drop(columns=["Full Path", "InternalName", "Parent"]).head(10), use_container_width=True, hide_index=True)
        else:
            st.info("Scan a project to export data.")

    elif d_mode == "Tests":
        # --- TEST CATEGORY MAPPING ---
        CATEGORY_MAP = {
            'test_parser.py': 'Parser Tests',
            'test_validator.py': 'Validator Tests',
            'test_integration.py': 'LLM Integration Tests',
            'test_integration_new.py': 'LLM Integration Tests',
            'test_report.py': 'Coverage Reporter Tests',
            'test_main.py': 'Dashboard Tests',
            'test_generator.py': 'Generator Tests',
            'parser.py': 'Parser Tests',
            'py_parser.py': 'Parser Tests',
            'code_validator.py': 'Validator Tests',
            'groq_review.py': 'LLM Integration Tests',
            'docstring_generator.py': 'Generator Tests',
            'main.py': 'Dashboard Tests',
            'report.py': 'Coverage Reporter Tests',
            'test.py': 'General Tests'
        }
        DEFAULT_CATEGORY = 'Other Tests'

        # --- TEST RESULTS UI ---
        st.markdown('<div class="info-banner" style="background: #880E4F; margin-bottom: 0.5rem;"><span>🧪</span> <b>Execution Report</b></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="pytest-btn">', unsafe_allow_html=True)
        if st.button("▶ Run Pytest Suite", type="primary", use_container_width=True):
            with st.spinner("Running tests..."):
                import subprocess
                import sys
                import json
                try:
                    # Run pytest on the current active folder
                    path = st.session_state.get('active_scan_path', 'tests')
                    
                    # Smart Path: If scanning a single non-test file, run 'tests' instead
                    is_file = os.path.isfile(path)
                    is_test_file = os.path.basename(path).startswith("test_") or "_test." in path
                    
                    if is_file and not is_test_file:
                        path = 'tests'
                    
                    if not os.path.exists(path): path = 'tests'
                    
                    # Ensure path exists before running
                    if not os.path.exists(path):
                        st.error(f"Test path '{path}' not found. Please ensure project is scanned correctly.")

                    # Use absolute paths for the report to avoid Windows issues
                    report_path = os.path.abspath("storage/test_report.json")
                    if os.path.exists(report_path):
                        try: os.remove(report_path)
                        except: pass
                    
                    os.makedirs(os.path.dirname(report_path), exist_ok=True)
                    
                    # Use sys.executable to ensure we use the same python environment
                    # Using --json-report for structured output
                    # Include src directory to find integration tests
                    result = subprocess.run([
                        sys.executable, "-m", "pytest", path, "src",
                        "--tb=short", "--json-report", f"--json-report-file={report_path}"
                    ], capture_output=True, text=True)
                    
                    # Capture both stdout and stderr for better debugging
                    st.session_state['last_test_output'] = result.stdout + "\n" + result.stderr
                    
                    if os.path.exists(report_path):
                        with open(report_path, 'r') as f:
                            report_data = json.load(f)
                        
                        summary = report_data.get('summary', {})
                        st.session_state['test_stats'] = {
                            "passed": summary.get('passed', 0),
                            "failed": summary.get('failed', 0),
                            "total": summary.get('total', 0),
                            "duration": f"{report_data.get('duration', 0):.2f}s"
                        }
                        
                        # Populate detailed test data for bar chart
                        details = []
                        tests = report_data.get('tests', [])
                        
                        # Pre-populate all categories as 0 to ensure they appear on the graph
                        category_results = {cat: {'passed': 0, 'failed': 0} for cat in set(CATEGORY_MAP.values())}
                        if DEFAULT_CATEGORY not in category_results:
                            category_results[DEFAULT_CATEGORY] = {'passed': 0, 'failed': 0}

                        for t in tests:
                            nodeid = t.get('nodeid', '')
                            fname = os.path.basename(nodeid.split('::')[0])
                            outcome = t.get('outcome', 'passed')
                            
                            category = CATEGORY_MAP.get(fname, DEFAULT_CATEGORY)
                            
                            if category not in category_results:
                                category_results[category] = {'passed': 0, 'failed': 0}
                            
                            if outcome == 'passed': category_results[category]['passed'] += 1
                            else: category_results[category]['failed'] += 1
                        
                        for cat, stats in category_results.items():
                            details.append({
                                'category': cat,
                                'passed': stats['passed'],
                                'failed': stats['failed']
                            })
                        details.sort(key=lambda x: x['category'])
                        st.session_state['detailed_tests'] = details
                        st.success("Test run completed!")
                    else:
                        # Fallback to regex if JSON report failed
                        import re
                        passed_m = re.search(r'(\d+) passed', result.stdout)
                        failed_m = re.search(r'(\d+) failed', result.stdout)
                        error_m = re.search(r'ERROR: (.*)', result.stdout + result.stderr)
                        
                        p_count = int(passed_m.group(1)) if passed_m else 0
                        f_count = int(failed_m.group(1)) if failed_m else 0
                        
                        st.session_state['test_stats'] = {
                            "passed": p_count,
                            "failed": f_count,
                            "total": p_count + f_count,
                            "duration": "N/A"
                        }
                        st.session_state['detailed_tests'] = []
                        if error_m:
                            st.warning(f"JSON report failed. Pytest Error: {error_m.group(1)}")
                        else:
                            st.warning("JSON report not generated. Using text fallback.")
                except Exception as e:
                    st.error(f"Error running tests: {e}")

        st.markdown('</div>', unsafe_allow_html=True)
        
        stats = st.session_state.get('test_stats', {"passed": 0, "failed": 0, "total": 0, "duration": "0s"})
        
        # Metric Cards Row
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        with m_c1: st.markdown(f'<div class="metric-box" style="background: #B388EB;"><h3>{stats["passed"]}</h3><small>PASSED</small></div>', unsafe_allow_html=True)
        with m_c2: st.markdown(f'<div class="metric-box" style="background: #F7AEF8;"><h3>{stats["failed"]}</h3><small>FAILED</small></div>', unsafe_allow_html=True)
        with m_c3: st.markdown(f'<div class="metric-box" style="background: #F6A6BB;"><h3>{stats["passed"] + stats["failed"]}</h3><small>TOTAL</small></div>', unsafe_allow_html=True)
        with m_c4: st.markdown(f'<div class="metric-box" style="background: #F06292;"><h3>{stats.get("duration", "N/A")}</h3><small>DURATION</small></div>', unsafe_allow_html=True)
        
        if 'last_test_output' in st.session_state:
            with st.expander("📝 Detailed Console Output", expanded=False):
                st.code(st.session_state['last_test_output'])

        st.markdown("#### 📊 Tests by Category")
        detailed_data = st.session_state.get('detailed_tests', [])
        
        if not detailed_data:
             test_labels = ["No Data"]
             passed_counts = [0]
             failed_counts = [0]
        else:
             test_labels = [d['category'] for d in detailed_data]
             passed_counts = [d['passed'] for d in detailed_data]
             failed_counts = [d['failed'] for d in detailed_data]
        
        if st_echarts:
            options = {
                "tooltip": {"trigger": 'axis', "axisPointer": {"type": 'shadow'}},
                "legend": {"data": ['Passed', 'Failed'], "top": "bottom"},
                "grid": {"left": '3%', "right": '4%', "bottom": '15%', "containLabel": True},
                "xAxis": {"type": 'category', "data": test_labels, "axisLabel": {"interval": 0, "rotate": 30}},
                "yAxis": {"type": 'value'},
                "series": [
                    {"name": 'Passed', "type": 'bar', "stack": 'total', "color": '#B388EB', "data": passed_counts, "label": {"show": True, "position": "top"}},
                    {"name": 'Failed', "type": 'bar', "stack": 'total', "color": '#F7AEF8', "data": failed_counts, "label": {"show": True, "position": "top"}}
                ]
            }
            st_echarts(options, height="400px", key="test_tab_chart")
        else:
             if detailed_data:
                 chart_df = pd.DataFrame(detailed_data).set_index('category')
                 st.bar_chart(chart_df[['passed', 'failed']], color=["#B388EB", "#F7AEF8"])
             else:
                 st.info("No detailed test data available to chart.")
        
        # --- DETAILED LIST VIEW ---
        st.markdown("#### 📋 Test Results by Category")
        if detailed_data:
             for d in detailed_data:
                 status_class = "test-cat-pass" if d['failed'] == 0 else "test-cat-fail"
                 icon = "✅" if d['failed'] == 0 else "❌"
                 total = d['passed'] + d['failed']
                 
                 st.markdown(f"""
                    <div class="test-cat-row {status_class}">
                        <div class="test-cat-info">
                            <span class="test-cat-icon">{icon}</span>
                            <span class="test-cat-name">{d['category']}</span>
                        </div>
                        <div class="test-cat-stats">
                            {d['passed']}/{total} passed
                        </div>
                    </div>
                 """, unsafe_allow_html=True)
        else:
             st.info("No test results to display. Click 'Run Pytest Suite' to begin.")
        
    elif d_mode == "Help":
        # --- HELP & TIPS UI ---
        st.markdown('<div class="info-banner" style="background: #fbbf24; color: #92400e;"><span>💡</span> <b>Help and Tips</b></div>', unsafe_allow_html=True)
        
        h_col1, h_col2 = st.columns(2)
        with h_col1:
            st.markdown("""
                <div class="help-card">
                    <h4 style="color: #10b981;">🚀 Getting Started</h4>
                    <ul style="font-size: 0.9rem; color: #475569;">
                        <li>Open <b>Settings & Scan</b> in the sidebar</li>
                        <li>Enter a codebase path and click <b>Start AST Scan</b></li>
                        <li>The app will automatically analyze functions and classes</li>
                        <li>Metrics will update at the top of the main window</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
            st.markdown("""
                <div class="help-card">
                    <h4 style="color: #0ea5e9;">🔧 Function Status</h4>
                    <ul style="font-size: 0.9rem; color: #475569;">
                        <li>🟢 <b>OK</b>: Function has valid docstring</li>
                        <li>🔴 <b>Fix</b>: Missing or invalid docstring</li>
                        <li>Use <b>Generated Docstrings</b> tab to preview & apply fixes</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        with h_col2:
            st.markdown("""
                <div class="help-card">
                    <h4 style="color: #f59e0b;">📄 Docstring Styles</h4>
                    <ul style="font-size: 0.9rem; color: #475569;">
                        <li><b>Google</b>: Args, Returns, Raises sections</li>
                        <li><b>NumPy</b>: Parameters, Returns with dashes</li>
                        <li><b>reST</b>: :param, :type, :return directives</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
            st.markdown("""
                <div class="help-card">
                    <h4 style="color: #8b5cf6;">📤 Export Options</h4>
                    <ul style="font-size: 0.9rem; color: #475569;">
                        <li><b>JSON</b>: Structured data for programmatic access</li>
                        <li><b>CSV</b>: Spreadsheet-friendly analysis</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

    # Dashboard Page Rendered (Already in the main block)
    pass

elif st.session_state['active_nav'] == "Docstring":
    st.markdown('<div class="info-banner"><span>📄</span> <b>Generated Docstrings</b></div>', unsafe_allow_html=True)
    if 'scan_results' in st.session_state:
        # Existing review logic
        item_options = [f"{r['File']} : {r['Name']}" for r in clean_data]
        selected_item_str = st.selectbox("Select Item to Review", item_options)
        
        # Clear generated doc if selection changes
        if 'last_selected_item' in st.session_state and st.session_state['last_selected_item'] != selected_item_str:
            if 'generated_doc' in st.session_state:
                del st.session_state['generated_doc']
        st.session_state['last_selected_item'] = selected_item_str
        
        if selected_item_str:
            selected_row = next((item for item in clean_data if f"{item['File']} : {item['Name']}" == selected_item_str), None)
            if selected_row:
                file_path = selected_row['Full Path']
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                
                with st.expander("📄 Source Code", expanded=True):
                    st.code(code_content, language='python')
                
                c_act1, c_act2 = st.columns([1, 2])
                with c_act1:
                    d_style = st.selectbox("Style", ["Google", "Numpy", "ReST"], key="tab_doc_style")
                    if st.button("✨ Generate", key="tab_gen_btn"):
                        if not os.environ.get("GROQ_API_KEY"): st.error("API Key missing")
                        else:
                            with st.spinner("Generating..."):
                                prompt = f"File: {selected_row['File']}\nCode:\n{code_content}\n\nGENERATE DOCSTRING ONLY FOR: {selected_row['Name']}"
                                generated = groq_review.generate_docstring(prompt, d_style)
                                st.session_state['generated_doc'] = generated.strip()
                
                with c_act2:
                    if 'generated_doc' in st.session_state:
                        # Allow user to edit the generated docstrip
                        st.session_state['generated_doc'] = st.text_area(
                            "Summary", 
                            st.session_state['generated_doc'], 
                            height=200,
                            help="You can edit the docstring here before applying."
                        )
                
                        st.divider()
                        st.subheader("🔍 Preview Changes")
                        
                        modified_code_preview, msg = get_modified_code(file_path, selected_row['InternalName'], st.session_state['generated_doc'], selected_row.get('Parent'))
                        p_col1, p_col2 = st.columns(2)
                        with p_col1:
                            st.caption("Current Code")
                            st.code(code_content, language='python')
                        with p_col2:
                            st.caption("Preview with Docstring")
                            if modified_code_preview: st.code(modified_code_preview, language='python')
                            else: st.error(f"Could not generate preview: {msg}")
                        
                        if st.button("✅ Accept & Apply", use_container_width=True, type="primary", key="tab_apply_btn"):
                            success, apply_msg = write_docstring_to_file(file_path, selected_row['InternalName'], st.session_state['generated_doc'], selected_row.get('Parent'))
                            if success: 
                                st.success("Documentation applied successfully!")
                                del st.session_state['generated_doc']
                                st.rerun()
                            else: st.error(f"Failed to apply: {apply_msg}")
    else:
        st.info("Scan your project to generate docstrings.")

elif st.session_state['active_nav'] == "Metrics":
    st.markdown('<div class="info-banner" style="background: #db2777;"><span>📊</span> <b>Metrics</b></div>', unsafe_allow_html=True)
    if 'scan_results' in st.session_state:
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Coverage Ring")
            if st_echarts:
                options = {
                    "tooltip": {"formatter": '{a} <br/>{b} : {c}%'},
                    "series": [{
                        "name": 'Coverage',
                        "type": 'gauge',
                        "startAngle": 90, "endAngle": -270,
                        "pointer": {"show": False},
                        "progress": {"show": True, "overlap": False, "roundCap": True, "clip": False},
                        "axisLine": {"lineStyle": {"width": 20}},
                        "splitLine": {"show": False},
                        "axisTick": {"show": False},
                        "axisLabel": {"show": False},
                        "data": [{"value": round(coverage_score, 1), "name": 'Doc Coverage'}],
                        "detail": {"width": 50, "height": 14, "fontSize": 18, "color": 'auto', "formatter": '{value}%'}
                    }]
                }
                st_echarts(options, height="280px", key="tab_coverage_ring")
            else:
                st.progress(coverage_score / 100)
                st.write(f"**{coverage_score:.1f}%** Documentation Coverage")
        with col2:
            st.caption("Type Distribution")
            dist = pd.DataFrame(clean_data)["Type"].value_counts()
            st.bar_chart(dist, color="#F6A6BB")
    else:
        st.info("Scan your project to view metrics.")

elif st.session_state['active_nav'] == "Validation":
    st.markdown('<div class="info-banner" style="background: #be185d;"><span>🛡</span> <b>Validator</b></div>', unsafe_allow_html=True)
    if 'scan_results' in st.session_state:
        vdf = pd.DataFrame(clean_data)
        st.dataframe(vdf[["File", "Name", "Type", "Docstring", "Score"]], use_container_width=True, hide_index=True)
        
        d_c1, d_c2 = st.columns(2)
        with d_c1: st.download_button("📊 Download CSV Report", vdf.to_csv(index=False), "validation_report.csv", "text/csv", use_container_width=True)
        with d_c2: st.download_button("📥 Download JSON Report", json.dumps(clean_data, indent=2), "validation_report.json", "application/json", use_container_width=True)
        
        st.divider()
        st.markdown("### 🔍 Issues Found")
        undocumented = [r for r in clean_data if r['Docstring'] == "No"]
        if undocumented:
            for item in undocumented:
                st.markdown(f"- ❌ `{item['Name']}` in `{item['File']}` is missing documentation.")
        else: st.success("✨ All scanned items are documented!")
    else:
        st.info("Scan your project to validate documentation.")


 