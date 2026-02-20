# app/routes/configuracao.py
"""
Módulo de Configuração de Elite - MercadinhoSys
Gerenciamento resiliente de configurações e dados do estabelecimento.
Usa SQL direto via query_helpers para evitar falhas de ORM em produção.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from app.models import Configuracao
from app.utils.query_helpers import get_configuracao_safe, get_estabelecimento_full_safe
from app.utils.smart_cache import get_cached_config, set_cached_config, invalidate_config
import json
import traceback

configuracao_bp = Blueprint("configuracao", __name__)

# ==================== CONFIGURAÇÕES ====================

@configuracao_bp.route("/", methods=["GET"])
@jwt_required()
def obter_configuracoes():
    """Obtém configurações do estabelecimento (Padrão Blindado)"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        if not estabelecimento_id:
            return jsonify({"success": False, "error": "Estabelecimento não identificado no token"}), 400

        # Tenta buscar do cache primeiro
        config_data = get_cached_config(estabelecimento_id)
        if config_data:
            return jsonify({"success": True, "config": config_data}), 200

        config_data = get_configuracao_safe(estabelecimento_id)
        
        # Se não existir, tenta criar uma padrão via ORM (operação segura inicial)
        if not config_data:
            try:
                nova_config = Configuracao(estabelecimento_id=estabelecimento_id)
                db.session.add(nova_config)
                db.session.commit()
                config_data = get_configuracao_safe(estabelecimento_id)
            except Exception:
                db.session.rollback()
                # Fallback total: retorna objeto default em memória
                config_data = {
                    "cor_principal": "#007bff",
                    "tema_escuro": False,
                    "formas_pagamento": "[]"
                }

        # Salva no cache se encontrou ou criou
        set_cached_config(estabelecimento_id, config_data)

        return jsonify({
            "success": True, 
            "config": config_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"❌ Erro em obter_configuracoes: {str(e)}")
        return jsonify({"success": False, "error": "Erro ao carregar configurações"}), 500


@configuracao_bp.route("/", methods=["PUT"])
@jwt_required()
def atualizar_configuracoes():
    """Atualiza as configurações do estabelecimento com auditoria"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        role = claims.get("role")
        
        if role not in ["admin", "dono", "gerente", "ADMIN"]:
            return jsonify({"success": False, "error": "Sem permissão para alterar configurações"}), 403

        data = request.get_json() or {}
        config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()
        
        if not config:
            config = Configuracao(estabelecimento_id=estabelecimento_id)

        # Campos permitidos para atualização via PDV/Config
        perm = [
            "logo_url", "cor_principal", "tema_escuro", "impressao_automatica",
            "tipo_impressora", "formas_pagamento"
        ]

        for campo in perm:
            if campo in data:
                valor = data[campo]
                if campo == "formas_pagamento" and isinstance(valor, list):
                    valor = json.dumps(valor, ensure_ascii=False)
                setattr(config, campo, valor)

        db.session.add(config)
        db.session.commit()

        # Invalida o cache para forçar recarregamento
        invalidate_config(estabelecimento_id)

        return jsonify({
            "success": True, 
            "message": "Configurações atualizadas com sucesso",
            "config": get_configuracao_safe(estabelecimento_id)
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em atualizar_configuracoes: {str(e)}")
        return jsonify({"success": False, "error": "Erro ao salvar configurações"}), 500


# ==================== ESTABELECIMENTO ====================

@configuracao_bp.route("/estabelecimento", methods=["GET"])
@jwt_required()
def get_estabelecimento():
    """Retorna dados do estabelecimento com resiliência total"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        dados = get_estabelecimento_full_safe(estabelecimento_id)

        if not dados:
            return jsonify({"success": False, "error": "Dados do estabelecimento não encontrados"}), 404

        return jsonify({
            "success": True, 
            "estabelecimento": dados
        }), 200

    except Exception as e:
        current_app.logger.error(f"❌ Erro em get_estabelecimento: {str(e)}")
        return jsonify({"success": False, "error": "Erro ao carregar dados da empresa"}), 500


@configuracao_bp.route("/estabelecimento", methods=["PUT"])
@jwt_required()
def update_estabelecimento():
    """Atualização segura do estabelecimento (Somente Admin/Dono)"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        role = claims.get("role")
        
        if role not in ["admin", "dono", "ADMIN"]:
            return jsonify({"success": False, "error": "Apenas proprietários podem alterar dados da empresa"}), 403

        data = request.get_json() or {}
        
        # Filtro de segurança: apenas campos cadastrais básicos
        campos_update = ["nome_fantasia", "razao_social", "telefone", "email"]
        
        from sqlalchemy import text
        set_clauses = []
        params = {"eid": estabelecimento_id}
        
        for c in campos_update:
            if c in data:
                set_clauses.append(f"{c} = :{c}")
                params[c] = data[c]
        
        if set_clauses:
            sql = f"UPDATE estabelecimentos SET {', '.join(set_clauses)} WHERE id = :eid"
            db.session.execute(text(sql), params)
            db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Dados da empresa atualizados",
            "estabelecimento": get_estabelecimento_full_safe(estabelecimento_id)
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em update_estabelecimento: {str(e)}")
        return jsonify({"success": False, "error": "Falha ao atualizar dados"}), 500
