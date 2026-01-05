# app/routes/pdv.py
"""
PDV - Ponto de Venda
Rotas otimizadas para operações em tempo real no PDV
Separado de vendas.py para melhor performance e manutenibilidade
"""

from datetime import datetime
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
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func
import random
import string

pdv_bp = Blueprint("pdv", __name__)

# ==================== FUNÇÕES AUXILIARES ====================

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
    """Calcula subtotal, desconto e total da venda"""
    subtotal = sum(item['total_item'] for item in itens)
    
    # Calcular desconto
    if desconto_percentual:
        desconto_valor = subtotal * (desconto_geral / 100)
    else:
        desconto_valor = desconto_geral
    
    desconto_valor = min(desconto_valor, subtotal)  # Desconto não pode ser maior que subtotal
    total = subtotal - desconto_valor
    
    return {
        'subtotal': round(subtotal, 2),
        'desconto': round(desconto_valor, 2),
        'total': round(total, 2)
    }


# ==================== ROTAS PDV ====================

@pdv_bp.route("/configuracoes", methods=["GET"])
@funcionario_required
def obter_configuracoes_pdv():
    """
    Retorna configurações do PDV para o funcionário logado
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
        
        return jsonify({
            "success": True,
            "configuracoes": {
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
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter configurações PDV: {str(e)}")
        return jsonify({"error": "Erro ao carregar configurações"}), 500


@pdv_bp.route("/validar-produto", methods=["POST"])
@funcionario_required
def validar_produto():
    """
    Valida se produto está disponível e retorna informações completas
    Útil para busca por código de barras ou ID
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
        return jsonify({
            "valido": True,
            "produto": {
                "id": produto.id,
                "nome": produto.nome,
                "codigo_barras": produto.codigo_barras,
                "preco_venda": float(produto.preco_venda),
                "preco_custo": float(produto.preco_custo) if produto.preco_custo else 0,
                "quantidade_estoque": produto.quantidade,
                "categoria": produto.categoria,
                "marca": produto.marca,
                "unidade_medida": produto.unidade_medida,
                "margem_lucro": float(produto.margem_lucro) if produto.margem_lucro else 0,
                "ativo": produto.ativo,
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
    """
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        if not funcionario:
            return jsonify({"error": "Funcionário não encontrado"}), 404
        
        data = request.get_json()
        
        # ===== VALIDAÇÕES =====
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        items = data.get("items", [])
        if not items or len(items) == 0:
            return jsonify({"error": "Nenhum produto na venda"}), 400
        
        # Validar valores numéricos
        try:
            subtotal = float(data.get("subtotal", 0))
            desconto_geral = float(data.get("desconto", 0))
            total = float(data.get("total", 0))
            valor_recebido = float(data.get("valor_recebido", total))
            troco = float(data.get("troco", 0))
        except ValueError:
            return jsonify({"error": "Valores numéricos inválidos"}), 400
        
        forma_pagamento = data.get("paymentMethod", "dinheiro")
        cliente_id = data.get("cliente_id")
        observacoes = data.get("observacoes", "")
        
        # ===== INÍCIO DA TRANSAÇÃO =====
        try:
            # 1. GERAR CÓDIGO DA VENDA
            codigo_venda = gerar_codigo_venda()
            
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
            
            # 3. PROCESSAR ITENS
            itens_processados = []
            produtos_atualizados = []
            
            for item_data in items:
                produto_id = item_data.get("id")
                quantidade = int(item_data.get("quantity", 1))
                desconto_item = float(item_data.get("discount", 0))
                
                # Buscar produto com lock (evita race condition)
                produto = db.session.query(Produto).with_for_update().get(produto_id)
                
                if not produto:
                    raise ValueError(f"Produto {produto_id} não encontrado")
                
                if not produto.ativo:
                    raise ValueError(f"Produto '{produto.nome}' está inativo")
                
                if produto.quantidade < quantidade:
                    raise ValueError(
                        f"Estoque insuficiente para '{produto.nome}'. "
                        f"Disponível: {produto.quantidade}, Solicitado: {quantidade}"
                    )
                
                # Calcular valores
                preco_unitario = float(produto.preco_venda)
                total_item = (preco_unitario * quantidade) - desconto_item
                
                # Criar item da venda
                venda_item = VendaItem(
                    venda_id=nova_venda.id,
                    produto_id=produto.id,
                    produto_nome=produto.nome,
                    descricao=produto.descricao,
                    produto_codigo=produto.codigo_barras,
                    produto_unidade=produto.unidade_medida,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    desconto=desconto_item,
                    total_item=total_item,
                    custo_unitario=produto.preco_custo,
                    margem_item=round(
                        ((preco_unitario - (produto.preco_custo or 0)) / preco_unitario * 100)
                        if preco_unitario > 0 else 0,
                        2
                    )
                )
                
                db.session.add(venda_item)
                
                # Atualizar estoque
                estoque_anterior = produto.quantidade
                produto.quantidade -= quantidade
                produto.updated_at = datetime.now()
                
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
            db.session.commit()
            
            # 5. LOG DE SUCESSO
            current_app.logger.info(
                f"✅ Venda {codigo_venda} finalizada | "
                f"Total: R$ {total:.2f} | "
                f"Itens: {len(itens_processados)} | "
                f"Funcionário: {funcionario.nome}"
            )
            
            # 6. PREPARAR RESPOSTA
            return jsonify({
                "success": True,
                "message": "Venda finalizada com sucesso!",
                "venda": {
                    "id": nova_venda.id,
                    "codigo": codigo_venda,
                    "total": total,
                    "subtotal": subtotal,
                    "desconto": desconto_geral,
                    "troco": troco,
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
                    "subtotal": subtotal,
                    "desconto": desconto_geral,
                    "total": total,
                    "forma_pagamento": forma_pagamento.replace("_", " ").title(),
                    "valor_recebido": valor_recebido,
                    "troco": troco,
                    "rodape": "Obrigado pela preferência!",
                }
            }), 201
            
        except ValueError as ve:
            db.session.rollback()
            current_app.logger.warning(f"⚠️ Validação falhou: {str(ve)}")
            return jsonify({"error": str(ve)}), 400
            
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
        
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        
        # Query otimizada
        stats = db.session.query(
            func.count(Venda.id).label("total_vendas"),
            func.sum(Venda.total).label("faturamento"),
            func.avg(Venda.total).label("ticket_medio"),
        ).filter(
            Venda.estabelecimento_id == funcionario.estabelecimento_id,
            Venda.data_venda >= inicio_dia,
            Venda.status == "finalizada"
        ).first()
        
        return jsonify({
            "success": True,
            "estatisticas": {
                "total_vendas": stats.total_vendas or 0,
                "faturamento": round(float(stats.faturamento or 0), 2),
                "ticket_medio": round(float(stats.ticket_medio or 0), 2),
                "funcionario": funcionario.nome,
                "hora_atual": datetime.now().strftime("%H:%M"),
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro nas estatísticas: {str(e)}")
        return jsonify({"error": "Erro ao carregar estatísticas"}), 500
