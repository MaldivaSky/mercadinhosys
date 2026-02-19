
import sys
import os
import logging
from unittest.mock import MagicMock, PropertyMock
import traceback

# Add backend directory to path
sys.path.append(os.getcwd())

# 1. Mock the DB structure BEFORE importing the module under test
mock_db = MagicMock()
mock_session = mock_db.session
sys.modules['app.models'] = MagicMock()
sys.modules['app.models'].db = mock_db
sys.modules['app.models'].Venda = MagicMock()
sys.modules['app.models'].VendaItem = MagicMock()
sys.modules['app.models'].Produto = MagicMock()

# 2. Import the class
from app.dashboard_cientifico.models_layer import PracticalModels

# 3. Setup Logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

def test_correlations_logic():
    sys.stderr.write("\n" + "="*60 + "\n")
    sys.stderr.write("🧪 UNIT TEST: PracticalModels.calculate_correlations\n")
    sys.stderr.write("="*60 + "\n")
    
    # --- DATA SETUP ---
    sales_timeseries = [
        {'data': '2023-01-01', 'total': 100},
        {'data': '2023-01-02', 'total': 150},
    ]
    expense_details = [
         {'data': '2023-01-01', 'valor': 50, 'estabelecimento_id': 1},
    ]
    
    # --- MOCK QUERY CHAIN ---
    # The code does: db.session.query(...).filter(...).group_by(...).all()
    # We need to make sure this chain returns our mock rows.

    # Mock Rows for "Hour vs Sales"
    # Row needs to support attribute access: row.hora, row.total
    row1 = MagicMock(); row1.hora = 10; row1.total = 1000
    row2 = MagicMock(); row2.hora = 14; row2.total = 5000
    
    # Mock Rows for "Day vs Ticket"
    # Row needs: row.dia (0-6), row.ticket_medio
    row3 = MagicMock(); row3.dia = 0; row3.ticket_medio = 50.0
    row4 = MagicMock(); row4.dia = 5; row4.ticket_medio = 120.0 # Weekend peak

    # Create a Query Object that returns itself for all method calls
    query_obj = MagicMock()
    query_obj.filter.return_value = query_obj
    query_obj.join.return_value = query_obj
    query_obj.group_by.return_value = query_obj
    
    # side_effect for .all() to return different data for each call
    # Order of calls in models_layer.py:
    # 1. Hourly Sales
    # 2. Day of Week
    # 3. Product Mix
    # 4. Stock
    # 5. Margin
    query_obj.all.side_effect = [
        [row1, row2],       # Call 1: Hourly
        [row3, row4],       # Call 2: Day of Week
        [], [], [], []      # Others
    ]
    
    # Connect session.query to return our query_obj
    mock_session.query.return_value = query_obj

    # --- EXECUTION ---
    try:
        sys.stderr.write("⏳ Calling calculate_correlations...\n")
        correlations = PracticalModels.calculate_correlations(sales_timeseries, expense_details, establishment_id=1)
        
        sys.stderr.write(f"✅ Return received: {len(correlations)} correlations.\n")
        
        found_hourly = False
        found_weekly = False
        
        for c in correlations:
            msg = f"  - [{c.get('variavel1')}] x [{c.get('variavel2')}] | R={c.get('correlacao')}\n"
            sys.stderr.write(msg)
            
            v1 = str(c.get('variavel1'))
            v2 = str(c.get('variavel2'))
            
            if "Hora" in v1 or "Horário" in v2 or "Pico" in v1:
                found_hourly = True
            if "Dia" in v1 or "Semana" in v1:
                found_weekly = True
                
        # --- VERIFICATION ---
        if found_hourly:
            sys.stderr.write("\n✅ PASS: Hora do Dia correlation found.\n")
        else:
            sys.stderr.write("\n❌ FAIL: Hora do Dia correlation MISSING.\n")
            
        if found_weekly:
            sys.stderr.write("✅ PASS: Dia da Semana correlation found.\n")
        else:
            sys.stderr.write("❌ FAIL: Dia da Semana correlation MISSING.\n")
            
        if found_hourly and found_weekly:
            sys.exit(0) # Success
        else:
            sys.exit(1) # Logic failure

    except Exception as e:
        sys.stderr.write(f"\n❌ CRITICAL EXCEPTION: {type(e).__name__}: {e}\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_correlations_logic()
