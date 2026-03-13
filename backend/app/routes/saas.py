# app/routes/saas.py
from flask import Blueprint, request, jsonify
from app.models import (
    db, Lead, Estabelecimento, Funcionario, Configuracao, 
    ConfiguracaoHorario, Caixa, CategoriaProduto
)
from app.decorators.decorator_jwt import super_admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date
import logging
from app.services.email_service import email_service
import json

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
@super_admin_required
def listar_leads():
    """
    Lista todos os leads capturados (Apenas para Super Admin SaaS)
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


# ==================== TENANT ONBOARDING ====================

@saas_bp.route("/onboarding", methods=["POST"])
@super_admin_required
def tenant_onboarding():
    """
    Onboarding Atômico de Novo Cliente (Tenant)
    Cria todo o ecossistema básico do cliente em uma única transação
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Dados não fornecidos",
                "message": "Envie os dados do estabelecimento e administrador"
            }), 400

        # Validação dos campos obrigatórios
        campos_obrigatorios = [
            'nome_fantasia', 'razao_social', 'telefone', 'email_estabelecimento',
            'nome_admin', 'email_admin', 'senha_admin'
        ]
        
        campos_faltantes = [campo for campo in campos_obrigatorios if not data.get(campo)]
        if campos_faltantes:
            return jsonify({
                "success": False,
                "error": "Campos obrigatórios faltando",
                "missing_fields": campos_faltantes
            }), 400

        # Validação de documento (CNPJ ou CPF)
        documento = data.get('cnpj') or data.get('cpf')
        if not documento:
            return jsonify({
                "success": False,
                "error": "É necessário fornecer CNPJ ou CPF"
            }), 400

        # Início da transação atômica
        logger.info(f"🚀 Iniciando onboarding atômico: {data['nome_fantasia']}")

        # 1. Criar Estabelecimento
        estabelecimento = Estabelecimento(
            nome_fantasia=data['nome_fantasia'].strip(),
            razao_social=data['razao_social'].strip(),
            cnpj=documento if len(documento) > 14 else None,
            cpf=documento if len(documento) <= 14 else None,
            telefone=data['telefone'].strip(),
            email=data['email_estabelecimento'].strip(),
            plano='Basic',
            plano_status='ativo',
            data_abertura=date.today(),
            ativo=True,
            regime_tributario='SIMPLES NACIONAL'  # Padrão para novos clientes
        )
        
        db.session.add(estabelecimento)
        db.session.flush()  # Obter ID do estabelecimento
        logger.info(f"✅ Estabelecimento criado: ID {estabelecimento.id}")

        # 2. Criar Funcionário Administrador
        admin_funcionario = Funcionario(
            estabelecimento_id=estabelecimento.id,
            nome=data['nome_admin'].strip(),
            username=data['email_admin'].strip().split('@')[0],  # Usa parte do email como username
            email=data['email_admin'].strip(),
            role='ADMIN',
            cargo='Proprietário',
            salario_base=0.0,  # Define zero para proprietário inicial
            status='ativo',
            ativo=True,
            data_admissao=date.today(),
            data_cadastro=datetime.utcnow(),
            # Endereço opcional - não requerido no cadastro rápido
            cep=data.get('cep', ''),
            logradouro=data.get('logradouro', ''),
            numero=data.get('numero', ''),
            bairro=data.get('bairro', ''),
            cidade=data.get('cidade', ''),
            estado=data.get('estado', ''),
            pais='Brasil',
            permissoes_json=json.dumps({
                "pdv": True,
                "estoque": True,
                "compras": True,
                "financeiro": True,
                "configuracoes": True,
                "funcionarios": True,
                "relatorios": True
            })
        )
        
        admin_funcionario.set_senha(data['senha_admin'])
        db.session.add(admin_funcionario)
        db.session.flush()
        logger.info(f"✅ Administrador criado: {admin_funcionario.username}")

        # 3. Criar Configuração padrão
        config = Configuracao(
            estabelecimento_id=estabelecimento.id,
            formas_pagamento=json.dumps([
                "Dinheiro", "Pix", "Cartão de Crédito", 
                "Cartão de Débito", "Fiado"
            ]),
            logo_url="https://placehold.co/200x100?text=Logo",
            controlar_validade=True,
            alerta_estoque_minimo=True,
            permitir_venda_sem_estoque=False,
            imprimir_cupom=False,
            tema_visual="default"
        )
        db.session.add(config)
        logger.info(f"✅ Configuração padrão criada")

        # 4. Criar ConfiguraçãoHorario padrão
        config_horario = ConfiguracaoHorario(
            estabelecimento_id=estabelecimento.id,
            seg_aberta=True, seg_abertura="08:00", seg_fechamento="18:00",
            ter_aberta=True, ter_abertura="08:00", ter_fechamento="18:00",
            qua_aberta=True, qua_abertura="08:00", qua_fechamento="18:00",
            qui_aberta=True, qui_abertura="08:00", qui_fechamento="18:00",
            sex_aberta=True, sex_abertura="08:00", sex_fechamento="18:00",
            sab_aberta=True, sab_abertura="08:00", sab_fechamento="12:00",
            dom_aberta=False, dom_abertura="00:00", dom_fechamento="00:00"
        )
        db.session.add(config_horario)
        logger.info(f"✅ Horário comercial criado")

        # 5. Criar Caixa inicial
        caixa = Caixa(
            estabelecimento_id=estabelecimento.id,
            numero_caixa="PDV-01",
            status="fechado",
            saldo_inicial=0.0,
            saldo_atual=0.0,
            funcionario_abertura_id=admin_funcionario.id,
            data_abertura=date.today()
        )
        db.session.add(caixa)
        logger.info(f"✅ Caixa inicial criado")

        # 6. Criar Categorias padrão
        categorias_padrao = [
            {"nome": "Geral", "codigo": "CAT001"},
            {"nome": "Bebidas", "codigo": "CAT002"},
            {"nome": "Mercearia", "codigo": "CAT003"}
        ]
        
        for cat_data in categorias_padrao:
            categoria = CategoriaProduto(
                estabelecimento_id=estabelecimento.id,
                nome=cat_data["nome"],
                codigo=cat_data["codigo"],
                ativo=True
            )
            db.session.add(categoria)
        
        logger.info(f"✅ Categorias padrão criadas")

        # Commit da transação atômica
        db.session.commit()
        logger.info(f"🎉 ONBOARDING CONCLUÍDO: {estabelecimento.nome_fantasia}")

        # Enviar email de boas-vindas (assíncrono)
        try:
            email_service.send_welcome_email_tenant(
                admin_funcionario.email, 
                admin_funcionario.nome,
                estabelecimento.nome_fantasia,
                data['senha_admin']
            )
        except Exception as e:
            logger.warning(f"Erro ao enviar email de boas-vindas: {e}")

        # Retorno sucesso com dados de acesso
        return jsonify({
            "success": True,
            "message": "Ambiente do cliente provisionado com sucesso!",
            "data": {
                "estabelecimento": {
                    "id": estabelecimento.id,
                    "nome_fantasia": estabelecimento.nome_fantasia,
                    "plano": estabelecimento.plano,
                    "plano_status": estabelecimento.plano_status,
                    "data_cadastro": estabelecimento.data_cadastro.isoformat() if estabelecimento.data_cadastro else None
                },
                "administrador": {
                    "id": admin_funcionario.id,
                    "nome": admin_funcionario.nome,
                    "username": admin_funcionario.username,
                    "email": admin_funcionario.email,
                    "role": admin_funcionario.role,
                    "cargo": admin_funcionario.cargo
                },
                "acesso": {
                    "login": admin_funcionario.username,
                    "senha": data['senha_admin'],  # Retorno apenas para confirmação
                    "url_acesso": "https://app.mercadinhosys.com/login"
                },
                "recursos_criados": [
                    "Estabelecimento",
                    "Usuário Administrador", 
                    "Configurações Básicas",
                    "Horário Comercial",
                    "Caixa PDV-01",
                    "3 Categorias de Produtos"
                ]
            }
        }), 201

    except Exception as e:
        # Rollback em caso de qualquer erro
        db.session.rollback()
        logger.error(f"❌ FALHA NO ONBOARDING: {str(e)}")
        
        return jsonify({
            "success": False,
            "error": "Falha ao provisionar ambiente do cliente",
            "details": str(e) if logger.isEnabledFor(logging.DEBUG) else "Erro interno. Contate o suporte."
        }), 500


# ==================== SUBSCRIPTION & PAYMENTS ====================

@saas_bp.route("/assinatura/status", methods=["GET"])
@jwt_required()
def get_assinatura_status():
    """Retorna o status do plano do estabelecimento atual via utilitário safe"""
    try:
        from app.utils.query_helpers import get_estabelecimento_safe
        from app.utils.query_helpers import get_authorized_establishment_id
        estabelecimento_id = get_authorized_establishment_id()

        if not estabelecimento_id:
            return jsonify({"success": False, "error": "Estabelecimento não identificado"}), 400

        # Usa o utilitário centralizado que é blindado contra colunas ausentes
        dados = get_estabelecimento_safe(estabelecimento_id)

        if not dados:
            return jsonify({"success": False, "error": "Estabelecimento não encontrado"}), 404

        vencimento = dados.get("vencimento_assinatura")
        plano_status_val = dados.get("plano_status", "experimental")

        return jsonify({
            "success": True,
            "data": {
                "plano": dados.get("plano", "Basic"),
                "status": plano_status_val,
                "vencimento": vencimento.isoformat() if vencimento and hasattr(vencimento, 'isoformat') else None,
                "is_active": plano_status_val in ["ativo", "experimental"],
                "nome_estabelecimento": dados.get("nome_fantasia"),
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
        from flask import current_app
@saas_bp.route("/monitor/estabelecimentos", methods=["GET"])
@jwt_required()
def listar_estabelecimentos_monitor():
    """
    Lista todos os estabelecimentos para o Seletor de Unidades (Super-Admin)
    """
    try:
        claims = get_jwt()
        if not claims.get("is_super_admin"):
            return jsonify({"success": False, "error": "Acesso restrito"}), 403
            
        estabelecimentos = Estabelecimento.query.all()
        return jsonify({
            "success": True,
            "estabelecimentos": [e.to_dict() for e in estabelecimentos]
        }), 200
    except Exception as e:
        logger.error(f"Erro ao listar estabelecimentos monitor: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
