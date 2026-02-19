from flask import Blueprint, request, jsonify
from app.services.stripe_service import StripeService
from app.models import Estabelecimento, db
from flask_jwt_extended import jwt_required, get_jwt_identity

stripe_bp = Blueprint('stripe_bp', __name__, url_prefix='/api/stripe')
stripe_service = StripeService()

@stripe_bp.route('/checkout', methods=['POST'])
@jwt_required()
def create_checkout():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        plan_name = data.get('plan_name')
        
        # Buscar estabelecimento do usuário
        # Assumindo que o usuário logado é admin de um estabelecimento
        # Na estrutura atual, o user_id é do Funcionario, precisamos achar o Estabelecimento
        from app.models import Funcionario
        funcionario = Funcionario.query.get(current_user_id)
        
        if not funcionario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
            
        checkout_url = stripe_service.create_checkout_session(
            estabelecimento_id=funcionario.estabelecimento_id,
            plan_name=plan_name,
            user_email=funcionario.email
        )
        
        return jsonify({'success': True, 'checkout_url': checkout_url})
    except Exception as e:
        print(f"Erro no checkout: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@stripe_bp.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        stripe_service.handle_webhook(payload, sig_header)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'failure', 'error': str(e)}), 400
