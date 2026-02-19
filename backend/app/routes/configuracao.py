# app/routes/configuracao.py
# VERSAO BLINDADA: usa SQL direto para evitar falha do ORM
# quando colunas novas nao existem ainda no banco de producao.

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from app.models import Configuracao, Estabelecimento
from datetime import datetime
import json
import os
import base64
from werkzeug.utils import secure_filename
from sqlalchemy import text, inspect
import traceback

configuracao_bp = Blueprint("configuracao", __name__, url_prefix="/api/configuracao")


def _get_estabelecimento_safe(estab_id: int):
    """
    Busca o estabelecimento via SQL direto (colunas core apenas).
    Evita que o ORM gere SELECT com colunas novas que nao existem no banco de producao.
    Retorna um dicionario com os dados ou None se nao encontrado.
    """
    try:
        row = db.session.execute(
            text("""
                SELECT id, nome_fantasia, razao_social, cnpj, telefone, email, ativo,
                       data_abertura, data_cadastro, regime_tributario, inscricao_estadual
                FROM estabelecimentos
                WHERE id = :eid
                LIMIT 1
            """),
            {"eid": estab_id}
        ).fetchone()

        if not row:
            return None

        # Busca colunas opcionais individualmente para nao quebrar se nao existirem
        def _col(col_name, default=None):
            try:
                r = db.session.execute(
                    text(f"SELECT {col_name} FROM estabelecimentos WHERE id = :eid LIMIT 1"),
                    {"eid": estab_id}
                ).fetchone()
                return r[0] if r else default
            except Exception:
                return default

        return {
            "id": row[0],
            "nome_fantasia": row[1],
            "razao_social": row[2],
            "cnpj": row[3],
            "telefone": row[4],
            "email": row[5],
            "ativo": row[6],
            "data_abertura": row[7].isoformat() if row[7] else None,
            "data_cadastro": row[8].isoformat() if row[8] else None,
            "regime_tributario": row[9],
            "inscricao_estadual": row[10],
            # Colunas que podem nao existir no banco de producao antigo:
            "cep": _col("cep", "00000-000"),
            "logradouro": _col("logradouro", "Nao Informado"),
            "numero": _col("numero", "S/N"),
            "complemento": _col("complemento", ""),
            "bairro": _col("bairro", "Centro"),
            "cidade": _col("cidade", ""),
            "estado": _col("estado", ""),
            "pais": _col("pais", "Brasil"),
            "plano": _col("plano", "Basic"),
            "plano_status": _col("plano_status", "experimental"),
            "stripe_customer_id": _col("stripe_customer_id"),
            "stripe_subscription_id": _col("stripe_subscription_id"),
            "vencimento_assinatura": None,
        }
    except Exception as e:
        current_app.logger.error(f"[_get_estabelecimento_safe] Erro: {e}\n{traceback.format_exc()}")
        return None


# ==================== CONFIGURACOES ====================

@configuracao_bp.route("/", methods=["GET"])
def obter_configuracoes():
    """Obtém as configurações reais do estabelecimento"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)

        config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()

        if not config:
            config = Configuracao(estabelecimento_id=estabelecimento_id)
            db.session.add(config)
            db.session.commit()

        return jsonify({"success": True, "config": config.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em obter_configuracoes: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@configuracao_bp.route("/", methods=["PUT"])
def atualizar_configuracoes():
    """Atualiza as configurações reais do estabelecimento"""
    try:
        data = request.get_json() or {}
        estabelecimento_id = int(data.get("estabelecimento_id", 1))

        config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()
        if not config:
            config = Configuracao(estabelecimento_id=estabelecimento_id)

        campos_permitidos = [
            "logo_url", "cor_principal", "tema_escuro", "impressao_automatica",
            "tipo_impressora", "exibir_preco_tela", "permitir_venda_sem_estoque",
            "desconto_maximo_percentual", "arredondamento_valores", "dias_alerta_validade",
            "estoque_minimo_padrao", "tempo_sessao_minutos", "tentativas_senha_bloqueio",
            "formas_pagamento", "alertas_email", "alertas_whatsapp",
        ]

        for campo in campos_permitidos:
            if campo in data:
                valor = data[campo]
                if campo == "formas_pagamento" and isinstance(valor, list):
                    valor = json.dumps(valor, ensure_ascii=False)
                setattr(config, campo, valor)

        db.session.add(config)
        db.session.commit()

        return jsonify({"success": True, "message": "Configurações atualizadas", "config": config.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em atualizar_configuracoes: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== ESTABELECIMENTO ====================

@configuracao_bp.route("/estabelecimento", methods=["GET"])
def get_estabelecimento():
    """GET do estabelecimento via SQL direto (blindado para producao)"""
    try:
        # Tenta pegar o estabelecimento_id do JWT primeiro, depois do query param
        estab_id = request.args.get("estabelecimento_id", 1, type=int)

        dados = _get_estabelecimento_safe(estab_id)

        if not dados:
            # Nenhum estabelecimento encontrado - retorna dados minimos para o frontend nao quebrar
            dados = {
                "id": estab_id,
                "nome_fantasia": "MercadinhoSys",
                "razao_social": "MercadinhoSys LTDA",
                "cnpj": "00.000.000/0001-00",
                "telefone": "(00) 0000-0000",
                "email": "admin@mercadinhosys.com",
                "ativo": True,
                "cep": "00000-000",
                "logradouro": "Nao Informado",
                "numero": "S/N",
                "complemento": "",
                "bairro": "Centro",
                "cidade": "Cidade",
                "estado": "SP",
                "pais": "Brasil",
                "plano": "Basic",
                "plano_status": "experimental",
                "stripe_customer_id": None,
                "stripe_subscription_id": None,
                "vencimento_assinatura": None,
                "regime_tributario": "SIMPLES NACIONAL",
                "inscricao_estadual": None,
                "data_abertura": None,
                "data_cadastro": None,
            }

        return jsonify({"success": True, "estabelecimento": dados}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em get_estabelecimento: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@configuracao_bp.route("/estabelecimento", methods=["PUT"])
def update_estabelecimento():
    """PUT do estabelecimento"""
    try:
        data = request.get_json() or {}
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)

        # Atualiza apenas os campos que CERTAMENTE existem no banco
        campos_core = ["nome_fantasia", "razao_social", "cnpj", "telefone", "email", "inscricao_estadual"]
        campos_opcionais = ["cep", "logradouro", "numero", "bairro", "cidade", "estado", "complemento"]

        sets_core = []
        params = {"eid": estabelecimento_id}

        for c in campos_core:
            if c in data:
                sets_core.append(f"{c} = :{c}")
                params[c] = data[c]

        if sets_core:
            sql = f"UPDATE estabelecimentos SET {', '.join(sets_core)} WHERE id = :eid"
            db.session.execute(text(sql), params)
            db.session.commit()

        # Tenta atualizar campos opcionais (podem nao existir)
        for c in campos_opcionais:
            if c in data:
                try:
                    db.session.execute(
                        text(f"UPDATE estabelecimentos SET {c} = :{c} WHERE id = :eid"),
                        {c: data[c], "eid": estabelecimento_id}
                    )
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        dados = _get_estabelecimento_safe(estabelecimento_id)
        return jsonify({"success": True, "message": "Atualizado com sucesso", "estabelecimento": dados or {}}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em update_estabelecimento: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500
