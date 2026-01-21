import ast
import os

class SignatureModifier:
    """Helper to modify function signatures using AST."""
    
    @staticmethod
    def add_missing_arguments(file_path: str, function_name: str, missing_args: list[str]) -> tuple[bool, str]:
        """
        Appends missing arguments to a function definition.
        
        Args:
            file_path: Path to the python file.
            function_name: Name of the function to modify.
            missing_args: List of argument names to append.
            
        Returns:
            (success, message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            lines = source.splitlines()
            
            target_node = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                    target_node = node
                    break
            
            if not target_node:
                return False, f"Function '{function_name}' not found."
                
            # We need to find the definition line and insert args
            # AST doesn't give precise char offsets for args in old python versions easily, 
            # but we can try a robust text manipulation if we find the 'def name(' part.
            
            # Simple approach: Find the closing parenthesis of the definition
            start_line_idx = target_node.lineno - 1
            # We need to look forward from start_line until we find '):' or ')'
            # Use simple parsing for now. 
            
            # Re-read lines to be safe
            joined_code = ""
            def_end_idx = -1
            
            # Heuristic: Scan lines starting from lineno to find the end of the signature
            # This handles multi-line definitions
            current_line_idx = start_line_idx
            buffer = ""
            while current_line_idx < len(lines):
                line_content = lines[current_line_idx]
                buffer += line_content
                if "):" in buffer or (")" in buffer and ":" in buffer.split(")")[-1]):
                    # Found end of signature
                    # Find last occurence of ')' before the colon
                    # This is tricky with types like -> int:
                    
                    # Safer: Use AST to find existing args and reconstruct?
                    # No, recreating code from AST loses formatting/comments.
                    
                    # Regex/Text approach:
                    # Find the last ')' before the ':' that ends the def.
                    pass
                    break
                current_line_idx += 1
                
            # Let's try a simpler robust approach:
            # 1. Get the line with 'def function_name'
            # 2. Find the closing ')' that matches the opening '('
            # 3. Insert args before that ')'
            
            # Re-implementation with simple logic for now (assuming single line or simple multi-line)
            # Find the def start
            # This is complex to do robustly without a refactoring library like libcst, 
            # but we will try a best-effort text match for this task.
            
            content_to_modify = "\n".join(lines[start_line_idx:current_line_idx+1])
            
            # Find the last closing parenthesis that is part of the args
            # We can traverse backwards from the first colon
            colon_pos = content_to_modify.find(':')
            if colon_pos == -1: return False, "Could not find function body start ':'"
            
            # Search backwards from colon for ')'
            close_paren_pos = content_to_modify.rfind(')', 0, colon_pos)
            if close_paren_pos == -1: return False, "Could not find closing ')' for arguments"
            
            # Check if there are existing args (char before ')' isn't '(')
            # Ignore whitespace
            has_args = False
            check_pos = close_paren_pos - 1
            while check_pos >= 0:
                char = content_to_modify[check_pos]
                if char == '(':
                    has_args = False
                    break
                if not char.isspace():
                    has_args = True
                    break
                check_pos -= 1
            
            prefix = ", " if has_args else ""
            insertion = prefix + ", ".join(missing_args)
            
            new_content = content_to_modify[:close_paren_pos] + insertion + content_to_modify[close_paren_pos:]
            
            # Replace lines
            # Split new_content back into lines
            new_lines_chunk = new_content.split('\n')
            lines[start_line_idx:current_line_idx+1] = new_lines_chunk
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
                
            return True, "Signature updated successfully"
            
        except Exception as e:
            return False, str(e)
