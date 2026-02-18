# app/fornecedores.py
# MÓDULO COMPLETO DE FORNECEDORES - ERP INDUSTRIAL BRASILEIRO
# CRUD completo com todas as operações necessárias

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt
from app.decorators.decorator_jwt import funcionario_required
from datetime import datetime
from decimal import Decimal
import re
from app.models import (
    db,
    Fornecedor,
    Estabelecimento,
    PedidoCompra,
    Produto,
    ContaPagar,
)
from app.utils import validar_cnpj, validar_email, formatar_telefone

fornecedores_bp = Blueprint("fornecedores", __name__)

# ============================================
# VALIDAÇÕES ESPECÍFICAS DE FORNECEDOR
# ============================================


def validar_dados_fornecedor(data, fornecedor_id=None, estabelecimento_id=None):
    """Valida todos os dados do fornecedor antes de salvar"""
    erros = []

    # Validação de campos obrigatórios
    campos_obrigatorios = ["nome_fantasia", "razao_social", "cnpj", "telefone", "email"]
    for campo in campos_obrigatorios:
        if not data.get(campo):
            erros.append(f'O campo {campo.replace("_", " ").title()} é obrigatório')

    # Validação de CNPJ
    if data.get("cnpj") and estabelecimento_id:
        cnpj = re.sub(r"\D", "", data["cnpj"])
        if len(cnpj) != 14:
            erros.append("CNPJ deve conter 14 dígitos")
        elif not validar_cnpj(cnpj):
            erros.append("CNPJ inválido")

        # Verifica se CNPJ já existe (exceto para o próprio fornecedor em atualização)
        fornecedor_existente = Fornecedor.query.filter_by(
            cnpj=cnpj, estabelecimento_id=estabelecimento_id
        ).first()

        if fornecedor_existente and fornecedor_existente.id != fornecedor_id:
            erros.append("CNPJ já cadastrado para outro fornecedor")

    # Validação de email
    if data.get("email") and not validar_email(data["email"]):
        erros.append("Email inválido")

    # Validação de telefone
    if data.get("telefone"):
        telefone = re.sub(r"\D", "", data["telefone"])
        if len(telefone) < 10 or len(telefone) > 11:
            erros.append("Telefone inválido")

    # Validação de prazo de entrega
    if data.get("prazo_entrega"):
        try:
            prazo = int(data["prazo_entrega"])
            if prazo < 0 or prazo > 365:
                erros.append("Prazo de entrega deve estar entre 0 e 365 dias")
        except ValueError:
            erros.append("Prazo de entrega deve ser um número inteiro")

    # Validação de endereço
    campos_endereco = ["cep", "logradouro", "numero", "bairro", "cidade", "estado"]
    for campo in campos_endereco:
        if not data.get(campo):
            erros.append(f'O campo {campo.replace("_", " ").title()} é obrigatório')

    # Validação de estado
    if data.get("estado"):
        estados_brasil = [
            "AC",
            "AL",
            "AP",
            "AM",
            "BA",
            "CE",
            "DF",
            "ES",
            "GO",
            "MA",
            "MT",
            "MS",
            "MG",
            "PA",
            "PB",
            "PR",
            "PE",
            "PI",
            "RJ",
            "RN",
            "RS",
            "RO",
            "RR",
            "SC",
            "SP",
            "SE",
            "TO",
        ]
        if data["estado"].upper() not in estados_brasil:
            erros.append("Estado inválido. Use a sigla de 2 letras (ex: SP)")

    return erros


def formatar_cnpj(cnpj):
    """Formata CNPJ para o padrão 00.000.000/0000-00"""
    cnpj = re.sub(r"\D", "", cnpj)
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj


def calcular_classificacao_fornecedor(fornecedor):
    """Calcula classificação do fornecedor baseado em métricas"""
    if fornecedor.total_compras == 0:
        return "NOVO"

    # Baseado em volume de compras e prazo médio
    valor_total = float(fornecedor.valor_total_comprado or 0)
    total_compras = fornecedor.total_compras or 0

    if valor_total > 100000:
        return "PREMIUM"
    elif valor_total > 50000:
        return "A"
    elif valor_total > 10000:
        return "B"
    else:
        return "C"


# ============================================
# ROTAS DE FORNECEDORES
# ============================================


@fornecedores_bp.route("", methods=["GET"])
@funcionario_required
def listar_fornecedores():
    """Lista todos os fornecedores com filtros e paginação"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 50, type=int)
        ativo = request.args.get("ativo", None, type=str)
        classificacao = request.args.get("classificacao", None, type=str)
        busca = request.args.get("busca", "", type=str).strip()

        # Query base
        query = Fornecedor.query.filter_by(
            estabelecimento_id=estabelecimento_id
        )

        # Filtros
        if ativo is not None:
            query = query.filter_by(ativo=ativo.lower() == "true")

        if classificacao:
            query = query.filter_by(classificacao=classificacao.upper())

        if busca:
            busca_termo = f"%{busca}%"
            query = query.filter(
                db.or_(
                    Fornecedor.nome_fantasia.ilike(busca_termo),
                    Fornecedor.razao_social.ilike(busca_termo),
                    Fornecedor.cnpj.ilike(busca_termo),
                    Fornecedor.email.ilike(busca_termo),
                    Fornecedor.contato_nome.ilike(busca_termo),
                )
            )

        # Ordenação
        query = query.order_by(
            Fornecedor.nome_fantasia.asc(), Fornecedor.data_cadastro.desc()
        )

        # Paginação
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

        fornecedores = []
        for fornecedor in paginacao.items:
            fornecedor_dict = fornecedor.to_dict()
            fornecedor_dict["classificacao"] = calcular_classificacao_fornecedor(
                fornecedor
            )
            fornecedor_dict["ultima_compra"] = (
                fornecedor.pedidos_compra.order_by(PedidoCompra.data_pedido.desc())
                .first()
                .data_pedido.isoformat()
                if fornecedor.pedidos_compra.first()
                else None
            )

            # Contar produtos ativos
            produtos_ativos = Produto.query.filter_by(
                fornecedor_id=fornecedor.id,
                ativo=True,
                estabelecimento_id=estabelecimento_id,
            ).count()
            fornecedor_dict["produtos_ativos"] = produtos_ativos

            fornecedores.append(fornecedor_dict)

        return jsonify(
            {
                "success": True,
                "fornecedores": fornecedores,
                "total": paginacao.total,
                "pagina": pagina,
                "por_pagina": por_pagina,
                "total_paginas": paginacao.pages,
            }
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao listar fornecedores: {str(e)}")
        try:
            jwt_data = get_jwt()
            estabelecimento_id = jwt_data.get("estabelecimento_id")
            pagina = request.args.get("pagina", 1, type=int)
            por_pagina = request.args.get("por_pagina", 50, type=int)
            offset = (pagina - 1) * por_pagina
            from sqlalchemy import text
            sql = text(
                "SELECT id, nome_fantasia, razao_social, cnpj, telefone, email, cidade, estado, ativo, classificacao "
                "FROM fornecedores "
                "WHERE estabelecimento_id = :estabelecimento_id "
                "ORDER BY nome_fantasia ASC "
                "LIMIT :limit OFFSET :offset"
            )
            rows = db.session.execute(sql, {"estabelecimento_id": estabelecimento_id, "limit": por_pagina, "offset": offset}).fetchall()
            fornecedores = []
            for r in rows:
                try:
                    d = {
                        "id": r["id"],
                        "nome_fantasia": r["nome_fantasia"],
                        "razao_social": r["razao_social"],
                        "cnpj": r["cnpj"],
                        "telefone": r["telefone"],
                        "email": r["email"],
                        "cidade": r.get("cidade"),
                        "estado": r.get("estado"),
                        "ativo": bool(r.get("ativo", True)),
                        "classificacao": r.get("classificacao") or "REGULAR",
                        "produtos_ativos": None,
                    }
                except Exception:
                    d = {
                        "id": r[0],
                        "nome_fantasia": r[1],
                        "razao_social": r[2],
                        "cnpj": r[3],
                        "telefone": r[4],
                        "email": r[5],
                        "cidade": r[6] if len(r) > 6 else None,
                        "estado": r[7] if len(r) > 7 else None,
                        "ativo": bool(r[8]) if len(r) > 8 else True,
                        "classificacao": r[9] if len(r) > 9 else "REGULAR",
                        "produtos_ativos": None,
                    }
                fornecedores.append(d)
            total_sql = text(
                "SELECT COUNT(*) FROM fornecedores WHERE estabelecimento_id = :estabelecimento_id"
            )
            total = db.session.execute(total_sql, {"estabelecimento_id": estabelecimento_id}).scalar() or 0
            total_paginas = (total + por_pagina - 1) // por_pagina
            return jsonify(
                {
                    "success": True,
                    "fornecedores": fornecedores,
                    "total": total,
                    "pagina": pagina,
                    "por_pagina": por_pagina,
                    "total_paginas": total_paginas,
                }
            )
        except Exception as e2:
            current_app.logger.error(f"Fallback fornecedores falhou: {str(e2)}")
            return (
                jsonify(
                    {"success": False, "message": "Erro interno ao listar fornecedores"}
                ),
                500,
            )


@fornecedores_bp.route("/<int:id>", methods=["GET"])
@funcionario_required
def obter_fornecedor(id):
    """Obtém detalhes completos de um fornecedor específico"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        
        fornecedor = Fornecedor.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        # Dados básicos
        dados_fornecedor = fornecedor.to_dict()

        # Estatísticas
        pedidos = PedidoCompra.query.filter_by(
            fornecedor_id=id, estabelecimento_id=estabelecimento_id
        ).all()

        contas_pagar = ContaPagar.query.filter_by(
            fornecedor_id=id,
            estabelecimento_id=estabelecimento_id,
            status="aberto",
        ).all()

        produtos = Produto.query.filter_by(
            fornecedor_id=id,
            estabelecimento_id=estabelecimento_id,
            ativo=True,
        ).all()

        # Métricas
        total_pedidos = len(pedidos)
        pedidos_pendentes = len([p for p in pedidos if p.status == "pendente"])
        total_contas_abertas = len(contas_pagar)
        valor_total_devido = sum(float(c.valor_atual) for c in contas_pagar)
        total_produtos = len(produtos)

        # Últimos pedidos
        ultimos_pedidos = []
        for pedido in pedidos[:10]:  # Últimos 10 pedidos
            ultimos_pedidos.append(
                {
                    "id": pedido.id,
                    "numero_pedido": pedido.numero_pedido,
                    "data_pedido": (
                        pedido.data_pedido.isoformat() if pedido.data_pedido else None
                    ),
                    "status": pedido.status,
                    "total": float(pedido.total),
                    "quantidade_itens": pedido.itens.count(),
                }
            )

        # Produtos do fornecedor
        lista_produtos = []
        for produto in produtos[:20]:  # Primeiros 20 produtos
            lista_produtos.append(
                {
                    "id": produto.id,
                    "nome": produto.nome,
                    "codigo_barras": produto.codigo_barras,
                    "quantidade": produto.quantidade,
                    "preco_custo": float(produto.preco_custo),
                    "preco_venda": float(produto.preco_venda),
                    "ativo": produto.ativo,
                }
            )

        return jsonify(
            {
                "success": True,
                "fornecedor": dados_fornecedor,
                "metricas": {
                    "total_pedidos": total_pedidos,
                    "pedidos_pendentes": pedidos_pendentes,
                    "total_contas_abertas": total_contas_abertas,
                    "valor_total_devido": valor_total_devido,
                    "total_produtos": total_produtos,
                    "classificacao": calcular_classificacao_fornecedor(fornecedor),
                },
                "ultimos_pedidos": ultimos_pedidos,
                "produtos": lista_produtos,
                "endereco_completo": fornecedor.endereco_completo(),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao obter fornecedor {id}: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao obter fornecedor"}),
            500,
        )


@fornecedores_bp.route("", methods=["POST"])
@funcionario_required
def criar_fornecedor():
    """Cria um novo fornecedor"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        username = jwt_data.get("sub")
        
        data = request.get_json()

        # Validação dos dados
        erros = validar_dados_fornecedor(data, estabelecimento_id=estabelecimento_id)
        if erros:
            return (
                jsonify(
                    {"success": False, "message": "Erros de validação", "errors": erros}
                ),
                400,
            )

        # Formatar dados
        cnpj_formatado = formatar_cnpj(data["cnpj"])
        telefone_formatado = formatar_telefone(data["telefone"])

        # Criar fornecedor
        fornecedor = Fornecedor(
            estabelecimento_id=estabelecimento_id,
            nome_fantasia=data["nome_fantasia"].strip(),
            razao_social=data["razao_social"].strip(),
            cnpj=cnpj_formatado,
            inscricao_estadual=data.get("inscricao_estadual", "").strip(),
            telefone=telefone_formatado,
            email=data["email"].strip().lower(),
            contato_nome=data.get("contato_nome", "").strip(),
            contato_telefone=formatar_telefone(data.get("contato_telefone", "")),
            prazo_entrega=int(data.get("prazo_entrega", 7)),
            forma_pagamento=data.get("forma_pagamento", "30 DIAS"),
            classificacao=data.get("classificacao", "REGULAR"),
            # Endereço
            cep=data["cep"].strip(),
            logradouro=data["logradouro"].strip(),
            numero=data["numero"].strip(),
            complemento=data.get("complemento", "").strip(),
            bairro=data["bairro"].strip(),
            cidade=data["cidade"].strip(),
            estado=data["estado"].strip().upper(),
            pais=data.get("pais", "Brasil").strip(),
            ativo=data.get("ativo", True),
            total_compras=0,
            valor_total_comprado=0,
        )

        db.session.add(fornecedor)
        db.session.commit()

        # Log de auditoria
        current_app.logger.info(
            f"Fornecedor criado: {fornecedor.id} - {fornecedor.nome_fantasia} por {username}"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Fornecedor criado com sucesso",
                    "fornecedor": fornecedor.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar fornecedor: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao criar fornecedor"}),
            500,
        )


@fornecedores_bp.route("/<int:id>", methods=["PUT"])
@funcionario_required
def atualizar_fornecedor(id):
    """Atualiza um fornecedor existente"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        username = jwt_data.get("sub")
        
        fornecedor = Fornecedor.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        data = request.get_json()

        # Validação dos dados (passando ID para verificação de CNPJ único)
        erros = validar_dados_fornecedor(data, fornecedor.id, estabelecimento_id)
        if erros:
            return (
                jsonify(
                    {"success": False, "message": "Erros de validação", "errors": erros}
                ),
                400,
            )

        # Formatar dados
        if "cnpj" in data:
            fornecedor.cnpj = formatar_cnpj(data["cnpj"])

        if "telefone" in data:
            fornecedor.telefone = formatar_telefone(data["telefone"])

        if "contato_telefone" in data:
            fornecedor.contato_telefone = formatar_telefone(data["contato_telefone"])

        # Atualizar campos básicos
        campos_basicos = [
            "nome_fantasia",
            "razao_social",
            "inscricao_estadual",
            "email",
            "contato_nome",
            "prazo_entrega",
            "forma_pagamento",
            "classificacao",
            "ativo",
        ]

        for campo in campos_basicos:
            if campo in data:
                setattr(fornecedor, campo, data[campo])

        # Atualizar endereço
        campos_endereco = [
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "estado",
            "pais",
        ]

        for campo in campos_endereco:
            if campo in data:
                setattr(fornecedor, campo, data[campo])

        fornecedor.data_atualizacao = datetime.utcnow()

        db.session.commit()

        # Log de auditoria
        current_app.logger.info(
            f"Fornecedor atualizado: {fornecedor.id} por {username}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Fornecedor atualizado com sucesso",
                "fornecedor": fornecedor.to_dict(),
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar fornecedor {id}: {str(e)}")
        return (
            jsonify(
                {"success": False, "message": "Erro interno ao atualizar fornecedor"}
            ),
            500,
        )


@fornecedores_bp.route("/<int:id>/status", methods=["PATCH"])
@funcionario_required
def atualizar_status_fornecedor(id):
    """Ativa/desativa um fornecedor"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        username = jwt_data.get("sub")
        
        fornecedor = Fornecedor.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        data = request.get_json()
        novo_status = data.get("ativo")

        if novo_status is None:
            return (
                jsonify({"success": False, "message": 'Campo "ativo" é obrigatório'}),
                400,
            )

        # Verificar se há produtos ativos vinculados
        if not novo_status:  # Se estiver desativando
            produtos_ativos = Produto.query.filter_by(
                fornecedor_id=id,
                ativo=True,
                estabelecimento_id=estabelecimento_id,
            ).count()

            if produtos_ativos > 0:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Não é possível desativar o fornecedor. Existem {produtos_ativos} produtos ativos vinculados.",
                        }
                    ),
                    400,
                )

        fornecedor.ativo = novo_status
        fornecedor.data_atualizacao = datetime.utcnow()

        db.session.commit()

        acao = "ativado" if novo_status else "desativado"
        current_app.logger.info(
            f"Fornecedor {acao}: {fornecedor.id} por {username}"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Fornecedor {acao} com sucesso",
                "ativo": fornecedor.ativo,
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao atualizar status do fornecedor {id}: {str(e)}"
        )
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Erro interno ao atualizar status do fornecedor",
                }
            ),
            500,
        )


@fornecedores_bp.route("/<int:id>", methods=["DELETE"])
@funcionario_required
def excluir_fornecedor(id):
    """Exclui um fornecedor (apenas se não houver vínculos)"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        username = jwt_data.get("sub")
        
        fornecedor = Fornecedor.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        # Verificar vínculos
        # 1. Produtos vinculados
        produtos_count = Produto.query.filter_by(
            fornecedor_id=id, estabelecimento_id=estabelecimento_id
        ).count()

        # 2. Pedidos de compra
        pedidos_count = PedidoCompra.query.filter_by(
            fornecedor_id=id, estabelecimento_id=estabelecimento_id
        ).count()

        # 3. Contas a pagar
        contas_count = ContaPagar.query.filter_by(
            fornecedor_id=id, estabelecimento_id=estabelecimento_id
        ).count()

        if produtos_count > 0 or pedidos_count > 0 or contas_count > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Não é possível excluir o fornecedor. Existem vínculos ativos.",
                        "vinculos": {
                            "produtos": produtos_count,
                            "pedidos": pedidos_count,
                            "contas": contas_count,
                        },
                    }
                ),
                400,
            )

        # Excluir fornecedor
        db.session.delete(fornecedor)
        db.session.commit()

        current_app.logger.info(
            f"Fornecedor excluído: {id} por {username}"
        )

        return jsonify({"success": True, "message": "Fornecedor excluído com sucesso"})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao excluir fornecedor {id}: {str(e)}")
        return (
            jsonify(
                {"success": False, "message": "Erro interno ao excluir fornecedor"}
            ),
            500,
        )


@fornecedores_bp.route("/busca", methods=["GET"])
@funcionario_required
def buscar_fornecedores():
    """Busca rápida de fornecedores para autocomplete"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        
        termo = request.args.get("q", "", type=str).strip()
        limite = request.args.get("limite", 20, type=int)
        apenas_ativos = request.args.get("ativo", "true", type=str).lower() == "true"

        if not termo or len(termo) < 2:
            return jsonify({"success": True, "fornecedores": []})

        query = Fornecedor.query.filter_by(
            estabelecimento_id=estabelecimento_id
        )

        if apenas_ativos:
            query = query.filter_by(ativo=True)

        busca_termo = f"%{termo}%"
        fornecedores = (
            query.filter(
                db.or_(
                    Fornecedor.nome_fantasia.ilike(busca_termo),
                    Fornecedor.razao_social.ilike(busca_termo),
                    Fornecedor.cnpj.ilike(busca_termo),
                    Fornecedor.contato_nome.ilike(busca_termo),
                )
            )
            .limit(limite)
            .all()
        )

        resultados = []
        for fornecedor in fornecedores:
            resultados.append(
                {
                    "id": fornecedor.id,
                    "nome_fantasia": fornecedor.nome_fantasia,
                    "razao_social": fornecedor.razao_social,
                    "cnpj": fornecedor.cnpj,
                    "telefone": fornecedor.telefone,
                    "email": fornecedor.email,
                    "ativo": fornecedor.ativo,
                    "classificacao": calcular_classificacao_fornecedor(fornecedor),
                }
            )

        return jsonify(
            {"success": True, "fornecedores": resultados, "total": len(resultados)}
        )

    except Exception as e:
        current_app.logger.error(f"Erro na busca de fornecedores: {str(e)}")
        return (
            jsonify(
                {"success": False, "message": "Erro interno na busca de fornecedores"}
            ),
            500,
        )


@fornecedores_bp.route("/estatisticas", methods=["GET"])
@funcionario_required
def estatisticas_fornecedores():
    """Retorna estatísticas gerais sobre fornecedores"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")

        # Total de fornecedores
        total_fornecedores = Fornecedor.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).count()

        # Fornecedores ativos
        fornecedores_ativos = Fornecedor.query.filter_by(
            estabelecimento_id=estabelecimento_id, ativo=True
        ).count()

        # Fornecedores inativos
        fornecedores_inativos = total_fornecedores - fornecedores_ativos

        # Classificação por tipo
        classificacoes = (
            db.session.query(
                Fornecedor.classificacao, db.func.count(Fornecedor.id).label("total")
            )
            .filter_by(estabelecimento_id=estabelecimento_id)
            .group_by(Fornecedor.classificacao)
            .all()
        )

        # Fornecedores por estado
        fornecedores_por_estado = (
            db.session.query(
                Fornecedor.estado, db.func.count(Fornecedor.id).label("total")
            )
            .filter_by(estabelecimento_id=estabelecimento_id)
            .group_by(Fornecedor.estado)
            .all()
        )

        # Top 5 fornecedores por volume de compras
        top_fornecedores = (
            Fornecedor.query.filter_by(estabelecimento_id=estabelecimento_id)
            .order_by(Fornecedor.valor_total_comprado.desc())
            .limit(5)
            .all()
        )

        top_fornecedores_list = []
        for f in top_fornecedores:
            top_fornecedores_list.append(
                {
                    "id": f.id,
                    "nome": f.nome_fantasia,
                    "valor_total": float(f.valor_total_comprado or 0),
                    "total_compras": f.total_compras or 0,
                }
            )

        # Últimos fornecedores cadastrados
        ultimos_cadastrados = (
            Fornecedor.query.filter_by(estabelecimento_id=estabelecimento_id)
            .order_by(Fornecedor.data_cadastro.desc())
            .limit(5)
            .all()
        )

        ultimos_cadastrados_list = []
        for f in ultimos_cadastrados:
            ultimos_cadastrados_list.append(
                {
                    "id": f.id,
                    "nome": f.nome_fantasia,
                    "data_cadastro": (
                        f.data_cadastro.isoformat() if f.data_cadastro else None
                    ),
                    "classificacao": calcular_classificacao_fornecedor(f),
                }
            )

        return jsonify(
            {
                "success": True,
                "estatisticas": {
                    "total": total_fornecedores,
                    "ativos": fornecedores_ativos,
                    "inativos": fornecedores_inativos,
                    "percentual_ativos": (
                        (fornecedores_ativos / total_fornecedores * 100)
                        if total_fornecedores > 0
                        else 0
                    ),
                    "classificacoes": {c[0]: c[1] for c in classificacoes},
                    "por_estado": {e[0]: e[1] for e in fornecedores_por_estado},
                },
                "top_fornecedores": top_fornecedores_list,
                "ultimos_cadastrados": ultimos_cadastrados_list,
            }
        )

    except Exception as e:
        current_app.logger.error(
            f"Erro ao obter estatísticas de fornecedores: {str(e)}"
        )
        return (
            jsonify(
                {"success": False, "message": "Erro interno ao obter estatísticas"}
            ),
            500,
        )


@fornecedores_bp.route("/<int:id>/pedidos", methods=["GET"])
@funcionario_required
def listar_pedidos_fornecedor(id):
    """Lista todos os pedidos de um fornecedor"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = request.args.get("por_pagina", 20, type=int)
        status = request.args.get("status", None, type=str)

        # Verificar se fornecedor existe
        fornecedor = Fornecedor.query.filter_by(
            id=id, estabelecimento_id=estabelecimento_id
        ).first_or_404()

        # Query de pedidos
        query = PedidoCompra.query.filter_by(
            fornecedor_id=id, estabelecimento_id=estabelecimento_id
        )

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(PedidoCompra.data_pedido.desc())

        # Paginação
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

        pedidos = []
        for pedido in paginacao.items:
            pedidos.append(
                {
                    "id": pedido.id,
                    "numero_pedido": pedido.numero_pedido,
                    "data_pedido": (
                        pedido.data_pedido.isoformat() if pedido.data_pedido else None
                    ),
                    "data_previsao_entrega": (
                        pedido.data_previsao_entrega.isoformat()
                        if pedido.data_previsao_entrega
                        else None
                    ),
                    "status": pedido.status,
                    "total": float(pedido.total),
                    "quantidade_itens": pedido.itens.count(),
                    "funcionario": (
                        pedido.funcionario.nome if pedido.funcionario else None
                    ),
                }
            )

        return jsonify(
            {
                "success": True,
                "pedidos": pedidos,
                "fornecedor": fornecedor.nome_fantasia,
                "total": paginacao.total,
                "pagina": pagina,
                "total_paginas": paginacao.pages,
            }
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao listar pedidos do fornecedor {id}: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao listar pedidos"}),
            500,
        )


@fornecedores_bp.route("/exportar", methods=["GET"])
@funcionario_required
def exportar_fornecedores():
    """Exporta fornecedores em formato CSV ou Excel"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        
        formato = request.args.get("formato", "csv", type=str).lower()
        apenas_ativos = request.args.get("ativo", "true", type=str).lower() == "true"

        # Buscar fornecedores
        query = Fornecedor.query.filter_by(
            estabelecimento_id=estabelecimento_id
        )

        if apenas_ativos:
            query = query.filter_by(ativo=True)

        fornecedores = query.order_by(Fornecedor.nome_fantasia.asc()).all()

        if formato == "csv":
            # Gerar CSV
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output, delimiter=";")

            # Cabeçalho
            writer.writerow(
                [
                    "ID",
                    "Nome Fantasia",
                    "Razão Social",
                    "CNPJ",
                    "Inscrição Estadual",
                    "Telefone",
                    "Email",
                    "Contato",
                    "Telefone Contato",
                    "Prazo Entrega",
                    "Forma Pagamento",
                    "Classificação",
                    "CEP",
                    "Logradouro",
                    "Número",
                    "Complemento",
                    "Bairro",
                    "Cidade",
                    "Estado",
                    "País",
                    "Ativo",
                    "Total Compras",
                    "Valor Total Comprado",
                    "Data Cadastro",
                ]
            )

            # Dados
            for f in fornecedores:
                writer.writerow(
                    [
                        f.id,
                        f.nome_fantasia or "",
                        f.razao_social or "",
                        f.cnpj or "",
                        f.inscricao_estadual or "",
                        f.telefone or "",
                        f.email or "",
                        f.contato_nome or "",
                        f.contato_telefone or "",
                        f.prazo_entrega or "",
                        f.forma_pagamento or "",
                        f.classificacao or "",
                        f.cep or "",
                        f.logradouro or "",
                        f.numero or "",
                        f.complemento or "",
                        f.bairro or "",
                        f.cidade or "",
                        f.estado or "",
                        f.pais or "",
                        "SIM" if f.ativo else "NÃO",
                        f.total_compras or 0,
                        float(f.valor_total_comprado or 0),
                        (
                            f.data_cadastro.strftime("%d/%m/%Y %H:%M:%S")
                            if f.data_cadastro
                            else ""
                        ),
                    ]
                )

            output.seek(0)
            return (
                output.getvalue(),
                200,
                {
                    "Content-Type": "text/csv; charset=utf-8",
                    "Content-Disposition": "attachment; filename=fornecedores.csv",
                },
            )

        elif formato == "excel":
            # Gerar Excel
            import pandas as pd

            dados = []
            for f in fornecedores:
                dados.append(
                    {
                        "ID": f.id,
                        "Nome Fantasia": f.nome_fantasia or "",
                        "Razão Social": f.razao_social or "",
                        "CNPJ": f.cnpj or "",
                        "Inscrição Estadual": f.inscricao_estadual or "",
                        "Telefone": f.telefone or "",
                        "Email": f.email or "",
                        "Contato": f.contato_nome or "",
                        "Telefone Contato": f.contato_telefone or "",
                        "Prazo Entrega": f.prazo_entrega or "",
                        "Forma Pagamento": f.forma_pagamento or "",
                        "Classificação": f.classificacao or "",
                        "CEP": f.cep or "",
                        "Logradouro": f.logradouro or "",
                        "Número": f.numero or "",
                        "Complemento": f.complemento or "",
                        "Bairro": f.bairro or "",
                        "Cidade": f.cidade or "",
                        "Estado": f.estado or "",
                        "País": f.pais or "",
                        "Ativo": "SIM" if f.ativo else "NÃO",
                        "Total Compras": f.total_compras or 0,
                        "Valor Total Comprado": float(f.valor_total_comprado or 0),
                        "Data Cadastro": (
                            f.data_cadastro.strftime("%d/%m/%Y %H:%M:%S")
                            if f.data_cadastro
                            else ""
                        ),
                    }
                )

            df = pd.DataFrame(dados)

            # Salvar em buffer
            from io import BytesIO

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Fornecedores", index=False)

            output.seek(0)
            return (
                output.getvalue(),
                200,
                {
                    "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "Content-Disposition": "attachment; filename=fornecedores.xlsx",
                },
            )

        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": 'Formato não suportado. Use "csv" ou "excel"',
                    }
                ),
                400,
            )

    except Exception as e:
        current_app.logger.error(f"Erro ao exportar fornecedores: {str(e)}")
        return (
            jsonify(
                {"success": False, "message": "Erro interno ao exportar fornecedores"}
            ),
            500,
        )


@fornecedores_bp.route("/importar", methods=["POST"])
@funcionario_required
def importar_fornecedores():
    """Importa fornecedores a partir de arquivo CSV"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        
        if "file" not in request.files:
            return jsonify({"success": False, "message": "Nenhum arquivo enviado"}), 400

        arquivo = request.files["file"]

        if arquivo.filename == "":
            return (
                jsonify({"success": False, "message": "Nenhum arquivo selecionado"}),
                400,
            )

        if not arquivo.filename.endswith(".csv"):
            return (
                jsonify(
                    {"success": False, "message": "Apenas arquivos CSV são suportados"}
                ),
                400,
            )

        import csv
        import io

        # Ler arquivo CSV
        stream = io.StringIO(arquivo.read().decode("utf-8-sig"))
        leitor = csv.DictReader(stream, delimiter=";")

        # Verificar cabeçalho mínimo
        cabecalhos_necessarios = [
            "nome_fantasia",
            "razao_social",
            "cnpj",
            "email",
            "telefone",
        ]
        cabecalhos_arquivo = leitor.fieldnames or []

        for cabecalho in cabecalhos_necessarios:
            if cabecalho not in cabecalhos_arquivo:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Cabeçalho obrigatório não encontrado: {cabecalho}",
                        }
                    ),
                    400,
                )

        # Processar linhas
        fornecedores_criados = 0
        fornecedores_atualizados = 0
        erros = []

        for linha_num, linha in enumerate(
            leitor, start=2
        ):  # start=2 para incluir cabeçalho
            try:
                # Verificar se fornecedor já existe pelo CNPJ
                cnpj_formatado = formatar_cnpj(linha["cnpj"])
                fornecedor_existente = Fornecedor.query.filter_by(
                    cnpj=cnpj_formatado,
                    estabelecimento_id=estabelecimento_id,
                ).first()

                if fornecedor_existente:
                    # Atualizar fornecedor existente
                    fornecedor_existente.nome_fantasia = linha["nome_fantasia"].strip()
                    fornecedor_existente.razao_social = linha["razao_social"].strip()
                    fornecedor_existente.email = linha["email"].strip().lower()
                    fornecedor_existente.telefone = formatar_telefone(linha["telefone"])
                    fornecedor_existente.data_atualizacao = datetime.utcnow()
                    fornecedores_atualizados += 1
                else:
                    # Criar novo fornecedor
                    fornecedor = Fornecedor(
                        estabelecimento_id=estabelecimento_id,
                        nome_fantasia=linha["nome_fantasia"].strip(),
                        razao_social=linha["razao_social"].strip(),
                        cnpj=cnpj_formatado,
                        email=linha["email"].strip().lower(),
                        telefone=formatar_telefone(linha["telefone"]),
                        # Campos opcionais
                        inscricao_estadual=linha.get("inscricao_estadual", "").strip(),
                        contato_nome=linha.get("contato_nome", "").strip(),
                        contato_telefone=formatar_telefone(
                            linha.get("contato_telefone", "")
                        ),
                        prazo_entrega=int(linha.get("prazo_entrega", 7)),
                        forma_pagamento=linha.get("forma_pagamento", "30 DIAS"),
                        classificacao=linha.get("classificacao", "REGULAR"),
                        # Endereço
                        cep=linha.get("cep", "").strip(),
                        logradouro=linha.get("logradouro", "").strip(),
                        numero=linha.get("numero", "").strip(),
                        complemento=linha.get("complemento", "").strip(),
                        bairro=linha.get("bairro", "").strip(),
                        cidade=linha.get("cidade", "").strip(),
                        estado=linha.get("estado", "").strip().upper(),
                        pais=linha.get("pais", "Brasil").strip(),
                        ativo=linha.get("ativo", "true").lower() == "true",
                        total_compras=0,
                        valor_total_comprado=0,
                    )
                    db.session.add(fornecedor)
                    fornecedores_criados += 1

            except Exception as e:
                erros.append(f"Linha {linha_num}: {str(e)}")

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Importação concluída",
                "resultado": {
                    "criados": fornecedores_criados,
                    "atualizados": fornecedores_atualizados,
                    "erros": erros,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao importar fornecedores: {str(e)}")
        return (
            jsonify(
                {"success": False, "message": "Erro interno ao importar fornecedores"}
            ),
            500,
        )


@fornecedores_bp.route("/relatorio/analitico", methods=["GET"])
@funcionario_required
def relatorio_analitico_fornecedores():
    """Gera relatório analítico detalhado dos fornecedores"""
    try:
        # Get estabelecimento_id from JWT
        jwt_data = get_jwt()
        estabelecimento_id = jwt_data.get("estabelecimento_id")
        
        # Parâmetros de filtro
        data_inicio = request.args.get("data_inicio", None)
        data_fim = request.args.get("data_fim", None)
        classificacao = request.args.get("classificacao", None, type=str)

        # Query base de fornecedores
        query = Fornecedor.query.filter_by(
            estabelecimento_id=estabelecimento_id, ativo=True
        )

        if classificacao:
            query = query.filter_by(classificacao=classificacao.upper())

        fornecedores = query.all()

        relatorio = []
        for fornecedor in fornecedores:
            # Pedidos do fornecedor no período
            pedidos_query = PedidoCompra.query.filter_by(
                fornecedor_id=fornecedor.id,
                estabelecimento_id=estabelecimento_id,
            )

            if data_inicio:
                try:
                    data_inicio_dt = datetime.fromisoformat(data_inicio.replace('Z', '+00:00'))
                    pedidos_query = pedidos_query.filter(PedidoCompra.data_pedido >= data_inicio_dt)
                except ValueError:
                    # Fallback para parsing simples
                    data_inicio_dt = datetime.strptime(data_inicio.split('T')[0], "%Y-%m-%d")
                    pedidos_query = pedidos_query.filter(PedidoCompra.data_pedido >= data_inicio_dt)

            if data_fim:
                try:
                    data_fim_dt = datetime.fromisoformat(data_fim.replace('Z', '+00:00'))
                    # Se for apenas data (00:00:00), ajustar para 23:59:59
                    if data_fim_dt.hour == 0 and data_fim_dt.minute == 0:
                        data_fim_dt = data_fim_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                    pedidos_query = pedidos_query.filter(PedidoCompra.data_pedido <= data_fim_dt)
                except ValueError:
                    # Fallback para parsing simples
                    data_fim_dt = datetime.strptime(data_fim.split('T')[0], "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
                    pedidos_query = pedidos_query.filter(PedidoCompra.data_pedido <= data_fim_dt)

            pedidos = pedidos_query.all()

            # Cálculos
            total_pedidos = len(pedidos)
            valor_total = sum(float(p.total) for p in pedidos)
            pedidos_pendentes = len([p for p in pedidos if p.status == "pendente"])
            pedidos_concluidos = len([p for p in pedidos if p.status == "concluido"])

            # Média de tempo de entrega (apenas pedidos concluídos)
            tempos_entrega = []
            atrasos = []
            entregas_no_prazo = 0
            total_entregas_avaliadas = 0

            for p in pedidos:
                # Considerar entregas concluídas
                if p.status == "concluido":
                    # Garantir que temos objetos date (não datetime)
                    data_pedido_date = p.data_pedido.date() if isinstance(p.data_pedido, datetime) else p.data_pedido
                    
                    # Data Efetiva (Recebimento)
                    if p.data_recebimento:
                        data_efetiva = p.data_recebimento.date() if isinstance(p.data_recebimento, datetime) else p.data_recebimento
                    else:
                        data_efetiva = data_pedido_date # Fallback

                    if data_pedido_date:
                        dias_reais = (data_efetiva - data_pedido_date).days
                        tempos_entrega.append(dias_reais)
                        
                        # Cálculo de OTD (On-Time Delivery)
                        prazo_prometido_date = None
                        if p.data_previsao_entrega:
                            prazo_prometido_date = p.data_previsao_entrega.date() if isinstance(p.data_previsao_entrega, datetime) else p.data_previsao_entrega
                        else:
                            # Fallback: data_pedido + prazo_padrao
                            from datetime import timedelta
                            prazo_padrao = fornecedor.prazo_entrega or 7
                            prazo_prometido_date = data_pedido_date + timedelta(days=prazo_padrao)
                        
                        if prazo_prometido_date:
                            total_entregas_avaliadas += 1
                            if data_efetiva <= prazo_prometido_date:
                                entregas_no_prazo += 1
                            else:
                                dias_atraso = (data_efetiva - prazo_prometido_date).days
                                atrasos.append(dias_atraso)

            media_entrega = (
                sum(tempos_entrega) / len(tempos_entrega) if tempos_entrega else 0
            )
            
            # Se não há entregas avaliadas, assumir 100% (Inocente até que se prove o contrário) ou Neutro
            # Se o fornecedor tem pedidos mas nenhum concluído, talvez Score deva ser neutro (100)
            if total_entregas_avaliadas > 0:
                taxa_otd = (entregas_no_prazo / total_entregas_avaliadas * 100)
            else:
                taxa_otd = 100.0 # Sem histórico negativo

            media_atraso = (sum(atrasos) / len(atrasos)) if atrasos else 0

            # Produtos fornecidos e Variação de Preço (Simplificada)
            produtos = Produto.query.filter_by(
                fornecedor_id=fornecedor.id,
                estabelecimento_id=estabelecimento_id,
                ativo=True,
            ).all()

            total_produtos = len(produtos)
            
            # Cálculo de Score (0-100)
            score = taxa_otd * 0.6 + (100 if media_atraso <= 0 else max(0, 100 - media_atraso * 10)) * 0.4
            
            if not pedidos:
                score = 100.0

            # Adicionar ao relatório
            relatorio.append(
                {
                    "fornecedor": {
                        "id": fornecedor.id,
                        "nome": fornecedor.nome_fantasia,
                        "cnpj": fornecedor.cnpj,
                        "classificacao": fornecedor.classificacao,
                        "prazo_entrega_padrao": fornecedor.prazo_entrega,
                        "score": round(score, 1)
                    },
                    "metricas": {
                        "total_pedidos": total_pedidos,
                        "valor_total_comprado": valor_total,
                        "pedidos_pendentes": pedidos_pendentes,
                        "pedidos_concluidos": pedidos_concluidos,
                        "taxa_conclusao": (
                            (pedidos_concluidos / total_pedidos * 100)
                            if total_pedidos > 0
                            else 0
                        ),
                        "media_tempo_entrega": media_entrega,
                        "taxa_otd": taxa_otd,
                        "media_atraso": media_atraso,
                        "total_produtos": total_produtos,
                    },
                    "produtos": [
                        {
                            "id": p.id,
                            "nome": p.nome,
                            "preco_custo": float(p.preco_custo),
                            "preco_venda": float(p.preco_venda),
                            "margem": float(p.margem_lucro) if p.margem_lucro else 0,
                            "quantidade_estoque": p.quantidade,
                        }
                        for p in produtos[:10]
                    ],  # Limitar a 10 produtos
                }
            )

        return jsonify(
            {
                "success": True,
                "relatorio": relatorio,
                "total_fornecedores": len(relatorio),
                "filtros": {
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "classificacao": classificacao,
                },
            }
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório analítico: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro interno ao gerar relatório"}),
            500,
        )


# ============================================
# UTILITÁRIOS DE FORNECEDOR
# ============================================


def sincronizar_metricas_fornecedor(fornecedor_id):
    """Sincroniza métricas de um fornecedor (chamar após cada pedido)"""
    try:
        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return

        # Calcular total de compras
        pedidos = PedidoCompra.query.filter_by(
            fornecedor_id=fornecedor_id,
            estabelecimento_id=fornecedor.estabelecimento_id,
            status="concluido",
        ).all()

        total_compras = len(pedidos)
        valor_total = sum(float(p.total) for p in pedidos)

        # Atualizar fornecedor
        fornecedor.total_compras = total_compras
        fornecedor.valor_total_comprado = valor_total

        # Atualizar classificação
        if valor_total > 100000:
            fornecedor.classificacao = "PREMIUM"
        elif valor_total > 50000:
            fornecedor.classificacao = "A"
        elif valor_total > 10000:
            fornecedor.classificacao = "B"
        else:
            fornecedor.classificacao = "C"

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao sincronizar métricas do fornecedor {fornecedor_id}: {str(e)}"
        )
