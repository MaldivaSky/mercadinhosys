"""ROTA DE FORNECEDORES - VERSÃO QUE FUNCIONA"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from app.models import db, Fornecedor, Produto

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
