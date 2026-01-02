from flask import Blueprint, request, jsonify
from app import db
from app.models import Fornecedor, Produto
from datetime import datetime
from sqlalchemy import or_, and_, distinct

fornecedores_bp = Blueprint("fornecedores", __name__, url_prefix="/api/fornecedores")

# ==================== CONSTANTES E FUNÇÕES AUXILIARES ====================

FILTROS_PERMITIDOS_FORNECEDOR = {
    "nome": lambda value: Fornecedor.nome.ilike(f"%{value}%"),
    "cnpj": lambda value: Fornecedor.cnpj.ilike(f"%{value}%"),
    "contato_nome": lambda value: Fornecedor.contato_nome.ilike(f"%{value}%"),
    "telefone": lambda value: Fornecedor.telefone.ilike(f"%{value}%"),
    "email": lambda value: Fornecedor.email.ilike(f"%{value}%"),
    "cidade": lambda value: Fornecedor.cidade.ilike(f"%{value}%"),
    "estado": lambda value: Fornecedor.estado.ilike(f"%{value}%"),
    "ativo": lambda value: Fornecedor.ativo == (value.lower() == "true"),
}

ORDENACOES_PERMITIDAS = {
    "nome": Fornecedor.nome,
    "cnpj": Fornecedor.cnpj,
    "cidade": Fornecedor.cidade,
    "estado": Fornecedor.estado,
    "data_cadastro": Fornecedor.data_cadastro,
    "data_atualizacao": Fornecedor.data_atualizacao,
    "contato_nome": Fornecedor.contato_nome,
}


def aplicar_filtros_avancados(query, filtros):
    """Aplica filtros avançados na query"""
    for filtro, valor in filtros.items():
        if filtro in FILTROS_PERMITIDOS_FORNECEDOR and valor not in [None, ""]:
            # Filtros especiais (range de datas)
            if filtro.startswith("data_"):
                if filtro.endswith("_inicio"):
                    campo = filtro.replace("_inicio", "")
                    if hasattr(Fornecedor, campo):
                        try:
                            data_dt = datetime.fromisoformat(valor)
                            query = query.filter(getattr(Fornecedor, campo) >= data_dt)
                        except ValueError:
                            pass
                elif filtro.endswith("_fim"):
                    campo = filtro.replace("_fim", "")
                    if hasattr(Fornecedor, campo):
                        try:
                            data_dt = datetime.fromisoformat(valor)
                            query = query.filter(getattr(Fornecedor, campo) <= data_dt)
                        except ValueError:
                            pass
            # Filtro de produto associado
            elif filtro == "tem_produtos":
                if valor.lower() == "true":
                    # Fornecedores que têm pelo menos 1 produto ativo
                    subquery = (
                        db.session.query(Produto.fornecedor_id)
                        .filter(Produto.ativo == True)
                        .distinct()
                    )
                    query = query.filter(Fornecedor.id.in_(subquery))
                elif valor.lower() == "false":
                    # Fornecedores sem produtos ativos
                    subquery = (
                        db.session.query(Produto.fornecedor_id)
                        .filter(Produto.ativo == True)
                        .distinct()
                    )
                    query = query.filter(~Fornecedor.id.in_(subquery))
            # Filtro por quantidade mínima de produtos
            elif filtro == "min_produtos":
                try:
                    min_prod = int(valor)
                    subquery = (
                        db.session.query(
                            Produto.fornecedor_id,
                            db.func.count(Produto.id).label("total"),
                        )
                        .filter(Produto.ativo == True)
                        .group_by(Produto.fornecedor_id)
                        .having(db.func.count(Produto.id) >= min_prod)
                        .subquery()
                    )
                    query = query.filter(
                        Fornecedor.id.in_(db.session.query(subquery.c.fornecedor_id))
                    )
                except ValueError:
                    pass
            # Filtros regulares
            else:
                query = query.filter(FILTROS_PERMITIDOS_FORNECEDOR[filtro](valor))

    return query


def aplicar_ordenacao(query, ordenar_por, direcao):
    """Aplica ordenação na query"""
    if ordenar_por in ORDENACOES_PERMITIDAS:
        campo = ORDENACOES_PERMITIDAS[ordenar_por]
        if direcao.lower() == "desc":
            query = query.order_by(campo.desc())
        else:
            query = query.order_by(campo.asc())
    else:
        # Ordenação padrão
        query = query.order_by(Fornecedor.nome.asc())

    return query


# ==================== CRUD FORNECEDORES COM FILTROS AVANÇADOS ====================


@fornecedores_bp.route("/", methods=["GET"])
def listar_fornecedores():
    """Listar todos os fornecedores com filtros avançados"""
    try:
        # Configuração de paginação
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        per_page = min(per_page, 100)  # Limite máximo por página

        # Configuração de ordenação
        ordenar_por = request.args.get("ordenar_por", "nome")
        direcao = request.args.get("direcao", "asc")

        # Iniciar query
        query = Fornecedor.query

        # Aplicar filtro de busca global (mantido para compatibilidade)
        search = request.args.get("search", "").strip()
        if search:
            query = query.filter(
                or_(
                    Fornecedor.nome.ilike(f"%{search}%"),
                    Fornecedor.cnpj.ilike(f"%{search}%"),
                    Fornecedor.contato_nome.ilike(f"%{search}%"),
                    Fornecedor.email.ilike(f"%{search}%"),
                    Fornecedor.cidade.ilike(f"%{search}%"),
                    Fornecedor.estado.ilike(f"%{search}%"),
                )
            )

        # Aplicar filtros avançados
        filtros_avancados = {}
        for filtro in FILTROS_PERMITIDOS_FORNECEDOR.keys():
            valor = request.args.get(filtro, "").strip()
            if valor:
                filtros_avancados[filtro] = valor

        # Filtros especiais de data
        for filtro_data in [
            "data_cadastro_inicio",
            "data_cadastro_fim",
            "data_atualizacao_inicio",
            "data_atualizacao_fim",
        ]:
            valor = request.args.get(filtro_data, "").strip()
            if valor:
                filtros_avancados[filtro_data] = valor

        # Filtros relacionais
        for filtro_rel in ["tem_produtos", "min_produtos"]:
            valor = request.args.get(filtro_rel, "").strip()
            if valor:
                filtros_avancados[filtro_rel] = valor

        # Aplicar todos os filtros
        query = aplicar_filtros_avancados(query, filtros_avancados)

        # Aplicar ordenação
        query = aplicar_ordenacao(query, ordenar_por, direcao)

        # Executar paginação
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        fornecedores = pagination.items

        # Construir resposta
        resultado = []
        for f in fornecedores:
            # Contar produtos ativos deste fornecedor
            total_produtos = Produto.query.filter_by(
                fornecedor_id=f.id, ativo=True
            ).count()

            resultado.append(
                {
                    "id": f.id,
                    "nome": f.nome,
                    "cnpj": f.cnpj,
                    "telefone": f.telefone,
                    "email": f.email,
                    "cidade": f.cidade,
                    "estado": f.estado,
                    "contato_nome": f.contato_nome,
                    "ativo": f.ativo,
                    "total_produtos": total_produtos,
                    "data_cadastro": (
                        f.data_cadastro.isoformat() if f.data_cadastro else None
                    ),
                    "data_atualizacao": (
                        f.data_atualizacao.isoformat() if f.data_atualizacao else None
                    ),
                }
            )

        # Metadados da paginação
        metadados = {
            "pagina_atual": pagination.page,
            "total_paginas": pagination.pages,
            "total_itens": pagination.total,
            "itens_por_pagina": pagination.per_page,
            "tem_proxima": pagination.has_next,
            "tem_anterior": pagination.has_prev,
        }

        # Metadados dos filtros aplicados (útil para frontend)
        if filtros_avancados:
            metadados["filtros_aplicados"] = filtros_avancados
        if search:
            metadados["busca_global"] = search

        metadados["ordenacao"] = {"campo": ordenar_por, "direcao": direcao}

        return jsonify(
            {
                "fornecedores": resultado,
                "paginacao": metadados,
                "filtros_disponiveis": list(FILTROS_PERMITIDOS_FORNECEDOR.keys()),
                "ordenacoes_disponiveis": list(ORDENACOES_PERMITIDAS.keys()),
            }
        )

    except Exception as e:
        print(f"Erro ao listar fornecedores: {str(e)}")
        return jsonify({"error": f"Erro ao listar fornecedores: {str(e)}"}), 500


@fornecedores_bp.route("/<int:id>/produtos", methods=["GET"])
def produtos_fornecedor(id):
    """Listar produtos de um fornecedor específico com filtros e paginação"""
    try:
        # Verificar se fornecedor existe
        fornecedor = Fornecedor.query.get(id)
        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404

        # Configuração de paginação
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        per_page = min(per_page, 100)

        # Iniciar query para produtos do fornecedor
        query = Produto.query.filter_by(fornecedor_id=id, ativo=True)

        # Aplicar filtros nos produtos
        nome_produto = request.args.get("nome", "").strip()
        categoria = request.args.get("categoria", "").strip()
        marca = request.args.get("marca", "").strip()
        estoque_status = request.args.get("estoque_status", "").strip().lower()

        if nome_produto:
            query = query.filter(Produto.nome.ilike(f"%{nome_produto}%"))
        if categoria:
            query = query.filter(Produto.categoria.ilike(f"%{categoria}%"))
        if marca:
            query = query.filter(Produto.marca.ilike(f"%{marca}%"))

        # Filtro por status de estoque
        if estoque_status:
            if estoque_status == "baixo":
                query = query.filter(Produto.quantidade < Produto.quantidade_minima)
            elif estoque_status == "esgotado":
                query = query.filter(Produto.quantidade <= 0)
            elif estoque_status == "normal":
                query = query.filter(Produto.quantidade >= Produto.quantidade_minima)

        # Ordenação
        ordenar_por = request.args.get("ordenar_por", "nome")
        direcao = request.args.get("direcao", "asc")

        if hasattr(Produto, ordenar_por):
            campo = getattr(Produto, ordenar_por)
            if direcao.lower() == "desc":
                query = query.order_by(campo.desc())
            else:
                query = query.order_by(campo.asc())
        else:
            query = query.order_by(Produto.nome.asc())

        # Executar paginação
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        produtos = pagination.items

        # Construir resposta
        resultado = []
        for p in produtos:
            # Determinar status do estoque
            if p.quantidade <= 0:
                status = "esgotado"
            elif p.quantidade < p.quantidade_minima:
                status = "baixo"
            else:
                status = "normal"

            resultado.append(
                {
                    "id": p.id,
                    "nome": p.nome,
                    "preco_custo": float(p.preco_custo),
                    "preco_venda": float(p.preco_venda),
                    "quantidade": p.quantidade,
                    "quantidade_minima": p.quantidade_minima,
                    "estoque_status": status,
                    "categoria": p.categoria,
                    "marca": p.marca,
                    "codigo_barras": p.codigo_barras or "",
                    "data_cadastro": (
                        p.data_cadastro.isoformat() if p.data_cadastro else None
                    ),
                }
            )

        # Metadados
        metadados = {
            "pagina_atual": pagination.page,
            "total_paginas": pagination.pages,
            "total_itens": pagination.total,
            "itens_por_pagina": pagination.per_page,
            "tem_proxima": pagination.has_next,
            "tem_anterior": pagination.has_prev,
        }

        # Adicionar filtros aplicados
        filtros_aplicados = {}
        if nome_produto:
            filtros_aplicados["nome"] = nome_produto
        if categoria:
            filtros_aplicados["categoria"] = categoria
        if marca:
            filtros_aplicados["marca"] = marca
        if estoque_status:
            filtros_aplicados["estoque_status"] = estoque_status

        if filtros_aplicados:
            metadados["filtros_aplicados"] = filtros_aplicados

        return jsonify(
            {
                "fornecedor": {
                    "id": fornecedor.id,
                    "nome": fornecedor.nome,
                    "cnpj": fornecedor.cnpj,
                },
                "produtos": resultado,
                "paginacao": metadados,
                "total_produtos": pagination.total,
            }
        )

    except Exception as e:
        print(f"Erro ao listar produtos do fornecedor {id}: {str(e)}")
        return jsonify({"error": f"Erro ao listar produtos: {str(e)}"}), 500


# ==================== ENDPOINTS DE ESTATÍSTICAS (BÔNUS) ====================


@fornecedores_bp.route("/estatisticas", methods=["GET"])
def estatisticas_fornecedores():
    """Obter estatísticas agregadas dos fornecedores"""
    try:
        # Contagem total
        total_fornecedores = Fornecedor.query.count()
        total_ativos = Fornecedor.query.filter_by(ativo=True).count()
        total_inativos = total_fornecedores - total_ativos

        # Contagem por estado
        estados = (
            db.session.query(
                Fornecedor.estado, db.func.count(Fornecedor.id).label("quantidade")
            )
            .filter(Fornecedor.estado != "")
            .group_by(Fornecedor.estado)
            .all()
        )

        # Contagem de fornecedores com/sem produtos
        com_produtos = (
            db.session.query(db.func.count(distinct(Produto.fornecedor_id)))
            .filter(Produto.ativo == True)
            .scalar()
            or 0
        )

        sem_produtos = total_ativos - com_produtos

        return jsonify(
            {
                "total_fornecedores": total_fornecedores,
                "total_ativos": total_ativos,
                "total_inativos": total_inativos,
                "distribuicao_estados": [
                    {"estado": estado, "quantidade": qtd} for estado, qtd in estados
                ],
                "fornecedores_com_produtos": com_produtos,
                "fornecedores_sem_produtos": sem_produtos,
            }
        )

    except Exception as e:
        print(f"Erro ao obter estatísticas: {str(e)}")
        return jsonify({"error": f"Erro ao obter estatísticas: {str(e)}"}), 500


# ==================== ENDPOINTS DE RELATÓRIOS (BÔNUS) ====================


@fornecedores_bp.route("/relatorio", methods=["GET"])
def relatorio_fornecedores():
    """Gerar relatório completo de fornecedores"""
    try:
        # Filtros básicos
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"
        estado = request.args.get("estado", "").strip()

        query = Fornecedor.query

        if apenas_ativos:
            query = query.filter(Fornecedor.ativo == True)

        if estado:
            query = query.filter(Fornecedor.estado.ilike(f"%{estado}%"))

        fornecedores = query.order_by(Fornecedor.nome.asc()).all()

        resultado = []
        for f in fornecedores:
            # Buscar produtos ativos
            produtos = Produto.query.filter_by(fornecedor_id=f.id, ativo=True).all()

            # Calcular valor total em estoque
            valor_estoque = sum(p.quantidade * p.preco_custo for p in produtos)

            resultado.append(
                {
                    "id": f.id,
                    "nome": f.nome,
                    "cnpj": f.cnpj,
                    "cidade": f.cidade,
                    "estado": f.estado,
                    "contato": f.contato_nome,
                    "telefone": f.telefone,
                    "email": f.email,
                    "ativo": f.ativo,
                    "quantidade_produtos": len(produtos),
                    "valor_total_estoque": float(valor_estoque),
                    "data_cadastro": (
                        f.data_cadastro.isoformat() if f.data_cadastro else None
                    ),
                }
            )

        # Totais
        totais = {
            "total_fornecedores": len(resultado),
            "total_produtos": sum(f["quantidade_produtos"] for f in resultado),
            "valor_total_estoque": sum(f["valor_total_estoque"] for f in resultado),
        }

        return jsonify(
            {
                "fornecedores": resultado,
                "totais": totais,
                "gerado_em": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        print(f"Erro ao gerar relatório: {str(e)}")
        return jsonify({"error": f"Erro ao gerar relatório: {str(e)}"}), 500


# ==================== MANTENDO AS OUTRAS ROTAS CRUD (inalteradas) ====================


@fornecedores_bp.route("/<int:id>", methods=["GET"])
def detalhes_fornecedor(id):
    """Obter detalhes de um fornecedor (mantida igual)"""
    try:
        fornecedor = Fornecedor.query.get(id)

        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404

        # Listar produtos deste fornecedor
        produtos = Produto.query.filter_by(fornecedor_id=id, ativo=True).all()
        produtos_list = []

        for p in produtos:
            produtos_list.append(
                {
                    "id": p.id,
                    "nome": p.nome,
                    "preco_custo": float(p.preco_custo),
                    "preco_venda": float(p.preco_venda),
                    "quantidade": p.quantidade,
                }
            )

        fornecedor_dict = {
            "id": fornecedor.id,
            "nome": fornecedor.nome,
            "cnpj": fornecedor.cnpj,
            "telefone": fornecedor.telefone,
            "email": fornecedor.email,
            "cidade": fornecedor.cidade,
            "estado": fornecedor.estado,
            "contato_nome": fornecedor.contato_nome,
            "ativo": fornecedor.ativo,
            "data_cadastro": (
                fornecedor.data_cadastro.isoformat()
                if fornecedor.data_cadastro
                else None
            ),
            "data_atualizacao": (
                fornecedor.data_atualizacao.isoformat()
                if fornecedor.data_atualizacao
                else None
            ),
            "produtos": produtos_list,
            "total_produtos": len(produtos_list),
        }

        return jsonify(fornecedor_dict)

    except Exception as e:
        print(f"Erro ao obter fornecedor {id}: {str(e)}")
        return jsonify({"error": f"Erro ao obter fornecedor: {str(e)}"}), 404


@fornecedores_bp.route("/", methods=["POST"])
def criar_fornecedor():
    """Criar um novo fornecedor (mantida igual)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Validações
        if not data.get("nome"):
            return jsonify({"error": "Nome do fornecedor é obrigatório"}), 400

        # Verificar CNPJ único
        cnpj = data.get("cnpj")
        if cnpj:
            existente = Fornecedor.query.filter_by(cnpj=cnpj).first()
            if existente:
                return (
                    jsonify(
                        {
                            "error": "CNPJ já cadastrado",
                            "fornecedor_existente": {
                                "id": existente.id,
                                "nome": existente.nome,
                            },
                        }
                    ),
                    409,
                )

        novo_fornecedor = Fornecedor(
            nome=data["nome"],
            cnpj=cnpj or "",
            telefone=data.get("telefone", ""),
            email=data.get("email", ""),
            cidade=data.get("cidade", ""),
            estado=data.get("estado", ""),
            contato_nome=data.get("contato_nome", ""),
            ativo=data.get("ativo", True),
        )

        db.session.add(novo_fornecedor)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Fornecedor criado com sucesso",
                    "fornecedor": {
                        "id": novo_fornecedor.id,
                        "nome": novo_fornecedor.nome,
                        "cnpj": novo_fornecedor.cnpj,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar fornecedor: {str(e)}")
        return jsonify({"error": f"Erro ao criar fornecedor: {str(e)}"}), 500


@fornecedores_bp.route("/<int:id>", methods=["PUT"])
def atualizar_fornecedor(id):
    """Atualizar informações de um fornecedor (mantida igual)"""
    try:
        fornecedor = Fornecedor.query.get(id)

        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Verificar CNPJ único (se estiver sendo alterado)
        if "cnpj" in data and data["cnpj"] != fornecedor.cnpj:
            existente = Fornecedor.query.filter_by(cnpj=data["cnpj"]).first()
            if existente and existente.id != id:
                return (
                    jsonify(
                        {
                            "error": "CNPJ já cadastrado em outro fornecedor",
                            "fornecedor_existente": {
                                "id": existente.id,
                                "nome": existente.nome,
                            },
                        }
                    ),
                    409,
                )

        # Atualizar campos
        campos_permitidos = [
            "nome",
            "cnpj",
            "telefone",
            "email",
            "cidade",
            "estado",
            "contato_nome",
            "ativo",
        ]

        for campo in campos_permitidos:
            if campo in data:
                setattr(fornecedor, campo, data[campo])

        fornecedor.data_atualizacao = datetime.utcnow()
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Fornecedor atualizado com sucesso",
                "fornecedor": {
                    "id": fornecedor.id,
                    "nome": fornecedor.nome,
                    "cnpj": fornecedor.cnpj,
                    "ativo": fornecedor.ativo,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar fornecedor {id}: {str(e)}")
        return jsonify({"error": f"Erro ao atualizar fornecedor: {str(e)}"}), 500


@fornecedores_bp.route("/<int:id>", methods=["DELETE"])
def excluir_fornecedor(id):
    """Excluir (desativar) um fornecedor (mantida igual)"""
    try:
        fornecedor = Fornecedor.query.get(id)

        if not fornecedor:
            return jsonify({"error": "Fornecedor não encontrado"}), 404

        # Verificar se fornecedor tem produtos ativos
        produtos_ativos = Produto.query.filter_by(fornecedor_id=id, ativo=True).count()
        if produtos_ativos > 0:
            return (
                jsonify(
                    {
                        "error": "Não é possível excluir o fornecedor pois existem produtos ativos vinculados a ele",
                        "quantidade_produtos": produtos_ativos,
                    }
                ),
                400,
            )

        # Exclusão lógica
        fornecedor.ativo = False
        fornecedor.data_atualizacao = datetime.utcnow()

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Fornecedor desativado com sucesso",
                "fornecedor": {
                    "id": fornecedor.id,
                    "nome": fornecedor.nome,
                    "ativo": False,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir fornecedor {id}: {str(e)}")
        return jsonify({"error": f"Erro ao excluir fornecedor: {str(e)}"}), 500
