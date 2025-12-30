from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import Venda, VendaItem, Produto, Funcionario, MovimentacaoEstoque
import random
import string

vendas_bp = Blueprint("vendas", __name__)


def gerar_codigo_venda():
    """Gera código único para venda no formato V-YYYYMMDD-XXXX"""
    data_atual = datetime.now().strftime("%Y%m%d")
    # 4 dígitos aleatórios
    random_part = "".join(random.choices(string.digits, k=4))
    return f"V-{data_atual}-{random_part}"


@vendas_bp.route("/", methods=["POST"])
def criar_venda():
    """Cria uma nova venda (finalizar compra no PDV)"""
    try:
        data = request.get_json()
        print(f"📦 Dados da venda recebidos: {data}")

        # Validações
        if not data.get("items") or len(data["items"]) == 0:
            return jsonify({"error": "Carrinho vazio"}), 400

        # 1. GERAR CÓDIGO DA VENDA
        codigo_venda = gerar_codigo_venda()

        # Verificar se código já existe (raro, mas possível)
        while Venda.query.filter_by(codigo=codigo_venda).first():
            codigo_venda = gerar_codigo_venda()

        # 2. CRIAR A VENDA
        nova_venda = Venda(
            codigo=codigo_venda,
            cliente_id=data.get("cliente_id"),
            funcionario_id=1,  # Temporário - depois pegar do usuário logado
            subtotal=float(data.get("subtotal", 0)),
            desconto=float(data.get("desconto", 0)),
            total=float(data.get("total", 0)),
            forma_pagamento=data.get("paymentMethod", "dinheiro"),
            valor_recebido=float(data.get("cashReceived", 0)),
            troco=float(data.get("change", 0)),
            status="finalizada",
            observacoes=data.get("observacoes", ""),
        )

        db.session.add(nova_venda)
        db.session.flush()  # Para obter o ID sem commitar

        # 3. ADICIONAR ITENS DA VENDA E ATUALIZAR ESTOQUE
        for item_data in data["items"]:
            produto_id = item_data.get("productId")
            quantidade = item_data.get("quantity", 1)

            # Buscar produto
            produto = Produto.query.get(produto_id)
            if not produto:
                db.session.rollback()
                return jsonify({"error": f"Produto {produto_id} não encontrado"}), 404

            # Verificar estoque
            if produto.quantidade < quantidade:
                db.session.rollback()
                return (
                    jsonify(
                        {
                            "error": f"Estoque insuficiente para {produto.nome}. Disponível: {produto.quantidade}, Solicitado: {quantidade}"
                        }
                    ),
                    400,
                )

            # Criar item da venda
            venda_item = VendaItem(
                venda_id=nova_venda.id,
                produto_id=produto_id,
                quantidade=quantidade,
                preco_unitario=float(item_data.get("price", 0)),
                desconto=0.0,  # Poderia receber desconto por item
                total_item=float(item_data.get("total", 0)),
                produto_nome=produto.nome,
                produto_codigo=produto.codigo_barras,
                produto_unidade=produto.unidade_medida,
            )

            db.session.add(venda_item)

            # 4. ATUALIZAR ESTOQUE DO PRODUTO
            quantidade_anterior = produto.quantidade
            produto.quantidade -= quantidade
            quantidade_atual = produto.quantidade

            # 5. REGISTRAR MOVIMENTAÇÃO DE ESTOQUE
            movimentacao = MovimentacaoEstoque(
                produto_id=produto_id,
                tipo="saida",
                quantidade=quantidade,
                quantidade_anterior=quantidade_anterior,
                quantidade_atual=quantidade_atual,
                motivo=f"Venda #{codigo_venda}",
                observacoes=f"Venda realizada via PDV",
                venda_id=nova_venda.id,
                funcionario_id=1,  # Temporário
            )

            db.session.add(movimentacao)

            # 6. VERIFICAR SE ESTOQUE ESTÁ BAIXO (alerta)
            if produto.quantidade <= produto.quantidade_minima:
                print(
                    f"⚠️ ALERTA: Estoque baixo para {produto.nome} - {produto.quantidade} unidades"
                )

        # 7. FINALIZAR TRANSAÇÃO
        db.session.commit()

        # 8. PREPARAR RESPOSTA
        resposta = {
            "success": True,
            "message": "Venda finalizada com sucesso!",
            "venda": {
                "id": nova_venda.id,
                "codigo": nova_venda.codigo,
                "total": nova_venda.total,
                "data": nova_venda.created_at.isoformat(),
                "troco": nova_venda.troco,
                "forma_pagamento": nova_venda.forma_pagamento,
            },
            "recibo": {
                "cabecalho": "MERCADINHO SYS - COMPROVANTE DE VENDA",
                "codigo": nova_venda.codigo,
                "data": nova_venda.created_at.strftime("%d/%m/%Y %H:%M"),
                "itens": [
                    {
                        "nome": item.produto_nome,
                        "quantidade": item.quantidade,
                        "preco_unitario": item.preco_unitario,
                        "total": item.total_item,
                    }
                    for item in nova_venda.itens
                ],
                "subtotal": nova_venda.subtotal,
                "desconto": nova_venda.desconto,
                "total": nova_venda.total,
                "pagamento": nova_venda.forma_pagamento,
                "recebido": nova_venda.valor_recebido,
                "troco": nova_venda.troco,
                "rodape": "Obrigado pela preferência!",
            },
        }

        print(f"✅ Venda {codigo_venda} finalizada - Total: R$ {nova_venda.total:.2f}")

        return jsonify(resposta), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao finalizar venda: {str(e)}")
        return jsonify({"error": f"Erro ao processar venda: {str(e)}"}), 500
