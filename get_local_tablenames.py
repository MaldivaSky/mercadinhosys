
import os
import re

path = 'backend/app/models.py'
if not os.path.exists(path):
    print(f"File {path} not found")
else:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_class = None
    print("LOCAL_MODELS_START")
    for line in lines:
        class_match = re.match(r'^class\s+(\w+)\s*\(.*\):', line)
        if class_match:
            current_class = class_match.group(1)
        
        table_match = re.search(r'__tablename__\s*=\s*"(.*?)"', line)
        if table_match and current_class:
            print(f"{current_class}: {table_match.group(1)}")
            current_class = None 
    print("LOCAL_MODELS_END")
