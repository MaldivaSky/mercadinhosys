from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import logging

logger = logging.getLogger(__name__)
logistica_bp = Blueprint('logistica', __name__)

@logistica_bp.route('/eventos', methods=['POST'])
@jwt_required()
def registrar_evento():
    """A Ponte Síncrona: Recebe o gatilho real-time do entregador (Saiu, Chegou, Entregou)"""
    data = request.json
    venda_id = data.get('venda_id')
    status = data.get('status')
    lat = data.get('latitude')
    lon = data.get('longitude')

    if not all([status, lat, lon]):
        return jsonify({"success": False, "error": "Faltam dados do evento (lat/lon/status)"}), 400

    funcionario_id = get_jwt_identity()
    est_id = _get_est_id()

    novo_evento = StatusPedidoLogistica(
        estabelecimento_id=est_id,
        venda_id=venda_id,
        funcionario_id=funcionario_id,
        status=status,
        latitude=lat,
        longitude=lon
    )

    db.session.add(novo_evento)
    db.session.commit()

    return jsonify({
        "success": True, 
        "msg": f"Evento {status} gravado como prova legal."
    }), 201

@logistica_bp.route('/auditoria-batch', methods=['POST'])
@jwt_required()
def registrar_lote_rastreio():
    """A Ponte Assíncrona: Recebe a lista pesada (JSON) de coordenadas do turno inteiro"""
    data = request.json
    pontos = data.get('pontos_gps', [])
    
    funcionario_id = get_jwt_identity()
    est_id = _get_est_id()

    # Salvamos o JSON massivo e retornamos "202 Accepted" super rápido pro App.
    # O processamento da distância total rodaria no Celery Worker.
    auditoria = AuditoriaQuilometragem(
        estabelecimento_id=est_id,
        funcionario_id=funcionario_id,
        pontos_gps=pontos
    )
    db.session.add(auditoria)
    db.session.commit()

    return jsonify({
        "success": True, 
        "msg": "Lote recebido. Cálculo de KM enviado para fila assíncrona."
    }), 202

@logistica_bp.route('/eventos/recentes', methods=['GET'])
@jwt_required()
def listar_eventos_recentes():
    """Retorna a última posição conhecida de cada entregador ativo hoje"""
    est_id = _get_est_id()

    # Pegamos os eventos, ordenados do mais recente pro mais antigo
    eventos = StatusPedidoLogistica.query.filter_by(
        estabelecimento_id=est_id
    ).order_by(StatusPedidoLogistica.timestamp.desc()).limit(50).all()
    
    # Deduplicamos por funcionário (queremos só o último ping de cada um)
    recentes_por_entregador = {}
    for ev in eventos:
        if ev.funcionario_id not in recentes_por_entregador:
            recentes_por_entregador[ev.funcionario_id] = {
                "id": ev.id,
                "funcionario_id": ev.funcionario_id,
                "venda_id": ev.venda_id,
                "status": ev.status,
                "latitude": ev.latitude,
                "longitude": ev.longitude,
                "timestamp": ev.timestamp.isoformat()
            }
            
    return jsonify({
        "success": True,
        "eventos": list(recentes_por_entregador.values())
    }), 200
