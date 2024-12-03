import os
import ast

def extract_user_defined_functions(file_path):
    """
    Extract user-defined function names from a Python file.
    """
    user_defined_functions = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            tree = ast.parse(file.read(), filename=file_path)
            for node in ast.walk(tree):
                # Only consider function definitions
                if isinstance(node, ast.FunctionDef) and node.name != "__init__" and "_" in node.name:
                    user_defined_functions.append(node.name)
        except SyntaxError as e:
            print(f"Syntax error in file {file_path}: {e}")
    
    return user_defined_functions

def find_user_defined_functions(repo_path, output_file):
    """
    Traverse the repository and find user-defined functions, storing them in a text file.
    """
    all_functions = []

    # Walk through all files in the repo_path
    for root, dirs, files in os.walk(repo_path):
        # Exclude 'lib' and 'static' directories
        if 'lib' in root.split(os.sep) or 'static' in root.split(os.sep):
            continue
        
        for file_name in files:
            # Skip __init__.py files and non-Python files
            if 'init' in file_name or not file_name.endswith('.py'):
                continue
            
            file_path = os.path.join(root, file_name)
            user_defined_functions = extract_user_defined_functions(file_path)
            if user_defined_functions:
                all_functions.extend(user_defined_functions)

    # Write all function names to the output file
    with open(output_file, 'w', encoding='utf-8') as out_file:
        for func_name in all_functions:
            out_file.write(f"{func_name}\n")

    print(f"Extracted {len(all_functions)} user-defined functions and saved to {output_file}")
