"""
Dashboard Routes - Blueprint limpo e simples
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.dashboard_cientifico import DashboardOrchestrator
from app.models import Funcionario
import logging

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)


def get_establishment_id():
    """Obtém ID do estabelecimento do usuário logado"""
    user_id = get_jwt_identity()
    funcionario = Funcionario.query.get(user_id)
    if not funcionario:
        raise ValueError("Usuário não encontrado")
    return funcionario.estabelecimento_id


@dashboard_bp.route("/cientifico", methods=["GET"])
@jwt_required()
def dashboard_cientifico():
    """Endpoint para o Dashboard Científico"""
    try:
        estabelecimento_id = get_establishment_id()
        try:
            orchestrator = DashboardOrchestrator(estabelecimento_id)
            if hasattr(orchestrator, "get_scientific_dashboard"):
                data = orchestrator.get_scientific_dashboard()
            else:
                data = orchestrator.get_executive_dashboard(30)
        except Exception as e:
            logger.warning(f"Orquestrador indisponível: {e}")
            data = {}

        response = {
            "success": True,
            "usuario": {"nome": "Admin", "role": "admin", "acesso_avancado": True},
            "data": data if data and "hoje" in data else _get_mock_data(),
        }
        return jsonify(response)
    except Exception as e:
        logger.error(f"Erro Crítico Dashboard: {e}")
        return jsonify({"success": False, "data": _get_mock_data()}), 200


def _get_mock_data():
    return {
        "hoje": {
            "total_vendas": 0,
            "ticket_medio": 0,
            "clientes_atendidos": 0,
            "crescimento_vs_ontem": 0,
        },
        "mes": {
            "total_vendas": 0,
            "lucro_bruto": 0,
            "margem_lucro": 0,
            "roi_mensal": 0,
            "investimentos": 0,
        },
        "analise_produtos": {
            "curva_abc": {
                "pareto_80_20": False,
                "produtos": [],
                "resumo": {
                    "A": {"percentual": 0},
                    "B": {"percentual": 0},
                    "C": {"percentual": 0},
                },
            },
            "produtos_estrela": [],
            "produtos_lentos": [],
            "previsao_demanda": [],
        },
        "analise_financeira": {
            "despesas_detalhadas": [],
            "margens": {"bruta": 0, "operacional": 0, "liquida": 0},
            "indicadores": {"ponto_equilibrio": 0, "margem_seguranca": 0, "ebitda": 0},
        },
        "insights_cientificos": {
            "correlações": [],
            "previsoes": [],
            "recomendacoes_otimizacao": [],
        },
    }


@dashboard_bp.route("/executivo", methods=["GET"])
@jwt_required()
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
@jwt_required()
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
