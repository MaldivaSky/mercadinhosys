from flask import Blueprint, request, jsonify
from app import db
from app.models import Produto
from datetime import datetime
import json

produtos_bp = Blueprint("produtos", __name__)


# Rota de busca (nova) - ESSENCIAL PARA O PDV
@produtos_bp.route("/search", methods=["GET"])
def search_products():
    """Buscar produtos por nome ou código de barras"""
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    # Busca por nome (case insensitive) ou código
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

    # Formatar resposta - ATENÇÃO: converter campos para inglês
    resultado = []
    for p in produtos:
        resultado.append(
            {
                "id": p.id,
                "name": p.nome,  # Convertendo 'nome' para 'name'
                "barcode": p.codigo_barras,  # Convertendo 'codigo_barras' para 'barcode'
                "price": float(p.preco_venda),  # Convertendo 'preco_venda' para 'price'
                "stock": (
                    p.quantidade
                ),  # Usar estoque_atual se existir, senão quantidade
                "isBulk": p.tipo == "granel" if hasattr(p, "tipo") else False,
                "unit": p.unidade_medida if hasattr(p, "unidade_medida") else "un",
            }
        )

    return jsonify(resultado)


# Rota de busca por código de barras (nova)
@produtos_bp.route("/barcode/<codigo>", methods=["GET"])
def get_by_barcode(codigo):
    """Buscar produto específico por código de barras"""
    produto = Produto.query.filter_by(codigo_barras=codigo).first()

    if not produto:
        return jsonify({"error": "Produto não encontrado"}), 404

    return jsonify(
        {
            "id": produto.id,
            "name": produto.nome,
            "barcode": produto.codigo_barras,
            "price": float(produto.preco_venda),
            "stock": (produto.quantidade),
            "isBulk": produto.tipo == "granel" if hasattr(produto, "tipo") else False,
            "unit": (
                produto.unidade_medida if hasattr(produto, "unidade_medida") else "un"
            ),
        }
    )


# Rota de cadastro rápido (nova) - PARA O PDV
@produtos_bp.route("/quick-add", methods=["POST"])
def quick_add():
    """Cadastro rápido de produto direto do PDV"""
    data = request.json

    # Log para debug
    print(f"📦 Dados recebidos no quick-add: {data}")

    # Validações básicas
    if not data.get("name"):
        return jsonify({"error": "Nome do produto é obrigatório"}), 400

    try:
        preco = float(data.get("price", 0))
        if preco <= 0:
            return jsonify({"error": "Preço deve ser maior que zero"}), 400
    except:
        return jsonify({"error": "Preço inválido"}), 400

    # Verificar se código de barras já existe
    if data.get("barcode"):
        existe = Produto.query.filter_by(codigo_barras=data["barcode"]).first()
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

    # Criar novo produto
    # ATENÇÃO: Mapear campos do frontend para o modelo do backend
    novo_produto = Produto(
        nome=data["name"],  # Frontend manda "name", backend espera "nome"
        codigo_barras=data.get("barcode", ""),
        preco_venda=preco,
        preco_custo=preco * 0.6,  # Exemplo: 40% de margem
        quantidade=int(
            data.get("stock", 0)
        ),  # Também preencher quantidade para compatibilidade  
        unidade_medida=data.get("unit", "un"),
        tipo="granel" if data.get("isBulk") else "unidade",
        categoria=data.get("category", "Geral"),
        descricao=data.get("description", ""),
        ativo=True,
    )

    try:
        db.session.add(novo_produto)
        db.session.commit()

        print(
            f"✅ Produto cadastrado: {novo_produto.nome} - R$ {novo_produto.preco_venda}"
        )

        return (
            jsonify(
                {
                    "id": novo_produto.id,
                    "name": novo_produto.nome,
                    "barcode": novo_produto.codigo_barras,
                    "price": float(novo_produto.preco_venda),
                    "stock": (
                        novo_produto.quantidade
                        
                    ),
                    "isBulk": (
                        novo_produto.tipo == "granel"
                        if hasattr(novo_produto, "tipo")
                        else False
                    ),
                    "unit": (
                        novo_produto.unidade_medida
                        if hasattr(novo_produto, "unidade_medida")
                        else "un"
                    ),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao salvar produto: {str(e)}")
        return jsonify({"error": f"Erro ao salvar produto: {str(e)}"}), 500


# ... O RESTO DO SEU CÓDIGO PERMANECE IGUAL ...
# (listar_produtos, obter_produto, criar_produto, etc.)
