import os
import sys
import re

def check_js_files(directory):
    missing = []
    
    # regexes
    const_re = re.compile(r'^\s*(export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(async\s+)?\(')
    func_re = re.compile(r'^\s*(export\s+)?(async\s+)?function\s+([A-Za-z0-9_]+)\s*\(')
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.js') or file.endswith('.jsx'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines):
                    name = None
                    m1 = const_re.match(line)
                    if m1:
                        name = m1.group(2)
                    else:
                        m2 = func_re.match(line)
                        if m2:
                            name = m2.group(3)
                            
                    if name:
                        # check if there's JSDoc above
                        has_doc = False
                        start = max(0, i - 10)
                        for j in range(start, i):
                            if '*/' in lines[j]:
                                has_doc = True
                                break
                        if not has_doc:
                            missing.append(f"{path}:{i+1} : {name}")
    return missing

if __name__ == '__main__':
    js_dir = sys.argv[1]
    missing_docs = check_js_files(js_dir)
    if missing_docs:
        for m in missing_docs:
            print(f"Missing JSDoc: {m}")
    else:
        print("All JS functions have JSDoc!")
