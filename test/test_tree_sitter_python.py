import sys
import os
import tree_sitter

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(src_path)

from language_parser import LANGUAGE_MAP


def get_python_functions_in_range(code, start_line, end_line):
    parser = tree_sitter.Parser()
    python_language = LANGUAGE_MAP.get('python')
    if python_language is None:
        print("python language could not be loaded.")
        return None
    else:
        print("python language loaded successfully.")

    parser.set_language(python_language)

    # Parse the python code
    try:
        tree = parser.parse(bytes(code, "utf8"))
    except Exception as e:
        print(f"Parsing failed for: \n{code}\n")
        print(f"Error:\n{e}")
        return None

    root_node = tree.root_node

    # Split the code into lines for extracting function code
    code_lines = code.splitlines()
    functions_in_diff = []

    # Traverse the tree to find functions
    def find_functions(node):
        # Check if node is a function
        # print("\n\n\n", node)
        if node.type == "function" or node.type == "function_definition":
            func_start = node.start_point[0] + 1  # Convert to 1-based line numbers
            func_end = node.end_point[0] + 1

            # Check if function overlaps with the specified line range
            if func_start <= end_line and func_end >= start_line:
                # Extract the function code using line range
                function_code = "\n".join(code_lines[func_start - 1:func_end])
                functions_in_diff.append(function_code)

        # Recursively visit each child node
        for child in node.children:
            if node.type != "function" or node.type != "function_declaration":
                find_functions(child)
            
    find_functions(root_node)

    return functions_in_diff


file_contents = ""
with open("sample_python_code.py", 'r') as file:
    file_contents = file.read()

functions = get_python_functions_in_range(file_contents, 846, 862)
for func in functions:
    print("Function code")
    print(func)
    print()