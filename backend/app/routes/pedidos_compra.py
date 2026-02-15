# app/routes/pedidos_compra.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload

from app import db
from app.models import (
    PedidoCompra, PedidoCompraItem, Produto, Fornecedor, Funcionario,
    ContaPagar, MovimentacaoEstoque, Despesa, ProdutoLote
)
from app.decorators.decorator_jwt import funcionario_required

pedidos_compra_bp = Blueprint('pedidos_compra', __name__)

def get_current_user():
    """Helper para obter usuário atual"""
    user_id = get_jwt_identity()
    user = Funcionario.query.get(user_id)
    if not user:
        return None
    return user

@pedidos_compra_bp.route('/pedidos-compra/', methods=['GET'])
@funcionario_required
def listar_pedidos():
    """Lista pedidos de compra com filtros e paginação"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Filtros
        status = request.args.get('status')
        fornecedor_id = request.args.get('fornecedor_id')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        query = PedidoCompra.query.filter_by(
            estabelecimento_id=user.estabelecimento_id
        ).options(
            joinedload(PedidoCompra.fornecedor),
            joinedload(PedidoCompra.funcionario),
            joinedload(PedidoCompra.itens),
        )
        
        if status:
            query = query.filter(PedidoCompra.status == status)
        if fornecedor_id:
            query = query.filter(PedidoCompra.fornecedor_id == fornecedor_id)
        if data_inicio:
            query = query.filter(PedidoCompra.data_pedido >= datetime.strptime(data_inicio, '%Y-%m-%d'))
        if data_fim:
            query = query.filter(PedidoCompra.data_pedido <= datetime.strptime(data_fim, '%Y-%m-%d'))
        
        query = query.order_by(PedidoCompra.data_pedido.desc())
        
        pedidos_paginados = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        pedidos = []
        for pedido in pedidos_paginados.items:
            try:
                pedido_dict = pedido.to_dict()
                pedido_dict['fornecedor_nome'] = pedido.fornecedor.nome_fantasia if pedido.fornecedor else None
                pedido_dict['funcionario_nome'] = pedido.funcionario.nome if pedido.funcionario else None
                pedido_dict['total_itens'] = len(pedido.itens) if pedido.itens else 0
                pedido_dict['itens'] = [item.to_dict() for item in pedido.itens] if pedido.itens else []
                pedidos.append(pedido_dict)
            except Exception as e:
                print(f"Erro ao processar pedido {pedido.id}: {str(e)}")
                continue
        
        return jsonify({
            'pedidos': pedidos,
            'paginacao': {
                'pagina_atual': page,
                'total_paginas': pedidos_paginados.pages,
                'total_itens': pedidos_paginados.total,
                'itens_por_pagina': per_page
            }
        })
        
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Erro ao listar pedidos: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@pedidos_compra_bp.route('/pedidos-compra/', methods=['POST'])
@funcionario_required
def criar_pedido():
    """Cria um novo pedido de compra"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        
        # Validações
        if not data.get('fornecedor_id'):
            return jsonify({'error': 'Fornecedor é obrigatório'}), 400
        if not data.get('itens') or len(data.get('itens', [])) == 0:
            return jsonify({'error': 'Pelo menos um item é obrigatório'}), 400
        
        # Verificar se fornecedor existe
        fornecedor = Fornecedor.query.filter_by(
            id=data['fornecedor_id'],
            estabelecimento_id=user.estabelecimento_id
        ).first()
        if not fornecedor:
            return jsonify({'error': 'Fornecedor não encontrado'}), 404
        
        # Gerar número do pedido
        ultimo_pedido = PedidoCompra.query.filter_by(
            estabelecimento_id=user.estabelecimento_id
        ).order_by(PedidoCompra.id.desc()).first()
        
        numero_pedido = f"PC{(ultimo_pedido.id + 1 if ultimo_pedido else 1):06d}"
        
        # Calcular data de previsão de entrega
        data_previsao = date.today() + timedelta(days=fornecedor.prazo_entrega or 7)
        
        # Criar pedido
        pedido = PedidoCompra(
            estabelecimento_id=user.estabelecimento_id,
            fornecedor_id=data['fornecedor_id'],
            funcionario_id=user.id,
            numero_pedido=numero_pedido,
            data_previsao_entrega=data_previsao,
            condicao_pagamento=data.get('condicao_pagamento', fornecedor.forma_pagamento),
            observacoes=data.get('observacoes', ''),
            status='pendente'
        )
        
        db.session.add(pedido)
        db.session.flush()  # Para obter o ID
        
        # Processar itens
        subtotal = Decimal('0')
        for item_data in data['itens']:
            produto = Produto.query.filter_by(
                id=item_data['produto_id'],
                estabelecimento_id=user.estabelecimento_id
            ).first()
            
            if not produto:
                return jsonify({'error': f'Produto ID {item_data["produto_id"]} não encontrado'}), 404
            
            quantidade = int(item_data['quantidade'])
            preco_unitario = Decimal(str(item_data.get('preco_unitario', produto.preco_custo)))
            desconto = Decimal(str(item_data.get('desconto_percentual', 0)))
            
            total_item = quantidade * preco_unitario * (1 - desconto / 100)
            
            item = PedidoCompraItem(
                pedido_id=pedido.id,
                produto_id=produto.id,
                produto_nome=produto.nome,
                produto_unidade=produto.unidade_medida,
                quantidade_solicitada=quantidade,
                preco_unitario=preco_unitario,
                desconto_percentual=desconto,
                total_item=total_item,
                status='pendente'
            )
            
            db.session.add(item)
            subtotal += total_item
        
        # Calcular totais
        desconto_pedido = Decimal(str(data.get('desconto', 0)))
        frete = Decimal(str(data.get('frete', 0)))
        total = subtotal - desconto_pedido + frete
        
        pedido.subtotal = subtotal
        pedido.desconto = desconto_pedido
        pedido.frete = frete
        pedido.total = total

        # ERP: criar Conta a Pagar ao emitir o pedido (obrigação financeira)
        # A Despesa é criada quando o boleto for pago (pagar boleto)
        data_vencimento = data_previsao or (date.today() + timedelta(days=30))
        conta_pagar = ContaPagar(
            estabelecimento_id=user.estabelecimento_id,
            fornecedor_id=pedido.fornecedor_id,
            pedido_compra_id=pedido.id,
            numero_documento=f'PC-{numero_pedido}',
            tipo_documento='pedido_compra',
            valor_original=total,
            valor_atual=total,
            data_emissao=date.today(),
            data_vencimento=data_vencimento,
            status='aberto',
            observacoes=f'Pedido de compra {numero_pedido}' + (f' - {pedido.observacoes}' if pedido.observacoes else ''),
        )
        db.session.add(conta_pagar)

        db.session.commit()

        return jsonify({
            'message': 'Pedido criado com sucesso',
            'pedido': pedido.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@pedidos_compra_bp.route('/pedidos-compra/<int:pedido_id>', methods=['GET'])
@funcionario_required
def obter_pedido(pedido_id):
    """Obtém detalhes de um pedido específico"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        pedido = PedidoCompra.query.filter_by(
            id=pedido_id,
            estabelecimento_id=user.estabelecimento_id
        ).options(
            joinedload(PedidoCompra.fornecedor),
            joinedload(PedidoCompra.funcionario),
            joinedload(PedidoCompra.itens).joinedload(PedidoCompraItem.produto)
        ).first()
        
        if not pedido:
            return jsonify({'error': 'Pedido não encontrado'}), 404
        
        pedido_dict = pedido.to_dict()
        pedido_dict['fornecedor'] = pedido.fornecedor.to_dict() if pedido.fornecedor else None
        pedido_dict['funcionario'] = pedido.funcionario.to_dict() if pedido.funcionario else None
        pedido_dict['itens'] = [item.to_dict() for item in pedido.itens]
        
        # Adicionar informações de conta a pagar se existir
        if pedido.conta_pagar:
            pedido_dict['conta_pagar'] = pedido.conta_pagar.to_dict()
        
        return jsonify({'pedido': pedido_dict})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pedidos_compra_bp.route('/pedidos-compra/receber', methods=['POST'])
@funcionario_required
def receber_pedido_compra():
    """Confirma o recebimento de um pedido e atualiza estoque com sistema de lotes"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        
        pedido = PedidoCompra.query.filter_by(
            id=pedido_id,
            estabelecimento_id=user.estabelecimento_id
        ).first()
        
        if not pedido:
            return jsonify({'error': 'Pedido não encontrado'}), 404
        
        if pedido.status != 'pendente':
            return jsonify({'error': 'Pedido já foi processado'}), 400
        
        # Processar recebimento dos itens
        itens_recebidos = data.get('itens', [])
        total_recebido = Decimal('0')
        
        for item_data in itens_recebidos:
            item = PedidoCompraItem.query.filter_by(
                id=item_data['item_id'],
                pedido_id=pedido.id
            ).first()
            
            if not item:
                continue
            
            quantidade_recebida = int(item_data.get('quantidade_recebida', 0))
            if quantidade_recebida <= 0:
                continue
            
            # Atualizar item
            item.quantidade_recebida = quantidade_recebida
            item.status = 'recebido' if quantidade_recebida >= item.quantidade_solicitada else 'parcial'
            
            # Atualizar estoque do produto
            produto = item.produto
            if produto:
                # Obter data de validade do item (se fornecida)
                data_validade = None
                if item_data.get('data_validade'):
                    from datetime import datetime as dt
                    data_validade = dt.strptime(item_data['data_validade'], '%Y-%m-%d').date()
                
                # Criar lote para este recebimento
                numero_lote = item_data.get('numero_lote', f"LOTE-{pedido.numero_pedido}-{item.id}")
                
                lote = ProdutoLote(
                    estabelecimento_id=user.estabelecimento_id,
                    produto_id=produto.id,
                    fornecedor_id=pedido.fornecedor_id,
                    pedido_compra_id=pedido.id,
                    numero_lote=numero_lote,
                    quantidade=quantidade_recebida,
                    quantidade_inicial=quantidade_recebida,
                    data_validade=data_validade or (date.today() + timedelta(days=365)),  # Padrão: 1 ano
                    data_entrada=date.today(),
                    preco_custo_unitario=item.preco_unitario,
                    ativo=True,
                )
                
                db.session.add(lote)
                
                # Recalcular preço de custo médio ponderado ANTES de atualizar o estoque
                if hasattr(produto, 'recalcular_preco_custo_ponderado'):
                    try:
                        produto.recalcular_preco_custo_ponderado(
                            quantidade_entrada=quantidade_recebida,
                            custo_unitario_entrada=item.preco_unitario,
                            funcionario_id=user.id,
                            motivo=f'Recebimento pedido {pedido.numero_pedido}'
                        )
                    except Exception as ex:
                        from flask import current_app
                        current_app.logger.warning(
                            f"recalcular_preco_custo_ponderado ignorado para produto {produto.id}: {ex}"
                        )

                # Movimentar estoque (atualiza produto.quantidade e cria MovimentacaoEstoque)
                movimentacao = produto.movimentar_estoque(
                    quantidade=quantidade_recebida,
                    tipo='entrada',
                    motivo=f'Recebimento pedido {pedido.numero_pedido}. Lote: {numero_lote}',
                    usuario_id=user.id
                )
                movimentacao.pedido_compra_id = pedido.id
                db.session.add(movimentacao)
            
            total_recebido += item.preco_unitario * quantidade_recebida
        
        # Atualizar pedido
        pedido.data_recebimento = date.today()
        pedido.status = 'recebido'
        pedido.numero_nota_fiscal = data.get('numero_nota_fiscal', '')
        pedido.serie_nota_fiscal = data.get('serie_nota_fiscal', '')

        # Conta a pagar: usar a criada na emissão do pedido ou criar se recebimento pedir boleto
        conta_existente = getattr(pedido, 'conta_pagar', None) or (
            ContaPagar.query.filter_by(pedido_compra_id=pedido.id, estabelecimento_id=user.estabelecimento_id).first()
        )
        if conta_existente:
            # Atualizar valor com o total realmente recebido (pode diferir do pedido)
            conta_existente.valor_original = total_recebido
            conta_existente.valor_atual = total_recebido
            if data.get('numero_documento'):
                conta_existente.numero_documento = data.get('numero_documento')
        elif data.get('gerar_boleto', False):
            data_vencimento_str = data.get('data_vencimento')
            if not data_vencimento_str:
                dias_prazo = 30
                if pedido.condicao_pagamento:
                    try:
                        dias_prazo = int(str(pedido.condicao_pagamento).split()[0])
                    except (ValueError, IndexError):
                        pass
                data_vencimento = date.today() + timedelta(days=dias_prazo)
            else:
                data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date()

            conta_pagar = ContaPagar(
                estabelecimento_id=user.estabelecimento_id,
                fornecedor_id=pedido.fornecedor_id,
                pedido_compra_id=pedido.id,
                numero_documento=data.get('numero_documento', f'BOL-{pedido.numero_pedido}'),
                tipo_documento='boleto',
                valor_original=total_recebido,
                valor_atual=total_recebido,
                data_emissao=date.today(),
                data_vencimento=data_vencimento,
                status='aberto',
                observacoes=f'Referente ao pedido {pedido.numero_pedido}'
            )
            db.session.add(conta_pagar)

        db.session.commit()
        
        return jsonify({
            'message': 'Pedido recebido com sucesso',
            'pedido': pedido.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@pedidos_compra_bp.route('/boletos-fornecedores/', methods=['GET'])
@funcionario_required
def listar_boletos():
    """Lista boletos de fornecedores com filtros"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Filtros
        status = request.args.get('status', 'aberto')
        fornecedor_id = request.args.get('fornecedor_id')
        vencimento_ate = request.args.get('vencimento_ate')
        apenas_vencidos = request.args.get('apenas_vencidos') == 'true'
        
        query = ContaPagar.query.filter_by(
            estabelecimento_id=user.estabelecimento_id
        ).options(
            joinedload(ContaPagar.fornecedor),
            joinedload(ContaPagar.pedido_compra)
        )
        
        if status:
            query = query.filter(ContaPagar.status == status)
        if fornecedor_id:
            query = query.filter(ContaPagar.fornecedor_id == fornecedor_id)
        if vencimento_ate:
            query = query.filter(ContaPagar.data_vencimento <= datetime.strptime(vencimento_ate, '%Y-%m-%d').date())
        if apenas_vencidos:
            query = query.filter(ContaPagar.data_vencimento < date.today())
        
        query = query.order_by(ContaPagar.data_vencimento.asc())
        
        boletos_paginados = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        boletos = []
        for conta in boletos_paginados.items:
            conta_dict = conta.to_dict()
            conta_dict['fornecedor_nome'] = conta.fornecedor.nome_fantasia if conta.fornecedor else None
            conta_dict['pedido_numero'] = conta.pedido_compra.numero_pedido if conta.pedido_compra else None
            conta_dict['pedido_id'] = conta.pedido_compra.id if conta.pedido_compra else None
            conta_dict['data_pedido'] = conta.pedido_compra.data_pedido.isoformat() if conta.pedido_compra and conta.pedido_compra.data_pedido else None
            conta_dict['itens'] = [item.to_dict() for item in conta.pedido_compra.itens] if conta.pedido_compra else []
            
            # Calcular dias para vencimento
            if conta.data_vencimento:
                dias_vencimento = (conta.data_vencimento - date.today()).days
                conta_dict['dias_vencimento'] = dias_vencimento
                conta_dict['status_vencimento'] = (
                    'vencido' if dias_vencimento < 0 else
                    'vence_hoje' if dias_vencimento == 0 else
                    'vence_em_breve' if dias_vencimento <= 7 else
                    'normal'
                )
            
            boletos.append(conta_dict)
        
        # Estatísticas
        stats = {
            'total_aberto': db.session.query(func.sum(ContaPagar.valor_atual)).filter(
                ContaPagar.estabelecimento_id == user.estabelecimento_id,
                ContaPagar.status == 'aberto'
            ).scalar() or 0,
            'vencidos': db.session.query(func.count(ContaPagar.id)).filter(
                ContaPagar.estabelecimento_id == user.estabelecimento_id,
                ContaPagar.status == 'aberto',
                ContaPagar.data_vencimento < date.today()
            ).scalar() or 0,
            'vence_hoje': db.session.query(func.count(ContaPagar.id)).filter(
                ContaPagar.estabelecimento_id == user.estabelecimento_id,
                ContaPagar.status == 'aberto',
                ContaPagar.data_vencimento == date.today()
            ).scalar() or 0,
            'vence_7_dias': db.session.query(func.count(ContaPagar.id)).filter(
                ContaPagar.estabelecimento_id == user.estabelecimento_id,
                ContaPagar.status == 'aberto',
                ContaPagar.data_vencimento.between(date.today(), date.today() + timedelta(days=7))
            ).scalar() or 0
        }
        
        return jsonify({
            'boletos': boletos,
            'estatisticas': stats,
            'paginacao': {
                'pagina_atual': page,
                'total_paginas': boletos_paginados.pages,
                'total_itens': boletos_paginados.total,
                'itens_por_pagina': per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pedidos_compra_bp.route('/produtos/<int:produto_id>/lotes-disponiveis', methods=['GET'])
@funcionario_required
def listar_lotes_disponiveis(produto_id):
    """Lista lotes disponíveis de um produto ordenados por FIFO (validade)"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        produto = Produto.query.filter_by(
            id=produto_id,
            estabelecimento_id=user.estabelecimento_id
        ).first()
        
        if not produto:
            return jsonify({'error': 'Produto não encontrado'}), 404
        
        # Buscar lotes ativos ordenados por data de validade (FIFO)
        lotes = ProdutoLote.query.filter_by(
            produto_id=produto_id,
            estabelecimento_id=user.estabelecimento_id,
            ativo=True
        ).filter(
            ProdutoLote.quantidade > 0  # Apenas lotes com quantidade disponível
        ).order_by(
            ProdutoLote.data_validade.asc()  # FIFO: primeiro a vencer primeiro
        ).all()
        
        lotes_dict = [lote.to_dict() for lote in lotes]
        
        return jsonify({
            'produto_id': produto_id,
            'produto_nome': produto.nome,
            'total_quantidade': produto.quantidade,
            'lotes': lotes_dict,
            'total_lotes': len(lotes_dict)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pedidos_compra_bp.route('/boletos/<int:conta_id>/pagar', methods=['POST'])
@funcionario_required
def pagar_boleto(conta_id):
    """Registra o pagamento de um boleto"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        
        conta = ContaPagar.query.filter_by(
            id=conta_id,
            estabelecimento_id=user.estabelecimento_id
        ).first()
        
        if not conta:
            return jsonify({'error': 'Boleto não encontrado'}), 404
        
        if conta.status != 'aberto':
            return jsonify({'error': 'Boleto já foi pago'}), 400
        
        valor_pago = Decimal(str(data.get('valor_pago', conta.valor_atual)))
        data_pagamento = datetime.strptime(data.get('data_pagamento', date.today().isoformat()), '%Y-%m-%d').date()
        
        # Atualizar conta
        conta.valor_pago = valor_pago
        conta.valor_atual = conta.valor_original - valor_pago
        conta.data_pagamento = data_pagamento
        conta.forma_pagamento = data.get('forma_pagamento', 'Transferência')
        conta.status = 'pago' if conta.valor_atual <= 0 else 'parcial'
        conta.observacoes = data.get('observacoes', conta.observacoes)
        
        # Criar despesa correspondente
        despesa = Despesa(
            estabelecimento_id=user.estabelecimento_id,
            fornecedor_id=conta.fornecedor_id,
            descricao=f'Pagamento {conta.numero_documento} - {conta.fornecedor.nome_fantasia if conta.fornecedor else "Fornecedor"}',
            categoria='Fornecedores',
            tipo='variavel',
            valor=valor_pago,
            data_despesa=data_pagamento,
            forma_pagamento=conta.forma_pagamento,
            recorrente=False,
            observacoes=f'Pagamento de boleto - Pedido: {conta.pedido_compra.numero_pedido if conta.pedido_compra else "N/A"}'
        )
        
        db.session.add(despesa)
        db.session.commit()
        
        return jsonify({
            'message': 'Pagamento registrado com sucesso',
            'conta': conta.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
