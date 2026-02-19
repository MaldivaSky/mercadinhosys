import stripe
import os
from flask import url_for
from app.models import Estabelecimento, db
from datetime import datetime

class StripeService:
    def __init__(self):
        secret_key = os.getenv('STRIPE_SECRET_KEY')
        if not secret_key:
            raise RuntimeError(
                "STRIPE_SECRET_KEY não está configurado. "
                "Adicione esta variável no arquivo .env ou no Render Dashboard."
            )
        stripe.api_key = secret_key
        self.publishable_key = os.getenv('STRIPE_PUBLIC_KEY', '')
        # Preços em centavos (BRL) por plano
        self.PLAN_PRICES = {
            'Basic': 2990,      # R$ 29,90/mês
            'Premium': 6990,    # R$ 69,90/mês
            'Enterprise': 9990  # R$ 99,90/mês
        }

    def create_checkout_session(self, estabelecimento_id, plan_name, user_email):
        """
        Cria uma sessão de Checkout no Stripe para assinatura.
        """
        try:
            estab = Estabelecimento.query.get(estabelecimento_id)
            if not estab:
                raise Exception("Estabelecimento não encontrado")

            # Criar ou recuperar cliente no Stripe
            customer_id = self._get_or_create_customer(estab, user_email)

            # Definir preço (Hardcoded para teste se não tiver IDs reais ainda)
            # Em produção, usaríamos os IDs de preço reais do Stripe Dashboard
            # Para teste rápido, podemos criar "on the fly" ou usar IDs fixos
            
            # URL de retorno
            # Frontend URL (Vite)
            success_url = os.getenv('FRONTEND_URL', 'http://localhost:5173') + '/configuracoes?session_id={CHECKOUT_SESSION_ID}&status=success'
            cancel_url = os.getenv('FRONTEND_URL', 'http://localhost:5173') + '/configuracoes?status=canceled'

            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card', 'boleto'], # Pix precisa de configuração extra no dashboard, boleto é nativo
                line_items=[
                    {
                        # Para teste dinâmico. O ideal é usar price_id
                        'price_data': {
                            'currency': 'brl',
                            'product_data': {
                                'name': f'Plano {plan_name}',
                            },
                            'unit_amount': self._get_price_amount(plan_name),
                            'recurring': {
                                'interval': 'month',
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'estabelecimento_id': estabelecimento_id,
                    'plan_name': plan_name
                }
            )
            return checkout_session.url
        except Exception as e:
            print(f"Erro ao criar checkout: {str(e)}")
            raise e

    def _get_or_create_customer(self, estab, email):
        if estab.stripe_customer_id:
            return estab.stripe_customer_id
        
        customer = stripe.Customer.create(
            email=email,
            name=estab.nome_fantasia,
            metadata={'estabelecimento_id': estab.id}
        )
        
        estab.stripe_customer_id = customer.id
        db.session.commit()
        return customer.id

    def _get_price_amount(self, plan_name):
        return self.PLAN_PRICES.get(plan_name, 2990)

    def handle_webhook(self, payload, sig_header):
        """
        Processa eventos do Webhook do Stripe
        """
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise Exception("Invalid signature")

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self._handle_checkout_completed(session)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            self._handle_invoice_paid(invoice)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            self._handle_subscription_deleted(subscription)

        return True

    def _handle_checkout_completed(self, session):
        # Ativar assinatura após checkout com sucesso
        estabelecimento_id = session['metadata'].get('estabelecimento_id')
        plan_name = session['metadata'].get('plan_name')
        subscription_id = session.get('subscription')
        
        if estabelecimento_id:
            estab = Estabelecimento.query.get(estabelecimento_id)
            if estab:
                estab.plano = plan_name
                estab.plano_status = 'ativo'
                estab.stripe_subscription_id = subscription_id
                # Data de vencimento será atualizada no invoice.payment_succeeded
                db.session.commit()

    def _handle_invoice_paid(self, invoice):
        # Atualizar validade
        subscription_id = invoice.get('subscription')
        # Buscar estabelecimento pelo subscription_id
        estab = Estabelecimento.query.filter_by(stripe_subscription_id=subscription_id).first()
        
        if estab:
            # period_end é timestamp unix
            period_end = invoice['lines']['data'][0]['period']['end']
            estab.vencimento_assinatura = datetime.fromtimestamp(period_end)
            estab.plano_status = 'ativo'
            db.session.commit()

    def _handle_subscription_deleted(self, subscription):
        # Assinatura cancelada
        subscription_id = subscription.get('id')
        estab = Estabelecimento.query.filter_by(stripe_subscription_id=subscription_id).first()
        
        if estab:
            estab.plano_status = 'canceled'
            db.session.commit()
