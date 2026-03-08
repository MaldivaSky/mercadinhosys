# app/routes/monitor.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db, Auditoria, Estabelecimento, Venda, Funcionario
from sqlalchemy import func
from datetime import datetime, timedelta

monitor_bp = Blueprint("monitor", __name__)

def super_admin_required(fn):
    """Custom decorator for super admin routes"""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("is_super_admin") is True:
            return fn(*args, **kwargs)
        
        return jsonify({"success": False, "error": "Acesso restrito ao Administrador do Sistema"}), 403
    return jwt_required()(wrapper)

@monitor_bp.route("/logs", methods=["GET"])
@super_admin_required
def get_global_logs():
    """Retorna logs de auditoria de todos os estabelecimentos"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        tipo = request.args.get("tipo")
        estab_id = request.args.get("estabelecimento_id", type=int)

        query = Auditoria.query

        if tipo:
            query = query.filter(Auditoria.tipo_evento == tipo)
        if estab_id:
            query = query.filter(Auditoria.estabelecimento_id == estab_id)

        logs_pagination = query.order_by(Auditoria.data_evento.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            "success": True,
            "logs": [log.to_dict() for log in logs_pagination.items],
            "total": logs_pagination.total,
            "pages": logs_pagination.pages,
            "current_page": logs_pagination.page
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@monitor_bp.route("/summary", methods=["GET"])
@super_admin_required
def get_global_summary():
    """Retorna resumo estatístico global do sistema"""
    try:
        hoje = datetime.utcnow().date()
        
        total_estabelecimentos = Estabelecimento.query.count()
        total_vendas_hoje = Venda.query.filter(func.date(Venda.data_venda) == hoje).count()
        valor_vendas_hoje = db.session.query(func.sum(Venda.total)).filter(func.date(Venda.data_venda) == hoje).scalar() or 0
        
        # Últimos eventos importantes
        ultimos_registros = Auditoria.query.filter(Auditoria.tipo_evento == "estabelecimento_registrado").order_by(Auditoria.data_evento.desc()).limit(5).all()

        return jsonify({
            "success": True,
            "summary": {
                "total_estabelecimentos": total_estabelecimentos,
                "vendas_hoje_qtd": total_vendas_hoje,
                "vendas_hoje_valor": float(valor_vendas_hoje),
                "novos_clientes_recentes": [
                    {
                        "nome": log.detalhes.get("estabelecimento") if log.detalhes else "N/A",
                        "data": log.data_evento.isoformat()
                    } for log in ultimos_registros
                ]
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
