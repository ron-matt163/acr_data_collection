import javalang

def get_java_functions_in_range(code, start_line, end_line):
    tree = javalang.parse.parse(code)
    functions_in_diff = []

    # Split the code into lines for easy line-based extraction
    code_lines = code.splitlines()

    for _, node in tree:
        if isinstance(node, javalang.tree.MethodDeclaration) and node.position:
            func_start = node.position.line

            # Only proceed if the function starts within the specified range
            if func_start > end_line:
                continue

            # Estimate function end using brace matching
            open_braces = 0
            func_end = func_start  # Start at the function's start line

            for i in range(func_start - 1, len(code_lines)):
                line = code_lines[i]
                open_braces += line.count("{")
                open_braces -= line.count("}")

                # When all braces are closed, we've found the function's end
                if open_braces == 0:
                    func_end = i + 1  # Account for zero-based index
                    break

            # Check if this function overlaps with the specified line range
            if func_start <= end_line and func_end >= start_line:
                # Extract the function code using line range
                function_code = "\n".join(code_lines[func_start - 1:func_end])
                functions_in_diff.append(function_code)

    return functions_in_diff

# Example usage
file_contents = ""
with open("sample_java_code.java", 'r') as file:
    file_contents = file.read()

functions_in_diff = get_java_functions_in_range(file_contents, 176, 184)
# Print the function contents
for func_code in functions_in_diff:
    print("Function Code:")
    print(func_code)
    print()
