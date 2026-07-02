"""
Auditoria do TENANT — cada loja vê apenas os próprios logs.
(O superadmin usa /api/saas/monitor/logs, que vê todos os estabelecimentos.)
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from app.models import db, Auditoria
from app.utils.query_helpers import ilike_unaccent, get_authorized_establishment_id

auditoria_bp = Blueprint("auditoria", __name__)


@auditoria_bp.route("/", methods=["GET"])
@jwt_required()
def listar_auditoria():
    """Logs de auditoria do próprio estabelecimento, paginados e filtráveis."""
    try:
        estab_id = get_authorized_establishment_id()
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 30, type=int), 100)
        tipo = request.args.get("tipo")
        busca = (request.args.get("q") or "").strip()

        # Auditoria.query (TenantQuery) já filtra por g.estabelecimento_id.
        # Filtro explícito reforça o escopo e cobre o superadmin (estab_id selecionado).
        q = Auditoria.query
        if estab_id and str(estab_id).lower() != "all":
            q = q.filter(Auditoria.estabelecimento_id == estab_id)
        if tipo:
            q = q.filter(Auditoria.tipo_evento == tipo)
        if busca:
            q = q.filter(ilike_unaccent(Auditoria.descricao, f"%{busca}%"))

        pag = q.order_by(Auditoria.data_evento.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return jsonify({
            "success": True,
            "logs": [l.to_dict() for l in pag.items],
            "paginacao": {"pagina": pag.page, "total_paginas": pag.pages, "total": pag.total},
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro em listar_auditoria: {e}")
        return jsonify({"success": False, "error": "Falha ao listar auditoria"}), 500


@auditoria_bp.route("/resumo", methods=["GET"])
@jwt_required()
def resumo_auditoria():
    """Contagem por tipo de evento (para chips de filtro)."""
    try:
        from sqlalchemy import func
        estab_id = get_authorized_establishment_id()
        q = db.session.query(Auditoria.tipo_evento, func.count(Auditoria.id))
        if estab_id and str(estab_id).lower() != "all":
            q = q.filter(Auditoria.estabelecimento_id == estab_id)
        tipos = [{"tipo": t, "total": c} for t, c in q.group_by(Auditoria.tipo_evento).all()]
        return jsonify({"success": True, "tipos": sorted(tipos, key=lambda x: -x["total"])}), 200
    except Exception as e:
        current_app.logger.error(f"Erro em resumo_auditoria: {e}")
        return jsonify({"success": False, "error": "Falha ao resumir auditoria"}), 500
