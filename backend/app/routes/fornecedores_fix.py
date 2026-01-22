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
