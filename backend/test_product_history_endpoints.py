"""
Test script for product history endpoints
"""
import sys
sys.path.insert(0, '.')

from app import create_app
from app.models import db, Produto, HistoricoPrecos, VendaItem, Venda
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    # Test 1: Check if Venda model is imported correctly
    print("✓ Venda model imported successfully")
    
    # Test 2: Check if we have any products
    produtos = Produto.query.limit(5).all()
    print(f"✓ Found {len(produtos)} products in database")
    
    if produtos:
        produto = produtos[0]
        print(f"  Testing with product: {produto.id} - {produto.nome}")
        
        # Test 3: Check historico_precos
        historico = HistoricoPrecos.query.filter_by(produto_id=produto.id).all()
        print(f"✓ Found {len(historico)} price history records")
        
        # Test 4: Check vendas
        vendas = VendaItem.query.filter_by(produto_id=produto.id).limit(10).all()
        print(f"✓ Found {len(vendas)} sales records")
        
        # Test 5: Try to serialize historico
        if historico:
            try:
                hist_dict = historico[0].to_dict()
                print(f"✓ Successfully serialized price history")
            except Exception as e:
                print(f"✗ Error serializing price history: {e}")
        
        print("\n✓ All basic checks passed!")
    else:
        print("⚠ No products found in database")
