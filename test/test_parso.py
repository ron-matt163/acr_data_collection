import parso

file_contents = ""

with open("sample_python_code.py", 'r') as file:
    file_contents = file.read()

def get_python_functions_in_range(code, start_line, end_line):
    tree = parso.parse(code)
    functions_in_diff = []

    for func in tree.iter_funcdefs():
        func_start = func.start_pos[0]
        func_end = func.end_pos[0]
        if func_start <= end_line and func_end >= start_line:
            functions_in_diff.append(func.get_code())  # Extracts full function code

    return functions_in_diff

functions_in_diff = get_python_functions_in_range(file_contents, 965, 975)

print(functions_in_diff)

