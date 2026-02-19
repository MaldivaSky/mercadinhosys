# app/routes/configuracao.py

from flask import Blueprint, request, jsonify, current_app
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

@configuracao_bp.route("/", methods=["GET"])
def obter_configuracoes():
    """Obtém as configurações reais do estabelecimento"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        
        # O banco Aiven agora possui todas as colunas via bootstrap sync
        config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()
        
        if not config:
            # Cria se não existir
            config = Configuracao(estabelecimento_id=estabelecimento_id)
            db.session.add(config)
            db.session.commit()
            
        return jsonify({"success": True, "config": config.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        current_app.logger.error(f"❌ Erro Real em obter_configuracoes: {str(e)}\n{traceback.format_exc()}")
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

        config.updated_at = datetime.now()
        db.session.add(config)
        db.session.commit()

        return jsonify({"success": True, "message": "Configurações atualizadas", "config": config.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@configuracao_bp.route("/estabelecimento", methods=["GET", "PUT"])
def gerenciar_estabelecimento():
    """Gerenciamento real do estabelecimento"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        
        if request.method == "GET":
            estabelecimento = Estabelecimento.query.get(estabelecimento_id)
            if not estabelecimento:
                # Criar estabelecimento padrão se não existir (vazio mas com ID)
                estabelecimento = Estabelecimento(
                    id=estabelecimento_id,
                    nome_fantasia="Novo Estabelecimento",
                    razao_social="Nova Empresa LTDA",
                    cnpj=f"00.000.000/0001-{str(datetime.now().timestamp())[-2:]}",
                    telefone="(00) 0000-0000",
                    email="admin@admin.com",
                    cep="00000-000",
                    logradouro="Rua Exemplo",
                    numero="0",
                    bairro="Centro",
                    cidade="Cidade",
                    estado="SP",
                    data_abertura=datetime.now().date()
                )
                db.session.add(estabelecimento)
                db.session.commit()
            
            return jsonify({"success": True, "estabelecimento": estabelecimento.to_dict()}), 200

        elif request.method == "PUT":
            data = request.get_json()
            estabelecimento = Estabelecimento.query.get(estabelecimento_id)
            if not estabelecimento:
                return jsonify({"success": False, "error": "Não encontrado"}), 404
            
            campos = ["nome_fantasia", "razao_social", "cnpj", "telefone", "email", 
                      "cep", "logradouro", "numero", "bairro", "cidade", "estado", 
                      "inscricao_estadual", "complemento"]
            
            for c in campos:
                if c in data: setattr(estabelecimento, c, data[c])
            
            db.session.commit()
            return jsonify({"success": True, "message": "Atualizado com sucesso", "estabelecimento": estabelecimento.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro Real em Estabelecimento: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
