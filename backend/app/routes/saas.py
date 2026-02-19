from flask import Blueprint, request, jsonify, current_app
from app.models import db, Lead, Estabelecimento
from app.decorators.decorator_jwt import admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
import logging
from app.services.email_service import email_service

saas_bp = Blueprint("saas", __name__)
logger = logging.getLogger(__name__)

# ==================== LEAD MANAGEMENT ====================

@saas_bp.route("/leads/registrar", methods=["POST"])
def registrar_lead():
    """
    Captura leads do formulário da Landing Page
    """
    try:
        data = request.get_json()
        if not data or not data.get("email"):
            return jsonify({
                "success": False, 
                "error": "Dados incompletos", 
                "message": "Nome e WhatsApp são recomendados, mas Email é obrigatório."
            }), 400
        
        # Verificar duplicados recentemente (opcional, mas bom para evitar spam)
        # Por enquanto, apenas registramos
        
        novo_lead = Lead(
            nome=data.get("nome", "Interessado"),
            email=data.get("email"),
            whatsapp=data.get("whatsapp", ""),
            origem=data.get("origem", "landing_page"),
            observacao=data.get("mensagem", "")
        )
        db.session.add(novo_lead)
        db.session.commit()
        
        logger.info(f"🆕 NOVO LEAD: {novo_lead.email} ({novo_lead.nome})")
        
        # Enviar email de boas-vindas (assíncrono futuramente)
        try:
            email_service.send_welcome_email(novo_lead.email, novo_lead.nome)
        except Exception as e:
            logger.error(f"Erro ao disparar email de boas-vindas: {e}")
        
        return jsonify({
            "success": True, 
            "message": "Obrigado pelo interesse! Nossa equipe entrará em contato em breve."
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao registrar lead: {e}")
        return jsonify({"success": False, "error": "Erro ao processar sua solicitação"}), 500


@saas_bp.route("/leads", methods=["GET"])
@admin_required
def listar_leads():
    """
    Lista todos os leads capturados (Apenas para Admin)
    """
    try:
        leads = Lead.query.order_by(Lead.data_cadastro.desc()).all()
        return jsonify({
            "success": True,
            "count": len(leads),
            "data": [lead.to_dict() for lead in leads]
        }), 200
    except Exception as e:
        logger.error(f"Erro ao listar leads: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== SUBSCRIPTION & PAYMENTS ====================

@saas_bp.route("/assinatura/status", methods=["GET"])
@jwt_required()
def get_assinatura_status():
    """
    Retorna o status do plano do estabelecimento atual
    """
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        
        if not estabelecimento_id:
            return jsonify({"success": False, "error": "Estabelecimento não identificado"}), 400
            
        estabelecimento = Estabelecimento.query.get(estabelecimento_id)
        if not estabelecimento:
            return jsonify({"success": False, "error": "Estabelecimento não encontrado"}), 404
            
        return jsonify({
            "success": True,
            "data": {
                "plano": estabelecimento.plano,
                "status": estabelecimento.plano_status,
                "vencimento": estabelecimento.vencimento_assinatura.isoformat() if estabelecimento.vencimento_assinatura else None,
                "is_active": estabelecimento.plano_status in ["ativo", "experimental"]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar status de assinatura: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@saas_bp.route("/assinatura/webhook", methods=["POST"])
def pagarme_webhook():
    """
    Recebe notificações de pagamento do Pagar.me
    """
    try:
        # Pagar.me envia o payload no body
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Payload vazio"}), 400
            
        logger.info(f"💰 WEBHOOK PAGAR.ME: Evento {data.get('type')} recebido.")
        
        # TODO: Implementar lógica de validação de assinatura X-PagarMe-Signature
        # TODO: Processar eventos de subscription_updated, transaction_paid, etc.
        
        # Exemplo de lógica para 'subscription_updated' ou 'paid'
        # Se evento for de pagamento confirmado:
        #   1. Identificar estabelecimento via metadata ou pagarme_id
        #   2. Atualizar plano_status para 'ativo'
        #   3. Estender vencimento_assinatura
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook Pagar.me: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
