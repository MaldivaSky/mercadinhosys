from flask import Blueprint, request, jsonify
from app import db
from app.models import Produto
from datetime import datetime
import json

produtos_bp = Blueprint("produtos", __name__)


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
                "isBulk": p.tipo == "granel" if hasattr(p, "tipo") else False,
                "unit": p.unidade_medida if hasattr(p, "unidade_medida") else "un",
            }
        )

    return jsonify(resultado)


@produtos_bp.route("/barcode/<codigo>", methods=["GET"])
def get_by_barcode(codigo):
    """Buscar produto específico por código de barras - PARA PDV"""
    produto = Produto.query.filter_by(codigo_barras=codigo).first()

    if not produto:
        return jsonify({"error": "Produto não encontrado"}), 404

    return jsonify(
        {
            "id": produto.id,
            "name": produto.nome,
            "barcode": produto.codigo_barras,
            "price": float(produto.preco_venda),
            "stock": produto.quantidade,
            "isBulk": produto.tipo == "granel" if hasattr(produto, "tipo") else False,
            "unit": (
                produto.unidade_medida if hasattr(produto, "unidade_medida") else "un"
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
            print("Erro: Nenhum JSON recebido")
            return jsonify({"error": "Dados JSON inválidos ou vazios"}), 400

        print(f"Dados recebidos: {data}")

        nome = data.get("nome")
        if not nome:
            print("Erro: Campo 'nome' não fornecido")
            return jsonify({"error": "Campo 'nome' é obrigatório"}), 400

        preco_venda = data.get("preco_venda")
        if preco_venda is None:
            print("Erro: Campo 'preco_venda' não fornecido")
            return jsonify({"error": "Campo 'preco_venda' é obrigatório"}), 400

        try:
            preco_venda_float = float(preco_venda)
        except (ValueError, TypeError):
            print(f"Erro: 'preco_venda' não é número válido: {preco_venda}")
            return jsonify({"error": "Campo 'preco_venda' deve ser um número"}), 400

        if preco_venda_float <= 0:
            print(f"Erro: 'preco_venda' deve ser > 0: {preco_venda_float}")
            return jsonify({"error": "Preço de venda deve ser maior que zero"}), 400

        print(f"Validações passadas: nome='{nome}', preco={preco_venda_float}")

        novo_produto = Produto(
            nome=nome,
            preco_venda=preco_venda_float,
            preco_custo=float(data.get("preco_custo", 0)),
            quantidade=int(data.get("quantidade", 0)),
            codigo_barras=data.get("codigo_barras") or "",
            descricao=data.get("descricao") or "",
            margem_lucro=float(data.get("margem_lucro", 30.0)),
            quantidade_minima=int(data.get("quantidade_minima", 10)),
            marca=data.get("marca") or "Sem Marca",
            fabricante=data.get("fabricante") or "",
            tipo=data.get("tipo") or "unidade",
            unidade_medida=data.get("unidade_medida") or "un",
            categoria_id=data.get("categoria_id"),
            ativo=True,
        )

        print(f"Produto criado: {novo_produto.nome}")

        db.session.add(novo_produto)
        db.session.commit()

        print(f"Produto salvo! ID: {novo_produto.id}")

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
                    "preco_custo": float(novo_produto.preco_custo),
                    "margem_lucro": float(novo_produto.margem_lucro),
                    "success": True,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"ERRO EXCEÇÃO: {type(e).__name__}: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


# ==================== CRUD COMPLETO PARA ESTOQUE ====================


@produtos_bp.route("/estoque", methods=["GET"])
def listar_estoque():
    """Listar todos os produtos com paginação e filtros"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        search = request.args.get("search", "").strip()
        categoria_id = request.args.get("categoria_id", type=int)
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"

        query = Produto.query

        if search:
            query = query.filter(
                db.or_(
                    Produto.nome.ilike(f"%{search}%"),
                    Produto.codigo_barras.ilike(f"%{search}%"),
                    Produto.marca.ilike(f"%{search}%"),
                    Produto.descricao.ilike(f"%{search}%"),
                )
            )

        if categoria_id:
            query = query.filter(Produto.categoria_id == categoria_id)

        if apenas_ativos:
            query = query.filter(Produto.ativo == True)

        query = query.order_by(Produto.nome.asc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        produtos = pagination.items

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
                "codigo_barras": p.codigo_barras or "",
                "descricao": p.descricao or "",
                "preco_custo": float(p.preco_custo),
                "preco_venda": float(p.preco_venda),
                "margem_lucro": float(p.margem_lucro),
                "quantidade": p.quantidade,
                "quantidade_minima": p.quantidade_minima,
                "estoque_status": estoque_status,
                "marca": p.marca or "Sem Marca",
                "fabricante": p.fabricante or "",
                "tipo": p.tipo or "unidade",
                "unidade_medida": p.unidade_medida or "un",
                "ativo": p.ativo,
                "valor_estoque": float(p.preco_custo * p.quantidade),
                "valor_venda_estoque": float(p.preco_venda * p.quantidade),
            }

            if hasattr(p, "categoria_id") and p.categoria_id:
                produto_dict["categoria_id"] = p.categoria_id

            resultado.append(produto_dict)

        # Estatísticas totais
        total_produtos = query.count()
        total_valor_estoque = sum(p.preco_custo * p.quantidade for p in query.all())
        total_valor_venda = sum(p.preco_venda * p.quantidade for p in query.all())
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
                    "pagina_atual": pagination.page,
                    "total_paginas": pagination.pages,
                    "total_itens": pagination.total,
                    "itens_por_pagina": pagination.per_page,
                    "tem_proxima": pagination.has_next,
                    "tem_anterior": pagination.has_prev,
                },
                "estatisticas": {
                    "total_produtos": total_produtos,
                    "total_valor_estoque": float(total_valor_estoque),
                    "total_valor_venda": float(total_valor_venda),
                    "produtos_baixo_estoque": produtos_baixo_estoque,
                    "produtos_esgotados": produtos_esgotados,
                },
            }
        )

    except Exception as e:
        print(f"Erro ao listar estoque: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Erro ao listar produtos: {str(e)}"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["GET"])
def detalhes_produto(id):
    """Obter detalhes completos de um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        produto_dict = {
            "id": produto.id,
            "nome": produto.nome,
            "codigo_barras": produto.codigo_barras or "",
            "descricao": produto.descricao or "",
            "preco_custo": float(produto.preco_custo),
            "preco_venda": float(produto.preco_venda),
            "margem_lucro": float(produto.margem_lucro),
            "quantidade": produto.quantidade,
            "quantidade_minima": produto.quantidade_minima,
            "marca": produto.marca or "Sem Marca",
            "fabricante": produto.fabricante or "",
            "tipo": produto.tipo or "unidade",
            "unidade_medida": produto.unidade_medida or "un",
            "ativo": produto.ativo,
            "valor_estoque": float(produto.preco_custo * produto.quantidade),
            "valor_venda_estoque": float(produto.preco_venda * produto.quantidade),
        }

        if hasattr(produto, "categoria_id") and produto.categoria_id:
            produto_dict["categoria_id"] = produto.categoria_id

        return jsonify(produto_dict)

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

        # Validações obrigatórias
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
            preco_custo=float(data.get("preco_custo", 0)),
            preco_venda=preco_venda,
            margem_lucro=float(data.get("margem_lucro", 30.0)),
            quantidade=int(data.get("quantidade", 0)),
            quantidade_minima=int(data.get("quantidade_minima", 10)),
            marca=data.get("marca", "Sem Marca"),
            fabricante=data.get("fabricante", ""),
            tipo=data.get("tipo", "unidade"),
            unidade_medida=data.get("unidade_medida", "un"),
            categoria_id=data.get("categoria_id"),
            ativo=data.get("ativo", True),
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

        # Verificar código de barras único (se estiver sendo alterado)
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
            "preco_custo",
            "preco_venda",
            "margem_lucro",
            "quantidade",
            "quantidade_minima",
            "marca",
            "fabricante",
            "tipo",
            "unidade_medida",
            "categoria_id",
            "ativo",
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
    """Excluir (ou desativar) um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        # Verificar se produto tem vendas/histórico
        # (Aqui você pode adicionar lógica para verificar se pode excluir permanentemente)

        # Opção 1: Exclusão física (PERMANENTE)
        # db.session.delete(produto)

        # Opção 2: Exclusão lógica (RECOMENDADO)
        produto.ativo = False
        produto.quantidade = 0  # Zerar estoque

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
    """Ajustar estoque de um produto com motivo"""
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

        quantidade = int(data["quantidade"])
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
                    "operacao": operacao,
                    "quantidade_ajustada": quantidade,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao ajustar estoque do produto {id}: {str(e)}")
        return jsonify({"error": f"Erro ao ajustar estoque: {str(e)}"}), 500


@produtos_bp.route("/estoque/relatorio", methods=["GET"])
def relatorio_estoque():
    """Gerar relatório de estoque com filtros"""
    try:
        # Filtros
        categoria_id = request.args.get("categoria_id", type=int)
        apenas_baixo_estoque = (
            request.args.get("baixo_estoque", "false").lower() == "true"
        )
        apenas_esgotados = request.args.get("esgotados", "false").lower() == "true"

        query = Produto.query.filter_by(ativo=True)

        if categoria_id:
            query = query.filter(Produto.categoria_id == categoria_id)

        if apenas_baixo_estoque:
            query = query.filter(Produto.quantidade < Produto.quantidade_minima)

        if apenas_esgotados:
            query = query.filter(Produto.quantidade <= 0)

        produtos = query.order_by(Produto.nome.asc()).all()

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
                    "codigo_barras": p.codigo_barras or "",
                    "quantidade": p.quantidade,
                    "quantidade_minima": p.quantidade_minima,
                    "estoque_status": estoque_status,
                    "preco_custo": float(p.preco_custo),
                    "preco_venda": float(p.preco_venda),
                    "valor_estoque": float(p.preco_custo * p.quantidade),
                    "marca": p.marca or "Sem Marca",
                    "tipo": p.tipo or "unidade",
                    "unidade_medida": p.unidade_medida or "un",
                }
            )

        # Totais
        total_produtos = len(resultado)
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
                    "total_produtos": total_produtos,
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
