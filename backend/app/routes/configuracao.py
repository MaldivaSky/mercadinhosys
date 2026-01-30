# app/routes/configuracao.py

from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Configuracao, Estabelecimento
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
from sqlalchemy import text

configuracao_bp = Blueprint("configuracao", __name__, url_prefix="/api/configuracao")

def ensure_configuracoes_schema():
    try:
        result = db.session.execute(text("PRAGMA table_info(configuracoes)")).fetchall()
        cols = {row[1] for row in result}
        ddl = []
        if "tema_escuro" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN tema_escuro INTEGER DEFAULT 0"))
        if "cor_principal" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN cor_principal VARCHAR(7) DEFAULT '#2563eb'"))
        if "emitir_nfe" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN emitir_nfe INTEGER DEFAULT 0"))
        if "impressao_automatica" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN impressao_automatica INTEGER DEFAULT 0"))
        if "tipo_impressora" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN tipo_impressora VARCHAR(20) DEFAULT 'termica_80mm'"))
        if "exibir_preco_tela" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN exibir_preco_tela INTEGER DEFAULT 1"))
        if "permitir_venda_sem_estoque" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN permitir_venda_sem_estoque INTEGER DEFAULT 0"))
        if "desconto_maximo_percentual" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN desconto_maximo_percentual NUMERIC(5,2) DEFAULT 10.00"))
        if "arredondamento_valores" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN arredondamento_valores INTEGER DEFAULT 1"))
        if "formas_pagamento" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN formas_pagamento TEXT DEFAULT '[\"Dinheiro\", \"Cartão de Crédito\", \"Cartão de Débito\", \"PIX\"]'"))
        if "dias_alerta_validade" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN dias_alerta_validade INTEGER DEFAULT 30"))
        if "estoque_minimo_padrao" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN estoque_minimo_padrao INTEGER DEFAULT 10"))
        if "tempo_sessao_minutos" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN tempo_sessao_minutos INTEGER DEFAULT 30"))
        if "tentativas_senha_bloqueio" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN tentativas_senha_bloqueio INTEGER DEFAULT 3"))
        if "alertas_email" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN alertas_email INTEGER DEFAULT 0"))
        if "alertas_whatsapp" not in cols:
            ddl.append(text("ALTER TABLE configuracoes ADD COLUMN alertas_whatsapp INTEGER DEFAULT 0"))
        for stmt in ddl:
            try:
                db.session.execute(stmt)
            except Exception:
                pass
        if ddl:
            db.session.commit()
    except Exception:
        pass

@configuracao_bp.route("/", methods=["GET"])
def obter_configuracoes():
    """Obtém as configurações do estabelecimento"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)

        ensure_configuracoes_schema()

        # Garantir que o estabelecimento exista
        estabelecimento = Estabelecimento.query.get(estabelecimento_id)
        if not estabelecimento:
            # Gerar CNPJ placeholder único com 14 dígitos e formato válido (18 caracteres com pontuação)
            raw = datetime.now().strftime("%H%M%S%f")  # ex: 141523123456
            digits = (raw + "00000000000000")[:14]
            cnpj_placeholder = f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"
            estabelecimento = Estabelecimento(
                id=estabelecimento_id,
                nome_fantasia="Empresa Padrão",
                razao_social="Empresa Padrão LTDA",
                cnpj=cnpj_placeholder,
                telefone="(00) 0000-0000",
                email="contato@empresa.com",
                cep="00000-000",
                logradouro="Rua Exemplo",
                numero="100",
                bairro="Centro",
                cidade="Cidade",
                estado="SP",
                data_abertura=datetime.now().date(),
            )
            db.session.add(estabelecimento)
            db.session.commit()

        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()

        if not config:
            # Cria configurações padrão se não existirem
            config = Configuracao(estabelecimento_id=estabelecimento_id)
            db.session.add(config)
            db.session.commit()

        config_dict = config.to_dict()
        return jsonify({"success": True, "config": config_dict}), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao obter configurações: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
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


@configuracao_bp.route("/", methods=["PUT"])
def atualizar_configuracoes():
    """Atualiza as configurações do estabelecimento"""
    try:
        ensure_configuracoes_schema()
        data = request.get_json() or {}
        estabelecimento_id = int(data.get("estabelecimento_id", 1))

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
                valor = data[campo]
                if campo == "formas_pagamento" and isinstance(valor, list):
                    valor = json.dumps(valor, ensure_ascii=False)
                if campo in ("desconto_maximo_percentual", "desconto_maximo_funcionario"):
                    try:
                        valor = float(valor)
                    except Exception:
                        pass
                setattr(config, campo, valor)

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


@configuracao_bp.route("/logo", methods=["POST"])
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


@configuracao_bp.route("/estabelecimento", methods=["GET", "PUT"])
def gerenciar_estabelecimento():
    """Obtém ou atualiza dados do estabelecimento"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)

        if request.method == "GET":
            estabelecimento = Estabelecimento.query.get(estabelecimento_id)

            if not estabelecimento:
                raw = datetime.now().strftime("%H%M%S%f")
                digits = (raw + "00000000000000")[:14]
                cnpj_placeholder = f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"
                estabelecimento = Estabelecimento(
                    id=estabelecimento_id,
                    nome_fantasia="Empresa Padrão",
                    razao_social="Empresa Padrão LTDA",
                    cnpj=cnpj_placeholder,
                    telefone="(00) 0000-0000",
                    email="contato@empresa.com",
                    cep="00000-000",
                    logradouro="Rua Exemplo",
                    numero="100",
                    bairro="Centro",
                    cidade="Cidade",
                    estado="SP",
                    data_abertura=datetime.now().date(),
                )
                db.session.add(estabelecimento)
                db.session.commit()

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

            # Atualizar campos permitidos (alinhados ao modelo)
            campos_permitidos = [
                "nome_fantasia",
                "razao_social",
                "cnpj",
                "inscricao_estadual",
                "telefone",
                "email",
                "cep",
                "logradouro",
                "numero",
                "complemento",
                "bairro",
                "cidade",
                "estado",
                "regime_tributario",
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
