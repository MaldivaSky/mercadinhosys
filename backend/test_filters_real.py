
import unittest
import json
from datetime import date
from app import create_app, db
from app.models import Funcionario, Estabelecimento, Produto, CategoriaProduto

class TestProductFilters(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        db.create_all()
        
        # Create Establishment
        self.estab = Estabelecimento(
            nome_fantasia="Test Market",
            razao_social="Test Market LTDA",
            cnpj="00000000000000",
            email="test@market.com",
            telefone="11999999999",
            cep="00000000",
            logradouro="Rua Teste",
            numero="123",
            bairro="Centro",
            cidade="Sao Paulo",
            estado="SP",
            data_abertura=date(2020, 1, 1)
        )
        db.session.add(self.estab)
        db.session.commit()
        
        # Create Admin User
        self.admin = Funcionario(
            estabelecimento_id=self.estab.id,
            nome="Admin",
            username="admin_test",
            email="admin@test.com",
            cpf="00000000000",
            celular="11999999999",
            cargo="Gerente",
            data_admissao=date(2020, 1, 1),
            data_nascimento=date(1990, 1, 1),
            cep="00000000",
            logradouro="Rua Teste",
            numero="123",
            bairro="Centro",
            cidade="Sao Paulo",
            estado="SP",
            role="ADMIN"
        )
        self.admin.set_senha("123456")
        db.session.add(self.admin)
        db.session.commit()
        
        # Login to get token
        resp = self.client.post('/api/auth/login', json={
            "username": "admin_test",
            "senha": "123456"
        })
        self.token = resp.json['data']['access_token']
        self.headers = {'Authorization': f'Bearer {self.token}'}
        
        # Create Categories
        self.cat_bebidas = CategoriaProduto(
            estabelecimento_id=self.estab.id,
            nome="Bebidas"
        )
        self.cat_limpeza = CategoriaProduto(
            estabelecimento_id=self.estab.id,
            nome="Limpeza"
        )
        db.session.add_all([self.cat_bebidas, self.cat_limpeza])
        db.session.commit()
        
        # Create Products
        self.prod_coca = Produto(
            estabelecimento_id=self.estab.id,
            categoria_id=self.cat_bebidas.id,
            nome="Coca Cola",
            preco_custo=5.0,
            preco_venda=10.0,
            quantidade=100
        )
        self.prod_detergente = Produto(
            estabelecimento_id=self.estab.id,
            categoria_id=self.cat_limpeza.id,
            nome="Detergente Ype",
            preco_custo=2.0,
            preco_venda=4.0,
            quantidade=50
        )
        db.session.add_all([self.prod_coca, self.prod_detergente])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_filter_exact_match(self):
        resp = self.client.get('/api/produtos/estoque?categoria=Bebidas', headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json
        self.assertEqual(len(data['produtos']), 1)
        self.assertEqual(data['produtos'][0]['nome'], "Coca Cola")
        print(f"Exact match: Found {len(data['produtos'])} products")

    def test_filter_case_insensitive(self):
        resp = self.client.get('/api/produtos/estoque?categoria=bebidas', headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json
        self.assertEqual(len(data['produtos']), 1)
        self.assertEqual(data['produtos'][0]['nome'], "Coca Cola")
        print(f"Case insensitive: Found {len(data['produtos'])} products")

    def test_filter_normalization(self):
        # Testing extra spaces and lowercase, which normalization should handle
        resp = self.client.get('/api/produtos/estoque?categoria=  bebidas  ', headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json
        self.assertEqual(len(data['produtos']), 1)
        self.assertEqual(data['produtos'][0]['nome'], "Coca Cola")
        print(f"Normalization: Found {len(data['produtos'])} products")
        
    def test_filter_non_existent(self):
        resp = self.client.get('/api/produtos/estoque?categoria=Inexistente', headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json
        self.assertEqual(len(data['produtos']), 0)
        print(f"Non existent: Found {len(data['produtos'])} products")

if __name__ == '__main__':
    unittest.main()
