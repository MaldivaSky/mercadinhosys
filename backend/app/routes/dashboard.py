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


# Helper para obter estabelecimento
def get_establishment_id():
    """Obtém ID do estabelecimento do usuário logado"""
    user_id = get_jwt_identity()
    funcionario = Funcionario.query.get(user_id)
    if not funcionario:
        raise ValueError("Usuário não encontrado")
    return funcionario.estabelecimento_id


# Endpoints principais
@dashboard_bp.route("/executivo", methods=["GET"])
@jwt_required()
def dashboard_executivo():
    """Dashboard executivo - Resumo para gestão"""
    try:
        estabelecimento_id = get_establishment_id()
        days = request.args.get("days", default=30, type=int)

        orchestrator = DashboardOrchestrator(estabelecimento_id)
        dashboard_data = orchestrator.get_executive_dashboard(days)

        return jsonify(dashboard_data)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Erro no dashboard executivo: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar dashboard",
                    "message": str(e),
                }
            ),
            500,
        )


@dashboard_bp.route("/analise/<tipo>", methods=["GET"])
@jwt_required()
def analise_detalhada(tipo: str):
    """Análise detalhada por tipo (sales, inventory, customers)"""
    try:
        estabelecimento_id = get_establishment_id()
        days = request.args.get("days", default=90, type=int)

        orchestrator = DashboardOrchestrator(estabelecimento_id)
        analysis_data = orchestrator.get_detailed_analysis(tipo, days)

        return jsonify({"success": True, "analysis_type": tipo, "data": analysis_data})

    except Exception as e:
        logger.error(f"Erro na análise {tipo}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Erro na análise {tipo}",
                    "message": str(e),
                }
            ),
            500,
        )


@dashboard_bp.route("/status", methods=["GET"])
@jwt_required()
def dashboard_status():
    """Status do dashboard"""
    try:
        estabelecimento_id = get_establishment_id()

        # Verificações básicas
        from app import db
        from sqlalchemy import text

        # Verificar conexão com banco
        db.session.execute(text("SELECT 1"))

        # Contar dados básicos
        from app.models import Venda, Produto

        total_vendas = Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id
        ).count()

        total_produtos = Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id, Produto.ativo == True
        ).count()

        return jsonify(
            {
                "status": "operational",
                "module": "dashboard_cientifico_v2",
                "establishment_id": estabelecimento_id,
                "data_points": {"sales": total_vendas, "products": total_produtos},
                "endpoints": {
                    "executive": "/api/dashboard/executivo?days=30",
                    "sales_analysis": "/api/dashboard/analise/sales?days=90",
                    "inventory_analysis": "/api/dashboard/analise/inventory",
                },
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@dashboard_bp.route("/cache/clear", methods=["POST"])
@jwt_required()
def clear_cache():
    """Limpa cache do dashboard (apenas admin)"""
    try:
        # Verificar se usuário é admin
        user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(user_id)

        if funcionario.nivel_acesso not in ["admin", "dono"]:
            return jsonify({"error": "Acesso negado"}), 403

        from app.dashboard_cientifico.cache_layer import SmartCache

        SmartCache.invalidate_pattern("dashboard")

        return jsonify({"success": True, "message": "Cache do dashboard limpo"})

    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        return jsonify({"error": str(e)}), 500
