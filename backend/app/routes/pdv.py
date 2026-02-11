# app/routes/pdv.py
"""
PDV - Ponto de Venda MISSION-CRITICAL
Rotas otimizadas para operações em tempo real no PDV
Separado de vendas.py para melhor performance e manutenibilidade

OTIMIZAÇÕES IMPLEMENTADAS:
- Custo Médio Ponderado (CMP) em tempo real
- Validação de estoque com lock pessimista (with_for_update)
- Inteligência RFM para sugestão de descontos
- Auditoria completa de vendas
- Alertas de produtos Classe A (alto giro)
"""

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import (
    Venda,
    VendaItem,
    Produto,
    Cliente,
    Funcionario,
    MovimentacaoEstoque,
)
from app.decorators.decorator_jwt import funcionario_required
from flask_jwt_extended import get_jwt_identity, get_jwt
from sqlalchemy import func
import random
import string

pdv_bp = Blueprint("pdv", __name__)


# ==================== EXCEÇÕES PERSONALIZADAS ====================

class InsuficientStockError(Exception):
    """Exceção lançada quando não há estoque suficiente para a venda"""
    pass

# ==================== FUNÇÕES AUXILIARES ====================

def calcular_rfm_cliente(cliente_id: int, estabelecimento_id: int) -> dict:
    """
    Calcula o segmento RFM de um cliente específico.
    
    Retorna dados RFM incluindo flag de sugestão de desconto para clientes em risco.
    
    Args:
        cliente_id: ID do cliente
        estabelecimento_id: ID do estabelecimento
        
    Returns:
        dict: Dados RFM com segmento e flag sugerir_desconto
    """
    from datetime import datetime, timedelta
    
    # Buscar vendas do cliente nos últimos 180 dias
    data_inicio = datetime.utcnow() - timedelta(days=180)
    
    vendas = Venda.query.filter(
        Venda.estabelecimento_id == estabelecimento_id,
        Venda.cliente_id == cliente_id,
        Venda.data_venda >= data_inicio,
        Venda.status == "finalizada"
    ).all()
    
    if not vendas:
        return {
            "segmento": "Novo",
            "sugerir_desconto": False,
            "recency_days": None,
            "frequency": 0,
            "monetary": 0.0
        }
    
    # Calcular métricas
    now = datetime.utcnow()
    ultima_compra = max(v.data_venda for v in vendas)
    recency_days = (now - ultima_compra).days
    frequency = len(vendas)
    monetary = sum(float(v.total) for v in vendas)
    
    # Calcular scores simplificados (1-5)
    # Recency: quanto menor o número de dias, melhor (score invertido)
    if recency_days <= 30:
        recency_score = 5
    elif recency_days <= 60:
        recency_score = 4
    elif recency_days <= 90:
        recency_score = 3
    elif recency_days <= 120:
        recency_score = 2
    else:
        recency_score = 1
    
    # Frequency: quanto mais compras, melhor
    if frequency >= 10:
        frequency_score = 5
    elif frequency >= 7:
        frequency_score = 4
    elif frequency >= 5:
        frequency_score = 3
    elif frequency >= 3:
        frequency_score = 2
    else:
        frequency_score = 1
    
    # Monetary: quanto maior o valor, melhor
    if monetary >= 1000:
        monetary_score = 5
    elif monetary >= 500:
        monetary_score = 4
    elif monetary >= 250:
        monetary_score = 3
    elif monetary >= 100:
        monetary_score = 2
    else:
        monetary_score = 1
    
    # Determinar segmento usando a lógica do modelo Cliente
    segmento = Cliente.segmentar_rfm(recency_score, frequency_score, monetary_score)
    
    # Sugerir desconto para clientes em risco de abandono
    sugerir_desconto = segmento in ["Risco", "Perdido"]
    
    return {
        "segmento": segmento,
        "sugerir_desconto": sugerir_desconto,
        "recency_days": recency_days,
        "recency_score": recency_score,
        "frequency": frequency,
        "frequency_score": frequency_score,
        "monetary": round(monetary, 2),
        "monetary_score": monetary_score,
        "ultima_compra": ultima_compra.isoformat() if ultima_compra else None
    }


def to_decimal(value):
    """Converte qualquer valor numérico para Decimal de forma segura (2 casas decimais)"""
    if value is None:
        return Decimal('0.00')
    if isinstance(value, Decimal):
        return value.quantize(Decimal('0.01'))
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (ValueError, TypeError, InvalidOperation):
        return Decimal('0.00')


def decimal_to_float(value):
    """Converte Decimal para float APENAS para serialização JSON"""
    if isinstance(value, Decimal):
        return float(value)
    return value


def gerar_codigo_venda():
    """Gera código único para venda no formato V-YYYYMMDD-XXXX"""
    data_atual = datetime.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.digits, k=4))
    codigo = f"V-{data_atual}-{random_part}"
    
    # Garantir unicidade
    while Venda.query.filter_by(codigo=codigo).first():
        random_part = "".join(random.choices(string.digits, k=4))
        codigo = f"V-{data_atual}-{random_part}"
    
    return codigo


def validar_estoque_disponivel(produto_id, quantidade_solicitada):
    """Valida se há estoque suficiente"""
    produto = Produto.query.get(produto_id)
    
    if not produto:
        return False, "Produto não encontrado"
    
    if not produto.ativo:
        return False, "Produto inativo"
    
    if produto.quantidade < quantidade_solicitada:
        return False, f"Estoque insuficiente. Disponível: {produto.quantidade}"
    
    return True, produto


def calcular_totais_venda(itens, desconto_geral=0, desconto_percentual=False):
    """Calcula subtotal, desconto e total da venda usando Decimal para precisão"""
    # Converter tudo para Decimal
    subtotal = Decimal('0.00')
    for item in itens:
        subtotal += to_decimal(item['total_item'])
    
    desconto_geral_dec = to_decimal(desconto_geral)
    
    # Calcular desconto
    if desconto_percentual:
        desconto_valor = subtotal * (desconto_geral_dec / Decimal('100'))
    else:
        desconto_valor = desconto_geral_dec
    
    # Desconto não pode ser maior que subtotal
    desconto_valor = min(desconto_valor, subtotal)
    total = subtotal - desconto_valor
    
    return {
        'subtotal': subtotal.quantize(Decimal('0.01')),
        'desconto': desconto_valor.quantize(Decimal('0.01')),
        'total': total.quantize(Decimal('0.01'))
    }


# ==================== ROTAS PDV ====================

@pdv_bp.route("/configuracoes", methods=["GET"])
@funcionario_required
def obter_configuracoes_pdv():
    """
    Retorna configurações do PDV para o funcionário logado
    
    OTIMIZAÇÃO: Inclui dados RFM do cliente se cliente_id for fornecido
    """
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        if not funcionario:
            return jsonify({"error": "Funcionário não encontrado"}), 404
        
        # Formas de pagamento disponíveis
        formas_pagamento = [
            {"tipo": "dinheiro", "label": "Dinheiro", "taxa": 0, "permite_troco": True},
            {"tipo": "cartao_debito", "label": "Cartão de Débito", "taxa": 0, "permite_troco": False},
            {"tipo": "cartao_credito", "label": "Cartão de Crédito", "taxa": 2.5, "permite_troco": False},
            {"tipo": "pix", "label": "PIX", "taxa": 0, "permite_troco": False},
            {"tipo": "outros", "label": "Outros", "taxa": 0, "permite_troco": False},
        ]
        
        configuracoes = {
            "funcionario": {
                "id": funcionario.id,
                "nome": funcionario.nome,
                "role": funcionario.role,
                "pode_dar_desconto": funcionario.permissoes.get("pode_dar_desconto", False),
                "limite_desconto": funcionario.permissoes.get("limite_desconto", 0),
                "pode_cancelar_venda": funcionario.permissoes.get("pode_cancelar_venda", False),
            },
            "formas_pagamento": formas_pagamento,
            "permite_venda_sem_cliente": True,
            "exige_observacao_desconto": True,
        }
        
        # OTIMIZAÇÃO: Incluir dados RFM se cliente_id for fornecido
        cliente_id = request.args.get("cliente_id", type=int)
        if cliente_id:
            try:
                rfm_data = calcular_rfm_cliente(cliente_id, funcionario.estabelecimento_id)
                if rfm_data:
                    configuracoes["rfm"] = rfm_data
            except Exception as rfm_error:
                current_app.logger.warning(f"Erro ao calcular RFM: {str(rfm_error)}")
        
        return jsonify({
            "success": True,
            "configuracoes": configuracoes
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter configurações PDV: {str(e)}")
        return jsonify({"error": "Erro ao carregar configurações"}), 500


@pdv_bp.route("/cliente/<int:cliente_id>/rfm", methods=["GET"])
@funcionario_required
def obter_rfm_cliente(cliente_id):
    """
    Retorna dados RFM de um cliente específico.
    
    OTIMIZAÇÃO: Inteligência RFM para sugestão de descontos no PDV.
    Se o cliente estiver em "Risco" ou "Perdido", retorna flag sugerir_desconto=True.
    """
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        if not funcionario:
            return jsonify({"error": "Funcionário não encontrado"}), 404
        
        # Verificar se cliente existe
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404
        
        # Calcular RFM
        rfm_data = calcular_rfm_cliente(cliente_id, funcionario.estabelecimento_id)
        
        return jsonify({
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nome": cliente.nome,
                "cpf": cliente.cpf
            },
            "rfm": rfm_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter RFM do cliente: {str(e)}")
        return jsonify({"error": "Erro ao calcular RFM"}), 500


@pdv_bp.route("/validar-produto", methods=["POST"])
@funcionario_required
def validar_produto():
    """
    Valida se produto está disponível e retorna informações completas
    Útil para busca por código de barras ou ID
    
    OTIMIZAÇÃO: Retorna alerta para produtos Classe A (alto giro)
    """
    try:
        data = request.get_json()
        produto_id = data.get("produto_id")
        codigo_barras = data.get("codigo_barras")
        quantidade = data.get("quantidade", 1)
        
        # Buscar produto
        if produto_id:
            produto = Produto.query.get(produto_id)
        elif codigo_barras:
            produto = Produto.query.filter_by(codigo_barras=codigo_barras).first()
        else:
            return jsonify({"error": "Informe produto_id ou codigo_barras"}), 400
        
        if not produto:
            return jsonify({
                "valido": False,
                "erro": "Produto não encontrado"
            }), 404
        
        # Validar estoque
        valido, resultado = validar_estoque_disponivel(produto.id, quantidade)
        
        if not valido:
            return jsonify({
                "valido": False,
                "erro": resultado
            }), 400
        
        # Retornar informações do produto
        categoria_nome = "Sem categoria"
        if produto.categoria:
            categoria_nome = produto.categoria.nome
        
        # OTIMIZAÇÃO: Verificar se é produto Classe A (alto giro)
        alerta_alto_giro = False
        mensagem_alerta = None
        if produto.classificacao_abc == "A":
            alerta_alto_giro = True
            mensagem_alerta = "Produto de Alto Giro - Verificar se precisa de reposição na gôndola"
            
        return jsonify({
            "valido": True,
            "produto": {
                "id": produto.id,
                "nome": produto.nome,
                "codigo_barras": produto.codigo_barras,
                "preco_venda": float(produto.preco_venda),
                "preco_custo": float(produto.preco_custo) if produto.preco_custo else 0,
                "quantidade_estoque": produto.quantidade,
                "categoria": categoria_nome,
                "marca": produto.marca or "",
                "unidade_medida": produto.unidade_medida or "UN",
                "margem_lucro": float(produto.margem_lucro) if produto.margem_lucro else 0,
                "ativo": produto.ativo,
                "classificacao_abc": produto.classificacao_abc,
                "alerta_alto_giro": alerta_alto_giro,
                "mensagem_alerta": mensagem_alerta,
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao validar produto: {str(e)}")
        return jsonify({"error": "Erro ao validar produto"}), 500


@pdv_bp.route("/calcular-venda", methods=["POST"])
@funcionario_required
def calcular_venda():
    """
    Calcula totais da venda sem persistir (para preview em tempo real)
    Recebe: itens, desconto_geral, desconto_percentual, forma_pagamento
    Retorna: subtotal, desconto, total, troco
    """
    try:
        data = request.get_json()
        itens = data.get("items", [])
        desconto_geral = float(data.get("desconto_geral", 0))
        desconto_percentual = data.get("desconto_percentual", False)
        forma_pagamento = data.get("forma_pagamento", "dinheiro")
        valor_recebido = float(data.get("valor_recebido", 0))
        
        if not itens:
            return jsonify({"error": "Nenhum item na venda"}), 400
        
        # Validar e calcular cada item
        itens_calculados = []
        for item in itens:
            produto_id = item.get("produto_id")
            quantidade = item.get("quantidade", 1)
            desconto_item = float(item.get("desconto", 0))
            
            # Buscar produto
            produto = Produto.query.get(produto_id)
            if not produto:
                return jsonify({"error": f"Produto {produto_id} não encontrado"}), 404
            
            # Calcular item
            preco_unitario = float(produto.preco_venda)
            total_item = (preco_unitario * quantidade) - desconto_item
            
            itens_calculados.append({
                "produto_id": produto_id,
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "desconto_item": desconto_item,
                "total_item": round(total_item, 2)
            })
        
        # Calcular totais
        totais = calcular_totais_venda(itens_calculados, desconto_geral, desconto_percentual)
        
        # Calcular troco (se dinheiro)
        troco = 0
        if forma_pagamento == "dinheiro" and valor_recebido > 0:
            troco = max(0, valor_recebido - totais['total'])
        
        return jsonify({
            "success": True,
            "calculo": {
                **totais,
                "troco": round(troco, 2),
                "quantidade_itens": len(itens_calculados),
                "valor_recebido": valor_recebido,
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular venda: {str(e)}")
        return jsonify({"error": f"Erro ao calcular: {str(e)}"}), 500


@pdv_bp.route("/finalizar", methods=["POST"])
@funcionario_required
def finalizar_venda():
    """
    Finaliza a venda de forma ATÔMICA
    - Cria venda e itens
    - Atualiza estoque
    - Registra movimentações
    - Retorna comprovante
    - Envia email (opcional)
    """
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        if not funcionario:
            return jsonify({"error": "Funcionário não encontrado"}), 404
        
        data = request.get_json()
        current_app.logger.info(f"📦 Dados recebidos para finalizar venda: {data}")
        
        # ===== VALIDAÇÕES =====
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        items = data.get("items", [])
        if not items or len(items) == 0:
            return jsonify({"error": "Nenhum produto na venda"}), 400
        
        # VALIDAÇÃO CRÍTICA: Cliente obrigatório (replicar regra do frontend no backend)
        cliente_id = data.get("cliente_id")
        # TODO: Buscar configuração do estabelecimento para verificar se exige cliente
        # Por enquanto, vamos permitir venda sem cliente, mas logar um warning
        if not cliente_id:
            current_app.logger.warning(
                f"⚠️ Venda sem cliente - Funcionário: {funcionario.nome} (ID: {funcionario.id})"
            )
        
        # Validar valores numéricos
        try:
            subtotal = to_decimal(data.get("subtotal", 0))
            desconto_geral = to_decimal(data.get("desconto", 0))
            total = to_decimal(data.get("total", 0))
            valor_recebido = to_decimal(data.get("valor_recebido", total))
            troco = to_decimal(data.get("troco", 0))
        except (ValueError, TypeError, InvalidOperation) as ve:
            current_app.logger.error(f"❌ Erro ao converter valores: {str(ve)}")
            return jsonify({"error": f"Valores numéricos inválidos: {str(ve)}"}), 400
        
        forma_pagamento = data.get("paymentMethod", "dinheiro")
        observacoes = data.get("observacoes", "")
        
        current_app.logger.info(
            f"💰 Finalizando venda | Total: R$ {decimal_to_float(total):.2f} | "
            f"Itens: {len(items)} | Funcionário: {funcionario.nome}"
        )
        
        # ===== INÍCIO DA TRANSAÇÃO =====
        try:
            # 1. GERAR CÓDIGO DA VENDA
            codigo_venda = gerar_codigo_venda()
            current_app.logger.info(f"✅ Código gerado: {codigo_venda}")
            
            # 2. CRIAR VENDA
            nova_venda = Venda(
                codigo=codigo_venda,
                estabelecimento_id=funcionario.estabelecimento_id,
                cliente_id=cliente_id,
                funcionario_id=funcionario.id,
                subtotal=subtotal,
                desconto=desconto_geral,
                total=total,
                forma_pagamento=forma_pagamento,
                valor_recebido=valor_recebido,
                troco=troco,
                status="finalizada",
                observacoes=observacoes,
                data_venda=datetime.now()
            )
            
            db.session.add(nova_venda)
            db.session.flush()  # Obter ID da venda
            current_app.logger.info(f"✅ Venda criada com ID: {nova_venda.id}")
            
            # 3. PROCESSAR ITENS
            itens_processados = []
            produtos_atualizados = []
            
            current_app.logger.info(f"📦 Processando {len(items)} itens...")
            
            for idx, item_data in enumerate(items):
                produto_id = item_data.get("id")
                quantidade = int(item_data.get("quantity", 1))
                desconto_item = float(item_data.get("discount", 0))
                
                current_app.logger.info(
                    f"  Item {idx+1}: Produto ID={produto_id}, Qtd={quantidade}, Desc={desconto_item}"
                )
                
                # Buscar produto com lock (evita race condition)
                produto = db.session.query(Produto).with_for_update().get(produto_id)
                
                if not produto:
                    raise ValueError(f"Produto {produto_id} não encontrado")
                
                if not produto.ativo:
                    raise ValueError(f"Produto '{produto.nome}' está inativo")
                
                # Converter quantidade do produto para int para comparação
                estoque_disponivel = int(produto.quantidade) if produto.quantidade else 0
                
                # OTIMIZAÇÃO: Validação de estoque com exceção personalizada
                if estoque_disponivel < quantidade:
                    raise InsuficientStockError(
                        f"Estoque insuficiente para '{produto.nome}'. "
                        f"Disponível: {estoque_disponivel}, Solicitado: {quantidade}"
                    )
                
                # OTIMIZAÇÃO: Usar CMP (Custo Médio Ponderado) em tempo real
                preco_unitario = decimal_to_float(produto.preco_venda)
                preco_custo_atual = decimal_to_float(produto.preco_custo)  # CMP já calculado no modelo
                total_item = (preco_unitario * quantidade) - desconto_item
                
                # OTIMIZAÇÃO: Calcular margem de lucro REAL (preço venda - custo atual)
                margem_lucro_real = (preco_unitario - preco_custo_atual) * quantidade
                
                # Calcular margem percentual
                margem_item = 0.0
                if preco_unitario > 0:
                    margem_item = round(
                        ((preco_unitario - preco_custo_atual) / preco_unitario * 100),
                        2
                    )
                
                # Criar item da venda
                venda_item = VendaItem(
                    venda_id=nova_venda.id,
                    produto_id=produto.id,
                    produto_nome=produto.nome,
                    produto_codigo=produto.codigo_barras,
                    produto_unidade=produto.unidade_medida,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    desconto=desconto_item,
                    total_item=total_item,
                    custo_unitario=preco_custo_atual,
                    margem_item=margem_item,
                    margem_lucro_real=margem_lucro_real  # NOVO CAMPO
                )
                
                db.session.add(venda_item)
                
                # Atualizar estoque
                estoque_anterior = int(produto.quantidade) if produto.quantidade else 0
                produto.quantidade = estoque_anterior - quantidade
                produto.updated_at = datetime.now()
                
                # ATUALIZAR CAMPOS DE VENDAS PARA ANÁLISE ABC
                produto.quantidade_vendida = (produto.quantidade_vendida or 0) + quantidade
                produto.total_vendido = (produto.total_vendido or 0) + total_item
                produto.ultima_venda = datetime.now()
                
                # Registrar movimentação
                movimentacao = MovimentacaoEstoque(
                    estabelecimento_id=funcionario.estabelecimento_id,
                    produto_id=produto.id,
                    tipo="saida",
                    quantidade=quantidade,
                    quantidade_anterior=estoque_anterior,
                    quantidade_atual=produto.quantidade,
                    venda_id=nova_venda.id,
                    funcionario_id=funcionario.id,
                    motivo="Venda",
                    observacoes=f"Venda {codigo_venda}"
                )
                
                db.session.add(movimentacao)
                
                itens_processados.append({
                    "nome": produto.nome,
                    "quantidade": quantidade,
                    "preco_unitario": preco_unitario,
                    "total": total_item
                })
                
                produtos_atualizados.append(produto.nome)
            
            # 4. COMMIT DA TRANSAÇÃO
            current_app.logger.info(f"💾 Commitando transação...")
            db.session.commit()
            current_app.logger.info(f"✅ Transação commitada com sucesso!")
            
            # 5. PREPARAR RESPOSTA
            resposta_venda = {
                "success": True,
                "message": "Venda finalizada com sucesso!",
                "venda": {
                    "id": nova_venda.id,
                    "codigo": codigo_venda,
                    "total": decimal_to_float(total),
                    "subtotal": decimal_to_float(subtotal),
                    "desconto": decimal_to_float(desconto_geral),
                    "troco": decimal_to_float(troco),
                    "forma_pagamento": forma_pagamento,
                    "data": nova_venda.data_venda.isoformat(),
                    "quantidade_itens": len(itens_processados),
                },
                "comprovante": {
                    "cabecalho": "MERCADINHO SYS",
                    "titulo": "COMPROVANTE DE VENDA",
                    "codigo": codigo_venda,
                    "data": nova_venda.data_venda.strftime("%d/%m/%Y %H:%M:%S"),
                    "funcionario": funcionario.nome,
                    "cliente": nova_venda.cliente.nome if nova_venda.cliente else "Consumidor Final",
                    "itens": itens_processados,
                    "subtotal": decimal_to_float(subtotal),
                    "desconto": decimal_to_float(desconto_geral),
                    "total": decimal_to_float(total),
                    "forma_pagamento": forma_pagamento.replace("_", " ").title(),
                    "valor_recebido": decimal_to_float(valor_recebido),
                    "troco": decimal_to_float(troco),
                    "rodape": "Obrigado pela preferência!",
                }
            }
            
            # 6. ENVIAR EMAIL (se solicitado e cliente tiver email)
            enviar_email = data.get("enviar_email", False)
            if enviar_email and nova_venda.cliente and nova_venda.cliente.email:
                try:
                    from app.utils.email_service import enviar_cupom_fiscal
                    
                    email_enviado = enviar_cupom_fiscal(
                        venda_data=resposta_venda,
                        cliente_email=nova_venda.cliente.email
                    )
                    
                    if email_enviado:
                        resposta_venda["email_enviado"] = True
                        resposta_venda["email_destinatario"] = nova_venda.cliente.email
                        current_app.logger.info(
                            f"📧 Email enviado para {nova_venda.cliente.email} - Venda {codigo_venda}"
                        )
                    else:
                        resposta_venda["email_enviado"] = False
                        resposta_venda["email_erro"] = "Falha ao enviar email"
                        current_app.logger.warning(
                            f"⚠️ Falha ao enviar email para {nova_venda.cliente.email}"
                        )
                        
                except Exception as email_error:
                    current_app.logger.error(f"❌ Erro ao enviar email: {str(email_error)}")
                    resposta_venda["email_enviado"] = False
                    resposta_venda["email_erro"] = str(email_error)
            
            # 7. LOG DE SUCESSO
            current_app.logger.info(
                f"✅ Venda {codigo_venda} finalizada | "
                f"Total: R$ {decimal_to_float(total):.2f} | "
                f"Itens: {len(itens_processados)} | "
                f"Funcionário: {funcionario.nome}"
            )
            
            return jsonify(resposta_venda), 201
            
        except ValueError as ve:
            db.session.rollback()
            current_app.logger.warning(f"⚠️ Validação falhou: {str(ve)}")
            return jsonify({"error": str(ve)}), 400
        
        except InsuficientStockError as ise:
            db.session.rollback()
            current_app.logger.warning(f"⚠️ Estoque insuficiente: {str(ise)}")
            return jsonify({"error": str(ise), "tipo": "estoque_insuficiente"}), 400
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao finalizar venda: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro ao processar venda: {str(e)}"}), 500


@pdv_bp.route("/vendas-hoje", methods=["GET"])
@funcionario_required
def vendas_hoje():
    """
    Retorna resumo das vendas do dia atual
    Útil para dashboard do PDV
    """
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = datetime.combine(hoje, datetime.max.time())
        
        # Vendas do dia
        vendas = Venda.query.filter(
            Venda.estabelecimento_id == funcionario.estabelecimento_id,
            Venda.data_venda >= inicio_dia,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada"
        ).all()
        
        # Estatísticas
        total_vendas = sum(v.total for v in vendas)
        quantidade_vendas = len(vendas)
        ticket_medio = total_vendas / quantidade_vendas if quantidade_vendas > 0 else 0
        
        # Por forma de pagamento
        por_forma_pagamento = {}
        for v in vendas:
            forma = v.forma_pagamento
            if forma not in por_forma_pagamento:
                por_forma_pagamento[forma] = {"quantidade": 0, "total": 0}
            por_forma_pagamento[forma]["quantidade"] += 1
            por_forma_pagamento[forma]["total"] += v.total
        
        return jsonify({
            "success": True,
            "data": hoje.isoformat(),
            "resumo": {
                "total_vendas": round(total_vendas, 2),
                "quantidade_vendas": quantidade_vendas,
                "ticket_medio": round(ticket_medio, 2),
                "por_forma_pagamento": por_forma_pagamento,
            },
            "ultimas_vendas": [
                {
                    "id": v.id,
                    "codigo": v.codigo,
                    "total": float(v.total),
                    "hora": v.data_venda.strftime("%H:%M"),
                    "forma_pagamento": v.forma_pagamento,
                }
                for v in sorted(vendas, key=lambda x: x.data_venda, reverse=True)[:10]
            ]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar vendas do dia: {str(e)}")
        return jsonify({"error": "Erro ao carregar vendas"}), 500


@pdv_bp.route("/cancelar-venda/<int:venda_id>", methods=["POST"])
@funcionario_required
def cancelar_venda_pdv(venda_id):
    """
    Cancela uma venda e devolve produtos ao estoque
    Requer permissão específica
    """
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        # Verificar permissão
        if not funcionario.permissoes.get("pode_cancelar_venda", False):
            return jsonify({"error": "Sem permissão para cancelar vendas"}), 403
        
        data = request.get_json()
        motivo = data.get("motivo", "Cancelamento solicitado")
        
        # Buscar venda
        venda = Venda.query.get(venda_id)
        
        if not venda:
            return jsonify({"error": "Venda não encontrada"}), 404
        
        if venda.status == "cancelada":
            return jsonify({"error": "Venda já está cancelada"}), 400
        
        # Cancelar venda
        try:
            venda.status = "cancelada"
            venda.observacoes = f"{venda.observacoes}\n[CANCELADA] {motivo}"
            
            # Devolver produtos ao estoque
            for item in venda.itens:
                produto = Produto.query.with_for_update().get(item.produto_id)
                
                if produto:
                    estoque_anterior = produto.quantidade
                    produto.quantidade += item.quantidade
                    
                    # Registrar movimentação
                    movimentacao = MovimentacaoEstoque(
                        produto_id=produto.id,
                        tipo_movimentacao="entrada",
                        quantidade=item.quantidade,
                        estoque_anterior=estoque_anterior,
                        estoque_posterior=produto.quantidade,
                        venda_id=venda.id,
                        funcionario_id=funcionario.id,
                        data_movimentacao=datetime.now(),
                        observacao=f"Cancelamento venda {venda.codigo}"
                    )
                    db.session.add(movimentacao)
            
            db.session.commit()
            
            current_app.logger.info(f"🚫 Venda {venda.codigo} cancelada por {funcionario.nome}")
            
            return jsonify({
                "success": True,
                "message": f"Venda {venda.codigo} cancelada com sucesso",
                "venda": {
                    "id": venda.id,
                    "codigo": venda.codigo,
                    "status": "cancelada",
                }
            }), 200
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    except Exception as e:
        current_app.logger.error(f"Erro ao cancelar venda: {str(e)}")
        return jsonify({"error": f"Erro ao cancelar: {str(e)}"}), 500


# ==================== ESTATÍSTICAS RÁPIDAS ====================

@pdv_bp.route("/estatisticas-rapidas", methods=["GET"])
@funcionario_required
def estatisticas_rapidas():
    """
    Estatísticas em tempo real para exibição no PDV
    Performance otimizada (sem joins pesados)
    """
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        if not funcionario:
            try:
                claims = get_jwt()
                est_id_claim = claims.get("estabelecimento_id")
            except Exception:
                est_id_claim = None
            if est_id_claim is None:
                return jsonify({"error": "Usuário não encontrado"}), 404
        
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        
        # Query otimizada
        est_id = funcionario.estabelecimento_id if funcionario else int(est_id_claim)
        stats = db.session.query(
            func.count(Venda.id).label("total_vendas"),
            func.sum(Venda.total).label("faturamento"),
            func.avg(Venda.total).label("ticket_medio"),
        ).filter(
            Venda.estabelecimento_id == est_id,
            Venda.data_venda >= inicio_dia,
            Venda.status == "finalizada"
        ).first()
        
        return jsonify({
            "success": True,
            "estatisticas": {
                "total_vendas": stats.total_vendas or 0,
                "faturamento": round(float(stats.faturamento or 0), 2),
                "ticket_medio": round(float(stats.ticket_medio or 0), 2),
                "funcionario": (funcionario.nome if funcionario else "Usuário"),
                "hora_atual": datetime.now().strftime("%H:%M"),
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro nas estatísticas: {str(e)}")
        return jsonify({"error": "Erro ao carregar estatísticas"}), 500


# ==================== ENVIAR CUPOM FISCAL POR EMAIL ====================

@pdv_bp.route("/enviar-cupom", methods=["POST"])
@funcionario_required
def enviar_cupom_email():
    """
    Envia cupom fiscal por email para o cliente
    Requer: venda_id
    """
    try:
        data = request.get_json()
        venda_id = data.get("venda_id")
        
        if not venda_id:
            return jsonify({"error": "venda_id é obrigatório"}), 400
        
        # Buscar venda com relacionamentos
        venda = Venda.query.get(venda_id)
        if not venda:
            return jsonify({"error": "Venda não encontrada"}), 404
        
        # Buscar cliente
        cliente = Cliente.query.get(venda.cliente_id) if venda.cliente_id else None
        
        if not cliente or not cliente.email:
            return jsonify({"error": "Cliente não possui email cadastrado"}), 400
        
        # Buscar estabelecimento
        from app.models import Estabelecimento
        estabelecimento = Estabelecimento.query.get(venda.estabelecimento_id)
        
        if not estabelecimento:
            return jsonify({"error": "Estabelecimento não encontrado"}), 404
        
        # Preparar dados da venda
        from app.utils.email_service import enviar_cupom_fiscal
        
        # Estrutura compatível com o template em email_service.py
        dados_formatados = {
            "venda": {
                "codigo": venda.codigo,
                "data": venda.data_venda.strftime("%d/%m/%Y %H:%M")
            },
            "comprovante": {
                "funcionario": venda.funcionario.nome if venda.funcionario else "Balcão",
                "cliente": cliente.nome if cliente else "Consumidor Final",
                "itens": [
                    {
                        "nome": item.produto.nome,
                        "quantidade": float(item.quantidade),
                        "preco_unitario": float(item.preco_unitario)
                    }
                    for item in venda.itens
                ],
                "total": float(venda.total),
                "subtotal": float(venda.subtotal),
                "desconto": float(venda.desconto)
            }
        }
        
        # Enviar email
        sucesso = enviar_cupom_fiscal(dados_formatados, cliente.email)
        
        if sucesso:
            return jsonify({
                "success": True,
                "message": "Cupom fiscal enviado com sucesso!",
                "email_destino": cliente.email
            }), 200
        else:
            current_app.logger.error(f"Erro ao enviar email para {cliente.email}")
            return jsonify({
                "error": "Erro ao enviar email",
                "details": "Falha no serviço de email"
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar cupom: {str(e)}")
        return jsonify({"error": f"Erro ao enviar cupom: {str(e)}"}), 500
