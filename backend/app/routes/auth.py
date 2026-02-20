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


@auth_bp.route("/setup-db", methods=["GET", "POST"])
def setup_db():
    """
    Endpoint de emergência para criar todas as tabelas e o admin padrão
    no banco de produção vazio. Use apenas uma vez e remova depois.
    """
    import traceback as _tb
    result = {"steps": [], "success": False}
    try:
        # 1. Criar todas as tabelas
        db.create_all()
        result["steps"].append("db.create_all() OK")

        # 2. Adicionar colunas extras que podem não existir
        from sqlalchemy import text as _t, inspect as _insp
        inspector = _insp(db.engine)
        extra_cols = {
            "estabelecimentos": [
                ("plano", "VARCHAR(20) DEFAULT 'Basic'"),
                ("plano_status", "VARCHAR(20) DEFAULT 'experimental'"),
                ("stripe_customer_id", "VARCHAR(100)"),
                ("stripe_subscription_id", "VARCHAR(100)"),
                ("vencimento_assinatura", "TIMESTAMP"),
            ],
        }
        for tname, cols in extra_cols.items():
            if tname in inspector.get_table_names():
                existing = [c["name"] for c in inspector.get_columns(tname)]
                for cname, ctype in cols:
                    if cname not in existing:
                        try:
                            db.session.execute(_t(f"ALTER TABLE {tname} ADD COLUMN {cname} {ctype}"))
                            db.session.commit()
                            result["steps"].append(f"ADD COLUMN {tname}.{cname} OK")
                        except Exception as ce:
                            db.session.rollback()
                            result["steps"].append(f"SKIP {tname}.{cname}: {str(ce)[:80]}")

        # 3. Criar login_history se necessário
        try:
            db.session.execute(_t("""
                CREATE TABLE IF NOT EXISTS login_history (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(150),
                    ip_address VARCHAR(45),
                    dispositivo VARCHAR(200),
                    success BOOLEAN,
                    observacoes TEXT,
                    token_hash INTEGER,
                    funcionario_id INTEGER,
                    estabelecimento_id INTEGER,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.session.commit()
            result["steps"].append("login_history OK")
        except Exception as lhe:
            db.session.rollback()
            result["steps"].append(f"login_history SKIP: {str(lhe)[:80]}")

        # 4. Criar admin padrão se banco vazio
        if Funcionario.query.count() == 0:
            estab = Estabelecimento.query.first()
            if not estab:
                estab = Estabelecimento(
                    nome_fantasia="MercadinhoSys",
                    razao_social="MercadinhoSys LTDA",
                    cnpj="00.000.000/0001-00",
                    telefone="(00) 0000-0000",
                    email="admin@mercadinhosys.com",
                    cep="00000-000",
                    logradouro="Rua do Sistema",
                    numero="0",
                    bairro="Centro",
                    cidade="Cloud",
                    estado="SP",
                    data_abertura=datetime.utcnow().date()
                )
                db.session.add(estab)
                db.session.flush()
                result["steps"].append(f"Estabelecimento criado id={estab.id}")

            admin = Funcionario(
                estabelecimento_id=estab.id,
                nome="Administrador",
                username="admin",
                email="admin@mercadinhosys.com",
                cpf="000.000.000-00",
                data_nascimento=datetime(1990, 1, 1).date(),
                celular="(00) 00000-0000",
                cargo="Gerente",
                data_admissao=datetime.utcnow().date(),
                role="ADMIN",
                status="ativo",
                ativo=True
            )
            admin.set_senha("admin123")
            db.session.add(admin)
            db.session.commit()
            result["steps"].append("Admin criado: username=admin, senha=admin123")
        else:
            result["steps"].append(f"Banco já tem {Funcionario.query.count()} funcionários - seed ignorado")

        result["success"] = True
        return jsonify(result), 200

    except Exception as e:
        db.session.rollback()
        result["error"] = str(e)
        result["traceback"] = _tb.format_exc()
        return jsonify(result), 500




@auth_bp.route("/db-schema", methods=["GET"])
def db_schema_check():
    """
    Diagnóstico do schema no banco (Postgres/Neon).
    Verifica migrações aplicadas e colunas críticas para viabilizar deploy.
    """
    result = {
        "database": "disconnected",
        "migrations_revision": None,
        "checks": {},
        "schema_ok": False,
        "message": "",
    }
    try:
        db.session.execute(db.text("SELECT 1"))
        result["database"] = "connected"
    except Exception as e:
        result["message"] = str(e)
        return jsonify(result), 503

    try:
        r = db.session.execute(db.text("SELECT version_num FROM alembic_version"))
        row = r.fetchone()
        result["migrations_revision"] = row[0] if row else None
        result["checks"]["alembic_version"] = bool(row)
    except Exception as e:
        result["checks"]["alembic_version"] = False
        result["message"] = f"alembic_version: {e}"

    for table in ["estabelecimentos", "venda_itens", "produtos"]:
        try:
            db.session.execute(db.text(f"SELECT 1 FROM {table} LIMIT 1"))
            result["checks"][f"table_{table}"] = True
        except Exception:
            result["checks"][f"table_{table}"] = False

    try:
        db.session.execute(db.text("SELECT margem_lucro_real FROM venda_itens LIMIT 1"))
        result["checks"]["venda_itens.margem_lucro_real"] = True
    except Exception:
        result["checks"]["venda_itens.margem_lucro_real"] = False

    try:
        db.session.execute(db.text("SELECT 1 FROM historico_precos LIMIT 1"))
        result["checks"]["table_historico_precos"] = True
    except Exception:
        result["checks"]["table_historico_precos"] = False

    all_ok = all(result["checks"].get(k) for k in [
        "alembic_version", "table_estabelecimentos", "table_venda_itens",
        "table_produtos", "venda_itens.margem_lucro_real"
    ])
    result["schema_ok"] = all_ok
    if not all_ok:
        result["message"] = "Schema desatualizado. No servidor rode: flask db upgrade"
    return jsonify(result), 200 if result["database"] == "connected" else 503


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
            # TENTATIVA DE AUTO-BOOTSTRAP (Apenas se o banco estiver vazio e for admin)
            try:
                if identifier.lower() == 'admin' and Funcionario.query.first() is None:
                    current_app.logger.info("[LOGIN] Banco vazio detectado. Criando administrador padrão via Auto-Bootstrap...")
                    
                    # Criar estabelecimento padrão se não existir
                    estabelecimento = Estabelecimento.query.first()
                    if not estabelecimento:
                        estabelecimento = Estabelecimento(
                            nome_fantasia="Sistema MercadinhoSys",
                            razao_social="MercadinhoSys LTDA",
                            cnpj="00.000.000/0001-00",
                            telefone="(00) 0000-0000",
                            email="admin@mercadinhosys.com",
                            cep="00000-000",
                            logradouro="Rua do Sistema",
                            numero="0",
                            bairro="Centro",
                            cidade="Cloud",
                            estado="SY",
                            data_abertura=datetime.utcnow().date()
                        )
                        db.session.add(estabelecimento)
                        db.session.flush()

                    admin = Funcionario(
                        estabelecimento_id=estabelecimento.id,
                        nome="Administrador do Sistema",
                        username="admin",
                        email="admin@mercadinhosys.com",
                        cpf="000.000.000-00",
                        data_nascimento=datetime(1990, 1, 1).date(),
                        celular="(00) 00000-0000",
                        cargo="Gerente",
                        data_admissao=datetime.utcnow().date(),
                        role="ADMIN",
                        status="ativo",
                        ativo=True
                    )
                    admin.set_senha("admin123")
                    db.session.add(admin)
                    db.session.commit()
                    
                    # Re-buscar funcionário após bootstrap
                    funcionario = Funcionario.query.filter_by(username='admin').first()
                    current_app.logger.info("[LOGIN] Auto-Bootstrap concluído com sucesso.")
            except Exception as be:
                db.session.rollback()
                current_app.logger.error(f"[LOGIN] Falha crítica no auto-bootstrap: {be}\n{traceback.format_exc()}")

        if not funcionario:
            current_app.logger.warning(
                f"Tentativa de login com credencial não encontrada: {identifier} "
                f"de IP: {ip_address}"
            )

            try:
                login_history.observacoes = "Usuário não encontrado"
                # Tentar encontrar algum estabelecimento para associar
                estabelecimento_default = Estabelecimento.query.first()
                if estabelecimento_default:
                    login_history.estabelecimento_id = estabelecimento_default.id
                db.session.add(login_history)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.warning(f"Não foi possível salvar histórico de login (tabela ausente?): {str(e)}")

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
            try:
                db.session.add(login_history)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.warning(f"Erro ao salvar histórico (senha incorreta): {e}")

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
            try:
                db.session.add(login_history)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.warning(f"Erro ao salvar histórico (conta status): {e}")

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
            try:
                db.session.add(login_history)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.warning(f"Erro ao salvar histórico (conta inativa): {e}")

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

        # Buscar estabelecimento via utilitário safe (blindado contra colunas ausentes)
        from app.utils.query_helpers import get_estabelecimento_safe
        dados_estab = get_estabelecimento_safe(funcionario.estabelecimento_id)

        if not dados_estab:
            login_history.observacoes = "Estabelecimento não encontrado"
            try:
                db.session.add(login_history)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.warning(f"Erro ao salvar histórico (sem estab): {e}")

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
        
        # Simula objeto para compatibilidade downstream se necessário (embora usemos dados_estab direto agora)
        class _EstabProxy:
            pass
        estabelecimento = _EstabProxy()
        for k, v in dados_estab.items():
            setattr(estabelecimento, k, v)

        if not estabelecimento:
            login_history.observacoes = "Estabelecimento não encontrado"
            try:
                db.session.add(login_history)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.warning(f"Erro ao salvar histórico (sem estab): {e}")

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
        try:
            db.session.add(login_history)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.warning(f"Erro ao salvar histórico (sucesso): {e}")

        current_app.logger.info(
            f"Login bem-sucedido: {identifier} ({funcionario.nome}) "
            f"Estabelecimento: {estabelecimento.nome_fantasia} "
            f"de IP: {ip_address}"
        )

        # Monta resposta com campos defensivos para não quebrar se banco estiver desatualizado
        try:
            endereco_str = estabelecimento.endereco_completo()
        except Exception:
            endereco_str = 'Endereço não disponível'

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
                            "telefone": getattr(funcionario, 'telefone', None),
                            "foto_url": getattr(funcionario, 'foto_url', None),
                            "permissoes": getattr(funcionario, 'permissoes', []),
                            "data_admissao": (
                                funcionario.data_admissao.isoformat()
                                if funcionario.data_admissao
                                else None
                            ),
                            "estabelecimento_id": funcionario.estabelecimento_id,
                            "estabelecimento_nome": estabelecimento.nome_fantasia,
                            "created_at": (
                                funcionario.data_cadastro.isoformat()
                                if getattr(funcionario, 'data_cadastro', None)
                                else None
                            ),
                        },
                        "session": {
                            "login_time": additional_claims["login_time"],
                            "expires_in": 28800,
                            "refresh_expires_in": 604800,
                            "token_type": "bearer",
                        },
                        "estabelecimento": {
                            "id": estabelecimento.id,
                            "nome": estabelecimento.nome_fantasia,
                            "cnpj": estabelecimento.cnpj,
                            "telefone": estabelecimento.telefone,
                            "email": estabelecimento.email,
                            "endereco": endereco_str,
                            "cidade": getattr(estabelecimento, 'cidade', ''),
                            "estado": getattr(estabelecimento, 'estado', ''),
                            "plano": getattr(estabelecimento, 'plano', 'Basic'),
                            "plano_status": getattr(estabelecimento, 'plano_status', 'experimental'),
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
            email = "rafaelmaldivas@gmail.com"

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

        # Buscar funcionário de forma safe
        from app.utils.query_helpers import get_funcionario_safe, get_estabelecimento_safe
        funcionario_data = get_funcionario_safe(int(current_user_id))

        if not funcionario_data:
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
        if funcionario_data.get("status") != "ativo" or not funcionario_data.get("ativo"):
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

        # Buscar informações do estabelecimento de forma safe
        estabelecimento_data = get_estabelecimento_safe(funcionario_data.get("estabelecimento_id"))

        # Usar dados do token e do banco
        user_data = {
            "id": int(current_user_id),
            "username": claims.get("username"),
            "nome": claims.get("nome"),
            "estabelecimento_id": claims.get("estabelecimento_id"),
            "estabelecimento_nome": claims.get("estabelecimento_nome"),
            "role": claims.get("role"),
            "status": funcionario_data.get("status"),
            "cargo": claims.get("cargo"),
            "email": funcionario_data.get("email"),
            "foto_url": funcionario_data.get("foto_url"),
            "telefone": funcionario_data.get("telefone"),
            "cpf": funcionario_data.get("cpf"),
            "permissoes": funcionario_data.get("permissoes"),
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

        from app.utils.query_helpers import get_funcionario_safe, get_estabelecimento_safe
        funcionario_data = get_funcionario_safe(int(current_user_id))

        if not funcionario_data:
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

        estabelecimento_data = get_estabelecimento_safe(funcionario_data.get("estabelecimento_id"))

        # Estatísticas do usuário (se aplicável)
        hoje = datetime.utcnow().date()
        total_vendas_hoje = 0
        if hasattr(funcionario, "vendas"):
            total_vendas_hoje = len(
                [v for v in funcionario.vendas if v.data_venda.date() == hoje]
            )

        profile_data = {
            "id": funcionario_data.get("id"),
            "nome": funcionario_data.get("nome"),
            "username": funcionario_data.get("username"),
            "email": funcionario_data.get("email"),
            "cpf": funcionario_data.get("cpf"),
            "telefone": funcionario_data.get("telefone"),
            "foto_url": funcionario_data.get("foto_url"),
            "cargo": funcionario_data.get("cargo"),
            "role": funcionario_data.get("role"),
            "status": funcionario_data.get("status"),
            "ativo": funcionario_data.get("ativo"),
            "data_admissao": (
                funcionario_data.get("data_admissao").isoformat()
                if funcionario_data.get("data_admissao") and hasattr(funcionario_data.get("data_admissao"), "isoformat")
                else funcionario_data.get("data_admissao")
            ),
            "data_demissao": (
                funcionario_data.get("data_demissao").isoformat()
                if funcionario_data.get("data_demissao") and hasattr(funcionario_data.get("data_demissao"), "isoformat")
                else funcionario_data.get("data_demissao")
            ),
            "permissoes": funcionario_data.get("permissoes"),
            "estabelecimento": {
                "id": estabelecimento_data.get("id") if estabelecimento_data else None,
                "nome": estabelecimento_data.get("nome_fantasia") if estabelecimento_data else None,
                "cnpj": estabelecimento_data.get("cnpj") if estabelecimento_data else None,
                "telefone": estabelecimento_data.get("telefone") if estabelecimento_data else None,
                "email": estabelecimento_data.get("email") if estabelecimento_data else None,
                "endereco": estabelecimento_data.get("logradouro") if estabelecimento_data else None,
                "cidade": estabelecimento_data.get("cidade") if estabelecimento_data else None,
                "estado": estabelecimento_data.get("estado") if estabelecimento_data else None,
            },
            "permissions": get_permissions_for_role(
                funcionario_data.get("role"), funcionario_data.get("permissoes")
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
        query = query.order_by(LoginHistory.data_cadastro.desc())

        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        sessoes = paginacao.items

        resultado = []
        for sessao in sessoes:
            resultado.append(
                {
                    "id": sessao.id,
                    "login_time": sessao.data_cadastro.isoformat(),
                    "ip_address": sessao.ip_address,
                    "dispositivo": sessao.dispositivo,
                    "success": sessao.success,
                    "observacoes": sessao.observacoes,
                    "duracao_minutos": None,
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
    permissions = role_permissions.get(role_key, ["view_products", "view_clients"])

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


@auth_bp.route("/demo", methods=["POST"])
def guest_demo():
    """Access the system in demo mode with a single click"""
    try:
        from datetime import date
        from werkzeug.security import generate_password_hash
        
        # 1. Encontrar ou criar o estabelecimento demo
        demo_est = Estabelecimento.query.filter_by(cnpj="00.000.000/0000-00").first()
        if not demo_est:
            demo_est = Estabelecimento(
                nome_fantasia="Supermercado Fictício (Demo)",
                razao_social="Demo Mercadinho Sys LTDA",
                cnpj="00.000.000/0000-00",
                telefone="(11) 99999-9999",
                email="demo@mercadinhosys.com",
                data_abertura=date(2020, 1, 1),
                cep="01001-000",
                logradouro="Praça da Sé",
                numero="1",
                bairro="Sé",
                cidade="São Paulo",
                estado="SP",
                plano="Advanced",
                plano_status="active"
            )
            db.session.add(demo_est)
            db.session.flush() # Pegar ID

        # 2. Encontrar ou criar o admin demo
        demo_admin = Funcionario.query.filter_by(estabelecimento_id=demo_est.id, username="demo").first()
        if not demo_admin:
            demo_admin = Funcionario(
                estabelecimento_id=demo_est.id,
                nome="Administrador Demo",
                cpf="000.000.000-00",
                data_nascimento=date(1990, 1, 1),
                celular="(11) 99999-9999",
                email="demo@mercadinhosys.com",
                cargo="admin",
                data_admissao=date(2020, 1, 1),
                username="demo",
                senha_hash=generate_password_hash("demo123"),
                ativo=True
            )
            db.session.add(demo_admin)
            db.session.commit()

        # 3. Gerar tokens
        access_token = create_access_token(identity=demo_admin.id)
        refresh_token = create_refresh_token(identity=demo_admin.id)

        # 4. Registrar histórico
        try:
            history = LoginHistory(
                funcionario_id=demo_admin.id,
                username=demo_admin.username,
                estabelecimento_id=demo_est.id,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                success=True,
                observacoes="Acesso via Modo Demo Instantâneo"
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e:
            current_app.logger.warning(f"Erro ao registrar histórico demo: {e}")
            db.session.rollback()

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": demo_admin.id,
                "nome": demo_admin.nome,
                "cargo": demo_admin.cargo,
                "estabelecimento": demo_est.nome_fantasia,
                "estabelecimento_id": demo_est.id,
                "is_demo": True
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no Login Demo: {traceback.format_exc()}")
        return jsonify({
            "error": "Falha ao acessar modo demo",
            "details": str(e),
            "code": "DEMO_ACCESS_ERROR"
        }), 500
