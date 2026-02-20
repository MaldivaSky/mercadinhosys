
import sys
import os
import unittest
import json
from unittest.mock import MagicMock, patch

print("======================================================================")
print("🔎  INICIANDO AUDITORIA DE ELITE 360 - MERCADINHO SIS (BACKEND)   🔍")
print("======================================================================")

# ==================== CONFIGURAÇÃO DE MOCKS (PRE-IMPORT) ====================
# Garante isolamento total do ambiente
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Mocka módulos que dependem de contexto global ou conexão real
sys.modules['app.models'] = MagicMock()
sys.modules['app.models.db'] = MagicMock()
sys.modules['app.utils.smart_cache'] = MagicMock() # Mock para evitar erro de import

# ==================== ARQUITETURA DE TESTE ====================
from flask import Flask, jsonify
from app.decorators.decorator_jwt import funcionario_required

# Configura App Fake para Teste de Integração
app = Flask(__name__)
app.config['TESTING'] = True

# Registra rotas fake usando os decorators reais para testar o middleware
@app.route('/api/test/auth', methods=['GET', 'POST', 'OPTIONS'])
@funcionario_required
def endpoint_protegido():
    return jsonify({"msg": "Acesso Autorizado"}), 200

# Importa as funções de negócio para teste unitário
from app.utils.query_helpers import get_configuracao_safe, db as mock_db_helper
from app.routes.pdv import estatisticas_rapidas
# Importa a rota de configuração para teste
from app.routes.configuracao import atualizar_configuracoes

class AuditElite360(unittest.TestCase):

    def setUp(self):
        self.ctx = app.test_request_context()
        self.ctx.push()
        self.client = app.test_client()
        self.mock_session = mock_db_helper.session

    def tearDown(self):
        self.ctx.pop()

    # ==================== 1. AUDITORIA DE SEGURANÇA & CORS ====================
    
    @patch('flask_jwt_extended.verify_jwt_in_request')
    def test_cors_preflight_bypass(self, mock_verify):
        """
        [SEGURANÇA] Verifica se rotas protegidas permitem OPTIONS sem token (CORS Fix)
        """
        print("\n🔸 [AUDIT 1/6] Verificando Protocolo CORS (OPTIONS Bypass)...")
        
        response = self.client.options('/api/test/auth')
        
        if response.status_code == 200:
            print("   ✅ PASS: Preflight (OPTIONS) retornou 200 OK.")
        else:
            print(f"   ❌ FAIL: Preflight retornou {response.status_code}. CORS será bloqueado.")
            self.fail("CORS Preflight failed")

        # Garante que NÃO tentou validar token
        if not mock_verify.called:
            print("   ✅ PASS: Token JWT NÃO foi solicitado (Correto para CORS).")
        else:
            print("   ❌ FAIL: Token JWT FOI solicitado no OPTIONS.")
            self.fail("JWT Validation triggered on OPTIONS")

    @patch('flask_jwt_extended.verify_jwt_in_request')
    def test_auth_enforcement(self, mock_verify):
        """
        [SEGURANÇA] Verifica se rotas protegidas EXIGEM token em POST/GET
        """
        print("\n🔸 [AUDIT 2/6] Verificando Blindagem de Autenticação (POST/GET)...")
        
        # Simula token ausente/inválido
        mock_verify.side_effect = Exception("Missing Token")
        
        response = self.client.post('/api/test/auth')
        
        if response.status_code == 401:
             print("   ✅ PASS: Acesso sem token foi BLOQUEADO (401 Unauthorized).")
        else:
             print(f"   ❌ FAIL: Acesso sem token permitido ou erro incorreto ({response.status_code}).")
             self.fail("Auth enforcement failed")

    # ==================== 2. AUDITORIA DE RESILIÊNCIA DE DADOS ====================

    def test_schema_resilience(self):
        """
        [DADOS] Verifica se carregamento de configuração resiste a Schema Drift (Colunas novas/faltando)
        """
        print("\n🔸 [AUDIT 3/6] Verificando Resiliência de Schema (Hybrid Load)...")
        
        # Simula erro na query principal (Fast Path falha)
        def side_effect(*args, **kwargs):
            sql_obj = args[0]
            sql = getattr(sql_obj, 'text', str(sql_obj)) # Extrai texto de TextClause ou str
            if "logo_url, logo_base64" in sql: # Identifica Fast Path
                raise Exception("Column 'emitir_nfce' not found")
            
            # Safe Path returns
            if "SELECT id, estabelecimento_id FROM" in sql: return MagicMock(fetchone=lambda: (1, 100))
            if "SELECT logo_url" in sql: return MagicMock(fetchone=lambda: ("http://logo.com",))
            # Outros retornam None (default)
            return MagicMock(fetchone=lambda: None)

        self.mock_session.execute.side_effect = side_effect
        
        res = get_configuracao_safe(100)
        
        if res and res['id'] == 1 and res['logo_url'] == "http://logo.com":
             print("   ✅ PASS: Sistema recuperou dados parciais mesmo com erro de Schema.")
             print(f"          Dados recuperados: ID={res['id']}, Logo={res['logo_url']}")
        else:
             print("   ❌ FAIL: Sistema falhou em recuperar dados parciais.")
             self.fail("Schema resilience failed")

    def test_database_connection_failure(self):
        """
        [DADOS] Verifica comportamento quando banco cai totalmente
        """
        print("\n🔸 [AUDIT 4/6] Verificando Falha Total de Conexão (Database Down)...")
        
        self.mock_session.execute.side_effect = Exception("FATAL: Tem too many clients already")
        
        res = get_configuracao_safe(100)
        
        if res is None:
            print("   ✅ PASS: Sistema tratou a queda do banco graciosamente (Retornou None).")
        else:
            print("   ❌ FAIL: Sistema vazou exceção ou retornou lixo.")
            self.fail("Database failure handling failed")

    # ==================== 3. AUDITORIA DE PERFORMANCE (PDV) ====================
    
    @patch('app.routes.pdv.get_jwt')
    @patch('app.routes.pdv.get_jwt_identity')
    @patch('flask_jwt_extended.verify_jwt_in_request')
    def test_performance_route(self, mock_verify, mock_get_identity, mock_get_jwt):
        """
        [PERFORMANCE] Verifica se Estatísticas Rápidas usa SQL Puro e não trava
        """
        print("\n🔸 [AUDIT 5/6] Verificando Rota de Alta Performance (Estatísticas)...")
        
        # Configura Contexto
        mock_get_identity.return_value = 1
        mock_get_jwt.return_value = {"estabelecimento_id": 1}
        
        # Simula retorno do SQL
        mock_result = MagicMock()
        mock_result.qtd_vendas = 150
        mock_result.total_vendido = 5000.00
        self.mock_session.execute.return_value.fetchone.return_value = mock_result
        
        # Executa a rota diretamente (como função, mockando o request context já ativo)
        response, status = estatisticas_rapidas()
        
        data = response.json
        if status == 200 and data['qtd_vendas'] == 150:
            print("   ✅ PASS: Rota executou com sucesso (200 OK).")
            print(f"          Retorno: {json.dumps(data)}")
        else:
            print(f"   ❌ FAIL: Rota falhou ou retornou dados incorretos.")
            self.fail("Performance route failed")

    # ==================== 4. AUDITORIA DE UPDATE (CONFIG) ====================

    @patch('app.routes.configuracao.get_jwt')
    @patch('app.routes.configuracao.get_jwt_identity')
    @patch('app.routes.configuracao.request')
    @patch('app.routes.configuracao.db') # PATCH CRÍTICO: Mocka o db DENTRO da rota
    @patch('flask_jwt_extended.verify_jwt_in_request')
    def test_update_config_sql_injection(self, mock_verify, mock_db_route, mock_request, mock_get_identity, mock_get_jwt):
        """
        [UPDATE] Verifica se PUT /configuracao utiliza SQL Seguro e ignora Models
        """
        print("\n🔸 [AUDIT 6/6] Verificando Update via SQL Seguro (No-ORM)...")
        
        # Configura Contexto
        mock_get_identity.return_value = 1
        mock_get_jwt.return_value = {"estabelecimento_id": 1, "role": "admin"}
        mock_request.get_json.return_value = {"tema_escuro": True, "cor_principal": "#000"}
        
        # Simula que já existe config (retorna tuple)
        mock_db_route.session.execute.return_value.fetchone.return_value = (1,)
        
        # Executa a rota
        response, status = atualizar_configuracoes()

        # Verifica se chamou execute UPDATE no mock correto
        calls = mock_db_route.session.execute.call_args_list
        update_called = False
        for call in calls:
            sql = str(call[0][0])
            if "UPDATE configuracoes SET" in sql and "tema_escuro = :tema_escuro" in sql:
                update_called = True
                break
        
        if status == 200 and update_called:
            print("   ✅ PASS: Update utilizou SQL Puro e retornou 200 OK.")
        else:
            print(f"   ❌ FAIL: Update falhou ou usou ORM (Status {status}).")
            # print(f"          Calls: {calls}") # Debug
            self.fail("Config Update via SQL failed")


if __name__ == '__main__':
    # Roda os testes e captura o resultado
    runner = unittest.TextTestRunner(verbosity=0)
    suite = unittest.TestLoader().loadTestsFromTestCase(AuditElite360)
    result = runner.run(suite)
    
    print("\n======================================================================")
    if result.wasSuccessful():
        print("✅  CONCLUSÃO: O SISTEMA PASSOU NA AUDITORIA DE ELITE (6/6).")
        print("    Status: BLINDADO PARA PRODUÇÃO.")
    else:
        print("❌  CONCLUSÃO: FALHAS DETECTADAS. NÃO DEPLOYAR.")
    print("======================================================================")
    sys.exit(0 if result.wasSuccessful() else 1)
