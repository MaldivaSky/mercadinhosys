"""
MercadinhoSys - Rotas de Delivery Profissional
Integração total com os modelos: Motorista, Veiculo, Entrega, TaxaEntrega
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import (
    db, Motorista, Veiculo, TaxaEntrega, Entrega, 
    EntregaItem, RastreamentoEntrega, CustoEntrega,
    Venda, Cliente, Produto, VendaItem, Caixa, MovimentacaoCaixa
)
from app.decorators.rbac import tenant_or_super_admin_required
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import logging
from sqlalchemy import or_, and_, func

delivery_bp = Blueprint("delivery", __name__)
logger = logging.getLogger(__name__)

# ==================== MOTORISTAS & VEÍCULOS ====================

@delivery_bp.route("/motoristas", methods=["GET"])
@tenant_or_super_admin_required
def listar_motoristas():
    """Lista todos os motoristas do estabelecimento"""
    try:
        ativos = request.args.get("ativos", "true").lower() == "true"
        query = Motorista.query.filter_by(estabelecimento_id=request.allowed_estabelecimento_id)
        
        if ativos:
            query = query.filter_by(ativo=True)
            
        motoristas = query.order_by(Motorista.nome).all()
        
        return jsonify({
            "success": True,
            "motoristas": [m.to_dict() for m in motoristas]
        })
    except Exception as e:
        logger.error(f"Erro ao listar motoristas: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@delivery_bp.route("/motoristas", methods=["POST"])
@tenant_or_super_admin_required
def criar_motorista():
    """Cadastra um novo motorista"""
    try:
        data = request.get_json()
        motorista = Motorista(
            estabelecimento_id=request.allowed_estabelecimento_id,
            nome=data["nome"],
            cpf=data["cpf"],
            cnh=data.get("cnh"),
            categoria_cnh=data.get("categoria_cnh"),
            telefone=data.get("telefone"),
            celular=data.get("celular"),
            email=data.get("email"),
            tipo_vinculo=data.get("tipo_vinculo", "CLT"),
            percentual_comissao=Decimal(str(data.get("percentual_comissao", 0))),
            salario_fixo=Decimal(str(data.get("salario_fixo", 0)))
        )
        db.session.add(motorista)
        db.session.commit()
        return jsonify({"success": True, "motorista": motorista.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@delivery_bp.route("/veiculos", methods=["GET"])
@tenant_or_super_admin_required
def listar_veiculos():
    """Lista veículos disponíveis"""
    try:
        veiculos = Veiculo.query.filter_by(
            estabelecimento_id=request.allowed_estabelecimento_id,
            ativo=True
        ).all()
        return jsonify({"success": True, "veiculos": [v.to_dict() for v in veiculos]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@delivery_bp.route("/veiculos", methods=["POST"])
@tenant_or_super_admin_required
def criar_veiculo():
    """Cadastra um novo veículo da frota."""
    try:
        data = request.get_json() or {}

        veiculo = Veiculo(
            estabelecimento_id=request.allowed_estabelecimento_id,
            motorista_id=data.get("motorista_id"),
            placa=(data.get("placa") or "").upper(),
            tipo=data.get("tipo", "carro"),
            marca=data.get("marca"),
            modelo=data.get("modelo"),
            ano=data.get("ano"),
            cor=data.get("cor"),
            capacidade_kg=Decimal(str(data.get("capacidade_kg", 0))),
            capacidade_m3=Decimal(str(data.get("capacidade_m3", 0))),
            proprietario=data.get("proprietario", "motorista"),
            valor_aluguel=Decimal(str(data.get("valor_aluguel", 0))),
            km_atual=Decimal(str(data.get("km_atual", 0))),
            consumo_medio=Decimal(str(data.get("consumo_medio", 15))),
            ativo=bool(data.get("ativo", True)),
            disponivel=bool(data.get("disponivel", True)),
        )

        db.session.add(veiculo)
        db.session.commit()
        return jsonify({"success": True, "veiculo": veiculo.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar veículo: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== TAXAS DE ENTREGA ====================

@delivery_bp.route("/taxas", methods=["GET"])
@tenant_or_super_admin_required
def listar_taxas():
    """Lista taxas por região/bairro"""
    try:
        taxas = TaxaEntrega.query.filter_by(
            estabelecimento_id=request.allowed_estabelecimento_id,
            ativo=True
        ).all()
        return jsonify({"success": True, "taxas": [t.to_dict() for t in taxas]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@delivery_bp.route("/taxas", methods=["POST"])
@tenant_or_super_admin_required
def criar_taxa():
    """Cria nova configuração de taxa de entrega"""
    try:
        data = request.get_json()
        taxa = TaxaEntrega(
            estabelecimento_id=request.allowed_estabelecimento_id,
            nome_regiao=data["nome_regiao"],
            bairros=json.dumps(data.get("bairros", [])),
            taxa_fixa=Decimal(str(data.get("taxa_fixa", 0))),
            tempo_estimado_minutos=data.get("tempo_estimado_minutos", 30)
        )
        db.session.add(taxa)
        db.session.commit()
        return jsonify({"success": True, "taxa": taxa.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== ENTREGAS ====================

@delivery_bp.route("/entregas", methods=["GET"])
@tenant_or_super_admin_required
def listar_entregas():
    """Lista entregas com filtros avançados"""
    try:
        status = request.args.get("status")
        motorista_id = request.args.get("motorista_id")
        
        query = Entrega.query.filter_by(estabelecimento_id=request.allowed_estabelecimento_id)
        
        if status and status != "todos":
            query = query.filter_by(status=status)
        if motorista_id:
            query = query.filter_by(motorista_id=motorista_id)
            
        entregas = query.order_by(Entrega.created_at.desc()).limit(100).all()
        
        return jsonify({
            "success": True,
            "entregas": [e.to_dict() for e in entregas]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@delivery_bp.route("/entregas", methods=["POST"])
@tenant_or_super_admin_required
def criar_entrega():
    """Vincula uma venda a uma nova entrega com itens e detalhes financeiros"""
    try:
        data = request.get_json()
        venda = Venda.query.get_or_404(data["venda_id"])
        
        # Gerar código de rastreamento único
        codigo = f"MS{datetime.now().strftime('%y%m%d')}{str(venda.id).zfill(5)}"
        
        entrega = Entrega(
            estabelecimento_id=request.allowed_estabelecimento_id,
            venda_id=venda.id,
            cliente_id=venda.cliente_id,
            codigo_rastreamento=codigo,
            endereco_cep=data.get("endereco_cep", venda.cliente.cep if venda.cliente else ""),
            endereco_logradouro=data.get("endereco_logradouro", ""),
            endereco_numero=data.get("endereco_numero", ""),
            endereco_bairro=data.get("endereco_bairro", ""),
            endereco_cidade=data.get("endereco_cidade", "Manaus"),
            endereco_estado=data.get("endereco_estado", "AM"),
            endereco_complemento=data.get("endereco_complemento", ""),
            endereco_referencia=data.get("endereco_referencia", ""),
            status="pendente",
            data_prevista=datetime.now() + timedelta(minutes=45),
            taxa_entrega=Decimal(str(data.get("taxa_entrega", 0))),
            pagamento_tipo=data.get("pagamento_tipo", "loja"), # loja ou entrega
            pagamento_status=data.get("pagamento_status", "pendente"),
            observacoes=data.get("observacoes", "")
        )
        
        db.session.add(entrega)
        db.session.flush() # Para pegar o ID da entrega
        
        # Clonar itens da venda para a entrega
        for item_venda in venda.itens:
            item_entrega = EntregaItem(
                entrega_id=entrega.id,
                produto_id=item_venda.produto_id,
                venda_item_id=item_venda.id,
                quantidade=item_venda.quantidade,
                quantidade_entregue=0,
                status="pendente"
            )
            db.session.add(item_entrega)
        
        # Adicionar histórico inicial
        rastreio = RastreamentoEntrega(
            entrega_id=entrega.id,
            status="pedido_recebido",
            observacao="Entrega agendada no sistema"
        )
        db.session.add(rastreio)
        db.session.commit()
        
        return jsonify({"success": True, "entrega": entrega.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar entrega: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@delivery_bp.route("/entregas/<int:id>/status", methods=["PUT"])
@tenant_or_super_admin_required
def atualizar_status(id):
    """Atualiza o status da entrega e registra no histórico"""
    try:
        data = request.get_json()
        entrega = Entrega.query.filter_by(
            id=id, 
            estabelecimento_id=request.allowed_estabelecimento_id
        ).first_or_404()
        
        novo_status = data.get("status")
        entrega.status = novo_status
        
        if novo_status == "em_rota":
            entrega.data_saida = datetime.now()
            entrega.motorista_id = data.get("motorista_id")
            entrega.veiculo_id = data.get("veiculo_id")
        elif novo_status == "entregue":
            entrega.data_entrega = datetime.now()
            # Incrementar estatística do motorista
            if entrega.motorista:
                entrega.motorista.total_entregas += 1
        
        # Registro no Rastreamento
        rastreio = RastreamentoEntrega(
            entrega_id=entrega.id,
            status=novo_status,
            observacao=data.get("observacao", f"Status alterado para {novo_status}"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude")
        )
        db.session.add(rastreio)
        db.session.commit()
        
        return jsonify({"success": True, "entrega": entrega.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@delivery_bp.route("/rastreamento/<int:id>", methods=["GET"])
@tenant_or_super_admin_required
def obter_rastreamento(id):
    """Retorna timeline e dados de rastreamento de uma entrega."""
    try:
        entrega = Entrega.query.filter_by(
            id=id,
            estabelecimento_id=request.allowed_estabelecimento_id
        ).first_or_404()

        rastreamentos = (
            RastreamentoEntrega.query.filter_by(entrega_id=entrega.id)
            .order_by(RastreamentoEntrega.data_hora.asc())
            .all()
        )

        return jsonify({
            "success": True,
            "entrega": entrega.to_dict(),
            "timeline": [item.to_dict() for item in rastreamentos],
        })
    except Exception as e:
        logger.error(f"Erro ao obter rastreamento da entrega {id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@delivery_bp.route("/venda-entrega", methods=["POST"])
@tenant_or_super_admin_required
def criar_venda_entrega_unificada():
    """
    Cria uma Venda e uma Entrega vinculada em uma única transação atômica.
    Ideal para o fluxo 'Venda Entrega na Prática'.
    """
    try:
        data = request.get_json()
        from app.utils.query_helpers import get_authorized_establishment_id
        est_id = get_authorized_establishment_id()
        claims = get_jwt()
        est_id = int(claims.get("estabelecimento_id") or 1)
        
        # 1. Criar a Venda
        cliente_id = data.get("cliente_id")
        cliente = Cliente.query.filter_by(id=cliente_id, estabelecimento_id=est_id).first() if cliente_id else None
        
        venda = Venda(
            estabelecimento_id=est_id,
            cliente_id=cliente_id,
            funcionario_id=data.get("funcionario_id") or int(get_jwt_identity()), 
            codigo=f"VE-{datetime.now().strftime('%y%m%d%H%M%S')}",
            status="finalizada",
            tipo_venda="delivery",
            subtotal=Decimal(str(data.get("subtotal", 0))),
            desconto=Decimal(str(data.get("desconto", 0))),
            total=Decimal(str(data.get("total", 0))),
            data_venda=datetime.now()
        )
        db.session.add(venda)
        db.session.flush() # ID da venda

        # 1.1 Processar Multi-Pagamentos
        pagamentos_data = data.get("pagamentos", [])
        if not pagamentos_data:
            # Fallback para compatibilidade se enviarem o formato antigo
            forma_antiga = data.get("forma_pagamento", "dinheiro")
            pagamentos_data = [{"forma_pagamento": forma_antiga, "valor": data.get("total", 0)}]

        total_recebido = Decimal("0")
        from app.models import Pagamento
        for p_data in pagamentos_data:
            valor_p = Decimal(str(p_data["valor"]))
            total_recebido += valor_p
            pagamento = Pagamento(
                estabelecimento_id=est_id,
                venda_id=venda.id,
                forma_pagamento=p_data["forma_pagamento"],
                valor=valor_p,
                status="pendente" if p_data["forma_pagamento"] == "entrega" else "aprovado",
                data_pagamento=datetime.now()
            )
            db.session.add(pagamento)
        
        venda.valor_recebido = total_recebido
        venda.troco = max(Decimal("0"), total_recebido - venda.total)
        
        # 2. Adicionar Itens
        for item in data.get("itens", []):
            # Pessimistic Locking para Consistência de Estoque ACID e isolamento Tenant
            # Suporte SuperAdmin 'all'
            query_prod = db.session.query(Produto).filter(Produto.id == item["produto_id"])
            if str(est_id).lower() != 'all':
                query_prod = query_prod.filter(Produto.id == item["produto_id"], Produto.estabelecimento_id == est_id)
            
            # with_for_update() não é suportado em SQLite; usar apenas em PostgreSQL
            try:
                prod = query_prod.with_for_update().first()
            except Exception:
                prod = query_prod.first()
            if not prod: continue
            
            v_item = VendaItem(
                venda_id=venda.id,
                estabelecimento_id=est_id, # Usar variável local garantida
                produto_id=prod.id,
                produto_nome=prod.nome,
                quantidade=Decimal(str(item.get("quantidade") or item.get("quantity", 1))),
                preco_unitario=Decimal(str(item.get("preco_unitario") or item.get("price", prod.preco_venda))),
                total_item=Decimal(str(item.get("total_item") or item.get("total", 0))),
            )
            db.session.add(v_item)
            # O processamento de estoque deve ser feito pelos listeners ou manualmente aqui
            if hasattr(prod, 'estoque_atual'):
                prod.estoque_atual -= v_item.quantidade

        # 3. Criar a Entrega
        motorista_id = data.get("motorista_id")
        veiculo_id = data.get("veiculo_id")
        
        # Calcular KM e Combustível se informados (ou usar padrões)
        distancia = Decimal(str(data.get("distancia_km", 5.0)))
        km_total = distancia * 2
        custo_fuel = Decimal("0.00")
        
        if veiculo_id:
            veiculo = Veiculo.query.get(veiculo_id)
            if veiculo and veiculo.consumo_medio:
                custo_fuel = (km_total / veiculo.consumo_medio) * Decimal("5.80")

        main_payment = pagamentos_data[0]["forma_pagamento"] if pagamentos_data else "loja"
        entrega = Entrega(
            estabelecimento_id=est_id,
            venda_id=venda.id,
            cliente_id=cliente_id,
            motorista_id=motorista_id,
            veiculo_id=veiculo_id,
            codigo_rastreamento=f"TRK{venda.codigo.split('-')[-1]}",
            status="em_preparo",
            data_prevista=datetime.now() + timedelta(minutes=45),
            taxa_entrega=Decimal(str(data.get("taxa_entrega", 0))),
            custo_combustivel=custo_fuel,
            distancia_km=distancia,
            km_percorridos=km_total,
            endereco_cep=data.get("endereco_cep", cliente.cep if cliente else ""),
            endereco_logradouro=data.get("endereco_logradouro", ""),
            endereco_numero=data.get("endereco_numero", ""),
            endereco_bairro=data.get("endereco_bairro", ""),
            endereco_cidade=data.get("endereco_cidade", "Manaus"),
            endereco_estado=data.get("endereco_estado", "AM"),
            endereco_complemento=data.get("endereco_complemento", ""),
            pagamento_tipo="loja" if main_payment != "entrega" else "entrega",
            pagamento_status="pago" if main_payment != "entrega" else "pendente"
        )
        
        db.session.add(entrega)
        
        # 4. Movimentação de Caixa (usando Pagamento, não mais venda.forma_pagamento)
        caixa = Caixa.query.filter_by(estabelecimento_id=est_id, status="aberto").first()
        if caixa:
            # Verificar se há pagamentos em dinheiro/pix para dar entrada no caixa
            formas_caixa = [p["forma_pagamento"] for p in pagamentos_data if p["forma_pagamento"] in ["dinheiro", "pix"]]
            if formas_caixa:
                mov = MovimentacaoCaixa(
                    caixa_id=caixa.id,
                    estabelecimento_id=est_id,
                    venda_id=venda.id,
                    tipo="entrada",
                    valor=venda.total,
                    descricao=f"Venda Entrega Unificada #{venda.codigo}"
                )
                db.session.add(mov)
                caixa.saldo_atual += venda.total

        db.session.commit()
        
        return jsonify({
            "success": True, 
            "venda_id": venda.id, 
            "entrega_id": entrega.id,
            "codigo": venda.codigo
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro na Venda Entrega Unificada: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== VENDAS PENDENTES ====================

@delivery_bp.route("/vendas-pendentes", methods=["GET"])
@tenant_or_super_admin_required
def listar_vendas_pendentes():
    """Lista vendas que ainda não possuem uma entrega vinculada"""
    try:
        est_id = request.allowed_estabelecimento_id
        
        # Subquery para pegar IDs de vendas que já têm entrega
        vendas_com_entrega = db.session.query(Entrega.venda_id).filter(
            Entrega.estabelecimento_id == est_id
        ).all()
        vendas_com_entrega_ids = [v[0] for v in vendas_com_entrega]
        
        # Vendas finalizadas que não estão na lista
        vendas = Venda.query.filter(
            Venda.estabelecimento_id == est_id,
            Venda.status == "finalizada",
            ~Venda.id.in_(vendas_com_entrega_ids)
        ).order_by(Venda.data_venda.desc()).limit(50).all()
        
        return jsonify({
            "success": True,
            "vendas": [{
                "id": v.id,
                "codigo": v.codigo,
                "data": v.data_venda.isoformat(),
                "total": float(v.total),
                "cliente": v.cliente.to_dict() if v.cliente else None,
                "itens": [{"nome": i.produto_nome, "qtd": float(i.quantidade)} for i in v.itens]
            } for v in vendas]
        })
    except Exception as e:
        logger.error(f"Erro ao listar vendas pendentes: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== DASHBOARD & ESTATÍSTICAS ====================

@delivery_bp.route("/stats", methods=["GET"])
@tenant_or_super_admin_required
def get_stats():
    """Estatísticas consolidadas para o Dashboard de Delivery"""
    try:
        est_id = request.allowed_estabelecimento_id
        
        total_hoje = Entrega.query.filter(
            Entrega.estabelecimento_id == est_id,
            func.date(Entrega.created_at) == date.today()
        ).count()
        
        pendentes = Entrega.query.filter_by(estabelecimento_id=est_id, status="pendente").count()
        em_rota = Entrega.query.filter_by(estabelecimento_id=est_id, status="em_rota").count()
        entregues_hoje = Entrega.query.filter(
            Entrega.estabelecimento_id == est_id,
            Entrega.status == "entregue",
            func.date(Entrega.data_entrega) == date.today()
        ).count()
        
        # Top Motoristas (últimos 30 dias)
        top_motoristas = db.session.query(
            Motorista.nome,
            func.count(Entrega.id).label("total")
        ).join(Entrega).filter(
            Motorista.estabelecimento_id == est_id,
            Entrega.status == "entregue",
            Entrega.data_entrega >= datetime.now() - timedelta(days=30)
        ).group_by(Motorista.id).order_by(func.count(Entrega.id).desc()).limit(5).all()

        # MÉTRICAS AVANÇADAS (Magnitude Senior)
        vendas_delivery = db.session.query(Venda).filter(
            Venda.estabelecimento_id == est_id,
            Venda.tipo_venda == "delivery",
            Venda.status == "finalizada"
        ).all()
        
        total_vendas_val = sum(v.total for v in vendas_delivery)
        ticket_medio = total_vendas_val / len(vendas_delivery) if vendas_delivery else 0
        
        stats_entregas = db.session.query(
            func.sum(Entrega.km_percorridos).label("km_total"),
            func.sum(Entrega.custo_combustivel).label("combustivel_total"),
            func.avg(Entrega.distancia_km).label("dist_media")
        ).filter(Entrega.estabelecimento_id == est_id, Entrega.status == "entregue").first()

        # Top Produto entregue
        top_produto = db.session.query(
            EntregaItem.produto_id,
            func.sum(EntregaItem.quantidade).label("total")
        ).join(Entrega).filter(
            Entrega.estabelecimento_id == est_id,
            Entrega.status == "entregue"
        ).group_by(EntregaItem.produto_id).order_by(func.sum(EntregaItem.quantidade).desc()).first()
        
        nome_top_prod = "N/A"
        if top_produto:
            p_obj = db.session.get(Produto, top_produto.produto_id)
            nome_top_prod = p_obj.nome if p_obj else "Desconhecido"

        return jsonify({
            "success": True,
            "stats": {
                "total_hoje": total_hoje,
                "pendentes": pendentes,
                "em_rota": em_rota,
                "entregues_hoje": entregues_hoje,
                "ticket_medio": float(ticket_medio),
                "km_totais": float(stats_entregas.km_total or 0),
                "combustivel_total": float(stats_entregas.combustivel_total or 0),
                "distancia_media": float(stats_entregas.dist_media or 0),
                "top_produto": nome_top_prod,
                "top_motoristas": [{"nome": m[0], "total": m[1]} for m in top_motoristas]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== DETALHE DO PEDIDO (venda + itens + rastreio) ====================

@delivery_bp.route("/entregas/<int:id>/detalhe", methods=["GET"])
@tenant_or_super_admin_required
def detalhe_entrega(id):
    """Abre o pedido de venda vinculado à entrega: itens, data, valores e
    a linha do tempo de rastreamento (eventos com posição)."""
    try:
        entrega = Entrega.query.filter_by(
            id=id, estabelecimento_id=request.allowed_estabelecimento_id
        ).first()
        if not entrega:
            return jsonify({"success": False, "error": "Entrega não encontrada"}), 404

        venda = entrega.venda
        venda_data = None
        itens = []
        if venda:
            venda_data = {
                "id": venda.id,
                "codigo": venda.codigo,
                "data_venda": venda.data_venda.isoformat() if venda.data_venda else None,
                "tipo_venda": venda.tipo_venda,
                "status": venda.status,
                "subtotal": float(venda.subtotal or 0),
                "desconto": float(venda.desconto or 0),
                "total": float(venda.total or 0),
                "cliente_nome": venda.cliente.nome if venda.cliente else "Não informado",
                "funcionario_nome": venda.funcionario.nome if venda.funcionario else None,
            }
            itens = [{
                "produto_nome": it.produto_nome,
                "produto_codigo": it.produto_codigo,
                "quantidade": float(it.quantidade or 0),
                "produto_unidade": it.produto_unidade,
                "preco_unitario": float(it.preco_unitario or 0),
                "total_item": float(it.total_item or 0),
            } for it in (venda.itens or [])]

        rastreamento = sorted(
            (entrega.rastreamentos or []),
            key=lambda r: r.data_hora or datetime.min,
        )
        return jsonify({
            "success": True,
            "entrega": entrega.to_dict(),
            "venda": venda_data,
            "itens": itens,
            "rastreamento": [r.to_dict() for r in rastreamento],
        })
    except Exception as e:
        logger.error(f"Erro no detalhe da entrega {id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== CENTRAL LOGÍSTICA (dashboard com filtros) ====================

@delivery_bp.route("/dashboard", methods=["GET"])
@tenant_or_super_admin_required
def dashboard_logistica():
    """Métricas logísticas ricas com filtros (período, entregador, veículo):
    entregas, km, saldo de taxa de entrega, combustível, comissão, top
    clientes/bairros/produtos e distribuição por status."""
    try:
        est_id = request.allowed_estabelecimento_id
        di = request.args.get("data_inicio")
        df = request.args.get("data_fim")
        motorista_id = request.args.get("motorista_id", type=int)
        veiculo_id = request.args.get("veiculo_id", type=int)

        data_ref = func.coalesce(Entrega.data_entrega, Entrega.data_saida, Entrega.created_at)
        filtros = [Entrega.estabelecimento_id == est_id, Entrega.deleted_at.is_(None)]
        if di:
            filtros.append(func.date(data_ref) >= datetime.strptime(di, "%Y-%m-%d").date())
        if df:
            filtros.append(func.date(data_ref) <= datetime.strptime(df, "%Y-%m-%d").date())
        if motorista_id:
            filtros.append(Entrega.motorista_id == motorista_id)
        if veiculo_id:
            filtros.append(Entrega.veiculo_id == veiculo_id)
        escopo = and_(*filtros)
        escopo_entregue = and_(escopo, Entrega.status == "entregue")

        # KPIs
        km_expr = func.sum(func.coalesce(
            func.nullif(Entrega.km_percorridos, 0), Entrega.distancia_km))
        agg = db.session.query(
            func.count(Entrega.id),
            func.coalesce(func.sum(Entrega.taxa_entrega), 0),
            func.coalesce(func.sum(Entrega.custo_combustivel), 0),
            func.coalesce(func.sum(Entrega.comissao_motorista), 0),
            func.coalesce(km_expr, 0),
            func.coalesce(func.avg(Entrega.tempo_real_minutos), 0),
        ).filter(escopo).first()
        total_entregas = int(agg[0] or 0)
        taxa_total = float(agg[1] or 0)
        combustivel_total = float(agg[2] or 0)
        comissao_total = float(agg[3] or 0)
        km_total = float(agg[4] or 0)
        tempo_medio = round(float(agg[5] or 0), 1)

        por_status = dict(db.session.query(Entrega.status, func.count(Entrega.id))
                          .filter(escopo).group_by(Entrega.status).all())

        # Top clientes (por nº de entregas e taxa gerada)
        top_clientes = db.session.query(
            Cliente.nome, func.count(Entrega.id), func.coalesce(func.sum(Entrega.taxa_entrega), 0)
        ).join(Cliente, Entrega.cliente_id == Cliente.id).filter(escopo).group_by(
            Cliente.id).order_by(func.count(Entrega.id).desc()).limit(5).all()

        # Top bairros
        top_bairros = db.session.query(
            Entrega.endereco_bairro, func.count(Entrega.id)
        ).filter(escopo, Entrega.endereco_bairro.isnot(None)).group_by(
            Entrega.endereco_bairro).order_by(func.count(Entrega.id).desc()).limit(5).all()

        # Top produtos entregues (quantidade)
        top_produtos = db.session.query(
            Produto.nome, func.sum(EntregaItem.quantidade)
        ).join(Entrega, EntregaItem.entrega_id == Entrega.id).join(
            Produto, EntregaItem.produto_id == Produto.id
        ).filter(escopo).group_by(Produto.id).order_by(
            func.sum(EntregaItem.quantidade).desc()).limit(5).all()

        # Faturamento delivery (vendas vinculadas às entregas do escopo)
        fat_delivery = db.session.query(func.coalesce(func.sum(Venda.total), 0)).join(
            Entrega, Entrega.venda_id == Venda.id).filter(escopo).scalar() or 0
        ticket_medio = round(float(fat_delivery) / total_entregas, 2) if total_entregas else 0.0

        return jsonify({
            "success": True,
            "kpis": {
                "total_entregas": total_entregas,
                "km_total": round(km_total, 1),
                "taxa_entrega_total": round(taxa_total, 2),
                "combustivel_total": round(combustivel_total, 2),
                "comissao_total": round(comissao_total, 2),
                "faturamento_delivery": round(float(fat_delivery), 2),
                "ticket_medio": ticket_medio,
                "tempo_medio_minutos": tempo_medio,
                "saldo_taxa": round(taxa_total - combustivel_total - comissao_total, 2),
            },
            "por_status": {k: int(v) for k, v in por_status.items()},
            "top_clientes": [{"nome": c[0], "entregas": int(c[1]), "taxa": float(c[2] or 0)} for c in top_clientes],
            "top_bairros": [{"bairro": b[0], "entregas": int(b[1])} for b in top_bairros],
            "top_produtos": [{"produto": p[0], "quantidade": float(p[1] or 0)} for p in top_produtos],
        })
    except Exception as e:
        logger.error(f"Erro no dashboard logística: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
