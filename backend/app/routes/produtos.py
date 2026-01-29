# app/produtos.py
# MÓDULO COMPLETO DE PRODUTOS - ERP INDUSTRIAL BRASILEIRO
# CRUD completo com controle de estoque, validade, precificação

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_jwt_extended import get_jwt_identity, get_jwt
from datetime import datetime, date, timedelta
from decimal import Decimal
import re
from app.models import (
    db,
    Produto,
    Estabelecimento,
    Fornecedor,
    CategoriaProduto,
    MovimentacaoEstoque,
    VendaItem,
    PedidoCompraItem,
)
from app.utils import calcular_margem_lucro, formatar_codigo_barras
from app.decorators.decorator_jwt import funcionario_required

produtos_bp = Blueprint("produtos", __name__)

# ============================================
# VALIDAÇÕES ESPECÍFICAS DE PRODUTO
# ============================================


def validar_dados_produto(data, produto_id=None, estabelecimento_id=None):
    """Valida todos os dados do produto antes de salvar"""
    erros = []

    # Campos obrigatórios
    campos_obrigatorios = ["nome", "categoria", "preco_custo", "preco_venda"]
    for campo in campos_obrigatorios:
        if not data.get(campo):
            erros.append(f'O campo {campo.replace("_", " ").title()} é obrigatório')

    # Validação de código de barras único (apenas se estabelecimento_id for fornecido)
    if estabelecimento_id and data.get("codigo_barras"):
        codigo_barras = data["codigo_barras"].strip()
        produto_existente = Produto.query.filter_by(
            codigo_barras=codigo_barras,
            estabelecimento_id=estabelecimento_id,
        ).first()

        if produto_existente and produto_existente.id != produto_id:
            erros.append("Código de barras já cadastrado para outro produto")

    # Validação de código interno único (apenas se estabelecimento_id for fornecido)
    if estabelecimento_id and data.get("codigo_interno"):
        codigo_interno = data["codigo_interno"].strip()
        produto_existente = Produto.query.filter_by(
            codigo_interno=codigo_interno,
            estabelecimento_id=estabelecimento_id,
        ).first()

        if produto_existente and produto_existente.id != produto_id:
            erros.append("Código interno já cadastrado para outro produto")

    # Validação de preços
    if data.get("preco_custo"):
        try:
            preco_custo = Decimal(str(data["preco_custo"]))
            if preco_custo < 0:
                erros.append("Preço de custo não pode ser negativo")
        except:
            erros.append("Preço de custo inválido")

    if data.get("preco_venda"):
        try:
            preco_venda = Decimal(str(data["preco_venda"]))
            if preco_venda < 0:
                erros.append("Preço de venda não pode ser negativo")
        except:
            erros.append("Preço de venda inválido")

    # Validação se preço de venda é maior que custo
    if data.get("preco_custo") and data.get("preco_venda"):
        try:
            preco_custo = Decimal(str(data["preco_custo"]))
            preco_venda = Decimal(str(data["preco_venda"]))
            if preco_venda <= preco_custo:
                erros.append("Preço de venda deve ser maior que o preço de custo")
        except:
            pass

    # Validação de quantidade mínima
    if data.get("quantidade_minima"):
        try:
            qtd_minima = int(data["quantidade_minima"])
            if qtd_minima < 0:
                erros.append("Quantidade mínima não pode ser negativa")
        except:
            erros.append("Quantidade mínima inválida")

    # Validação de data de validade
    if data.get("data_validade"):
        try:
            data_validade = datetime.strptime(data["data_validade"], "%Y-%m-%d").date()
            if data_validade < date.today():
                erros.append("Data de validade não pode ser passada")
        except ValueError:
            erros.append("Formato de data inválido. Use YYYY-MM-DD")

    # Validação de NCM (8 dígitos)
    if data.get("ncm"):
        ncm = re.sub(r"\D", "", data["ncm"])
        if len(ncm) != 8:
            erros.append("NCM deve conter 8 dígitos")

    return erros


def calcular_classificacao_abc(produto):
    """Calcula classificação ABC do produto"""
    valor_total_vendido = float(produto.preco_venda * (produto.quantidade_vendida or 0))

    # Esses valores deveriam ser calculados em relação ao total do estabelecimento
    # Para simplificar, usamos valores fixos
    if valor_total_vendido > 10000:
        return "A"
    elif valor_total_vendido > 5000:
        return "B"
    else:
        return "C"


def verificar_estoque_baixo(produto):
    """Verifica se o produto está com estoque baixo"""
    if produto.quantidade_minima and produto.quantidade <= produto.quantidade_minima:
        return True
    return False


def verificar_validade_proxima(produto):
    """Verifica se o produto está próximo da validade"""
    if produto.controlar_validade and produto.data_validade:
        dias_para_validade = (produto.data_validade - date.today()).days
        if 0 <= dias_para_validade <= 30:  # 30 dias para expirar
            return True
    return False


# ============================================
# ROTAS DE PRODUTOS
# ============================================


@produtos_bp.route("/", methods=["GET"])
@login_required
def listar_produtos():
    """Lista todos os produtos com filtros e paginação"""
    try:
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 50, type=int)
        ativo = request.args.get("ativo", None, type=str)
        categoria = request.args.get("categoria", None, type=str)
        estoque_baixo = request.args.get("estoque_baixo", None, type=str)
        validade_proxima = request.args.get("validade_proxima", None, type=str)
        busca = request.args.get("busca", "", type=str).strip()

        # Query base
        query = Produto.query.filter_by(
            estabelecimento_id=current_user.estabelecimento_id
        )

        # Filtros
        if ativo is not None:
            query = query.filter_by(ativo=ativo.lower() == "true")

        if categoria:
            query = query.filter_by(categoria=categoria)

        if estoque_baixo and estoque_baixo.lower() == "true":
            query = query.filter(Produto.quantidade <= Produto.quantidade_minima)

        if validade_proxima and validade_proxima.lower() == "true":
            hoje = date.today()
            query = query.filter(
                Produto.controlar_validade == True,
                Produto.data_validade != None,
                Produto.data_validade.between(hoje, hoje + timedelta(days=30)),
            )

        if busca:
            busca_termo = f"%{busca}%"
            query = query.filter(
                db.or_(
                    Produto.nome.ilike(busca_termo),
                    Produto.codigo_barras.ilike(busca_termo),
                    Produto.codigo_interno.ilike(busca_termo),
                    Produto.descricao.ilike(busca_termo),
                    Produto.marca.ilike(busca_termo),
                )
            )

        # Ordenação padrão: por nome
        query = query.order_by(Produto.nome.asc())

        # Paginação
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

        produtos = []
        alertas = []

        for produto in paginacao.items:
            produto_dict = produto.to_dict()

            # Adicionar informações calculadas
            produto_dict["margem_lucro"] = calcular_margem_lucro(
                float(produto.preco_custo), float(produto.preco_venda)
            )
            produto_dict["valor_total_estoque"] = float(
                produto.quantidade * produto.preco_custo
            )
            produto_dict["classificacao_abc"] = calcular_classificacao_abc(produto)

            # Verificar alertas
            if verificar_estoque_baixo(produto):
                produto_dict["alerta_estoque"] = True
                alertas.append(
                    {
                        "produto_id": produto.id,
                        "tipo": "estoque_baixo",
                        "mensagem": f"Estoque baixo: {produto.quantidade} unidades (mínimo: {produto.quantidade_minima})",
                    }
                )
            else:
                produto_dict["alerta_estoque"] = False

            if verificar_validade_proxima(produto):
                produto_dict["alerta_validade"] = True
                dias = (produto.data_validade - date.today()).days
                alertas.append(
                    {
                        "produto_id": produto.id,
                        "tipo": "validade_proxima",
                        "mensagem": f"Validade próxima: {produto.data_validade} ({dias} dias)",
                    }
                )
            else:
                produto_dict["alerta_validade"] = False

            produtos.append(produto_dict)

        # Estatísticas
        total_produtos = paginacao.total
        produtos_ativos = (
            query.filter_by(ativo=True).count() if ativo is None else paginacao.total
        )
        produtos_inativos = total_produtos - produtos_ativos

        # Valor total em estoque
        valor_total_estoque = (
            db.session.query(db.func.sum(Produto.quantidade * Produto.preco_custo))
            .filter_by(estabelecimento_id=current_user.estabelecimento_id, ativo=True)
            .scalar()
            or 0
        )

        # Produtos com estoque baixo
        produtos_estoque_baixo = Produto.query.filter(
            Produto.estabelecimento_id == current_user.estabelecimento_id,
            Produto.ativo == True,
            Produto.quantidade <= Produto.quantidade_minima,
        ).count()

        return jsonify(
            {
                "success": True,
                "produtos": produtos,
                "total": total_produtos,
                "pagina": pagina,
                "por_pagina": por_pagina,
                "total_paginas": paginacao.pages,
                "estatisticas": {
                    "total": total_produtos,
                    "ativos": produtos_ativos,
                    "inativos": produtos_inativos,
                    "valor_total_estoque": float(valor_total_estoque),
                    "produtos_estoque_baixo": produtos_estoque_baixo,
                    "produtos_validade_proxima": len(
                        [p for p in produtos if p.get("alerta_validade")]
                    ),
                },
                "alertas": alertas[:10],  # Limitar a 10 alertas
            }
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao listar produtos: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao listar produtos"}),
            500,
        )


@produtos_bp.route("/<int:id>", methods=["GET"])
@login_required
def obter_produto(id):
    """Obtém detalhes completos de um produto específico"""
    try:
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=current_user.estabelecimento_id
        ).first_or_404()

        # Dados básicos
        dados_produto = produto.to_dict()

        # Adicionar informações calculadas
        dados_produto["margem_lucro"] = calcular_margem_lucro(
            float(produto.preco_custo), float(produto.preco_venda)
        )
        dados_produto["valor_total_estoque"] = float(
            produto.quantidade * produto.preco_custo
        )
        dados_produto["classificacao_abc"] = calcular_classificacao_abc(produto)
        dados_produto["estoque_baixo"] = verificar_estoque_baixo(produto)
        dados_produto["validade_proxima"] = verificar_validade_proxima(produto)

        # Histórico de movimentações (últimas 20)
        movimentacoes = (
            MovimentacaoEstoque.query.filter_by(
                produto_id=id, estabelecimento_id=current_user.estabelecimento_id
            )
            .order_by(MovimentacaoEstoque.created_at.desc())
            .limit(20)
            .all()
        )

        movimentacoes_lista = []
        for mov in movimentacoes:
            movimentacoes_lista.append(
                {
                    "id": mov.id,
                    "tipo": mov.tipo,
                    "quantidade": mov.quantidade,
                    "quantidade_atual": mov.quantidade_atual,
                    "motivo": mov.motivo,
                    "created_at": (
                        mov.created_at.isoformat() if mov.created_at else None
                    ),
                    "funcionario": mov.funcionario.nome if mov.funcionario else None,
                }
            )

        # Histórico de vendas (últimas 10)
        vendas = (
            VendaItem.query.filter_by(produto_id=id)
            .order_by(VendaItem.created_at.desc())
            .limit(10)
            .all()
        )

        vendas_lista = []
        for venda_item in vendas:
            vendas_lista.append(
                {
                    "id": venda_item.id,
                    "venda_id": venda_item.venda_id,
                    "quantidade": venda_item.quantidade,
                    "preco_unitario": float(venda_item.preco_unitario),
                    "total_item": float(venda_item.total_item),
                    "data_venda": (
                        venda_item.created_at.isoformat()
                        if venda_item.created_at
                        else None
                    ),
                    "venda_codigo": (
                        venda_item.venda.codigo if venda_item.venda else None
                    ),
                }
            )

        # Pedidos de compra pendentes
        pedidos_pendentes = PedidoCompraItem.query.filter_by(
            produto_id=id, status="pendente"
        ).all()

        pedidos_lista = []
        for pedido_item in pedidos_pendentes:
            pedidos_lista.append(
                {
                    "id": pedido_item.id,
                    "pedido_id": pedido_item.pedido_id,
                    "quantidade_solicitada": pedido_item.quantidade_solicitada,
                    "quantidade_recebida": pedido_item.quantidade_recebida,
                    "preco_unitario": float(pedido_item.preco_unitario),
                    "total_item": float(pedido_item.total_item),
                    "pedido_numero": (
                        pedido_item.pedido.numero_pedido if pedido_item.pedido else None
                    ),
                }
            )

        # Estatísticas de vendas
        total_vendido = produto.quantidade_vendida or 0
        valor_total_vendido = float(
            produto.preco_venda * (produto.quantidade_vendida or 0)
        )
        ticket_medio_produto = (
            valor_total_vendido / total_vendido if total_vendido > 0 else 0
        )

        return jsonify(
            {
                "success": True,
                "produto": dados_produto,
                "movimentacoes": movimentacoes_lista,
                "historico_vendas": vendas_lista,
                "pedidos_pendentes": pedidos_lista,
                "estatisticas": {
                    "total_vendido": total_vendido,
                    "valor_total_vendido": valor_total_vendido,
                    "ticket_medio": ticket_medio_produto,
                    "ultima_venda": (
                        produto.ultima_venda.isoformat()
                        if produto.ultima_venda
                        else None
                    ),
                    "dias_ultima_venda": (
                        (datetime.utcnow().date() - produto.ultima_venda.date()).days
                        if produto.ultima_venda
                        else None
                    ),
                },
            }
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao obter produto {id}: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao obter produto"}),
            500,
        )


@produtos_bp.route("/", methods=["POST"])
@login_required
def criar_produto():
    """Cria um novo produto"""
    try:
        data = request.get_json()

        # Validação dos dados
        erros = validar_dados_produto(data)
        if erros:
            return (
                jsonify(
                    {"success": False, "message": "Erros de validação", "errors": erros}
                ),
                400,
            )

        # Calcular margem de lucro
        preco_custo = Decimal(str(data["preco_custo"]))
        preco_venda = Decimal(str(data["preco_venda"]))

        margem = (
            ((preco_venda - preco_custo) / preco_custo * 100) if preco_custo > 0 else 0
        )

        # Criar produto
        produto = Produto(
            estabelecimento_id=current_user.estabelecimento_id,
            fornecedor_id=data.get("fornecedor_id"),
            codigo_barras=data.get("codigo_barras", "").strip(),
            codigo_interno=data.get("codigo_interno", "").strip(),
            nome=data["nome"].strip(),
            descricao=data.get("descricao", "").strip(),
            marca=data.get("marca", "").strip(),
            categoria=data["categoria"].strip(),
            subcategoria=data.get("subcategoria", "").strip(),
            unidade_medida=data.get("unidade_medida", "UN"),
            quantidade=int(data.get("quantidade", 0)),
            quantidade_minima=int(data.get("quantidade_minima", 10)),
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            margem_lucro=margem,
            ncm=data.get("ncm", "").strip(),
            origem=int(data.get("origem", 0)),
            controlar_validade=data.get("controlar_validade", False),
            data_validade=(
                datetime.strptime(data["data_validade"], "%Y-%m-%d").date()
                if data.get("data_validade")
                else None
            ),
            lote=data.get("lote", "").strip(),
            imagem_url=data.get("imagem_url", "").strip(),
            ativo=data.get("ativo", True),
            total_vendido=0.0,
            quantidade_vendida=0,
            ultima_venda=None,
        )

        db.session.add(produto)

        # Criar movimentação inicial de estoque
        if produto.quantidade > 0:
            movimentacao = MovimentacaoEstoque(
                estabelecimento_id=current_user.estabelecimento_id,
                produto_id=produto.id,
                funcionario_id=current_user.id,
                tipo="entrada",
                quantidade=produto.quantidade,
                quantidade_anterior=0,
                quantidade_atual=produto.quantidade,
                custo_unitario=produto.preco_custo,
                valor_total=produto.quantidade * produto.preco_custo,
                motivo="Cadastro inicial do produto",
                observacoes=f"Produto cadastrado por {current_user.nome}",
            )
            db.session.add(movimentacao)

        db.session.commit()

        current_app.logger.info(
            f"Produto criado: {produto.id} - {produto.nome} por {current_user.username}"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Produto criado com sucesso",
                    "produto": produto.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar produto: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao criar produto"}),
            500,
        )


@produtos_bp.route("/<int:id>", methods=["PUT"])
@login_required
def atualizar_produto(id):
    """Atualiza um produto existente"""
    try:
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=current_user.estabelecimento_id
        ).first_or_404()

        data = request.get_json()

        # Validação dos dados (passando ID para verificação de unicidade)
        erros = validar_dados_produto(data, produto.id)
        if erros:
            return (
                jsonify(
                    {"success": False, "message": "Erros de validação", "errors": erros}
                ),
                400,
            )

        # Guardar valores antigos para auditoria
        quantidade_anterior = produto.quantidade

        # Atualizar campos
        campos_atualizaveis = [
            "fornecedor_id",
            "codigo_barras",
            "codigo_interno",
            "nome",
            "descricao",
            "marca",
            "categoria",
            "subcategoria",
            "unidade_medida",
            "quantidade_minima",
            "preco_custo",
            "preco_venda",
            "ncm",
            "origem",
            "controlar_validade",
            "data_validade",
            "lote",
            "imagem_url",
            "ativo",
        ]

        for campo in campos_atualizaveis:
            if campo in data:
                if campo == "preco_custo":
                    produto.preco_custo = Decimal(str(data[campo]))
                elif campo == "preco_venda":
                    produto.preco_venda = Decimal(str(data[campo]))
                elif campo == "data_validade" and data[campo]:
                    produto.data_validade = datetime.strptime(
                        data[campo], "%Y-%m-%d"
                    ).date()
                elif campo in ["quantidade_minima", "origem"]:
                    setattr(produto, campo, int(data[campo]))
                elif campo == "controlar_validade":
                    setattr(produto, campo, bool(data[campo]))
                else:
                    setattr(produto, campo, data[campo])

        # Recalcular margem de lucro
        if "preco_custo" in data or "preco_venda" in data:
            if produto.preco_custo > 0:
                produto.margem_lucro = (
                    (produto.preco_venda - produto.preco_custo)
                    / produto.preco_custo
                    * 100
                )
            else:
                produto.margem_lucro = 0

        produto.updated_at = datetime.utcnow()

        # Se quantidade foi alterada, criar movimentação
        if "quantidade" in data:
            nova_quantidade = int(data["quantidade"])
            diferenca = nova_quantidade - quantidade_anterior

            if diferenca != 0:
                produto.quantidade = nova_quantidade

                movimentacao = MovimentacaoEstoque(
                    estabelecimento_id=current_user.estabelecimento_id,
                    produto_id=produto.id,
                    funcionario_id=current_user.id,
                    tipo="entrada" if diferenca > 0 else "saida",
                    quantidade=abs(diferenca),
                    quantidade_anterior=quantidade_anterior,
                    quantidade_atual=nova_quantidade,
                    custo_unitario=produto.preco_custo,
                    valor_total=abs(diferenca) * produto.preco_custo,
                    motivo="Ajuste manual de estoque",
                    observacoes=f"Produto atualizado por {current_user.nome}. Diferença: {diferenca}",
                )
                db.session.add(movimentacao)

        db.session.commit()

        current_app.logger.info(
            f"Produto atualizado: {produto.id} por {current_user.username}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Produto atualizado com sucesso",
                "produto": produto.to_dict(),
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar produto {id}: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao atualizar produto"}),
            500,
        )


@produtos_bp.route("/<int:id>/estoque", methods=["POST"])
@login_required
def ajustar_estoque(id):
    """Ajusta o estoque de um produto com movimentação registrada"""
    try:
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=current_user.estabelecimento_id
        ).first_or_404()

        data = request.get_json()

        tipo = data.get("tipo")  # 'entrada' ou 'saida'
        quantidade = data.get("quantidade", 0)
        motivo = data.get("motivo", "")
        observacoes = data.get("observacoes", "")

        if tipo not in ["entrada", "saida"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": 'Tipo inválido. Use "entrada" ou "saida"',
                    }
                ),
                400,
            )

        if not quantidade or quantidade <= 0:
            return jsonify({"success": False, "message": "Quantidade inválida"}), 400

        if not motivo:
            return jsonify({"success": False, "message": "Motivo é obrigatório"}), 400

        quantidade_anterior = produto.quantidade

        if tipo == "entrada":
            produto.quantidade += quantidade
        else:  # saida
            if produto.quantidade < quantidade:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Estoque insuficiente. Disponível: {produto.quantidade}",
                        }
                    ),
                    400,
                )
            produto.quantidade -= quantidade

        # Criar movimentação
        movimentacao = MovimentacaoEstoque(
            estabelecimento_id=current_user.estabelecimento_id,
            produto_id=produto.id,
            funcionario_id=current_user.id,
            tipo=tipo,
            quantidade=quantidade,
            quantidade_anterior=quantidade_anterior,
            quantidade_atual=produto.quantidade,
            custo_unitario=produto.preco_custo,
            valor_total=quantidade * produto.preco_custo,
            motivo=motivo,
            observacoes=observacoes,
        )

        db.session.add(movimentacao)
        db.session.commit()

        current_app.logger.info(
            f"Estoque ajustado: produto {produto.id}, tipo {tipo}, quantidade {quantidade} por {current_user.username}"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Estoque ajustado com sucesso",
                "produto": {
                    "id": produto.id,
                    "nome": produto.nome,
                    "quantidade_anterior": quantidade_anterior,
                    "quantidade_atual": produto.quantidade,
                    "diferenca": quantidade if tipo == "entrada" else -quantidade,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao ajustar estoque do produto {id}: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao ajustar estoque"}),
            500,
        )


@produtos_bp.route("/<int:id>/preco", methods=["POST"])
@login_required
def atualizar_preco(id):
    """Atualiza preços do produto com histórico"""
    try:
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=current_user.estabelecimento_id
        ).first_or_404()

        data = request.get_json()

        novo_preco_custo = data.get("preco_custo")
        novo_preco_venda = data.get("preco_venda")

        if not novo_preco_custo and not novo_preco_venda:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Informe pelo menos um preço para atualizar",
                    }
                ),
                400,
            )

        # Guardar valores antigos
        preco_custo_anterior = produto.preco_custo
        preco_venda_anterior = produto.preco_venda

        # Atualizar preços
        if novo_preco_custo:
            produto.preco_custo = Decimal(str(novo_preco_custo))

        if novo_preco_venda:
            produto.preco_venda = Decimal(str(novo_preco_venda))

        # Recalcular margem
        if produto.preco_custo > 0:
            produto.margem_lucro = (
                (produto.preco_venda - produto.preco_custo) / produto.preco_custo * 100
            )

        produto.updated_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(
            f"Preços atualizados: produto {produto.id}, custo: {preco_custo_anterior}->{produto.preco_custo}, venda: {preco_venda_anterior}->{produto.preco_venda} por {current_user.username}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Preços atualizados com sucesso",
                "produto": {
                    "id": produto.id,
                    "nome": produto.nome,
                    "preco_custo_anterior": float(preco_custo_anterior),
                    "preco_custo_atual": float(produto.preco_custo),
                    "preco_venda_anterior": float(preco_venda_anterior),
                    "preco_venda_atual": float(produto.preco_venda),
                    "margem_lucro": float(produto.margem_lucro),
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar preços do produto {id}: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao atualizar preços"}),
            500,
        )


@produtos_bp.route("/search", methods=["GET"])
@funcionario_required
def buscar_produtos():
    """Busca rápida de produtos para autocomplete (PDV, etc.)"""
    try:
        termo = request.args.get("q", "", type=str).strip()
        limite = request.args.get("limite", 20, type=int)
        apenas_ativos = request.args.get("ativo", "true", type=str).lower() == "true"
        com_estoque = request.args.get("com_estoque", None, type=str)

        if not termo or len(termo) < 1:
            return jsonify({"success": True, "produtos": []})

        # Obter claims do JWT
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")

        query = Produto.query.filter_by(
            estabelecimento_id=estabelecimento_id
        )

        if apenas_ativos:
            query = query.filter_by(ativo=True)

        if com_estoque == "true":
            query = query.filter(Produto.quantidade > 0)
        elif com_estoque == "false":
            query = query.filter(Produto.quantidade == 0)

        busca_termo = f"%{termo}%"
        produtos = (
            query.filter(
                db.or_(
                    Produto.nome.ilike(busca_termo),
                    Produto.codigo_barras.ilike(busca_termo),
                    Produto.codigo_interno.ilike(busca_termo),
                    Produto.descricao.ilike(busca_termo),
                )
            )
            .limit(limite)
            .all()
        )

        resultados = []
        for produto in produtos:
            # Obter nome da categoria de forma segura
            categoria_nome = "Sem categoria"
            if produto.categoria:
                categoria_nome = produto.categoria.nome
            
            resultados.append(
                {
                    "id": produto.id,
                    "nome": produto.nome,
                    "codigo_barras": produto.codigo_barras,
                    "codigo_interno": produto.codigo_interno,
                    "quantidade": produto.quantidade,
                    "quantidade_estoque": produto.quantidade,  # Alias para compatibilidade frontend
                    "preco_custo": float(produto.preco_custo),
                    "preco_venda": float(produto.preco_venda),
                    "margem_lucro": calcular_margem_lucro(
                        float(produto.preco_custo), float(produto.preco_venda)
                    ),
                    "ativo": produto.ativo,
                    "estoque_baixo": verificar_estoque_baixo(produto),
                    "validade_proxima": verificar_validade_proxima(produto),
                    "categoria": categoria_nome,
                    "marca": produto.marca or "",
                    "unidade_medida": produto.unidade_medida or "UN",
                }
            )

        return jsonify(
            {"success": True, "produtos": resultados, "total": len(resultados)}
        )

    except Exception as e:
        current_app.logger.error(f"Erro na busca de produtos: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno na busca de produtos"}),
            500,
        )


# ==================== ROTA DE ESTOQUE (COMPATÍVEL COM JWT) ====================

@produtos_bp.route("/estoque", methods=["GET"])
@funcionario_required
def listar_produtos_estoque():
    """Lista todos os produtos com filtros e paginação - Compatível com JWT"""
    try:
        # Obter claims do JWT
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 50, type=int)
        ativos = request.args.get("ativos", None, type=str)
        categoria = request.args.get("categoria", None, type=str)
        estoque_status = request.args.get("estoque_status", None, type=str)
        tipo = request.args.get("tipo", None, type=str)
        fornecedor_id = request.args.get("fornecedor_id", None, type=int)
        busca = request.args.get("busca", "", type=str).strip()
        ordenar_por = request.args.get("ordenar_por", "nome", type=str)
        direcao = request.args.get("direcao", "asc", type=str)

        # Query base
        query = Produto.query.filter_by(estabelecimento_id=estabelecimento_id)

        # Filtros
        if ativos is not None:
            query = query.filter_by(ativo=ativos.lower() == "true")

        if categoria:
            # Buscar categoria pelo nome
            cat = CategoriaProduto.query.filter_by(
                estabelecimento_id=estabelecimento_id,
                nome=categoria
            ).first()
            if cat:
                query = query.filter_by(categoria_id=cat.id)

        if tipo:
            query = query.filter(Produto.descricao.ilike(f"%{tipo}%"))

        if fornecedor_id:
            query = query.filter_by(fornecedor_id=fornecedor_id)

        if estoque_status:
            if estoque_status == "esgotado":
                query = query.filter(Produto.quantidade == 0)
            elif estoque_status == "baixo":
                query = query.filter(
                    Produto.quantidade > 0,
                    Produto.quantidade <= Produto.quantidade_minima
                )
            elif estoque_status == "normal":
                query = query.filter(Produto.quantidade > Produto.quantidade_minima)

        if busca:
            busca_termo = f"%{busca}%"
            query = query.filter(
                db.or_(
                    Produto.nome.ilike(busca_termo),
                    Produto.codigo_barras.ilike(busca_termo),
                    Produto.codigo_interno.ilike(busca_termo),
                    Produto.descricao.ilike(busca_termo),
                    Produto.marca.ilike(busca_termo),
                )
            )

        # Ordenação
        if ordenar_por == "nome":
            query = query.order_by(Produto.nome.asc() if direcao == "asc" else Produto.nome.desc())
        elif ordenar_por == "preco_venda":
            query = query.order_by(Produto.preco_venda.asc() if direcao == "asc" else Produto.preco_venda.desc())
        elif ordenar_por == "quantidade":
            query = query.order_by(Produto.quantidade.asc() if direcao == "asc" else Produto.quantidade.desc())
        elif ordenar_por == "margem_lucro":
            query = query.order_by(Produto.margem_lucro.asc() if direcao == "asc" else Produto.margem_lucro.desc())

        # Paginação
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

        # Estatísticas
        total_query = Produto.query.filter_by(estabelecimento_id=estabelecimento_id, ativo=True)
        total_produtos = total_query.count()
        produtos_esgotados = total_query.filter(Produto.quantidade == 0).count()
        produtos_baixo_estoque = total_query.filter(
            Produto.quantidade > 0,
            Produto.quantidade <= Produto.quantidade_minima
        ).count()
        produtos_normal = total_produtos - produtos_esgotados - produtos_baixo_estoque

        # Formatar produtos
        produtos_lista = []
        for produto in paginacao.items:
            categoria_nome = "Sem categoria"
            if produto.categoria:
                categoria_nome = produto.categoria.nome
            
            fornecedor_nome = None
            if produto.fornecedor:
                fornecedor_nome = produto.fornecedor.razao_social or produto.fornecedor.nome_fantasia

            # Determinar status do estoque
            if produto.quantidade == 0:
                estoque_status_produto = "esgotado"
            elif produto.quantidade <= produto.quantidade_minima:
                estoque_status_produto = "baixo"
            else:
                estoque_status_produto = "normal"

            produtos_lista.append({
                "id": produto.id,
                "nome": produto.nome,
                "codigo_barras": produto.codigo_barras,
                "codigo_interno": produto.codigo_interno,
                "descricao": produto.descricao,
                "categoria": categoria_nome,
                "marca": produto.marca or "",
                "fabricante": "",
                "tipo": "",
                "unidade_medida": produto.unidade_medida or "UN",
                "preco_custo": float(produto.preco_custo),
                "preco_venda": float(produto.preco_venda),
                "margem_lucro": float(produto.margem_lucro) if produto.margem_lucro else 0.0,
                "quantidade": produto.quantidade,
                "quantidade_estoque": produto.quantidade,
                "quantidade_minima": produto.quantidade_minima,
                "estoque_minimo": produto.quantidade_minima,
                "estoque_status": estoque_status_produto,
                "fornecedor_id": produto.fornecedor_id,
                "fornecedor_nome": fornecedor_nome,
                "ativo": produto.ativo,
                "lote": produto.lote if hasattr(produto, 'lote') else None,
                "data_fabricacao": None,
                "data_validade": produto.data_validade.isoformat() if hasattr(produto, 'data_validade') and produto.data_validade else None,
                "created_at": produto.created_at.isoformat() if produto.created_at else None,
                "updated_at": produto.updated_at.isoformat() if produto.updated_at else None,
            })

        return jsonify({
            "produtos": produtos_lista,
            "paginacao": {
                "pagina_atual": paginacao.page,
                "total_paginas": paginacao.pages,
                "total_itens": paginacao.total,
                "itens_por_pagina": por_pagina,
                "tem_proxima": paginacao.has_next,
                "tem_anterior": paginacao.has_prev,
                "primeira_pagina": 1,
                "ultima_pagina": paginacao.pages,
            },
            "estatisticas": {
                "total_produtos": total_produtos,
                "produtos_baixo_estoque": produtos_baixo_estoque,
                "produtos_esgotados": produtos_esgotados,
                "produtos_normal": produtos_normal,
            }
        })

    except Exception as e:
        current_app.logger.error(f"❌ Erro ao listar produtos: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.error(f"Traceback completo:\n{error_trace}")
        print(f"❌ ERRO NA ROTA /estoque: {str(e)}")
        print(error_trace)
        return jsonify({"error": f"Erro ao listar produtos: {str(e)}"}), 500


@produtos_bp.route("/categorias", methods=["GET"])
@funcionario_required
def listar_categorias():
    """Lista todas as categorias de produtos"""
    try:
        # Obter claims do JWT
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        categorias = (
            CategoriaProduto.query.filter_by(
                estabelecimento_id=estabelecimento_id, ativo=True
            )
            .order_by(CategoriaProduto.nome.asc())
            .all()
        )

        categorias_lista = []
        for categoria in categorias:
            # Contar produtos ativos na categoria
            total_produtos = Produto.query.filter_by(
                estabelecimento_id=estabelecimento_id,
                categoria_id=categoria.id,
                ativo=True,
            ).count()

            categorias_lista.append(
                {
                    "id": categoria.id,
                    "nome": categoria.nome,
                    "descricao": categoria.descricao,
                    "codigo": categoria.codigo,
                    "total_produtos": total_produtos,
                }
            )

        return jsonify(
            {
                "success": True,
                "categorias": [c["nome"] for c in categorias_lista],  # Retornar apenas nomes para compatibilidade
                "categorias_detalhadas": categorias_lista,  # Detalhes completos
                "total_categorias": len(categorias_lista),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao listar categorias: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao listar categorias"}),
            500,
        )


@produtos_bp.route("/alertas", methods=["GET"])
@login_required
def alertas_produtos():
    """Lista alertas de produtos (estoque baixo, validade próxima)"""
    try:
        alertas = []

        # Produtos com estoque baixo
        produtos_estoque_baixo = Produto.query.filter(
            Produto.estabelecimento_id == current_user.estabelecimento_id,
            Produto.ativo == True,
            Produto.quantidade_minima > 0,
            Produto.quantidade <= Produto.quantidade_minima,
        ).all()

        for produto in produtos_estoque_baixo:
            alertas.append(
                {
                    "tipo": "estoque_baixo",
                    "nivel": "alto" if produto.quantidade == 0 else "medio",
                    "produto_id": produto.id,
                    "produto_nome": produto.nome,
                    "mensagem": f"Estoque baixo: {produto.quantidade} unidades (mínimo: {produto.quantidade_minima})",
                    "quantidade": produto.quantidade,
                    "quantidade_minima": produto.quantidade_minima,
                }
            )

        # Produtos com validade próxima
        hoje = date.today()
        produtos_validade_proxima = Produto.query.filter(
            Produto.estabelecimento_id == current_user.estabelecimento_id,
            Produto.ativo == True,
            Produto.controlar_validade == True,
            Produto.data_validade != None,
            Produto.data_validade.between(hoje, hoje + timedelta(days=30)),
        ).all()

        for produto in produtos_validade_proxima:
            dias_para_validade = (produto.data_validade - hoje).days
            nivel = "critico" if dias_para_validade <= 7 else "medio"

            alertas.append(
                {
                    "tipo": "validade_proxima",
                    "nivel": nivel,
                    "produto_id": produto.id,
                    "produto_nome": produto.nome,
                    "mensagem": f"Validade próxima: {produto.data_validade} ({dias_para_validade} dias)",
                    "data_validade": produto.data_validade.isoformat(),
                    "dias_restantes": dias_para_validade,
                }
            )

        # Produtos sem movimentação há muito tempo
        data_limite = datetime.utcnow() - timedelta(days=180)  # 6 meses
        produtos_sem_movimento = Produto.query.filter(
            Produto.estabelecimento_id == current_user.estabelecimento_id,
            Produto.ativo == True,
            Produto.quantidade > 0,
            db.or_(Produto.ultima_venda == None, Produto.ultima_venda < data_limite),
        ).all()

        for produto in produtos_sem_movimento:
            if produto.ultima_venda:
                dias_sem_venda = (datetime.utcnow() - produto.ultima_venda).days
                alertas.append(
                    {
                        "tipo": "sem_movimento",
                        "nivel": "baixo",
                        "produto_id": produto.id,
                        "produto_nome": produto.nome,
                        "mensagem": f"Sem vendas há {dias_sem_venda} dias",
                        "dias_sem_venda": dias_sem_venda,
                        "ultima_venda": (
                            produto.ultima_venda.isoformat()
                            if produto.ultima_venda
                            else None
                        ),
                    }
                )

        # Ordenar por nível de criticidade
        nivel_prioridade = {"critico": 1, "alto": 2, "medio": 3, "baixo": 4}
        alertas.sort(key=lambda x: nivel_prioridade.get(x["nivel"], 5))

        return jsonify(
            {
                "success": True,
                "alertas": alertas,
                "total": len(alertas),
                "resumo": {
                    "estoque_baixo": len(
                        [a for a in alertas if a["tipo"] == "estoque_baixo"]
                    ),
                    "validade_proxima": len(
                        [a for a in alertas if a["tipo"] == "validade_proxima"]
                    ),
                    "sem_movimento": len(
                        [a for a in alertas if a["tipo"] == "sem_movimento"]
                    ),
                },
            }
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao listar alertas de produtos: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao listar alertas"}),
            500,
        )


@produtos_bp.route("/exportar", methods=["GET"])
@login_required
def exportar_produtos():
    """Exporta produtos em formato CSV"""
    try:
        apenas_ativos = request.args.get("ativo", "true", type=str).lower() == "true"

        # Buscar produtos
        query = Produto.query.filter_by(
            estabelecimento_id=current_user.estabelecimento_id
        )

        if apenas_ativos:
            query = query.filter_by(ativo=True)

        produtos = query.order_by(Produto.nome.asc()).all()

        # Gerar CSV
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")

        # Cabeçalho
        writer.writerow(
            [
                "ID",
                "Código Barras",
                "Código Interno",
                "Nome",
                "Descrição",
                "Marca",
                "Categoria",
                "Subcategoria",
                "Unidade Medida",
                "Quantidade",
                "Quantidade Mínima",
                "Preço Custo",
                "Preço Venda",
                "Margem Lucro %",
                "NCM",
                "Origem",
                "Controlar Validade",
                "Data Validade",
                "Lote",
                "Fornecedor",
                "Total Vendido",
                "Quantidade Vendida",
                "Última Venda",
                "Classificação ABC",
                "Ativo",
                "Data Cadastro",
            ]
        )

        # Dados
        for produto in produtos:
            fornecedor_nome = (
                produto.fornecedor.nome_fantasia if produto.fornecedor else ""
            )
            classificacao = calcular_classificacao_abc(produto)
            margem = calcular_margem_lucro(
                float(produto.preco_custo), float(produto.preco_venda)
            )

            writer.writerow(
                [
                    produto.id,
                    produto.codigo_barras or "",
                    produto.codigo_interno or "",
                    produto.nome or "",
                    produto.descricao or "",
                    produto.marca or "",
                    produto.categoria or "",
                    produto.subcategoria or "",
                    produto.unidade_medida or "",
                    produto.quantidade,
                    produto.quantidade_minima,
                    float(produto.preco_custo),
                    float(produto.preco_venda),
                    margem,
                    produto.ncm or "",
                    produto.origem,
                    "SIM" if produto.controlar_validade else "NÃO",
                    (
                        produto.data_validade.strftime("%d/%m/%Y")
                        if produto.data_validade
                        else ""
                    ),
                    produto.lote or "",
                    fornecedor_nome,
                    produto.total_vendido or 0,
                    produto.quantidade_vendida or 0,
                    (
                        produto.ultima_venda.strftime("%d/%m/%Y %H:%M")
                        if produto.ultima_venda
                        else ""
                    ),
                    classificacao,
                    "SIM" if produto.ativo else "NÃO",
                    (
                        produto.created_at.strftime("%d/%m/%Y %H:%M:%S")
                        if produto.created_at
                        else ""
                    ),
                ]
            )

        output.seek(0)
        return (
            output.getvalue(),
            200,
            {
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": f'attachment; filename=produtos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            },
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao exportar produtos: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao exportar produtos"}),
            500,
        )


# ============================================
# UTILITÁRIOS DE PRODUTO
# ============================================


def registrar_venda_produto(produto_id, quantidade, preco_venda, venda_id):
    """Registra uma venda para o produto (atualiza estatísticas)"""
    try:
        produto = Produto.query.get(produto_id)
        if not produto:
            return

        # Atualizar quantidade vendida
        produto.quantidade_vendida = (produto.quantidade_vendida or 0) + quantidade
        produto.total_vendido = (produto.total_vendido or 0) + (
            quantidade * preco_venda
        )
        produto.ultima_venda = datetime.utcnow()

        # Atualizar classificação ABC
        produto.classificacao_abc = calcular_classificacao_abc(produto)

        produto.updated_at = datetime.utcnow()

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao registrar venda do produto {produto_id}: {str(e)}"
        )


# ============================================
# EXPORTAÇÃO CSV
# ============================================

@produtos_bp.route("/exportar/csv", methods=["GET"])
@funcionario_required
def exportar_csv():
    """Exporta produtos para CSV"""
    try:
        import csv
        from io import StringIO
        
        # Obter claims do JWT
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        ativos = request.args.get("ativos", None, type=str)
        
        # Query base
        query = Produto.query.filter_by(estabelecimento_id=estabelecimento_id)
        
        if ativos is not None:
            query = query.filter_by(ativo=ativos.lower() == "true")
        
        produtos = query.order_by(Produto.nome.asc()).all()
        
        # Criar CSV em memória
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'ID', 'Nome', 'Código Barras', 'Código Interno', 'Categoria',
            'Marca', 'Unidade', 'Quantidade', 'Quantidade Mínima',
            'Preço Custo', 'Preço Venda', 'Margem Lucro %',
            'Fornecedor', 'Ativo', 'Data Cadastro'
        ])
        
        # Dados
        for produto in produtos:
            categoria_nome = produto.categoria.nome if produto.categoria else "Sem categoria"
            fornecedor_nome = ""
            if produto.fornecedor:
                fornecedor_nome = produto.fornecedor.razao_social or produto.fornecedor.nome_fantasia
            
            writer.writerow([
                produto.id,
                produto.nome,
                produto.codigo_barras or "",
                produto.codigo_interno or "",
                categoria_nome,
                produto.marca or "",
                produto.unidade_medida or "UN",
                produto.quantidade,
                produto.quantidade_minima,
                float(produto.preco_custo),
                float(produto.preco_venda),
                float(produto.margem_lucro) if produto.margem_lucro else 0.0,
                fornecedor_nome,
                "Sim" if produto.ativo else "Não",
                produto.created_at.strftime("%d/%m/%Y %H:%M") if produto.created_at else ""
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return jsonify({
            "success": True,
            "csv": csv_content,
            "total_produtos": len(produtos)
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao exportar CSV: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback completo:\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "message": f"❌ ERRO NA EXPORTAÇÃO CSV: {str(e)}"
        }), 500


# ==================== ROTAS CRUD ESTOQ


# ==================== ROTAS CRUD ESTOQUE COM JWT (POST, PUT, DELETE) ====================

@produtos_bp.route("/estoque", methods=["POST", "OPTIONS"])
@funcionario_required
def criar_produto_estoque():
    """Cria um novo produto - Compatível com JWT"""
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
    
    try:
        # Obter claims do JWT
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        data = request.get_json()

        # Validação dos dados
        erros = validar_dados_produto(data, estabelecimento_id=estabelecimento_id)
        if erros:
            return jsonify({"success": False, "message": "Erros de validação", "errors": erros}), 400

        # Calcular margem de lucro
        preco_custo = Decimal(str(data["preco_custo"]))
        preco_venda = Decimal(str(data["preco_venda"]))
        margem = ((preco_venda - preco_custo) / preco_custo * 100) if preco_custo > 0 else 0

        # Buscar ou criar categoria
        categoria_nome = data["categoria"].strip()
        categoria = CategoriaProduto.query.filter_by(
            estabelecimento_id=estabelecimento_id,
            nome=categoria_nome
        ).first()
        
        if not categoria:
            # Criar nova categoria
            categoria = CategoriaProduto(
                estabelecimento_id=estabelecimento_id,
                nome=categoria_nome,
                ativo=True
            )
            db.session.add(categoria)
            db.session.flush()  # Para obter o ID

        # Criar produto
        produto = Produto(
            estabelecimento_id=estabelecimento_id,
            categoria_id=categoria.id,
            fornecedor_id=data.get("fornecedor_id"),
            codigo_barras=data.get("codigo_barras", "").strip(),
            codigo_interno=data.get("codigo_interno", "").strip(),
            nome=data["nome"].strip(),
            descricao=data.get("descricao", "").strip(),
            marca=data.get("marca", "").strip(),
            unidade_medida=data.get("unidade_medida", "UN"),
            quantidade=int(data.get("quantidade", 0)),
            quantidade_minima=int(data.get("quantidade_minima", 10)),
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            margem_lucro=margem,
            ativo=data.get("ativo", True),
        )

        db.session.add(produto)
        db.session.commit()

        current_app.logger.info(f"Produto criado: {produto.id} - {produto.nome}")

        return jsonify({
            "success": True,
            "message": "Produto criado com sucesso",
            "produto": produto.to_dict(),
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar produto: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno ao criar produto"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["GET", "OPTIONS"])
@funcionario_required
def obter_produto_estoque(id):
    """Obtém um produto específico - Compatível com JWT"""
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
    
    try:
        # Obter claims do JWT
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        dados_produto = produto.to_dict()
        dados_produto["margem_lucro"] = calcular_margem_lucro(
            float(produto.preco_custo), float(produto.preco_venda)
        )

        return jsonify({
            "success": True,
            "produto": dados_produto,
        })

    except Exception as e:
        current_app.logger.error(f"Erro ao obter produto {id}: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno ao obter produto"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["PUT", "OPTIONS"])
@funcionario_required
def atualizar_produto_estoque(id):
    """Atualiza um produto existente - Compatível com JWT"""
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
    
    try:
        # Obter claims do JWT
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        data = request.get_json()

        # Validação dos dados
        erros = validar_dados_produto(data, produto.id, estabelecimento_id=estabelecimento_id)
        if erros:
            return jsonify({"success": False, "message": "Erros de validação", "errors": erros}), 400

        # Atualizar campos básicos
        if "nome" in data:
            produto.nome = data["nome"].strip()
        if "descricao" in data:
            produto.descricao = data["descricao"].strip()
        if "marca" in data:
            produto.marca = data["marca"].strip()
        if "categoria" in data:
            # Buscar ou criar categoria
            categoria_nome = data["categoria"].strip()
            categoria = CategoriaProduto.query.filter_by(
                estabelecimento_id=estabelecimento_id,
                nome=categoria_nome
            ).first()
            
            if not categoria:
                categoria = CategoriaProduto(
                    estabelecimento_id=estabelecimento_id,
                    nome=categoria_nome,
                    ativo=True
                )
                db.session.add(categoria)
                db.session.flush()
            
            produto.categoria_id = categoria.id
        if "fornecedor_id" in data:
            produto.fornecedor_id = data["fornecedor_id"]
        if "quantidade_minima" in data:
            produto.quantidade_minima = int(data["quantidade_minima"])
        if "ativo" in data:
            produto.ativo = data["ativo"]

        # Atualizar preços e recalcular margem
        if "preco_custo" in data:
            produto.preco_custo = Decimal(str(data["preco_custo"]))
        if "preco_venda" in data:
            produto.preco_venda = Decimal(str(data["preco_venda"]))

        if "preco_custo" in data or "preco_venda" in data:
            if produto.preco_custo > 0:
                produto.margem_lucro = ((produto.preco_venda - produto.preco_custo) / produto.preco_custo * 100)
            else:
                produto.margem_lucro = 0

        produto.updated_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(f"Produto atualizado: {produto.id}")

        return jsonify({
            "success": True,
            "message": "Produto atualizado com sucesso",
            "produto": produto.to_dict(),
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar produto {id}: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno ao atualizar produto"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["DELETE", "OPTIONS"])
@funcionario_required
def deletar_produto_estoque(id):
    """Desativa um produto (soft delete) - Compatível com JWT"""
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
    
    try:
        # Obter claims do JWT
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()
        
        # Soft delete - apenas desativa
        produto.ativo = False
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Produto desativado com sucesso"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Erro ao desativar produto: {str(e)}"
        }), 500
