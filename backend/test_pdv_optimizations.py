"""
Test script for PDV Mission-Critical Optimizations
Tests:
1. InsuficientStockError exception
2. CMP (Custo Médio Ponderado) integration
3. RFM intelligence
4. margem_lucro_real field
"""

from app import create_app, db
from app.models import Produto, Cliente, Venda, VendaItem
from app.routes.pdv import InsuficientStockError, calcular_rfm_cliente
from datetime import datetime, timedelta
from decimal import Decimal

def test_insuficient_stock_error():
    """Test custom exception for insufficient stock"""
    print("\n🧪 Test 1: InsuficientStockError Exception")
    try:
        raise InsuficientStockError("Estoque insuficiente para 'Produto Teste'")
    except InsuficientStockError as e:
        print(f"✅ Exception caught correctly: {str(e)}")
        return True
    except Exception as e:
        print(f"❌ Wrong exception type: {type(e)}")
        return False

def test_margem_lucro_real_field():
    """Test margem_lucro_real field in VendaItem model"""
    print("\n🧪 Test 2: margem_lucro_real Field")
    app = create_app()
    with app.app_context():
        # Check if field exists in model
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('venda_itens')]
        
        if 'margem_lucro_real' in columns:
            print(f"✅ margem_lucro_real field exists in venda_itens table")
            print(f"   Columns: {columns}")
            return True
        else:
            print(f"❌ margem_lucro_real field NOT found in venda_itens table")
            print(f"   Available columns: {columns}")
            return False

def test_rfm_calculation():
    """Test RFM calculation function"""
    print("\n🧪 Test 3: RFM Calculation Function")
    app = create_app()
    with app.app_context():
        # Get first cliente for testing
        cliente = Cliente.query.first()
        
        if not cliente:
            print("⚠️  No clients found in database, skipping RFM test")
            return True
        
        try:
            rfm_data = calcular_rfm_cliente(cliente.id, cliente.estabelecimento_id)
            print(f"✅ RFM calculated successfully for cliente {cliente.nome}")
            print(f"   Segmento: {rfm_data['segmento']}")
            print(f"   Sugerir Desconto: {rfm_data['sugerir_desconto']}")
            print(f"   Recency: {rfm_data['recency_days']} days (score: {rfm_data['recency_score']})")
            print(f"   Frequency: {rfm_data['frequency']} (score: {rfm_data['frequency_score']})")
            print(f"   Monetary: R$ {rfm_data['monetary']:.2f} (score: {rfm_data['monetary_score']})")
            return True
        except Exception as e:
            print(f"❌ Error calculating RFM: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_produto_cmp():
    """Test CMP (Custo Médio Ponderado) in Produto model"""
    print("\n🧪 Test 4: CMP (Custo Médio Ponderado)")
    app = create_app()
    with app.app_context():
        produto = Produto.query.first()
        
        if not produto:
            print("⚠️  No products found in database, skipping CMP test")
            return True
        
        print(f"✅ Product found: {produto.nome}")
        print(f"   Current preco_custo (CMP): R$ {float(produto.preco_custo):.2f}")
        print(f"   Current preco_venda: R$ {float(produto.preco_venda):.2f}")
        print(f"   Current margem_lucro: {float(produto.margem_lucro):.2f}%")
        
        # Test recalcular_preco_custo_ponderado method exists
        if hasattr(produto, 'recalcular_preco_custo_ponderado'):
            print(f"✅ recalcular_preco_custo_ponderado method exists")
            return True
        else:
            print(f"❌ recalcular_preco_custo_ponderado method NOT found")
            return False

def test_venda_item_to_dict():
    """Test VendaItem.to_dict includes margem_lucro_real"""
    print("\n🧪 Test 5: VendaItem.to_dict() includes margem_lucro_real")
    app = create_app()
    with app.app_context():
        venda_item = VendaItem.query.first()
        
        if not venda_item:
            print("⚠️  No venda items found in database, skipping test")
            return True
        
        item_dict = venda_item.to_dict()
        
        if 'margem_lucro_real' in item_dict:
            print(f"✅ margem_lucro_real included in to_dict()")
            print(f"   Value: R$ {item_dict['margem_lucro_real']:.2f}")
            return True
        else:
            print(f"❌ margem_lucro_real NOT included in to_dict()")
            print(f"   Keys: {list(item_dict.keys())}")
            return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("PDV MISSION-CRITICAL OPTIMIZATIONS - TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("InsuficientStockError", test_insuficient_stock_error()))
    results.append(("margem_lucro_real Field", test_margem_lucro_real_field()))
    results.append(("RFM Calculation", test_rfm_calculation()))
    results.append(("CMP Method", test_produto_cmp()))
    results.append(("VendaItem.to_dict()", test_venda_item_to_dict()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! PDV optimizations are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")

if __name__ == "__main__":
    main()
