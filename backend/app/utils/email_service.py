# app/utils/email_service.py
"""
Serviço de envio de emails
Cupons fiscais, notificações, etc.
"""

from flask import current_app, render_template_string
from flask_mail import Mail, Message
from datetime import datetime

mail = Mail()

def enviar_cupom_fiscal(venda_data: dict, cliente_email: str) -> bool:
    """
    Envia cupom fiscal por email para o cliente
    
    Args:
        venda_data: Dados completos da venda (do response de finalizar)
        cliente_email: Email do cliente
        
    Returns:
        bool: True se enviou, False se falhou
    """
    try:
        # Template HTML do cupom
        html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cupom Fiscal</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .cupom {
            max-width: 400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border: 2px dashed #333;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }
        .header p {
            margin: 5px 0;
            font-size: 12px;
        }
        .info {
            margin-bottom: 20px;
            font-size: 13px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }
        .items {
            border-top: 1px dashed #666;
            border-bottom: 1px dashed #666;
            padding: 15px 0;
            margin: 15px 0;
        }
        .item {
            margin: 10px 0;
            font-size: 13px;
        }
        .item-header {
            font-weight: bold;
            margin-bottom: 3px;
        }
        .item-details {
            color: #666;
            font-size: 11px;
            margin-left: 10px;
        }
        .totals {
            margin-top: 20px;
            font-size: 14px;
        }
        .total-row {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
        }
        .total-final {
            font-size: 18px;
            font-weight: bold;
            border-top: 2px solid #333;
            padding-top: 10px;
            margin-top: 10px;
        }
        .footer {
            text-align: center;
            margin-top: 25px;
            padding-top: 15px;
            border-top: 2px solid #333;
            font-size: 12px;
            color: #666;
        }
        .qrcode {
            text-align: center;
            margin: 20px 0;
        }
        .destacado {
            background: #fffacd;
            padding: 2px 5px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="cupom">
        <div class="header">
            <h1>🛒 MERCADINHO SYS</h1>
            <p>CNPJ: 00.000.000/0001-00</p>
            <p>Av. Principal, 123 - Centro</p>
            <p>Tel: (00) 0000-0000</p>
        </div>

        <div class="info">
            <div class="info-row">
                <strong>CUPOM FISCAL NÃO FISCAL</strong>
            </div>
            <div class="info-row">
                <span>Código:</span>
                <span class="destacado">{{ venda.codigo }}</span>
            </div>
            <div class="info-row">
                <span>Data/Hora:</span>
                <span>{{ venda.data }}</span>
            </div>
            <div class="info-row">
                <span>Operador:</span>
                <span>{{ comprovante.funcionario }}</span>
            </div>
            {% if comprovante.cliente != 'Consumidor Final' %}
            <div class="info-row">
                <span>Cliente:</span>
                <span>{{ comprovante.cliente }}</span>
            </div>
            {% endif %}
        </div>

        <div class="items">
            <strong>PRODUTOS:</strong>
            {% for item in comprovante.itens %}
            <div class="item">
                <div class="item-header">{{ item.nome }}</div>
                <div class="item-details">
                    {{ item.quantidade }} x R$ {{ "%.2f"|format(item.preco_unitario) }} = 
                    <strong>R$ {{ "%.2f"|format(item.total) }}</strong>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="totals">
            <div class="total-row">
                <span>Subtotal:</span>
                <span>R$ {{ "%.2f"|format(comprovante.subtotal) }}</span>
            </div>
            {% if comprovante.desconto > 0 %}
            <div class="total-row" style="color: #e74c3c;">
                <span>Desconto:</span>
                <span>- R$ {{ "%.2f"|format(comprovante.desconto) }}</span>
            </div>
            {% endif %}
            <div class="total-row total-final">
                <span>TOTAL:</span>
                <span>R$ {{ "%.2f"|format(comprovante.total) }}</span>
            </div>
        </div>

        <div class="info" style="margin-top: 20px;">
            <div class="info-row">
                <span>Forma Pagamento:</span>
                <span><strong>{{ comprovante.forma_pagamento }}</strong></span>
            </div>
            {% if comprovante.valor_recebido > 0 %}
            <div class="info-row">
                <span>Valor Recebido:</span>
                <span>R$ {{ "%.2f"|format(comprovante.valor_recebido) }}</span>
            </div>
            {% endif %}
            {% if comprovante.troco > 0 %}
            <div class="info-row" style="color: #27ae60;">
                <span>Troco:</span>
                <span><strong>R$ {{ "%.2f"|format(comprovante.troco) }}</strong></span>
            </div>
            {% endif %}
        </div>

        <div class="footer">
            <p><strong>{{ comprovante.rodape }}</strong></p>
            <p style="margin-top: 10px; font-size: 10px;">
                Este é um documento não fiscal.<br>
                Válido apenas para controle interno.
            </p>
            <p style="margin-top: 15px; font-size: 10px; color: #999;">
                Email enviado automaticamente pelo sistema MercadinhoSys
            </p>
        </div>
    </div>
</body>
</html>
        """

        # Renderizar template
        html_content = render_template_string(
            html_template,
            venda=venda_data['venda'],
            comprovante=venda_data['comprovante']
        )

        # Criar mensagem
        msg = Message(
            subject=f"Cupom Fiscal - {venda_data['venda']['codigo']}",
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@mercadinhosys.com'),
            recipients=[cliente_email]
        )

        msg.html = html_content

        # Enviar
        mail.send(msg)

        current_app.logger.info(f"✅ Cupom enviado para {cliente_email} - Venda {venda_data['venda']['codigo']}")
        return True

    except Exception as e:
        current_app.logger.error(f"❌ Erro ao enviar cupom: {str(e)}")
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
