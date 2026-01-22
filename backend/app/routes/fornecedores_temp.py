"""
ROTA TEMPORÁRIA DE FORNECEDORES - PARA TESTE
Copie este conteúdo para fornecedores.py se quiser testar
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt
from app.decorators.decorator_jwt import funcionario_required
from app.models import db, Fornecedor, Produto

fornecedores_bp = Blueprint("fornecedores", __name__)

@fornecedores_bp.route("", methods=["GET"])
@funcionario_required
def listar_fornecedores():
    """Lista todos os fornecedores com filtros e paginação"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        
        current_app.logger.info(f"🔍 Listando fornecedores para estabelecimento {estabelecimento_id}")
        
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 50, type=int)
        
        # Query base
        query = Fornecedor.query.filter_by(estabelecimento_id=estabelecimento_id)
        
        # Ordenação
        query = query.order_by(Fornecedor.nome_fantasia.asc())
        
        # Paginação
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        
        fornecedores = []
        for fornecedor in paginacao.items:
            # Contar produtos ativos
            produtos_ativos = Produto.query.filter_by(
                fornecedor_id=fornecedor.id,
                ativo=True,
                estabelecimento_id=estabelecimento_id,
            ).count()
            
            fornecedores.append({
                "id": fornecedor.id,
                "nome_fantasia": fornecedor.nome_fantasia,
                "razao_social": fornecedor.razao_social,
                "cnpj": fornecedor.cnpj,
                "telefone": fornecedor.telefone,
                "email": fornecedor.email,
                "cidade": fornecedor.cidade,
                "estado": fornecedor.estado,
                "ativo": fornecedor.ativo,
                "produtos_ativos": produtos_ativos,
                "classificacao": fornecedor.classificacao or "REGULAR",
            })
        
        current_app.logger.info(f"✅ Retornando {len(fornecedores)} fornecedores")
        
        return jsonify({
            "success": True,
            "fornecedores": fornecedores,
            "total": paginacao.total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_paginas": paginacao.pages,
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao listar fornecedores: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
