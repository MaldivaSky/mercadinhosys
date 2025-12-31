# app/routes/configuracao.py

from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Configuracao, Estabelecimento
from datetime import datetime
import os
from werkzeug.utils import secure_filename

config_bp = Blueprint("configuracao", __name__)


@config_bp.route("/", methods=["GET"])
def obter_configuracoes():
    """Obtém as configurações do estabelecimento"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)

        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()

        if not config:
            # Cria configurações padrão se não existirem
            config = Configuracao(estabelecimento_id=estabelecimento_id)
            db.session.add(config)
            db.session.commit()

        return jsonify({"success": True, "config": config.to_dict()}), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao obter configurações: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao obter configurações",
                    "message": str(e),
                }
            ),
            500,
        )


@config_bp.route("/", methods=["PUT"])
def atualizar_configuracoes():
    """Atualiza as configurações do estabelecimento"""
    try:
        data = request.get_json()
        estabelecimento_id = data.get("estabelecimento_id", 1, type=int)

        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()

        if not config:
            config = Configuracao(estabelecimento_id=estabelecimento_id)

        # Campos permitidos para atualização
        campos_permitidos = [
            "logo_url",
            "cor_principal",
            "tema_escuro",
            "impressao_automatica",
            "tipo_impressora",
            "exibir_preco_tela",
            "permitir_venda_sem_estoque",
            "desconto_maximo_percentual",
            "arredondamento_valores",
            "dias_alerta_validade",
            "estoque_minimo_padrao",
            "tempo_sessao_minutos",
            "tentativas_senha_bloqueio",
            "formas_pagamento",
            "alertas_email",
            "alertas_whatsapp",
        ]

        # Atualizar campos permitidos
        for campo in campos_permitidos:
            if campo in data:
                setattr(config, campo, data[campo])

        config.updated_at = datetime.now()
        db.session.add(config)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Configurações atualizadas com sucesso",
                    "config": config.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar configurações: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao atualizar configurações",
                    "message": str(e),
                }
            ),
            500,
        )


@config_bp.route("/logo", methods=["POST"])
def upload_logo():
    """Faz upload da logo do estabelecimento"""
    try:
        estabelecimento_id = request.form.get("estabelecimento_id", 1, type=int)

        if "logo" not in request.files:
            return jsonify({"success": False, "error": "Nenhum arquivo enviado"}), 400

        file = request.files["logo"]

        if file.filename == "":
            return (
                jsonify({"success": False, "error": "Nenhum arquivo selecionado"}),
                400,
            )

        # Validar extensão
        allowed_extensions = {"png", "jpg", "jpeg", "gif", "svg"}
        filename = secure_filename(file.filename)

        if (
            "." not in filename
            or filename.rsplit(".", 1)[1].lower() not in allowed_extensions
        ):
            return (
                jsonify(
                    {"success": False, "error": "Extensão de arquivo não permitida"}
                ),
                400,
            )

        # Criar diretório se não existir
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        logos_folder = os.path.join(upload_folder, "logos")

        if not os.path.exists(logos_folder):
            os.makedirs(logos_folder)

        # Salvar arquivo
        filename = f"logo_{estabelecimento_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{filename.rsplit('.', 1)[1].lower()}"
        filepath = os.path.join(logos_folder, filename)
        file.save(filepath)

        # URL relativa para acesso
        logo_url = f"/uploads/logos/{filename}"

        # Atualizar configuração
        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()

        if not config:
            config = Configuracao(estabelecimento_id=estabelecimento_id)

        config.logo_url = logo_url
        db.session.add(config)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Logo atualizada com sucesso",
                    "logo_url": logo_url,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao fazer upload da logo: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao fazer upload da logo",
                    "message": str(e),
                }
            ),
            500,
        )


@config_bp.route("/estabelecimento", methods=["GET", "PUT"])
def gerenciar_estabelecimento():
    """Obtém ou atualiza dados do estabelecimento"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)

        if request.method == "GET":
            estabelecimento = Estabelecimento.query.get(estabelecimento_id)

            if not estabelecimento:
                return (
                    jsonify(
                        {"success": False, "error": "Estabelecimento não encontrado"}
                    ),
                    404,
                )

            return (
                jsonify(
                    {"success": True, "estabelecimento": estabelecimento.to_dict()}
                ),
                200,
            )

        elif request.method == "PUT":
            data = request.get_json()
            estabelecimento = Estabelecimento.query.get(estabelecimento_id)

            if not estabelecimento:
                return (
                    jsonify(
                        {"success": False, "error": "Estabelecimento não encontrado"}
                    ),
                    404,
                )

            # Atualizar campos permitidos
            campos_permitidos = [
                "nome",
                "telefone",
                "email",
                "endereco",
                "cidade",
                "estado",
            ]

            for campo in campos_permitidos:
                if campo in data:
                    setattr(estabelecimento, campo, data[campo])

            estabelecimento.updated_at = datetime.now()
            db.session.commit()

            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Dados do estabelecimento atualizados com sucesso",
                        "estabelecimento": estabelecimento.to_dict(),
                    }
                ),
                200,
            )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao gerenciar estabelecimento: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerenciar estabelecimento",
                    "message": str(e),
                }
            ),
            500,
        )
