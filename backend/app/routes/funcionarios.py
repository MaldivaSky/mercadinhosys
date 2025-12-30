from flask import Blueprint, request, jsonify
from app import db
from app.models import Funcionario, Venda
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

funcionarios_bp = Blueprint("funcionarios", __name__, url_prefix="/api/funcionarios")

# ==================== CRUD FUNCIONÁRIOS ====================


@funcionarios_bp.route("/", methods=["GET"])
def listar_funcionarios():
    """Listar todos os funcionários"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        search = request.args.get("search", "").strip()
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"

        query = Funcionario.query

        if search:
            query = query.filter(
                db.or_(
                    Funcionario.nome.ilike(f"%{search}%"),
                    Funcionario.cpf.ilike(f"%{search}%"),
                    Funcionario.usuario.ilike(f"%{search}%"),
                )
            )

        if apenas_ativos:
            query = query.filter(Funcionario.ativo == True)

        query = query.order_by(Funcionario.nome.asc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        funcionarios = pagination.items

        resultado = []
        for f in funcionarios:
            # Não incluir a senha_hash na resposta
            funcionario_dict = {
                "id": f.id,
                "nome": f.nome,
                "cpf": f.cpf,
                "telefone": f.telefone,
                "email": f.email,
                "cargo": f.cargo,
                "salario": f.salario,
                "data_admissao": (
                    f.data_admissao.isoformat() if f.data_admissao else None
                ),
                "data_demissao": (
                    f.data_demissao.isoformat() if f.data_demissao else None
                ),
                "usuario": f.usuario,
                "nivel_acesso": f.nivel_acesso,
                "ativo": f.ativo,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }

            resultado.append(funcionario_dict)

        return jsonify(
            {
                "funcionarios": resultado,
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
        print(f"Erro ao listar funcionários: {str(e)}")
        return jsonify({"error": f"Erro ao listar funcionários: {str(e)}"}), 500


@funcionarios_bp.route("/<int:id>", methods=["GET"])
def detalhes_funcionario(id):
    """Obter detalhes de um funcionário"""
    try:
        funcionario = Funcionario.query.get(id)

        if not funcionario:
            return jsonify({"error": "Funcionário não encontrado"}), 404

        # Estatísticas do funcionário
        total_vendas = Venda.query.filter_by(funcionario_id=id).count()
        vendas_30_dias = Venda.query.filter(
            Venda.funcionario_id == id,
            Venda.created_at >= (datetime.utcnow() - datetime.timedelta(days=30)),
        ).count()

        funcionario_dict = {
            "id": funcionario.id,
            "nome": funcionario.nome,
            "cpf": funcionario.cpf,
            "rg": funcionario.rg,
            "data_nascimento": (
                funcionario.data_nascimento.isoformat()
                if funcionario.data_nascimento
                else None
            ),
            "telefone": funcionario.telefone,
            "celular": funcionario.celular,
            "email": funcionario.email,
            "endereco": funcionario.endereco,
            "cargo": funcionario.cargo,
            "salario": funcionario.salario,
            "data_admissao": (
                funcionario.data_admissao.isoformat()
                if funcionario.data_admissao
                else None
            ),
            "data_demissao": (
                funcionario.data_demissao.isoformat()
                if funcionario.data_demissao
                else None
            ),
            "usuario": funcionario.usuario,
            "nivel_acesso": funcionario.nivel_acesso,
            "ativo": funcionario.ativo,
            "created_at": (
                funcionario.created_at.isoformat() if funcionario.created_at else None
            ),
            "updated_at": (
                funcionario.updated_at.isoformat() if funcionario.updated_at else None
            ),
            "estatisticas": {
                "total_vendas": total_vendas,
                "vendas_30_dias": vendas_30_dias,
            },
        }

        return jsonify(funcionario_dict)

    except Exception as e:
        print(f"Erro ao obter funcionário {id}: {str(e)}")
        return jsonify({"error": f"Erro ao obter funcionário: {str(e)}"}), 404


@funcionarios_bp.route("/", methods=["POST"])
def criar_funcionario():
    """Criar um novo funcionário"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Validações obrigatórias
        if not data.get("nome"):
            return jsonify({"error": "Nome do funcionário é obrigatório"}), 400

        if not data.get("cpf"):
            return jsonify({"error": "CPF do funcionário é obrigatório"}), 400

        if not data.get("usuario"):
            return jsonify({"error": "Usuário é obrigatório"}), 400

        if not data.get("senha"):
            return jsonify({"error": "Senha é obrigatória"}), 400

        # Verificar CPF único
        cpf = data.get("cpf")
        existente_cpf = Funcionario.query.filter_by(cpf=cpf).first()
        if existente_cpf:
            return (
                jsonify(
                    {
                        "error": "CPF já cadastrado",
                        "funcionario_existente": {
                            "id": existente_cpf.id,
                            "nome": existente_cpf.nome,
                        },
                    }
                ),
                409,
            )

        # Verificar usuário único
        usuario = data.get("usuario")
        existente_usuario = Funcionario.query.filter_by(usuario=usuario).first()
        if existente_usuario:
            return (
                jsonify(
                    {
                        "error": "Usuário já cadastrado",
                        "funcionario_existente": {
                            "id": existente_usuario.id,
                            "nome": existente_usuario.nome,
                        },
                    }
                ),
                409,
            )

        # Criar funcionário
        novo_funcionario = Funcionario(
            nome=data["nome"],
            cpf=cpf,
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
            cargo=data.get("cargo", "Atendente"),
            salario=float(data.get("salario", 0)),
            data_admissao=(
                datetime.strptime(data["data_admissao"], "%Y-%m-%d").date()
                if data.get("data_admissao")
                else date.today()
            ),
            data_demissao=(
                datetime.strptime(data["data_demissao"], "%Y-%m-%d").date()
                if data.get("data_demissao")
                else None
            ),
            usuario=usuario,
            nivel_acesso=data.get("nivel_acesso", "atendente"),
            ativo=data.get("ativo", True),
        )

        # Definir senha
        novo_funcionario.set_senha(data["senha"])

        # Definir PIN se fornecido
        if data.get("pin"):
            novo_funcionario.set_pin(data["pin"])

        db.session.add(novo_funcionario)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Funcionário criado com sucesso",
                    "funcionario": {
                        "id": novo_funcionario.id,
                        "nome": novo_funcionario.nome,
                        "usuario": novo_funcionario.usuario,
                        "cargo": novo_funcionario.cargo,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar funcionário: {str(e)}")
        return jsonify({"error": f"Erro ao criar funcionário: {str(e)}"}), 500


@funcionarios_bp.route("/<int:id>", methods=["PUT"])
def atualizar_funcionario(id):
    """Atualizar informações de um funcionário"""
    try:
        funcionario = Funcionario.query.get(id)

        if not funcionario:
            return jsonify({"error": "Funcionário não encontrado"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Verificar CPF único (se estiver sendo alterado)
        if "cpf" in data and data["cpf"] != funcionario.cpf:
            existente = Funcionario.query.filter_by(cpf=data["cpf"]).first()
            if existente and existente.id != id:
                return (
                    jsonify(
                        {
                            "error": "CPF já cadastrado em outro funcionário",
                            "funcionario_existente": {
                                "id": existente.id,
                                "nome": existente.nome,
                            },
                        }
                    ),
                    409,
                )

        # Verificar usuário único (se estiver sendo alterado)
        if "usuario" in data and data["usuario"] != funcionario.usuario:
            existente = Funcionario.query.filter_by(usuario=data["usuario"]).first()
            if existente and existente.id != id:
                return (
                    jsonify(
                        {
                            "error": "Usuário já cadastrado em outro funcionário",
                            "funcionario_existente": {
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
            "cargo",
            "salario",
            "data_admissao",
            "data_demissao",
            "usuario",
            "nivel_acesso",
            "ativo",
        ]

        for campo in campos_permitidos:
            if campo in data:
                if (
                    campo in ["data_nascimento", "data_admissao", "data_demissao"]
                    and data[campo]
                ):
                    setattr(
                        funcionario,
                        campo,
                        datetime.strptime(data[campo], "%Y-%m-%d").date(),
                    )
                else:
                    setattr(funcionario, campo, data[campo])

        # Atualizar senha se fornecida
        if "senha" in data and data["senha"]:
            funcionario.set_senha(data["senha"])

        # Atualizar PIN se fornecido
        if "pin" in data and data["pin"]:
            funcionario.set_pin(data["pin"])

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Funcionário atualizado com sucesso",
                "funcionario": {
                    "id": funcionario.id,
                    "nome": funcionario.nome,
                    "usuario": funcionario.usuario,
                    "cargo": funcionario.cargo,
                    "ativo": funcionario.ativo,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar funcionário {id}: {str(e)}")
        return jsonify({"error": f"Erro ao atualizar funcionário: {str(e)}"}), 500


@funcionarios_bp.route("/<int:id>", methods=["DELETE"])
def excluir_funcionario(id):
    """Excluir (desativar) um funcionário"""
    try:
        funcionario = Funcionario.query.get(id)

        if not funcionario:
            return jsonify({"error": "Funcionário não encontrado"}), 404

        # Verificar se é o único admin
        if funcionario.nivel_acesso == "admin":
            admins_ativos = Funcionario.query.filter_by(
                nivel_acesso="admin", ativo=True
            ).count()
            if admins_ativos <= 1:
                return (
                    jsonify(
                        {
                            "error": "Não é possível desativar o único administrador do sistema"
                        }
                    ),
                    400,
                )

        # Verificar se funcionário tem vendas
        total_vendas = Venda.query.filter_by(funcionario_id=id).count()
        if total_vendas > 0:
            return (
                jsonify(
                    {
                        "error": "Não é possível excluir o funcionário pois existem vendas vinculadas a ele",
                        "quantidade_vendas": total_vendas,
                    }
                ),
                400,
            )

        # Exclusão lógica
        funcionario.ativo = False
        funcionario.data_demissao = date.today()

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Funcionário desativado com sucesso",
                "funcionario": {
                    "id": funcionario.id,
                    "nome": funcionario.nome,
                    "ativo": False,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir funcionário {id}: {str(e)}")
        return jsonify({"error": f"Erro ao excluir funcionário: {str(e)}"}), 500


@funcionarios_bp.route("/login", methods=["POST"])
def login_funcionario():
    """Login de funcionário"""
    try:
        data = request.get_json()

        if not data or not data.get("usuario") or not data.get("senha"):
            return jsonify({"error": "Usuário e senha são obrigatórios"}), 400

        usuario = data["usuario"]
        senha = data["senha"]

        funcionario = Funcionario.query.filter_by(usuario=usuario, ativo=True).first()

        if not funcionario:
            return jsonify({"error": "Usuário não encontrado ou inativo"}), 401

        if not funcionario.check_senha(senha):
            return jsonify({"error": "Senha incorreta"}), 401

        # Retornar dados do funcionário (sem senha)
        return jsonify(
            {
                "success": True,
                "message": "Login realizado com sucesso",
                "funcionario": {
                    "id": funcionario.id,
                    "nome": funcionario.nome,
                    "usuario": funcionario.usuario,
                    "nivel_acesso": funcionario.nivel_acesso,
                    "cargo": funcionario.cargo,
                },
            }
        )

    except Exception as e:
        print(f"Erro no login: {str(e)}")
        return jsonify({"error": f"Erro no login: {str(e)}"}), 500


@funcionarios_bp.route("/verificar-pin", methods=["POST"])
def verificar_pin():
    """Verificar PIN para PDV"""
    try:
        data = request.get_json()

        if not data or not data.get("pin"):
            return jsonify({"error": "PIN é obrigatório"}), 400

        pin = data["pin"]

        funcionario = Funcionario.query.filter_by(
            ativo=True
        ).first()  # Na prática, você teria o ID do funcionário

        if not funcionario:
            return jsonify({"error": "Nenhum funcionário ativo encontrado"}), 404

        if not funcionario.check_pin(pin):
            return jsonify({"error": "PIN incorreto"}), 401

        return jsonify(
            {
                "success": True,
                "message": "PIN verificado com sucesso",
                "funcionario": {"id": funcionario.id, "nome": funcionario.nome},
            }
        )

    except Exception as e:
        print(f"Erro ao verificar PIN: {str(e)}")
        return jsonify({"error": f"Erro ao verificar PIN: {str(e)}"}), 500
