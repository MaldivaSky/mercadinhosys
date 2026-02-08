from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from datetime import datetime, timedelta
from decimal import Decimal
from app import db
from app.models import Funcionario, Estabelecimento, LoginHistory
from werkzeug.security import generate_password_hash
import traceback
import pytz
import hashlib
import secrets
import os

auth_bp = Blueprint("auth", __name__)


# ==================== HEALTH CHECK ====================


@auth_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint para monitoramento"""
    try:
        # Testar conexão com banco de dados
        db.session.execute(db.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {str(e)}")
        db_status = "disconnected"
    
    # Detectar ambiente
    is_production = os.environ.get("RENDER") or os.environ.get("RAILWAY") or os.environ.get("HEROKU")
    environment = "production" if is_production else "development"
    
    # Status geral
    status = "healthy" if db_status == "connected" else "unhealthy"
    
    response = {
        "status": status,
        "database": db_status,
        "environment": environment,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }
    
    status_code = 200 if status == "healthy" else 503
    
    return jsonify(response), status_code


@auth_bp.route("/ping", methods=["GET"])
def ping():
    """Rota simples de ping para monitoramento básico"""
    return jsonify({"status": "ok", "message": "Servidor ativo!"}), 200


# ==================== ROTAS DE AUTENTICAÇÃO COM AUDITORIA ====================


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Autenticação de usuário com auditoria de login
    """
    try:
        data = request.get_json(silent=True)
        current_app.logger.info(f"[LOGIN] Payload recebido: {data}")

        if not data:
            current_app.logger.warning("[LOGIN] Nenhum dado recebido no body da requisição.")
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

        # Aceitar 'email', 'username' e compatibilidade com versões antigas ('identifier')
        identifier = (
            data.get("email")
            or data.get("username")
            or data.get("identifier")
            or ""
        ).strip()
        # Aceitar 'senha' e compatibilidade com versões antigas ('password')
        senha = (data.get("senha") or data.get("password") or "").strip()
        dispositivo = request.headers.get("User-Agent", "Desconhecido")
        ip_address = request.remote_addr

        current_app.logger.info(f"[LOGIN] identifier: {identifier} | senha: {'*' * len(senha)}")

        if not identifier or not senha:
            current_app.logger.warning("[LOGIN] Username/email ou senha não enviados.")
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

        # Buscar funcionário por username OU email (sem estabelecimento_id)
        funcionario = Funcionario.query.filter(
            db.or_( 
                Funcionario.username == identifier,
                db.func.lower(Funcionario.email) == identifier.lower(),
            )
        ).first()
        if funcionario:
            current_app.logger.info(f"[LOGIN] Funcionário encontrado: id={funcionario.id}, username={funcionario.username}, email={funcionario.email}, ativo={funcionario.ativo}, status={getattr(funcionario, 'status', 'N/A')}")
        else:
            current_app.logger.warning(f"[LOGIN] Nenhum funcionário encontrado para identifier: {identifier}")

        # Registrar tentativa de login (sucesso ou falha)
        login_history = LoginHistory(
            username=identifier,
            ip_address=ip_address,
            dispositivo=dispositivo[:200],
            success=False,
        )

        if not funcionario:
            current_app.logger.warning(
                f"Tentativa de login com credencial não encontrada: {identifier} "
                f"de IP: {ip_address}"
            )

            login_history.observacoes = "Usuário não encontrado"

            # Tentar encontrar algum estabelecimento para associar
            try:
                estabelecimento_default = Estabelecimento.query.first()
                if estabelecimento_default:
                    login_history.estabelecimento_id = estabelecimento_default.id
            except Exception:
                pass  # Ignora se não conseguir

            # Só salva se estabelecimento_id não for None
            if login_history.estabelecimento_id is not None:
                db.session.add(login_history)
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()  # 🔥 IMPORTANTE: rollback em caso de erro
                    current_app.logger.error(f"Erro ao salvar histórico de login: {str(e)}")
            else:
                current_app.logger.warning("Não foi possível registrar histórico de login: nenhum estabelecimento encontrado.")

            current_app.logger.warning("[LOGIN] Retornando 401 - Credenciais inválidas (usuário não encontrado)")
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

        # Adicionar estabelecimento_id do funcionário ao histórico
        login_history.estabelecimento_id = funcionario.estabelecimento_id
        login_history.funcionario_id = funcionario.id

        # Verificar senha
        if not funcionario.check_senha(senha):
            current_app.logger.warning(
                f"[LOGIN] Senha incorreta para: {identifier} (ID: {funcionario.id}) "
                f"de IP: {ip_address}"
            )

            login_history.observacoes = "Senha incorreta"
            db.session.add(login_history)
            db.session.commit()

            current_app.logger.warning("[LOGIN] Retornando 401 - Credenciais inválidas (senha incorreta)")
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
        if funcionario.status != "ativo":
            login_history.observacoes = f"Conta {funcionario.status}"
            db.session.add(login_history)
            db.session.commit()

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Conta inativa",
                        "message": f"Sua conta está {funcionario.status}. Contate o administrador.",
                        "code": "ACCOUNT_INACTIVE",
                    }
                ),
                403,
            )

        # Verificar se está ativo (campo ativo)
        if not funcionario.ativo:
            login_history.observacoes = "Conta inativa (campo ativo=False)"
            db.session.add(login_history)
            db.session.commit()

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Conta inativa",
                        "message": "Sua conta está desativada. Contate o administrador.",
                        "code": "ACCOUNT_INACTIVE",
                    }
                ),
                403,
            )

        # Identity como string (user_id)
        identity = str(funcionario.id)

        # Buscar estabelecimento do funcionário
        estabelecimento = Estabelecimento.query.get(funcionario.estabelecimento_id)

        if not estabelecimento:
            login_history.observacoes = "Estabelecimento não encontrado"
            db.session.add(login_history)
            db.session.commit()

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Estabelecimento não configurado",
                        "code": "ESTABLISHMENT_NOT_FOUND",
                    }
                ),
                404,
            )

        # Claims adicionais
        additional_claims = {
            "username": funcionario.username,
            "nome": funcionario.nome,
            "estabelecimento_id": funcionario.estabelecimento_id,
            "estabelecimento_nome": estabelecimento.nome_fantasia,
            "status": funcionario.status,
            "role": funcionario.role,
            "cargo": funcionario.cargo,
            "login_time": datetime.utcnow().isoformat(),
            "ip_address": ip_address,
            "dispositivo": dispositivo[:100],
        }

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

        # Hash do token para auditoria (usando hashlib para consistência)
        token_hash = (
            int(hashlib.sha256(access_token.encode()).hexdigest(), 16) % 1000000
        )

        # Registrar login bem-sucedido
        login_history.success = True
        login_history.token_hash = token_hash
        db.session.add(login_history)
        db.session.commit()

        current_app.logger.info(
            f"Login bem-sucedido: {identifier} ({funcionario.nome}) "
            f"Estabelecimento: {estabelecimento.nome_fantasia} "
            f"de IP: {ip_address}"
        )

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
                            "role": funcionario.role,
                            "status": funcionario.status,
                            "cpf": funcionario.cpf,
                            "telefone": funcionario.telefone,
                            "foto_url": funcionario.foto_url,
                            "permissoes": funcionario.permissoes,
                            "data_admissao": (
                                funcionario.data_admissao.isoformat()
                                if funcionario.data_admissao
                                else None
                            ),
                            "estabelecimento_id": funcionario.estabelecimento_id,
                            "estabelecimento_nome": estabelecimento.nome_fantasia,
                            "created_at": (
                                funcionario.data_cadastro.isoformat()
                                if funcionario.data_cadastro
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
                            "id": estabelecimento.id,
                            "nome": estabelecimento.nome_fantasia,
                            "cnpj": estabelecimento.cnpj,
                            "telefone": estabelecimento.telefone,
                            "email": estabelecimento.email,
                            "endereco": estabelecimento.endereco_completo(),
                            "cidade": estabelecimento.cidade,
                            "estado": estabelecimento.estado,
                        },
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro no login: {str(e)}\n{traceback.format_exc()}"
        )
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


@auth_bp.route("/bootstrap", methods=["POST"])
def bootstrap_admin():
    try:
        data = request.get_json() or {}
        identifier = (
            data.get("email")
            or data.get("username")
            or data.get("identifier")
            or ""
        ).strip()
        senha = (data.get("senha") or data.get("password") or "").strip()

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

        if Funcionario.query.first() is not None:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Bootstrap indisponível: o sistema já possui usuários",
                        "code": "BOOTSTRAP_DISABLED",
                    }
                ),
                409,
            )

        if "@" in identifier:
            email = identifier.lower()
            username = identifier.split("@", 1)[0]
        else:
            username = identifier
            email = "admin@empresa.com"

        estabelecimento = Estabelecimento.query.first()
        if estabelecimento is None:
            estabelecimento = Estabelecimento(
                nome_fantasia="Mercado Souza Center",
                razao_social="Mercado Souza Center LTDA",
                cnpj="12.345.678/0001-90",
                inscricao_estadual="ISENTO",
                telefone="(84) 3234-5678",
                email="contato@mercadosouza.com",
                cep="59000-000",
                logradouro="Rua Principal",
                numero="123",
                bairro="Centro",
                cidade="Natal",
                estado="RN",
                pais="Brasil",
                regime_tributario="SIMPLES NACIONAL",
                ativo=True,
                data_abertura=datetime.utcnow().date(),
                data_cadastro=datetime.utcnow(),
            )
            db.session.add(estabelecimento)
            db.session.flush()

        admin = Funcionario(
            estabelecimento_id=estabelecimento.id,
            nome="Administrador Sistema",
            username=username,
            senha_hash=generate_password_hash(senha),
            email=email,
            cpf="111.222.333-44",
            rg="RN-12345678",
            data_nascimento=datetime(1985, 1, 1).date(),
            telefone="(84) 91234-5678",
            celular="(84) 91234-5678",
            cargo="Gerente",
            role="ADMIN",
            ativo=True,
            status="ativo",
            data_admissao=datetime.utcnow().date(),
            salario_base=Decimal("3500.00"),
            cep="59000-000",
            logradouro="Rua Principal",
            numero="100",
            bairro="Centro",
            cidade="Natal",
            estado="RN",
            pais="Brasil",
            permissoes_json='{"pdv":true,"estoque":true,"compras":true,"financeiro":true,"configuracoes":true,"relatorios":true}',
        )
        db.session.add(admin)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Bootstrap concluído: usuário admin criado",
                    "data": {"username": admin.username, "email": admin.email},
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro no bootstrap: {str(e)}\n{traceback.format_exc()}"
        )
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
            "estabelecimento_nome": claims.get("estabelecimento_nome"),
            "status": claims.get("status"),
            "role": claims.get("role"),
            "cargo": claims.get("cargo"),
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
        if funcionario.status != "ativo" or not funcionario.ativo:
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
            "estabelecimento_nome": claims.get("estabelecimento_nome"),
            "role": claims.get("role"),
            "status": funcionario.status,
            "cargo": claims.get("cargo"),
            "email": funcionario.email,
            "foto_url": funcionario.foto_url,
            "telefone": funcionario.telefone,
            "cpf": funcionario.cpf,
            "permissoes": funcionario.permissoes,
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
        )

        # Calcular hash do token atual para auditoria
        if claims.get("jti"):
            login_history.token_hash = (
                int(hashlib.sha256(claims.get("jti").encode()).hexdigest(), 16)
                % 1000000
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
        hoje = datetime.utcnow().date()
        total_vendas_hoje = 0
        if hasattr(funcionario, "vendas"):
            total_vendas_hoje = len(
                [v for v in funcionario.vendas if v.data_venda.date() == hoje]
            )

        profile_data = {
            "id": funcionario.id,
            "nome": funcionario.nome,
            "username": funcionario.username,
            "email": funcionario.email,
            "cpf": funcionario.cpf,
            "telefone": funcionario.telefone,
            "foto_url": funcionario.foto_url,
            "cargo": funcionario.cargo,
            "role": funcionario.role,
            "status": funcionario.status,
            "ativo": funcionario.ativo,
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
            "permissoes": funcionario.permissoes,
            "estabelecimento": {
                "id": estabelecimento.id if estabelecimento else None,
                "nome": estabelecimento.nome_fantasia if estabelecimento else None,
                "cnpj": estabelecimento.cnpj if estabelecimento else None,
                "telefone": estabelecimento.telefone if estabelecimento else None,
                "email": estabelecimento.email if estabelecimento else None,
                "endereco": estabelecimento.endereco_completo() if estabelecimento else None,
                "cidade": estabelecimento.cidade if estabelecimento else None,
                "estado": estabelecimento.estado if estabelecimento else None,
            },
            "permissions": get_permissions_for_role(
                funcionario.role, funcionario.permissoes
            ),
            "estatisticas": {
                "total_vendas_hoje": total_vendas_hoje,
                "online": True,
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
            "foto_url",
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
                        "telefone": funcionario.telefone,
                        "foto_url": funcionario.foto_url,
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
        current_app.logger.info(
            f"Solicitação de reset de senha para: {email} (ID: {funcionario.id})"
        )

        # Gerar token de reset
        reset_token = secrets.token_urlsafe(32)

        # Salvar token no banco
        funcionario.reset_token = reset_token
        funcionario.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        # EM PRODUÇÃO: Enviar email com link de reset
        # Exemplo: f"{current_app.config['APP_URL']}/reset-password?token={reset_token}"

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Se o email estiver cadastrado, você receberá instruções para redefinir sua senha",
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


def get_permissions_for_role(role, permissoes_db=None):
    """Retornar permissões baseadas no role e nas permissões do banco"""

    # Permissões baseadas no role
    role_permissions = {
        "admin": [
            "full_access",
            "acesso_configuracoes",
            "acesso_financeiro",
            "acesso_relatorios",
        ],
        "gerente": [
            "view_reports",
            "manage_products",
            "manage_clients",
            "manage_sales",
            "view_financial",
        ],
        "funcionario": ["view_products", "view_clients"],
        "caixa": ["process_sales", "view_products", "view_clients"],
    }

    # Permissões padrão baseadas no role
    permissions = role_permissions.get(role, ["view_products", "view_clients"])

    # Adicionar permissões específicas do banco de dados
    if permissoes_db and isinstance(permissoes_db, dict):
        for key, value in permissoes_db.items():
            if value and key.startswith("acesso_") or key.startswith("pode_"):
                # Converter nomes de permissões do banco para formato padrão
                if key == "acesso_pdv":
                    permissions.append("process_sales")
                elif key == "acesso_estoque":
                    permissions.append("manage_products")
                elif key == "acesso_relatorios":
                    permissions.append("view_reports")
                elif key == "acesso_configuracoes":
                    permissions.append("manage_settings")
                elif key == "acesso_financeiro":
                    permissions.append("view_financial")
                elif key == "pode_dar_desconto":
                    permissions.append("give_discount")
                elif key == "pode_cancelar_venda":
                    permissions.append("cancel_sale")
                elif key == "acesso_dashboard_avancado":
                    permissions.append("view_advanced_dashboard")

    # Remover duplicatas
    return list(set(permissions))
