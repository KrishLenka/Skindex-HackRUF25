import ast
import os
import sys

def check_python_files(directory):
    missing = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read())
                    except SyntaxError:
                        continue
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                            if not ast.get_docstring(node):
                                # Skip __init__ if class has docstring? Let's just track everything for now.
                                if node.name != "__init__":
                                    missing.append(f"{path}:{node.lineno} {node.name}")
    return missing

if __name__ == '__main__':
    backend_dir = sys.argv[1]
    missing_docs = check_python_files(backend_dir)
    if missing_docs:
        for m in missing_docs:
            print(f"Missing docstring: {m}")
    else:
        print("All Python functions/classes have docstrings!")
