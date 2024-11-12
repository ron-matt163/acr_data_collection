import clang
from clang.cindex import Index

def get_cpp_functions_in_range(file_contents, start_line, end_line):
    
    def get_function_code(extent, file_contents):
        start_line = extent.start.line - 1  # Convert to 0-based index
        end_line = extent.end.line  # Line is inclusive in Clang, so no need to adjust end
        lines = file_contents.splitlines()
        function_code = "\n".join(lines[start_line:end_line])
        return function_code

    index = Index.create()
    args = ["-fsyntax-only"]
    translation_unit = index.parse('sample_cpp_code.cpp', args=args)    
    functions_in_diff = []

    for func in translation_unit.cursor.get_children():
        if func.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            func_start = func.extent.start.line
            func_end = func.extent.end.line
            if func_start <= end_line and func_end >= start_line:
                # Get the function's source code from the file using the extent
                func_code = get_function_code(func.extent, file_contents)
                functions_in_diff.append(func_code)

    return functions_in_diff


file_contents = ""
with open("sample_cpp_code.cpp", 'r') as file:
    file_contents = file.read()

functions_in_diff = get_cpp_functions_in_range(file_contents, 41, 49)

# Print the function contents
for func_code in functions_in_diff:
    print("Function Code:")
    print(func_code)
    print()