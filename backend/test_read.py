import os
import traceback

app_dir = os.path.join(os.getcwd(), 'app')
for root, _, files in os.walk(app_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
