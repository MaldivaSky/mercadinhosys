from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from datetime import datetime, timedelta
from app import db
from app.models import Funcionario, Estabelecimento, LoginHistory
import traceback
import pytz

auth_bp = Blueprint("auth", __name__)


# ==================== ROTAS DE AUTENTICAÇÃO COM AUDITORIA ====================


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Autenticação de usuário com auditoria de login
    """
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Dados não fornecidos",
                        "code": "NO_DATA",
                    }
                ),
                400,
            )

        # Aceitar tanto 'email' quanto 'username' no campo de login
        identifier = data.get("email", data.get("username", "")).strip()
        senha = data.get("senha", "")
        estabelecimento_id = data.get("estabelecimento_id", 4)
        dispositivo = request.headers.get("User-Agent", "Desconhecido")
        ip_address = request.remote_addr

        if not identifier or not senha:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Email/Username e senha são obrigatórios",
                        "code": "CREDENTIALS_REQUIRED",
                    }
                ),
                400,
            )

        # Buscar funcionário por username OU email e estabelecimento_id
        funcionario = Funcionario.query.filter(
            db.or_(
                db.and_(
                    Funcionario.username == identifier,
                    Funcionario.estabelecimento_id == estabelecimento_id
                ),
                db.and_(
                    db.func.lower(Funcionario.email) == identifier.lower(),
                    Funcionario.estabelecimento_id == estabelecimento_id
                )
            )
        ).first()

        # Registrar tentativa de login (sucesso ou falha)
        login_history = LoginHistory(
            username=identifier,  # Pode ser email ou username
            estabelecimento_id=estabelecimento_id,
            ip_address=ip_address,
            dispositivo=dispositivo[:200],  # Limitar tamanho
            success=False,  # Inicialmente falha
        )

        if not funcionario:
            current_app.logger.warning(
                f"Tentativa de login com credencial não encontrada: {identifier} "
                f"de IP: {ip_address}"
            )

            login_history.observacoes = "Usuário não encontrado"
            db.session.add(login_history)
            db.session.commit()

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Credenciais inválidas",
                        "code": "INVALID_CREDENTIALS",
                    }
                ),
                401,
            )

        # Verificar senha
        if not funcionario.check_senha(senha):
            current_app.logger.warning(
                f"Senha incorreta para: {identifier} " f"de IP: {ip_address}"
            )

            login_history.funcionario_id = funcionario.id
            login_history.observacoes = "Senha incorreta"
            db.session.add(login_history)
            db.session.commit()

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Credenciais inválidas",
                        "code": "INVALID_CREDENTIALS",
                    }
                ),
                401,
            )

        # Verificar status
        status = getattr(
            funcionario, "status", "ativo" if funcionario.ativo else "inativo"
        )

        if status != "ativo":
            login_history.funcionario_id = funcionario.id
            login_history.observacoes = f"Conta {status}"
            db.session.add(login_history)
            db.session.commit()

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Conta inativa",
                        "message": f"Sua conta está {status}. Contate o administrador.",
                        "code": "ACCOUNT_INACTIVE",
                    }
                ),
                403,
            )

        # Identity como string (user_id)
        identity = str(funcionario.id)

        # Claims adicionais
        additional_claims = {
            "username": funcionario.username,
            "nome": funcionario.nome,
            "estabelecimento_id": funcionario.estabelecimento_id,
            "status": status,
            "login_time": datetime.utcnow().isoformat(),
            "ip_address": ip_address,
            "dispositivo": dispositivo[:100],
        }

        # Adicionar role
        if hasattr(funcionario, "role"):
            additional_claims["role"] = funcionario.role
        else:
            cargo = funcionario.cargo.lower()
            if cargo == "dono" or cargo == "admin":
                additional_claims["role"] = "admin"
            elif cargo == "gerente":
                additional_claims["role"] = "gerente"
            elif cargo == "caixa":
                additional_claims["role"] = "caixa"
            elif cargo == "vendedor":
                additional_claims["role"] = "vendedor"
            else:
                additional_claims["role"] = "funcionario"

        # Criar tokens
        access_token = create_access_token(
            identity=identity,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=8),
        )

        refresh_token = create_refresh_token(
            identity=identity,
            additional_claims=additional_claims,
            expires_delta=timedelta(days=7),
        )

        # Registrar login bem-sucedido
        login_history.funcionario_id = funcionario.id
        login_history.success = True
        login_history.token_hash = (
            hash(access_token) % 1000000
        )  # Hash simples para referência
        db.session.add(login_history)
        db.session.commit()

        # Atualizar último login do funcionário
        funcionario.ultimo_login = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(
            f"Login bem-sucedido: {identifier} ({funcionario.nome}) "
            f"de IP: {ip_address}"
        )

        # Buscar informações do estabelecimento
        estabelecimento = Estabelecimento.query.get(estabelecimento_id)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Login realizado com sucesso",
                    "data": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user": {
                            "id": funcionario.id,
                            "nome": funcionario.nome,
                            "username": funcionario.username,
                            "email": funcionario.email,
                            "cargo": funcionario.cargo,
                            "role": additional_claims["role"],
                            "status": status,
                            "estabelecimento_id": funcionario.estabelecimento_id,
                            "estabelecimento_nome": (
                                estabelecimento.nome if estabelecimento else None
                            ),
                            "avatar": (
                                funcionario.avatar
                                if hasattr(funcionario, "avatar")
                                else None
                            ),
                            "telefone": (
                                funcionario.telefone
                                if hasattr(funcionario, "telefone")
                                else None
                            ),
                            "ultimo_login": (
                                funcionario.ultimo_login.isoformat()
                                if funcionario.ultimo_login
                                else None
                            ),
                        },
                        "session": {
                            "login_time": additional_claims["login_time"],
                            "expires_in": 28800,  # 8 horas em segundos
                            "refresh_expires_in": 604800,  # 7 dias em segundos
                            "token_type": "bearer",
                        },
                        "estabelecimento": {
                            "id": estabelecimento.id if estabelecimento else None,
                            "nome": estabelecimento.nome if estabelecimento else None,
                            "cnpj": estabelecimento.cnpj if estabelecimento else None,
                            "telefone": (
                                estabelecimento.telefone if estabelecimento else None
                            ),
                        },
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no login: {str(e)}\n{traceback.format_exc()}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro interno no servidor",
                    "message": str(e),
                    "code": "INTERNAL_ERROR",
                }
            ),
            500,
        )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Renovar access token usando refresh token"""
    try:
        current_user = get_jwt_identity()
        claims = get_jwt()

        # Verificar se o refresh token não está expirado
        exp_timestamp = claims.get("exp")
        if exp_timestamp:
            exp_time = datetime.fromtimestamp(exp_timestamp, tz=pytz.UTC)
            if exp_time < datetime.now(pytz.UTC):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Refresh token expirado",
                            "code": "REFRESH_TOKEN_EXPIRED",
                        }
                    ),
                    401,
                )

        # Extrair claims adicionais
        additional_claims = {
            "username": claims.get("username"),
            "nome": claims.get("nome"),
            "estabelecimento_id": claims.get("estabelecimento_id"),
            "status": claims.get("status"),
            "role": claims.get("role"),
            "refresh_time": datetime.utcnow().isoformat(),
            "ip_address": request.remote_addr,
            "dispositivo": request.headers.get("User-Agent", "Desconhecido")[:100],
        }

        access_token = create_access_token(
            identity=current_user,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=8),
        )

        current_app.logger.info(f"Token renovado para usuário: {current_user}")

        return (
            jsonify(
                {
                    "success": True,
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": 28800,
                    "refresh_time": additional_claims["refresh_time"],
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro no refresh token: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Token inválido ou expirado",
                    "code": "INVALID_REFRESH_TOKEN",
                }
            ),
            401,
        )


@auth_bp.route("/validate", methods=["GET"])
@jwt_required()
def validate_token():
    """Validar token e retornar informações do usuário"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        # Verificar expiração
        exp_timestamp = claims.get("exp")
        if exp_timestamp:
            exp_time = datetime.fromtimestamp(exp_timestamp, tz=pytz.UTC)
            time_remaining = exp_time - datetime.now(pytz.UTC)

            if time_remaining.total_seconds() <= 0:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Token expirado",
                            "code": "TOKEN_EXPIRED",
                        }
                    ),
                    401,
                )

        # Buscar funcionário para garantir que ainda existe
        funcionario = Funcionario.query.get(int(current_user_id))

        if not funcionario:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Usuário não encontrado",
                        "code": "USER_NOT_FOUND",
                    }
                ),
                404,
            )

        # Verificar se usuário ainda está ativo
        status = getattr(
            funcionario, "status", "ativo" if funcionario.ativo else "inativo"
        )
        if status != "ativo":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Usuário inativo",
                        "code": "USER_INACTIVE",
                    }
                ),
                403,
            )

        # Buscar informações do estabelecimento
        estabelecimento = Estabelecimento.query.get(funcionario.estabelecimento_id)

        # Usar dados do token e do banco
        user_data = {
            "id": int(current_user_id),
            "username": claims.get("username"),
            "nome": claims.get("nome"),
            "estabelecimento_id": claims.get("estabelecimento_id"),
            "role": claims.get("role"),
            "status": status,
            "cargo": funcionario.cargo,
            "email": funcionario.email,
            "avatar": funcionario.avatar if hasattr(funcionario, "avatar") else None,
            "telefone": (
                funcionario.telefone if hasattr(funcionario, "telefone") else None
            ),
            "ultimo_login": (
                funcionario.ultimo_login.isoformat()
                if funcionario.ultimo_login
                else None
            ),
            "estabelecimento_nome": estabelecimento.nome if estabelecimento else None,
        }

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Token válido",
                    "data": {
                        "user": user_data,
                        "session": {
                            "expires_at": (
                                exp_time.isoformat() if exp_timestamp else None
                            ),
                            "time_remaining_seconds": (
                                time_remaining.total_seconds()
                                if exp_timestamp
                                else None
                            ),
                            "login_time": claims.get("login_time"),
                            "ip_address": claims.get("ip_address"),
                            "is_valid": True,
                        },
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro na validação do token: {str(e)}")
        return (
            jsonify(
                {"success": False, "error": "Token inválido", "code": "INVALID_TOKEN"}
            ),
            401,
        )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """Logout do usuário com registro de auditoria"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        # Registrar logout
        login_history = LoginHistory(
            funcionario_id=int(current_user_id),
            username=claims.get("username"),
            estabelecimento_id=claims.get("estabelecimento_id"),
            ip_address=request.remote_addr,
            dispositivo=request.headers.get("User-Agent", "Desconhecido")[:200],
            success=True,
            observacoes="Logout realizado",
            token_hash=hash(claims.get("jti", "")) % 1000000,
        )

        db.session.add(login_history)
        db.session.commit()

        current_app.logger.info(f"Logout: {current_user_id}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Logout realizado com sucesso",
                    "logout_time": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no logout: {str(e)}")
        return (
            jsonify(
                {"success": False, "error": "Erro no logout", "code": "LOGOUT_ERROR"}
            ),
            500,
        )


@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Obter perfil completo do usuário autenticado"""
    try:
        current_user_id = get_jwt_identity()

        funcionario = Funcionario.query.get(int(current_user_id))

        if not funcionario:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Usuário não encontrado",
                        "code": "USER_NOT_FOUND",
                    }
                ),
                404,
            )

        estabelecimento = Estabelecimento.query.get(funcionario.estabelecimento_id)

        # Estatísticas do usuário (se aplicável)
        # Exemplo: total de vendas hoje
        hoje = datetime.utcnow().date()
        total_vendas_hoje = 0
        if hasattr(funcionario, "vendas"):
            total_vendas_hoje = len(
                [v for v in funcionario.vendas if v.created_at.date() == hoje]
            )

        profile_data = {
            "id": funcionario.id,
            "nome": funcionario.nome,
            "username": funcionario.username,
            "email": funcionario.email,
            "cargo": funcionario.cargo,
            "role": getattr(funcionario, "role", funcionario.cargo),
            "status": getattr(
                funcionario, "status", "ativo" if funcionario.ativo else "inativo"
            ),
            "avatar": funcionario.avatar if hasattr(funcionario, "avatar") else None,
            "telefone": (
                funcionario.telefone if hasattr(funcionario, "telefone") else None
            ),
            "data_nascimento": (
                funcionario.data_nascimento.isoformat()
                if hasattr(funcionario, "data_nascimento")
                and funcionario.data_nascimento
                else None
            ),
            "endereco": (
                funcionario.endereco if hasattr(funcionario, "endereco") else None
            ),
            "data_admissao": (
                funcionario.data_admissao.isoformat()
                if hasattr(funcionario, "data_admissao") and funcionario.data_admissao
                else None
            ),
            "ultimo_login": (
                funcionario.ultimo_login.isoformat()
                if funcionario.ultimo_login
                else None
            ),
            "estabelecimento": {
                "id": estabelecimento.id if estabelecimento else None,
                "nome": estabelecimento.nome if estabelecimento else None,
                "cnpj": estabelecimento.cnpj if estabelecimento else None,
                "telefone": estabelecimento.telefone if estabelecimento else None,
                "endereco": estabelecimento.endereco if estabelecimento else None,
            },
            "permissions": get_permissions_for_role(funcionario.cargo),
            "estatisticas": {
                "total_vendas_hoje": total_vendas_hoje,
                "online": True,  # Poderia verificar último heartbeat
            },
            "configuracoes": {
                "tema": getattr(funcionario, "tema_preferido", "claro"),
                "notificacoes": getattr(funcionario, "receber_notificacoes", True),
                "idioma": getattr(funcionario, "idioma_preferido", "pt-BR"),
            },
        }

        return jsonify({"success": True, "data": profile_data}), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao obter perfil: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao obter perfil",
                    "code": "PROFILE_ERROR",
                }
            ),
            500,
        )


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Atualizar perfil do usuário"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Nenhum dado fornecido",
                        "code": "NO_DATA",
                    }
                ),
                400,
            )

        funcionario = Funcionario.query.get(int(current_user_id))

        if not funcionario:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Usuário não encontrado",
                        "code": "USER_NOT_FOUND",
                    }
                ),
                404,
            )

        # Campos permitidos para atualização
        allowed_fields = [
            "nome",
            "email",
            "telefone",
            "avatar",
            "data_nascimento",
            "endereco",
            "tema_preferido",
            "receber_notificacoes",
            "idioma_preferido",
        ]

        updated_fields = []

        for field in allowed_fields:
            if field in data and hasattr(funcionario, field):
                setattr(funcionario, field, data[field])
                updated_fields.append(field)

        # Atualizar senha (se fornecido)
        if "senha_atual" in data and "nova_senha" in data:
            if not funcionario.check_senha(data["senha_atual"]):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Senha atual incorreta",
                            "code": "WRONG_CURRENT_PASSWORD",
                        }
                    ),
                    400,
                )

            funcionario.set_senha(data["nova_senha"])
            updated_fields.append("senha")

        funcionario.data_atualizacao = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Perfil atualizado com sucesso",
                    "updated_fields": updated_fields,
                    "data": {
                        "nome": funcionario.nome,
                        "email": funcionario.email,
                        "data_atualizacao": funcionario.data_atualizacao.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar perfil: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao atualizar perfil",
                    "code": "UPDATE_PROFILE_ERROR",
                }
            ),
            500,
        )


@auth_bp.route("/sessions", methods=["GET"])
@jwt_required()
def get_sessions():
    """Obter histórico de sessões do usuário"""
    try:
        current_user_id = get_jwt_identity()

        # Parâmetros de paginação
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = min(request.args.get("por_pagina", 20, type=int), 100)

        # Consultar histórico de login
        query = LoginHistory.query.filter_by(funcionario_id=int(current_user_id))
        query = query.order_by(LoginHistory.created_at.desc())

        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        sessoes = paginacao.items

        resultado = []
        for sessao in sessoes:
            resultado.append(
                {
                    "id": sessao.id,
                    "login_time": sessao.created_at.isoformat(),
                    "ip_address": sessao.ip_address,
                    "dispositivo": sessao.dispositivo,
                    "success": sessao.success,
                    "observacoes": sessao.observacoes,
                    "duracao_minutos": (
                        (sessao.updated_at - sessao.created_at).total_seconds() / 60
                        if sessao.updated_at and sessao.created_at
                        else None
                    ),
                }
            )

        # Sessão atual
        claims = get_jwt()
        current_session = {
            "login_time": claims.get("login_time"),
            "ip_address": claims.get("ip_address"),
            "dispositivo": claims.get("dispositivo"),
            "expires_at": (
                datetime.fromtimestamp(claims.get("exp")).isoformat()
                if claims.get("exp")
                else None
            ),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "current_session": current_session,
                    "sessions": resultado,
                    "paginacao": {
                        "pagina_atual": paginacao.page,
                        "total_paginas": paginacao.pages,
                        "total_itens": paginacao.total,
                        "itens_por_pagina": paginacao.per_page,
                        "tem_proxima": paginacao.has_next,
                        "tem_anterior": paginacao.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao obter sessões: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao obter sessões",
                    "code": "SESSIONS_ERROR",
                }
            ),
            500,
        )


@auth_bp.route("/password/reset-request", methods=["POST"])
def password_reset_request():
    """Solicitar redefinição de senha"""
    try:
        data = request.get_json()

        if not data or not data.get("email"):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Email é obrigatório",
                        "code": "EMAIL_REQUIRED",
                    }
                ),
                400,
            )

        email = data["email"].strip().lower()

        # Buscar usuário pelo email
        funcionario = Funcionario.query.filter(
            db.func.lower(Funcionario.email) == email
        ).first()

        if not funcionario:
            # Não revelar que o email não existe por segurança
            current_app.logger.info(
                f"Solicitação de reset de senha para email não cadastrado: {email}"
            )
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Se o email estiver cadastrado, você receberá instruções para redefinir sua senha",
                    }
                ),
                200,
            )

        # Aqui você implementaria o envio de email
        # Por enquanto, apenas logamos
        current_app.logger.info(
            f"Solicitação de reset de senha para: {email} (ID: {funcionario.id})"
        )

        # Gerar token de reset (em produção, use uma biblioteca segura)
        import secrets

        reset_token = secrets.token_urlsafe(32)

        # Salvar token no banco (implementação básica)
        funcionario.reset_token = reset_token
        funcionario.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Se o email estiver cadastrado, você receberá instruções para redefinir sua senha",
                    "token": reset_token,  # Em produção, não enviar o token na resposta
                    "expires_in": 3600,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro na solicitação de reset de senha: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao processar solicitação",
                    "code": "RESET_REQUEST_ERROR",
                }
            ),
            500,
        )


def get_permissions_for_role(cargo):
    """Retornar permissões baseadas no cargo"""
    cargo = cargo.lower() if cargo else ""

    permissions = {
        "admin": ["full_access"],
        "dono": ["full_access"],
        "gerente": [
            "view_reports",
            "manage_products",
            "manage_clients",
            "manage_sales",
            "view_financial",
            "manage_staff",
        ],
        "caixa": ["process_sales", "view_products", "view_clients"],
        "vendedor": ["process_sales", "view_products", "view_clients"],
        "funcionario": ["view_products", "view_clients"],
    }

    for key in permissions:
        if key in cargo:
            return permissions[key]

    return permissions["funcionario"]


# Modelo para LoginHistory (adicione ao models.py se necessário):
"""
class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=True)
    username = db.Column(db.String(100), nullable=False)
    estabelecimento_id = db.Column(db.Integer, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 suporta 45 caracteres
    dispositivo = db.Column(db.String(200))
    success = db.Column(db.Boolean, default=False)
    token_hash = db.Column(db.Integer)  # Hash do token para referência
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    funcionario = db.relationship('Funcionario', backref='login_history')
    
    def __repr__(self):
        return f'<LoginHistory {self.username} {self.created_at}>'
"""
