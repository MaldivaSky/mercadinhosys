# app/utils/email_service.py
"""
Serviço de envio de emails
Cupons fiscais, notificações, etc.
"""

from flask import current_app, render_template_string
from flask_mail import Message
from app import mail
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl


def _format_moeda(valor) -> str:
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def _read_env_file_value(key: str):
    """
    Lê uma chave de arquivo .env simples sem depender de libs externas.
    Ordem de busca: backend/mail.env -> backend/.env
    """
    # Lista de chaves alternativas para buscar
    msg_keys = [key]
    if key == "MAIL_PASSWORD":
        msg_keys.append("EMAIL_APP_PASSWORD")

    candidate_files = ["/app/mail.env", "/app/.env", "mail.env", ".env"]
    
    val = None
    
    # Tenta buscar nas env vars primeiro (prioridade)
    # MAS apenas se não for MAIL_PASSWORD, pois queremos forçar leitura do arquivo se possível?
    # Não, env vars sempre prioridade.
    
    for file_path in candidate_files:
        try:
            if not os.path.exists(file_path):
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k.strip() in msg_keys:
                        found_val = v.strip().strip('"').strip("'")
                        if found_val:
                            return found_val
        except Exception:
            continue
    return None


def _resolve_mail_setting(key: str, default=None):
    """
    Resolves a mail setting from:
    1. Flask config
    2. OS environment
    3. .env files (mail.env, .env)
    4. Default value
    """
    # Lista de chaves alternativas para buscar
    msg_keys = [key]
    if key == "MAIL_PASSWORD":
        msg_keys.append("EMAIL_APP_PASSWORD")

    val = None
    for k in msg_keys:
        val = (
            current_app.config.get(k)
            or os.environ.get(k)
            or _read_env_file_value(k)
        )
        if val:
            break
    
    if not val:
        val = default

    # Handle boolean strings for TLS/SSL
    if key in ["MAIL_USE_TLS", "MAIL_USE_SSL"] and isinstance(val, str):
        return val.lower() == "true"
        
    # Remove espaços em branco da senha (comum em App Passwords copia-e-cola)
    if key == "MAIL_PASSWORD" and val and isinstance(val, str):
        return val.replace(" ", "")

    return val


from email.mime.image import MIMEImage
import uuid

def _embed_images_cid(html_content, logo_url):
    """
    Detects if logo_url is base64. If so, prepares a MIMEImage part with a Content-ID (cid)
    and returns the modified HTML (using src="cid:...") and the image part to attach.
    
    Returns:
        tuple: (modified_html, image_part_or_none)
    """
    import base64
    
    if not logo_url or not logo_url.startswith("data:image"):
        return html_content, None
        
    try:
        # Extract metadata and data
        # Format: data:image/png;base64,.....
        header, encoded = logo_url.split(",", 1)
        
        # Generate unique Content-ID
        cid = str(uuid.uuid4()) + "@mercadinhosys.logo"
        
        # Decode image
        image_data = base64.b64decode(encoded)
        
        # Create MIMEImage part
        image_part = MIMEImage(image_data)
        
        # Define Content-ID header (must be enclosed in angle brackets)
        image_part.add_header('Content-ID', f'<{cid}>')
        image_part.add_header('Content-Disposition', 'inline', filename='logo.png')
        
        # Replace src in HTML
        # We need to be careful to replace the EXACT string that was put in the template
        
        if logo_url in html_content:
            modified_html = html_content.replace(logo_url, f"cid:{cid}")
            return modified_html, image_part
        else:
            current_app.logger.warning("⚠️ _embed_images_cid: URL do logo NÃO encontrada no HTML renderizado! A substituição falhou.")
            return html_content, None
        
    except Exception as e:
        current_app.logger.warning(f"Erro ao processar imagem base64 para CID: {e}")
        return html_content, None


def enviar_cupom_fiscal(venda_data: dict, cliente_email: str):
    """
    Envia cupom/comprovante por email usando smtplib direto.
    """
    try:
        # Resolver configurações
        mail_server = _resolve_mail_setting("MAIL_SERVER", "smtp.gmail.com")
        mail_port = int(_resolve_mail_setting("MAIL_PORT", 587))
        mail_username = _resolve_mail_setting("MAIL_USERNAME")
        mail_password = _resolve_mail_setting("MAIL_PASSWORD")
        mail_sender = _resolve_mail_setting("MAIL_DEFAULT_SENDER", mail_username)
        mail_use_tls = _resolve_mail_setting("MAIL_USE_TLS", True)
        mail_use_ssl = _resolve_mail_setting("MAIL_USE_SSL", False)

        if not mail_server or not mail_port:
            return False, "Configuração SMTP incompleta"
        if not mail_username or not mail_password:
            return False, "Credenciais SMTP não configuradas"

        venda = venda_data.get("venda", {})
        comprovante = venda_data.get("comprovante", {})
        estabelecimento = venda_data.get("estabelecimento", {})

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Comprovante de Venda</title>
    <style>
        body, table, td, p, div, span {
            font-family: 'Courier New', Courier, monospace; 
            color: #000000;
        }
    </style>
</head>
<body style="margin: 0; padding: 20px; background-color: #f4f4f4;">
    <center>
        <!-- Container Principal: Largura ~80mm (300-320px) simula impressora térmica -->
            <!-- Cabeçalho / Logo -->
            <tr>
                <td align="center" style="padding-bottom: 10px;">
                    {% if comprovante.logo_url %}
                        <!-- Usa CID se for anexo, ou URL se for externa -->
                        <!-- O Python substitui o src por cid:... antes de enviar -->
                        <img src="{{ comprovante.logo_url }}" style="max-width: 120px; max-height: 80px; display: block;" alt="Logo">
                        <br>
                    {% endif %}
                    
                    <div style="font-size: 14px; font-weight: bold; text-transform: uppercase;">
                        {{ estabelecimento.nome_fantasia or 'MERCADINHO' }}
                    </div>
                    <div style="font-size: 11px;">
                        {{ estabelecimento.razao_social }}<br>
                        CNPJ: {{ estabelecimento.cnpj }}<br>
                        {{ estabelecimento.endereco }}<br>
                        Tel: {{ estabelecimento.telefone }}
                    </div>
                </td>
            </tr>

            <!-- Divisor -->
            <tr>
                <td style="border-bottom: 1px dashed #000; padding: 5px 0;"></td>
            </tr>

            <!-- Dados da Venda -->
            <tr>
                <td style="padding: 10px 0; font-size: 11px;">
                    <div><strong>VENDA:</strong> {{ venda.codigo }}</div>
                    <div><strong>DATA:</strong> {{ venda.data }}</div>
                    <div><strong>CLIENTE:</strong> {{ comprovante.cliente }}</div>
                    <div><strong>OPERADOR:</strong> {{ comprovante.funcionario }}</div>
                </td>
            </tr>

            <!-- Divisor -->
            <tr>
                <td style="border-bottom: 1px dashed #000; padding: 5px 0;"></td>
            </tr>

            <!-- Itens -->
            <tr>
                <td style="padding: 5px 0;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%">
                        <!-- Cabeçalho Itens -->
                        <tr>
                            <td align="left" style="font-size: 11px; font-weight: bold; border-bottom: 1px solid #000;">ITEM</td>
                            <td align="center" style="font-size: 11px; font-weight: bold; border-bottom: 1px solid #000;">QTD</td>
                            <td align="right" style="font-size: 11px; font-weight: bold; border-bottom: 1px solid #000;">VL</td>
                        </tr>
                        
                        <!-- Lista de Itens -->
                        {% for item in comprovante.itens %}
                        <tr>
                            <td colspan="3" style="font-size: 11px; font-weight: bold; padding-top: 4px;">
                                {{ item.nome }}
                            </td>
                        </tr>
                        <tr>
                            <td align="left" style="font-size: 11px; color: #333;">
                                {{ item.codigo }}
                            </td>
                            <td align="center" style="font-size: 11px;">
                                {{ item.quantidade }}
                            </td>
                            <td align="right" style="font-size: 11px;">
                                R$ {{ fmt(item.total) }}
                            </td>
                        </tr>
                        {% endfor %}
                    </table>
                </td>
            </tr>

            <!-- Divisor -->
            <tr>
                <td style="border-bottom: 1px dashed #000; padding: 5px 0;"></td>
            </tr>

            <!-- Totais -->
            <tr>
                <td style="padding: 5px 0;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <td align="left" style="font-size: 12px;">QTD TOTAL:</td>
                            <td align="right" style="font-size: 12px;">{{ comprovante.itens|length }}</td>
                        </tr>
                        <tr>
                            <td align="left" style="font-size: 12px;">SUBTOTAL:</td>
                            <td align="right" style="font-size: 12px;">R$ {{ fmt(comprovante.subtotal) }}</td>
                        </tr>
                        {% if comprovante.desconto > 0 %}
                        <tr>
                            <td align="left" style="font-size: 12px;">DESCONTO:</td>
                            <td align="right" style="font-size: 12px;">- R$ {{ fmt(comprovante.desconto) }}</td>
                        </tr>
                        {% endif %}
                        <tr>
                            <td colspan="2" style="padding-top: 5px;">
                                <div style="border-top: 1px dashed #000;"></div>
                            </td>
                        </tr>
                        <tr>
                            <td align="left" style="font-size: 16px; font-weight: bold; padding-top: 5px;">TOTAL:</td>
                            <td align="right" style="font-size: 16px; font-weight: bold; padding-top: 5px;">R$ {{ fmt(comprovante.total) }}</td>
                        </tr>
                    </table>
                </td>
            </tr>

            <!-- Divisor -->
            <tr>
                <td style="border-bottom: 1px dashed #000; padding: 5px 0;"></td>
            </tr>

            <!-- Pagamento -->
            <tr>
                <td style="padding: 5px 0;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <td align="left" style="font-size: 11px;">Forma Pagto:</td>
                            <td align="right" style="font-size: 11px; text-transform: uppercase;">{{ comprovante.forma_pagamento }}</td>
                        </tr>
                        <tr>
                            <td align="left" style="font-size: 11px;">Valor Recebido:</td>
                            <td align="right" style="font-size: 11px;">R$ {{ fmt(comprovante.valor_recebido) }}</td>
                        </tr>
                        <tr>
                            <td align="left" style="font-size: 11px;">Troco:</td>
                            <td align="right" style="font-size: 11px;">R$ {{ fmt(comprovante.troco) }}</td>
                        </tr>
                    </table>
                </td>
            </tr>

            <!-- Divisor -->
            <tr>
                <td style="border-bottom: 1px dashed #000; padding: 5px 0;"></td>
            </tr>

            <!-- Rodapé -->
            <tr>
                <td align="center" style="padding-top: 10px; font-size: 10px;">
                    <p style="margin: 0;">{{ comprovante.rodape or 'Obrigado pela preferência!' }}</p>
                    <p style="margin: 5px 0 0 0;">*** Documento Não Fiscal ***</p>
                    <p style="margin: 5px 0 0 0;">Sistema: MercadinhoSys</p>
                </td>
            </tr>
            
        </table>
    </center>
</body>
</html>
"""

        html_content = render_template_string(
            html_template,
            venda=venda,
            comprovante=comprovante,
            estabelecimento=estabelecimento,
            fmt=_format_moeda,
        )
        
        # PROCESS IMAGE EMBEDDING (CID)
        image_part = None
        logo_url = comprovante.get("logo_url")
        if logo_url and logo_url.startswith("data:image"):
            html_content, image_part = _embed_images_cid(html_content, logo_url)

        # Configurar mensagem MIME
        msg = MIMEMultipart("related") # Changed from 'alternative' to 'related' for inline images
        msg["Subject"] = f"Comprovante de Venda - {venda.get('codigo', '')}"
        msg["From"] = mail_sender
        msg["To"] = cliente_email
        
        # Encapsulate the plain and HTML versions of the message body in an
        # 'alternative' part, so message agents can decide which they want to display.
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)

        # Create the plain-text and HTML version of your message
        text_content = f"""
Comprovante de Venda #{venda.get('codigo', '')}

Estabelecimento: {estabelecimento.get("nome_fantasia", "")}
Data: {venda.get("data", "")}
Total: R$ {venda.get("total", "0.00")}

Obrigado pela preferência!
        """
        
        msg_alternative.attach(MIMEText(text_content, "plain"))
        msg_alternative.attach(MIMEText(html_content, "html"))
        
        # Anexar imagem inline ao ROOT 'related' (apenas uma vez)
        if image_part:
            msg.attach(image_part)

        # Enviar email
        if mail_port == 465 or mail_use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(mail_server, mail_port, context=context) as server:
                server.login(mail_username, mail_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(mail_server, mail_port) as server:
                if mail_use_tls:
                    server.starttls()
                server.login(mail_username, mail_password)
                server.send_message(msg)

        current_app.logger.info(f"✅ Cupom enviado para {cliente_email} - Venda {venda.get('codigo', '')}")
        return True, ""

    except smtplib.SMTPAuthenticationError as e:
        msg_erro = str(e)
        if "535" in msg_erro or "Username and Password not accepted" in msg_erro:
            detalhe = (
                "Credenciais Gmail rejeitadas. "
                "O Gmail exige App Password (senha de aplicativo), não a senha normal da conta. "
                "Acesse: myaccount.google.com → Segurança → Senhas de app → Gere uma senha para 'Email'. "
                "Atualize MAIL_PASSWORD no backend/mail.env com os 16 caracteres gerados (sem espaços)."
            )
        else:
            detalhe = f"Erro de autenticação SMTP: {msg_erro}"
        current_app.logger.error(f"❌ Erro de autenticação ao enviar cupom: {msg_erro}")
        return False, detalhe

    except smtplib.SMTPConnectError as e:
        detalhe = f"Não foi possível conectar ao servidor SMTP ({mail_server}:{mail_port}). Verifique MAIL_SERVER e MAIL_PORT."
        current_app.logger.error(f"❌ Erro de conexão SMTP: {str(e)}")
        return False, detalhe

    except Exception as e:
        current_app.logger.error(f"❌ Erro ao enviar cupom: {str(e)}")
        return False, str(e)


def enviar_email_com_anexo(to, subject, body, attachment_name, attachment_data, attachment_type):
    """
    Envia email com anexo (PDF, Excel, etc)
    """
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@mercadinhosys.com'),
            recipients=[to],
            body=body
        )
        
        msg.attach(
            attachment_name,
            attachment_type,
            attachment_data
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao enviar email com anexo: {str(e)}")
        return False


def enviar_email(to, subject, template):
    """
    Função genérica de compatibilidade para envio de emails.
    O sistema antigo tenta importar isso.
    """
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config.get(
                "MAIL_DEFAULT_SENDER", "noreply@mercadinhosys.com"
            ),
            recipients=[to],
        )
        # Se o template for HTML, usa html, senão usa body
        if "<html" in template:
            msg.html = template
        else:
            msg.body = template

        mail.send(msg)
        return True
    except Exception as e:
        # Usamos print ou logger aqui para não quebrar se o logger não estiver pronto
        print(f"Erro ao enviar email genérico: {e}")
        return False
