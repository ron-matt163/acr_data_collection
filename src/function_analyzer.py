import ast
import re
import os
from typing import Dict, List, Set
from user_defined_functions import *

def load_user_defined_functions(file_path: str) -> Set[str]:
    """
    Load the list of user-defined functions from a text file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return {line.strip() for line in file if line.strip()}

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

def get_function_code_pattern(function_name):
    # Regex pattern to capture the function definition and body
    return re.compile(rf"(def {function_name}\s*\(.*?\):\s*\n(?:\s+.*\n)*)", re.MULTILINE)

def extract_function_code_from_repo(repo_path: str, function_name: str) -> List[Dict[str, str]]:
    """
    Extracts the function code for the specified function name across the repository.
    """
    function_code_data = []
    
    # Walk through all files in the repo_path
    for root, dirs, files in os.walk(repo_path):
        # Exclude 'lib' and 'static' directories
        if 'lib' in root.split(os.sep) or 'static' in root.split(os.sep):
            continue
        
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            # Only check .py files (skip __init__ files)
            if file_path.endswith('.py') and 'init' not in file_name:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # Search and extract the function code in the file
                    match = get_function_code_pattern(function_name).search(content)
                    if match:
                        function_code_data.append({
                            "code": match.group(1)
                        })
    return function_code_data

def analyze_diff_and_functions(diff_data: Dict, repo_path) -> Dict:
    """
    Analyze a code diff and extract function call information for user-defined functions.
    """
    result = {
        'function_calls': [],
        'extracted_code': {}
    }
    
    output_file = "user_defined_functions.txt"
    find_user_defined_functions(repo_path, output_file)

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_defined_functions_file = os.path.join(script_dir, output_file)

    # Read the file and store each line in a list
    with open(user_defined_functions_file, 'r') as file:
        user_defined_functions = [line.strip() for line in file]
    
    # Extract function calls from the diff
    diff_functions = extract_function_calls(diff_data['code_diff'])

    # Filter to include only functions with at least one underscore and are in the user-defined functions list
    filtered_functions = {func for func in diff_functions if func in user_defined_functions}
    result['function_calls'] = list(filtered_functions)

    for function_name in filtered_functions:
        print("Processing function:", function_name)
        function_code = extract_function_code_from_repo(repo_path, function_name)
        if function_code:
            result['extracted_code'][function_name] = function_code

    return result