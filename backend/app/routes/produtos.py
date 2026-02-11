# app/produtos.py
# MÓDULO COMPLETO DE PRODUTOS - ERP INDUSTRIAL BRASILEIRO
# CRUD completo com controle de estoque, validade, precificação

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from flask_jwt_extended import get_jwt_identity, get_jwt
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import re
from app.models import (
    db,
    Produto,
    Estabelecimento,
    Fornecedor,
    CategoriaProduto,
    MovimentacaoEstoque,
    Venda,
    VendaItem,
    PedidoCompraItem,
    HistoricoPrecos,
)
from app.utils import calcular_margem_lucro, formatar_codigo_barras
from app.decorators.decorator_jwt import funcionario_required
from sqlalchemy import text, func, or_

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
    """
    Calcula classificação ABC do produto usando Pareto dinâmico.
    
    Usa a classificação já calculada no modelo se disponível.
    Caso contrário, retorna 'C' como padrão.
    """
    # Se o produto já tem classificação calculada, usar ela
    if hasattr(produto, 'classificacao_abc') and produto.classificacao_abc:
        return produto.classificacao_abc
    
    # Padrão: retornar C
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
@funcionario_required
def listar_produtos():
    """Lista todos os produtos com filtros e paginação"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 50, type=int)
        ativo = request.args.get("ativo", None, type=str)
        categoria = request.args.get("categoria", None, type=str)
        estoque_baixo = request.args.get("estoque_baixo", None, type=str)
        validade_proxima = request.args.get("validade_proxima", None, type=str)
        status_giro = request.args.get("status_giro", None, type=str)  # Novo filtro
        busca = request.args.get("busca", "", type=str).strip()

        # Query base
        query = Produto.query.filter_by(
            estabelecimento_id=estabelecimento_id
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
                float(produto.preco_venda), float(produto.preco_custo)
            )
            produto_dict["valor_total_estoque"] = float(
                produto.quantidade * produto.preco_custo
            )
            produto_dict["classificacao_abc"] = calcular_classificacao_abc(produto)
            produto_dict["status_giro"] = produto.calcular_status_giro()  # Novo campo
            
            # 🔥 NOVO: Adicionar estoque_status para o frontend
            if produto.quantidade == 0:
                produto_dict["estoque_status"] = "esgotado"
            elif produto.quantidade <= produto.quantidade_minima:
                produto_dict["estoque_status"] = "baixo"
            else:
                produto_dict["estoque_status"] = "normal"

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

            # Aplicar filtro de status_giro se especificado
            if status_giro and produto_dict["status_giro"] != status_giro.lower():
                continue

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
            .filter_by(estabelecimento_id=estabelecimento_id, ativo=True)
            .scalar()
            or 0
        )

        # Produtos com estoque baixo
        produtos_estoque_baixo = Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
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
@funcionario_required
def obter_produto(id):
    """Obtém detalhes completos de um produto específico"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        # Dados básicos
        dados_produto = produto.to_dict()

        # Adicionar informações calculadas
        dados_produto["margem_lucro"] = calcular_margem_lucro(
            float(produto.preco_venda), float(produto.preco_custo)
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
                produto_id=id, estabelecimento_id=estabelecimento_id
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
@funcionario_required
def criar_produto():
    """Cria um novo produto"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        data = request.get_json()

        # Validação dos dados
        erros = validar_dados_produto(data, estabelecimento_id=estabelecimento_id)
        if erros:
            return (
                jsonify(
                    {"success": False, "message": "Erros de validação", "errors": erros}
                ),
                400,
            )

        # Encontrar categoria_id baseado no nome da categoria
        categoria_id = None
        if data.get("categoria"):
            categoria_nome = CategoriaProduto.normalizar_nome_categoria(data["categoria"])
            current_app.logger.info(f"Procurando categoria normalizada: {categoria_nome}")
            categoria_obj = CategoriaProduto.query.filter_by(
                nome=categoria_nome,
                estabelecimento_id=estabelecimento_id
            ).first()
            if categoria_obj:
                categoria_id = categoria_obj.id
                current_app.logger.info(f"Categoria encontrada: {categoria_obj.id}")
            else:
                current_app.logger.info(f"Categoria não encontrada, criando nova: {categoria_nome}")
                # Se categoria não existe, criar uma nova
                nova_categoria = CategoriaProduto(
                    nome=categoria_nome,
                    estabelecimento_id=estabelecimento_id
                )
                db.session.add(nova_categoria)
                db.session.flush()
                categoria_id = nova_categoria.id
                current_app.logger.info(f"Nova categoria criada: {categoria_id}")
        else:
            current_app.logger.info("Nenhuma categoria fornecida")

        # Calcular preços e margem
        preco_custo = Decimal(str(data.get("preco_custo", 0)))
        preco_venda = Decimal(str(data.get("preco_venda", 0)))
        
        # Calcular margem de lucro
        if preco_custo > 0:
            margem = (preco_venda - preco_custo) / preco_custo * 100
        else:
            margem = Decimal("0")

        # Criar produto
        produto = Produto(
            estabelecimento_id=estabelecimento_id,
            categoria_id=categoria_id,
            fornecedor_id=data.get("fornecedor_id"),
            codigo_barras=data.get("codigo_barras", "").strip(),
            codigo_interno=data.get("codigo_interno", "").strip(),
            nome=data["nome"].strip(),
            descricao=data.get("descricao", "").strip(),
            marca=data.get("marca", "").strip(),
            fabricante=data.get("fabricante", "").strip(),
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
        db.session.flush()  # Para obter o ID do produto

        # Registrar histórico inicial de preços
        historico_inicial = HistoricoPrecos(
            estabelecimento_id=estabelecimento_id,
            produto_id=produto.id,
            funcionario_id=int(get_jwt_identity()),
            preco_custo_anterior=Decimal("0"),
            preco_venda_anterior=Decimal("0"),
            margem_anterior=Decimal("0"),
            preco_custo_novo=produto.preco_custo,
            preco_venda_novo=produto.preco_venda,
            margem_nova=produto.margem_lucro,
            motivo="Cadastro inicial do produto",
            observacoes=f"Produto cadastrado por {claims.get('nome')}"
        )
        db.session.add(historico_inicial)

        # Criar movimentação inicial de estoque com CMP
        if produto.quantidade > 0:
            # Aplicar CMP na criação se houver quantidade inicial
            produto.recalcular_preco_custo_ponderado(
                quantidade_entrada=produto.quantidade,
                custo_unitario_entrada=preco_custo,
                estoque_atual=0,
                registrar_historico=False,  # Já registramos no histórico acima
                funcionario_id=int(get_jwt_identity()),
                motivo="Cadastro inicial do produto"
            )
            
            movimentacao = MovimentacaoEstoque(
                estabelecimento_id=estabelecimento_id,
                produto_id=produto.id,
                funcionario_id=int(get_jwt_identity()),
                tipo="entrada",
                quantidade=produto.quantidade,
                quantidade_anterior=0,
                quantidade_atual=produto.quantidade,
                custo_unitario=produto.preco_custo,
                valor_total=produto.quantidade * produto.preco_custo,
                motivo="Cadastro inicial do produto",
                observacoes=f"Produto cadastrado por {claims.get('nome')}",
            )
            db.session.add(movimentacao)

        db.session.commit()

        current_app.logger.info(
            f"Produto criado: {produto.id} - {produto.nome} por {claims.get('username')}"
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
@funcionario_required
def atualizar_produto(id):
    """Atualiza um produto existente"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        data = request.get_json()
        current_app.logger.info(f"Dados recebidos para atualização: {data}")

        # Validação dos dados (passando ID para verificação de unicidade)
        # erros = validar_dados_produto(data, produto.id)
        # if erros:
        #     current_app.logger.error(f"Erros de validação: {erros}")
        #     return (
        #         jsonify(
        #             {"success": False, "message": "Erros de validação", "errors": erros}
        #         ),
        #         400,
        #     )

        # Guardar valores antigos para auditoria
        quantidade_anterior = produto.quantidade
        preco_custo_anterior = produto.preco_custo
        preco_venda_anterior = produto.preco_venda
        margem_anterior = produto.margem_lucro

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
            "tipo",
            "fabricante",
            "data_fabricacao",
        ]

        for campo in campos_atualizaveis:
            if campo in data and data[campo] is not None:
                current_app.logger.info(f"Atualizando campo {campo}: {data[campo]} (tipo: {type(data[campo])})")
                try:
                    if campo == "preco_custo":
                        if data[campo] == "" or data[campo] is None:
                            produto.preco_custo = 0
                        else:
                            produto.preco_custo = Decimal(str(data[campo]))
                    elif campo == "preco_venda":
                        if data[campo] == "" or data[campo] is None:
                            produto.preco_venda = 0
                        else:
                            produto.preco_venda = Decimal(str(data[campo]))
                    elif campo in ["data_validade", "data_fabricacao"]:
                        if data[campo] and data[campo] != "":
                            setattr(produto, campo, datetime.strptime(data[campo], "%Y-%m-%d").date())
                        else:
                            setattr(produto, campo, None)
                    elif campo in ["quantidade_minima", "origem", "fornecedor_id"]:
                        if data[campo] == "" or data[campo] is None:
                            setattr(produto, campo, None)
                        else:
                            setattr(produto, campo, int(data[campo]))
                    elif campo == "controlar_validade":
                        setattr(produto, campo, bool(data[campo]))
                    elif campo == "categoria":
                        # Tratar categoria separadamente - encontrar ou criar categoria
                        if data[campo] and data[campo].strip():
                            categoria_nome = CategoriaProduto.normalizar_nome_categoria(data[campo])
                            categoria_obj = CategoriaProduto.query.filter_by(
                                nome=categoria_nome, 
                                estabelecimento_id=estabelecimento_id
                            ).first()
                            if categoria_obj:
                                produto.categoria_id = categoria_obj.id
                            else:
                                # Se categoria não existe, criar uma nova
                                nova_categoria = CategoriaProduto(
                                    nome=categoria_nome,
                                    estabelecimento_id=estabelecimento_id
                                )
                                db.session.add(nova_categoria)
                                db.session.flush()
                                produto.categoria_id = nova_categoria.id
                        else:
                            produto.categoria_id = None
                    else:
                        setattr(produto, campo, data[campo])
                except Exception as field_error:
                    current_app.logger.error(f"Erro específico no campo {campo}: {data[campo]} - Tipo: {type(data[campo])} - Erro: {str(field_error)}")
                    raise field_error

        # Recalcular margem de lucro
        if produto.preco_custo and produto.preco_venda and produto.preco_custo > 0:
            produto.margem_lucro = (
                (produto.preco_venda - produto.preco_custo)
                / produto.preco_custo
                * 100
            )
        else:
            produto.margem_lucro = 0

        # Registrar histórico de preços se houve alteração
        preco_alterado = False
        motivo_alteracao = []
        
        if "preco_custo" in data and abs(produto.preco_custo - preco_custo_anterior) > Decimal("0.01"):
            preco_alterado = True
            motivo_alteracao.append("custo")
        
        if "preco_venda" in data and abs(produto.preco_venda - preco_venda_anterior) > Decimal("0.01"):
            preco_alterado = True
            motivo_alteracao.append("venda")
        
        if preco_alterado:
            motivo = f"Atualização de preço ({', '.join(motivo_alteracao)})"
            historico = HistoricoPrecos(
                estabelecimento_id=estabelecimento_id,
                produto_id=produto.id,
                funcionario_id=int(get_jwt_identity()),
                preco_custo_anterior=preco_custo_anterior,
                preco_venda_anterior=preco_venda_anterior,
                margem_anterior=margem_anterior or Decimal("0"),
                preco_custo_novo=produto.preco_custo,
                preco_venda_novo=produto.preco_venda,
                margem_nova=produto.margem_lucro or Decimal("0"),
                motivo=motivo,
                observacoes=f"Produto atualizado por {claims.get('nome')}"
            )
            db.session.add(historico)

        produto.updated_at = datetime.utcnow()

        # Se quantidade foi alterada, criar movimentação
        if "quantidade" in data:
            try:
                nova_quantidade = int(data["quantidade"])
                diferenca = nova_quantidade - quantidade_anterior

                if diferenca != 0:
                    custo_unitario = data.get("custo_unitario", None)
                    if diferenca > 0:
                        produto.recalcular_preco_custo_ponderado(
                            quantidade_entrada=diferenca,
                            custo_unitario_entrada=custo_unitario,
                            estoque_atual=quantidade_anterior,
                        )
                    produto.quantidade = nova_quantidade

                    movimentacao = MovimentacaoEstoque(
                        estabelecimento_id=estabelecimento_id,
                        produto_id=produto.id,
                        funcionario_id=int(get_jwt_identity()),
                        tipo="entrada" if diferenca > 0 else "saida",
                        quantidade=abs(diferenca),
                        quantidade_anterior=quantidade_anterior,
                        quantidade_atual=nova_quantidade,
                        custo_unitario=(
                            custo_unitario
                            if (diferenca > 0 and custo_unitario is not None)
                            else produto.preco_custo
                        ),
                        valor_total=abs(diferenca)
                        * (
                            custo_unitario
                            if (diferenca > 0 and custo_unitario is not None)
                            else produto.preco_custo
                        ),
                        motivo="Ajuste manual de estoque",
                        observacoes=f"Produto atualizado por {claims.get('nome')}. Diferença: {diferenca}",
                    )
                    db.session.add(movimentacao)
            except (ValueError, TypeError) as e:
                current_app.logger.error(f"Erro ao processar quantidade: {data.get('quantidade')} - {e}")
                return jsonify({"success": False, "message": f"Erro na quantidade: {str(e)}"}), 400

        db.session.commit()

        current_app.logger.info(
            f"Produto atualizado: {produto.id} por {claims.get('username')}"
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


@produtos_bp.route("/<int:id>", methods=["DELETE"])
@funcionario_required
def deletar_produto(id):
    """Desativa um produto (soft delete)"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        # Soft delete - apenas desativa
        produto.ativo = False
        db.session.commit()

        current_app.logger.info(
            f"Produto desativado: {produto.id} por {claims.get('username')}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Produto desativado com sucesso",
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao desativar produto {id}: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao desativar produto"}),
            500,
        )


@produtos_bp.route("/<int:id>/estoque", methods=["POST"])
@funcionario_required
def ajustar_estoque(id):
    """Ajusta o estoque de um produto com movimentação registrada"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        data = request.get_json()

        tipo = data.get("tipo")  # 'entrada' ou 'saida'
        quantidade = data.get("quantidade", 0)
        custo_unitario = data.get("custo_unitario", None)
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
            # Guardar custo anterior para auditoria
            custo_anterior = Decimal(str(produto.preco_custo or 0))
            
            # Aplicar CMP (Custo Médio Ponderado)
            produto.recalcular_preco_custo_ponderado(
                quantidade_entrada=quantidade,
                custo_unitario_entrada=custo_unitario,
                estoque_atual=quantidade_anterior,
                registrar_historico=True,
                funcionario_id=int(get_jwt_identity()),
                motivo=motivo
            )
            produto.quantidade += quantidade
            
            # Registrar no histórico se houve mudança de custo
            if abs(produto.preco_custo - custo_anterior) > Decimal("0.01"):
                historico = HistoricoPrecos(
                    estabelecimento_id=estabelecimento_id,
                    produto_id=produto.id,
                    funcionario_id=int(get_jwt_identity()),
                    preco_custo_anterior=custo_anterior,
                    preco_venda_anterior=produto.preco_venda,
                    margem_anterior=produto.margem_lucro,
                    preco_custo_novo=produto.preco_custo,
                    preco_venda_novo=produto.preco_venda,
                    margem_nova=produto.margem_lucro,
                    motivo=f"CMP - Entrada de {quantidade} unidades",
                    observacoes=f"Custo anterior: R$ {custo_anterior}, Novo custo: R$ {produto.preco_custo}"
                )
                db.session.add(historico)
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
            estabelecimento_id=estabelecimento_id,
            produto_id=produto.id,
            funcionario_id=int(get_jwt_identity()),
            tipo=tipo,
            quantidade=quantidade,
            quantidade_anterior=quantidade_anterior,
            quantidade_atual=produto.quantidade,
            custo_unitario=(
                custo_unitario if (tipo == "entrada" and custo_unitario is not None) else produto.preco_custo
            ),
            valor_total=quantidade
            * (
                custo_unitario if (tipo == "entrada" and custo_unitario is not None) else produto.preco_custo
            ),
            motivo=motivo,
            observacoes=observacoes,
        )

        db.session.add(movimentacao)
        db.session.commit()

        current_app.logger.info(
            f"Estoque ajustado: produto {produto.id}, tipo {tipo}, quantidade {quantidade} por {claims.get('username')}"
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
@funcionario_required
def atualizar_preco(id):
    """Atualiza preços do produto com histórico de auditoria"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        funcionario_id = int(get_jwt_identity())
        
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        data = request.get_json()

        novo_preco_custo = data.get("preco_custo")
        novo_preco_venda = data.get("preco_venda")
        motivo = data.get("motivo", "Ajuste de preço")

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

        # Guardar valores antigos para auditoria
        preco_custo_anterior = Decimal(str(produto.preco_custo or 0))
        preco_venda_anterior = Decimal(str(produto.preco_venda or 0))
        margem_anterior = Decimal(str(produto.margem_lucro or 0))

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
        else:
            produto.margem_lucro = Decimal("0")

        produto.updated_at = datetime.utcnow()
        
        # Registrar histórico de preços para auditoria
        historico = HistoricoPrecos(
            estabelecimento_id=estabelecimento_id,
            produto_id=produto.id,
            funcionario_id=funcionario_id,
            preco_custo_anterior=preco_custo_anterior,
            preco_venda_anterior=preco_venda_anterior,
            margem_anterior=margem_anterior,
            preco_custo_novo=produto.preco_custo,
            preco_venda_novo=produto.preco_venda,
            margem_nova=produto.margem_lucro,
            motivo=motivo,
            observacoes=f"Atualizado por {claims.get('nome')}"
        )
        db.session.add(historico)
        db.session.commit()

        current_app.logger.info(
            f"Preços atualizados: produto {produto.id}, custo: {preco_custo_anterior}->{produto.preco_custo}, venda: {preco_venda_anterior}->{produto.preco_venda} por {claims.get('username')}"
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
                    "margem_lucro": calcular_margem_lucro(float(produto.preco_venda), float(produto.preco_custo)),
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

        busca_termo = f"%{termo.lower()}%"
        produtos = (
            query.filter(
                db.or_(
                    db.func.lower(Produto.nome).like(busca_termo),
                    Produto.codigo_barras.ilike(busca_termo),
                    Produto.codigo_interno.ilike(busca_termo),
                    db.func.lower(Produto.descricao).like(busca_termo),
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
                        float(produto.preco_venda), float(produto.preco_custo)
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
        
        # Atualizar classificações ABC se não foram atualizadas recentemente
        try:
            Produto.atualizar_classificacoes_abc(estabelecimento_id, periodo_dias=90)
        except Exception as abc_error:
            current_app.logger.warning(f"⚠️ Erro ao atualizar ABC: {str(abc_error)}")
            # Continuar mesmo se falhar
        
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
            # Buscar categoria pelo nome (case insensitive)
            current_app.logger.info(f"🔍 Filtrando por categoria: '{categoria}'")
            cat = CategoriaProduto.query.filter(
                CategoriaProduto.estabelecimento_id == estabelecimento_id,
                CategoriaProduto.nome.ilike(categoria)
            ).first()

            if cat:
                current_app.logger.info(f"✅ Categoria encontrada: ID={cat.id}, Nome={cat.nome}")
                query = query.filter_by(categoria_id=cat.id)
            else:
                current_app.logger.warning(f"⚠️ Categoria '{categoria}' não encontrada na busca direta")
                # Tentar buscar com normalização
                categoria_normalizada = CategoriaProduto.normalizar_nome_categoria(categoria)
                current_app.logger.info(f"🔄 Tentando com nome normalizado: '{categoria_normalizada}'")
                
                cat = CategoriaProduto.query.filter(
                    CategoriaProduto.estabelecimento_id == estabelecimento_id,
                    CategoriaProduto.nome.ilike(categoria_normalizada)
                ).first()
                
                if cat:
                    current_app.logger.info(f"✅ Categoria encontrada após normalização: ID={cat.id}")
                    query = query.filter_by(categoria_id=cat.id)
                else:
                    current_app.logger.error(f"❌ Categoria não encontrada mesmo após normalização. Retornando vazio.")
                    # Se filtrou por categoria e ela não existe, não deve retornar nada
                    query = query.filter(Produto.id == -1)

        if tipo:
            # CORRIGIDO: Filtrar por campo 'tipo' ao invés de 'descricao'
            current_app.logger.info(f"🔍 Filtrando por tipo: '{tipo}'")
            query = query.filter(Produto.tipo.ilike(f"%{tipo}%"))
            count_tipo = query.count()
            current_app.logger.info(f"📊 Produtos encontrados com tipo '{tipo}': {count_tipo}")

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
        produtos_esgotados = total_query.filter(Produto.quantidade <= 0).count()
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
            if produto.quantidade <= 0:
                estoque_status_produto = "esgotado"
            elif produto.quantidade <= produto.quantidade_minima:
                estoque_status_produto = "baixo"
            else:
                estoque_status_produto = "normal"

            # Calcular margem de lucro corretamente
            margem_lucro_calculada = calcular_margem_lucro(
                float(produto.preco_venda), float(produto.preco_custo)
            )

            produto_dict = {
                "id": produto.id,
                "nome": produto.nome,
                "codigo_barras": produto.codigo_barras,
                "codigo_interno": produto.codigo_interno,
                "descricao": produto.descricao,
                "categoria": categoria_nome,
                "marca": produto.marca or "",
                "fabricante": produto.fabricante or "",
                "tipo": produto.tipo or "",
                "unidade_medida": produto.unidade_medida or "UN",
                "preco_custo": float(produto.preco_custo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "preco_venda": float(produto.preco_venda.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "margem_lucro": margem_lucro_calculada,
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
                "quantidade_vendida": produto.quantidade_vendida or 0,
                "total_vendido": float((produto.total_vendido or Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                "ultima_venda": produto.ultima_venda.isoformat() if produto.ultima_venda else None,
                "classificacao_abc": produto.classificacao_abc or "C",
            }
            
            produtos_lista.append(produto_dict)

        # DEBUG: Log do primeiro produto para verificar dados
        if produtos_lista:
            current_app.logger.info(f"🔍 PRIMEIRO PRODUTO ENVIADO: {produtos_lista[0]['nome']}")
            current_app.logger.info(f"   quantidade_vendida: {produtos_lista[0]['quantidade_vendida']}")
            current_app.logger.info(f"   total_vendido: {produtos_lista[0]['total_vendido']}")
            current_app.logger.info(f"   ultima_venda: {produtos_lista[0]['ultima_venda']}")

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
        try:
            claims = get_jwt()
            estabelecimento_id = claims.get("estabelecimento_id")
            pagina = request.args.get("pagina", 1, type=int)
            por_pagina = request.args.get("por_pagina", 50, type=int)
            ordenar_por = request.args.get("ordenar_por", "nome", type=str)
            direcao = request.args.get("direcao", "asc", type=str)
            order_clause = "nome" if ordenar_por not in {"preco_venda", "quantidade"} else ordenar_por
            order_dir = "ASC" if direcao == "asc" else "DESC"
            sql = text(
                f"SELECT id, nome, codigo_barras, codigo_interno, descricao, marca, unidade_medida, "
                f"preco_custo, preco_venda, quantidade, quantidade_minima, ativo, "
                f"quantidade_vendida, total_vendido, ultima_venda, classificacao_abc, fornecedor_id, "
                f"lote, data_validade, controlar_validade "
                f"FROM produtos "
                f"WHERE estabelecimento_id = :estabelecimento_id "
                f"ORDER BY {order_clause} {order_dir} "
                f"LIMIT :limit OFFSET :offset"
            )
            offset = (pagina - 1) * por_pagina
            rows = db.session.execute(sql, {"estabelecimento_id": estabelecimento_id, "limit": por_pagina, "offset": offset}).fetchall()
            produtos_lista = []
            for r in rows:
                # r can be RowMapping or tuple; support both
                rid = r["id"] if isinstance(r, dict) or hasattr(r, "keys") else r[0]
                nome = r["nome"] if isinstance(r, dict) or hasattr(r, "keys") else r[1]
                codigo_barras = r.get("codigo_barras", None) if hasattr(r, "get") else r[2]
                codigo_interno = r.get("codigo_interno", None) if hasattr(r, "get") else r[3]
                descricao = r.get("descricao", None) if hasattr(r, "get") else r[4]
                marca = r.get("marca", None) if hasattr(r, "get") else r[5]
                unidade_medida = r.get("unidade_medida", "UN") if hasattr(r, "get") else r[6]
                preco_custo = r.get("preco_custo", 0) if hasattr(r, "get") else r[7]
                preco_venda = r.get("preco_venda", 0) if hasattr(r, "get") else r[8]
                quantidade = r.get("quantidade", 0) if hasattr(r, "get") else r[9]
                quantidade_minima = r.get("quantidade_minima", 0) if hasattr(r, "get") else r[10]
                ativo = r.get("ativo", True) if hasattr(r, "get") else r[11]
                quantidade_vendida = r.get("quantidade_vendida", 0) if hasattr(r, "get") else r[12]
                total_vendido = r.get("total_vendido", 0) if hasattr(r, "get") else r[13]
                ultima_venda = r.get("ultima_venda", None) if hasattr(r, "get") else r[14]
                classificacao_abc = r.get("classificacao_abc", "C") if hasattr(r, "get") else r[15]
                fornecedor_id = r.get("fornecedor_id", None) if hasattr(r, "get") else r[16]
                lote = r.get("lote", None) if hasattr(r, "get") else r[17]
                data_validade = r.get("data_validade", None) if hasattr(r, "get") else r[18]
                controlar_validade = r.get("controlar_validade", False) if hasattr(r, "get") else r[19]
                
                # Formatar ultima_venda se existir
                ultima_venda_iso = None
                if ultima_venda:
                    if isinstance(ultima_venda, str):
                        ultima_venda_iso = ultima_venda
                    else:
                        ultima_venda_iso = ultima_venda.isoformat() if hasattr(ultima_venda, 'isoformat') else str(ultima_venda)
                
                # Buscar fornecedor_nome se fornecedor_id existe
                fornecedor_nome = None
                if fornecedor_id:
                    try:
                        fornecedor = Fornecedor.query.get(fornecedor_id)
                        if fornecedor:
                            fornecedor_nome = fornecedor.razao_social or fornecedor.nome_fantasia
                    except Exception as e:
                        current_app.logger.warning(f"⚠️ Erro ao buscar fornecedor {fornecedor_id}: {str(e)}")
                
                estoque_status_produto = "esgotado" if quantidade <= 0 else ("baixo" if quantidade <= quantidade_minima else "normal")
                produtos_lista.append({
                    "id": rid,
                    "nome": nome,
                    "codigo_barras": codigo_barras,
                    "codigo_interno": codigo_interno,
                    "descricao": descricao,
                    "categoria": None,
                    "marca": marca or "",
                    "fabricante": "",
                    "tipo": "",
                    "unidade_medida": unidade_medida or "UN",
                    "preco_custo": float(preco_custo or 0),
                    "preco_venda": float(preco_venda or 0),
                    "margem_lucro": calcular_margem_lucro(float(preco_venda or 0), float(preco_custo or 0)),
                    "quantidade": quantidade,
                    "quantidade_estoque": quantidade,
                    "quantidade_minima": quantidade_minima,
                    "estoque_minimo": quantidade_minima,
                    "estoque_status": estoque_status_produto,
                    "fornecedor_id": fornecedor_id,
                    "fornecedor_nome": fornecedor_nome,
                    "ativo": bool(ativo),
                    "lote": lote,
                    "data_fabricacao": None,
                    "data_validade": str(data_validade) if data_validade else None,
                    "controlar_validade": bool(controlar_validade),
                    "created_at": None,
                    "updated_at": None,
                    "quantidade_vendida": quantidade_vendida or 0,
                    "total_vendido": float(total_vendido or 0),
                    "ultima_venda": ultima_venda_iso,
                    "classificacao_abc": classificacao_abc or "C",
                })
            total_sql = text(
                "SELECT COUNT(*) FROM produtos WHERE estabelecimento_id = :estabelecimento_id"
            )
            total = db.session.execute(total_sql, {"estabelecimento_id": estabelecimento_id}).scalar() or 0
            total_paginas = (total + por_pagina - 1) // por_pagina
            return jsonify({
                "produtos": produtos_lista,
                "paginacao": {
                    "pagina_atual": pagina,
                    "total_paginas": total_paginas,
                    "total_itens": total,
                    "itens_por_pagina": por_pagina,
                    "tem_proxima": pagina < total_paginas,
                    "tem_anterior": pagina > 1,
                    "primeira_pagina": 1,
                    "ultima_pagina": total_paginas,
                },
            })
        except Exception as e2:
            current_app.logger.error(f"Fallback estoque falhou: {str(e2)}")
            return jsonify({"error": f"Erro ao listar produtos: {str(e)}"}), 500


@produtos_bp.route("/estatisticas", methods=["GET"])
@funcionario_required
def obter_estatisticas_produtos():
    """
    Retorna estatísticas agregadas dos produtos com filtros aplicados.
    Suporta os mesmos filtros da listagem para consistência.
    """
    try:
        # Obter claims do JWT
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        # Obter filtros (mesmos da listagem)
        ativos = request.args.get("ativos", None, type=str)
        categoria = request.args.get("categoria", None, type=str)
        estoque_status = request.args.get("estoque_status", None, type=str)
        tipo = request.args.get("tipo", None, type=str)
        fornecedor_id = request.args.get("fornecedor_id", None, type=int)
        busca = request.args.get("busca", "", type=str).strip()
        filtro_rapido = request.args.get("filtro_rapido", None, type=str)

        # Query base
        query = Produto.query.filter_by(estabelecimento_id=estabelecimento_id)

        # Aplicar mesmos filtros da listagem
        if ativos is not None:
            query = query.filter_by(ativo=ativos.lower() == "true")

        if categoria:
            cat = CategoriaProduto.query.filter(
                CategoriaProduto.estabelecimento_id == estabelecimento_id,
                CategoriaProduto.nome.ilike(categoria)
            ).first()
            if cat:
                query = query.filter_by(categoria_id=cat.id)
            else:
                # Categoria não encontrada, retornar estatísticas zeradas
                return jsonify({
                    "success": True,
                    "estatisticas": {
                        "total_produtos": 0,
                        "produtos_baixo_estoque": 0,
                        "produtos_esgotados": 0,
                        "produtos_normal": 0,
                        "valor_total_estoque": 0.0,
                        "margem_media": 0.0,
                        "classificacao_abc": {"A": 0, "B": 0, "C": 0},
                        "giro_estoque": {"rapido": 0, "normal": 0, "lento": 0},
                        "filtros_aplicados": {
                            "categoria": categoria,
                            "ativos": ativos,
                            "estoque_status": estoque_status,
                            "tipo": tipo,
                            "fornecedor_id": fornecedor_id,
                            "busca": busca,
                            "filtro_rapido": filtro_rapido
                        }
                    }
                })

        if tipo:
            query = query.filter(Produto.tipo.ilike(f"%{tipo}%"))

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

        # Aplicar filtro rápido
        if filtro_rapido:
            hoje = datetime.utcnow()
            
            if filtro_rapido == "classe_a":
                # Para classe A, precisamos calcular baseado no faturamento
                # Por simplicidade, vamos usar produtos com maior total_vendido
                query = query.filter(Produto.total_vendido > 0).order_by(Produto.total_vendido.desc())
                total_produtos = query.count()
                limite_a = int(total_produtos * 0.2)  # Top 20%
                if limite_a > 0:
                    produtos_classe_a = query.limit(limite_a).all()
                    ids_classe_a = [p.id for p in produtos_classe_a]
                    query = query.filter(Produto.id.in_(ids_classe_a))
                else:
                    query = query.filter(Produto.id == -1)  # Nenhum resultado
                    
            elif filtro_rapido == "classe_c":
                # Classe C: produtos com menor faturamento ou sem vendas
                query = query.filter(
                    or_(
                        Produto.total_vendido == None,
                        Produto.total_vendido == 0,
                        Produto.quantidade_vendida == None,
                        Produto.quantidade_vendida == 0
                    )
                )
                
            elif filtro_rapido == "giro_rapido":
                # Vendido nos últimos 7 dias
                data_limite = hoje - timedelta(days=7)
                query = query.filter(Produto.ultima_venda >= data_limite)
                
            elif filtro_rapido == "giro_lento":
                # Mais de 30 dias sem venda ou nunca vendeu
                data_limite = hoje - timedelta(days=30)
                query = query.filter(
                    or_(
                        Produto.ultima_venda == None,
                        Produto.ultima_venda < data_limite
                    )
                )
                
            elif filtro_rapido == "margem_alta":
                # Filtrar em Python: margem > 50%
                # Será aplicado após buscar todos os produtos
                pass
                
            elif filtro_rapido == "margem_baixa":
                # Filtrar em Python: margem < 30%
                # Será aplicado após buscar todos os produtos
                pass
                
            elif filtro_rapido == "repor_urgente":
                query = query.filter(
                    or_(
                        Produto.quantidade == 0,
                        Produto.quantidade <= Produto.quantidade_minima
                    )
                )
                
            elif filtro_rapido == "sem_fornecedor":
                query = query.filter(Produto.fornecedor_id == None)

        # Obter todos os produtos filtrados
        produtos = query.all()
        
        # Aplicar filtros de margem em Python (após calcular a margem corretamente)
        if filtro_rapido == "margem_alta":
            produtos = [p for p in produtos if calcular_margem_lucro(float(p.preco_venda), float(p.preco_custo)) >= 50]
        elif filtro_rapido == "margem_baixa":
            produtos = [p for p in produtos if calcular_margem_lucro(float(p.preco_venda), float(p.preco_custo)) < 30]

        # CALCULAR ESTATÍSTICAS COM DECIMAL PARA PRECISÃO
        total_produtos = len(produtos)
        produtos_esgotados = 0
        produtos_baixo_estoque = 0
        produtos_normal = 0
        valor_total_estoque = Decimal('0')
        soma_margens = Decimal('0')
        
        # Classificação ABC
        abc_counts = {"A": 0, "B": 0, "C": 0}
        
        # Giro de estoque
        giro_counts = {"rapido": 0, "normal": 0, "lento": 0}
        
        hoje = datetime.utcnow()
        
        # Calcular faturamento total para classificação ABC
        produtos_com_faturamento = []
        faturamento_total = Decimal('0')
        
        for produto in produtos:
            faturamento = Decimal(str(produto.total_vendido or 0))
            produtos_com_faturamento.append({
                'produto': produto,
                'faturamento': faturamento
            })
            faturamento_total += faturamento
        
        # Ordenar por faturamento para classificação ABC
        produtos_com_faturamento.sort(key=lambda x: x['faturamento'], reverse=True)
        
        # Processar cada produto - LOOP ÚNICO
        acumulado_faturamento = Decimal('0')
        
        for item in produtos_com_faturamento:
            produto = item['produto']
            faturamento = item['faturamento']
            
            # Status do estoque
            if produto.quantidade <= 0:
                produtos_esgotados += 1
            elif produto.quantidade <= produto.quantidade_minima:
                produtos_baixo_estoque += 1
            else:
                produtos_normal += 1
            
            # Valor total do estoque
            valor_produto = Decimal(str(produto.preco_custo or 0)) * Decimal(str(produto.quantidade or 0))
            valor_total_estoque += valor_produto
            
            # Margem - USAR FÓRMULA CORRIGIDA
            margem_calculada = calcular_margem_lucro(float(produto.preco_venda), float(produto.preco_custo))
            soma_margens += Decimal(str(margem_calculada))
            
            # Acumular faturamento para ABC
            acumulado_faturamento += faturamento
            
            # Classificação ABC (Pareto 80/20)
            # A: primeiros 80% do faturamento acumulado (produtos mais valiosos)
            # B: próximos 15% (até 95% acumulado)
            # C: últimos 5% (produtos menos valiosos)
            if faturamento_total > 0:
                percentual_acumulado = acumulado_faturamento / faturamento_total
                
                # Classificar baseado no percentual acumulado
                if percentual_acumulado <= Decimal('0.80'):
                    abc_counts["A"] += 1
                    produto.classificacao_abc = "A"
                elif percentual_acumulado <= Decimal('0.95'):
                    abc_counts["B"] += 1
                    produto.classificacao_abc = "B"
                else:
                    abc_counts["C"] += 1
                    produto.classificacao_abc = "C"
            else:
                # Se não há faturamento, classificar como C
                abc_counts["C"] += 1
                produto.classificacao_abc = "C"
            
            # Giro de estoque - Corrigido
            # Rápido: vendido nos últimos 7 dias
            # Normal: vendido entre 8 e 30 dias
            # Lento: não vendido há mais de 30 dias ou nunca vendeu
            if produto.ultima_venda:
                dias_desde_venda = (hoje - produto.ultima_venda).days
                if dias_desde_venda <= 7:
                    giro_counts["rapido"] += 1
                elif dias_desde_venda <= 30:
                    giro_counts["normal"] += 1
                else:
                    giro_counts["lento"] += 1
            else:
                # Nunca vendeu = giro lento
                giro_counts["lento"] += 1

        # Calcular margem média
        margem_media = soma_margens / total_produtos if total_produtos > 0 else Decimal('0')

        # Preparar lista de produtos com todos os campos
        produtos_lista = []
        for produto in produtos:
            prod_dict = produto.to_dict()
            # Garantir que os campos estão presentes
            prod_dict['total_vendido'] = float(produto.total_vendido or 0)
            prod_dict['quantidade_vendida'] = int(produto.quantidade_vendida or 0)
            prod_dict['ultima_venda'] = produto.ultima_venda.isoformat() if produto.ultima_venda else None
            # USAR FÓRMULA CORRIGIDA PARA MARGEM
            prod_dict['margem_lucro'] = calcular_margem_lucro(float(produto.preco_venda), float(produto.preco_custo))
            produtos_lista.append(prod_dict)

        # Preparar resposta
        estatisticas = {
            "total_produtos": total_produtos,
            "produtos_baixo_estoque": produtos_baixo_estoque,
            "produtos_esgotados": produtos_esgotados,
            "produtos_normal": produtos_normal,
            "valor_total_estoque": float(valor_total_estoque.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            "margem_media": float(margem_media.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            "classificacao_abc": abc_counts,
            "giro_estoque": giro_counts,
            "produtos": produtos_lista,
            "filtros_aplicados": {
                "categoria": categoria,
                "ativos": ativos,
                "estoque_status": estoque_status,
                "tipo": tipo,
                "fornecedor_id": fornecedor_id,
                "busca": busca,
                "filtro_rapido": filtro_rapido
            }
        }

        current_app.logger.info(f"📊 Estatísticas calculadas: {total_produtos} produtos, filtros: {filtro_rapido}")

        return jsonify({
            "success": True,
            "estatisticas": estatisticas
        })

    except Exception as e:
        current_app.logger.error(f"❌ Erro ao calcular estatísticas: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback completo:\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "message": f"Erro interno ao calcular estatísticas: {str(e)}"
        }), 500


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
        try:
            claims = get_jwt()
            estabelecimento_id = claims.get("estabelecimento_id")
            sql = text(
                "SELECT DISTINCT categoria AS nome "
                "FROM produtos "
                "WHERE estabelecimento_id = :estabelecimento_id AND (ativo = TRUE OR ativo IS NULL)"
            )
            result = db.session.execute(sql, {"estabelecimento_id": estabelecimento_id}).fetchall()
            categorias_nomes = []
            for row in result:
                try:
                    categorias_nomes.append(row["nome"])
                except Exception:
                    categorias_nomes.append(row[0])
            categorias_nomes = [n for n in categorias_nomes if n]
            return jsonify(
                {
                    "success": True,
                    "categorias": categorias_nomes,
                    "categorias_detalhadas": [{"id": None, "nome": n, "descricao": None, "codigo": None, "total_produtos": None} for n in categorias_nomes],
                    "total_categorias": len(categorias_nomes),
                }
            )
        except Exception as e2:
            current_app.logger.error(f"Fallback categorias falhou: {str(e2)}")
            return (
                jsonify({"success": False, "message": "Erro interno ao listar categorias"}),
                500,
            )


@produtos_bp.route("/alertas", methods=["GET"])
@funcionario_required
def alertas_produtos():
    """Lista alertas de produtos (estoque baixo, validade próxima)"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        alertas = []

        # Produtos com estoque baixo
        produtos_estoque_baixo = Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
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
            Produto.estabelecimento_id == estabelecimento_id,
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
            Produto.estabelecimento_id == estabelecimento_id,
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
@funcionario_required
def exportar_produtos():
    """Exporta produtos em formato CSV"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        apenas_ativos = request.args.get("ativo", "true", type=str).lower() == "true"

        # Buscar produtos
        query = Produto.query.filter_by(
            estabelecimento_id=estabelecimento_id
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
                float(produto.preco_venda), float(produto.preco_custo)
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
                calcular_margem_lucro(float(produto.preco_venda), float(produto.preco_custo)),
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
            float(produto.preco_venda), float(produto.preco_custo)
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


# ============================================
# ROTAS PROFISSIONAIS - UPGRADE DE ENGENHARIA
# ============================================


@produtos_bp.route("/<int:id>/historico-precos", methods=["GET"])
@funcionario_required
def obter_historico_precos(id):
    """
    Obtém o histórico completo de alterações de preços de um produto.
    
    Permite análise temporal de:
    - Evolução de margem de lucro
    - Impacto de reajustes no faturamento
    - Elasticidade-preço da demanda
    - Compliance e auditoria fiscal
    """
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        # Verificar se produto existe e pertence ao estabelecimento
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()
        
        # Buscar histórico ordenado por data (mais recente primeiro)
        historico = (
            HistoricoPrecos.query
            .filter_by(produto_id=id, estabelecimento_id=estabelecimento_id)
            .order_by(HistoricoPrecos.data_alteracao.desc())
            .all()
        )
        
        historico_lista = [h.to_dict() for h in historico]
        
        # Calcular estatísticas do histórico
        if historico_lista:
            primeira_alteracao = historico[-1]  # Mais antiga
            ultima_alteracao = historico[0]  # Mais recente
            
            variacao_custo_total = (
                (ultima_alteracao.preco_custo_novo - primeira_alteracao.preco_custo_anterior) 
                / primeira_alteracao.preco_custo_anterior * 100
                if primeira_alteracao.preco_custo_anterior > 0 else 0
            )
            
            variacao_venda_total = (
                (ultima_alteracao.preco_venda_novo - primeira_alteracao.preco_venda_anterior)
                / primeira_alteracao.preco_venda_anterior * 100
                if primeira_alteracao.preco_venda_anterior > 0 else 0
            )
            
            estatisticas = {
                "total_alteracoes": len(historico_lista),
                "primeira_alteracao": primeira_alteracao.data_alteracao.isoformat(),
                "ultima_alteracao": ultima_alteracao.data_alteracao.isoformat(),
                "variacao_custo_total_pct": float(variacao_custo_total),
                "variacao_venda_total_pct": float(variacao_venda_total),
                "preco_custo_inicial": float(primeira_alteracao.preco_custo_anterior),
                "preco_custo_atual": float(produto.preco_custo),
                "preco_venda_inicial": float(primeira_alteracao.preco_venda_anterior),
                "preco_venda_atual": float(produto.preco_venda),
            }
        else:
            estatisticas = {
                "total_alteracoes": 0,
                "preco_custo_atual": float(produto.preco_custo),
                "preco_venda_atual": float(produto.preco_venda),
            }
        
        return jsonify({
            "success": True,
            "produto": {
                "id": produto.id,
                "nome": produto.nome,
                "codigo_interno": produto.codigo_interno,
            },
            "historico": historico_lista,
            "estatisticas": estatisticas,
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter histórico de preços do produto {id}: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao obter histórico de preços"}),
            500,
        )


@produtos_bp.route("/<int:id>/vendas-historico", methods=["GET"])
@funcionario_required
def obter_vendas_historico(id):
    """
    Obtém o histórico de vendas de um produto nos últimos 90 dias.
    
    Retorna dados agregados por dia para análise temporal:
    - Quantidade vendida por dia
    - Faturamento por dia
    - Identificação de padrões e sazonalidade
    """
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        # Verificar se produto existe e pertence ao estabelecimento
        produto = Produto.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()
        
        # Calcular data de 90 dias atrás
        from datetime import datetime, timedelta
        data_inicio = datetime.utcnow() - timedelta(days=90)
        
        # Buscar vendas dos últimos 90 dias
        # Agregar por data usando func.date() que é mais compatível
        from sqlalchemy import func
        
        vendas_por_dia = (
            db.session.query(
                func.date(VendaItem.created_at).label('data'),
                func.sum(VendaItem.quantidade).label('quantidade_total'),
                func.sum(VendaItem.total_item).label('valor_total'),
                func.count(VendaItem.id).label('numero_vendas')
            )
            .join(Venda, VendaItem.venda_id == Venda.id)
            .filter(
                VendaItem.produto_id == id,
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.status == 'finalizada',
                VendaItem.created_at >= data_inicio
            )
            .group_by(func.date(VendaItem.created_at))
            .order_by(func.date(VendaItem.created_at).asc())
            .all()
        )
        
        # Formatar dados para o frontend
        historico_vendas = []
        for venda in vendas_por_dia:
            # A data vem como string do func.date()
            data_str = str(venda.data) if venda.data else None
            
            if data_str:
                historico_vendas.append({
                    'data': data_str,
                    'quantidade': int(venda.quantidade_total or 0),
                    'valor_total': float(venda.valor_total or 0),
                    'numero_vendas': int(venda.numero_vendas or 0),
                    'ticket_medio': float(venda.valor_total / venda.numero_vendas) if venda.numero_vendas and venda.numero_vendas > 0 else 0
                })
        
        # Calcular estatísticas
        if historico_vendas:
            total_quantidade = sum(v['quantidade'] for v in historico_vendas)
            total_valor = sum(v['valor_total'] for v in historico_vendas)
            dias_com_venda = len(historico_vendas)
            media_diaria = total_quantidade / 90  # Média considerando todos os 90 dias
            
            estatisticas = {
                'total_vendido_90d': total_quantidade,
                'faturamento_90d': total_valor,
                'dias_com_venda': dias_com_venda,
                'dias_sem_venda': 90 - dias_com_venda,
                'media_diaria': round(media_diaria, 2),
                'ticket_medio': round(total_valor / total_quantidade, 2) if total_quantidade > 0 else 0
            }
        else:
            estatisticas = {
                'total_vendido_90d': 0,
                'faturamento_90d': 0,
                'dias_com_venda': 0,
                'dias_sem_venda': 90,
                'media_diaria': 0,
                'ticket_medio': 0
            }
        
        return jsonify({
            "success": True,
            "produto": {
                "id": produto.id,
                "nome": produto.nome,
            },
            "historico": historico_vendas,
            "estatisticas": estatisticas,
            "periodo": {
                "data_inicio": data_inicio.date().isoformat(),
                "data_fim": datetime.utcnow().date().isoformat(),
                "dias": 90
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter histórico de vendas do produto {id}: {str(e)}")
        return (
            jsonify({"success": False, "message": f"Erro interno ao obter histórico de vendas: {str(e)}"}),
            500,
        )


@produtos_bp.route("/calcular-preco-markup", methods=["POST"])
@funcionario_required
def calcular_preco_markup():
    """
    Calcula preço de venda baseado em markup sobre o custo.
    
    Útil para precificação rápida e padronizada.
    
    Body:
    {
        "preco_custo": 10.00,
        "markup_percentual": 50
    }
    
    Response:
    {
        "preco_custo": 10.00,
        "markup_percentual": 50,
        "preco_venda_sugerido": 15.00,
        "margem_lucro": 50.00
    }
    """
    try:
        data = request.get_json()
        
        preco_custo = data.get("preco_custo")
        markup_percentual = data.get("markup_percentual")
        
        if preco_custo is None or markup_percentual is None:
            return (
                jsonify({
                    "success": False,
                    "message": "Informe preco_custo e markup_percentual"
                }),
                400,
            )
        
        # Calcular preço de venda
        preco_venda = Produto.calcular_preco_por_markup(preco_custo, markup_percentual)
        
        # Calcular margem de lucro (para confirmação)
        margem = Produto.calcular_markup_de_preco(preco_custo, preco_venda)
        
        return jsonify({
            "success": True,
            "preco_custo": float(preco_custo),
            "markup_percentual": float(markup_percentual),
            "preco_venda_sugerido": float(preco_venda),
            "margem_lucro": float(margem),
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular preço por markup: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao calcular preço"}),
            500,
        )


@produtos_bp.route("/atualizar-abc", methods=["POST"])
@funcionario_required
def atualizar_classificacao_abc():
    """
    Atualiza classificações ABC de todos os produtos usando Princípio de Pareto (80/20).
    
    Esta é a metodologia correta para gestão de estoque, substituindo valores fixos arbitrários.
    
    Body (opcional):
    {
        "periodo_dias": 90  // Período de análise (padrão: 90 dias)
    }
    
    Response:
    {
        "success": true,
        "estatisticas": {
            "produtos_atualizados": 150,
            "classe_a": 30,  // 20% dos produtos, 80% do faturamento
            "classe_b": 45,  // 30% dos produtos, 15% do faturamento
            "classe_c": 75,  // 50% dos produtos, 5% do faturamento
            "sem_vendas": 20
        }
    }
    """
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        data = request.get_json() or {}
        periodo_dias = data.get("periodo_dias", 90)
        
        # Validar período
        if periodo_dias < 7 or periodo_dias > 365:
            return (
                jsonify({
                    "success": False,
                    "message": "Período deve estar entre 7 e 365 dias"
                }),
                400,
            )
        
        # Atualizar classificações
        estatisticas = Produto.atualizar_classificacoes_abc(
            estabelecimento_id, periodo_dias
        )
        
        current_app.logger.info(
            f"Classificação ABC atualizada para estabelecimento {estabelecimento_id}: "
            f"{estatisticas['produtos_atualizados']} produtos atualizados"
        )
        
        return jsonify({
            "success": True,
            "message": f"Classificação ABC atualizada com sucesso ({periodo_dias} dias)",
            "estatisticas": estatisticas,
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar classificação ABC: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao atualizar classificação ABC"}),
            500,
        )
