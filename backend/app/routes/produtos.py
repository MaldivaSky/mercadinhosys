from flask import Blueprint, request, jsonify
from app import db
from app.models import Produto, Fornecedor
from datetime import datetime

produtos_bp = Blueprint("produtos", __name__, url_prefix="/api/produtos")


# ==================== ROTAS PARA PDV ====================


@produtos_bp.route("/search", methods=["GET"])
def search_products():
    """Buscar produtos por nome ou código de barras - PARA PDV"""
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    produtos = (
        Produto.query.filter(
            db.or_(
                Produto.nome.ilike(f"%{query}%"),
                Produto.codigo_barras.ilike(f"%{query}%"),
            )
        )
        .filter_by(ativo=True)
        .limit(20)
        .all()
    )

    resultado = []
    for p in produtos:
        resultado.append(
            {
                "id": p.id,
                "name": p.nome,
                "barcode": p.codigo_barras,
                "price": float(p.preco_venda),
                "stock": p.quantidade,
                "isBulk": p.tipo == "granel",
                "unit": p.unidade_medida,
                "fornecedor_id": p.fornecedor_id,
                "fornecedor_nome": p.fornecedor_rel.nome if p.fornecedor_rel else None,
            }
        )

    return jsonify(resultado)


@produtos_bp.route("/barcode/<codigo>", methods=["GET"])
def get_by_barcode(codigo):
    """Buscar produto específico por código de barras - PARA PDV"""
    produto = Produto.query.filter_by(codigo_barras=codigo, ativo=True).first()

    if not produto:
        return jsonify({"error": "Produto não encontrado"}), 404

    return jsonify(
        {
            "id": produto.id,
            "name": produto.nome,
            "barcode": produto.codigo_barras,
            "price": float(produto.preco_venda),
            "stock": produto.quantidade,
            "isBulk": produto.tipo == "granel",
            "unit": produto.unidade_medida,
            "fornecedor_id": produto.fornecedor_id,
            "fornecedor_nome": (
                produto.fornecedor_rel.nome if produto.fornecedor_rel else None
            ),
        }
    )


@produtos_bp.route("/quick-add", methods=["POST"])
def quick_add():
    """Cadastro rápido de produto direto do PDV"""
    print("=== INÍCIO quick-add ===")

    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Dados JSON inválidos ou vazios"}), 400

        print(f"Dados recebidos: {data}")

        # Validações
        nome = data.get("nome")
        if not nome:
            return jsonify({"error": "Campo 'nome' é obrigatório"}), 400

        preco_venda = data.get("preco_venda")
        if preco_venda is None:
            return jsonify({"error": "Campo 'preco_venda' é obrigatório"}), 400

        try:
            preco_venda_float = float(preco_venda)
        except (ValueError, TypeError):
            return jsonify({"error": "Campo 'preco_venda' deve ser um número"}), 400

        if preco_venda_float <= 0:
            return jsonify({"error": "Preço de venda deve ser maior que zero"}), 400

        # Verificar código de barras único
        codigo_barras = data.get("codigo_barras")
        if codigo_barras:
            existe = Produto.query.filter_by(codigo_barras=codigo_barras).first()
            if existe:
                return (
                    jsonify(
                        {
                            "error": "Código de barras já existe",
                            "product": {
                                "id": existe.id,
                                "name": existe.nome,
                                "barcode": existe.codigo_barras,
                                "price": float(existe.preco_venda),
                            },
                        }
                    ),
                    409,
                )

        # Criar produto
        novo_produto = Produto(
            nome=nome,
            preco_venda=preco_venda_float,
            preco_custo=float(data.get("preco_custo", 0)),
            quantidade=float(data.get("quantidade", 0)),
            codigo_barras=codigo_barras or "",
            descricao=data.get("descricao", ""),
            margem_lucro=float(data.get("margem_lucro", 30.0)),
            quantidade_minima=float(data.get("quantidade_minima", 10)),
            marca=data.get("marca", "Sem Marca"),
            fabricante=data.get("fabricante", ""),
            tipo=data.get("tipo", "unidade"),
            unidade_medida=data.get("unidade_medida", "un"),
            fornecedor_id=data.get("fornecedor_id"),
            categoria=data.get("categoria", "Geral"),
            ativo=True,
        )

        db.session.add(novo_produto)
        db.session.commit()

        print(f"✅ Produto salvo! ID: {novo_produto.id}")

        return (
            jsonify(
                {
                    "id": novo_produto.id,
                    "name": novo_produto.nome,
                    "barcode": novo_produto.codigo_barras,
                    "price": float(novo_produto.preco_venda),
                    "stock": novo_produto.quantidade,
                    "isBulk": novo_produto.tipo == "granel",
                    "unit": novo_produto.unidade_medida,
                    "fornecedor_id": novo_produto.fornecedor_id,
                    "fornecedor_nome": (
                        novo_produto.fornecedor_rel.nome
                        if novo_produto.fornecedor_rel
                        else None
                    ),
                    "success": True,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"ERRO: {str(e)}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


# ==================== CRUD COMPLETO PARA ESTOQUE ====================


@produtos_bp.route("/estoque", methods=["GET"])
def listar_estoque():
    """Listar todos os produtos com paginação e filtros"""
    try:
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 50, type=int)
        busca = request.args.get("busca", "").strip()
        categoria = request.args.get("categoria")
        fornecedor_id = request.args.get("fornecedor_id", type=int)
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"

        query = Produto.query

        if busca:
            query = query.filter(
                db.or_(
                    Produto.nome.ilike(f"%{busca}%"),
                    Produto.codigo_barras.ilike(f"%{busca}%"),
                    Produto.marca.ilike(f"%{busca}%"),
                    Produto.descricao.ilike(f"%{busca}%"),
                )
            )

        if categoria:
            query = query.filter(Produto.categoria == categoria)

        if fornecedor_id:
            query = query.filter(Produto.fornecedor_id == fornecedor_id)

        if apenas_ativos:
            query = query.filter(Produto.ativo == True)

        query = query.order_by(Produto.nome.asc())

        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        produtos = paginacao.items

        resultado = []
        for p in produtos:
            estoque_status = "normal"
            if p.quantidade <= 0:
                estoque_status = "esgotado"
            elif p.quantidade < p.quantidade_minima:
                estoque_status = "baixo"

            produto_dict = {
                "id": p.id,
                "nome": p.nome,
                "codigo_barras": p.codigo_barras,
                "descricao": p.descricao,
                "fornecedor_id": p.fornecedor_id,
                "fornecedor_nome": p.fornecedor_rel.nome if p.fornecedor_rel else None,
                "preco_custo": float(p.preco_custo),
                "preco_venda": float(p.preco_venda),
                "margem_lucro": float(p.margem_lucro),
                "quantidade": p.quantidade,
                "quantidade_minima": p.quantidade_minima,
                "estoque_status": estoque_status,
                "categoria": p.categoria,
                "marca": p.marca,
                "tipo": p.tipo,
                "unidade_medida": p.unidade_medida,
                "ativo": p.ativo,
                "controla_estoque": p.controla_estoque,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }

            resultado.append(produto_dict)

        # Estatísticas
        total_produtos = query.count()
        produtos_baixo_estoque = sum(
            1
            for p in query.all()
            if p.quantidade < p.quantidade_minima and p.quantidade > 0
        )
        produtos_esgotados = sum(1 for p in query.all() if p.quantidade <= 0)

        return jsonify(
            {
                "produtos": resultado,
                "paginacao": {
                    "pagina_atual": paginacao.page,
                    "total_paginas": paginacao.pages,
                    "total_itens": paginacao.total,
                    "itens_por_pagina": paginacao.per_page,
                    "tem_proxima": paginacao.has_next,
                    "tem_anterior": paginacao.has_prev,
                },
                "estatisticas": {
                    "total_produtos": total_produtos,
                    "produtos_baixo_estoque": produtos_baixo_estoque,
                    "produtos_esgotados": produtos_esgotados,
                },
            }
        )

    except Exception as e:
        print(f"Erro ao listar estoque: {str(e)}")
        return jsonify({"error": f"Erro ao listar produtos: {str(e)}"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["GET"])
def detalhes_produto(id):
    """Obter detalhes completos de um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        estoque_status = "normal"
        if produto.quantidade <= 0:
            estoque_status = "esgotado"
        elif produto.quantidade < produto.quantidade_minima:
            estoque_status = "baixo"

        return jsonify(
            {
                "id": produto.id,
                "nome": produto.nome,
                "codigo_barras": produto.codigo_barras,
                "descricao": produto.descricao,
                "fornecedor_id": produto.fornecedor_id,
                "fornecedor_nome": (
                    produto.fornecedor_rel.nome if produto.fornecedor_rel else None
                ),
                "preco_custo": float(produto.preco_custo),
                "preco_venda": float(produto.preco_venda),
                "margem_lucro": float(produto.margem_lucro),
                "quantidade": produto.quantidade,
                "quantidade_minima": produto.quantidade_minima,
                "estoque_status": estoque_status,
                "categoria": produto.categoria,
                "marca": produto.marca,
                "tipo": produto.tipo,
                "unidade_medida": produto.unidade_medida,
                "ativo": produto.ativo,
                "controla_estoque": produto.controla_estoque,
                "created_at": (
                    produto.created_at.isoformat() if produto.created_at else None
                ),
                "updated_at": (
                    produto.updated_at.isoformat() if produto.updated_at else None
                ),
            }
        )

    except Exception as e:
        print(f"Erro ao obter detalhes do produto {id}: {str(e)}")
        return jsonify({"error": f"Erro ao obter produto: {str(e)}"}), 404


@produtos_bp.route("/estoque", methods=["POST"])
def criar_produto():
    """Criar um novo produto (cadastro completo)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Validações
        if not data.get("nome"):
            return jsonify({"error": "Nome do produto é obrigatório"}), 400

        try:
            preco_venda = float(data.get("preco_venda", 0))
            if preco_venda <= 0:
                return jsonify({"error": "Preço de venda deve ser maior que zero"}), 400
        except:
            return jsonify({"error": "Preço de venda inválido"}), 400

        # Verificar código de barras único
        codigo_barras = data.get("codigo_barras")
        if codigo_barras:
            existente = Produto.query.filter_by(codigo_barras=codigo_barras).first()
            if existente:
                return (
                    jsonify(
                        {
                            "error": "Código de barras já cadastrado",
                            "produto_existente": {
                                "id": existente.id,
                                "nome": existente.nome,
                            },
                        }
                    ),
                    409,
                )

        # Criar produto
        novo_produto = Produto(
            nome=data["nome"],
            codigo_barras=codigo_barras or "",
            descricao=data.get("descricao", ""),
            fornecedor_id=data.get("fornecedor_id"),
            preco_custo=float(data.get("preco_custo", 0)),
            preco_venda=preco_venda,
            margem_lucro=float(data.get("margem_lucro", 30.0)),
            quantidade=float(data.get("quantidade", 0)),
            quantidade_minima=float(data.get("quantidade_minima", 10)),
            categoria=data.get("categoria", "Geral"),
            marca=data.get("marca", "Sem Marca"),
            tipo=data.get("tipo", "unidade"),
            unidade_medida=data.get("unidade_medida", "un"),
            ativo=data.get("ativo", True),
            controla_estoque=data.get("controla_estoque", True),
        )

        db.session.add(novo_produto)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Produto criado com sucesso",
                    "produto": {
                        "id": novo_produto.id,
                        "nome": novo_produto.nome,
                        "codigo_barras": novo_produto.codigo_barras,
                        "fornecedor_id": novo_produto.fornecedor_id,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar produto: {str(e)}")
        return jsonify({"error": f"Erro ao criar produto: {str(e)}"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["PUT"])
def atualizar_produto(id):
    """Atualizar informações de um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Validações
        if "preco_venda" in data:
            try:
                preco_venda = float(data["preco_venda"])
                if preco_venda <= 0:
                    return (
                        jsonify({"error": "Preço de venda deve ser maior que zero"}),
                        400,
                    )
            except:
                return jsonify({"error": "Preço de venda inválido"}), 400

        # Verificar código de barras único
        if "codigo_barras" in data and data["codigo_barras"] != produto.codigo_barras:
            existente = Produto.query.filter_by(
                codigo_barras=data["codigo_barras"]
            ).first()
            if existente and existente.id != id:
                return (
                    jsonify(
                        {
                            "error": "Código de barras já cadastrado em outro produto",
                            "produto_existente": {
                                "id": existente.id,
                                "nome": existente.nome,
                            },
                        }
                    ),
                    409,
                )

        # Atualizar campos
        campos_permitidos = [
            "nome",
            "codigo_barras",
            "descricao",
            "fornecedor_id",
            "preco_custo",
            "preco_venda",
            "margem_lucro",
            "quantidade",
            "quantidade_minima",
            "categoria",
            "marca",
            "tipo",
            "unidade_medida",
            "ativo",
            "controla_estoque",
        ]

        for campo in campos_permitidos:
            if campo in data:
                setattr(produto, campo, data[campo])

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Produto atualizado com sucesso",
                "produto": {
                    "id": produto.id,
                    "nome": produto.nome,
                    "quantidade": produto.quantidade,
                    "preco_venda": float(produto.preco_venda),
                    "ativo": produto.ativo,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar produto {id}: {str(e)}")
        return jsonify({"error": f"Erro ao atualizar produto: {str(e)}"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["DELETE"])
def excluir_produto(id):
    """Excluir (desativar) um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        # Exclusão lógica
        produto.ativo = False
        produto.quantidade = 0

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Produto desativado com sucesso",
                "produto": {"id": produto.id, "nome": produto.nome, "ativo": False},
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir produto {id}: {str(e)}")
        return jsonify({"error": f"Erro ao excluir produto: {str(e)}"}), 500


@produtos_bp.route("/estoque/<int:id>/estoque", methods=["PUT"])
def ajustar_estoque(id):
    """Ajustar estoque de um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        data = request.get_json()

        if not data or "quantidade" not in data or "operacao" not in data:
            return (
                jsonify(
                    {"error": "Dados inválidos. Forneça 'quantidade' e 'operacao'"}
                ),
                400,
            )

        quantidade = float(data["quantidade"])
        operacao = data["operacao"]
        motivo = data.get("motivo", "")

        if quantidade <= 0:
            return jsonify({"error": "Quantidade deve ser maior que zero"}), 400

        if operacao == "entrada":
            produto.quantidade += quantidade
            movimento = "Entrada"
        elif operacao == "saida":
            if produto.quantidade < quantidade:
                return (
                    jsonify(
                        {
                            "error": "Estoque insuficiente",
                            "estoque_atual": produto.quantidade,
                            "quantidade_solicitada": quantidade,
                        }
                    ),
                    400,
                )
            produto.quantidade -= quantidade
            movimento = "Saída"
        else:
            return (
                jsonify({"error": "Operação inválida. Use 'entrada' ou 'saida'"}),
                400,
            )

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"Estoque ajustado: {movimento} de {quantidade} unidades",
                "motivo": motivo,
                "produto": {
                    "id": produto.id,
                    "nome": produto.nome,
                    "quantidade_anterior": produto.quantidade
                    - (quantidade if operacao == "entrada" else -quantidade),
                    "quantidade_atual": produto.quantidade,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao ajustar estoque do produto {id}: {str(e)}")
        return jsonify({"error": f"Erro ao ajustar estoque: {str(e)}"}), 500


@produtos_bp.route("/categorias", methods=["GET"])
def listar_categorias():
    """Listar todas as categorias de produtos"""
    try:
        produtos = Produto.query.filter_by(ativo=True).all()
        categorias = set()

        for p in produtos:
            if p.categoria:
                categorias.add(p.categoria)

        return jsonify(
            {
                "categorias": sorted(list(categorias)),
                "total_categorias": len(categorias),
            }
        )

    except Exception as e:
        print(f"Erro ao listar categorias: {str(e)}")
        return jsonify({"error": f"Erro ao listar categorias: {str(e)}"}), 500


@produtos_bp.route("/relatorio/estoque", methods=["GET"])
def relatorio_estoque():
    """Gerar relatório de estoque"""
    try:
        produtos = (
            Produto.query.filter_by(ativo=True).order_by(Produto.nome.asc()).all()
        )

        resultado = []
        for p in produtos:
            estoque_status = "normal"
            if p.quantidade <= 0:
                estoque_status = "esgotado"
            elif p.quantidade < p.quantidade_minima:
                estoque_status = "baixo"

            resultado.append(
                {
                    "id": p.id,
                    "nome": p.nome,
                    "codigo_barras": p.codigo_barras,
                    "quantidade": p.quantidade,
                    "quantidade_minima": p.quantidade_minima,
                    "estoque_status": estoque_status,
                    "preco_custo": float(p.preco_custo),
                    "preco_venda": float(p.preco_venda),
                    "valor_estoque": float(p.preco_custo * p.quantidade),
                    "marca": p.marca,
                    "categoria": p.categoria,
                    "fornecedor_nome": (
                        p.fornecedor_rel.nome if p.fornecedor_rel else None
                    ),
                }
            )

        # Totais
        total_valor_estoque = sum(p["valor_estoque"] for p in resultado)
        produtos_baixo_estoque = sum(
            1 for p in resultado if p["estoque_status"] == "baixo"
        )
        produtos_esgotados = sum(
            1 for p in resultado if p["estoque_status"] == "esgotado"
        )

        return jsonify(
            {
                "produtos": resultado,
                "totais": {
                    "total_produtos": len(resultado),
                    "total_valor_estoque": float(total_valor_estoque),
                    "produtos_baixo_estoque": produtos_baixo_estoque,
                    "produtos_esgotados": produtos_esgotados,
                    "data_geracao": datetime.now().isoformat(),
                },
            }
        )

    except Exception as e:
        print(f"Erro ao gerar relatório: {str(e)}")
        return jsonify({"error": f"Erro ao gerar relatório: {str(e)}"}), 500
