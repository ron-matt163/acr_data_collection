from tree_sitter_languages import get_language

# Load precompiled languages
def load_tree_sitter_libraries():
    return {
        "python": get_language('python'),
        "java": get_language('java'),
        "cpp": get_language('cpp'),
        "c": get_language('c'),
        "javascript": get_language('javascript'),
        "golang": get_language('go')
    }

# Map the language string to tree-sitter languages
LANGUAGE_MAP = load_tree_sitter_libraries()