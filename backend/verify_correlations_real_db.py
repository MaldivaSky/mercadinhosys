
import sys
import os
import logging
import json
from datetime import datetime, timedelta

# Configura o ambiente para evitar travamentos no setup do DB
os.environ["SKIP_DB_SETUP"] = "true"
os.environ["FLASK_ENV"] = "production"

# Setup logging para stderr (para ver output mesmo se stdout for capturado)
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='max_correlation_verify: %(message)s')
logger = logging.getLogger("verify_real")

def run_verification():
    sys.stderr.write("\n" + "="*80 + "\n")
    sys.stderr.write("🚀 INICIANDO VERIFICAÇÃO COM DADOS REAIS (SEM MOCKS)\n")
    sys.stderr.write("="*80 + "\n")

    try:
        # 1. Inicializar App
        from app import create_app
        from app.models import db
        from app.dashboard_cientifico.models_layer import PracticalModels
        from app.dashboard_cientifico.data_layer import DataLayer
        
        app = create_app()
        
        with app.app_context():
            # 2. Verificar Conexão DB
            db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "UNKNOWN")
            # Mascarar senha
            if "@" in db_uri:
                safe_uri = db_uri.split("@")[1]
            else:
                safe_uri = db_uri
            
            sys.stderr.write(f"🔌 Conectado ao banco: ...{safe_uri}\n")
            
            # Teste rápido de conexão
            from sqlalchemy import text
            try:
                db.session.execute(text("SELECT 1"))
                sys.stderr.write("✅ Conexão SQL ativa.\n")
            except Exception as e:
                sys.stderr.write(f"❌ FALHA DE CONEXÃO: {e}\n")
                return

            # 3. Buscar Dados Reais (DataLayer)
            est_id = 1 # Assumindo ID 1. Se falhar, tentar descobrir.
            days = 365 # Pegar janela grande para garantir dados
            
            sys.stderr.write(f"📊 Buscando dados de vendas para ID={est_id} nos últimos {days} dias...\n")
            
            try:
                sales_data = DataLayer.get_sales_timeseries(est_id, days)
                sys.stderr.write(f"   -> Encontrados {len(sales_data)} registros de vendas diárias.\n")
            except Exception as e:
                sys.stderr.write(f"⚠️ Erro ao buscar sales_timeseries: {e}\n")
                sales_data = []

            # Se não tiver dados, cria um dummy só para passar da primeira guarda
            if not sales_data:
                sys.stderr.write("⚠️  AVISO: Sem vendas retornadas. Criando 1 registro dummy para forçar execução do método.\n")
                sales_data = [{'data': datetime.now().isoformat(), 'total': 100}]

            # 4. Executar Correlações
            sys.stderr.write("🧠 Executando PracticalModels.calculate_correlations...\n")
            
            # Passamos expense_details vazio pois não afeta Hora/Dia
            correlations = PracticalModels.calculate_correlations(sales_data, [], establishment_id=est_id)
            
            sys.stderr.write(f"\n📈 RESULTADOS ({len(correlations)} insights encontrados):\n")
            
            found_target = False
            for c in correlations:
                v1 = c.get('variavel1')
                v2 = c.get('variavel2')
                insight = c.get('insight')
                sys.stderr.write(f"   - {v1} x {v2}: {insight}\n")
                
                if "Hora" in str(v1) or "Semana" in str(v1):
                    found_target = True

            if found_target:
                sys.stderr.write("\n✅ SUCESSO: Correlações temporais (Hora/Dia) foram geradas com dados reais!\n")
            else:
                sys.stderr.write("\n⚠️  AVISO: Correlações específicas não encontradas. Verifique se há vendas no banco.\n")

    except Exception as e:
        sys.stderr.write(f"\n❌ ERRO FATAL: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    # Adicionar diretório atual ao path
    sys.path.append(os.getcwd())
    run_verification()
