from flask import Blueprint, request, jsonify
from app import db
from app.models import Fornecedor, Produto
from datetime import datetime

fornecedores_bp = Blueprint("fornecedores", __name__, url_prefix="/api/fornecedores")

# ==================== CRUD FORNECEDORES ====================


@fornecedores_bp.route("/", methods=["GET"])
def listar_fornecedores():
    """Listar todos os fornecedores"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        search = request.args.get("search", "").strip()
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"

        query = Fornecedor.query

        if search:
            query = query.filter(
                db.or_(
                    Fornecedor.nome.ilike(f"%{search}%"),
                    Fornecedor.cnpj.ilike(f"%{search}%"),
                    Fornecedor.contato_nome.ilike(f"%{search}%"),
                )
            )

        if apenas_ativos:
            query = query.filter(Fornecedor.ativo == True)

        query = query.order_by(Fornecedor.nome.asc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        fornecedores = pagination.items

        resultado = []
        for f in fornecedores:
            # Contar produtos ativos deste fornecedor
            total_produtos = Produto.query.filter_by(
                fornecedor_id=f.id, ativo=True
            ).count()

            resultado.append(
                {
                    "id": f.id,
                    "nome": f.nome,
                    "cnpj": f.cnpj,
                    "telefone": f.telefone,
                    "email": f.email,
                    "cidade": f.cidade,
                    "estado": f.estado,
                    "contato_nome": f.contato_nome,
                    "ativo": f.ativo,
                    "total_produtos": total_produtos,
                    "data_cadastro": (
                        f.data_cadastro.isoformat() if f.data_cadastro else None
                    ),
                    "data_atualizacao": (
                        f.data_atualizacao.isoformat() if f.data_atualizacao else None
                    ),
                }
            )

        return jsonify(
            {
                "fornecedores": resultado,
                "paginacao": {
                    "pagina_atual": pagination.page,
                    "total_paginas": pagination.pages,
                    "total_itens": pagination.total,
                    "itens_por_pagina": pagination.per_page,
                    "tem_proxima": pagination.has_next,
                    "tem_anterior": pagination.has_prev,
                },
            }
        )

    except Exception as e:
        print(f"Erro ao listar fornecedores: {str(e)}")
        return jsonify({"error": f"Erro ao listar fornecedores: {str(e)}"}), 500


@fornecedores_bp.route("/<int:id>", methods=["GET"])
def detalhes_fornecedor(id):
    """Obter detalhes de um fornecedor"""
    try:
        fornecedor = Fornecedor.query.get(id)

        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404

        # Listar produtos deste fornecedor
        produtos = Produto.query.filter_by(fornecedor_id=id, ativo=True).all()
        produtos_list = []

        for p in produtos:
            produtos_list.append(
                {
                    "id": p.id,
                    "nome": p.nome,
                    "preco_custo": float(p.preco_custo),
                    "preco_venda": float(p.preco_venda),
                    "quantidade": p.quantidade,
                }
            )

        fornecedor_dict = {
            "id": fornecedor.id,
            "nome": fornecedor.nome,
            "cnpj": fornecedor.cnpj,
            "telefone": fornecedor.telefone,
            "email": fornecedor.email,
            "cidade": fornecedor.cidade,
            "estado": fornecedor.estado,
            "contato_nome": fornecedor.contato_nome,
            "ativo": fornecedor.ativo,
            "data_cadastro": (
                fornecedor.data_cadastro.isoformat()
                if fornecedor.data_cadastro
                else None
            ),
            "data_atualizacao": (
                fornecedor.data_atualizacao.isoformat()
                if fornecedor.data_atualizacao
                else None
            ),
            "produtos": produtos_list,
            "total_produtos": len(produtos_list),
        }

        return jsonify(fornecedor_dict)

    except Exception as e:
        print(f"Erro ao obter fornecedor {id}: {str(e)}")
        return jsonify({"error": f"Erro ao obter fornecedor: {str(e)}"}), 404


@fornecedores_bp.route("/", methods=["POST"])
def criar_fornecedor():
    """Criar um novo fornecedor"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Validações
        if not data.get("nome"):
            return jsonify({"error": "Nome do fornecedor é obrigatório"}), 400

        # Verificar CNPJ único
        cnpj = data.get("cnpj")
        if cnpj:
            existente = Fornecedor.query.filter_by(cnpj=cnpj).first()
            if existente:
                return (
                    jsonify(
                        {
                            "error": "CNPJ já cadastrado",
                            "fornecedor_existente": {
                                "id": existente.id,
                                "nome": existente.nome,
                            },
                        }
                    ),
                    409,
                )

        novo_fornecedor = Fornecedor(
            nome=data["nome"],
            cnpj=cnpj or "",
            telefone=data.get("telefone", ""),
            email=data.get("email", ""),
            cidade=data.get("cidade", ""),
            estado=data.get("estado", ""),
            contato_nome=data.get("contato_nome", ""),
            ativo=data.get("ativo", True),
        )

        db.session.add(novo_fornecedor)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Fornecedor criado com sucesso",
                    "fornecedor": {
                        "id": novo_fornecedor.id,
                        "nome": novo_fornecedor.nome,
                        "cnpj": novo_fornecedor.cnpj,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar fornecedor: {str(e)}")
        return jsonify({"error": f"Erro ao criar fornecedor: {str(e)}"}), 500


@fornecedores_bp.route("/<int:id>", methods=["PUT"])
def atualizar_fornecedor(id):
    """Atualizar informações de um fornecedor"""
    try:
        fornecedor = Fornecedor.query.get(id)

        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Verificar CNPJ único (se estiver sendo alterado)
        if "cnpj" in data and data["cnpj"] != fornecedor.cnpj:
            existente = Fornecedor.query.filter_by(cnpj=data["cnpj"]).first()
            if existente and existente.id != id:
                return (
                    jsonify(
                        {
                            "error": "CNPJ já cadastrado em outro fornecedor",
                            "fornecedor_existente": {
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
            "cnpj",
            "telefone",
            "email",
            "cidade",
            "estado",
            "contato_nome",
            "ativo",
        ]

        for campo in campos_permitidos:
            if campo in data:
                setattr(fornecedor, campo, data[campo])

        fornecedor.data_atualizacao = datetime.utcnow()
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Fornecedor atualizado com sucesso",
                "fornecedor": {
                    "id": fornecedor.id,
                    "nome": fornecedor.nome,
                    "cnpj": fornecedor.cnpj,
                    "ativo": fornecedor.ativo,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar fornecedor {id}: {str(e)}")
        return jsonify({"error": f"Erro ao atualizar fornecedor: {str(e)}"}), 500


@fornecedores_bp.route("/<int:id>", methods=["DELETE"])
def excluir_fornecedor(id):
    """Excluir (desativar) um fornecedor"""
    try:
        fornecedor = Fornecedor.query.get(id)

        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404

        # Verificar se fornecedor tem produtos ativos
        produtos_ativos = Produto.query.filter_by(fornecedor_id=id, ativo=True).count()
        if produtos_ativos > 0:
            return (
                jsonify(
                    {
                        "error": "Não é possível excluir o fornecedor pois existem produtos ativos vinculados a ele",
                        "quantidade_produtos": produtos_ativos,
                    }
                ),
                400,
            )

        # Exclusão lógica
        fornecedor.ativo = False
        fornecedor.data_atualizacao = datetime.utcnow()

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Fornecedor desativado com sucesso",
                "fornecedor": {
                    "id": fornecedor.id,
                    "nome": fornecedor.nome,
                    "ativo": False,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir fornecedor {id}: {str(e)}")
        return jsonify({"error": f"Erro ao excluir fornecedor: {str(e)}"}), 500


@fornecedores_bp.route("/<int:id>/produtos", methods=["GET"])
def produtos_fornecedor(id):
    """Listar produtos de um fornecedor específico"""
    try:
        fornecedor = Fornecedor.query.get(id)

        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404

        produtos = Produto.query.filter_by(fornecedor_id=id, ativo=True).all()

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
                    "preco_custo": float(p.preco_custo),
                    "preco_venda": float(p.preco_venda),
                    "quantidade": p.quantidade,
                    "quantidade_minima": p.quantidade_minima,
                    "estoque_status": estoque_status,
                    "categoria": p.categoria,
                    "marca": p.marca,
                }
            )

        return jsonify(
            {
                "fornecedor": {"id": fornecedor.id, "nome": fornecedor.nome},
                "produtos": resultado,
                "total_produtos": len(resultado),
            }
        )

    except Exception as e:
        print(f"Erro ao listar produtos do fornecedor {id}: {str(e)}")
        return jsonify({"error": f"Erro ao listar produtos: {str(e)}"}), 500
