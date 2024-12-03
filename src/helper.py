import pandas as pd
import re
import os
import json
import csv
from language_parser import LANGUAGE_MAP
from typing import Union
import tree_sitter
import parso
import shutil
import os

def get_repo_names_from_file(filename):
    df = pd.read_excel(filename, sheet_name='Result 1')
    return df['repo_full_name'].tolist()

def get_code_diff_start_line(code_diff_header):
    match = re.match(r'@@ -\d+,\d+ \+(\d+),\d+ @@', code_diff_header)
    if match:
        return int(match.group(1))  # Returns the starting line in the "new" version of the file
    return None

def extract_code_diffs(patch):
    code_diffs = []
    # Regular expression to capture the code_diff header and content
    pattern = re.compile(r'(@@ -\d+,\d+ \+\d+,\d+ @@)(.*?)\n(?=(@@|\Z))', re.DOTALL)
    matches = pattern.findall(patch)
    for match in matches:
        header = match[0]
        content = match[1].strip()
        code_diffs.append((header, content))
    return code_diffs

def write_json_to_file(data, file_path):
    """
    Writes a list of dictionaries to a file in JSON format.

    Parameters:
    data (list): A list of dictionaries to write to the file.
    file_path (str): The path of the file where the JSON should be saved.
    """
    # Get the directory name from the file path
    directory = os.path.dirname(file_path)
    
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    try:
        # Write JSON data to the specified file
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")
        raise


def write_dicts_to_csv(data, file_path):
    """
    Writes a list of dictionaries to a CSV file.

    Parameters:
    data (list): A list of dictionaries to write to the file.
    file_path (str): The path of the CSV file where the data should be saved.
    """
    if not data:
        print("No data to write.")
        return

    headers = data[0].keys()

    # Get the directory name from the file path
    directory = os.path.dirname(file_path)
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    try:
        with open(file_path, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)            
            writer.writeheader()
            writer.writerows(data)

        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


def has_allowed_extensions(filepath, allowed_extensions):
    for extension in allowed_extensions:
        if not extension.startswith('.'):
            extension = '.' + extension

        if os.path.splitext(os.path.basename(filepath))[1].lower() == extension.lower():
            return True

    return False

def detect_lang_from_extension(filepath):
    extension = os.path.splitext(os.path.basename(filepath))[1].lower()
    extension_to_lang = {".py": "python", ".cpp": "cpp", ".c": "c", ".java": "java", ".js": "javascript", ".go": "golang"}

    return extension_to_lang.get(extension, None)


# Using parso
def extract_python_functions_using_parso(code, start_line, end_line):
    tree = parso.parse(code)
    functions_in_diff = []

    for func in tree.iter_funcdefs():
        func_start = func.start_pos[0]
        func_end = func.end_pos[0]
        if func_start <= end_line and func_end >= start_line:
            functions_in_diff.append(func.get_code())  # Extracts full function code

    return ("\n\n").join(functions_in_diff)


def extract_function_from_full_content(code: str, diff_start_line: int, diff_end_line: int, language: str):
    # Initialize the tree-sitter parser as before
    parser = tree_sitter.Parser()
    tree_sitter_language = LANGUAGE_MAP.get(language)
    if tree_sitter_language is None:
        print("Language could not be loaded.")
        return None
    else:
        print("Language loaded successfully.")

    parser.set_language(tree_sitter_language)

    # Parse the cpp code
    try:
        tree = parser.parse(bytes(code, "utf8"))
    except Exception as e:
        print(f"Parsing failed for: \n{code}\n")
        print(f"Error:\n{e}")
        if language == "python":
            return extract_python_functions_using_parso(code, diff_start_line, diff_end_line)
        return None

    root_node = tree.root_node

    # Split the code into lines for extracting function code
    code_lines = code.splitlines()
    functions_in_diff = []
    function_markers = ["function", "function_declaration", "method_declaration", "function_definition"]
    # Traverse the tree to find functions
    def find_functions(node):
        # Check if node is a function
        if node.type in function_markers:
            func_start = node.start_point[0] + 1  # Convert to 1-based line numbers
            func_end = node.end_point[0] + 1

            # Check if function overlaps with the specified line range
            if func_start <= diff_end_line and func_end >= diff_start_line:
                # Extract the function code using line range
                function_code = "\n".join(code_lines[func_start - 1:func_end])
                functions_in_diff.append(function_code)

        # Recursively visit each child node
        for child in node.children:
            if node.type not in function_markers:
                find_functions(child)
            
    find_functions(root_node)

    return ("\n\n").join(functions_in_diff)


def get_code_diff_start_line(code_diff_header: str) -> Union[int, None]:
    """Extracts the starting line number from the code diff header."""
    match = re.match(r'@@ -\d+,\d+ \+(\d+),\d+ @@', code_diff_header)
    if match:
        return int(match.group(1))  # Returns the starting line in the "new" version of the file
    return None


def empty_directory(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove file or symbolic link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove directory and its contents
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def remove_file(file_path):
    try:
        os.remove(file_path)
        print(f"{file_path} has been deleted successfully.")
    except FileNotFoundError:
        print(f"{file_path} does not exist.")
    except PermissionError:
        print(f"Permission denied: unable to delete {file_path}.")
    except Exception as e:
        print(f"An error occurred while deleting {file_path}: {e}")