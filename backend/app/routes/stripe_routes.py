from flask import Blueprint, request, jsonify
from app.services.stripe_service import StripeService
from app.models import Estabelecimento, Funcionario, db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import logging

logger = logging.getLogger(__name__)

stripe_bp = Blueprint('stripe_bp', __name__, url_prefix='/api/stripe')


def _get_stripe_service():
    """Instancia StripeService por request para evitar falha no import se chave não estiver configurada."""
    return StripeService()


@stripe_bp.route('/checkout', methods=['POST'])
@jwt_required()
def create_checkout():
    try:
        from app.utils.query_helpers import get_estabelecimento_safe, get_funcionario_safe
        
        # JWT identity é string com o ID do funcionário (ex: "1")
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        data = request.get_json() or {}
        plan_name = data.get('plan_name', 'Basic')

        # Buscar estabelecimento_id primeiro via JWT claims (mais eficiente)
        estabelecimento_id = claims.get('estabelecimento_id')

        if not estabelecimento_id:
            # Fallback safe: buscar via Funcionario
            funcionario_data = get_funcionario_safe(int(current_user_id))
            if not funcionario_data:
                return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
            estabelecimento_id = funcionario_data.get('estabelecimento_id')
            user_email = funcionario_data.get('email')
        else:
            # Buscar email do funcionário de forma safe
            funcionario_data = get_funcionario_safe(int(current_user_id))
            user_email = funcionario_data.get('email') if funcionario_data else claims.get('email', '')

        # Busca estabelecimento de forma safe (blindado contra colunas ausentes)
        estab_data = get_estabelecimento_safe(estabelecimento_id)
        if not estab_data:
            return jsonify({'success': False, 'message': 'Estabelecimento não encontrado'}), 404

        stripe_svc = _get_stripe_service()
        checkout_url = stripe_svc.create_checkout_session(
            estabelecimento_id=estabelecimento_id,
            plan_name=plan_name,
            user_email=user_email
        )

        return jsonify({'success': True, 'checkout_url': checkout_url})

    except Exception as e:
        logger.error(f"Erro no checkout Stripe: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro ao iniciar checkout: {str(e)}'}), 500


@stripe_bp.route('/public-checkout', methods=['POST'])
def public_checkout():
    """
    Cria uma conta e inicia o checkout para novos clientes da Landing Page.
    """
    try:
        from app.models import Estabelecimento, Funcionario, db
        from datetime import datetime

        data = request.get_json() or {}
        email = data.get('email')
        whatsapp = data.get('whatsapp')
        nome_loja = data.get('nome_loja')
        plan_name = data.get('plan_name', 'Basic')

        if not email or not nome_loja:
            return jsonify({'success': False, 'message': 'Email e nome da loja são obrigatórios'}), 400

        # 1. Verificar se usuário já existe
        if Funcionario.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Este e-mail já está cadastrado. Por favor, faça login.'}), 409

        # 2. Criar Estabelecimento
        novo_estab = Estabelecimento(
            nome_fantasia=nome_loja,
            razao_social=nome_loja,
            cnpj="00.000.000/0001-00", # Placeholder
            telefone=whatsapp or "(00) 0000-0000",
            email=email,
            cep="00000-000",           # Placeholder
            logradouro="Pendente",     # Placeholder
            numero="0",                # Placeholder
            bairro="Pendente",         # Placeholder
            cidade="Pendente",         # Placeholder
            estado="AM",               # Placeholder (Amazonas, target region)
            plano=plan_name,
            plano_status='pendente',
            data_abertura=datetime.utcnow().date()
        )
        db.session.add(novo_estab)
        db.session.flush()

        # 3. Criar Funcionario Admin
        novo_admin = Funcionario(
            estabelecimento_id=novo_estab.id,
            nome="Proprietário",
            username=email.split('@')[0],
            email=email,
            cpf="000.000.000-00",        # Placeholder
            data_nascimento=datetime(1990, 1, 1).date(), # Placeholder
            celular=whatsapp or "(00) 00000-0000",
            role="ADMIN",
            cargo="Gerente",
            status="ativo",
            ativo=True,
            data_admissao=datetime.utcnow().date(),
            cep="00000-000",             # Placeholder
            logradouro="Pendente",       # Placeholder
            numero="0",                  # Placeholder
            bairro="Pendente",           # Placeholder
            cidade="Pendente",           # Placeholder
            estado="AM"                  # Placeholder
        )
        novo_admin.set_senha("Trocar@123")
        db.session.add(novo_admin)
        db.session.commit()
        
        # 4. Notificar Lead (Log & Email)
        logger.info(f"📍 NOVO LEAD CAPTURADO NO CHECKOUT: {email} | Loja: {nome_loja} | WhatsApp: {whatsapp}")
        try:
            from app.services.email_service import email_service
            email_service.send_welcome_email(email, "Proprietário")
        except Exception as email_err:
            logger.error(f"Não foi possível enviar email de boas-vindas para o lead: {email_err}")

        # 5. Iniciar Checkout Stripe
        stripe_svc = _get_stripe_service()
        checkout_url = stripe_svc.create_checkout_session(
            estabelecimento_id=novo_estab.id,
            plan_name=plan_name,
            user_email=email
        )

        return jsonify({
            'success': True, 
            'checkout_url': checkout_url,
            'message': 'Conta criada. Redirecionando para o pagamento seguro.'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro no public-checkout: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro ao processar: {str(e)}'}), 500


@stripe_bp.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        stripe_svc = _get_stripe_service()
        stripe_svc.handle_webhook(payload, sig_header)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Erro no webhook Stripe: {str(e)}")
        return jsonify({'status': 'failure', 'error': str(e)}), 400


@stripe_bp.route('/portal', methods=['POST'])
@jwt_required()
def customer_portal():
    """Redireciona para o portal do cliente Stripe para gerenciar assinatura."""
    try:
        from app.utils.query_helpers import get_estabelecimento_safe, get_funcionario_safe
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        estabelecimento_id = claims.get('estabelecimento_id')
        if not estabelecimento_id:
            funcionario_data = get_funcionario_safe(int(current_user_id))
            if not funcionario_data:
                return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
            estabelecimento_id = funcionario_data.get('estabelecimento_id')

        estab_data = get_estabelecimento_safe(estabelecimento_id)
        if not estab_data or not estab_data.get('stripe_customer_id'):
            # Tenta buscar o stripe_customer_id isoladamente se não veio no safe (pode ser coluna nova que falhou no fetch_col generico)
            # Mas o get_estabelecimento_safe já tenta isso.
            return jsonify({'success': False, 'message': 'Nenhuma assinatura Stripe ativa encontrada'}), 404

        import os
        import stripe as stripe_lib
        stripe_lib.api_key = os.getenv('STRIPE_SECRET_KEY')

        return_url = os.getenv('FRONTEND_URL', 'http://localhost:5173') + '/configuracoes'
        portal_session = stripe_lib.billing_portal.Session.create(
            customer=estab_data.get('stripe_customer_id'),
            return_url=return_url,
        )
        return jsonify({'success': True, 'portal_url': portal_session.url})

    except Exception as e:
        logger.error(f"Erro no portal Stripe: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@stripe_bp.route('/config', methods=['GET'])
def get_config():
    """Retorna a chave pública do Stripe para o frontend."""
    import os
    pk = os.getenv('STRIPE_PUBLIC_KEY', '')
    return jsonify({'publishable_key': pk})
