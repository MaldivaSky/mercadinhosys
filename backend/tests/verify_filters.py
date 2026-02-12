import requests
import json
from datetime import datetime, timedelta
import os

BASE_URL = "http://localhost:5000/api/vendas"

def test_filters():
    print("Testing Sales Filters - Aggressive check...")
    
    # Check if backend is reachable
    try:
        requests.get("http://localhost:5000/")
    except:
        print("Backend not reachable!")
        return

    # 1. Listing all sales (no filters) -> Baseline
    print("\n1. Listing all sales (no filters):")
    try:
        resp = requests.get(BASE_URL)
        if resp.status_code == 200:
            data = resp.json()
            total_all = data['paginacao']['total_itens']
            print(f"   Success. Total sales: {total_all}")
            if total_all == 0:
                print("   WARNING: No sales found at all. Seed database?")
        else:
            print(f"   Failed: {resp.status_code} - {resp.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return

    # 2. Filtering by Status=cancelada
    # If total_all > 0, cancelada should be < total_all (unless all are canceled)
    # If cancelada == total_all, filter is broken.
    print("\n2. Filtering by Status=cancelada:")
    try:
        resp = requests.get(BASE_URL, params={"status": "cancelada"})
        if resp.status_code == 200:
            data = resp.json()
            total_canceled = data['paginacao']['total_itens']
            print(f"   Total canceled sales: {total_canceled}")
            
            if total_canceled > 0:
                first_status = data['vendas'][0]['status']
                print(f"   First sale status: {first_status}")
                if first_status.lower() != 'cancelada':
                    print("   FAIL: Filter did not filter! Returned non-canceled sale.")
                else:
                    print("   PASS: Returned canceled sale.")
            else:
                 print("   PASS: 0 canceled sales found")
            
            # Check debug info
            print(f"   Applied Filters (Backend): {data['paginacao'].get('filtros_aplicados', 'NONE')}")

            if total_canceled == total_all and total_all > 0:
                print("   FAIL: Count matches total sales. Filter ignored!")
            
        else:
            print(f"   Failed: {resp.status_code}")
            try:
                print(f"   Response: {resp.text}")
            except:
                pass
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Filtering by Status=finalizada
    print("\n3. Filtering by Status=finalizada:")
    try:
        resp = requests.get(BASE_URL, params={"status": "finalizada"})
        if resp.status_code == 200:
            data = resp.json()
            total_finalized = data['paginacao']['total_itens']
            print(f"   Total finalized: {total_finalized}")
            print(f"   Applied Filters: {data['paginacao'].get('filtros_aplicados', 'NONE')}")
        else:
            print(f"   Failed: {resp.status_code}")
    except Exception as e:
        print(f"   Error: {e}")

    # 4. Statistics Check
    print("\n4. Statistics Endpoint (Profit Check):")
    try:
        resp = requests.get(f"{BASE_URL}/estatisticas")
        if resp.status_code == 200:
            data = resp.json()
            lucro = data.get('estatisticas_gerais', {}).get('total_lucro')
            print(f"   Total Lucro: {lucro}")
            if lucro is None:
                print("   FAIL: 'total_lucro' missing from response!")
            else:
                print("   PASS: 'total_lucro' present.")
        else:
            print(f"   Failed: {resp.status_code}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_filters()
