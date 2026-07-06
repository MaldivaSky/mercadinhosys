from locust import HttpUser, task, between
import random
import uuid

class MercadinhoUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        Executado quando cada usuário virtual inicia.
        Cria uma sessão válida simulando um login em uma conta DEMO fixa
        (ou cria uma conta por worker se necessário).
        Para teste de carga real sem sujar o banco, usaremos um token mockado ou 
        apenas endpoints públicos e leituras no banco.
        """
        # Exemplo simples: chamamos a rota de health para checar se está vivo
        self.client.get("/api/health")
        
        # Em um teste real E2E, o Locust faria login aqui:
        # response = self.client.post("/api/auth/login", json={"email": "demo@test.com", "password": "pass"})
        # self.token = response.json()["access_token"]
        # self.headers = {"Authorization": f"Bearer {self.token}"}
        
    @task(3)
    def check_health(self):
        """Simula monitoramento constante do app"""
        self.client.get("/api/health")

    @task(1)
    def public_checkout(self):
        """Simula acessos simultâneos na página pública de compra (Checkout)"""
        # Bate na rota de checkout (que consulta o banco para validar plano)
        self.client.post("/api/billing/public-checkout", json={
            "email": f"loadtest_{uuid.uuid4().hex[:6]}@test.com",
            "plan_name": "Premium"
        })
        
    @task(2)
    def view_onboarding(self):
        """Simula requisições à rota GET de dados auxiliares se existir, 
        ou simula tentativas de onboarding com erro (para estressar validação)"""
        self.client.post("/api/saas/onboarding", json={
            "nome_fantasia": "",  # Força validação de erro (400)
            "email_admin": "invalido",
        })
