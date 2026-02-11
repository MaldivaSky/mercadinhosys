#!/usr/bin/env python
"""
Create the produto_lotes table if it doesn't exist
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import ProdutoLote

app = create_app()

with app.app_context():
    print("Creating produto_lotes table...")
    
    # Create the table
    db.create_all()
    
    print("✅ Table created successfully!")
    
    # Verify the table exists
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'produto_lotes' in tables:
        print("✅ produto_lotes table exists")
        columns = inspector.get_columns('produto_lotes')
        print("\nColumns:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    else:
        print("❌ produto_lotes table not found")
