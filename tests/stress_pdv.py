import requests
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:5000"
# Adjust these credentials as needed for your local environment
USERNAME = "admin"
PASSWORD = "admin123" 

class PDVStressTest:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.produtos = []
        self.clientes = []
        self.success_count = 0
        self.error_count = 0
        self.latencies = []
        self.lock = threading.Lock()

    def login(self):
        print("Logging in...")
        try:
            resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            if resp.status_code == 200:
                data = resp.json()
                self.token = data['data']['access_token']
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print("Login successful.")
                return True
            else:
                print(f"Login failed: {resp.text}")
                return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    def fetch_data(self):
        print("Fetching products and clients...")
        try:
            # Fetch products
            resp_prod = requests.get(f"{BASE_URL}/api/produtos/?por_pagina=100&ativo=true", headers=self.headers)
            if resp_prod.status_code == 200:
                self.produtos = resp_prod.json().get('produtos', [])
                print(f"Loaded {len(self.produtos)} products.")
            
            # Fetch clients
            resp_cli = requests.get(f"{BASE_URL}/api/clientes/?por_pagina=50", headers=self.headers)
            if resp_cli.status_code == 200:
                self.clientes = resp_cli.json().get('clientes', [])
                print(f"Loaded {len(self.clientes)} clients.")
                
            return len(self.produtos) > 0
        except Exception as e:
            print(f"Data fetch error: {e}")
            return False

    def simulate_sale(self, sale_id):
        if not self.produtos:
            return

        start_time = time.time()
        
        # Select 1-5 random products
        num_items = random.randint(1, 5)
        selected_items = random.sample(self.produtos, min(num_items, len(self.produtos)))
        
        items_payload = []
        subtotal = 0
        
        for prod in selected_items:
            # Use 'quantidade_estoque' if available, otherwise 'quantidade'
            estoque = prod.get('quantidade_estoque', prod.get('quantidade', 0))
            if estoque <= 0:
                continue
                
            qty = 1
            price = float(prod['preco_venda'])
            items_payload.append({
                "id": prod['id'],
                "quantity": qty,
                "discount": 0
            })
            subtotal += price * qty
            
        if not items_payload:
            return # Skip if no valid items found

        total = subtotal
        
        payload = {
            "items": items_payload,
            "subtotal": subtotal,
            "desconto": 0,
            "total": total,
            "paymentMethod": "dinheiro",
            "valor_recebido": total,
            "troco": 0,
            "cliente_id": self.clientes[0]['id'] if self.clientes else None
        }
        
        try:
            resp = requests.post(f"{BASE_URL}/api/pdv/finalizar", json=payload, headers=self.headers)
            duration = (time.time() - start_time) * 1000 # ms
            
            with self.lock:
                self.latencies.append(duration)
                if resp.status_code == 200 or resp.status_code == 201:
                    self.success_count += 1
                    # print(f"Sale {sale_id}: Success ({duration:.0f}ms)")
                else:
                    self.error_count += 1
                    print(f"Sale {sale_id}: Failed ({resp.status_code}) - {resp.text}")
                    
        except Exception as e:
            with self.lock:
                self.error_count += 1
            print(f"Sale {sale_id}: Exception - {e}")

    def run_stress_test(self, num_sales=50, concurrency=10):
        if not self.login():
            return
        if not self.fetch_data():
            return
            
        print(f"\nStarting stress test: {num_sales} sales with {concurrency} threads...")
        start_total = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(self.simulate_sale, i) for i in range(num_sales)]
            for future in futures:
                future.result()
                
        total_duration = time.time() - start_total
        
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        max_latency = max(self.latencies) if self.latencies else 0
        min_latency = min(self.latencies) if self.latencies else 0
        
        print("\n=== RESULTS ===")
        print(f"Total Time: {total_duration:.2f}s")
        print(f"Total Sales: {num_sales}")
        print(f"Successful: {self.success_count}")
        print(f"Failed: {self.error_count}")
        print(f"Throughput: {self.success_count / total_duration:.2f} sales/sec")
        print(f"Avg Latency: {avg_latency:.2f}ms")
        print(f"Min Latency: {min_latency:.2f}ms")
        print(f"Max Latency: {max_latency:.2f}ms")

if __name__ == "__main__":
    test = PDVStressTest()
    # Reduced concurrency for local SQLite environment to avoid database locking
    test.run_stress_test(num_sales=50, concurrency=2)
