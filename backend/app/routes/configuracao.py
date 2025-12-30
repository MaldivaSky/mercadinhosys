from flask import Blueprint, request, jsonify
from app import db
from app.models import Configuracao, Estabelecimento
import json

config_bp = Blueprint("configuracao", __name__)


@config_bp.route("/", methods=["GET"])
def obter_configuracoes():
    """Obtém todas as configurações do estabelecimento"""
    estabelecimento_id = request.args.get("estabelecimento_id", 1)

    config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()

    if not config:
        return jsonify({"error": "Configurações não encontradas"}), 404

    return jsonify(config.to_dict()), 200


@config_bp.route("/", methods=["PUT"])
def atualizar_configuracoes():
    """Atualiza as configurações"""
    data = request.get_json()
    estabelecimento_id = data.get("estabelecimento_id", 1)

    config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()

    if not config:
        config = Configuracao(estabelecimento_id=estabelecimento_id)

    # Atualiza campos
    for key, value in data.items():
        if hasattr(config, key):
            setattr(config, key, value)

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
