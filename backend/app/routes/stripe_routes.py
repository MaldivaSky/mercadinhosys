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
        # JWT identity é string com o ID do funcionário (ex: "1")
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        data = request.get_json() or {}
        plan_name = data.get('plan_name', 'Basic')

        # Buscar estabelecimento_id primeiro via JWT claims (mais eficiente)
        estabelecimento_id = claims.get('estabelecimento_id')

        if not estabelecimento_id:
            # Fallback: buscar via Funcionario
            funcionario = Funcionario.query.get(int(current_user_id))
            if not funcionario:
                return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
            estabelecimento_id = funcionario.estabelecimento_id
            user_email = funcionario.email
        else:
            # Buscar email do funcionário
            funcionario = Funcionario.query.get(int(current_user_id))
            user_email = funcionario.email if funcionario else claims.get('email', '')

        estab = Estabelecimento.query.get(estabelecimento_id)
        if not estab:
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
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        estabelecimento_id = claims.get('estabelecimento_id')
        if not estabelecimento_id:
            funcionario = Funcionario.query.get(int(current_user_id))
            if not funcionario:
                return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
            estabelecimento_id = funcionario.estabelecimento_id

        estab = Estabelecimento.query.get(estabelecimento_id)
        if not estab or not estab.stripe_customer_id:
            return jsonify({'success': False, 'message': 'Nenhuma assinatura Stripe ativa encontrada'}), 404

        import os
        import stripe as stripe_lib
        stripe_lib.api_key = os.getenv('STRIPE_SECRET_KEY')

        return_url = os.getenv('FRONTEND_URL', 'http://localhost:5173') + '/configuracoes'
        portal_session = stripe_lib.billing_portal.Session.create(
            customer=estab.stripe_customer_id,
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
