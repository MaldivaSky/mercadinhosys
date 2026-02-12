
import ast
import sys

filename = r"c:\Users\rafae\OneDrive\Desktop\mercadinhosys\backend\app\dashboard_cientifico\models_layer.py"

try:
    with open(filename, "r", encoding="utf-8") as f:
        source = f.read()
    ast.parse(source)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
    print(f"Line: {e.lineno}")
    print(f"Offset: {e.offset}")
    print(f"Text: {e.text}")
except Exception as e:
    print(f"Error: {e}")
