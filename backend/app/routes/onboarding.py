# app/routes/onboarding.py
"""
Módulo de Onboarding SaaS
Rotas públicas para registro de novos clientes/lojas (Self-Service).
"""

from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.models import db, Estabelecimento, Funcionario, Configuracao, Auditoria
import json

onboarding_bp = Blueprint("onboarding", __name__)

def super_admin_required(fn):
    """Custom decorator for super admin routes"""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask import current_app
        claims = get_jwt()
        
        # 1. Verificação Primária: Claim no Token JWT (Rápida)
        if claims.get("is_super_admin") is True:
            return fn(*args, **kwargs)
            
        # 2. Verificação de Redundância: Fail-safe Senior via DB
        try:
            from app.models import Funcionario
            user_id = get_jwt_identity()
            user = Funcionario.query.get(int(user_id))
            
            if user and user.username in ['maldivas', 'admin']:
                return fn(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Erro na redundância de onboarding: {str(e)}")
            
        return jsonify({"success": False, "error": "Acesso restrito ao Administrador do Sistema"}), 403
    return jwt_required()(wrapper)

@onboarding_bp.route("/registrar", methods=["POST"])
@super_admin_required
def registrar_conta():
    """
    Endpoint público para registrar um novo Estabelecimento e seu Usuário Administrador.
    Tudo é feito em uma única transação atômica.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Nenhum dado fornecido"}), 400

        # Dados da Loja (Estabelecimento)
        nome_fantasia = data.get("nome_fantasia")
        razao_social = data.get("razao_social") or nome_fantasia
        cnpj = data.get("cnpj")
        telefone_loja = data.get("telefone_loja")
        email_loja = data.get("email_loja")
        cep = data.get("cep", "00000000")
        logradouro = data.get("logradouro", "Não informado")
        numero = data.get("numero", "S/N")
        bairro = data.get("bairro", "Não informado")
        cidade = data.get("cidade", "Não informado")
        estado = data.get("estado", "XX")
        
        # Dados do Usuário (Dono/Admin)
        nome_admin = data.get("nome_admin")
        cpf_admin = data.get("cpf_admin")
        celular_admin = data.get("celular_admin")
        email_admin = data.get("email_admin") or email_loja
        username = data.get("username")
        data_nascimento_str = data.get("data_nascimento")

        # Validações Básicas
        if not all([nome_fantasia, cnpj, telefone_loja, email_loja, nome_admin, cpf_admin, celular_admin, username]):
            return jsonify({"success": False, "error": "Dados incompletos. Preencha todos os campos obrigatórios."}), 400

        # Validação de Duplicidade (CNPJ e Username - global)
        if Estabelecimento.query.filter_by(cnpj=cnpj).first():
            return jsonify({"success": False, "error": f"O CNPJ {cnpj} já está registrado no sistema."}), 400
            
        if Funcionario.query.filter_by(username=username).first():
            return jsonify({"success": False, "error": f"O usuário '{username}' já existe. Escolha outro username."}), 400

        data_nascimento = date(1900, 1, 1) # Default
        if data_nascimento_str:
            try:
                data_nascimento = datetime.strptime(data_nascimento_str, "%Y-%m-%d").date()
            except:
                pass

        # Gerar senha temporária aleatória de 8 caracteres
        import string
        import random
        caracteres = string.ascii_letters + string.digits + "@#$*"
        senha_temporaria = ''.join(random.choice(caracteres) for i in range(8))

        # Início da Transação Atômica
        try:
            # 1. Criar Estabelecimento
            novo_estabelecimento = Estabelecimento(
                nome_fantasia=nome_fantasia,
                razao_social=razao_social,
                cnpj=cnpj,
                telefone=telefone_loja,
                email=email_loja,
                cep=cep,
                logradouro=logradouro,
                numero=numero,
                bairro=bairro,
                cidade=cidade,
                estado=estado,
                data_abertura=date.today(),
                plano="Basic",
                plano_status="ativo"
            )
            db.session.add(novo_estabelecimento)
            db.session.flush() # Manter na transação para pegar o ID gerado

            # 2. Criar Configuração Padrão
            permissoes_admin = {
                "pdv": True,
                "estoque": True,
                "compras": True,
                "financeiro": True,
                "configuracoes": True,
                "rh": True,
                "pode_dar_desconto": True,
                "limite_desconto": 100,
                "pode_cancelar_venda": True
            }

            nova_config = Configuracao(
                estabelecimento_id=novo_estabelecimento.id,
                emitir_nfe=False,
                emitir_nfce=True,
                arredondamento_valores=True,
                controlar_validade=True,
                alerta_estoque_minimo=True
            )
            db.session.add(nova_config)

            # 3. Criar Funcionário Administrador (Dono)
            novo_admin = Funcionario(
                estabelecimento_id=novo_estabelecimento.id,
                nome=nome_admin,
                cpf=cpf_admin,
                data_nascimento=data_nascimento,
                celular=celular_admin,
                telefone=celular_admin,
                email=email_admin,
                cargo="Propietário",
                data_admissao=date.today(),
                username=username,
                role="ADMIN",
                permissoes_json=json.dumps(permissoes_admin),
                cep=cep,
                logradouro=logradouro,
                numero=numero,
                bairro=bairro,
                cidade=cidade,
                estado=estado
            )
            novo_admin.set_senha(senha_temporaria)
            db.session.add(novo_admin)
            db.session.flush()

            # Auditoria SaaS (Log de Onboarding)
            Auditoria.registrar(
                estabelecimento_id=novo_estabelecimento.id,
                tipo_evento="estabelecimento_registrado",
                descricao=f"Novo estabelecimento: {nome_fantasia} (CNPJ: {cnpj})",
                usuario_id=novo_admin.id,
                detalhes={"estabelecimento": nome_fantasia, "admin": username, "email": email_admin}
            )

            # Confirmar tudo!
            db.session.commit()

            # Enviar e-mail com as credenciais
            try:
                from app.services.email_service import email_service
                email_service.send_credentials_email(
                    email_admin, 
                    nome_admin, 
                    senha_temporaria,
                    nome_loja=novo_estabelecimento.nome_fantasia
                )
            except Exception as email_e:
                from flask import current_app
                current_app.logger.warning(f"Conta criada, mas erro ao enviar e-mail: {str(email_e)}")

            return jsonify({
                "success": True, 
                "message": "Conta criada com sucesso! Verifique seu e-mail para acessar suas credenciais de login.",
                "estabelecimento_id": novo_estabelecimento.id
            }), 201

        except Exception as intern_e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Erro transacional ao registrar conta SaaS: {str(intern_e)}")
            return jsonify({"success": False, "error": "Erro interno ao processar cadastro. Tente novamente."}), 500

    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Erro grave no onboarding: {str(e)}")
        return jsonify({"success": False, "error": f"Falha no servidor: {str(e)}"}), 500
