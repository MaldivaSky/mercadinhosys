import os
from flask import current_app
from app.models import Estabelecimento, db
from datetime import datetime, timedelta, timezone
from efipay import EfiPay

class BillingService:
    def __init__(self):
        is_sandbox = os.getenv('EFI_ENV', 'sandbox') == 'sandbox'
        
        client_id = os.getenv('EFI_CLIENT_ID_HOMOL') if is_sandbox else os.getenv('EFI_CLIENT_ID_PROD')
        client_secret = os.getenv('EFI_CLIENT_SECRET_HOMOL') if is_sandbox else os.getenv('EFI_CLIENT_SECRET_PROD')
        cert_path = os.getenv('EFI_CERT_HOMOL') if is_sandbox else os.getenv('EFI_CERT_PROD')
        
        if not client_id or not client_secret:
            raise RuntimeError("As chaves da Efí (EFI_CLIENT_ID / EFI_CLIENT_SECRET) não estão configuradas no .env para este ambiente.")

        self.options = {
            'client_id': client_id,
            'client_secret': client_secret,
            'sandbox': is_sandbox,
            # 'certificate': os.path.abspath(cert_path) if cert_path and os.path.exists(cert_path) else None
        }

        self.efi = EfiPay(self.options)
        
        self.PLAN_PRICES = {
            'Premium': 9990,     # R$ 99,90/mês
            'Basic': 4990        # R$ 49,90/mês
        }

    def _get_price_amount(self, plan_name):
        return self.PLAN_PRICES.get(plan_name, 9990)

    def create_checkout_session(self, estabelecimento_id, plan_name, user_email):
        try:
            estab = Estabelecimento.query.get(estabelecimento_id)
            if not estab:
                raise Exception("Estabelecimento não encontrado")

            price = self._get_price_amount(plan_name)
            
            # Tentar criar um Plano de Assinatura Recorrente (Efí Assinaturas)
            try:
                plan_body = {
                    "name": f"Assinatura {plan_name} - MercadinhoSys",
                    "repeats": 0, # 0 = indefinido (cobrança recorrente mensal)
                    "interval": 1
                }
                plan_response = self.efi.create_plan(body=plan_body)
                if plan_response.get('code') != 200:
                    raise Exception("Falha ao criar plano")
                
                plan_id = plan_response['data']['plan_id']
                
                link_body = {
                    "items": [
                        {
                            "name": f"Mensalidade - {plan_name}",
                            "value": price,
                            "amount": 1
                        }
                    ],
                    "settings": {
                        "payment_method": "all",
                        "expire_at": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                        "request_delivery_address": False
                    },
                    "metadata": {
                        "custom_id": str(estabelecimento_id),
                        "notification_url": os.getenv('BACKEND_URL', 'https://mercadinhosys.herokuapp.com') + '/api/billing/webhook'
                    }
                }
                charge = self.efi.create_one_step_subscription_link(params={"id": plan_id}, body=link_body)
                
            except Exception as plan_err:
                current_app.logger.warning(f"Fallback para cobrança avulsa (Efí): {plan_err}")
                # Fallback para one-step link avulso
                body = {
                    "items": [
                        {
                            "name": f"Assinatura Plano {plan_name} - 1 Mês",
                            "value": price,
                            "amount": 1
                        }
                    ],
                    "settings": {
                        "message": f"Assinatura MercadinhoSys - {plan_name}",
                        "expire_at": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                        "request_delivery_address": False,
                        "payment_method": "pix,credit_card"
                    },
                    "metadata": {
                        "custom_id": str(estabelecimento_id),
                        "notification_url": os.getenv('BACKEND_URL', 'https://mercadinhosys.herokuapp.com') + '/api/billing/webhook'
                    }
                }
                charge = self.efi.create_one_step_link(body=body)

            if isinstance(charge, str) or charge.get('code') != 200:
                raise Exception(f"Erro ao gerar link de pagamento Efí (Verifique suas Credenciais): {charge}")

            charge_id = charge['data']['charge_id']
            
            # Update gateway info on estab
            estab.gateway_subscription_id = str(charge_id)
            estab.plano = plan_name
            db.session.commit()

            return charge['data']['payment_url']

        except Exception as e:
            current_app.logger.error(f"Erro no BillingService: {str(e)}")
            raise e

    def handle_webhook(self, notification_token):
        """
        Consulta os detalhes da notificação na Efí e processa o pagamento
        """
        try:
            params = { "token": notification_token }
            notification = self.efi.get_notification(params=params)

            if notification.get('code') != 200:
                return False

            for event in notification.get('data', []):
                if event.get('type') == 'charge':
                    status = event.get('status', {}).get('current')
                    charge_id = event.get('identifiers', {}).get('charge_id')
                    
                    if status == 'paid' or status == 'settled':
                        self._handle_charge_paid(charge_id)
                    elif status == 'canceled' or status == 'unpaid':
                        self._handle_charge_canceled(charge_id)

            return True
        except Exception as e:
            current_app.logger.error(f"Erro ao processar webhook da Efí: {str(e)}")
            raise e

    def _handle_charge_paid(self, charge_id):
        estab = Estabelecimento.query.filter_by(gateway_subscription_id=str(charge_id)).first()
        if estab:
            # Assinatura mensal, renova por 30 dias a partir de hoje
            estab.vencimento_assinatura = datetime.now(timezone.utc) + timedelta(days=30)
            estab.plano_status = 'ativo'
            db.session.commit()
            current_app.logger.info(f"Estabelecimento {estab.id} ativado via webhook Efí.")

    def _handle_charge_canceled(self, charge_id):
        estab = Estabelecimento.query.filter_by(gateway_subscription_id=str(charge_id)).first()
        if estab:
            estab.plano_status = 'cancelado'
            db.session.commit()
            current_app.logger.info(f"Estabelecimento {estab.id} cancelado via webhook Efí.")
