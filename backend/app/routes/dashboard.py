"""
Dashboard Routes - Blueprint limpo e simples
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.dashboard_cientifico import DashboardOrchestrator
from app.models import Funcionario
from app.decorators.decorator_jwt import gerente_ou_admin_required
from app import cache
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)


def make_dashboard_cache_key():
    """
    Gera chave de cache única por estabelecimento.
    Permite que o cache seja compartilhado entre usuários do mesmo estabelecimento.
    """
    try:
        claims = get_jwt()
        est_id = claims.get("estabelecimento_id")
        return f"dashboard_cientifico_v1:{est_id}"
    except Exception:
        return None  # Não cacheia se falhar ao pegar ID


def get_establishment_id():
    """
    Obtém ID do estabelecimento diretamente das Claims do JWT (sem consulta ao banco).
    Garante integridade e performance.
    """
    claims = get_jwt()
    est_id = claims.get("estabelecimento_id")
    
    if est_id is None:
        # Fallback apenas para logs de erro, não tenta query no banco
        raise ValueError("Token inválido: estabelecimento_id não encontrado nas claims")
        
    return int(est_id)


@dashboard_bp.route("/cientifico", methods=["GET"])
@gerente_ou_admin_required
@cache.cached(timeout=900, key_prefix=make_dashboard_cache_key)
def dashboard_cientifico():
    """
    Endpoint para o Dashboard Científico.
    Utiliza Cache (Redis/Mem) por 15 minutos para evitar sobrecarga no DB.
    """
    try:
        # 1. Obter contexto seguro (já validado pelo decorator)
        estabelecimento_id = get_establishment_id()
        
        # 2. Orquestração (Injeção de Dependência Simplificada)
        # O Orchestrator encapsula a complexidade e acesso a dados
        orchestrator = DashboardOrchestrator(estabelecimento_id)
        
        # 3. Execução Direta (Contrato Definido)
        # Removemos checks de hasattr para forçar consistência de contrato
        data = orchestrator.get_scientific_dashboard()

        # 4. Resposta Padronizada
        return jsonify({
            "success": True,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0",
                "cached": True # Flag para indicar que esta rota usa cache
            },
            "data": data
        }), 200
        
    except Exception as e:
        # Log detalhado para debug de infraestrutura
        logger.error(f"Erro Crítico Dashboard Científico: {e}", exc_info=True)
        
        # Diferenciação básica de erros (poderia ser expandida)
        error_msg = str(e)
        status_code = 500
        
        # Se for erro de conexão ou infra, mantém 500.
        # Se fosse erro de negócio conhecido, poderia ser 400/422.
        
        return jsonify({
            "success": False,
            "error": "Erro interno ao processar indicadores",
            "details": error_msg if current_app.debug else "Contate o suporte"
        }), status_code






@dashboard_bp.route("/executivo", methods=["GET"])
@gerente_ou_admin_required
def dashboard_executivo():
    try:
        estabelecimento_id = get_establishment_id()
        days = request.args.get("days", default=30, type=int)
        orchestrator = DashboardOrchestrator(estabelecimento_id)
        dashboard_data = orchestrator.get_executive_dashboard(days)
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Erro no dashboard executivo: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/analise/<tipo>", methods=["GET"])
@gerente_ou_admin_required
def analise_detalhada(tipo: str):
    try:
        estabelecimento_id = get_establishment_id()
        days = request.args.get("days", default=90, type=int)
        orchestrator = DashboardOrchestrator(estabelecimento_id)
        analysis_data = orchestrator.get_detailed_analysis(tipo, days)
        return jsonify({"success": True, "analysis_type": tipo, "data": analysis_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/status", methods=["GET"])
@jwt_required()
def dashboard_status():
    return jsonify({"status": "operational"})
