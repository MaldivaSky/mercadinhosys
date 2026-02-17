import os
from sqlalchemy import create_engine, inspect
import re

def get_database_url():
    url = os.environ.get('DATABASE_URL')
    if not url:
        return None
    return url

def get_tablenames_from_models():
    tablenames = {}
    models_path = os.path.join('backend', 'app', 'models.py')
    if not os.path.exists(models_path):
        return {}
    
    with open(models_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # More robust pattern to handle whitespace/comments
    # Look for each class and find the nearest __tablename__
    class_blocks = re.split(r'\nclass\s+', content)
    for block in class_blocks[1:]: # skip first part before first class
        class_match = re.match(r'^(\w+)', block)
        if class_match:
            class_name = class_match.group(1)
            # Find __tablename__ in this block (before next class)
            table_match = re.search(r'__tablename__\s*=\s*["\'](.+?)["\']', block)
            if table_match:
                table_name = table_match.group(1)
                tablenames[table_name] = class_name
        
    return tablenames

def verify_schema():
    url = get_database_url()
    if not url:
        print("Set DATABASE_URL environment variable.")
        return

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    try:
        engine = create_engine(url)
        inspector = inspect(engine)
        cloud_tables = set(inspector.get_table_names())
        print(f"--- Cloud Database Tables ({len(cloud_tables)}) ---")
        print(sorted(list(cloud_tables)))
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return
    
    local_tables_map = get_tablenames_from_models()
    local_tables = set(local_tables_map.keys())
    print(f"\n--- Local Model Tables ({len(local_tables)}) ---")
    print(sorted(list(local_tables)))
    
    # Tables Diff
    missing_in_cloud = local_tables - cloud_tables
    missing_in_local = cloud_tables - local_tables
    
    if missing_in_cloud:
        print("\n[!] Tables defined locally but MISSING in Cloud:")
        for t in sorted(missing_in_cloud):
            print(f"  - {t} (Model: {local_tables_map[t]})")
    
    if missing_in_local:
        print("\n[!] Tables exists in Cloud but NOT matched to Local models:")
        for t in sorted(missing_in_local):
            print(f"  - {t}")
            
    # Key table column check
    for table_to_check in ['produtos', 'venda_itens', 'vendas']:
        if table_to_check in cloud_tables:
            print(f"\n--- Column Audit for '{table_to_check}' ---")
            cloud_cols = set([c['name'] for c in inspector.get_columns(table_to_check)])
            print(f"Cloud columns: {sorted(list(cloud_cols))}")

if __name__ == "__main__":
    verify_schema()
