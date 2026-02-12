import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api/vendas"

def test_filters():
    print("Testing Sales Filters...")

    # 1. Test Listing (No filters)
    print("\n1. Listing all sales (no filters):")
    try:
        resp = requests.get(BASE_URL)
        if resp.status_code == 200:
            data = resp.json()
            total = data['paginacao']['total_itens']
            print(f"   Success. Total sales: {total}")
            if total > 0:
                print(f"   First sale status: {data['vendas'][0]['status']}")
        else:
            print(f"   Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # 2. Test Status Filter (Finalizada)
    print("\n2. Filtering by Status=finalizada:")
    try:
        resp = requests.get(BASE_URL, params={"status": "finalizada"})
        if resp.status_code == 200:
            data = resp.json()
            total = data['paginacao']['total_itens']
            print(f"   Total finalized sales: {total}")
            # Verify
            all_match = all(v['status'].lower() == 'finalizada' for v in data['vendas'])
            print(f"   ALL match 'finalizada'? {all_match}")
        else:
            print(f"   Failed: {resp.status_code}")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Test Status Filter (Cancelada)
    print("\n3. Filtering by Status=cancelada:")
    try:
        resp = requests.get(BASE_URL, params={"status": "cancelada"})
        if resp.status_code == 200:
            data = resp.json()
            total = data['paginacao']['total_itens']
            print(f"   Total canceled sales: {total}")
        else:
            print(f"   Failed: {resp.status_code}")
    except Exception as e:
        print(f"   Error: {e}")

    # 4. Test Date Filter
    print("\n4. Filtering by Date (Last 30 days):")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    print(f"   Range: {start_date} to {end_date}")
    try:
        resp = requests.get(BASE_URL, params={"data_inicio": start_date, "data_fim": end_date})
        if resp.status_code == 200:
            data = resp.json()
            total = data['paginacao']['total_itens']
            print(f"   Total sales in range: {total}")
        else:
            print(f"   Failed: {resp.status_code}")
    except Exception as e:
        print(f"   Error: {e}")

    # 5. Test Statistics Endpoint - Default (Should check logic about 'finalizada')
    print("\n5. Statistics (No filters - Checks default behavior):")
    try:
        resp = requests.get(f"{BASE_URL}/estatisticas")
        if resp.status_code == 200:
            data = resp.json()
            total_vendas = data['estatisticas_gerais']['total_vendas']
            print(f"   Total sales in stats: {total_vendas}")
        else:
            print(f"   Failed: {resp.status_code}")
    except Exception as e:
        print(f"   Error: {e}")

    # 6. Test Statistics Endpoint - Explicit 'todos' ? No, param is status="" or omitted.
    # Frontend logic: if status="", it is NOT sent.
    # Backend logic: if not "status", filter "finalizada".
    # So we cannot get STATS for "cancelada" unless we explicitly filter "status=cancelada".
    # And we cannot get STATS for ALL unless we change backend logic.
    
if __name__ == "__main__":
    test_filters()
