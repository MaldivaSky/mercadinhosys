"""ROTA DE FORNECEDORES - VERSÃO QUE FUNCIONA"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from app.models import db, Fornecedor, Produto, PedidoCompra, ContaPagar
from datetime import datetime, date

fornecedores_fix_bp = Blueprint("fornecedores_fix", __name__)

@fornecedores_fix_bp.route("", methods=["GET", "OPTIONS"])
@fornecedores_fix_bp.route("/", methods=["GET", "OPTIONS"])
def listar():
    # Responder OPTIONS sem autenticação
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
    
    # Aplicar autenticação apenas para GET
    from flask_jwt_extended import verify_jwt_in_request
    verify_jwt_in_request()
        
    try:
        jwt_data = get_jwt()
        est_id = jwt_data.get("estabelecimento_id", 1)
        
        fornecedores = Fornecedor.query.filter_by(estabelecimento_id=est_id).all()
        
        lista = []
        for f in fornecedores:
            prods = Produto.query.filter_by(fornecedor_id=f.id, ativo=True).count()
            lista.append({
                "id": f.id,
                "nome": f.nome_fantasia or f.razao_social,
                "nome_fantasia": f.nome_fantasia,
                "razao_social": f.razao_social,
                "cnpj": f.cnpj,
                "telefone": f.telefone,
                "email": f.email,
                "cidade": f.cidade,
                "estado": f.estado,
                "ativo": f.ativo,
                "produtos_ativos": prods,
                "total_produtos": prods,
                "classificacao": f.classificacao or "REGULAR",
                "total_compras": f.total_compras or 0,
                "valor_total_comprado": float(f.valor_total_comprado or 0),
            })
        
        return jsonify({"success": True, "fornecedores": lista, "total": len(lista)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@fornecedores_fix_bp.route("/<int:id>", methods=["GET", "OPTIONS"])
def obter_fornecedor(id):
    """Obtém detalhes de um fornecedor específico"""
    # Responder OPTIONS sem autenticação
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
    
    # Aplicar autenticação apenas para GET
    from flask_jwt_extended import verify_jwt_in_request
    verify_jwt_in_request()
        
    try:
        jwt_data = get_jwt()
        est_id = jwt_data.get("estabelecimento_id", 1)
        
        fornecedor = Fornecedor.query.filter_by(id=id, estabelecimento_id=est_id).first_or_404()
        
        # Contar produtos ativos
        produtos_ativos = Produto.query.filter_by(fornecedor_id=id, ativo=True).count()
        
        fornecedor_dict = {
            "id": fornecedor.id,
            "nome": fornecedor.nome_fantasia or fornecedor.razao_social,
            "nome_fantasia": fornecedor.nome_fantasia,
            "razao_social": fornecedor.razao_social,
            "cnpj": fornecedor.cnpj,
            "telefone": fornecedor.telefone,
            "email": fornecedor.email,
            "contato_nome": fornecedor.contato_nome,
            "contato_telefone": fornecedor.contato_telefone,
            "cep": fornecedor.cep,
            "logradouro": fornecedor.logradouro,
            "numero": fornecedor.numero,
            "complemento": fornecedor.complemento,
            "bairro": fornecedor.bairro,
            "cidade": fornecedor.cidade,
            "estado": fornecedor.estado,
            "pais": fornecedor.pais,
            "prazo_entrega": fornecedor.prazo_entrega,
            "forma_pagamento": fornecedor.forma_pagamento,
            "classificacao": fornecedor.classificacao or "REGULAR",
            "ativo": fornecedor.ativo,
            "produtos_ativos": produtos_ativos,
            "total_compras": fornecedor.total_compras or 0,
            "valor_total_comprado": float(fornecedor.valor_total_comprado or 0),
        }
        
        return jsonify({"success": True, "fornecedor": fornecedor_dict})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@fornecedores_fix_bp.route("", methods=["POST", "OPTIONS"])
@fornecedores_fix_bp.route("/", methods=["POST", "OPTIONS"])
def criar():
    # Responder OPTIONS sem autenticação
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    # Aplicar autenticação apenas para POST
    from flask_jwt_extended import verify_jwt_in_request
    verify_jwt_in_request()

    try:
        jwt_data = get_jwt()
        est_id = jwt_data.get("estabelecimento_id", 1)

        data = request.get_json()

        # Criar fornecedor
        fornecedor = Fornecedor(
            estabelecimento_id=est_id,
            nome_fantasia=data.get("nome_fantasia", "").strip(),
            razao_social=data.get("razao_social", "").strip(),
            cnpj=data.get("cnpj", "").strip(),
            telefone=data.get("telefone", "").strip(),
            email=data.get("email", "").strip(),
            contato_nome=data.get("contato_nome", "").strip(),
            contato_telefone=data.get("contato_telefone", "").strip(),
            prazo_entrega=data.get("prazo_entrega", 7),
            forma_pagamento=data.get("forma_pagamento", "30 DIAS"),
            classificacao=data.get("classificacao", "REGULAR"),
            cep=data.get("cep", "").strip(),
            logradouro=data.get("logradouro", "").strip(),
            numero=data.get("numero", "0"),
            complemento=data.get("complemento", "").strip(),
            bairro=data.get("bairro", "").strip(),
            cidade=data.get("cidade", "").strip(),
            estado=data.get("estado", "").strip(),
            pais=data.get("pais", "Brasil"),
            ativo=data.get("ativo", True),
            total_compras=0,
            valor_total_comprado=0.0,
        )

        db.session.add(fornecedor)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Fornecedor criado com sucesso",
            "fornecedor": {
                "id": fornecedor.id,
                "nome": fornecedor.nome_fantasia or fornecedor.razao_social,
                "nome_fantasia": fornecedor.nome_fantasia,
                "razao_social": fornecedor.razao_social,
                "cnpj": fornecedor.cnpj,
                "telefone": fornecedor.telefone,
                "email": fornecedor.email,
                "cidade": fornecedor.cidade,
                "estado": fornecedor.estado,
                "ativo": fornecedor.ativo,
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@fornecedores_fix_bp.route("/<int:id>", methods=["PUT", "OPTIONS"])
def atualizar(id):
    # Responder OPTIONS sem autenticação
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    # Aplicar autenticação apenas para PUT
    from flask_jwt_extended import verify_jwt_in_request
    verify_jwt_in_request()

    try:
        jwt_data = get_jwt()
        est_id = jwt_data.get("estabelecimento_id", 1)

        fornecedor = Fornecedor.query.filter_by(id=id, estabelecimento_id=est_id).first_or_404()

        data = request.get_json()

        # Atualizar campos
        campos_atualizaveis = [
            "nome_fantasia", "razao_social", "cnpj", "telefone", "email",
            "contato_nome", "contato_telefone", "prazo_entrega", "forma_pagamento",
            "classificacao", "cep", "logradouro", "numero", "complemento",
            "bairro", "cidade", "estado", "pais", "ativo"
        ]

        for campo in campos_atualizaveis:
            if campo in data:
                if campo == "ativo":
                    setattr(fornecedor, campo, bool(data[campo]))
                else:
                    setattr(fornecedor, campo, data[campo].strip() if isinstance(data[campo], str) else data[campo])

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Fornecedor atualizado com sucesso",
            "fornecedor": {
                "id": fornecedor.id,
                "nome": fornecedor.nome_fantasia or fornecedor.razao_social,
                "nome_fantasia": fornecedor.nome_fantasia,
                "razao_social": fornecedor.razao_social,
                "cnpj": fornecedor.cnpj,
                "telefone": fornecedor.telefone,
                "email": fornecedor.email,
                "cidade": fornecedor.cidade,
                "estado": fornecedor.estado,
                "ativo": fornecedor.ativo,
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@fornecedores_fix_bp.route("/<int:id>", methods=["DELETE", "OPTIONS"])
def deletar(id):
    # Responder OPTIONS sem autenticação
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    # Aplicar autenticação apenas para DELETE
    from flask_jwt_extended import verify_jwt_in_request
    verify_jwt_in_request()

    try:
        jwt_data = get_jwt()
        est_id = jwt_data.get("estabelecimento_id", 1)

        fornecedor = Fornecedor.query.filter_by(id=id, estabelecimento_id=est_id).first_or_404()

        # Verificar se tem produtos associados
        produtos_count = Produto.query.filter_by(fornecedor_id=id, ativo=True).count()
        if produtos_count > 0:
            return jsonify({
                "success": False,
                "error": f"Não é possível excluir fornecedor com {produtos_count} produto(s) ativo(s)"
            }), 400

        db.session.delete(fornecedor)
        db.session.commit()

        return jsonify({"success": True, "message": "Fornecedor excluído com sucesso"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@fornecedores_fix_bp.route("/relatorio/analitico", methods=["GET", "OPTIONS"])
def relatorio_analitico_fornecedores():
    """Gera relatório analítico detalhado dos fornecedores"""
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    from flask_jwt_extended import verify_jwt_in_request
    verify_jwt_in_request()

    try:
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id", 1)

        data_inicio = request.args.get("data_inicio", None)
        data_fim = request.args.get("data_fim", None)
        classificacao = request.args.get("classificacao", None, type=str)

        query = Fornecedor.query.filter_by(
            estabelecimento_id=estabelecimento_id, ativo=True
        )

        if classificacao:
            query = query.filter_by(classificacao=classificacao.upper())

        fornecedores = query.all()

        relatorio = []
        for fornecedor in fornecedores:
            pedidos_query = PedidoCompra.query.filter_by(
                fornecedor_id=fornecedor.id,
                estabelecimento_id=estabelecimento_id,
            )

            if data_inicio:
                pedidos_query = pedidos_query.filter(
                    PedidoCompra.data_pedido >= datetime.fromisoformat(data_inicio)
                )

            if data_fim:
                pedidos_query = pedidos_query.filter(
                    PedidoCompra.data_pedido <= datetime.fromisoformat(data_fim)
                )

            pedidos = pedidos_query.all()

            total_pedidos = len(pedidos)
            valor_total = sum(float(p.total) for p in pedidos if p.total)
            pedidos_pendentes = len([p for p in pedidos if p.status == "pendente"])
            pedidos_concluidos = len([p for p in pedidos if p.status == "concluido"])

            tempos_entrega = []
            for p in pedidos:
                if p.status == "concluido" and p.data_pedido and p.data_recebimento:
                    try:
                        d_pedido = p.data_pedido.date() if hasattr(p.data_pedido, 'date') else p.data_pedido
                        d_receb = p.data_recebimento if not hasattr(p.data_recebimento, 'date') else p.data_recebimento.date() if hasattr(p.data_recebimento, 'date') else p.data_recebimento
                        dias = (d_receb - d_pedido).days
                        if dias > 0:
                            tempos_entrega.append(dias)
                    except Exception:
                        pass

            media_entrega = (
                sum(tempos_entrega) / len(tempos_entrega) if tempos_entrega else 0
            )

            produtos = Produto.query.filter_by(
                fornecedor_id=fornecedor.id,
                estabelecimento_id=estabelecimento_id,
                ativo=True,
            ).all()

            total_produtos = len(produtos)

            # Boletos / Contas a Pagar do fornecedor
            boletos_query = ContaPagar.query.filter_by(
                fornecedor_id=fornecedor.id,
                estabelecimento_id=estabelecimento_id,
            )
            boletos_all = boletos_query.all()
            hoje = date.today()

            boletos_abertos = [b for b in boletos_all if b.status == "aberto"]
            boletos_vencidos = [b for b in boletos_abertos if b.data_vencimento and b.data_vencimento < hoje]
            boletos_pagos = [b for b in boletos_all if b.status == "pago"]

            valor_boletos_aberto = sum(float(b.valor_atual or b.valor_original or 0) for b in boletos_abertos)
            valor_boletos_vencido = sum(float(b.valor_atual or b.valor_original or 0) for b in boletos_vencidos)
            valor_boletos_pago = sum(float(b.valor_pago or 0) for b in boletos_pagos)

            relatorio.append({
                "fornecedor": {
                    "id": fornecedor.id,
                    "nome": fornecedor.nome_fantasia or fornecedor.razao_social,
                    "cnpj": fornecedor.cnpj,
                    "classificacao": fornecedor.classificacao,
                    "prazo_entrega_padrao": getattr(fornecedor, 'prazo_entrega', None),
                },
                "metricas": {
                    "total_pedidos": total_pedidos,
                    "valor_total": valor_total,
                    "pedidos_pendentes": pedidos_pendentes,
                    "pedidos_concluidos": pedidos_concluidos,
                    "taxa_conclusao": round(
                        (pedidos_concluidos / total_pedidos * 100)
                        if total_pedidos > 0
                        else 0, 1
                    ),
                    "media_entrega_dias": round(media_entrega, 1),
                    "total_produtos": total_produtos,
                },
                "boletos": {
                    "total_abertos": len(boletos_abertos),
                    "valor_aberto": round(valor_boletos_aberto, 2),
                    "total_vencidos": len(boletos_vencidos),
                    "valor_vencido": round(valor_boletos_vencido, 2),
                    "total_pagos": len(boletos_pagos),
                    "valor_pago": round(valor_boletos_pago, 2),
                },
                "produtos": [
                    {
                        "id": p.id,
                        "nome": p.nome,
                        "preco_custo": float(p.preco_custo) if p.preco_custo else 0,
                        "quantidade_estoque": p.quantidade,
                    }
                    for p in produtos[:10]
                ],
            })

        return jsonify({
            "success": True,
            "relatorio": relatorio,
            "total_fornecedores": len(relatorio),
            "filtros": {
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "classificacao": classificacao,
            },
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
