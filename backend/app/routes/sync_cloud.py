"""
MercadinhoSys - Cloud Sync Receiver
API para receber dados sincronizados dos clientes locais
Roda apenas no modo cloud (Vercel/Aiven)
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import logging
from datetime import datetime
from typing import Dict, Any

from app import db
from app.models import SyncLog

sync_bp = Blueprint("sync", __name__)
logger = logging.getLogger(__name__)

@sync_bp.route("/receive", methods=["POST"])
def receive_sync():
    """
    Recebe dados sincronizados dos clientes locais
    Endpoint seguro com token de autenticação
    """
    try:
        # Verificar se está no modo cloud
        if current_app.config.get("APP_MODE", "local") == "local":
            return jsonify({
                "success": False,
                "error": "Endpoint disponível apenas no modo cloud"
            }), 403
        
        # Verificar token de sincronização
        sync_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        expected_token = current_app.config.get("CLOUD_SYNC_TOKEN", "")
        
        if not sync_token or sync_token != expected_token:
            logger.warning("❌ Token de sync inválido")
            return jsonify({
                "success": False,
                "error": "Não autorizado"
            }), 401
        
        # Obter payload
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Payload inválido"
            }), 400
        
        # Validar campos obrigatórios
        required_fields = ["tabela", "operacao", "estabelecimento_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Campo obrigatório ausente: {field}"
                }), 400
        
        # Processar sincronização
        success = _process_sync_data(data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Dados sincronizados com sucesso",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Falha ao processar sincronização"
            }), 500
            
    except Exception as e:
        logger.error(f"💥 Erro no recebimento de sync: {e}")
        return jsonify({
            "success": False,
            "error": "Erro interno no servidor"
        }), 500

def _process_sync_data(data: Dict[str, Any]) -> bool:
    """
    Processa os dados sincronizados e realiza o upsert no PostgreSQL
    Preserva rigorosamente os IDs primários originais
    """
    try:
        tabela = data["tabela"]
        operacao = data["operacao"]
        estabelecimento_id = data["estabelecimento_id"]
        payload = data.get("payload", {})
        registro_id = data.get("registro_id")
        
        logger.info(f"📥 Processando sync: {tabela} {operacao} ID {registro_id}")
        
        # Importar modelos dinamicamente
        model_class = _get_model_class(tabela)
        if not model_class:
            logger.error(f"❌ Modelo não encontrado para tabela: {tabela}")
            return False
        
        # Iniciar transação
        with db.session.begin_nested():
            if operacao == "DELETE":
                # Deletar registro
                registro = model_class.query.filter_by(id=registro_id).first()
                if registro:
                    db.session.delete(registro)
                    logger.info(f"🗑️ Registro {registro_id} deletado")
                    
            elif operacao in ["INSERT", "UPDATE"]:
                # Fazer upsert preservando ID original
                if not payload:
                    logger.error(f"❌ Payload ausente para operação {operacao}")
                    return False
                
                # Verificar se já existe
                registro_existente = model_class.query.filter_by(id=registro_id).first()
                
                if registro_existente:
                    # Atualizar registro existente
                    _update_model_from_payload(registro_existente, payload)
                    logger.info(f"📝 Registro {registro_id} atualizado")
                else:
                    # Criar novo registro com ID original
                    novo_registro = _create_model_from_payload(model_class, payload, registro_id)
                    db.session.add(novo_registro)
                    logger.info(f"➕ Registro {registro_id} criado")
        
        # Commit da transação principal
        db.session.commit()
        
        # Criar log de sincronização
        _create_sync_log(data, "success")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erro ao processar sync data: {e}")
        _create_sync_log(data, "error", str(e))
        return False

def _get_model_class(tabela: str):
    """Retorna a classe do modelo baseada no nome da tabela"""
    from app.models import (
        Venda, Fiado, Cliente, Fornecedor, Produto, 
        CategoriaProduto, Despesa, Funcionario, Estabelecimento,
        Configuracao, Caixa
    )
    
    models_map = {
        "vendas": Venda,
        "fiados": Fiado,
        "clientes": Cliente,
        "fornecedores": Fornecedor,
        "produtos": Produto,
        "categoria_produtos": CategoriaProduto,
        "despesas": Despesa,
        "funcionarios": Funcionario,
        "estabelecimentos": Estabelecimento,
        "configuracoes": Configuracao,
        "caixas": Caixa
    }
    
    return models_map.get(tabela)

def _update_model_from_payload(model, payload: Dict[str, Any]):
    """Atualiza um modelo existente a partir do payload"""
    for key, value in payload.items():
        if hasattr(model, key):
            # Tratar campos especiais
            if key.endswith("_at") or key.endswith("_date"):
                # Campos de data/hora
                if isinstance(value, str):
                    try:
                        from datetime import datetime
                        if "T" in value:
                            setattr(model, key, datetime.fromisoformat(value.replace("Z", "+00:00")))
                        else:
                            from datetime import date
                            setattr(model, key, datetime.strptime(value, "%Y-%m-%d").date())
                    except:
                        continue
            elif key.endswith("_json"):
                # Campos JSON
                if isinstance(value, (dict, list)):
                    setattr(model, key, json.dumps(value))
            else:
                # Campos normais
                setattr(model, key, value)

def _create_model_from_payload(model_class, payload: Dict[str, Any], registro_id: int):
    """Cria uma nova instância do modelo com ID original"""
    # Criar instância sem ID primeiro
    novo_registro = model_class()
    
    # Definir ID explicitamente
    novo_registro.id = registro_id
    
    # Preencher outros campos
    _update_model_from_payload(novo_registro, payload)
    
    return novo_registro

def _create_sync_log(data: Dict[str, Any], status: str, error: str = None):
    """Cria um registro de log da sincronização"""
    try:
        log = SyncLog(
            estabelecimento_id=data.get("estabelecimento_id", 1),
            operacao=f"{data.get('tabela', 'unknown')}_{data.get('operacao', 'unknown')}",
            status=status,
            payload_json=json.dumps(data),
            mensagem_erro=error,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow() if status == "success" else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f"❌ Erro ao criar sync log: {e}")

@sync_bp.route("/status", methods=["GET"])
@jwt_required()
def sync_status():
    """Retorna status da sincronização (apenas para debugging)"""
    try:
        # Contar itens pendentes na SyncQueue (apenas no modo local)
        if current_app.config.get("APP_MODE", "local") == "local":
            from app.models import SyncQueue
            pending_count = SyncQueue.query.filter_by(status="pendente").count()
            error_count = SyncQueue.query.filter_by(status="erro").count()
        else:
            pending_count = 0
            error_count = 0
        
        # Logs recentes
        recent_logs = SyncLog.query.order_by(SyncLog.created_at.desc())\
                                 .limit(10)\
                                 .all()
        
        logs_data = []
        for log in recent_logs:
            logs_data.append({
                "id": log.id,
                "operacao": log.operacao,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "mensagem_erro": log.mensagem_erro
            })
        
        return jsonify({
            "success": True,
            "data": {
                "mode": current_app.config.get("APP_MODE", "local"),
                "pending_items": pending_count,
                "error_items": error_count,
                "recent_logs": logs_data
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status de sync: {e}")
        return jsonify({
            "success": False,
            "error": "Erro interno"
        }), 500
