import logging
import os

logger = logging.getLogger(__name__)

class EmailService:
    """
    Serviço centralizado para envio de comunicações por e-mail.
    Atualmente suporta simulação em log e preparação para SendGrid.
    """
    
    @staticmethod
    def send_welcome_email(to_email, nome_usuario):
        """
        Envia e-mail de boas-vindas para novos leads ou usuários.
        """
        subject = f"Bem-vindo ao MercadinhoSys, {nome_usuario}!"
        
        # Template simplificado (pode ser expandido com HTML profissional)
        content = f"""
        Olá {nome_usuario},
        
        Obrigado pelo seu interesse no MercadinhoSys!
        
        Nossa equipe recebeu sua solicitação e entrará em contato em breve via WhatsApp para agendar uma demonstração personalizada.
        
        Enquanto isso, você pode conhecer mais sobre nossas funcionalidades em nosso site.
        
        Atenciosamente,
        Equipe MercadinhoSys
        """
        
        # Simulação de envio (Iniciando infraestrutura)
        # TODO: Integrar com SendGrid ou SMTP futuramente
        logger.info(f"📧 [EMAIL SIMULADO] Enviando para: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {content[:100]}...")
        
        # Aqui entraria a lógica real do SendGrid:
        # sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        # response = sg.send(message)
        
        return True

    @staticmethod
    def send_payment_confirmation(to_email, plano_nome):
        """
        Confirmação de ativação de plano SaaS.
        """
        logger.info(f"📧 [EMAIL SIMULADO] Confirmação de pagamento para {to_email} - Plano {plano_nome}")
        return True

email_service = EmailService()
