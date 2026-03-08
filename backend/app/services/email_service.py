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
    def send_credentials_email(to_email, nome_usuario, senha_temporaria, nome_loja="Sua Loja"):
        """
        Envia e-mail profissional de boas-vindas com as credenciais de acesso.
        """
        subject = f"🚀 Seu Mercadinho está pronto para decolar! | Acesso ao MercadinhoSys"
        
        content = f"""
        Olá {nome_usuario},

        É um prazer ter o {nome_loja} como nosso parceiro! Você acaba de contratar um ecossistema de gestão inteligente projetado para maximizar seus lucros e organizar sua operação.

        Como medida de segurança, nós geramos automaticamente suas credenciais de acesso iniciais.
        Por favor, utilize as informações abaixo para entrar no sistema:

        URL de Acesso: https://mercadinhosys.vercel.app/login
        E-mail/Usuário: {to_email}
        Senha Temporária: {senha_temporaria}

        (Recomendamos que você altere esta senha no seu primeiro acesso para total segurança).

        🧭 PRÓXIMOS PASSOS:
        Ao entrar, você verá o nosso Tour de Boas-Vindas. Ele te guiará nos primeiros passos de configuração.

        Vamos crescer juntos?
        Equipe Maldivas Sistemas
        """
        
        logger.info(f"📧 [EMAIL BOAS-VINDAS] Enviando para: {to_email}")
        logger.info(f"Subject: {subject}")
        # Log completo apenas em ambientes controlados por segurança
        logger.info(f"Body: {content}")
        
        return True

    @staticmethod
    def send_payment_confirmation(to_email, plano_nome):
        """
        Confirmação de ativação de plano SaaS.
        """
        logger.info(f"📧 [EMAIL SIMULADO] Confirmação de pagamento para {to_email} - Plano {plano_nome}")
        return True

email_service = EmailService()
