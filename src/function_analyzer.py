import ast
import re
from typing import Dict, List, Set

def extract_function_calls(code: str) -> Set[str]:
    """
    Extract function calls from a Python code string using AST.
    """
    function_calls = set()
    
    try:
        tree = ast.parse(code)
        
        class FunctionCallVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    function_calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    function_calls.add(f"{node.func.value.id}.{node.func.attr}")
                self.generic_visit(node)
                
        FunctionCallVisitor().visit(tree)
    except:
        # If AST parsing fails, try regex-based approach
        function_pattern = r'\b\w+\s*\('
        matches = re.finditer(function_pattern, code)
        for match in matches:
            func_name = match.group().strip('(').strip()
            function_calls.add(func_name)
    
    return function_calls

def analyze_diff_and_functions(diff_data: Dict) -> Dict:
    """
    Analyze a code diff and extract function call information.
    """
    result = {
        'diff': diff_data['diff'],
        'file_path': diff_data['file_path'],
        'commit_sha': diff_data['commit_sha'],
        'function_calls': [],
    }
    
    # Extract function calls from the diff
    diff_functions = extract_function_calls(diff_data['diff'])
    
    # Extract function calls from the full file
    full_file_functions = extract_function_calls(diff_data['full_file'])
    
    # Find new function calls introduced in the diff
    new_functions = diff_functions - full_file_functions
    
    result['function_calls'] = list(diff_functions)
    result['new_function_calls'] = list(new_functions)
    
    return result
