from datetime import datetime
from sqlalchemy import or_, and_
from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import get_jwt_identity, get_jwt

from app import db
from app.decorators.decorator_jwt import funcionario_required
from app.decorators.plan_guards import plan_required
from app.models import Despesa, Funcionario
from app.dashboard_cientifico.data_layer import DataLayer


despesas_bp = Blueprint("despesas", __name__)


@despesas_bp.route("/", methods=["GET"], strict_slashes=False)
@funcionario_required
@plan_required('Enterprise')
def listar_despesas():
    """Lista despesas do estabelecimento do usuário logado com filtros avançados e paginação.

    Query params opcionais:

    **Filtros básicos:**
    - inicio: YYYY-MM-DD (data início)
    - fim: YYYY-MM-DD (data fim)
    - categoria: string
    - tipo: string (fixa/variavel)
    - forma_pagamento: string

    **Filtros avançados:**
    - valor_min: float (valor mínimo)
    - valor_max: float (valor máximo)
    - recorrente: boolean (true/false)
    - descricao: string (busca parcial na descrição)
    - observacoes: string (busca parcial nas observações)

    **Paginação:**
    - pagina: int (padrão: 1)
    - por_pagina: int (padrão: 20, máximo: 100)

    **Ordenação:**
    - ordenar_por: string (data_despesa, valor, categoria, descricao)
    - ordem: string (asc ou desc, padrão: desc)
    """
    from app.utils.query_helpers import get_authorized_establishment_id
    estabelecimento_id = get_authorized_establishment_id()
    if not estabelecimento_id:
        return jsonify({"success": False, "error": "Estabelecimento não identificado"}), 400

    # Query base
    query = Despesa.query
    if estabelecimento_id != 'all':
        query = query.filter(Despesa.estabelecimento_id == estabelecimento_id)

    # ========== FILTRAGEM ==========

    # Filtro por período
    inicio_str = request.args.get("inicio")
    fim_str = request.args.get("fim")

    try:
        if inicio_str:
            inicio = datetime.strptime(inicio_str, "%Y-%m-%d").date()
            query = query.filter(Despesa.data_despesa >= inicio)
        if fim_str:
            fim = datetime.strptime(fim_str, "%Y-%m-%d").date()
            query = query.filter(Despesa.data_despesa <= fim)
    except ValueError:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Parâmetros de data inválidos",
                    "message": "Use o formato YYYY-MM-DD em inicio/fim",
                }
            ),
            400,
        )

    # Filtro por categoria (Case-insensitive)
    categoria = request.args.get("categoria")
    if categoria:
        query = query.filter(Despesa.categoria.ilike(categoria))

    # Filtro por tipo
    tipo = request.args.get("tipo")
    if tipo:
        query = query.filter(Despesa.tipo == tipo)

    # Filtro por forma de pagamento
    forma_pagamento = request.args.get("forma_pagamento")
    if forma_pagamento:
        query = query.filter(Despesa.forma_pagamento == forma_pagamento)

    # Filtro por recorrência
    recorrente = request.args.get("recorrente")
    if recorrente is not None:
        if recorrente.lower() in ["true", "1", "yes"]:
            query = query.filter(Despesa.recorrente == True)
        elif recorrente.lower() in ["false", "0", "no"]:
            query = query.filter(Despesa.recorrente == False)

    # Filtro por valor mínimo e máximo
    valor_min = request.args.get("valor_min")
    valor_max = request.args.get("valor_max")

    if valor_min:
        try:
            valor_min_float = float(valor_min)
            query = query.filter(Despesa.valor >= valor_min_float)
        except ValueError:
            return (
                jsonify({"success": False, "error": "valor_min deve ser um número"}),
                400,
            )

    if valor_max:
        try:
            valor_max_float = float(valor_max)
            query = query.filter(Despesa.valor <= valor_max_float)
        except ValueError:
            return (
                jsonify({"success": False, "error": "valor_max deve ser um número"}),
                400,
            )

    # Busca textual (descrição e observações)
    busca = request.args.get("busca")
    if busca:
        busca_like = f"%{busca}%"
        query = query.filter(
            or_(
                Despesa.descricao.ilike(busca_like),
                Despesa.observacoes.ilike(busca_like),
                Despesa.categoria.ilike(busca_like),
            )
        )

    # Busca específica por descrição
    descricao = request.args.get("descricao")
    if descricao:
        query = query.filter(Despesa.descricao.ilike(f"%{descricao}%"))

    # ========== ORDENAÇÃO ==========

    # Parâmetros de ordenação
    ordenar_por = request.args.get("ordenar_por", "data_despesa")
    ordem = request.args.get("ordem", "desc").lower()

    # Mapeamento de campos permitidos para ordenação
    campos_ordenacao = {
        "data_despesa": Despesa.data_despesa,
        "valor": Despesa.valor,
        "categoria": Despesa.categoria,
        "descricao": Despesa.descricao,
        "tipo": Despesa.tipo,
        "created_at": Despesa.created_at,
        "updated_at": Despesa.updated_at,
    }

    # Verificar se o campo de ordenação é válido
    campo_ordenacao = campos_ordenacao.get(ordenar_por)
    if not campo_ordenacao:
        campo_ordenacao = Despesa.data_despesa  # Valor padrão

    # Aplicar ordenação
    if ordem == "asc":
        query = query.order_by(campo_ordenacao.asc())
    else:  # desc é o padrão
        query = query.order_by(campo_ordenacao.desc())

    # Ordenação secundária por ID para consistência
    query = query.order_by(Despesa.id.desc())

    # ========== PAGINAÇÃO ==========

    # Obter parâmetros de paginação
    try:
        pagina = int(request.args.get("pagina", 1))
        por_pagina = int(request.args.get("por_pagina", 20))
    except ValueError:
        return (
            jsonify({"success": False, "error": "Parâmetros de paginação inválidos"}),
            400,
        )

    # Limitar número máximo de itens por página
    por_pagina = min(por_pagina, 100)

    # Aplicar paginação
    try:
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

        # Calcular estatísticas para dashboard
        total_despesas = query.count()

        if total_despesas > 0:
            # Calcular soma total das despesas filtradas
            from sqlalchemy import func

            soma_query = db.session.query(func.sum(Despesa.valor))
            if estabelecimento_id != 'all':
                soma_query = soma_query.filter(Despesa.estabelecimento_id == estabelecimento_id)
            soma_despesas = soma_query.scalar() or 0.0

            # Calcular média
            media_despesas = soma_despesas / total_despesas
        else:
            soma_despesas = 0.0
            media_despesas = 0.0

        # Preparar resposta
        resposta = {
            "success": True,
            "data": [d.to_dict() for d in paginacao.items],
            "paginacao": {
                "pagina_atual": paginacao.page,
                "por_pagina": paginacao.per_page,
                "total_itens": paginacao.total,
                "total_paginas": paginacao.pages,
                "tem_proxima": paginacao.has_next,
                "tem_anterior": paginacao.has_prev,
                "proxima_pagina": paginacao.next_num,
                "pagina_anterior": paginacao.prev_num,
            },
            "estatisticas": {
                "total_despesas": total_despesas,
                "soma_total": float(soma_despesas),
                "media_valor": float(media_despesas),
                "pagina_atual_inicio": (pagina - 1) * por_pagina + 1,
                "pagina_atual_fim": min(pagina * por_pagina, paginacao.total),
            },
            "filtros_aplicados": {
                "inicio": inicio_str,
                "fim": fim_str,
                "categoria": categoria,
                "tipo": tipo,
                "forma_pagamento": forma_pagamento,
                "recorrente": recorrente,
                "valor_min": valor_min,
                "valor_max": valor_max,
                "busca": busca,
                "ordenar_por": ordenar_por,
                "ordem": ordem,
            },
        }

        # Adicionar categorias disponíveis para filtro
        categorias = (
            db.session.query(Despesa.categoria)
            .filter(Despesa.estabelecimento_id == estabelecimento_id)
            .distinct()
            .all()
        )

        resposta["filtros_disponiveis"] = {
            "categorias": [c[0] for c in categorias if c[0]],
            "tipos": ["fixa", "variavel"],
            "formas_pagamento": [
                fp[0] for fp in (
                    db.session.query(Despesa.forma_pagamento)
                    .filter(Despesa.forma_pagamento.isnot(None))
                    .filter(Despesa.estabelecimento_id == estabelecimento_id if estabelecimento_id != 'all' else True)
                    .distinct()
                    .all()
                )
                if fp[0]
            ],
        }

        return jsonify(resposta), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao listar despesas: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao processar a requisição",
                    "message": str(e),
                }
            ),
            500,
        )


@despesas_bp.route("/estatisticas", methods=["GET"], strict_slashes=False)
@despesas_bp.route("/estatisticas/", methods=["GET"], strict_slashes=False)
@funcionario_required
@plan_required('Enterprise')
def obter_estatisticas_despesas():
    """Obtém estatísticas de despesas para o dashboard, com suporte a filtros de data."""
    from app.utils.query_helpers import get_authorized_establishment_id
    estabelecimento_id = get_authorized_establishment_id()
    if not estabelecimento_id:
        return jsonify({"success": False, "error": "Estabelecimento não identificado"}), 400

    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        from decimal import Decimal, ROUND_HALF_UP

        hoje = datetime.now().date()
        mes_atual_inicio = hoje.replace(day=1)
        mes_anterior_inicio = (mes_atual_inicio - timedelta(days=1)).replace(day=1)
        mes_anterior_fim = mes_atual_inicio - timedelta(days=1)

        # ── Período customizado via query params ─────────────────────────────
        inicio_str = request.args.get("inicio")
        fim_str = request.args.get("fim")
        try:
            filtro_inicio = datetime.strptime(inicio_str, "%Y-%m-%d").date() if inicio_str else None
            filtro_fim = datetime.strptime(fim_str, "%Y-%m-%d").date() if fim_str else None
        except ValueError:
            filtro_inicio = None
            filtro_fim = None

        cat_inicio = filtro_inicio if filtro_inicio else (hoje - timedelta(days=30))
        cat_fim = filtro_fim if filtro_fim else hoje

        # ── Totais gerais (todos os registros do estabelecimento) ─────────────
        query_total = Despesa.query
        if estabelecimento_id != 'all':
            query_total = query_total.filter(Despesa.estabelecimento_id == estabelecimento_id)
        total_despesas = query_total.count()

        # CRITICAL FIX: convert to Decimal immediately, before any arithmetic
        query_soma = db.session.query(func.sum(Despesa.valor))
        if estabelecimento_id != 'all':
             query_soma = query_soma.filter(Despesa.estabelecimento_id == estabelecimento_id)
             
        soma_total = Decimal(str(query_soma.scalar() or 0))

        query_atual = db.session.query(func.sum(Despesa.valor)).filter(
                Despesa.data_despesa >= mes_atual_inicio,
                Despesa.data_despesa <= hoje,
            )
        if estabelecimento_id != 'all':
            query_atual = query_atual.filter(Despesa.estabelecimento_id == estabelecimento_id)
        despesas_mes_atual = Decimal(str(query_atual.scalar() or 0))

        query_anterior = db.session.query(func.sum(Despesa.valor)).filter(
                Despesa.data_despesa >= mes_anterior_inicio,
                Despesa.data_despesa <= mes_anterior_fim,
            )
        if estabelecimento_id != 'all':
            query_anterior = query_anterior.filter(Despesa.estabelecimento_id == estabelecimento_id)
        despesas_mes_anterior = Decimal(str(query_anterior.scalar() or 0))

        # ── Variação — todos os operandos já são Decimal ─────────────────────
        if despesas_mes_anterior > 0:
            variacao_percentual = (
                (despesas_mes_atual - despesas_mes_anterior) / despesas_mes_anterior
            ) * Decimal('100')
        else:
            variacao_percentual = Decimal('100') if despesas_mes_atual > 0 else Decimal('0')

        # ── Hoje / ontem / semana (métricas de curto prazo) ──────────────────
        ontem = hoje - timedelta(days=1)
        semana_inicio = hoje - timedelta(days=6)

        query_hoje = db.session.query(func.sum(Despesa.valor)).filter(Despesa.data_despesa == hoje)
        if estabelecimento_id != 'all':
            query_hoje = query_hoje.filter(Despesa.estabelecimento_id == estabelecimento_id)
        despesas_hoje = Decimal(str(query_hoje.scalar() or 0))

        query_ontem = db.session.query(func.sum(Despesa.valor)).filter(Despesa.data_despesa == ontem)
        if estabelecimento_id != 'all':
             query_ontem = query_ontem.filter(Despesa.estabelecimento_id == estabelecimento_id)
        despesas_ontem = Decimal(str(query_ontem.scalar() or 0))

        query_semana = db.session.query(func.sum(Despesa.valor)).filter(
                Despesa.data_despesa >= semana_inicio,
                Despesa.data_despesa <= hoje,
            )
        if estabelecimento_id != 'all':
            query_semana = query_semana.filter(Despesa.estabelecimento_id == estabelecimento_id)
        despesas_semana = Decimal(str(query_semana.scalar() or 0))

        # ── Período filtrado: total e por categoria ───────────────────────────
        query_periodo = db.session.query(func.sum(Despesa.valor)).filter(
                Despesa.data_despesa >= cat_inicio,
                Despesa.data_despesa <= cat_fim,
            )
        if estabelecimento_id != 'all':
             query_periodo = query_periodo.filter(Despesa.estabelecimento_id == estabelecimento_id)
        soma_periodo = Decimal(str(query_periodo.scalar() or 0))

        query_cats = db.session.query(
                Despesa.categoria,
                func.sum(Despesa.valor).label("total"),
                func.count(Despesa.id).label("quantidade"),
            ).filter(
                Despesa.data_despesa >= cat_inicio,
                Despesa.data_despesa <= cat_fim,
            )
        if estabelecimento_id != 'all':
            query_cats = query_cats.filter(Despesa.estabelecimento_id == estabelecimento_id)
        despesas_por_categoria_raw = query_cats.group_by(Despesa.categoria).order_by(func.sum(Despesa.valor).desc()).all()

        # ── Recorrentes ───────────────────────────────────────────────────────
        query_rec = db.session.query(func.sum(Despesa.valor)).filter(Despesa.recorrente == True)
        if estabelecimento_id != 'all':
             query_rec = query_rec.filter(Despesa.estabelecimento_id == estabelecimento_id)
        despesas_recorrentes = Decimal(str(query_rec.scalar() or 0))

        # ── Evolução mensal (últimos 6 meses) ─────────────────────────────────
        evolucao_mensal = []
        for i in range(6):
            mes_data = hoje.replace(day=1)
            for _ in range(i):
                if mes_data.month == 1:
                    mes_data = mes_data.replace(year=mes_data.year - 1, month=12)
                else:
                    mes_data = mes_data.replace(month=mes_data.month - 1)

            if mes_data.month == 12:
                mes_fim = mes_data.replace(year=mes_data.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                mes_fim = mes_data.replace(month=mes_data.month + 1, day=1) - timedelta(days=1)

            try:
                query_mes = db.session.query(func.sum(Despesa.valor)).filter(
                        Despesa.data_despesa >= mes_data,
                        Despesa.data_despesa <= mes_fim,
                    )
                if estabelecimento_id != 'all':
                     query_mes = query_mes.filter(Despesa.estabelecimento_id == estabelecimento_id)
                total_mes = Decimal(str(query_mes.scalar() or 0))
            except Exception as e_inner:
                current_app.logger.error(f"Erro ao calcular mês {mes_data}: {e_inner}")
                total_mes = Decimal('0')

            evolucao_mensal.append({
                "mes": mes_data.strftime("%Y-%m"),
                "total": float(total_mes),
                "mes_nome": mes_data.strftime("%b/%Y"),
            })

        evolucao_mensal.reverse()

        # ── Médias ────────────────────────────────────────────────────────────
        media_valor = soma_total / Decimal(str(total_despesas)) if total_despesas > 0 else Decimal('0')

        # ── Montar lista de categorias com percentual ─────────────────────────
        despesas_por_categoria_list = []
        for categoria, total, quantidade in despesas_por_categoria_raw:
            total_d = Decimal(str(total)) if total else Decimal('0')
            percentual = (
                (total_d / soma_periodo * Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                if soma_periodo > 0 else Decimal('0')
            )
            despesas_por_categoria_list.append({
                "categoria": categoria or "Sem categoria",
                "total": float(total_d),
                "quantidade": quantidade or 0,
                "percentual": float(percentual),
            })

        return (
            jsonify({
                "success": True,
                "periodo": {
                    "inicio": cat_inicio.isoformat(),
                    "fim": cat_fim.isoformat(),
                },
                "estatisticas": {
                    "total_despesas": total_despesas,
                    "soma_total": float(soma_total),
                    "soma_periodo": float(soma_periodo),
                    "media_valor": float(media_valor),
                    "despesas_hoje": float(despesas_hoje),
                    "despesas_ontem": float(despesas_ontem),
                    "despesas_semana": float(despesas_semana),
                    "despesas_mes_atual": float(despesas_mes_atual),
                    "despesas_mes_anterior": float(despesas_mes_anterior),
                    "variacao_percentual": float(
                        variacao_percentual.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    ),
                    "despesas_recorrentes": float(despesas_recorrentes),
                    "despesas_nao_recorrentes": float(soma_total - despesas_recorrentes),
                    "despesas_por_categoria": despesas_por_categoria_list,
                    "evolucao_mensal": evolucao_mensal,
                },
            }),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao obter estatísticas: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return (
            jsonify({
                "success": False,
                "error": "Erro ao obter estatísticas",
                "message": str(e),
            }),
            500,
        )


# Os endpoints POST, PUT e DELETE permanecem os mesmos
@despesas_bp.route("/", methods=["POST"], strict_slashes=False)
@funcionario_required
@plan_required('Enterprise')
def criar_despesa():
    """Cria uma despesa para o estabelecimento do usuário logado."""
    current_user_id = get_jwt_identity()
    funcionario = Funcionario.query.get(current_user_id)

    if not funcionario:
        return jsonify({"success": False, "error": "Usuário não encontrado"}), 404

    data = request.get_json() or {}

    descricao = (data.get("descricao") or "").strip()
    valor = data.get("valor")

    if not descricao:
        return jsonify({"success": False, "error": "Descrição é obrigatória"}), 400

    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Valor inválido"}), 400

    if valor < 0:
        return jsonify({"success": False, "error": "Valor não pode ser negativo"}), 400

    def _parse_date_field(raw):
        """Parse YYYY-MM-DD string to date, or return None."""
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return None

    data_despesa_date = _parse_date_field(data.get("data_despesa")) or datetime.now().date()
    data_emissao_date = _parse_date_field(data.get("data_emissao"))
    data_vencimento_date = _parse_date_field(data.get("data_vencimento"))

    despesa = Despesa(
        estabelecimento_id=funcionario.estabelecimento_id,
        descricao=descricao,
        categoria=(data.get("categoria") or "geral").strip() or "geral",
        tipo=(data.get("tipo") or "variavel").strip() or "variavel",
        valor=valor,
        data_despesa=data_despesa_date,
        data_emissao=data_emissao_date,
        data_vencimento=data_vencimento_date,
        forma_pagamento=(data.get("forma_pagamento") or "").strip() or None,
        recorrente=bool(data.get("recorrente", False)),
        observacoes=(data.get("observacoes") or "").strip() or None,
    )

    db.session.add(despesa)
    db.session.commit()

    return jsonify({"success": True, "data": despesa.to_dict()}), 201


@despesas_bp.route("/<int:despesa_id>", methods=["PUT"], strict_slashes=False)
@funcionario_required
@plan_required('Enterprise')
def atualizar_despesa(despesa_id: int):
    """Atualiza uma despesa (somente do próprio estabelecimento)."""
    current_user_id = get_jwt_identity()
    funcionario = Funcionario.query.get(current_user_id)

    if not funcionario:
        return jsonify({"success": False, "error": "Usuário não encontrado"}), 404

    despesa = Despesa.query.get(despesa_id)
    if not despesa or despesa.estabelecimento_id != funcionario.estabelecimento_id:
        return jsonify({"success": False, "error": "Despesa não encontrada"}), 404

    data = request.get_json() or {}

    if "descricao" in data:
        descricao = (data.get("descricao") or "").strip()
        if not descricao:
            return jsonify({"success": False, "error": "Descrição é obrigatória"}), 400
        despesa.descricao = descricao

    if "categoria" in data:
        despesa.categoria = (data.get("categoria") or "geral").strip() or "geral"

    if "tipo" in data:
        despesa.tipo = (data.get("tipo") or "variavel").strip() or "variavel"

    if "valor" in data:
        try:
            valor = float(data.get("valor"))
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Valor inválido"}), 400
        if valor < 0:
            return (
                jsonify({"success": False, "error": "Valor não pode ser negativo"}),
                400,
            )
        despesa.valor = valor

    def _parse_date(raw):
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return None

    if "data_despesa" in data:
        despesa.data_despesa = _parse_date(data["data_despesa"]) or despesa.data_despesa
    if "data_emissao" in data:
        despesa.data_emissao = _parse_date(data["data_emissao"])
    if "data_vencimento" in data:
        despesa.data_vencimento = _parse_date(data["data_vencimento"])



    if "forma_pagamento" in data:
        fp = (data.get("forma_pagamento") or "").strip()
        despesa.forma_pagamento = fp or None

    if "recorrente" in data:
        despesa.recorrente = bool(data.get("recorrente"))

    if "observacoes" in data:
        obs = (data.get("observacoes") or "").strip()
        despesa.observacoes = obs or None

    db.session.commit()

    return jsonify({"success": True, "data": despesa.to_dict()}), 200


@despesas_bp.route("/<int:despesa_id>", methods=["DELETE"], strict_slashes=False)
@funcionario_required
@plan_required('Enterprise')
def deletar_despesa(despesa_id: int):
    """Remove uma despesa (somente do próprio estabelecimento)."""
    current_user_id = get_jwt_identity()
    funcionario = Funcionario.query.get(current_user_id)

    if not funcionario:
        return jsonify({"success": False, "error": "Usuário não encontrado"}), 404

    despesa = Despesa.query.get(despesa_id)
    if not despesa or despesa.estabelecimento_id != funcionario.estabelecimento_id:
        return jsonify({"success": False, "error": "Despesa não encontrada"}), 404

    db.session.delete(despesa)
    db.session.commit()

    return jsonify({"success": True}), 200
@despesas_bp.route("/boletos-a-vencer/", methods=["GET"])
@funcionario_required
@plan_required('Enterprise')
def boletos_a_vencer():
    """Lista boletos de fornecedores que estão próximos ao vencimento"""
    try:
        from app.models import ContaPagar, Fornecedor
        from datetime import date, timedelta
        
        from app.utils.query_helpers import get_authorized_establishment_id
        estabelecimento_id = get_authorized_establishment_id()
        if not estabelecimento_id:
            return jsonify({"error": "Estabelecimento não identificado"}), 400
        
        # Parâmetros
        dias_antecedencia = int(request.args.get('dias', 30))  # Próximos 30 dias por padrão
        apenas_vencidos = request.args.get('apenas_vencidos') == 'true'
        
        # Query base
        query = db.session.query(ContaPagar).join(Fornecedor).filter(ContaPagar.status == 'aberto')
        if estabelecimento_id != 'all':
             query = query.filter(ContaPagar.estabelecimento_id == estabelecimento_id)
        
        if apenas_vencidos:
            # Apenas boletos já vencidos
            query = query.filter(ContaPagar.data_vencimento < date.today())
        else:
            # Boletos que vencem nos próximos X dias
            data_limite = date.today() + timedelta(days=dias_antecedencia)
            query = query.filter(ContaPagar.data_vencimento <= data_limite)
        
        boletos = query.order_by(ContaPagar.data_vencimento.asc()).all()
        
        # Processar resultados
        boletos_data = []
        total_valor = Decimal('0')
        
        for boleto in boletos:
            dias_vencimento = (boleto.data_vencimento - date.today()).days

            # Determinar origem: mercadoria (pedido de compra) ou despesa fixa
            tem_pedido = boleto.pedido_compra_id is not None and getattr(boleto, 'pedido_compra', None) is not None
            if tem_pedido:
                origem = "mercadoria"
                descricao = f"Pedido {boleto.pedido_compra.numero_pedido}"
            else:
                origem = "despesa"
                descricao = boleto.observacoes or "Despesa" # tipo_documento was removed from ContaPagar

            status_vencimento = 'normal'
            if dias_vencimento < 0:
                 status_vencimento = 'vencido'
            elif dias_vencimento == 0:
                 status_vencimento = 'vence_hoje'
            elif dias_vencimento <= 7:
                 status_vencimento = 'vence_em_breve'

            boleto_info = {
                'id': boleto.id,
                'numero_documento': boleto.numero_documento,
                'tipo_documento': 'boleto', # fallback since tipo_documento doesn't exist
                'origem': origem,
                'descricao': descricao,
                'fornecedor_nome': boleto.fornecedor.nome_fantasia if boleto.fornecedor else 'N/A',
                'fornecedor_id': boleto.fornecedor_id,
                'valor_original': float(boleto.valor_original),
                'valor_atual': float(boleto.valor_atual),
                'data_emissao': boleto.data_emissao.isoformat() if boleto.data_emissao else None,
                'data_vencimento': boleto.data_vencimento.isoformat() if boleto.data_vencimento else None,
                'dias_vencimento': dias_vencimento,
                'status_vencimento': status_vencimento,
                'pedido_numero': boleto.pedido_compra.numero_pedido if tem_pedido else None,
                'pedido_id': boleto.pedido_compra_id if tem_pedido else None,
                'data_pedido': boleto.pedido_compra.data_pedido.isoformat() if tem_pedido and boleto.pedido_compra.data_pedido else None,
                'itens': [item.to_dict() for item in boleto.pedido_compra.itens] if tem_pedido and hasattr(boleto.pedido_compra, 'itens') else [],
                'observacoes': boleto.observacoes
            }
            
            boletos_data.append(boleto_info)
            total_valor += boleto.valor_atual
        
        # Estatísticas
        vencidos = [b for b in boletos_data if b['dias_vencimento'] < 0]
        vence_hoje = [b for b in boletos_data if b['dias_vencimento'] == 0]
        vence_7_dias = [b for b in boletos_data if 0 < b['dias_vencimento'] <= 7]
        
        return jsonify({
            'boletos': boletos_data,
            'resumo': {
                'total_boletos': len(boletos_data),
                'total_valor': float(total_valor),
                'vencidos': len(vencidos),
                'vence_hoje': len(vence_hoje),
                'vence_7_dias': len(vence_7_dias),
                'valor_vencidos': float(sum(Decimal(str(b['valor_atual'])) for b in vencidos)),
                'valor_vence_hoje': float(sum(Decimal(str(b['valor_atual'])) for b in vence_hoje)),
                'valor_vence_7_dias': float(sum(Decimal(str(b['valor_atual'])) for b in vence_7_dias))
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar boletos a vencer: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@despesas_bp.route("/resumo-financeiro/", methods=["GET"], strict_slashes=False)
@funcionario_required
@plan_required('Enterprise')
def resumo_financeiro():
    """
    Resumo financeiro consolidado otimizado para Vercel.
    Retorna visão de DRE e Fluxo de Caixa Real.
    """
    try:
        from app.dashboard_cientifico.data_layer import DataLayer
        from datetime import date, timedelta, datetime

        from app.utils.query_helpers import get_authorized_establishment_id
        estabelecimento_id = get_authorized_establishment_id()
        if not estabelecimento_id:
            return jsonify({"error": "Estabelecimento não identificado"}), 400

        hoje = date.today()
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')

        if data_inicio_str and data_fim_str:
            try:
                dt_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
                dt_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
            except ValueError:
                dt_inicio = hoje.replace(day=1)
                dt_fim = hoje
        else:
            dt_inicio = hoje.replace(day=1)
            dt_fim = hoje

        # 🚀 CONSOLIDAÇÃO PROFISSIONAL: Reduz de 12 para 3 queries principais
        financial_data = DataLayer.get_consolidated_financial_summary(estabelecimento_id, dt_inicio, dt_fim)
        
        if not financial_data:
             return jsonify({"error": "Falha ao consolidar dados financeiros"}), 500

        cp = financial_data['contas_pagar']
        vendas = financial_data['vendas']
        desp = financial_data['despesas']
        caixa_pdv = financial_data.get('caixa_pdv', {'sangrias': 0.0, 'suprimentos': 0.0})
        
        # --- Lógica Exata para Mercadinho ---
        receita_bruta = vendas.get("revenue", 0.0)
        total_pagar_aberto = cp['total_aberto']
        
        # 1. Índice de Comprometimento (Dívida total vs Faturamento do período)
        indice_comprometimento = (total_pagar_aberto / receita_bruta * 100) if receita_bruta > 0 else 0
        
        # 2. Pressão de Caixa Diária (Vence Hoje vs Média de Venda Diária)
        dias_periodo = (dt_fim - dt_inicio).days + 1
        venda_media_diaria = receita_bruta / dias_periodo if dias_periodo > 0 else 0
        pressao_caixa = (cp['vence_hoje_valor'] / venda_media_diaria * 100) if venda_media_diaria > 0 else 0

        # Alertas simplificados e precisos (Foco em Saídas)
        alertas = []
        if cp['qtd_vencidos'] > 0:
            alertas.append({
                "tipo": "boleto_vencido",
                "severidade": "critica",
                "titulo": f"{cp['qtd_vencidos']} boleto(s) vencido(s)",
                "descricao": f"Total de R$ {cp['total_vencido']:,.2f} vencidos. Regularize para evitar juros.",
                "acao": "Regularizar pagamento imediatamente",
            })
            
        if indice_comprometimento > 80:
            alertas.append({
                "tipo": "comprometimento_alto",
                "severidade": "alta",
                "titulo": "Comprometimento Crítico",
                "descricao": f"Seus boletos em aberto representam {indice_comprometimento:.1f}% do faturamento deste período.",
                "acao": "Reduzir compras ou renegociar prazos com fornecedores",
            })

        # Fluxo de Caixa Real: inclui receita de vendas + suprimentos de caixa (entradas)
        # e pagamentos de contas + despesas cadastradas + sangrias de caixa (saídas)
        entradas_reais = vendas.get("total_recebido", 0.0) + caixa_pdv['suprimentos']
        saidas_reais = cp['pago_periodo'] + desp['total'] + caixa_pdv['sangrias']

        return jsonify({
            "success": True,
            "periodo": {
                "inicio": dt_inicio.isoformat(),
                "fim": dt_fim.isoformat()
            },
            "dre_consolidado": {
                "receita_bruta": vendas.get("revenue", 0.0),
                "custo_mercadoria": vendas.get("cogs", 0.0),
                "lucro_bruto": vendas.get("gross_profit", 0.0),
                "despesas_operacionais": desp['total'],
                "lucro_liquido": vendas.get("gross_profit", 0.0) - desp['total']
            },
            "indicadores_gestao": {
                "indice_comprometimento": indice_comprometimento,
                "pressao_caixa_diaria": pressao_caixa,
                "venda_media_diaria": venda_media_diaria,
                "vence_hoje_valor": cp['vence_hoje_valor']
            },
            "contas_pagar": {
                "total_aberto": cp['total_aberto'],
                "total_vencido": cp['total_vencido'],
                "vence_hoje": cp['vence_hoje_valor'],
                "vence_7_dias": cp['vence_7d'],
                "vence_30_dias": cp['vence_30d'],
                "pago_no_mes": cp['pago_periodo'],
                "qtd_vencidos": cp['qtd_vencidos'],
                "qtd_vence_hoje": cp['qtd_vence_hoje'],
                "qtd_vence_7d": cp['qtd_vence_7d']
            },
            "despesas_mes": {
                "total": desp['total'],
                "recorrentes": desp['recorrentes'],
                "variaveis": desp['total'] - desp['recorrentes']
            },
            "caixa_pdv": {
                "sangrias": caixa_pdv['sangrias'],
                "suprimentos": caixa_pdv['suprimentos'],
            },
            "fluxo_caixa_real": {
                "entradas": entradas_reais,
                "saidas": saidas_reais,
                "saldo": entradas_reais - saidas_reais,
                "interpretacao": "Positivo" if (entradas_reais - saidas_reais) >= 0 else "Negativo"
            },
            "alertas": alertas,
            "total_alertas": len(alertas),
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar resumo financeiro: {str(e)}")
        return jsonify({"error": "Erro interno do servidor", "message": str(e)}), 500