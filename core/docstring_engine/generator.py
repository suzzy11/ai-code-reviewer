import functools
import ast
import hashlib
import os
import re
from typing import Dict, Any, Set
from core.review_engine.groq_review import generate_docstring as groq_gen_func
from core.review_engine.groq_review import generate_module_docstring as groq_gen_mod

# ----------------- D401 IMPERATIVE MOOD FIXES -----------------
# Comprehensive mapping from third-person singular to imperative form
_IMPERATIVE_FIXES = {
    "Raises": "Raise", "Returns": "Return", "Yields": "Yield",
    "Calculates": "Calculate", "Computes": "Compute", "Creates": "Create",
    "Generates": "Generate", "Gets": "Get", "Sets": "Set",
    "Checks": "Check", "Validates": "Validate", "Parses": "Parse",
    "Processes": "Process", "Handles": "Handle", "Executes": "Execute",
    "Performs": "Perform", "Builds": "Build", "Initializes": "Initialize",
    "Converts": "Convert", "Extracts": "Extract", "Loads": "Load",
    "Saves": "Save", "Writes": "Write", "Reads": "Read",
    "Sends": "Send", "Receives": "Receive", "Updates": "Update",
    "Deletes": "Delete", "Removes": "Remove", "Adds": "Add",
    "Inserts": "Insert", "Finds": "Find", "Searches": "Search",
    "Sorts": "Sort", "Filters": "Filter", "Maps": "Map",
    "Reduces": "Reduce", "Transforms": "Transform", "Applies": "Apply",
    "Runs": "Run", "Starts": "Start", "Stops": "Stop",
    "Opens": "Open", "Closes": "Close", "Connects": "Connect",
    "Formats": "Format", "Prints": "Print", "Logs": "Log",
    "Tests": "Test", "Verifies": "Verify", "Determines": "Determine",
    "Evaluates": "Evaluate", "Fetches": "Fetch", "Retrieves": "Retrieve",
    "Stores": "Store", "Caches": "Cache", "Clears": "Clear",
    "Resets": "Reset", "Copies": "Copy", "Moves": "Move",
    "Merges": "Merge", "Splits": "Split", "Joins": "Join",
    "Appends": "Append", "Wraps": "Wrap", "Encodes": "Encode",
    "Decodes": "Decode", "Encrypts": "Encrypt", "Decrypts": "Decrypt",
    "Serializes": "Serialize", "Deserializes": "Deserialize",
    "Normalizes": "Normalize", "Sanitizes": "Sanitize",
    "Configures": "Configure", "Registers": "Register",
    "Enables": "Enable", "Disables": "Disable",
    "Displays": "Display", "Renders": "Render", "Shows": "Show",
    "Hides": "Hide", "Toggles": "Toggle", "Switches": "Switch",
    "Provides": "Provide", "Defines": "Define", "Describes": "Describe",
    "Implements": "Implement", "Extends": "Extend", "Overrides": "Override",
}

# ----------------- METADATA ANALYSIS -----------------
def analyze_code_metadata(source_code: str) -> Dict[str, Any]:
    """
    Analyzes code to determine if it truly returns, yields, or raises.
    Matches logic from src/py_parser.py to ensure consistency.
    """
    metadata = {
        "has_return": False,
        "has_yield": False,
        "raised_exceptions": set(),
        "params": []
    }
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            # 1. Return Value Detection
            if isinstance(node, ast.Return) and node.value is not None:
                if not (isinstance(node.value, ast.Constant) and node.value.value is None):
                    metadata["has_return"] = True
            
            # 2. Generator Detection
            elif isinstance(node, (ast.Yield, ast.YieldFrom)):
                metadata["has_yield"] = True
            
            # 3. Exception Detection
            elif isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                    metadata["raised_exceptions"].add(node.exc.func.id)
                elif isinstance(node.exc, ast.Name):
                    metadata["raised_exceptions"].add(node.exc.id)
            
            # 4. Params
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not metadata["params"]: # Only capture top-level func params
                    metadata["params"] = [a.arg for a in node.args.args if a.arg != 'self']

            # 5. Class Params (from __init__)
            elif isinstance(node, ast.ClassDef):
                if not metadata["params"]:
                    for subnode in node.body:
                        if isinstance(subnode, ast.FunctionDef) and subnode.name == "__init__":
                             metadata["params"] = [a.arg for a in subnode.args.args if a.arg != 'self']
                             break
    except:
        # If partial code or error, fail safe
        metadata["has_return"] = True 
        metadata["has_yield"] = True
        
    return metadata

# ----------------- CACHING -----------------
@functools.lru_cache(maxsize=128)
def _cached_gen(source_hash: str, style: str, source_code: str, is_module: bool) -> str:
    if is_module:
        return groq_gen_mod(source_code, style)
    return groq_gen_func(source_code, style)

# ----------------- CLEANING & POST-PROCESSING -----------------
def clean_docstring(docstring: str, metadata: Dict[str, Any] = None) -> str:
    """Post-processes AI output for Hallucination Control & Cleanup."""
    if not docstring: return ""
    
    docstring = docstring.strip()
    
    # 1. Remove AI conversational filler
    docstring = re.sub(r"^(Here is|Sure|I have generated|Generated by AI).+?(\n|$)", "", docstring, flags=re.IGNORECASE).strip()
    
    # 2. Strip markdown code blocks
    if docstring.startswith("```"):
        docstring = re.sub(r"^```[a-z]*\s*", "", docstring)
        docstring = re.sub(r"\s*```$", "", docstring)
    docstring = docstring.strip()
    
    # 3. Extract docstring from wrapper function/class
    if docstring.startswith("def ") or docstring.startswith("class "):
        try:
            m = ast.parse(docstring)
            if m.body and isinstance(m.body[0], (ast.FunctionDef, ast.ClassDef)):
                d = ast.get_docstring(m.body[0])
                if d: docstring = d
        except: pass

    # 4. Clean quotes
    if (docstring.startswith('"""') and docstring.endswith('"""')) and len(docstring) >= 6:
        docstring = docstring[3:-3]
    elif (docstring.startswith("'''") and docstring.endswith("'''")) and len(docstring) >= 6:
        docstring = docstring[3:-3]
        
    docstring = docstring.strip()
    if not docstring: return ""

    # ----------------- HALLUCINATION CONTROL -----------------
    if metadata:
        # A. Strip Returns/Yields
        if not metadata["has_return"]:
            # Google/ReST: Returns: ...
            docstring = re.sub(r"\n\s*Returns:\s*\n.+?(\n\n|$)", "\n\n", docstring, flags=re.DOTALL)
            # Numpy: Returns\n-------
            docstring = re.sub(r"\n\s*Returns\n\s*-+\s*\n.+?(\n\n|$)", "\n\n", docstring, flags=re.DOTALL)
            # ReST field
            docstring = re.sub(r"\n\s*:return:.+?(\n|$)", "\n", docstring)

        if not metadata["has_yield"]:
            docstring = re.sub(r"\n\s*Yields:\s*\n.+?(\n\n|$)", "\n\n", docstring, flags=re.DOTALL)
            docstring = re.sub(r"\n\s*Yields\n\s*-+\s*\n.+?(\n\n|$)", "\n\n", docstring, flags=re.DOTALL)

        # B. Strip Raises if empty or verify content
        if not metadata["raised_exceptions"]:
             docstring = re.sub(r"\n\s*Raises:\s*\n.+?(\n\n|$)", "\n\n", docstring, flags=re.DOTALL)
             docstring = re.sub(r"\n\s*Raises\n\s*-+\s*\n.+?(\n\n|$)", "\n\n", docstring, flags=re.DOTALL)
             docstring = re.sub(r"\n\s*:raises:.+?(\n|$)", "\n", docstring)
        else:
            # TODO: Advanced: Scan lines in Raises section and remove those not in metadata['raised_exceptions']
            pass

    # 5. Remove Forbidden Sections
    forbidden = ["Examples", "Example", "Notes", "See Also"]
    for section in forbidden:
        # Google style
        docstring = re.sub(rf"\n\s*{section}:\s*\n.+?(\n\n|$)", "\n\n", docstring, flags=re.DOTALL)
        # Numpy style
        docstring = re.sub(rf"\n\s*{section}\n\s*-+\s*\n.+?(\n\n|$)", "\n\n", docstring, flags=re.DOTALL)

    # ----------------- PEP 257 ENFORCEMENT -----------------
    lines = docstring.split('\n')
    if lines:
        summary = lines[0]
        
        # A. Remove "This function..."
        if summary.lower().startswith("this function") or summary.lower().startswith("this module"):
             summary = re.sub(r"^This (function|module|class|method) ", "", summary, flags=re.IGNORECASE)
        
        # B. Imperative Mood (D401) - Use comprehensive dictionary
        words = summary.split(' ', 1)
        if words:
            first_word = words[0]
            if first_word in _IMPERATIVE_FIXES:
                imperative = _IMPERATIVE_FIXES[first_word]
                if len(words) > 1:
                    summary = imperative + ' ' + words[1]
                else:
                    summary = imperative

        # C. Capitalize first letter
        if summary and summary[0].islower():
            summary = summary[0].upper() + summary[1:]

        # D. End with period
        if summary and summary.strip() and summary.strip()[-1] not in ".!?:":
            summary = summary.strip() + "."
            
        lines[0] = summary
        docstring = "\n".join(lines)

    return docstring.strip()

# ----------------- PUBLIC API -----------------

def generate_docstring(source_code: str, style: str = "google") -> str:
    """Generates and cleans a function/class docstring with hallucination control."""
    h = hashlib.md5(source_code.encode("utf-8")).hexdigest()
    raw = _cached_gen(h, style, source_code, is_module=False)
    
    metadata = analyze_code_metadata(source_code)
    return clean_docstring(raw, metadata)

def generate_module_docstring(source_code: str, style: str = "google") -> str:
    """Generates and cleans a module-level docstring."""
    h = hashlib.md5(source_code.encode("utf-8")).hexdigest()
    raw = _cached_gen(h, style, source_code, is_module=True)
    return clean_docstring(raw)

def insert_module_docstring(file_path: str, docstring: str) -> bool:
    """
    Safely inserts or replaces the module-level docstring in a file.
    Returns True on success.
    """
    try:
        if not os.path.exists(file_path): return False
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        tree = ast.parse(content)
        existing_doc = ast.get_docstring(tree)
        
        cleaned_doc = clean_docstring(docstring)
        new_doc_block = f'"""\n{cleaned_doc}\n"""\n'
        
        lines = content.splitlines(keepends=True)
        
        if existing_doc:
            # Replace existing
            # We need to find where the docstring node is
            module_body = tree.body
            if module_body and isinstance(module_body[0], ast.Expr) and \
               isinstance(module_body[0].value, ast.Constant) and \
               isinstance(module_body[0].value.value, str):
                   
                end_lineno = module_body[0].end_lineno
                # Skip the doc lines from the original content
                new_content = [new_doc_block] + lines[end_lineno:]
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(new_content)
                return True
        else:
            # Insert at top
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_doc_block + content)
            return True
            
        return False
    except Exception as e:
        print(f"Error inserting docstring: {e}")
        return False
