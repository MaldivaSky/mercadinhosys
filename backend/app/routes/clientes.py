from flask import Blueprint, request, jsonify
from app import db
from app.models import Cliente, Venda
from datetime import datetime

clientes_bp = Blueprint("clientes", __name__, url_prefix="/api/clientes")

# ==================== CRUD CLIENTES ====================


@clientes_bp.route("/", methods=["GET"])
def listar_clientes():
    """Listar todos os clientes"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        search = request.args.get("search", "").strip()
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"

        query = Cliente.query

        if search:
            query = query.filter(
                db.or_(
                    Cliente.nome.ilike(f"%{search}%"),
                    Cliente.cpf.ilike(f"%{search}%"),
                    Cliente.email.ilike(f"%{search}%"),
                )
            )

        if apenas_ativos:
            query = query.filter(Cliente.ativo == True)

        query = query.order_by(Cliente.nome.asc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        clientes = pagination.items

        resultado = []
        for c in clientes:
            # Calcular total de compras e valor gasto
            total_compras = Venda.query.filter_by(cliente_id=c.id).count()
            total_gasto = (
                db.session.query(db.func.sum(Venda.total))
                .filter_by(cliente_id=c.id)
                .scalar()
                or 0
            )

            resultado.append(
                {
                    "id": c.id,
                    "nome": c.nome,
                    "cpf": c.cpf,
                    "telefone": c.telefone,
                    "email": c.email,
                    "limite_credito": c.limite_credito,
                    "ativo": c.ativo,
                    "total_compras": total_compras,
                    "total_gasto": float(total_gasto),
                    "data_cadastro": (
                        c.data_cadastro.isoformat() if c.data_cadastro else None
                    ),
                    "data_atualizacao": (
                        c.data_atualizacao.isoformat() if c.data_atualizacao else None
                    ),
                }
            )

        return jsonify(
            {
                "clientes": resultado,
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
        print(f"Erro ao listar clientes: {str(e)}")
        return jsonify({"error": f"Erro ao listar clientes: {str(e)}"}), 500


@clientes_bp.route("/<int:id>", methods=["GET"])
def detalhes_cliente(id):
    """Obter detalhes de um cliente"""
    try:
        cliente = Cliente.query.get(id)

        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        # Buscar compras do cliente
        compras = (
            Venda.query.filter_by(cliente_id=id)
            .order_by(Venda.created_at.desc())
            .limit(10)
            .all()
        )
        compras_list = []

        for v in compras:
            compras_list.append(
                {
                    "id": v.id,
                    "codigo": v.codigo,
                    "total": float(v.total),
                    "forma_pagamento": v.forma_pagamento,
                    "data": v.created_at.isoformat() if v.created_at else None,
                }
            )

        # Estatísticas
        total_compras = Venda.query.filter_by(cliente_id=id).count()
        total_gasto = (
            db.session.query(db.func.sum(Venda.total)).filter_by(cliente_id=id).scalar()
            or 0
        )
        ultima_compra = (
            Venda.query.filter_by(cliente_id=id)
            .order_by(Venda.created_at.desc())
            .first()
        )

        cliente_dict = {
            "id": cliente.id,
            "nome": cliente.nome,
            "cpf": cliente.cpf,
            "rg": cliente.rg,
            "data_nascimento": (
                cliente.data_nascimento.isoformat() if cliente.data_nascimento else None
            ),
            "telefone": cliente.telefone,
            "celular": cliente.celular,
            "email": cliente.email,
            "endereco": cliente.endereco,
            "limite_credito": cliente.limite_credito,
            "dia_vencimento": cliente.dia_vencimento,
            "observacoes": cliente.observacoes,
            "ativo": cliente.ativo,
            "data_cadastro": (
                cliente.data_cadastro.isoformat() if cliente.data_cadastro else None
            ),
            "data_atualizacao": (
                cliente.data_atualizacao.isoformat()
                if cliente.data_atualizacao
                else None
            ),
            "compras_recentes": compras_list,
            "estatisticas": {
                "total_compras": total_compras,
                "total_gasto": float(total_gasto),
                "ultima_compra": (
                    ultima_compra.created_at.isoformat() if ultima_compra else None
                ),
            },
        }

        return jsonify(cliente_dict)

    except Exception as e:
        print(f"Erro ao obter cliente {id}: {str(e)}")
        return jsonify({"error": f"Erro ao obter cliente: {str(e)}"}), 404


@clientes_bp.route("/", methods=["POST"])
def criar_cliente():
    """Criar um novo cliente"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Validações
        if not data.get("nome"):
            return jsonify({"error": "Nome do cliente é obrigatório"}), 400

        # Verificar CPF único (se fornecido)
        cpf = data.get("cpf")
        if cpf:
            existente = Cliente.query.filter_by(cpf=cpf).first()
            if existente:
                return (
                    jsonify(
                        {
                            "error": "CPF já cadastrado",
                            "cliente_existente": {
                                "id": existente.id,
                                "nome": existente.nome,
                            },
                        }
                    ),
                    409,
                )

        novo_cliente = Cliente(
            nome=data["nome"],
            cpf=cpf or "",
            rg=data.get("rg", ""),
            data_nascimento=(
                datetime.strptime(data["data_nascimento"], "%Y-%m-%d").date()
                if data.get("data_nascimento")
                else None
            ),
            telefone=data.get("telefone", ""),
            celular=data.get("celular", ""),
            email=data.get("email", ""),
            endereco=data.get("endereco", ""),
            limite_credito=float(data.get("limite_credito", 0)),
            dia_vencimento=int(data.get("dia_vencimento", 10)),
            observacoes=data.get("observacoes", ""),
            ativo=data.get("ativo", True),
        )

        db.session.add(novo_cliente)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Cliente criado com sucesso",
                    "cliente": {
                        "id": novo_cliente.id,
                        "nome": novo_cliente.nome,
                        "cpf": novo_cliente.cpf,
                        "email": novo_cliente.email,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar cliente: {str(e)}")
        return jsonify({"error": f"Erro ao criar cliente: {str(e)}"}), 500


@clientes_bp.route("/<int:id>", methods=["PUT"])
def atualizar_cliente(id):
    """Atualizar informações de um cliente"""
    try:
        cliente = Cliente.query.get(id)

        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Verificar CPF único (se estiver sendo alterado)
        if "cpf" in data and data["cpf"] != cliente.cpf:
            existente = Cliente.query.filter_by(cpf=data["cpf"]).first()
            if existente and existente.id != id:
                return (
                    jsonify(
                        {
                            "error": "CPF já cadastrado em outro cliente",
                            "cliente_existente": {
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
            "cpf",
            "rg",
            "data_nascimento",
            "telefone",
            "celular",
            "email",
            "endereco",
            "limite_credito",
            "dia_vencimento",
            "observacoes",
            "ativo",
        ]

        for campo in campos_permitidos:
            if campo in data:
                if campo == "data_nascimento" and data[campo]:
                    setattr(
                        cliente,
                        campo,
                        datetime.strptime(data[campo], "%Y-%m-%d").date(),
                    )
                elif campo in ["limite_credito"]:
                    setattr(cliente, campo, float(data[campo]))
                elif campo == "dia_vencimento":
                    setattr(cliente, campo, int(data[campo]))
                else:
                    setattr(cliente, campo, data[campo])

        cliente.data_atualizacao = datetime.utcnow()
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Cliente atualizado com sucesso",
                "cliente": {
                    "id": cliente.id,
                    "nome": cliente.nome,
                    "cpf": cliente.cpf,
                    "ativo": cliente.ativo,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar cliente {id}: {str(e)}")
        return jsonify({"error": f"Erro ao atualizar cliente: {str(e)}"}), 500


@clientes_bp.route("/<int:id>", methods=["DELETE"])
def excluir_cliente(id):
    """Excluir (desativar) um cliente"""
    try:
        cliente = Cliente.query.get(id)

        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        # Verificar se cliente tem compras
        total_compras = Venda.query.filter_by(cliente_id=id).count()
        if total_compras > 0:
            return (
                jsonify(
                    {
                        "error": "Não é possível excluir o cliente pois existem compras vinculadas a ele",
                        "quantidade_compras": total_compras,
                    }
                ),
                400,
            )

        # Exclusão lógica
        cliente.ativo = False
        cliente.data_atualizacao = datetime.utcnow()

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Cliente desativado com sucesso",
                "cliente": {"id": cliente.id, "nome": cliente.nome, "ativo": False},
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir cliente {id}: {str(e)}")
        return jsonify({"error": f"Erro ao excluir cliente: {str(e)}"}), 500


@clientes_bp.route("/<int:id>/compras", methods=["GET"])
def compras_cliente(id):
    """Listar compras de um cliente específico"""
    try:
        cliente = Cliente.query.get(id)

        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        query = Venda.query.filter_by(cliente_id=id).order_by(Venda.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        compras = pagination.items

        resultado = []
        for v in compras:
            resultado.append(
                {
                    "id": v.id,
                    "codigo": v.codigo,
                    "total": float(v.total),
                    "forma_pagamento": v.forma_pagamento,
                    "status": v.status,
                    "data": v.created_at.isoformat() if v.created_at else None,
                    "itens_count": len(v.itens) if v.itens else 0,
                }
            )

        # Estatísticas
        total_gasto = (
            db.session.query(db.func.sum(Venda.total)).filter_by(cliente_id=id).scalar()
            or 0
        )
        media_compra = total_gasto / len(compras) if compras else 0

        return jsonify(
            {
                "cliente": {"id": cliente.id, "nome": cliente.nome},
                "compras": resultado,
                "paginacao": {
                    "pagina_atual": pagination.page,
                    "total_paginas": pagination.pages,
                    "total_itens": pagination.total,
                    "itens_por_pagina": pagination.per_page,
                },
                "estatisticas": {
                    "total_compras": len(compras),
                    "total_gasto": float(total_gasto),
                    "media_compra": float(media_compra),
                },
            }
        )

    except Exception as e:
        print(f"Erro ao listar compras do cliente {id}: {str(e)}")
        return jsonify({"error": f"Erro ao listar compras: {str(e)}"}), 500


@clientes_bp.route("/buscar", methods=["GET"])
def buscar_cliente():
    """Buscar cliente por CPF ou nome"""
    try:
        query = request.args.get("q", "").strip()

        if not query:
            return jsonify([])

        clientes = (
            Cliente.query.filter(
                db.or_(
                    Cliente.nome.ilike(f"%{query}%"), Cliente.cpf.ilike(f"%{query}%")
                )
            )
            .filter_by(ativo=True)
            .limit(10)
            .all()
        )

        resultado = []
        for c in clientes:
            resultado.append(
                {
                    "id": c.id,
                    "nome": c.nome,
                    "cpf": c.cpf,
                    "telefone": c.telefone,
                    "email": c.email,
                    "limite_credito": c.limite_credito,
                }
            )

        return jsonify(resultado)

    except Exception as e:
        print(f"Erro ao buscar clientes: {str(e)}")
        return jsonify({"error": f"Erro ao buscar clientes: {str(e)}"}), 500
