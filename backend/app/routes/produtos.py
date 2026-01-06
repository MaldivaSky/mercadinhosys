from flask import Blueprint, request, jsonify
from app import db
from app.models import Produto, Fornecedor
from datetime import datetime, date
from sqlalchemy import or_, and_, func

produtos_bp = Blueprint("produtos", __name__, url_prefix="/api/produtos")


# ==================== ROTAS PARA PDV ====================


@produtos_bp.route("/search", methods=["GET"])
def search_products():
    """Buscar produtos por nome, marca, categoria ou código de barras - PARA PDV"""
    query = request.args.get("q", "").strip()
    limit = min(request.args.get("limit", 20, type=int), 100)

    # Construir query base
    produtos_query = Produto.query.filter_by(ativo=True)

    # Se houver termo de busca, aplicar filtros
    if query:
        produtos_query = produtos_query.filter(
            db.or_(
                Produto.nome.ilike(f"%{query}%"),
                Produto.marca.ilike(f"%{query}%"),
                Produto.categoria.ilike(f"%{query}%"),
                Produto.codigo_barras.ilike(f"%{query}%"),
            )
        )

    # Ordenar e limitar
    produtos = produtos_query.order_by(Produto.nome).limit(limit).all()

    resultado = []
    for p in produtos:
        resultado.append(
            {
                "id": p.id,
                "nome": p.nome,
                "codigo_barras": p.codigo_barras,
                "preco_venda": float(p.preco_venda),
                "preco_custo": float(p.preco_custo) if p.preco_custo else 0,
                "quantidade_estoque": p.quantidade,
                "unidade_medida": p.unidade_medida,
                "categoria": p.categoria,
                "marca": p.marca,
                "margem_lucro": float(p.margem_lucro) if p.margem_lucro else 0,
                "ativo": p.ativo,
            }
        )

    return jsonify(resultado)


@produtos_bp.route("/barcode/<codigo>", methods=["GET"])
def get_by_barcode(codigo):
    """Buscar produto específico por código de barras - PARA PDV"""
    produto = Produto.query.filter_by(codigo_barras=codigo, ativo=True).first()

    if not produto:
        return jsonify({"error": "Produto não encontrado"}), 404

    return jsonify(
        {
            "id": produto.id,
            "nome": produto.nome,
            "codigo_barras": produto.codigo_barras,
            "preco_venda": float(produto.preco_venda),
            "preco_custo": float(produto.preco_custo) if produto.preco_custo else 0,
            "quantidade_estoque": produto.quantidade,
            "unidade_medida": produto.unidade_medida,
            "categoria": produto.categoria,
            "marca": produto.marca,
            "margem_lucro": float(produto.margem_lucro) if produto.margem_lucro else 0,
            "ativo": produto.ativo,
        }
    )


@produtos_bp.route("/quick-add", methods=["POST"])
def quick_add():
    """Cadastro rápido de produto direto do PDV"""
    print("=== INÍCIO quick-add ===")

    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Dados JSON inválidos ou vazios"}), 400

        print(f"Dados recebidos: {data}")

        # Validações
        nome = data.get("nome")
        if not nome:
            return jsonify({"error": "Campo 'nome' é obrigatório"}), 400

        preco_venda = data.get("preco_venda")
        if preco_venda is None:
            return jsonify({"error": "Campo 'preco_venda' é obrigatório"}), 400

        try:
            preco_venda_float = float(preco_venda)
        except (ValueError, TypeError):
            return jsonify({"error": "Campo 'preco_venda' deve ser um número"}), 400

        if preco_venda_float <= 0:
            return jsonify({"error": "Preço de venda deve ser maior que zero"}), 400

        # Verificar código de barras único
        codigo_barras = data.get("codigo_barras")
        if codigo_barras:
            existe = Produto.query.filter_by(codigo_barras=codigo_barras).first()
            if existe:
                return (
                    jsonify(
                        {
                            "error": "Código de barras já existe",
                            "product": {
                                "id": existe.id,
                                "name": existe.nome,
                                "barcode": existe.codigo_barras,
                                "price": float(existe.preco_venda),
                            },
                        }
                    ),
                    409,
                )

        # Criar produto
        novo_produto = Produto(
            estabelecimento_id=1,
            nome=nome,
            preco_venda=preco_venda_float,
            preco_custo=float(data.get("preco_custo", 0)),
            quantidade=float(data.get("quantidade", 0)),
            codigo_barras=codigo_barras or "",
            descricao=data.get("descricao", ""),
            margem_lucro=float(data.get("margem_lucro", 30.0)),
            quantidade_minima=float(data.get("quantidade_minima", 10)),
            marca=data.get("marca", "Sem Marca"),
            fabricante=data.get("fabricante", ""),
            tipo=data.get("tipo", "unidade"),
            unidade_medida=data.get("unidade_medida", "un"),
            fornecedor_id=data.get("fornecedor_id"),
            categoria=data.get("categoria", "Geral"),
            ativo=True,
        )

        db.session.add(novo_produto)
        db.session.commit()

        print(f"✅ Produto salvo! ID: {novo_produto.id}")

        return (
            jsonify(
                {
                    "id": novo_produto.id,
                    "name": novo_produto.nome,
                    "barcode": novo_produto.codigo_barras,
                    "price": float(novo_produto.preco_venda),
                    "stock": novo_produto.quantidade,
                    "isBulk": novo_produto.tipo == "granel",
                    "unit": novo_produto.unidade_medida,
                    "fornecedor_id": novo_produto.fornecedor_id,
                    "fornecedor_nome": (
                        novo_produto.fornecedor.nome if novo_produto.fornecedor else None
                    ),
                    "success": True,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"ERRO: {str(e)}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


# ==================== CRUD COMPLETO PARA ESTOQUE ====================


@produtos_bp.route("/estoque", methods=["GET"])
def listar_estoque():
    """
    Listar todos os produtos com paginação e filtros avançados

    Parâmetros de consulta (query parameters):
    - pagina: Número da página (padrão: 1)
    - por_pagina: Itens por página (padrão: 50, máximo: 100)
    - busca: Texto para busca (nome, código de barras, marca, descrição)
    - categoria: Filtrar por categoria específica
    - fornecedor_id: Filtrar por ID do fornecedor
    - ativos: 'true' para apenas ativos, 'false' para incluir inativos (padrão: 'true')
    - preco_min: Preço mínimo de venda
    - preco_max: Preço máximo de venda
    - estoque_status: 'baixo', 'esgotado', 'normal'
    - tipo: Tipo de produto (unidade, granel, etc.)
    - ordenar_por: Campo para ordenação (nome, preco_venda, quantidade, created_at, etc.)
    - direcao: Direção da ordenação ('asc' ou 'desc', padrão: 'asc')
    """
    try:
        # ==================== PARÂMETROS DE PAGINAÇÃO ====================
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = min(
            request.args.get("por_pagina", 50, type=int), 100
        )  # Máximo 100

        # ==================== PARÂMETROS DE FILTRO ====================
        busca = request.args.get("busca", "").strip()
        categoria = request.args.get("categoria", "").strip()
        fornecedor_id = request.args.get("fornecedor_id", type=int)
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"
        preco_min = request.args.get("preco_min", type=float)
        preco_max = request.args.get("preco_max", type=float)
        estoque_status = request.args.get("estoque_status", "").strip()
        tipo_produto = request.args.get("tipo", "").strip()

        # ==================== PARÂMETROS DE ORDENAÇÃO ====================
        ordenar_por = request.args.get("ordenar_por", "nome")
        direcao = request.args.get("direcao", "asc").lower()

        # Mapeamento seguro de campos para ordenação
        campos_ordenacao = {
            "id": Produto.id,
            "nome": Produto.nome,
            "codigo_barras": Produto.codigo_barras,
            "preco_custo": Produto.preco_custo,
            "preco_venda": Produto.preco_venda,
            "quantidade": Produto.quantidade,
            "quantidade_minima": Produto.quantidade_minima,
            "categoria": Produto.categoria,
            "marca": Produto.marca,
            "tipo": Produto.tipo,
            "created_at": Produto.created_at,
            "updated_at": Produto.updated_at,
            "ativo": Produto.ativo,
        }

        # Campo padrão se o campo solicitado não existir
        campo_ordenacao = campos_ordenacao.get(ordenar_por, Produto.nome)

        # ==================== CONSTRUÇÃO DA QUERY ====================
        query = Produto.query

        # Filtro de busca por texto
        if busca:
            query = query.filter(
                db.or_(
                    Produto.nome.ilike(f"%{busca}%"),
                    Produto.codigo_barras.ilike(f"%{busca}%"),
                    Produto.marca.ilike(f"%{busca}%"),
                    Produto.descricao.ilike(f"%{busca}%"),
                )
            )

        # Filtro por categoria (case-insensitive)
        if categoria:
            query = query.filter(Produto.categoria.ilike(f"%{categoria}%"))

        # Filtro por fornecedor
        if fornecedor_id:
            query = query.filter(Produto.fornecedor_id == fornecedor_id)

        # Filtro por status ativo/inativo
        if apenas_ativos:
            query = query.filter(Produto.ativo == True)

        # Filtro por faixa de preço
        if preco_min is not None:
            query = query.filter(Produto.preco_venda >= preco_min)
        if preco_max is not None:
            query = query.filter(Produto.preco_venda <= preco_max)

        # Filtro por status de estoque
        if estoque_status:
            if estoque_status == "baixo":
                query = query.filter(
                    Produto.quantidade < Produto.quantidade_minima,
                    Produto.quantidade > 0,
                )
            elif estoque_status == "esgotado":
                query = query.filter(Produto.quantidade <= 0)
            elif estoque_status == "normal":
                query = query.filter(Produto.quantidade >= Produto.quantidade_minima)

        # Filtro por tipo de produto (case-insensitive)
        if tipo_produto:
            query = query.filter(Produto.tipo.ilike(f"%{tipo_produto}%"))

        # ==================== APLICAÇÃO DA ORDENAÇÃO ====================
        if direcao == "desc":
            query = query.order_by(campo_ordenacao.desc())
        else:
            query = query.order_by(campo_ordenacao.asc())

        # ==================== PAGINAÇÃO ====================
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        produtos = paginacao.items

        # ==================== FORMATANDO RESULTADOS ====================
        resultado = []
        for p in produtos:
            # Determinar status do estoque
            estoque_status_local = "normal"
            if p.quantidade <= 0:
                estoque_status_local = "esgotado"
            elif p.quantidade < p.quantidade_minima:
                estoque_status_local = "baixo"

            produto_dict = {
                "id": p.id,
                "nome": p.nome,
                "codigo_barras": p.codigo_barras,
                "descricao": p.descricao,
                "fornecedor_id": p.fornecedor_id,
                "fornecedor_nome": p.fornecedor.nome if p.fornecedor else None,
                "preco_custo": float(p.preco_custo) if p.preco_custo else 0.0,
                "preco_venda": float(p.preco_venda) if p.preco_venda else 0.0,
                "margem_lucro": float(p.margem_lucro) if p.margem_lucro else 0.0,
                "quantidade": p.quantidade if p.quantidade is not None else 0,
                "quantidade_minima": p.quantidade_minima if p.quantidade_minima is not None else 0,
                "estoque_status": estoque_status_local,
                "categoria": p.categoria,
                "marca": p.marca,
                "fabricante": p.fabricante if hasattr(p, 'fabricante') else None,
                "tipo": p.tipo if hasattr(p, 'tipo') else "unidade",
                "unidade_medida": p.unidade_medida,
                "ativo": p.ativo,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }

            resultado.append(produto_dict)

        # ==================== ESTATÍSTICAS ====================
        # Para estatísticas, precisamos contar com os mesmos filtros
        total_produtos = paginacao.total
        produtos_baixo_estoque = 0
        produtos_esgotados = 0

        # Podemos calcular estatísticas com uma query separada ou reutilizando
        # Vamos fazer uma query para contar os status
        if query.count() > 0:
            produtos_baixo_estoque = query.filter(
                Produto.quantidade < Produto.quantidade_minima, Produto.quantidade > 0
            ).count()

            produtos_esgotados = query.filter(Produto.quantidade <= 0).count()

        # ==================== RESPOSTA ====================
        return jsonify(
            {
                "produtos": resultado,
                "paginacao": {
                    "pagina_atual": paginacao.page,
                    "total_paginas": paginacao.pages,
                    "total_itens": paginacao.total,
                    "itens_por_pagina": paginacao.per_page,
                    "tem_proxima": paginacao.has_next,
                    "tem_anterior": paginacao.has_prev,
                    "primeira_pagina": 1,
                    "ultima_pagina": paginacao.pages,
                },
                "estatisticas": {
                    "total_produtos": total_produtos,
                    "produtos_baixo_estoque": produtos_baixo_estoque,
                    "produtos_esgotados": produtos_esgotados,
                    "produtos_normal": total_produtos
                    - (produtos_baixo_estoque + produtos_esgotados),
                },
                "filtros_aplicados": {
                    "busca": busca if busca else None,
                    "categoria": categoria if categoria else None,
                    "fornecedor_id": fornecedor_id if fornecedor_id else None,
                    "apenas_ativos": apenas_ativos,
                    "preco_min": preco_min,
                    "preco_max": preco_max,
                    "estoque_status": estoque_status if estoque_status else None,
                    "tipo": tipo_produto if tipo_produto else None,
                    "ordenar_por": ordenar_por,
                    "direcao": direcao,
                },
            }
        )

    except Exception as e:
        print(f"Erro ao listar estoque: {str(e)}")
        return jsonify({"error": f"Erro ao listar produtos: {str(e)}"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["GET"])
def detalhes_produto(id):
    """Obter detalhes completos de um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        estoque_status = "normal"
        if produto.quantidade <= 0:
            estoque_status = "esgotado"
        elif produto.quantidade < produto.quantidade_minima:
            estoque_status = "baixo"

        return jsonify(
            {
                "id": produto.id,
                "nome": produto.nome,
                "codigo_barras": produto.codigo_barras,
                "descricao": produto.descricao,
                "fornecedor_id": produto.fornecedor_id,
                    "fornecedor_nome": produto.fornecedor.nome if produto.fornecedor else None,
                "fabricante": produto.fabricante,
                "preco_custo": float(produto.preco_custo),
                "preco_venda": float(produto.preco_venda),
                "margem_lucro": float(produto.margem_lucro),
                "quantidade": produto.quantidade,
                "quantidade_minima": produto.quantidade_minima,
                "estoque_status": estoque_status,
                "categoria": produto.categoria,
                "marca": produto.marca,
                "fabricante": produto.fabricante,
                "tipo": produto.tipo,
                "unidade_medida": produto.unidade_medida,
                "ativo": produto.ativo,
                "created_at": (
                    produto.created_at.isoformat() if produto.created_at else None
                ),
                "updated_at": (
                    produto.updated_at.isoformat() if produto.updated_at else None
                ),
            }
        )

    except Exception as e:
        print(f"Erro ao obter detalhes do produto {id}: {str(e)}")
        return jsonify({"error": f"Erro ao obter produto: {str(e)}"}), 404


@produtos_bp.route("/estoque", methods=["POST"])
def criar_produto():
    """Criar um novo produto (cadastro completo)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Validações
        if not data.get("nome"):
            return jsonify({"error": "Nome do produto é obrigatório"}), 400

        try:
            preco_venda = float(data.get("preco_venda", 0))
            if preco_venda <= 0:
                return jsonify({"error": "Preço de venda deve ser maior que zero"}), 400
        except:
            return jsonify({"error": "Preço de venda inválido"}), 400

        # Verificar código de barras único
        codigo_barras = data.get("codigo_barras")
        if codigo_barras:
            existente = Produto.query.filter_by(codigo_barras=codigo_barras).first()
            if existente:
                return (
                    jsonify(
                        {
                            "error": "Código de barras já cadastrado",
                            "produto_existente": {
                                "id": existente.id,
                                "nome": existente.nome,
                            },
                        }
                    ),
                    409,
                )

        # Converter datas de string para objetos date
        data_fabricacao = None
        if data.get("data_fabricacao"):
            try:
                data_fabricacao = datetime.strptime(data["data_fabricacao"], "%Y-%m-%d").date()
            except ValueError:
                pass

        data_validade = None
        if data.get("data_validade"):
            try:
                data_validade = datetime.strptime(data["data_validade"], "%Y-%m-%d").date()
            except ValueError:
                pass

        # Criar produto
        novo_produto = Produto(
            estabelecimento_id=1,  # ID do estabelecimento padrão
            nome=data["nome"],
            codigo_barras=codigo_barras or "",
            descricao=data.get("descricao", ""),
            fornecedor_id=data.get("fornecedor_id"),
            fabricante=data.get("fabricante", ""),
            preco_custo=float(data.get("preco_custo", 0)),
            preco_venda=preco_venda,
            margem_lucro=float(data.get("margem_lucro", 30.0)),
            quantidade=float(data.get("quantidade", 0)),
            quantidade_minima=float(data.get("quantidade_minima", 10)),
            categoria=data.get("categoria", "Geral"),
            marca=data.get("marca", "Sem Marca"),
            tipo=data.get("tipo", "unidade"),
            unidade_medida=data.get("unidade_medida", "un"),
            ativo=data.get("ativo", True),
            lote=data.get("lote"),
            data_fabricacao=data_fabricacao,
            data_validade=data_validade,
        )

        db.session.add(novo_produto)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Produto criado com sucesso",
                    "produto": {
                        "id": novo_produto.id,
                        "nome": novo_produto.nome,
                        "codigo_barras": novo_produto.codigo_barras,
                        "fornecedor_id": novo_produto.fornecedor_id,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar produto: {str(e)}")
        return jsonify({"error": f"Erro ao criar produto: {str(e)}"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["PUT"])
def atualizar_produto(id):
    """Atualizar informações de um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Validações
        if "preco_venda" in data:
            try:
                preco_venda = float(data["preco_venda"])
                if preco_venda <= 0:
                    return (
                        jsonify({"error": "Preço de venda deve ser maior que zero"}),
                        400,
                    )
            except:
                return jsonify({"error": "Preço de venda inválido"}), 400

        # Verificar código de barras único
        if "codigo_barras" in data and data["codigo_barras"] != produto.codigo_barras:
            existente = Produto.query.filter_by(
                codigo_barras=data["codigo_barras"]
            ).first()
            if existente and existente.id != id:
                return (
                    jsonify(
                        {
                            "error": "Código de barras já cadastrado em outro produto",
                            "produto_existente": {
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
            "codigo_barras",
            "descricao",
            "fornecedor_id",
            "preco_custo",
            "preco_venda",
            "margem_lucro",
            "quantidade",
            "quantidade_minima",
            "categoria",
            "marca",
            "fabricante",
            "tipo",
            "unidade_medida",
            "ativo",
            "lote",
        ]

        for campo in campos_permitidos:
            if campo in data:
                setattr(produto, campo, data[campo])

        # Converter datas de string para objetos date
        if "data_fabricacao" in data and data["data_fabricacao"]:
            try:
                produto.data_fabricacao = datetime.strptime(data["data_fabricacao"], "%Y-%m-%d").date()
            except ValueError:
                produto.data_fabricacao = None
        elif "data_fabricacao" in data:
            produto.data_fabricacao = None

        if "data_validade" in data and data["data_validade"]:
            try:
                produto.data_validade = datetime.strptime(data["data_validade"], "%Y-%m-%d").date()
            except ValueError:
                produto.data_validade = None
        elif "data_validade" in data:
            produto.data_validade = None

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Produto atualizado com sucesso",
                "produto": {
                    "id": produto.id,
                    "nome": produto.nome,
                    "quantidade": produto.quantidade,
                    "preco_venda": float(produto.preco_venda),
                    "ativo": produto.ativo,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar produto {id}: {str(e)}")
        return jsonify({"error": f"Erro ao atualizar produto: {str(e)}"}), 500


@produtos_bp.route("/estoque/<int:id>", methods=["DELETE"])
def excluir_produto(id):
    """Excluir (desativar) um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        # Exclusão lógica
        produto.ativo = False
        produto.quantidade = 0

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Produto desativado com sucesso",
                "produto": {"id": produto.id, "nome": produto.nome, "ativo": False},
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir produto {id}: {str(e)}")
        return jsonify({"error": f"Erro ao excluir produto: {str(e)}"}), 500


@produtos_bp.route("/estoque/<int:id>/estoque", methods=["PUT"])
def ajustar_estoque(id):
    """Ajustar estoque de um produto"""
    try:
        produto = Produto.query.get(id)

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        data = request.get_json()

        if not data or "quantidade" not in data or "operacao" not in data:
            return (
                jsonify(
                    {"error": "Dados inválidos. Forneça 'quantidade' e 'operacao'"}
                ),
                400,
            )

        quantidade = float(data["quantidade"])
        operacao = data["operacao"]
        motivo = data.get("motivo", "")

        if quantidade <= 0:
            return jsonify({"error": "Quantidade deve ser maior que zero"}), 400

        if operacao == "entrada":
            produto.quantidade += quantidade
            movimento = "Entrada"
        elif operacao == "saida":
            if produto.quantidade < quantidade:
                return (
                    jsonify(
                        {
                            "error": "Estoque insuficiente",
                            "estoque_atual": produto.quantidade,
                            "quantidade_solicitada": quantidade,
                        }
                    ),
                    400,
                )
            produto.quantidade -= quantidade
            movimento = "Saída"
        else:
            return (
                jsonify({"error": "Operação inválida. Use 'entrada' ou 'saida'"}),
                400,
            )

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"Estoque ajustado: {movimento} de {quantidade} unidades",
                "motivo": motivo,
                "produto": {
                    "id": produto.id,
                    "nome": produto.nome,
                    "quantidade_anterior": produto.quantidade
                    - (quantidade if operacao == "entrada" else -quantidade),
                    "quantidade_atual": produto.quantidade,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao ajustar estoque do produto {id}: {str(e)}")
        return jsonify({"error": f"Erro ao ajustar estoque: {str(e)}"}), 500


@produtos_bp.route("/categorias", methods=["GET"])
def listar_categorias():
    """Listar todas as categorias de produtos"""
    try:
        # Adicionar filtro por ativos apenas
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"

        query = Produto.query

        if apenas_ativos:
            query = query.filter_by(ativo=True)

        produtos = query.all()
        categorias = set()

        for p in produtos:
            if p.categoria:
                categorias.add(p.categoria)

        return jsonify(
            {
                "categorias": sorted(list(categorias)),
                "total_categorias": len(categorias),
            }
        )

    except Exception as e:
        print(f"Erro ao listar categorias: {str(e)}")
        return jsonify({"error": f"Erro ao listar categorias: {str(e)}"}), 500


@produtos_bp.route("/relatorio/estoque", methods=["GET"])
def relatorio_estoque():
    """Gerar relatório de estoque com paginação e filtros"""
    try:
        # ==================== PARÂMETROS DE PAGINAÇÃO ====================
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = min(request.args.get("por_pagina", 100, type=int), 500)

        # ==================== PARÂMETROS DE FILTRO ====================
        categoria = request.args.get("categoria", "").strip()
        estoque_status = request.args.get("estoque_status", "").strip()
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"

        # ==================== CONSTRUÇÃO DA QUERY ====================
        query = Produto.query

        if apenas_ativos:
            query = query.filter_by(ativo=True)

        if categoria:
            query = query.filter(Produto.categoria.ilike(f"%{categoria}%"))

        # Filtro por status de estoque
        if estoque_status:
            if estoque_status == "baixo":
                query = query.filter(
                    Produto.quantidade < Produto.quantidade_minima,
                    Produto.quantidade > 0,
                )
            elif estoque_status == "esgotado":
                query = query.filter(Produto.quantidade <= 0)
            elif estoque_status == "normal":
                query = query.filter(Produto.quantidade >= Produto.quantidade_minima)

        query = query.order_by(Produto.nome.asc())

        # ==================== PAGINAÇÃO ====================
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        produtos = paginacao.items

        resultado = []
        for p in produtos:
            estoque_status_local = "normal"
            if p.quantidade <= 0:
                estoque_status_local = "esgotado"
            elif p.quantidade < p.quantidade_minima:
                estoque_status_local = "baixo"

            resultado.append(
                {
                    "id": p.id,
                    "nome": p.nome,
                    "codigo_barras": p.codigo_barras,
                    "quantidade": p.quantidade,
                    "quantidade_minima": p.quantidade_minima,
                    "estoque_status": estoque_status_local,
                    "preco_custo": float(p.preco_custo),
                    "preco_venda": float(p.preco_venda),
                    "valor_estoque": float(p.preco_custo * p.quantidade),
                    "marca": p.marca,
                    "categoria": p.categoria,
                    "fornecedor_nome": (
                        p.fornecedor.nome if p.fornecedor else None
                    ),
                }
            )

        # Totais
        total_valor_estoque = sum(p["valor_estoque"] for p in resultado)
        produtos_baixo_estoque = sum(
            1 for p in resultado if p["estoque_status"] == "baixo"
        )
        produtos_esgotados = sum(
            1 for p in resultado if p["estoque_status"] == "esgotado"
        )

        # ==================== RESPOSTA ====================
        return jsonify(
            {
                "produtos": resultado,
                "paginacao": {
                    "pagina_atual": paginacao.page,
                    "total_paginas": paginacao.pages,
                    "total_itens": paginacao.total,
                    "itens_por_pagina": paginacao.per_page,
                    "tem_proxima": paginacao.has_next,
                    "tem_anterior": paginacao.has_prev,
                },
                "totais": {
                    "total_produtos": paginacao.total,
                    "total_valor_estoque": float(total_valor_estoque),
                    "produtos_baixo_estoque": produtos_baixo_estoque,
                    "produtos_esgotados": produtos_esgotados,
                    "data_geracao": datetime.now().isoformat(),
                },
            }
        )

    except Exception as e:
        print(f"Erro ao gerar relatório: {str(e)}")
        return jsonify({"error": f"Erro ao gerar relatório: {str(e)}"}), 500


@produtos_bp.route("/exportar/csv", methods=["GET"])
def exportar_csv():
    """Exportar produtos para CSV (simplificado)"""
    try:
        # Parâmetros básicos de filtro
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"

        query = Produto.query

        if apenas_ativos:
            query = query.filter_by(ativo=True)

        produtos = query.order_by(Produto.nome.asc()).all()

        # Cabeçalho CSV
        csv_lines = [
            "ID;Nome;Código de Barras;Categoria;Marca;Quantidade;Quantidade Mínima;Preço Custo;Preço Venda;Status Estoque;Fornecedor"
        ]

        for p in produtos:
            estoque_status = "NORMAL"
            if p.quantidade <= 0:
                estoque_status = "ESGOTADO"
            elif p.quantidade < p.quantidade_minima:
                estoque_status = "BAIXO"

            fornecedor_nome = p.fornecedor.nome if p.fornecedor else ""

            csv_lines.append(
                f'{p.id};"{p.nome}";{p.codigo_barras};{p.categoria};{p.marca};'
                f"{p.quantidade};{p.quantidade_minima};{p.preco_custo};{p.preco_venda};"
                f'{estoque_status};"{fornecedor_nome}"'
            )

        return jsonify(
            {
                "success": True,
                "csv": "\n".join(csv_lines),
                "total_produtos": len(produtos),
                "data_exportacao": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        print(f"Erro ao exportar CSV: {str(e)}")
        return jsonify({"error": f"Erro ao exportar CSV: {str(e)}"}), 500
