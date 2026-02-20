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

        # Simulação de dados fiscais (Elite Experience)
        import random
        chave_acesso = "".join([str(random.randint(0, 9)) for _ in range(44)])
        protocolo = f"{random.randint(100000000, 999999999)}"
        data_protocolo = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DANFE Simulado - {{ venda.codigo }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; margin: 0; padding: 40px; }
        .danfe-container { max-width: 800px; margin: 0 auto; background: #fff; border: 1px solid #000; padding: 0; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        .section-box { border-bottom: 1px solid #000; display: flex; }
        .header-logo { width: 30%; border-right: 1px solid #000; padding: 15px; text-align: center; }
        .header-ident { width: 40%; border-right: 1px solid #000; padding: 15px; font-size: 11px; line-height: 1.4; }
        .header-danfe { width: 30%; padding: 15px; text-align: center; font-weight: bold; }
        .label { font-size: 9px; font-weight: bold; text-transform: uppercase; color: #333; display: block; margin-bottom: 2px; }
        .value { font-size: 12px; font-weight: normal; color: #000; word-break: break-all; }
        .grid-box { border-bottom: 1px solid #000; display: flex; flex-wrap: wrap; }
        .grid-item { border-right: 1px solid #000; padding: 8px 12px; flex: 1; min-width: 100px; }
        .grid-item:last-child { border-right: none; }
        .table-items { width: 100%; border-collapse: collapse; font-size: 10px; }
        .table-items th { background: #f0f0f0; border-bottom: 1px solid #000; border-right: 1px solid #000; padding: 5px; text-align: left; font-size: 9px; }
        .table-items td { border-bottom: 1px dotted #ccc; border-right: 1px solid #000; padding: 5px; }
        .table-items th:last-child, .table-items td:last-child { border-right: none; }
        .total-box { display: flex; justify-content: flex-end; padding: 15px; background: #fafafa; border-bottom: 1px solid #000; }
        .total-item { margin-left: 30px; text-align: right; }
        .footer-note { padding: 10px; font-size: 10px; text-align: center; font-style: italic; color: #555; }
        .access-key-box { background: #eee; padding: 5px; font-family: 'Courier New', monospace; font-size: 11px; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="danfe-container">
        <!-- HEADER / IDENTIFICACAO -->
        <div class="section-box">
            <div class="header-logo">
                {% if comprovante.logo_url %}
                    <img src="{{ comprovante.logo_url }}" style="max-width: 100%; max-height: 90px;">
                {% else %}
                    <div style="font-weight: bold; font-size: 16px;">{{ estabelecimento.nome_fantasia or 'MERCADINHOSYS' }}</div>
                {% endif %}
            </div>
            <div class="header-ident">
                <span class="label">Emitente</span>
                <div class="value" style="font-weight: bold;">{{ estabelecimento.razao_social or estabelecimento.nome_fantasia }}</div>
                <div class="value">{{ estabelecimento.endereco }}</div>
                <div class="value">CNPJ: {{ estabelecimento.cnpj }} | Tel: {{ estabelecimento.telefone }}</div>
            </div>
            <div class="header-danfe">
                <div style="font-size: 18px; margin-bottom: 5px;">DANFE</div>
                <div style="font-size: 10px; font-weight: normal;">Documento Auxiliar da Nota Fiscal Eletrônica</div>
                <div style="margin-top: 10px; border: 1px solid #000; padding: 5px;">
                    <span class="label">Nº Venda: {{ venda.codigo }}</span>
                </div>
            </div>
        </div>

        <!-- CHAVE DE ACESSO SIMULADA -->
        <div class="grid-box">
            <div class="grid-item" style="flex: 2;">
                <span class="label">Chave de Acesso (Simulada)</span>
                <div class="access-key-box">{{ chave_acesso[:4] }} {{ chave_acesso[4:8] }} {{ chave_acesso[8:12] }} {{ chave_acesso[12:16] }} {{ chave_acesso[16:20] }} {{ chave_acesso[20:24] }} {{ chave_acesso[24:28] }} {{ chave_acesso[28:32] }} {{ chave_acesso[32:36] }} {{ chave_acesso[36:40] }} {{ chave_acesso[40:] }}</div>
            </div>
            <div class="grid-item">
                <span class="label">Protocolo de Autorização</span>
                <div class="value">{{ protocolo }} - {{ data_protocolo }}</div>
            </div>
        </div>

        <!-- DADOS DA OPERACAO -->
        <div class="grid-box">
            <div class="grid-item">
                <span class="label">Natureza da Operação</span>
                <div class="value">VENDA DE MERCADORIA ADQ. DE TERCEIROS</div>
            </div>
            <div class="grid-item">
                <span class="label">Inscrição Estadual</span>
                <div class="value">ISENTO</div>
            </div>
        </div>

        <!-- DESTINATARIO -->
        <div class="section-box" style="background: #f0f0f0;">
            <div style="padding: 5px 15px; font-weight: bold; font-size: 10px;">DESTINATÁRIO / REMETENTE</div>
        </div>
        <div class="grid-box">
            <div class="grid-item" style="flex: 2;">
                <span class="label">Nome / Razão Social</span>
                <div class="value">{{ comprovante.cliente or 'CONSUMIDOR FINAL' }}</div>
            </div>
            <div class="grid-item">
                <span class="label">Data de Emissão</span>
                <div class="value">{{ venda.data }}</div>
            </div>
        </div>

        <!-- ITENS -->
        <div class="section-box" style="background: #f0f0f0;">
            <div style="padding: 5px 15px; font-weight: bold; font-size: 10px;">DADOS DOS PRODUTOS / SERVIÇOS</div>
        </div>
        <table class="table-items">
            <thead>
                <tr>
                    <th width="10%">CÓDIGO</th>
                    <th width="40%">DESCRIÇÃO</th>
                    <th width="10%">NCM/SH</th>
                    <th width="5%">UN.</th>
                    <th width="10%">QTD</th>
                    <th width="10%">V. UNIT</th>
                    <th width="15%">V. TOTAL</th>
                </tr>
            </thead>
            <tbody>
                {% for item in comprovante.itens %}
                <tr>
                    <td>{{ item.codigo or '000' }}</td>
                    <td>{{ item.nome }}</td>
                    <td>8517.12.31</td> <!-- Mock NCM for ELITE feel -->
                    <td>UN</td>
                    <td>{{ item.quantidade }}</td>
                    <td>{{ fmt(item.preco_unitario) }}</td>
                    <td>{{ fmt(item.total) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <!-- TOTAIS -->
        <div class="total-box">
            <div class="total-item">
                <span class="label">Valor Total Bruto</span>
                <div class="value">R$ {{ fmt(comprovante.subtotal) }}</div>
            </div>
            {% if comprovante.desconto > 0 %}
            <div class="total-item">
                <span class="label">Descontos (-)</span>
                <div class="value">R$ {{ fmt(comprovante.desconto) }}</div>
            </div>
            {% endif %}
            <div class="total-item" style="border-left: 1px solid #ccc; padding-left: 20px;">
                <span class="label" style="color: #000; font-size: 11px;">VALOR TOTAL DA NOTA</span>
                <div class="value" style="font-size: 20px; font-weight: bold;">R$ {{ fmt(comprovante.total) }}</div>
            </div>
        </div>

        <!-- PAGAMENTO -->
        <div class="grid-box">
            <div class="grid-item">
                <span class="label">Forma de Pagamento</span>
                <div class="value" style="text-transform: uppercase;">{{ comprovante.forma_pagamento }}</div>
            </div>
            <div class="grid-item">
                <span class="label">Valor Recebido</span>
                <div class="value">R$ {{ fmt(comprovante.valor_recebido) }}</div>
            </div>
            <div class="grid-item">
                <span class="label">Troco</span>
                <div class="value">R$ {{ fmt(comprovante.troco) }}</div>
            </div>
        </div>

        <!-- RODAPE ADICIONAL -->
        <div class="footer-note">
            <p style="margin: 5px 0;">ESTE É UM SIMULACRO DE NF-E PARA FINS DE DEMONSTRAÇÃO DO SISTEMA MERCADINHOSYS.</p>
            <p style="margin: 5px 0;">OBSERVAÇÕES: {{ comprovante.rodape or 'Obrigado pela preferência!' }}</p>
            <p style="font-weight: bold; margin-top: 10px;">POWERED BY ELITE-PDV ENGINE v3.0</p>
        </div>
    </div>
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
