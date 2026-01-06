from flask import Blueprint, request, jsonify
from app import db
from app.models import Cliente, Venda, VendaItem
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func

clientes_bp = Blueprint("clientes", __name__, url_prefix="/api/clientes")

@clientes_bp.route("/curva_compras", methods=["GET"])
def curva_compras():
    """
    Retorna a curva de compras agregada por mês (últimos 12 meses) para todos os clientes.
    """
    try:
        hoje = datetime.utcnow()
        meses = []
        for i in range(11, -1, -1):
            mes = (hoje.replace(day=1) - timedelta(days=30*i)).replace(day=1)
            meses.append(mes)
        # Buscar vendas agrupadas por ano/mes
        results = (
            db.session.query(
                func.extract('year', Venda.created_at).label('ano'),
                func.extract('month', Venda.created_at).label('mes'),
                func.sum(Venda.total).label('total')
            )
            .filter(Venda.created_at >= meses[-1])
            .group_by('ano', 'mes')
            .order_by('ano', 'mes')
            .all()
        )
        # Montar lista de pontos (YYYY-MM, total)
        curva = []
        for r in results:
            curva.append({
                'periodo': f"{int(r.ano):04d}-{int(r.mes):02d}",
                'total': float(r.total or 0)
            })
        return jsonify({'curva_compras': curva})
    except Exception as e:
        print(f"Erro ao gerar curva de compras: {str(e)}")
        return jsonify({'error': f'Erro ao gerar curva de compras: {str(e)}'}), 500



# ==================== CRUD CLIENTES COM PAGINAÇÃO AVANÇADA ====================


@clientes_bp.route("/", methods=["GET"])
def listar_clientes():
    """
    Listar todos os clientes com paginação e filtros avançados

    Parâmetros:
    - pagina: Número da página (padrão: 1)
    - por_pagina: Itens por página (padrão: 50, máximo: 100)
    - busca: Texto para busca (nome, CPF, email, telefone)
    - ativos: 'true' para apenas ativos, 'false' para todos (padrão: 'true')
    - ordenar_por: Campo para ordenação (nome, total_gasto, total_compras, data_cadastro)
    - direcao: Direção da ordenação ('asc' ou 'desc', padrão: 'asc')
    - limite_min: Filtro por limite de crédito mínimo
    - limite_max: Filtro por limite de crédito máximo
    - dia_vencimento: Filtro por dia de vencimento
    """
    try:
        # ==================== PARÂMETROS DE PAGINAÇÃO ====================
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = min(request.args.get("por_pagina", 50, type=int), 100)

        # ==================== PARÂMETROS DE FILTRO ====================
        busca = request.args.get("busca", "").strip()
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"
        # Campos removidos pois não existem no model Cliente
        limite_min = None
        limite_max = None
        dia_vencimento = None

        # ==================== PARÂMETROS DE ORDENAÇÃO ====================
        ordenar_por = request.args.get("ordenar_por", "nome")
        direcao = request.args.get("direcao", "asc").lower()

        # Mapeamento seguro de campos para ordenação
        campos_ordenacao = {
            "id": Cliente.id,
            "nome": Cliente.nome,
            "cpf_cnpj": Cliente.cpf_cnpj,
            "email": Cliente.email,
            "data_cadastro": Cliente.data_cadastro,
        }

        campo_ordenacao = campos_ordenacao.get(ordenar_por, Cliente.nome)

        # ==================== CONSTRUÇÃO DA QUERY ====================
        query = Cliente.query

        # Filtro de busca por texto
        if busca:
            query = query.filter(
                db.or_(
                    Cliente.nome.ilike(f"%{busca}%"),
                    Cliente.cpf_cnpj.ilike(f"%{busca}%"),
                    Cliente.email.ilike(f"%{busca}%"),
                    Cliente.telefone.ilike(f"%{busca}%"),
                    Cliente.celular.ilike(f"%{busca}%"),
                )
            )

        # Filtro por status ativo/inativo
        if apenas_ativos:
            query = query.filter(Cliente.ativo == True)

        # Filtro por faixa de limite de crédito
        # Filtros removidos pois os campos não existem

        # ==================== APLICAÇÃO DA ORDENAÇÃO ====================
        if direcao == "desc":
            query = query.order_by(campo_ordenacao.desc())
        else:
            query = query.order_by(campo_ordenacao.asc())

        # ==================== PAGINAÇÃO ====================
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        clientes = paginacao.items

        # ==================== FORMATANDO RESULTADOS COM ESTATÍSTICAS ====================
        resultado = []
        for cliente in clientes:
            # Calcular estatísticas de compras
            total_compras = Venda.query.filter_by(cliente_id=cliente.id).count()
            total_gasto = (
                db.session.query(db.func.sum(Venda.total))
                .filter_by(cliente_id=cliente.id)
                .scalar()
                or 0
            )

            # Calcular último mês de compras
            um_mes_atras = datetime.utcnow() - timedelta(days=30)
            compras_ultimo_mes = Venda.query.filter(
                Venda.cliente_id == cliente.id, Venda.created_at >= um_mes_atras
            ).count()

            cliente_dict = {
                "id": cliente.id,
                "nome": cliente.nome,
                "cpf_cnpj": cliente.cpf_cnpj,
                "telefone": cliente.telefone,
                "celular": getattr(cliente, "celular", None),
                "email": cliente.email,
                "endereco": cliente.endereco,
                "ativo": getattr(cliente, "ativo", True),
                "total_compras": total_compras,
                "total_gasto": float(total_gasto),
                "compras_ultimo_mes": compras_ultimo_mes,
                "valor_medio_compra": (
                    float(total_gasto / total_compras) if total_compras > 0 else 0
                ),
                "data_cadastro": (
                    cliente.data_cadastro.isoformat() if cliente.data_cadastro else None
                ),
                "observacoes": cliente.observacoes,
            }

            # Adicionar classificação do cliente
            if total_compras >= 20:
                cliente_dict["classificacao"] = "VIP"
            elif total_compras >= 10:
                cliente_dict["classificacao"] = "Frequente"
            elif total_compras >= 5:
                cliente_dict["classificacao"] = "Ocasional"
            else:
                cliente_dict["classificacao"] = "Novo"

            resultado.append(cliente_dict)

        # ==================== ESTATÍSTICAS GERAIS ====================
        # Usar subquery para evitar consultas adicionais
        total_clientes = paginacao.total
        clientes_ativos = (
            query.filter(Cliente.ativo == True).count()
            if not apenas_ativos
            else total_clientes
        )
        clientes_inativos = total_clientes - clientes_ativos if not apenas_ativos else 0

        # Calcular totais de limite de crédito
        total_limite_credito = 0  # Campo removido

        # ==================== RESPOSTA ====================
        return jsonify(
            {
                "clientes": resultado,
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
                    "total_clientes": total_clientes,
                    "clientes_ativos": clientes_ativos,
                    "clientes_inativos": clientes_inativos,
                    # Campos removidos: total_limite_credito, media_limite_credito
                    "clientes_novos": sum(
                        1 for c in resultado if c["total_compras"] == 0
                    ),
                    "clientes_vip": sum(
                        1 for c in resultado if c["classificacao"] == "VIP"
                    ),
                },
                "filtros_aplicados": {
                    "busca": busca if busca else None,
                    "apenas_ativos": apenas_ativos,
                    # Filtros removidos: limite_min, limite_max, dia_vencimento
                    "ordenar_por": ordenar_por,
                    "direcao": direcao,
                },
            }
        )

    except Exception as e:
        import traceback
        print(f"Erro ao listar clientes: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Erro ao listar clientes: {str(e)}", "trace": traceback.format_exc()}), 500


@clientes_bp.route("/<int:id>", methods=["GET"])
def detalhes_cliente(id):
    """
    Obter detalhes completos de um cliente com histórico de compras paginado

    Parâmetros:
    - pagina_compras: Número da página para compras (padrão: 1)
    - por_pagina_compras: Compras por página (padrão: 10, máximo: 50)
    """
    try:
        # Produtos preferidos (top 3)
        produtos_preferidos = (
            db.session.query(
                VendaItem.produto_nome,
                db.func.count(VendaItem.id).label("quantidade"),
                db.func.sum(VendaItem.total_item).label("valor_total")
            )
            .join(Venda, Venda.id == VendaItem.venda_id)
            .filter(Venda.cliente_id == id)
            .group_by(VendaItem.produto_nome)
            .order_by(db.func.count(VendaItem.id).desc())
            .limit(3)
            .all()
        )
        produtos_preferidos_list = [
            {
                "nome": nome,
                "quantidade": int(qtd),
                "valor_total": float(valor)
            }
            for nome, qtd, valor in produtos_preferidos
        ]
        # ...restante do código do endpoint detalhes_cliente, tudo dentro da função...
        # Parâmetros para paginação de compras
        pagina_compras = request.args.get("pagina_compras", 1, type=int)
        por_pagina_compras = min(
            request.args.get("por_pagina_compras", 10, type=int), 50
        )


        print(f"[DEBUG] Buscando detalhes do cliente id={id}")
        cliente = Cliente.query.get(id)
        if not cliente:
            print(f"[DEBUG] Cliente id={id} NÃO encontrado no banco!")
            return jsonify({"error": "Cliente não encontrado"}), 404
        else:
            print(f"[DEBUG] Cliente id={id} encontrado: {cliente.nome}")

        # ==================== HISTÓRICO DE COMPRAS PAGINADO ====================
        query_compras = Venda.query.filter_by(cliente_id=id).order_by(
            Venda.created_at.desc()
        )
        paginacao_compras = query_compras.paginate(
            page=pagina_compras, per_page=por_pagina_compras, error_out=False
        )
        compras = paginacao_compras.items

        compras_list = []
        for venda in compras:
            compras_list.append(
                {
                    "id": venda.id,
                    "codigo": venda.codigo,
                    "total": float(venda.total),
                    "forma_pagamento": venda.forma_pagamento,
                    "status": venda.status,
                    "data": venda.created_at.isoformat() if venda.created_at else None,
                    "itens_count": len(venda.itens) if venda.itens else 0,
                    "desconto": (
                        float(venda.desconto) if hasattr(venda, "desconto") else 0
                    ),
                    "acrescimo": (
                        float(venda.acrescimo) if hasattr(venda, "acrescimo") else 0
                    ),
                }
            )

        # ==================== ESTATÍSTICAS DETALHADAS ====================
        # Total geral
        total_compras = Venda.query.filter_by(cliente_id=id).count()
        total_gasto = (
            db.session.query(db.func.sum(Venda.total)).filter_by(cliente_id=id).scalar()
            or 0
        )

        # Últimos 30 dias
        um_mes_atras = datetime.utcnow() - timedelta(days=30)
        compras_ultimo_mes = Venda.query.filter(
            Venda.cliente_id == id, Venda.created_at >= um_mes_atras
        ).count()

        gasto_ultimo_mes = (
            db.session.query(db.func.sum(Venda.total))
            .filter(Venda.cliente_id == id, Venda.created_at >= um_mes_atras)
            .scalar()
            or 0
        )

        # Última compra
        ultima_compra = (
            Venda.query.filter_by(cliente_id=id)
            .order_by(Venda.created_at.desc())
            .first()
        )

        # Média de compras
        primeira_compra = (
            Venda.query.filter_by(cliente_id=id)
            .order_by(Venda.created_at.asc())
            .first()
        )
        media_mensal = 0

        if primeira_compra and total_compras > 0:
            dias_cadastro = (datetime.utcnow() - primeira_compra.created_at).days
            if dias_cadastro > 0:
                media_mensal = (total_compras * 30) / dias_cadastro

        # Classificação
        if total_compras >= 20:
            classificacao = "VIP"
        elif total_compras >= 10:
            classificacao = "Frequente"
        elif total_compras >= 5:
            classificacao = "Ocasional"
        else:
            classificacao = "Novo"

        # ==================== DADOS DO CLIENTE ====================
        cliente_dict = {
            "id": cliente.id,
            "nome": cliente.nome,
            "cpf_cnpj": cliente.cpf_cnpj,
            # "data_nascimento": None,  # Campo não existe
            # "idade": None,  # Campo não existe
            "telefone": cliente.telefone,
            "celular": cliente.celular,
            "email": cliente.email,
            "endereco": cliente.endereco,
            "limite_credito": float(getattr(cliente, "limite_credito", 0)),
            "limite_disponivel": float(getattr(cliente, "limite_credito", 0) - total_gasto),
            "limite_utilizado_percent": (
                (total_gasto / getattr(cliente, "limite_credito", 1) * 100)
                if getattr(cliente, "limite_credito", 0) > 0 else 0
            ),
            "dia_vencimento": getattr(cliente, "dia_vencimento", None),
            "observacoes": cliente.observacoes,
            "ativo": cliente.ativo,
            "data_cadastro": (
                cliente.data_cadastro.isoformat() if cliente.data_cadastro else None
            ),
            "data_atualizacao": (
                cliente.data_atualizacao.isoformat()
                if cliente.data_atualizacao
                else None
            ),
            "classificacao": classificacao,
            "compras": {
                "lista": compras_list,
                "paginacao": {
                    "pagina_atual": paginacao_compras.page,
                    "total_paginas": paginacao_compras.pages,
                    "total_itens": paginacao_compras.total,
                    "itens_por_pagina": paginacao_compras.per_page,
                    "tem_proxima": paginacao_compras.has_next,
                    "tem_anterior": paginacao_compras.has_prev,
                },
            },
            "estatisticas": {
                "total_compras": total_compras,
                "total_gasto": float(total_gasto),
                "ticket_medio": float(total_gasto / total_compras) if total_compras > 0 else 0,
                "compras_ultimo_mes": compras_ultimo_mes,
                "gasto_ultimo_mes": float(gasto_ultimo_mes),
                "media_compras_mensal": float(media_mensal),
                "ultima_compra_data": ultima_compra.created_at.isoformat() if ultima_compra else None,
                "ultima_compra_valor": float(ultima_compra.total) if ultima_compra else 0,
                "primeira_compra_data": primeira_compra.created_at.isoformat() if primeira_compra else None,
                "dias_ultima_compra": (datetime.utcnow() - ultima_compra.created_at).days if ultima_compra else None,
                "produtos_preferidos": produtos_preferidos_list,
            },
        }

        return jsonify(cliente_dict)

    except Exception as e:
        print(f"Erro ao obter cliente {id}: {str(e)}")
        return jsonify({"error": f"Erro ao obter cliente: {str(e)}"}), 404


@clientes_bp.route("/<int:id>", methods=["PUT"])
def atualizar_cliente(id):
    """Atualizar informações de um cliente com validações"""
    try:
        cliente = Cliente.query.get(id)

        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # ==================== VALIDAÇÕES ====================
        # Verificar CPF/CNPJ único (se estiver sendo alterado)
        if "cpf_cnpj" in data and data["cpf_cnpj"] != cliente.cpf_cnpj:
            cpf_cnpj_novo = data["cpf_cnpj"].strip()
            if cpf_cnpj_novo:
                if len(cpf_cnpj_novo) not in [11, 14] or not cpf_cnpj_novo.replace('.', '').replace('-', '').replace('/', '').isdigit():
                    return (
                        jsonify(
                            {"error": "CPF/CNPJ inválido. Deve conter 11 ou 14 dígitos numéricos"}
                        ),
                        400,
                    )

                existente = Cliente.query.filter_by(cpf_cnpj=cpf_cnpj_novo).first()
                if existente and existente.id != id:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "CPF/CNPJ já cadastrado em outro cliente",
                                "cliente_existente": {
                                    "id": existente.id,
                                    "nome": existente.nome,
                                    "email": existente.email,
                                },
                            }
                        ),
                        409,
                    )

        # Verificar email único (se estiver sendo alterado)
        if "email" in data and data["email"] != cliente.email:
            email_novo = data["email"].strip()
            if email_novo:
                if "@" not in email_novo or "." not in email_novo:
                    return jsonify({"error": "Email inválido"}), 400

                existente_email = Cliente.query.filter_by(email=email_novo).first()
                if existente_email and existente_email.id != id:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "Email já cadastrado em outro cliente",
                                "cliente_existente": {
                                    "id": existente_email.id,
                                    "nome": existente_email.nome,
                                    "cpf": existente_email.cpf,
                                },
                            }
                        ),
                        409,
                    )

        # Validar data de nascimento (se fornecida)
        if "data_nascimento" in data and data["data_nascimento"]:
            try:
                data_nascimento = datetime.strptime(
                    data["data_nascimento"], "%Y-%m-%d"
                ).date()
                if data_nascimento > datetime.utcnow().date():
                    return (
                        jsonify({"error": "Data de nascimento não pode ser futura"}),
                        400,
                    )
            except ValueError:
                return (
                    jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}),
                    400,
                )

        # Validar limite de crédito (se fornecido)
        if "limite_credito" in data:
            limite_credito = float(data["limite_credito"])
            if limite_credito < 0:
                return (
                    jsonify({"error": "Limite de crédito não pode ser negativo"}),
                    400,
                )

        # Validar dia de vencimento (se fornecido)
        if "dia_vencimento" in data:
            dia_vencimento = int(data["dia_vencimento"])
            if dia_vencimento < 1 or dia_vencimento > 31:
                return (
                    jsonify({"error": "Dia de vencimento deve estar entre 1 e 31"}),
                    400,
                )

        # ==================== ATUALIZAR CAMPOS ====================
        campos_permitidos = [
            "nome",
            "cpf_cnpj",
            # "rg",  # Removido pois não existe no model
            "data_nascimento",
            "telefone",
            "celular",
            "email",
            "endereco",
            "limite_credito",
            "dia_vencimento",
            "observacoes",
            "ativo",
        ]

        for campo in campos_permitidos:
            if campo in data:
                if campo == "data_nascimento" and data[campo]:
                    setattr(
                        cliente,
                        campo,
                        datetime.strptime(data[campo], "%Y-%m-%d").date(),
                    )
                elif campo in ["limite_credito"]:
                    setattr(cliente, campo, float(data[campo]))
                elif campo == "dia_vencimento":
                    setattr(cliente, campo, int(data[campo]))
                else:
                    setattr(
                        cliente,
                        campo,
                        (
                            data[campo].strip()
                            if isinstance(data[campo], str)
                            else data[campo]
                        ),
                    )

        cliente.data_atualizacao = datetime.utcnow()
        db.session.commit()

        # Buscar estatísticas atualizadas
        total_gasto = (
            db.session.query(db.func.sum(Venda.total)).filter_by(cliente_id=id).scalar()
            or 0
        )

        return jsonify(
            {
                "success": True,
                "message": "Cliente atualizado com sucesso",
                "cliente": {
                    "id": cliente.id,
                    "nome": cliente.nome,
                    "cpf_cnpj": cliente.cpf_cnpj,
                    "email": cliente.email,
                    "ativo": cliente.ativo,
                    # Adicione outros campos conforme necessário
                    "data_atualizacao": cliente.data_atualizacao.isoformat(),
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar cliente {id}: {str(e)}")
        return jsonify({"error": f"Erro ao atualizar cliente: {str(e)}"}), 500




@clientes_bp.route("/<int:id>/compras", methods=["GET"])
def compras_cliente(id):
    """
    Listar compras de um cliente específico com filtros avançados

    Parâmetros:
    - pagina: Número da página (padrão: 1)
    - por_pagina: Itens por página (padrão: 20, máximo: 100)
    - data_inicio: Filtrar compras a partir desta data (YYYY-MM-DD)
    - data_fim: Filtrar compras até esta data (YYYY-MM-DD)
    - forma_pagamento: Filtrar por forma de pagamento
    - status: Filtrar por status da venda
    - valor_min: Valor mínimo da compra
    - valor_max: Valor máximo da compra
    - ordenar_por: Campo para ordenação (data, total, id)
    - direcao: Direção da ordenação ('asc' ou 'desc')
    """
    try:
        cliente = Cliente.query.get(id)

        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        # ==================== PARÂMETROS ====================
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = min(request.args.get("por_pagina", 20, type=int), 100)
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        forma_pagamento = request.args.get("forma_pagamento")
        status = request.args.get("status")
        valor_min = request.args.get("valor_min", type=float)
        valor_max = request.args.get("valor_max", type=float)
        ordenar_por = request.args.get("ordenar_por", "created_at")
        direcao = request.args.get("direcao", "desc").lower()

        # ==================== CONSTRUÇÃO DA QUERY ====================
        query = Venda.query.filter_by(cliente_id=id)

        # Filtro por período
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
                query = query.filter(Venda.created_at >= data_inicio_dt)
            except ValueError:
                return (
                    jsonify(
                        {"error": "Formato de data_inicio inválido. Use YYYY-MM-DD"}
                    ),
                    400,
                )

        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
                query = query.filter(Venda.created_at <= data_fim_dt)
            except ValueError:
                return (
                    jsonify({"error": "Formato de data_fim inválido. Use YYYY-MM-DD"}),
                    400,
                )

        # Filtro por forma de pagamento
        if forma_pagamento:
            query = query.filter(Venda.forma_pagamento == forma_pagamento)

        # Filtro por status
        if status:
            query = query.filter(Venda.status == status)

        # Filtro por valor
        if valor_min is not None:
            query = query.filter(Venda.total >= valor_min)
        if valor_max is not None:
            query = query.filter(Venda.total <= valor_max)

        # Ordenação
        campos_ordenacao = {
            "id": Venda.id,
            "codigo": Venda.codigo,
            "total": Venda.total,
            "created_at": Venda.created_at,
            "forma_pagamento": Venda.forma_pagamento,
        }

        campo_ordenacao = campos_ordenacao.get(ordenar_por, Venda.created_at)

        if direcao == "asc":
            query = query.order_by(campo_ordenacao.asc())
        else:
            query = query.order_by(campo_ordenacao.desc())

        # ==================== PAGINAÇÃO ====================
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        compras = paginacao.items

        resultado = []
        for venda in compras:
            resultado.append(
                {
                    "id": venda.id,
                    "codigo": venda.codigo,
                    "total": float(venda.total),
                    "forma_pagamento": venda.forma_pagamento,
                    "status": venda.status,
                    "desconto": (
                        float(venda.desconto) if hasattr(venda, "desconto") else 0
                    ),
                    "acrescimo": (
                        float(venda.acrescimo) if hasattr(venda, "acrescimo") else 0
                    ),
                    "data": venda.created_at.isoformat() if venda.created_at else None,
                    "itens_count": len(venda.itens) if venda.itens else 0,
                    "vendedor_id": venda.funcionario_id,
                    "observacoes": (
                        venda.observacoes if hasattr(venda, "observacoes") else ""
                    ),
                }
            )

        # ==================== ESTATÍSTICAS ====================
        # Calcular totais com os mesmos filtros
        total_gasto = (
            db.session.query(db.func.sum(Venda.total))
            .filter(
                Venda.cliente_id == id, *query._whereclauses  # Aplicar mesmos filtros
            )
            .scalar()
            or 0
        )

        # Estatísticas por forma de pagamento
        formas_pagamento = (
            db.session.query(
                Venda.forma_pagamento,
                db.func.count(Venda.id).label("quantidade"),
                db.func.sum(Venda.total).label("total"),
            )
            .filter(
                Venda.cliente_id == id, *query._whereclauses  # Aplicar mesmos filtros
            )
            .group_by(Venda.forma_pagamento)
            .all()
        )

        formas_pagamento_dict = []
        for forma, qtd, total in formas_pagamento:
            formas_pagamento_dict.append(
                {"forma": forma, "quantidade": qtd, "total": float(total)}
            )

        # Média de compras
        media_compra = total_gasto / paginacao.total if paginacao.total > 0 else 0

        # Maior e menor compra no período
        maior_compra = (
            db.session.query(db.func.max(Venda.total))
            .filter(Venda.cliente_id == id, *query._whereclauses)
            .scalar()
            or 0
        )

        menor_compra = (
            db.session.query(db.func.min(Venda.total))
            .filter(Venda.cliente_id == id, *query._whereclauses)
            .scalar()
            or 0
        )

        return jsonify(
            {
                "cliente": {
                    "id": cliente.id,
                    "nome": cliente.nome,
                    "cpf": cliente.cpf,
                    "total_compras": paginacao.total,
                },
                "compras": resultado,
                "paginacao": {
                    "pagina_atual": paginacao.page,
                    "total_paginas": paginacao.pages,
                    "total_itens": paginacao.total,
                    "itens_por_pagina": paginacao.per_page,
                    "tem_proxima": paginacao.has_next,
                    "tem_anterior": paginacao.has_prev,
                },
                "estatisticas": {
                    "total_gasto": float(total_gasto),
                    "media_compra": float(media_compra),
                    "maior_compra": float(maior_compra),
                    "menor_compra": float(menor_compra),
                    "formas_pagamento": formas_pagamento_dict,
                    "periodo": {"data_inicio": data_inicio, "data_fim": data_fim},
                },
                "filtros_aplicados": {
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "forma_pagamento": forma_pagamento,
                    "status": status,
                    "valor_min": valor_min,
                    "valor_max": valor_max,
                    "ordenar_por": ordenar_por,
                    "direcao": direcao,
                },
            }
        )

    except Exception as e:
        print(f"Erro ao listar compras do cliente {id}: {str(e)}")
        return jsonify({"error": f"Erro ao listar compras: {str(e)}"}), 500



# ========== ENDPOINT DE BUSCA DE CLIENTES (CORRIGIDO) ==========
@clientes_bp.route("/search", methods=["GET"])
def buscar_clientes():
    """Buscar clientes por nome, CPF/CNPJ, telefone ou email, com opção de filtrar apenas clientes com compras."""
    try:
        busca = request.args.get("busca", "").strip()
        limite = min(request.args.get("limite", 20, type=int), 100)
        com_compras = request.args.get("com_compras", "false").lower() == "true"

        busca_query = Cliente.query
        if busca:
            busca_query = busca_query.filter(
                or_(
                    Cliente.nome.ilike(f"%{busca}%"),
                    Cliente.cpf_cnpj.ilike(f"%{busca}%"),
                    Cliente.telefone.ilike(f"%{busca}%"),
                    Cliente.email.ilike(f"%{busca}%"),
                )
            )

        if com_compras:
            clientes_com_compras = db.session.query(Venda.cliente_id).distinct()
            busca_query = busca_query.filter(Cliente.id.in_(clientes_com_compras))

        clientes = busca_query.order_by(Cliente.nome.asc()).limit(limite).all()

        resultado = []
        for cliente in clientes:
            # Buscar total de compras
            total_compras = Venda.query.filter_by(cliente_id=cliente.id).count()
            resultado.append({
                "id": cliente.id,
                "nome": cliente.nome,
                "cpf_cnpj": getattr(cliente, "cpf_cnpj", "") or "",
                "telefone": getattr(cliente, "telefone", "") or "",
                "email": getattr(cliente, "email", "") or "",
                "total_compras": total_compras,
            })

        resultado.sort(key=lambda x: x["nome"].lower())
        return jsonify(resultado[:limite])
    except Exception as e:
        print(f"Erro ao buscar clientes: {str(e)}")
        return jsonify({"error": f"Erro ao buscar clientes: {str(e)}"}), 500


@clientes_bp.route("/estatisticas", methods=["GET"])
def estatisticas_clientes():
    """Obter estatísticas gerais sobre clientes"""
    try:
        # ==================== PARÂMETROS ====================
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")

        # ==================== ESTATÍSTICAS BÁSICAS ====================
        total_clientes = Cliente.query.count()
        clientes_ativos = Cliente.query.filter_by(ativo=True).count()
        clientes_inativos = total_clientes - clientes_ativos

        # ==================== ESTATÍSTICAS DE COMPRAS ====================
        # Clientes com compras
        clientes_com_compras = db.session.query(
            db.func.count(db.distinct(Venda.cliente_id))
        ).scalar()

        # Clientes sem compras
        clientes_sem_compras = total_clientes - clientes_com_compras

        # ==================== LIMITE DE CRÉDITO ====================
        total_limite_credito = (
            db.session.query(db.func.sum(Cliente.limite_credito))
            .filter_by(ativo=True)
            .scalar()
            or 0
        )

        # ==================== ESTATÍSTICAS POR PERÍODO ====================
        novos_clientes_mes = 0
        if data_inicio and data_fim:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
                data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")

                novos_clientes_mes = Cliente.query.filter(
                    Cliente.data_cadastro.between(data_inicio_dt, data_fim_dt)
                ).count()
            except ValueError:
                pass

        # ==================== CLASSIFICAÇÃO DE CLIENTES ====================
        # Clientes VIP (20+ compras)
        clientes_vip = (
            db.session.query(Cliente)
            .join(Venda)
            .group_by(Cliente.id)
            .having(db.func.count(Venda.id) >= 20)
            .count()
        )

        # Clientes Frequentes (10-19 compras)
        clientes_frequentes = (
            db.session.query(Cliente)
            .join(Venda)
            .group_by(Cliente.id)
            .having(db.func.count(Venda.id).between(10, 19))
            .count()
        )

        # Clientes Ocasionais (5-9 compras)
        clientes_ocasionais = (
            db.session.query(Cliente)
            .join(Venda)
            .group_by(Cliente.id)
            .having(db.func.count(Venda.id).between(5, 9))
            .count()
        )

        # Clientes Novos (1-4 compras)
        clientes_novos = (
            db.session.query(Cliente)
            .join(Venda)
            .group_by(Cliente.id)
            .having(db.func.count(Venda.id).between(1, 4))
            .count()
        )

        return jsonify(
            {
                "estatisticas_gerais": {
                    "total_clientes": total_clientes,
                    "clientes_ativos": clientes_ativos,
                    "clientes_inativos": clientes_inativos,
                    "percentual_ativos": (
                        (clientes_ativos / total_clientes * 100)
                        if total_clientes > 0
                        else 0
                    ),
                    "novos_clientes_mes": novos_clientes_mes,
                    "total_limite_credito": float(total_limite_credito),
                    "media_limite_credito": (
                        float(total_limite_credito / clientes_ativos)
                        if clientes_ativos > 0
                        else 0
                    ),
                },
                "estatisticas_compras": {
                    "clientes_com_compras": clientes_com_compras,
                    "clientes_sem_compras": clientes_sem_compras,
                    "percentual_compras": (
                        (clientes_com_compras / total_clientes * 100)
                        if total_clientes > 0
                        else 0
                    ),
                },
                "classificacao_clientes": {
                    "vip": clientes_vip,
                    "frequentes": clientes_frequentes,
                    "ocasionais": clientes_ocasionais,
                    "novos": clientes_novos,
                    "inativos": clientes_inativos,
                },
                "periodo_analise": {
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "data_geracao": datetime.utcnow().isoformat(),
                },
            }
        )

    except Exception as e:
        print(f"Erro ao obter estatísticas: {str(e)}")
        return jsonify({"error": f"Erro ao obter estatísticas: {str(e)}"}), 500


@clientes_bp.route("/exportar", methods=["GET"])
def exportar_clientes():
    """Exportar lista de clientes para CSV"""
    try:
        # Parâmetros básicos
        apenas_ativos = request.args.get("ativos", "true").lower() == "true"
        incluir_compras = request.args.get("incluir_compras", "false").lower() == "true"

        # Construir query
        query = Cliente.query

        if apenas_ativos:
            query = query.filter_by(ativo=True)

        query = query.order_by(Cliente.nome.asc())

        # Limitar para 1000 registros na exportação
        clientes = query.limit(1000).all()

        # Preparar dados para CSV
        csv_data = []

        # Cabeçalho
        cabecalho = [
            "ID",
            "Nome",
            "CPF",
            # "RG",  # Removido pois não existe no model
            "Data Nascimento",
            "Telefone",
            "Celular",
            "Email",
            "Endereço",
            "Limite Crédito",
            "Dia Vencimento",
            "Status",
            "Data Cadastro",
            "Observações",
        ]

        if incluir_compras:
            cabecalho.extend(["Total Compras", "Total Gasto", "Última Compra"])

        csv_data.append(";".join(cabecalho))

        # Dados
        for cliente in clientes:
            linha = [
                str(cliente.id),
                f'"{cliente.nome}"',
                cliente.cpf,
                # cliente.rg,  # Removido pois não existe no model
                cliente.data_nascimento.isoformat() if hasattr(cliente, "data_nascimento") and cliente.data_nascimento else "",
                cliente.telefone,
                cliente.celular,
                cliente.email,
                f'"{cliente.endereco}"' if cliente.endereco else "",
                str(cliente.limite_credito),
                str(cliente.dia_vencimento),
                "Ativo" if cliente.ativo else "Inativo",
                cliente.data_cadastro.isoformat() if cliente.data_cadastro else "",
                f'"{cliente.observacoes}"' if cliente.observacoes else "",
            ]

            if incluir_compras:
                # Calcular estatísticas
                total_compras = Venda.query.filter_by(cliente_id=cliente.id).count()
                total_gasto = (
                    db.session.query(db.func.sum(Venda.total))
                    .filter_by(cliente_id=cliente.id)
                    .scalar()
                    or 0
                )

                ultima_compra = (
                    Venda.query.filter_by(cliente_id=cliente.id)
                    .order_by(Venda.created_at.desc())
                    .first()
                )

                linha.extend(
                    [
                        str(total_compras),
                        str(total_gasto),
                        ultima_compra.created_at.isoformat() if ultima_compra else "",
                    ]
                )

            csv_data.append(";".join(linha))

        return jsonify(
            {
                "success": True,
                "csv": "\n".join(csv_data),
                "total_clientes": len(clientes),
                "data_exportacao": datetime.utcnow().isoformat(),
                "formato": "CSV (separador: ponto e vírgula)",
                "observacao": "Limite de 1000 registros por exportação",
            }
        )

    except Exception as e:
        print(f"Erro ao exportar clientes: {str(e)}")
        return jsonify({"error": f"Erro ao exportar clientes: {str(e)}"}), 500
