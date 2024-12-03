from py_mini_racer import py_mini_racer
import json

# Initialize JavaScript runtime and load esprima
ctx = py_mini_racer.MiniRacer()
ctx.eval("const esprima = require('esprima');")

def get_javascript_functions(code, start_line, end_line):
    # Parse JavaScript code to generate an AST
    ast = ctx.eval(f"esprima.parseScript({json.dumps(code)}, {{ loc: true }});")
    functions_in_diff = []

    # Recursively search for functions within the AST
    def find_functions(node):
        if node.get("type") == "FunctionDeclaration":
            func_start = node["loc"]["start"]["line"]
            func_end = node["loc"]["end"]["line"]
            if func_start <= end_line and func_end >= start_line:
                # Append function details or code
                functions_in_diff.append({
                    "name": node["id"]["name"],
                    "start": func_start,
                    "end": func_end
                })
        for key in node:
            child = node[key]
            if isinstance(child, dict):
                find_functions(child)
            elif isinstance(child, list):
                for subchild in child:
                    if isinstance(subchild, dict):
                        find_functions(subchild)

    find_functions(ast)
    return functions_in_diff

# Example usage

file_contents = ""
with open("sample_js_code.js", 'r') as file:
    file_contents = file.read()

functions = get_javascript_functions(file_contents, 19, 36)
# Print the function contents
for func_code in functions:
    print("Function Code:")
    print(func_code)
    print()