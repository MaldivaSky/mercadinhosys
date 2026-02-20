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

def _prepare_logo_cid(logo_b64):
    """
    Decodifica o base64 e prepara o objeto MIMEImage com CID fixo.
    Reforçado para compatibilidade total com Gmail e Outlook.
    """
    from flask import current_app
    if not logo_b64:
        return None, None
        
    try:
        import base64
        import re
        from email.mime.image import MIMEImage
        
        # 1. Extração Cirúrgica do Base64
        if "," in logo_b64:
            encoded = logo_b64.split(",")[1]
        else:
            encoded = logo_b64
            
        encoded = re.sub(r'[^A-Za-z0-9+/=]', '', encoded)
        image_data = base64.b64decode(encoded)
        
        # 2. Detecção de Subtipo
        subtype = "png"
        if image_data.startswith(b'\xff\xd8'): subtype = "jpeg"
        elif image_data.startswith(b'GIF8'): subtype = "gif"
        elif image_data.startswith(b'\x89PNG'): subtype = "png"
            
        # 3. Construção do Objeto MIMEImage
        image_part = MIMEImage(image_data, _subtype=subtype)
        
        # 4. Cabeçalhos de Elite (Vital para aparecer no Gmail)
        cid = "logo_img" 
        image_part.add_header('Content-ID', f'<{cid}>')
        image_part.add_header('Content-Type', f'image/{subtype}; name="logo.{subtype}"')
        image_part.add_header('Content-Disposition', 'inline', filename=f'logo.{subtype}')
        
        current_app.logger.info(f"✅ [LOGO SUCCESS] CID <{cid}> criado ({subtype})")
        return image_part, cid
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"❌ [LOGO CRITICAL ERROR] {e}")
        return None, None


def _get_official_logo_b64():
    """Busca o logo oficial do projeto e retorna em Base64"""
    try:
        # Tenta localizar o logo no projeto (Estrutura: backend/app -> ../../frontend)
        logo_path = os.path.abspath(os.path.join(current_app.root_path, "..", "..", "frontend", "mercadinhosys-frontend", "logoprincipal.png"))
        if not os.path.exists(logo_path):
            # Fallback path alternativa
            logo_path = os.path.abspath("frontend/mercadinhosys-frontend/logoprincipal.png")
            
        if os.path.exists(logo_path):
            import base64
            with open(logo_path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    except Exception:
        pass
    return None


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

        # Prioridade de Logo: 1. Logo Customizada do Estabelcimento (Base64) 2. Logo Oficial do Sistema
        # Blindagem: Garantir que comece com data:image
        logo_b64 = estabelecimento.get("logo_base64")
        image_part, _ = _prepare_logo_cid(logo_b64)
            
        # Fallback: Se não tem logo customizada ou falhou no processamento, usa a oficial
        if not image_part:
            current_app.logger.info("Tentando fallback para logo oficial...")
            logo_b64 = _get_official_logo_b64()
            image_part, _ = _prepare_logo_cid(logo_b64)

        # Simulação de dados fiscais (Elite Experience)
        import random
        chave_acesso = "".join([str(random.randint(0, 9)) for _ in range(44)])
        protocolo = f"{random.randint(100000000, 999999999)}"
        data_protocolo = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        html_template = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Comprovante de Venda</title>
    <style type="text/css">
        body { 
            margin: 0; padding: 0; min-width: 100%; font-family: 'Segoe UI', Arial, sans-serif; 
            background-color: #f4f6f8; color: #334155; 
        }
        table { border-spacing: 0; }
        td { padding: 0; }
        img { border: 0; }
        .wrapper { width: 100%; table-layout: fixed; background-color: #f4f6f8; padding-bottom: 40px; }
        .main { 
            background-color: #ffffff; margin: 0 auto; width: 100%; max-width: 600px; 
            border-spacing: 0; color: #334155; border-radius: 16px; overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        .header { background-color: #ffffff; padding: 40px 30px; text-align: center; }
        .logo { width: 120px; margin-bottom: 20px; }
        .store-name { font-size: 24px; font-weight: 800; color: #0f172a; margin: 0; text-transform: uppercase; }
        .store-info { font-size: 12px; color: #64748b; line-height: 1.5; margin-top: 8px; }
        
        .content { padding: 0 30px 30px 30px; }
        .section-title { 
            font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; 
            letter-spacing: 1px; margin: 30px 0 15px 0; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px;
        }

        .item-table { width: 100%; margin-bottom: 30px; }
        .item-row td { padding: 12px 0; vertical-align: top; border-bottom: 1px solid #f8fafc; }
        .item-name { font-size: 14px; font-weight: 600; color: #334155; }
        .item-meta { font-size: 11px; color: #94a3b8; margin-top: 4px; }
        .item-price { font-size: 14px; font-weight: 700; color: #0f172a; text-align: right; }

        .totals-table { width: 100%; background-color: #f8fafc; border-radius: 12px; padding: 20px; }
        .total-row td { padding: 5px 0; font-size: 13px; color: #64748b; }
        .total-value { text-align: right; font-weight: 600; }
        .grand-total td { padding-top: 15px; border-top: 1px solid #e2e8f0; margin-top: 10px; }
        .grand-label { font-size: 16px; font-weight: 800; color: #0f172a; }
        .grand-price { font-size: 24px; font-weight: 800; color: #ef4444; text-align: right; }

        .footer { background-color: #0f172a; padding: 40px 30px; text-align: center; color: #94a3b8; }
        .footer-text { font-size: 12px; line-height: 1.6; }
        .brand { font-size: 14px; font-weight: 800; color: #ffffff; margin-top: 10px; }
        
        .status-accent { height: 6px; background: #dc2626; }
    </style>
</head>
<body>
    <center class="wrapper">
        <table class="main" width="100%">
            <tr><td class="status-accent"></td></tr>
            <tr>
                <td class="header">
                    {% if has_logo %}
                    <img src="cid:logo_img" alt="Logo" class="logo" />
                    {% endif %}
                    <h1 class="store-name">{{ estabelecimento.nome_fantasia or 'MercadinhoSys' }}</h1>
                    <div class="store-info">
                        {{ estabelecimento.razao_social }}<br />
                        CNPJ: {{ estabelecimento.cnpj }}<br />
                        {% if estabelecimento.inscricao_estadual %}
                        IE: {{ estabelecimento.inscricao_estadual }}<br />
                        {% endif %}
                        {{ estabelecimento.endereco }}<br />
                        Tel: {{ estabelecimento.telefone }}
                    </div>
                </td>
            </tr>
            <tr>
                <td class="content">
                    <table width="100%">
                        <tr>
                            <td class="section-title">DETALHES DA VENDA #{{ venda.codigo }}</td>
                            <td align="right" style="font-size: 11px; color: #94a3b8; font-weight: 700;">{{ venda.data }}</td>
                        </tr>
                    </table>

                    <table class="item-table" width="100%">
                        {% for item in comprovante.itens %}
                        <tr class="item-row">
                            <td>
                                <div class="item-name">{{ item.nome }}</div>
                                <div class="item-meta">{{ item.quantidade }} UN x R$ {{ fmt(item.preco_unitario) }}</div>
                            </td>
                            <td class="item-price">R$ {{ fmt(item.total) }}</td>
                        </tr>
                        {% endfor %}
                    </table>

                    <table class="totals-table" width="100%">
                        <tr class="total-row">
                            <td>Subtotal</td>
                            <td class="total-value">R$ {{ fmt(comprovante.subtotal) }}</td>
                        </tr>
                        {% if comprovante.desconto > 0 %}
                        <tr class="total-row" style="color: #10b981;">
                            <td>Descontos (-)</td>
                            <td class="total-value">R$ {{ fmt(comprovante.desconto) }}</td>
                        </tr>
                        {% endif %}
                        <tr class="grand-total">
                            <td class="grand-label">TOTAL LÍQUIDO</td>
                            <td class="grand-price">R$ {{ fmt(comprovante.total) }}</td>
                        </tr>
                        
                        {# Exibição de Recebido e Troco (Extreme Transparency) #}
                        {% if comprovante.forma_pagamento|lower == 'dinheiro' or (comprovante.valor_recebido and comprovante.valor_recebido > 0) %}
                        <tr><td colspan="2" style="padding-top: 15px;"></td></tr>
                        <tr class="total-row">
                            <td style="font-weight: bold; color: #475569;">Valor Recebido</td>
                            <td class="total-value" style="color: #475569;">R$ {{ fmt(comprovante.valor_recebido or comprovante.total) }}</td>
                        </tr>
                        {% if comprovante.troco and comprovante.troco > 0 %}
                        <tr class="total-row">
                            <td style="font-weight: bold; color: #dc2626;">Troco</td>
                            <td class="total-value" style="color: #dc2626;">R$ {{ fmt(comprovante.troco) }}</td>
                        </tr>
                        {% endif %}
                        {% endif %}
                    </table>

                    <div style="margin-top: 30px; text-align: center;">
                        <span style="background-color: #f1f5f9; padding: 6px 15px; border-radius: 20px; font-size: 11px; font-weight: 800; color: #475569; text-transform: uppercase;">
                            PAGAMENTO: {{ comprovante.forma_pagamento }}
                        </span>
                    </div>
                </td>
            </tr>
            <tr>
                <td class="footer">
                    <div class="footer-text">
                        Obrigado por comprar conosco!<br />
                        Nossas ofertas são pensadas em você.
                    </div>
                    <div class="brand">MercadinhoSys.io</div>
                </td>
            </tr>
        </table>
    </center>
</body>
</html>
"""

        # 2. Preparar Logo CID (Já feito acima com fallback)

        html_content = render_template_string(
            html_template,
            venda=venda,
            comprovante=comprovante,
            estabelecimento=estabelecimento,
            fmt=_format_moeda,
            has_logo=True if image_part else False
        )

        # Simulação de envio com blindagem contra Erro 500
        try:
            # Configurar mensagem MIME
            msg = MIMEMultipart("related")
            msg["Subject"] = f"★ [Comprovante] {estabelecimento.get('nome_fantasia', 'Mercadinho')} - #{venda.get('codigo', '')}"
            msg["From"] = mail_sender
            msg["To"] = cliente_email
            
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            text_content = f"Comprovante {venda.get('codigo', '')} - Total: R$ {venda.get('total', '0.00')}"
            
            msg_alternative.attach(MIMEText(text_content, "plain"))
            msg_alternative.attach(MIMEText(html_content, "html"))
            
            # Se tiver imagem para embedar (CID), anexa ao MIME principal (related)
            # Ordem: alternative (text/html) -> image
            if image_part:
                msg.attach(image_part)
                current_app.logger.info("📎 [EMAIL] Logo CID anexada com sucesso.")
            else:
                current_app.logger.warning("⚠️ [EMAIL] Nenhuma logo anexada (has_logo era False).")
            
            # Enviar email com timeout para evitar travamento da API
            if mail_port == 465 or mail_use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(mail_server, mail_port, context=context, timeout=10) as server:
                    server.login(mail_username, mail_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
                    if mail_use_tls:
                        server.starttls()
                    server.login(mail_username, mail_password)
                    server.send_message(msg)

            current_app.logger.info(f"✅ Cupom enviado com sucesso para {cliente_email}")
            return True, ""

        except smtplib.SMTPException as smtp_err:
            erro_msg = f"Rejeição do servidor de e-mail: {str(smtp_err)}"
            current_app.logger.error(f"❌ SMTP Error: {erro_msg}")
            return False, erro_msg
        except Exception as generic_err:
            erro_msg = f"Falha técnica no serviço de e-mail: {str(generic_err)}"
            current_app.logger.error(f"❌ Email Delivery Error: {erro_msg}")
            return False, erro_msg

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
