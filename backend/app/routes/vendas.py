from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app import db
from app.models import (
    Venda,
    VendaItem,
    Produto,
    Funcionario,
    MovimentacaoEstoque,
    Cliente,
)
from sqlalchemy import or_, and_, func
import random
import string

vendas_bp = Blueprint("vendas", __name__)


def gerar_codigo_venda():
    """Gera código único para venda no formato V-YYYYMMDD-XXXX"""
    data_atual = datetime.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.digits, k=4))
    return f"V-{data_atual}-{random_part}"


@vendas_bp.route("/", methods=["POST", "OPTIONS"], strict_slashes=False)
def criar_venda():
    """Cria uma nova venda (finalizar compra no PDV)"""
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    try:
        data = request.get_json()
        print(f"📦 Dados da venda recebidos: {data}")

        # VALIDAÇÕES BÁSICAS
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        if not data.get("items") or len(data["items"]) == 0:
            return jsonify({"error": "Carrinho vazio"}), 400

        # Validação de valores numéricos
        try:
            subtotal = float(data.get("subtotal", 0))
            desconto = float(data.get("desconto", 0))
            total = float(data.get("total", 0))
            valor_recebido = float(data.get("cashReceived", 0))

            if total > valor_recebido and data.get("paymentMethod") == "dinheiro":
                return (
                    jsonify(
                        {
                            "error": "Valor recebido menor que o total para pagamento em dinheiro"
                        }
                    ),
                    400,
                )

            if subtotal < 0 or desconto < 0 or total < 0 or valor_recebido < 0:
                return jsonify({"error": "Valores não podem ser negativos"}), 400
        except ValueError:
            return jsonify({"error": "Valores numéricos inválidos"}), 400

        # 1. GERAR CÓDIGO DA VENDA
        codigo_venda = gerar_codigo_venda()
        while Venda.query.filter_by(codigo=codigo_venda).first():
            codigo_venda = gerar_codigo_venda()

        # 2. CRIAR A VENDA
        nova_venda = Venda(
            codigo=codigo_venda,
            cliente_id=data.get("cliente_id"),
            funcionario_id=data.get("funcionario_id", 1),
            subtotal=subtotal,
            desconto=desconto,
            total=total,
            forma_pagamento=data.get("paymentMethod", "dinheiro"),
            valor_recebido=valor_recebido,
            troco=float(data.get("change", 0)),
            status="finalizada",
            observacoes=data.get("observacoes", ""),
        )

        db.session.add(nova_venda)
        db.session.flush()

        # 3. ADICIONAR ITENS DA VENDA E ATUALIZAR ESTOQUE
        for item_data in data["items"]:
            produto_id = item_data.get("productId")
            quantidade = item_data.get("quantity", 1)
            preco_unitario = float(item_data.get("price", 0))
            total_item = float(item_data.get("total", 0))

            # Validações do item
            if not produto_id:
                db.session.rollback()
                return jsonify({"error": "ID do produto não informado"}), 400

            if quantidade <= 0:
                db.session.rollback()
                return (
                    jsonify(
                        {"error": f"Quantidade inválida para produto {produto_id}"}
                    ),
                    400,
                )

            # Buscar produto
            produto = Produto.query.get(produto_id)
            if not produto:
                db.session.rollback()
                return jsonify({"error": f"Produto {produto_id} não encontrado"}), 404

            # Verificar estoque
            if produto.quantidade < quantidade:
                db.session.rollback()
                return (
                    jsonify(
                        {
                            "error": f"Estoque insuficiente para {produto.nome}. Disponível: {produto.quantidade}, Solicitado: {quantidade}"
                        }
                    ),
                    400,
                )

            # Criar item da venda
            venda_item = VendaItem(
                venda_id=nova_venda.id,
                produto_id=produto_id,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                desconto=item_data.get("desconto_item", 0.0),
                total_item=total_item,
                produto_nome=produto.nome,
                produto_codigo=produto.codigo_barras,
                produto_unidade=produto.unidade_medida,
            )

            db.session.add(venda_item)

            # 4. ATUALIZAR ESTOQUE DO PRODUTO
            quantidade_anterior = produto.quantidade
            produto.quantidade -= quantidade
            quantidade_atual = produto.quantidade

            # 5. REGISTRAR MOVIMENTAÇÃO DE ESTOQUE
            movimentacao = MovimentacaoEstoque(
                produto_id=produto_id,
                tipo="saida",
                quantidade=quantidade,
                quantidade_anterior=quantidade_anterior,
                quantidade_atual=quantidade_atual,
                motivo=f"Venda #{codigo_venda}",
                observacoes=f"Venda realizada via PDV",
                venda_id=nova_venda.id,
                funcionario_id=nova_venda.funcionario_id,
            )

            db.session.add(movimentacao)

        # 7. FINALIZAR TRANSAÇÃO
        db.session.commit()

        # 8. PREPARAR RESPOSTA
        resposta = {
            "success": True,
            "message": "Venda finalizada com sucesso!",
            "venda": {
                "id": nova_venda.id,
                "codigo": nova_venda.codigo,
                "total": nova_venda.total,
                "data": nova_venda.created_at.isoformat(),
                "troco": nova_venda.troco,
                "forma_pagamento": nova_venda.forma_pagamento,
            },
            "recibo": {
                "cabecalho": "MERCADINHO SYS - COMPROVANTE DE VENDA",
                "codigo": nova_venda.codigo,
                "data": nova_venda.created_at.strftime("%d/%m/%Y %H:%M"),
                "itens": [
                    {
                        "nome": item.produto_nome,
                        "quantidade": item.quantidade,
                        "preco_unitario": item.preco_unitario,
                        "total": item.total_item,
                    }
                    for item in nova_venda.itens
                ],
                "subtotal": nova_venda.subtotal,
                "desconto": nova_venda.desconto,
                "total": nova_venda.total,
                "pagamento": nova_venda.forma_pagamento,
                "recebido": nova_venda.valor_recebido,
                "troco": nova_venda.troco,
                "rodape": "Obrigado pela preferência!",
            },
        }

        print(f"✅ Venda {codigo_venda} finalizada - Total: R$ {nova_venda.total:.2f}")
        print(f"📋 Itens vendidos: {len(nova_venda.itens)}")

        return jsonify(resposta), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao finalizar venda: {str(e)}")
        return jsonify({"error": f"Erro ao processar venda: {str(e)}"}), 500


@vendas_bp.route("/", methods=["GET"], strict_slashes=False)
def listar_vendas():
    """Lista vendas com filtros avançados - CEREJA DO BOLO 🍒"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        funcionario_id = request.args.get("funcionario_id")
        cliente_id = request.args.get("cliente_id")
        cliente_nome = request.args.get("cliente_nome")
        status = request.args.get("status")
        forma_pagamento = request.args.get("forma_pagamento")
        codigo_venda = request.args.get("codigo")
        min_total = request.args.get("min_total")
        max_total = request.args.get("max_total")

        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 20, type=int)

        # Query base com joins para otimização
        query = Venda.query

        # Carregamento antecipado para performance
        query = query.options(
            db.joinedload(Venda.funcionario), db.joinedload(Venda.cliente)
        )

        # APLICAR FILTROS DINÂMICOS
        if data_inicio:
            try:
                data_inicio = datetime.fromisoformat(data_inicio.replace("Z", "+00:00"))
                query = query.filter(Venda.created_at >= data_inicio)
            except ValueError:
                return (
                    jsonify({"error": "Formato de data_inicio inválido. Use ISO 8601"}),
                    400,
                )

        if data_fim:
            try:
                data_fim = datetime.fromisoformat(data_fim.replace("Z", "+00:00"))
                # Adiciona 1 dia para incluir o dia inteiro
                data_fim = data_fim + timedelta(days=1)
                query = query.filter(Venda.created_at <= data_fim)
            except ValueError:
                return (
                    jsonify({"error": "Formato de data_fim inválido. Use ISO 8601"}),
                    400,
                )

        if funcionario_id:
            query = query.filter(Venda.funcionario_id == funcionario_id)

        if cliente_id:
            query = query.filter(Venda.cliente_id == cliente_id)

        if cliente_nome:
            # Busca por nome do cliente (se existir relação)
            query = query.join(Cliente).filter(
                or_(
                    Cliente.nome.ilike(f"%{cliente_nome}%"),
                    Cliente.cpf_cnpj.ilike(f"%{cliente_nome}%"),
                )
            )

        if status:
            query = query.filter(Venda.status == status)

        if forma_pagamento:
            query = query.filter(Venda.forma_pagamento == forma_pagamento)

        if codigo_venda:
            query = query.filter(Venda.codigo.ilike(f"%{codigo_venda}%"))

        if min_total:
            try:
                query = query.filter(Venda.total >= float(min_total))
            except ValueError:
                return jsonify({"error": "min_total deve ser um número válido"}), 400

        if max_total:
            try:
                query = query.filter(Venda.total <= float(max_total))
            except ValueError:
                return jsonify({"error": "max_total deve ser um número válido"}), 400

        # Ordenar por data (mais recente primeiro)
        query = query.order_by(Venda.created_at.desc())

        # Paginação com tratamento de erros
        try:
            paginacao = query.paginate(
                page=pagina, per_page=por_pagina, error_out=False
            )
            vendas = paginacao.items
        except Exception as e:
            print(f"Erro na paginação: {str(e)}")
            return jsonify({"error": "Erro na paginação"}), 500

        # Serializar resultado com informações completas
        resultado = {
            "vendas": [
                {
                    "id": v.id,
                    "codigo": v.codigo,
                    "cliente": (
                        {
                            "id": v.cliente_id,
                            "nome": v.cliente.nome if v.cliente else "Consumidor Final",
                            "telefone": v.cliente.telefone if v.cliente else None,
                        }
                        if v.cliente_id
                        else {"nome": "Consumidor Final"}
                    ),
                    "funcionario": {
                        "id": v.funcionario_id,
                        "nome": (
                            v.funcionario.nome if v.funcionario else "Não Informado"
                        ),
                    },
                    "subtotal": float(v.subtotal),
                    "desconto": float(v.desconto),
                    "total": float(v.total),
                    "forma_pagamento": v.forma_pagamento,
                    "valor_recebido": float(v.valor_recebido),
                    "troco": float(v.troco),
                    "status": v.status,
                    "data": v.created_at.isoformat(),
                    "quantidade_itens": len(v.itens),
                    "observacoes": v.observacoes or "",
                }
                for v in vendas
            ],
            "paginacao": {
                "pagina_atual": paginacao.page,
                "total_paginas": paginacao.pages,
                "total_vendas": paginacao.total,
                "por_pagina": paginacao.per_page,
                "tem_proxima": paginacao.has_next,
                "tem_anterior": paginacao.has_prev,
            },
            "estatisticas": {
                "total_geral": db.session.query(func.sum(Venda.total))
                .filter(Venda.id.in_([v.id for v in vendas]))
                .scalar()
                or 0,
                "quantidade_vendas": len(vendas),
            },
        }

        return jsonify(resultado), 200

    except Exception as e:
        print(f"❌ Erro ao listar vendas: {str(e)}")
        return jsonify({"error": f"Erro ao listar vendas: {str(e)}"}), 500


@vendas_bp.route("/<int:venda_id>", methods=["GET"], strict_slashes=False)
def obter_venda(venda_id):
    """Obtém detalhes completos de uma venda específica"""
    try:
        venda = Venda.query.options(
            db.joinedload(Venda.itens),
            db.joinedload(Venda.cliente),
            db.joinedload(Venda.funcionario),
        ).get_or_404(venda_id)

        # Buscar movimentações relacionadas a esta venda
        movimentacoes = MovimentacaoEstoque.query.filter_by(venda_id=venda_id).all()

        return (
            jsonify(
                {
                    "venda": {
                        "id": venda.id,
                        "codigo": venda.codigo,
                        "cliente": {
                            "id": venda.cliente.id if venda.cliente else None,
                            "nome": (
                                venda.cliente.nome
                                if venda.cliente
                                else "Consumidor Final"
                            ),
                            "telefone": (
                                venda.cliente.telefone if venda.cliente else None
                            ),
                            "cpf_cnpj": (
                                venda.cliente.cpf_cnpj if venda.cliente else None
                            ),
                        },
                        "funcionario": {
                            "id": venda.funcionario.id if venda.funcionario else None,
                            "nome": (
                                venda.funcionario.nome
                                if venda.funcionario
                                else "Não Informado"
                            ),
                            "email": (
                                venda.funcionario.email if venda.funcionario else None
                            ),
                        },
                        "subtotal": float(venda.subtotal),
                        "desconto": float(venda.desconto),
                        "total": float(venda.total),
                        "forma_pagamento": venda.forma_pagamento,
                        "valor_recebido": float(venda.valor_recebido),
                        "troco": float(venda.troco),
                        "status": venda.status,
                        "observacoes": venda.observacoes,
                        "data_criacao": venda.created_at.isoformat(),
                        "data_atualizacao": (
                            venda.updated_at.isoformat() if venda.updated_at else None
                        ),
                        "itens": [
                            {
                                "id": item.id,
                                "produto_id": item.produto_id,
                                "produto_nome": item.produto_nome,
                                "produto_codigo": item.produto_codigo,
                                "quantidade": item.quantidade,
                                "preco_unitario": float(item.preco_unitario),
                                "desconto": float(item.desconto),
                                "total_item": float(item.total_item),
                                "unidade_medida": item.produto_unidade,
                            }
                            for item in venda.itens
                        ],
                        "movimentacoes_estoque": [
                            {
                                "id": mov.id,
                                "produto_id": mov.produto_id,
                                "produto_nome": (
                                    mov.produto.nome
                                    if mov.produto
                                    else "Produto Removido"
                                ),
                                "tipo": mov.tipo,
                                "quantidade": mov.quantidade,
                                "quantidade_anterior": mov.quantidade_anterior,
                                "quantidade_atual": mov.quantidade_atual,
                                "motivo": mov.motivo,
                                "data": mov.created_at.isoformat(),
                            }
                            for mov in movimentacoes
                        ],
                    }
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Erro ao obter venda: {str(e)}")
        return jsonify({"error": f"Erro ao obter venda: {str(e)}"}), 500


@vendas_bp.route("/dia", methods=["GET"], strict_slashes=False)
def vendas_do_dia():
    """Retorna as vendas do dia atual (para dashboard PDV)"""
    try:
        hoje = datetime.now().date()
        amanha = hoje + timedelta(days=1)

        # Vendas do dia
        vendas_hoje = (
            Venda.query.filter(
                Venda.created_at >= hoje,
                Venda.created_at < amanha,
                Venda.status == "finalizada",
            )
            .options(db.joinedload(Venda.funcionario), db.joinedload(Venda.itens))
            .order_by(Venda.created_at.desc())
            .all()
        )

        # Estatísticas do dia
        total_hoje = (
            db.session.query(func.sum(Venda.total))
            .filter(
                Venda.created_at >= hoje,
                Venda.created_at < amanha,
                Venda.status == "finalizada",
            )
            .scalar()
            or 0
        )

        quantidade_vendas = len(vendas_hoje)

        # Vendas por forma de pagamento
        formas_pagamento = (
            db.session.query(
                Venda.forma_pagamento,
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .filter(
                Venda.created_at >= hoje,
                Venda.created_at < amanha,
                Venda.status == "finalizada",
            )
            .group_by(Venda.forma_pagamento)
            .all()
        )

        # Produtos mais vendidos hoje
        produtos_mais_vendidos = (
            db.session.query(
                VendaItem.produto_nome,
                func.sum(VendaItem.quantidade).label("quantidade_total"),
                func.sum(VendaItem.total_item).label("total_vendido"),
            )
            .join(Venda)
            .filter(
                Venda.created_at >= hoje,
                Venda.created_at < amanha,
                Venda.status == "finalizada",
            )
            .group_by(VendaItem.produto_nome)
            .order_by(func.sum(VendaItem.quantidade).desc())
            .limit(10)
            .all()
        )

        return (
            jsonify(
                {
                    "data": hoje.isoformat(),
                    "vendas": [
                        {
                            "id": v.id,
                            "codigo": v.codigo,
                            "cliente": (
                                v.cliente.nome if v.cliente else "Consumidor Final"
                            ),
                            "funcionario": (
                                v.funcionario.nome if v.funcionario else "Não Informado"
                            ),
                            "total": float(v.total),
                            "forma_pagamento": v.forma_pagamento,
                            "hora": v.created_at.strftime("%H:%M"),
                            "quantidade_itens": len(v.itens),
                        }
                        for v in vendas_hoje
                    ],
                    "estatisticas": {
                        "total_vendas": float(total_hoje),
                        "quantidade_vendas": quantidade_vendas,
                        "ticket_medio": (
                            float(total_hoje / quantidade_vendas)
                            if quantidade_vendas > 0
                            else 0
                        ),
                        "formas_pagamento": [
                            {
                                "forma": fp.forma_pagamento,
                                "quantidade": fp.quantidade,
                                "total": float(fp.total),
                            }
                            for fp in formas_pagamento
                        ],
                        "produtos_mais_vendidos": [
                            {
                                "nome": pmv.produto_nome,
                                "quantidade": int(pmv.quantidade_total),
                                "total_vendido": float(pmv.total_vendido),
                            }
                            for pmv in produtos_mais_vendidos
                        ],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Erro ao obter vendas do dia: {str(e)}")
        return jsonify({"error": f"Erro ao obter vendas do dia: {str(e)}"}), 500


@vendas_bp.route("/<int:venda_id>/cancelar", methods=["POST"], strict_slashes=False)
def cancelar_venda(venda_id):
    """Cancela uma venda e devolve os produtos ao estoque"""
    try:
        data = request.get_json()
        motivo = data.get("motivo", "Cancelamento solicitado pelo usuário")
        funcionario_id = data.get(
            "funcionario_id", 1
        )  # ID do funcionário que está cancelando

        # Buscar venda
        venda = Venda.query.options(db.joinedload(Venda.itens)).get_or_404(venda_id)

        # Verificar se já está cancelada
        if venda.status == "cancelada":
            return jsonify({"error": "Esta venda já está cancelada"}), 400

        # Verificar se passou muito tempo (opcional - 24 horas)
        tempo_decorrido = datetime.now() - venda.created_at
        if tempo_decorrido.days > 0:
            return (
                jsonify(
                    {
                        "error": "Vendas com mais de 24 horas não podem ser canceladas automaticamente"
                    }
                ),
                400,
            )

        # Iniciar transação
        db.session.begin_nested()

        try:
            # Para cada item, devolver ao estoque
            for item in venda.itens:
                produto = Produto.query.get(item.produto_id)
                if produto:
                    quantidade_anterior = produto.quantidade
                    produto.quantidade += item.quantidade
                    quantidade_atual = produto.quantidade

                    # Registrar movimentação de entrada (devolução)
                    movimentacao = MovimentacaoEstoque(
                        produto_id=produto.id,
                        tipo="entrada",
                        quantidade=item.quantidade,
                        quantidade_anterior=quantidade_anterior,
                        quantidade_atual=quantidade_atual,
                        motivo=f"Cancelamento da venda #{venda.codigo}",
                        observacoes=f"Devolução por cancelamento. Motivo: {motivo}",
                        venda_id=venda.id,
                        funcionario_id=funcionario_id,
                    )
                    db.session.add(movimentacao)

            # Atualizar status da venda
            venda.status = "cancelada"
            venda.observacoes = f"{venda.observacoes or ''}\n[Cancelada em {datetime.now().strftime('%d/%m/%Y %H:%M')}] Motivo: {motivo}".strip()
            venda.updated_at = datetime.now()

            db.session.commit()

            print(f"✅ Venda {venda.codigo} cancelada com sucesso")

            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Venda cancelada com sucesso",
                        "venda": {
                            "id": venda.id,
                            "codigo": venda.codigo,
                            "status": venda.status,
                            "total": float(venda.total),
                        },
                    }
                ),
                200,
            )

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao cancelar venda: {str(e)}")
            return jsonify({"error": f"Erro ao cancelar venda: {str(e)}"}), 500

    except Exception as e:
        print(f"❌ Erro no processo de cancelamento: {str(e)}")
        return jsonify({"error": f"Erro no processo de cancelamento: {str(e)}"}), 500


@vendas_bp.route("/estatisticas", methods=["GET"], strict_slashes=False)
def estatisticas_vendas():
    """Estatísticas gerais de vendas"""
    try:
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")

        query = Venda.query.filter(Venda.status == "finalizada")

        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio.replace("Z", "+00:00"))
            query = query.filter(Venda.created_at >= data_inicio)

        if data_fim:
            data_fim = datetime.fromisoformat(data_fim.replace("Z", "+00:00"))
            query = query.filter(Venda.created_at <= data_fim)

        # Total geral
        total_geral = (
            db.session.query(func.sum(Venda.total))
            .filter(Venda.id.in_([v.id for v in query.all()]))
            .scalar()
            or 0
        )

        # Quantidade de vendas
        quantidade_vendas = query.count()

        # Ticket médio
        ticket_medio = total_geral / quantidade_vendas if quantidade_vendas > 0 else 0

        # Vendas por dia (últimos 7 dias)
        sete_dias_atras = datetime.now() - timedelta(days=7)
        vendas_por_dia = (
            db.session.query(
                func.date(Venda.created_at).label("data"),
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .filter(Venda.created_at >= sete_dias_atras, Venda.status == "finalizada")
            .group_by(func.date(Venda.created_at))
            .order_by(func.date(Venda.created_at).desc())
            .all()
        )

        # Formas de pagamento mais utilizadas
        formas_pagamento = (
            db.session.query(
                Venda.forma_pagamento,
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .filter(Venda.status == "finalizada")
            .group_by(Venda.forma_pagamento)
            .all()
        )

        return (
            jsonify(
                {
                    "estatisticas": {
                        "total_geral": float(total_geral),
                        "quantidade_vendas": quantidade_vendas,
                        "ticket_medio": float(ticket_medio),
                        "periodo": {
                            "inicio": data_inicio.isoformat() if data_inicio else None,
                            "fim": data_fim.isoformat() if data_fim else None,
                        },
                    },
                    "vendas_por_dia": [
                        {
                            "data": (
                                vpd.data.isoformat()
                                if hasattr(vpd.data, "isoformat")
                                else str(vpd.data)
                            ),
                            "quantidade": vpd.quantidade,
                            "total": float(vpd.total) if vpd.total else 0,
                        }
                        for vpd in vendas_por_dia
                    ],
                    "formas_pagamento": [
                        {
                            "forma": fp.forma_pagamento,
                            "quantidade": fp.quantidade,
                            "total": float(fp.total) if fp.total else 0,
                            "percentual": float(
                                (fp.total / total_geral * 100) if total_geral > 0 else 0
                            ),
                        }
                        for fp in formas_pagamento
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {str(e)}")
        return jsonify({"error": f"Erro ao obter estatísticas: {str(e)}"}), 500
