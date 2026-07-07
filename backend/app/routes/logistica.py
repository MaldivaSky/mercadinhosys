from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import logging
from datetime import datetime
import math
from app.models import (
    db, StatusPedidoLogistica, AuditoriaQuilometragem,
    TurnoEntregador, ConfiguracaoLogistica, ChecklistVeiculo, Funcionario, Veiculo
)

logger = logging.getLogger(__name__)
logistica_bp = Blueprint('logistica', __name__)

def _get_est_id():
    claims = get_jwt()
    return int(claims.get("estabelecimento_id") or 1)

@logistica_bp.route('/configuracao', methods=['GET', 'PUT'])
@jwt_required()
def configuracao_logistica():
    est_id = _get_est_id()
    config = ConfiguracaoLogistica.query.filter_by(estabelecimento_id=est_id).first()

    if request.method == 'GET':
        if not config:
            return jsonify({"success": True, "config": {
                "preco_gasolina": 6.00, "preco_alcool": 4.50, "preco_diesel": 5.00,
                "preco_por_km_moto": 1.00, "preco_por_km_carro": 2.00,
                "custo_manutencao_diario_moto": 10.00, "custo_manutencao_diario_carro": 20.00
            }})
        return jsonify({"success": True, "config": {
            "preco_gasolina": float(config.preco_gasolina),
            "preco_alcool": float(config.preco_alcool),
            "preco_diesel": float(config.preco_diesel),
            "preco_por_km_moto": float(config.preco_por_km_moto) if config.preco_por_km_moto else 1.0,
            "preco_por_km_carro": float(config.preco_por_km_carro) if config.preco_por_km_carro else 2.0,
            "custo_manutencao_diario_moto": float(config.manutencao_moto_diaria) if config.manutencao_moto_diaria else 100.0,
            "custo_manutencao_diario_carro": float(config.manutencao_carro_diaria) if config.manutencao_carro_diaria else 200.0
        }})

    # PUT
    data = request.json
    if not config:
        config = ConfiguracaoLogistica(estabelecimento_id=est_id)
        db.session.add(config)
    
    if 'preco_gasolina' in data: config.preco_gasolina = data['preco_gasolina']
    if 'preco_alcool' in data: config.preco_alcool = data['preco_alcool']
    if 'preco_diesel' in data: config.preco_diesel = data['preco_diesel']
    if 'preco_por_km_moto' in data: config.preco_por_km_moto = data['preco_por_km_moto']
    if 'preco_por_km_carro' in data: config.preco_por_km_carro = data['preco_por_km_carro']
    if 'custo_manutencao_diario_moto' in data: config.manutencao_moto_diaria = data['custo_manutencao_diario_moto']
    if 'custo_manutencao_diario_carro' in data: config.manutencao_carro_diaria = data['custo_manutencao_diario_carro']
    
    db.session.commit()
    return jsonify({"success": True, "msg": "Configurações salvas!"})

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
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else datetime.utcnow().isoformat()
            }
            
    return jsonify({
        "success": True,
        "eventos": list(recentes_por_entregador.values())
    }), 200

@logistica_bp.route('/turno/atual', methods=['GET'])
@jwt_required()
def get_turno_atual():
    funcionario_id = get_jwt_identity()
    est_id = _get_est_id()
    
    turno = TurnoEntregador.query.filter_by(
        estabelecimento_id=est_id,
        funcionario_id=funcionario_id,
        status="aberto"
    ).first()
    
    if not turno:
        return jsonify({"success": True, "turno": None})
        
    return jsonify({
        "success": True,
        "turno": {
            "id": turno.id,
            "km_inicial": float(turno.km_inicial),
            "data_turno": turno.data_turno.isoformat(),
            "veiculo_id": turno.veiculo_id,
            "tipo_combustivel": turno.tipo_combustivel
        }
    })

@logistica_bp.route('/turno/iniciar', methods=['POST'])
@jwt_required()
def iniciar_turno():
    data = request.json
    km_inicial = data.get('km_inicial')
    veiculo_id = data.get('veiculo_id')
    motorista_id = data.get('motorista_id')
    tipo_combustivel = data.get('tipo_combustivel', 'gasolina')
    
    if km_inicial is None:
        return jsonify({"success": False, "error": "KM Inicial é obrigatório"}), 400

    funcionario_id = get_jwt_identity()
    est_id = _get_est_id()
    
    # Verifica se já tem turno aberto
    turno_aberto = TurnoEntregador.query.filter_by(
        estabelecimento_id=est_id,
        funcionario_id=funcionario_id,
        status="aberto"
    ).first()
    
    if turno_aberto:
        return jsonify({"success": False, "error": "Já existe um turno aberto"}), 400
        
    novo_turno = TurnoEntregador(
        estabelecimento_id=est_id,
        funcionario_id=funcionario_id,
        veiculo_id=veiculo_id,
        km_inicial=km_inicial,
        tipo_combustivel=tipo_combustivel,
        status="aberto"
    )
    db.session.add(novo_turno)
    
    # Salvar checklist se enviado
    checklist_itens = data.get('checklist')
    if checklist_itens and veiculo_id:
        aprovado = all(item.get('ok', True) for item in checklist_itens)
        novo_checklist = ChecklistVeiculo(
            estabelecimento_id=est_id,
            veiculo_id=veiculo_id,
            motorista_id=motorista_id,
            km_atual=km_inicial,
            itens_json=checklist_itens,
            aprovado=aprovado
        )
        db.session.add(novo_checklist)
    
    db.session.commit()
    
    return jsonify({"success": True, "msg": "Turno iniciado com sucesso", "turno_id": novo_turno.id})

@logistica_bp.route('/turno/finalizar', methods=['POST'])
@jwt_required()
def finalizar_turno():
    data = request.json
    km_final = data.get('km_final')
    
    if km_final is None:
        return jsonify({"success": False, "error": "KM Final é obrigatório"}), 400
        
    funcionario_id = get_jwt_identity()
    est_id = _get_est_id()
    
    turno = TurnoEntregador.query.filter_by(
        estabelecimento_id=est_id,
        funcionario_id=funcionario_id,
        status="aberto"
    ).first()
    
    if not turno:
        return jsonify({"success": False, "error": "Nenhum turno aberto encontrado"}), 404
        
    if float(km_final) < float(turno.km_inicial):
        return jsonify({"success": False, "error": "KM Final não pode ser menor que o KM Inicial"}), 400
        
    distancia = float(km_final) - float(turno.km_inicial)
    
    # Pegar configurações para calcular custos
    config = ConfiguracaoLogistica.query.filter_by(estabelecimento_id=est_id).first()
    if not config:
        config = ConfiguracaoLogistica(estabelecimento_id=est_id)
        db.session.add(config)
        
    # Calcular custo de combustível
    preco_combustivel = float(config.preco_gasolina)
    if turno.tipo_combustivel == 'alcool':
        preco_combustivel = float(config.preco_alcool)
    elif turno.tipo_combustivel == 'diesel':
        preco_combustivel = float(config.preco_diesel)
        
    # Consumo assumido pelo tipo de veículo (moto vs carro) - pegando do cadastro do veículo se existir
    consumo_medio = 30.0 # moto padrao
    is_carro = False
    if turno.veiculo_id:
        veiculo = Veiculo.query.get(turno.veiculo_id)
        if veiculo:
            consumo_medio = float(veiculo.consumo_medio or 30.0)
            if veiculo.tipo.lower() in ['carro', 'furgão', 'caminhonete']:
                is_carro = True
                
    litros_consumidos = distancia / consumo_medio if consumo_medio > 0 else 0
    custo_combustivel = litros_consumidos * preco_combustivel
    
    # Manutenção diária
    custo_manutencao = float(config.manutencao_carro_diaria) if is_carro else float(config.manutencao_moto_diaria)
    
    turno.km_final = km_final
    turno.distancia_percorrida = distancia
    turno.custo_combustivel = custo_combustivel
    turno.custo_manutencao = custo_manutencao
    turno.horario_fim = datetime.utcnow()
    turno.status = "fechado"
    
    db.session.commit()
    
    return jsonify({
        "success": True, 
        "msg": "Turno encerrado e custos operacionais registrados.",
        "km_rodado": distancia,
        "custo_combustivel": float(custo_combustivel),
        "custo_manutencao": float(custo_manutencao)
    })

@logistica_bp.route('/estimar-taxa-cep', methods=['POST'])
@jwt_required()
def estimar_taxa_cep():
    """Estima a distância e a taxa baseada no CEP do cliente"""
    import math
    import requests
    from app.models import Estabelecimento

    data = request.json
    cep_destino = data.get('cep_destino')
    veiculo = data.get('veiculo', 'moto').lower()

    if not cep_destino:
        return jsonify({"success": False, "error": "CEP de destino não informado"}), 400

    est_id = _get_est_id()
    estabelecimento = Estabelecimento.query.get(est_id)
    cep_origem = estabelecimento.cep if estabelecimento else None

    if not cep_origem:
        return jsonify({"success": False, "error": "Estabelecimento sem CEP configurado"}), 400

    # Função simples de Haversine para caso o ViaCEP ou Nominatim retorne lat/lon
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Raio da terra em km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)
        a = math.sin(dLat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dLon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def get_coords_from_cep(cep):
        cep_clean = ''.join(filter(str.isdigit, cep))
        
        # 1. Tenta BrasilAPI v2
        try:
            b_api = requests.get(f"https://brasilapi.com.br/api/cep/v2/{cep_clean}", timeout=4).json()
            coords = b_api.get('location', {}).get('coordinates', {})
            lat = coords.get('latitude')
            lon = coords.get('longitude')
            if lat and lon:
                return float(lat), float(lon)
        except:
            pass

        # 2. Tenta ViaCEP + Nominatim
        try:
            viacep = requests.get(f"https://viacep.com.br/ws/{cep_clean}/json/", timeout=4).json()
            if 'erro' in viacep: return None
            logradouro = viacep.get('logradouro', '')
            localidade = viacep.get('localidade', '')
            uf = viacep.get('uf', '')
            bairro = viacep.get('bairro', '')
            
            headers = {'User-Agent': 'MercadinhoSys/1.0 (admin@mercadinhosys.com.br)'}
            
            # 2.a Tenta por rua
            if logradouro:
                query = f"{logradouro}, {localidade}, {uf}, Brasil"
                nom = requests.get(f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1", headers=headers, timeout=4).json()
                if nom and len(nom) > 0:
                    return float(nom[0]['lat']), float(nom[0]['lon'])
                    
            # 2.b Tenta por CEP postalcode
            nom_cep = requests.get(f"https://nominatim.openstreetmap.org/search?postalcode={cep_clean}&country=Brazil&format=json", headers=headers, timeout=4).json()
            if nom_cep and len(nom_cep) > 0:
                return float(nom_cep[0]['lat']), float(nom_cep[0]['lon'])
                
            # 2.c Fallback: tenta por bairro + cidade
            if bairro:
                query_bairro = f"{bairro}, {localidade}, {uf}, Brasil"
                nom_bairro = requests.get(f"https://nominatim.openstreetmap.org/search?q={query_bairro}&format=json&limit=1", headers=headers, timeout=4).json()
                if nom_bairro and len(nom_bairro) > 0:
                    return float(nom_bairro[0]['lat']), float(nom_bairro[0]['lon'])
                    
            # 2.d Fallback final: tenta apenas pela cidade
            if localidade:
                query_cidade = f"{localidade}, {uf}, Brasil"
                nom_cidade = requests.get(f"https://nominatim.openstreetmap.org/search?q={query_cidade}&format=json&limit=1", headers=headers, timeout=4).json()
                if nom_cidade and len(nom_cidade) > 0:
                    return float(nom_cidade[0]['lat']), float(nom_cidade[0]['lon'])
        except:
            pass
            
        return None

    coords_origem = get_coords_from_cep(cep_origem)
    coords_destino = get_coords_from_cep(cep_destino)

    if not coords_origem or not coords_destino:
        return jsonify({"success": False, "error": "Não foi possível calcular a distância pelo CEP. Insira manualmente."}), 200

    # Distância em linha reta
    dist_reta = haversine(coords_origem[0], coords_origem[1], coords_destino[0], coords_destino[1])
    # Multiplica por 1.4 para estimar rotas de ruas
    distancia_km = round(dist_reta * 1.4, 2)

    if distancia_km < 1.0:
        distancia_km = 1.0  # Minímo de 1km

    config = ConfiguracaoLogistica.query.filter_by(estabelecimento_id=est_id).first()
    preco_km = 1.00 if veiculo == 'moto' else 2.00
    if config:
        preco_km = float(config.preco_por_km_moto or 1.00) if veiculo == 'moto' else float(config.preco_por_km_carro or 2.00)
        
    taxa_sugerida = round(distancia_km * preco_km, 2)
    
    return jsonify({
        "success": True,
        "distancia_km": distancia_km,
        "taxa_sugerida": taxa_sugerida,
        "preco_km_utilizado": preco_km,
        "veiculo": veiculo
    })

@logistica_bp.route('/dashboard/metricas', methods=['GET'])
@jwt_required()
def dashboard_metricas():
    est_id = _get_est_id()
    filtro = request.args.get('filtro', 'hoje')
    
    from datetime import datetime, timedelta
    agora = datetime.utcnow()
    hoje_inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if filtro == 'hoje':
        data_inicio = hoje_inicio
    elif filtro == 'ontem':
        data_inicio = hoje_inicio - timedelta(days=1)
        agora = hoje_inicio
    elif filtro == '7d':
        data_inicio = hoje_inicio - timedelta(days=7)
    elif filtro == '15d':
        data_inicio = hoje_inicio - timedelta(days=15)
    elif filtro == '30d':
        data_inicio = hoje_inicio - timedelta(days=30)
    else:
        data_inicio = hoje_inicio

    # 1. Distância Total e Custos (Turnos)
    turnos = TurnoEntregador.query.filter(
        TurnoEntregador.estabelecimento_id == est_id,
        TurnoEntregador.status == 'fechado',
        TurnoEntregador.horario_fim >= data_inicio,
        TurnoEntregador.horario_fim <= agora
    ).all()
    
    custo_manutencao = sum(float(t.custo_manutencao or 0) for t in turnos)
    distancia_total = 0
    custo_combustivel = 0

    # 2. Entregas e Vendas Associadas
    from app.models import Entrega, Venda
    from sqlalchemy import func
    
    data_ref = func.coalesce(Entrega.data_entrega, Entrega.data_saida, Entrega.created_at)
    entregas = db.session.query(Entrega, Venda).join(Venda, Entrega.venda_id == Venda.id).filter(
        Entrega.estabelecimento_id == est_id,
        Entrega.deleted_at.is_(None),
        data_ref >= data_inicio,
        data_ref <= agora
    ).all()
    
    total_entregas = len(entregas)
    entregas_pdv = 0
    entregas_online = 0
    total_taxas = 0
    total_vendas_entregues = 0
    
    for ent, vend in entregas:
        total_taxas += float(ent.taxa_entrega or 0)
        total_vendas_entregues += float(vend.total or 0)
        
        km = float(ent.km_percorridos or 0)
        if km == 0:
            km = float(ent.distancia_km or 0) * 2
        distancia_total += km
        
        # Se a entrega ainda não tem custo de combustível calculado (ex: pendente no PDV sem veículo)
        custo_fuel_real = float(ent.custo_combustivel or 0)
        if custo_fuel_real == 0 and km > 0:
            # Estimativa: Moto padrão (35 km/l) com Gasolina a R$ 5.80
            custo_fuel_real = (km / 35.0) * 5.80
            
        custo_combustivel += custo_fuel_real
        
        # Estimativa de desgaste/manutenção por KM rodado (R$ 0,15/km)
        # O dashboard soma isso à apuração dos turnos fechados
        custo_manutencao += (km * 0.15)
        
        if vend.tipo_venda == 'delivery':
            entregas_online += 1
        else:
            entregas_pdv += 1

    return jsonify({
        "success": True,
        "metricas": {
            "distancia_total": round(distancia_total, 2),
            "custo_combustivel": round(custo_combustivel, 2),
            "custo_manutencao": round(custo_manutencao, 2),
            "total_entregas": total_entregas,
            "entregas_pdv": entregas_pdv,
            "entregas_online": entregas_online,
            "total_taxas": round(total_taxas, 2),
            "total_vendas_entregues": round(total_vendas_entregues, 2)
        }
    })

