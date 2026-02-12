from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app import db
from app.models import (
    Venda,
    VendaItem,
    Produto,
    Funcionario,
    MovimentacaoEstoque,
    Cliente,
    Fornecedor,
)
from sqlalchemy import or_, and_, func, extract, cast, String, Date, distinct
import random
import string
from collections import defaultdict

vendas_bp = Blueprint("vendas", __name__)

# ==================== CONSTANTES E FUNÇÕES AUXILIARES ====================

FILTROS_PERMITIDOS_VENDAS = {
    "codigo": lambda value: Venda.codigo.ilike(f"%{value}%"),
    "cliente_nome": lambda value: Cliente.nome.ilike(f"%{value}%"),
    "cliente_cpf": lambda value: Cliente.cpf.ilike(f"%{value}%"),
    "funcionario_nome": lambda value: Funcionario.nome.ilike(f"%{value}%"),
    "forma_pagamento": lambda value: Venda.forma_pagamento.ilike(f"%{value}%"),
    "status": lambda value: Venda.status.ilike(value),
    "observacoes": lambda value: Venda.observacoes.ilike(f"%{value}%"),
}

ORDENACOES_PERMITIDAS = {
    "data": Venda.data_venda,
    "total": Venda.total,
    "codigo": Venda.codigo,
    "cliente_nome": Cliente.nome,
    "funcionario_nome": Funcionario.nome,
    "forma_pagamento": Venda.forma_pagamento,
}


def aplicar_filtros_avancados_vendas(query, filtros, estabelecimento_id=1):
    """Aplica filtros avançados na query de vendas"""

    # Aplicar filtros definidos em FILTROS_PERMITIDOS_VENDAS
    for chave, valor in filtros.items():
        if chave in FILTROS_PERMITIDOS_VENDAS:
            try:
                with open("debug_vendas.txt", "a", encoding="utf-8") as f:
                     f.write(f"DEBUG APPLY: Applying filter {chave}={valor}\n")
            except:
                pass
            query = query.filter(FILTROS_PERMITIDOS_VENDAS[chave](valor))

    # Filtro por data
    for filtro_data in ["data_inicio", "data_fim"]:
        if filtro_data in filtros and filtros[filtro_data]:
            # Log dos filtros recebidos (para debug)
            print(f"Applying filter {filtro_data}: {filtros[filtro_data]}")
            
            try:
                data_str = filtros[filtro_data].strip()
                data_dt = None
                
                # Tentar múltiplos formatos
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]:
                    try:
                        data_dt = datetime.strptime(data_str.split('T')[0] if 'T' in data_str and fmt == "%Y-%m-%d" else data_str, fmt)
                        break
                    except ValueError:
                        continue
                
                # Se falhar, tenta fromisoformat
                if not data_dt:
                    try:
                        data_dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                
                if data_dt:
                    # Usar coalesce para considerar data_venda ou created_at
                    campo_data = func.coalesce(Venda.data_venda, Venda.created_at)
                    
                    if filtro_data == "data_inicio":
                        query = query.filter(campo_data >= data_dt)
                    elif filtro_data == "data_fim":
                        # Adiciona 1 dia para incluir o dia inteiro se for apenas data
                        if len(data_str) <= 10: # Apenas data, sem hora
                            data_fim = data_dt + timedelta(days=1)
                            query = query.filter(campo_data < data_fim)
                        else:
                            query = query.filter(campo_data <= data_dt)
                else:
                    print(f"❌ Failed to parse date: {data_str}")
            except Exception as e:
                print(f"❌ Error applying date filter: {str(e)}")
                pass

    # Filtro por intervalo de total
    if "min_total" in filtros and filtros["min_total"]:
        try:
            query = query.filter(Venda.total >= float(filtros["min_total"]))
        except ValueError:
            pass

    if "max_total" in filtros and filtros["max_total"]:
        try:
            query = query.filter(Venda.total <= float(filtros["max_total"]))
        except ValueError:
            pass

    # Filtro por cliente_id
    if "cliente_id" in filtros and filtros["cliente_id"]:
        try:
            query = query.filter(Venda.cliente_id == int(filtros["cliente_id"]))
        except (ValueError, TypeError):
            pass

    # Filtro por funcionario_id
    if "funcionario_id" in filtros and filtros["funcionario_id"]:
        try:
            query = query.filter(Venda.funcionario_id == int(filtros["funcionario_id"]))
        except (ValueError, TypeError):
            pass

    # Filtro por produto (nos itens da venda)
    if "produto_nome" in filtros and filtros["produto_nome"]:
        query = (
            query.join(VendaItem)
            .join(Produto)
            .filter(
                or_(
                    Produto.nome.ilike(f"%{filtros['produto_nome']}%"),
                    Produto.codigo_barras.ilike(f"%{filtros['produto_nome']}%"),
                )
            )
        )

    # Filtro por valor recebido
    if "min_valor_recebido" in filtros and filtros["min_valor_recebido"]:
        try:
            query = query.filter(
                Venda.valor_recebido >= float(filtros["min_valor_recebido"])
            )
        except ValueError:
            pass

    if "max_valor_recebido" in filtros and filtros["max_valor_recebido"]:
        try:
            query = query.filter(
                Venda.valor_recebido <= float(filtros["max_valor_recebido"])
            )
        except ValueError:
            pass

    # Filtro por tipo específico de vendas
    if "tipo_venda" in filtros and filtros["tipo_venda"]:
        if filtros["tipo_venda"] == "com_cliente":
            query = query.filter(Venda.cliente_id.isnot(None))
        elif filtros["tipo_venda"] == "sem_cliente":
            query = query.filter(Venda.cliente_id.is_(None))
        elif filtros["tipo_venda"] == "com_desconto":
            query = query.filter(Venda.desconto > 0)
        elif filtros["tipo_venda"] == "sem_desconto":
            query = query.filter(Venda.desconto == 0)

    # Filtro por dia da semana
    if "dia_semana" in filtros and filtros["dia_semana"]:
        try:
            from app.utils.query_helpers import get_dow_extract
            dia_num = int(filtros["dia_semana"])
            query = query.filter(get_dow_extract(Venda.data_venda) == dia_num)
        except (ValueError, TypeError):
            pass

    return query


def aplicar_ordenacao_vendas(query, ordenar_por, direcao):
    """Aplica ordenação na query de vendas"""
    if ordenar_por in ORDENACOES_PERMITIDAS:
        campo = ORDENACOES_PERMITIDAS[ordenar_por]
        if direcao.lower() == "desc":
            query = query.order_by(campo.desc())
        else:
            query = query.order_by(campo.asc())
    else:
        # Ordenação padrão
        query = query.order_by(Venda.data_venda.desc())

    return query


def calcular_estatisticas_vendas(query):
    """Calcula estatísticas agregadas das vendas filtradas"""
    estatisticas = {
        "total_vendas": 0,
        "quantidade_vendas": 0,
        "ticket_medio": 0,
        "total_descontos": 0,
        "total_valor_recebido": 0,
        "formas_pagamento": defaultdict(lambda: {"quantidade": 0, "total": 0}),
    }

    vendas = query.all()

    if vendas:
        estatisticas["total_vendas"] = sum(v.total for v in vendas)
        estatisticas["quantidade_vendas"] = len(vendas)
        estatisticas["ticket_medio"] = (
            estatisticas["total_vendas"] / estatisticas["quantidade_vendas"]
            if estatisticas["quantidade_vendas"] > 0
            else 0
        )
        estatisticas["total_descontos"] = sum(v.desconto for v in vendas)
        estatisticas["total_valor_recebido"] = sum(v.valor_recebido for v in vendas)

        # Agrupar por forma de pagamento
        for venda in vendas:
            forma = venda.forma_pagamento
            estatisticas["formas_pagamento"][forma]["quantidade"] += 1
            estatisticas["formas_pagamento"][forma]["total"] += venda.total

    return estatisticas


def gerar_codigo_venda():
    """Gera código único para venda no formato V-YYYYMMDD-XXXX"""
    data_atual = datetime.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.digits, k=4))
    return f"V-{data_atual}-{random_part}"


# ==================== ROTAS COM FILTROS AVANÇADOS ====================


@vendas_bp.route("/", methods=["GET"], strict_slashes=False)
def listar_vendas():
    """Lista vendas com filtros avançados"""
    try:
        with open("debug_vendas.txt", "a", encoding="utf-8") as f:
            f.write(f"DEBUG LISTAR: request.args={request.args}\n")
        
        # Configuração de paginação
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        per_page = min(per_page, 100)  # Limite máximo

        # Configuração de ordenação
        ordenar_por = request.args.get("ordenar_por", "data")
        direcao = request.args.get("direcao", "desc")

        # Iniciar query com joins para otimização
        query = Venda.query.options(
            db.joinedload(Venda.funcionario),
            db.joinedload(Venda.cliente),
            db.joinedload(Venda.itens),
        )

        # Aplicar filtro de busca global (mantido para compatibilidade)
        search = request.args.get("search", "").strip()
        if search:
            query = query.filter(
                or_(
                    Venda.codigo.ilike(f"%{search}%"),
                    Venda.observacoes.ilike(f"%{search}%"),
                    Cliente.nome.ilike(f"%{search}%"),
                    Cliente.cpf.ilike(f"%{search}%"),
                    Funcionario.nome.ilike(f"%{search}%"),
                )
            )

        # Coletar filtros avançados
        filtros_avancados = {}
        for filtro in FILTROS_PERMITIDOS_VENDAS.keys():
            valor = request.args.get(filtro, "").strip()
            if valor:
                filtros_avancados[filtro] = valor

        # Filtros especiais de data e valor
        filtros_especiais = [
            "data_inicio",
            "data_fim",
            "min_total",
            "max_total",
            "min_valor_recebido",
            "max_valor_recebido",
            "cliente_id",
            "funcionario_id",
            "produto_nome",
            "tipo_venda",
            "dia_semana",
        ]

        for filtro_especial in filtros_especiais:
            valor = request.args.get(filtro_especial, "").strip()
            if valor:
                filtros_avancados[filtro_especial] = valor

        with open("debug_vendas.txt", "a", encoding="utf-8") as f:
            f.write(f"DEBUG LISTAR: search='{search}', filtros_avancados={filtros_avancados}\n")

        # Aplicar todos os filtros
        query = aplicar_filtros_avancados_vendas(query, filtros_avancados)

        # Aplicar ordenação
        query = aplicar_ordenacao_vendas(query, ordenar_por, direcao)

        # Executar paginação
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        vendas = pagination.items

        # Calcular estatísticas para o conjunto filtrado
        estatisticas = calcular_estatisticas_vendas(query)

        # Construir resposta
        resultado = []
        for v in vendas:
            resultado.append(
                {
                    "id": v.id,
                    "codigo": v.codigo,
                    "cliente": (
                        {
                            "id": v.cliente_id,
                            "nome": v.cliente.nome if v.cliente else "Consumidor Final",
                            "telefone": v.cliente.telefone if v.cliente else None,
                            "cpf": v.cliente.cpf if v.cliente else None,
                        }
                        if v.cliente_id
                        else {"nome": "Consumidor Final"}
                    ),
                    "funcionario": {
                        "id": v.funcionario_id,
                        "nome": (
                            v.funcionario.nome if v.funcionario else "Não Informado"
                        ),
                        "email": v.funcionario.email if v.funcionario else None,
                    },
                    "subtotal": float(v.subtotal),
                    "desconto": float(v.desconto),
                    "total": float(v.total),
                    "forma_pagamento": v.forma_pagamento,
                    "valor_recebido": float(v.valor_recebido),
                    "troco": float(v.troco),
                    "status": v.status,
                    "data_venda": v.data_venda.isoformat() if v.data_venda else v.created_at.isoformat(),
                    "data": v.data_venda.isoformat() if v.data_venda else v.created_at.isoformat(),
                    "data_formatada": (v.data_venda if v.data_venda else v.created_at).strftime("%d/%m/%Y %H:%M"),
                    "quantidade_itens": len(v.itens),
                    "observacoes": v.observacoes or "",
                    "detalhes_url": f"/api/vendas/{v.id}",
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

        # Metadados dos filtros aplicados
        if filtros_avancados:
            metadados["filtros_aplicados"] = filtros_avancados
        if search:
            metadados["busca_global"] = search

        metadados["ordenacao"] = {"campo": ordenar_por, "direcao": direcao}

        # Adicionar estatísticas à resposta
        metadados["estatisticas"] = {
            "total_vendas": float(estatisticas["total_vendas"]),
            "quantidade_vendas": estatisticas["quantidade_vendas"],
            "ticket_medio": float(estatisticas["ticket_medio"]),
            "total_descontos": float(estatisticas["total_descontos"]),
            "total_valor_recebido": float(estatisticas["total_valor_recebido"]),
            "formas_pagamento": dict(estatisticas["formas_pagamento"]),
        }

        return jsonify(
            {
                "vendas": resultado,
                "paginacao": metadados,
                "filtros_disponiveis": list(FILTROS_PERMITIDOS_VENDAS.keys())
                + filtros_especiais,
                "ordenacoes_disponiveis": list(ORDENACOES_PERMITIDAS.keys()),
            }
        )

    except Exception as e:
        print(f"❌ Erro ao listar vendas: {str(e)}")
        return jsonify({"error": f"Erro ao listar vendas: {str(e)}"}), 500


@vendas_bp.route("/estatisticas", methods=["GET"], strict_slashes=False)
def estatisticas_vendas():
    """Estatísticas gerais de vendas com filtros avançados"""
    try:
        with open("debug_vendas.txt", "a", encoding="utf-8") as f:
            f.write(f"DEBUG ESTATISTICAS: args={request.args}\n")
            
        # Coletar filtros
        filtros = {k: v for k, v in request.args.items() if v}
        
        # 1. Query Base (Com todos os filtros aplicados)
        query_base = Venda.query
        
        # REMOVIDO: Filtro padrão de "finalizada". Agora mostra tudo se não especificado.
        # if "status" not in filtros:
        #    query_base = query_base.filter(Venda.status == "finalizada")
            
        # Aplicar todos os filtros (datas, cliente, func, pgto, valor, etc.)
        query_base = aplicar_filtros_avancados_vendas(query_base, filtros)

        # Clonar queries para diferentes agregações
        # (SQLAlchemy é preguiçoso, então isso só constrói a query, não executa ainda)
        
        # --- ESTATÍSTICAS GERAIS ---
        total_vendas = query_base.count()
        
        total_valor = (
            db.session.query(func.sum(Venda.total))
            .filter(Venda.id.in_(query_base.with_entities(Venda.id)))
            .scalar()
            or 0
        )
        
        # Calcular Lucro Total (Baseado na margem real dos itens)
        total_lucro = (
            db.session.query(func.sum(VendaItem.margem_lucro_real))
            .join(Venda, Venda.id == VendaItem.venda_id)
            .filter(Venda.id.in_(query_base.with_entities(Venda.id)))
            .scalar()
            or 0
        )

        ticket_medio = total_valor / total_vendas if total_vendas > 0 else 0

        # --- VENDAS POR DIA (Gráfico Principal) ---
        # Usamos coalesce para garantir uma data válida
        campo_data = func.coalesce(Venda.data_venda, Venda.created_at)
        campo_data_dia = func.date(campo_data)
        
        vendas_por_dia = (
            db.session.query(
                campo_data_dia.label("data"),
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .filter(Venda.id.in_(query_base.with_entities(Venda.id)))
            .group_by(campo_data_dia)
            .order_by(campo_data_dia.asc())
            .all()
        )
        
        # ==================== PREVISÃO DE VENDAS (7 DIAS) ====================
        previsao_vendas = []
        if len(vendas_por_dia) >= 7:
            valores_y = [float(vpd.total) if vpd.total else 0 for vpd in vendas_por_dia]
            n = len(valores_y)
            valores_x = list(range(n))
            
            media_x = sum(valores_x) / n
            media_y = sum(valores_y) / n
            
            numerador = sum((valores_x[i] - media_x) * (valores_y[i] - media_y) for i in range(n))
            denominador = sum((valores_x[i] - media_x) ** 2 for i in range(n))
            
            if denominador != 0:
                b = numerador / denominador
                a = media_y - b * media_x
                
                ultima_data_str = str(vendas_por_dia[-1].data)
                ultima_data = datetime.strptime(ultima_data_str, '%Y-%m-%d').date()
                
                for i in range(1, 8):
                    proxima_data = ultima_data + timedelta(days=i)
                    x_futuro = n + i - 1
                    valor_previsto = max(0, a + b * x_futuro)
                    
                    previsao_vendas.append({
                        "data": proxima_data.isoformat(),
                        "total": round(valor_previsto, 2),
                        "tipo": "previsao"
                    })
        
        vendas_historicas = [
            {
                "data": str(vpd.data),
                "quantidade": vpd.quantidade,
                "total": float(vpd.total) if vpd.total else 0,
                "tipo": "historico"
            }
            for vpd in vendas_por_dia
        ]

        # --- FORMAS DE PAGAMENTO ---
        formas_pagamento = (
            db.session.query(
                Venda.forma_pagamento,
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .filter(Venda.id.in_(query_base.with_entities(Venda.id)))
            .group_by(Venda.forma_pagamento)
            .all()
        )

        # --- TOP FUNCIONÁRIOS ---
        vendas_por_funcionario = (
            db.session.query(
                Funcionario.nome,
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .join(Venda, Venda.funcionario_id == Funcionario.id)
            .filter(Venda.id.in_(query_base.with_entities(Venda.id)))
            .group_by(Funcionario.id, Funcionario.nome)
            .order_by(func.sum(Venda.total).desc())
            .limit(10)
            .all()
        )

        # --- TOP CLIENTES ---
        vendas_por_cliente = (
            db.session.query(
                Cliente.nome,
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .filter(Venda.id.in_(query_base.with_entities(Venda.id)))
            .group_by(Cliente.id, Cliente.nome)
            .order_by(func.sum(Venda.total).desc())
            .limit(10)
            .all()
        )

        # --- VENDAS POR HORA ---
        from app.utils.query_helpers import get_hour_extract
        # Usar coalescencia também para hora
        campo_hora = get_hour_extract(func.coalesce(Venda.data_venda, Venda.created_at))
        
        vendas_por_hora = (
            db.session.query(
                campo_hora.label("hora"),
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .filter(Venda.id.in_(query_base.with_entities(Venda.id)))
            .group_by(campo_hora)
            .order_by("hora")
            .all()
        )

        # --- PRODUTOS MAIS VENDIDOS ---
        # Note: This involves joining VendaItem, need to be careful with filtering
        produtos_mais_vendidos = (
            db.session.query(
                Produto.nome,
                Produto.fornecedor_id,
                Fornecedor.nome_fantasia.label("fornecedor_nome"),
                func.sum(VendaItem.quantidade).label("quantidade"),
                func.sum(VendaItem.total_item).label("total"),
            )
            .join(VendaItem, VendaItem.produto_id == Produto.id)
            .join(Venda, Venda.id == VendaItem.venda_id)
            .outerjoin(Fornecedor, Fornecedor.id == Produto.fornecedor_id)
            .filter(Venda.id.in_(query_base.with_entities(Venda.id)))
            .group_by(Produto.id, Produto.nome, Produto.fornecedor_id, Fornecedor.nome_fantasia)
            .order_by(func.sum(VendaItem.quantidade).desc())
            .limit(10)
            .all()
        )

        # --- FORNECEDORES (Baseado em produtos vendidos) ---
        vendas_por_fornecedor = (
            db.session.query(
                Fornecedor.nome_fantasia,
                func.count(distinct(Venda.id)).label("quantidade_vendas"),
                func.sum(VendaItem.total_item).label("total"),
            )
            .join(Produto, Produto.fornecedor_id == Fornecedor.id)
            .join(VendaItem, VendaItem.produto_id == Produto.id)
            .join(Venda, Venda.id == VendaItem.venda_id)
            .filter(Venda.id.in_(query_base.with_entities(Venda.id)))
            .group_by(Fornecedor.id, Fornecedor.nome_fantasia)
            .order_by(func.sum(VendaItem.total_item).desc())
            .limit(10)
            .all()
        )

        return (
            jsonify(
                {
                    "estatisticas_gerais": {
                        "total_vendas": total_vendas,
                        "total_valor": float(total_valor),
                        "total_lucro": float(total_lucro),
                        "ticket_medio": float(ticket_medio),
                        "periodo": {
                            "data_inicio": data_inicio,
                            "data_fim": data_fim,
                        },
                    },
                    "vendas_por_dia": vendas_historicas,
                    "previsao_vendas": previsao_vendas,
                    "formas_pagamento": [
                        {
                            "forma": fp.forma_pagamento,
                            "quantidade": fp.quantidade,
                            "total": float(fp.total) if fp.total else 0,
                            "percentual": float(
                                (fp.total / total_valor * 100) if total_valor > 0 else 0
                            ),
                        }
                        for fp in formas_pagamento
                    ],
                    "vendas_por_funcionario": [
                        {
                            "funcionario": vpf.nome,
                            "quantidade": vpf.quantidade,
                            "total": float(vpf.total) if vpf.total else 0,
                        }
                        for vpf in vendas_por_funcionario
                    ],
                    "vendas_por_cliente": [
                        {
                            "cliente": vpc.nome,
                            "quantidade": vpc.quantidade,
                            "total": float(vpc.total) if vpc.total else 0,
                        }
                        for vpc in vendas_por_cliente
                    ],
                    "vendas_por_hora": [
                        {
                            "hora": int(vph.hora),
                            "quantidade": vph.quantidade,
                            "total": float(vph.total) if vph.total else 0,
                        }
                        for vph in vendas_por_hora
                    ],
                    "produtos_mais_vendidos": [
                        {
                            "nome": pmv.nome,
                            "fornecedor": pmv.fornecedor_nome or "Sem Fornecedor",
                            "quantidade": pmv.quantidade,
                            "total": float(pmv.total) if pmv.total else 0,
                        }
                        for pmv in produtos_mais_vendidos
                    ],
                    "vendas_por_fornecedor": [
                        {
                            "fornecedor": vpf.nome_fantasia,
                            "quantidade_vendas": vpf.quantidade_vendas,
                            "total": float(vpf.total) if vpf.total else 0,
                        }
                        for vpf in vendas_por_fornecedor
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {str(e)}")
        return jsonify({"error": f"Erro ao obter estatísticas: {str(e)}"}), 500


@vendas_bp.route("/relatorio-diario", methods=["GET"], strict_slashes=False)
def relatorio_diario():
    """Relatório diário detalhado de vendas"""
    try:
        # Parâmetros
        data_relatorio = request.args.get("data", datetime.now().strftime("%Y-%m-%d"))
        formato = request.args.get("formato", "json")

        try:
            data_dt = datetime.strptime(data_relatorio, "%Y-%m-%d")
        except ValueError:
            data_dt = datetime.now()

        inicio_dia = datetime.combine(data_dt.date(), datetime.min.time())
        fim_dia = datetime.combine(data_dt.date(), datetime.max.time())

        # Buscar vendas do dia
        vendas = (
            Venda.query.filter(
                Venda.created_at >= inicio_dia,
                Venda.created_at <= fim_dia,
                Venda.status == "finalizada",
            )
            .options(
                db.joinedload(Venda.itens),
                db.joinedload(Venda.funcionario),
                db.joinedload(Venda.cliente),
            )
            .order_by(Venda.created_at.desc())
            .all()
        )

        # Calcular estatísticas
        total_vendas = sum(v.total for v in vendas)
        total_descontos = sum(v.desconto for v in vendas)
        quantidade_vendas = len(vendas)
        ticket_medio = total_vendas / quantidade_vendas if quantidade_vendas > 0 else 0

        # Agrupar por forma de pagamento
        formas_pagamento = defaultdict(lambda: {"quantidade": 0, "total": 0})
        for v in vendas:
            forma = v.forma_pagamento
            formas_pagamento[forma]["quantidade"] += 1
            formas_pagamento[forma]["total"] += v.total

        # Agrupar por funcionário
        funcionarios = defaultdict(lambda: {"quantidade": 0, "total": 0, "nome": ""})
        for v in vendas:
            if v.funcionario:
                func_id = v.funcionario.id
                funcionarios[func_id]["quantidade"] += 1
                funcionarios[func_id]["total"] += v.total
                funcionarios[func_id]["nome"] = v.funcionario.nome

        # Produtos mais vendidos no dia
        produtos_dia = defaultdict(lambda: {"quantidade": 0, "total": 0, "nome": ""})
        for v in vendas:
            for item in v.itens:
                produtos_dia[item.produto_id]["quantidade"] += item.quantidade
                produtos_dia[item.produto_id]["total"] += item.total_item
                produtos_dia[item.produto_id]["nome"] = item.produto_nome

        # Vendas por hora
        vendas_por_hora = defaultdict(lambda: {"quantidade": 0, "total": 0})
        for v in vendas:
            hora = v.created_at.hour
            vendas_por_hora[hora]["quantidade"] += 1
            vendas_por_hora[hora]["total"] += v.total

        if formato == "json":
            return (
                jsonify(
                    {
                        "data": data_relatorio,
                        "resumo": {
                            "total_vendas": float(total_vendas),
                            "quantidade_vendas": quantidade_vendas,
                            "ticket_medio": float(ticket_medio),
                            "total_descontos": float(total_descontos),
                        },
                        "formas_pagamento": dict(formas_pagamento),
                        "funcionarios": [
                            {
                                "id": func_id,
                                "nome": dados["nome"],
                                "quantidade": dados["quantidade"],
                                "total": float(dados["total"]),
                            }
                            for func_id, dados in funcionarios.items()
                        ],
                        "produtos_mais_vendidos": [
                            {
                                "produto_id": prod_id,
                                "nome": dados["nome"],
                                "quantidade": dados["quantidade"],
                                "total": float(dados["total"]),
                            }
                            for prod_id, dados in sorted(
                                produtos_dia.items(),
                                key=lambda x: x[1]["quantidade"],
                                reverse=True,
                            )[:10]
                        ],
                        "vendas_por_hora": [
                            {
                                "hora": hora,
                                "quantidade": dados["quantidade"],
                                "total": float(dados["total"]),
                            }
                            for hora, dados in sorted(vendas_por_hora.items())
                        ],
                        "vendas": [
                            {
                                "id": v.id,
                                "codigo": v.codigo,
                                "cliente": (
                                    v.cliente.nome if v.cliente else "Consumidor Final"
                                ),
                                "funcionario": (
                                    v.funcionario.nome
                                    if v.funcionario
                                    else "Não Informado"
                                ),
                                "total": float(v.total),
                                "forma_pagamento": v.forma_pagamento,
                                "hora": v.created_at.strftime("%H:%M"),
                                "quantidade_itens": len(v.itens),
                            }
                            for v in vendas
                        ],
                    }
                ),
                200,
            )

        # Outros formatos podem ser adicionados aqui (excel, pdf, etc.)
        else:
            return jsonify({"error": "Formato não suportado"}), 400

    except Exception as e:
        print(f"❌ Erro ao gerar relatório diário: {str(e)}")
        return jsonify({"error": f"Erro ao gerar relatório diário: {str(e)}"}), 500


@vendas_bp.route("/analise-tendencia", methods=["GET"], strict_slashes=False)
def analise_tendencia():
    """Análise de tendência de vendas por período"""
    try:
        # Parâmetros
        periodo = request.args.get("periodo", "mensal")  # diario, semanal, mensal
        meses = int(request.args.get("meses", 6))

        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=30 * meses)

        # Consulta base
        query = Venda.query.filter(
            Venda.status == "finalizada",
            Venda.created_at >= data_inicio,
            Venda.created_at <= data_fim,
        )

        resultados = []

        if periodo == "diario":
            # Vendas por dia
            vendas_por_dia = (
                db.session.query(
                    func.date(Venda.created_at).label("data"),
                    func.count(Venda.id).label("quantidade"),
                    func.sum(Venda.total).label("total"),
                )
                .filter(Venda.status == "finalizada")
                .group_by(func.date(Venda.created_at))
                .order_by(func.date(Venda.created_at).desc())
                .limit(30)
                .all()
            )

            for vpd in vendas_por_dia:
                resultados.append(
                    {
                        "periodo": vpd.data.strftime("%d/%m/%Y"),
                        "quantidade": vpd.quantidade,
                        "total": float(vpd.total) if vpd.total else 0,
                    }
                )

        elif periodo == "semanal":
            # Vendas por semana
            for i in range(meses * 4):  # Aproximadamente 4 semanas por mês
                semana_fim = data_fim - timedelta(weeks=i)
                semana_inicio = semana_fim - timedelta(weeks=1)

                vendas_semana = query.filter(
                    Venda.created_at >= semana_inicio,
                    Venda.created_at <= semana_fim,
                ).all()

                resultados.append(
                    {
                        "periodo": f"Semana {i+1} ({semana_inicio.strftime('%d/%m')} - {semana_fim.strftime('%d/%m')})",
                        "quantidade": len(vendas_semana),
                        "total": sum(v.total for v in vendas_semana),
                    }
                )

        else:  # mensal
            # Vendas por mês
            for i in range(meses):
                mes_fim = data_fim - timedelta(days=30 * i)
                mes_inicio = mes_fim - timedelta(days=30)

                vendas_mes = query.filter(
                    Venda.created_at >= mes_inicio,
                    Venda.created_at <= mes_fim,
                ).all()

                resultados.append(
                    {
                        "periodo": mes_inicio.strftime("%B %Y"),
                        "quantidade": len(vendas_mes),
                        "total": sum(v.total for v in vendas_mes),
                        "ticket_medio": (
                            sum(v.total for v in vendas_mes) / len(vendas_mes)
                            if vendas_mes
                            else 0
                        ),
                    }
                )

        # Calcular crescimento
        if len(resultados) > 1:
            for i in range(len(resultados) - 1):
                atual = resultados[i]["total"]
                anterior = resultados[i + 1]["total"]

                if anterior > 0:
                    crescimento = ((atual - anterior) / anterior) * 100
                else:
                    crescimento = 100 if atual > 0 else 0

                resultados[i]["crescimento"] = round(crescimento, 2)

        return (
            jsonify(
                {
                    "periodo_analisado": periodo,
                    "meses_analisados": meses,
                    "data_inicio": data_inicio.strftime("%Y-%m-%d"),
                    "data_fim": data_fim.strftime("%Y-%m-%d"),
                    "resultados": resultados,
                    "total_geral": sum(r["total"] for r in resultados),
                    "media_mensal": (
                        sum(r["total"] for r in resultados) / len(resultados)
                        if resultados
                        else 0
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Erro na análise de tendência: {str(e)}")
        return jsonify({"error": f"Erro na análise de tendência: {str(e)}"}), 500


# ==================== MANTENDO AS OUTRAS ROTAS (inalteradas com filtros básicos) ====================


@vendas_bp.route("/", methods=["POST", "OPTIONS"], strict_slashes=False)
def criar_venda():
    """Cria uma nova venda (finalizar compra no PDV)"""
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    try:
        data = request.get_json()
        print(f"📦 Dados da venda recebidos: {data}")

        # VALIDAÇÕES BÁSICAS
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        if not data.get("items") or len(data["items"]) == 0:
            return jsonify({"error": "Carrinho vazio"}), 400

        # Validação de valores numéricos
        try:
            subtotal = float(data.get("subtotal", 0))
            desconto = float(data.get("desconto", 0))
            total = float(data.get("total", 0))
            valor_recebido = float(data.get("cashReceived", 0))

            if total > valor_recebido and data.get("paymentMethod") == "dinheiro":
                return (
                    jsonify(
                        {
                            "error": "Valor recebido menor que o total para pagamento em dinheiro"
                        }
                    ),
                    400,
                )

            if subtotal < 0 or desconto < 0 or total < 0 or valor_recebido < 0:
                return jsonify({"error": "Valores não podem ser negativos"}), 400
        except ValueError:
            return jsonify({"error": "Valores numéricos inválidos"}), 400

        # 1. GERAR CÓDIGO DA VENDA
        codigo_venda = gerar_codigo_venda()
        while Venda.query.filter_by(codigo=codigo_venda).first():
            codigo_venda = gerar_codigo_venda()

        # 2. CRIAR A VENDA
        nova_venda = Venda(
            codigo=codigo_venda,
            cliente_id=data.get("cliente_id"),
            funcionario_id=data.get("funcionario_id", 1),
            subtotal=subtotal,
            desconto=desconto,
            total=total,
            forma_pagamento=data.get("paymentMethod", "dinheiro"),
            valor_recebido=valor_recebido,
            troco=float(data.get("change", 0)),
            status="finalizada",
            observacoes=data.get("observacoes", ""),
        )

        db.session.add(nova_venda)
        db.session.flush()

        # 3. ADICIONAR ITENS DA VENDA E ATUALIZAR ESTOQUE
        for item_data in data["items"]:
            produto_id = item_data.get("productId")
            quantidade = item_data.get("quantity", 1)
            preco_unitario = float(item_data.get("price", 0))
            total_item = float(item_data.get("total", 0))

            # Validações do item
            if not produto_id:
                db.session.rollback()
                return jsonify({"error": "ID do produto não informado"}), 400

            if quantidade <= 0:
                db.session.rollback()
                return (
                    jsonify(
                        {"error": f"Quantidade inválida para produto {produto_id}"}
                    ),
                    400,
                )

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
                preco_unitario=preco_unitario,
                desconto=item_data.get("desconto_item", 0.0),
                total_item=total_item,
                produto_nome=produto.nome,
                produto_codigo=produto.codigo_barras,
                produto_unidade=produto.unidade_medida,
            )

            db.session.add(venda_item)

            # 4. ATUALIZAR ESTOQUE DO PRODUTO
            quantidade_anterior = produto.quantidade
            produto.quantidade -= quantidade
            quantidade_atual = produto.quantidade
            
            # ATUALIZAR CAMPOS DE VENDAS PARA ANÁLISE ABC
            produto.quantidade_vendida = (produto.quantidade_vendida or 0) + quantidade
            produto.total_vendido = (produto.total_vendido or 0) + total_item
            produto.ultima_venda = datetime.utcnow()

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
                funcionario_id=nova_venda.funcionario_id,
            )

            db.session.add(movimentacao)

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
        print(f"📋 Itens vendidos: {len(nova_venda.itens)}")

        return jsonify(resposta), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao finalizar venda: {str(e)}")
        return jsonify({"error": f"Erro ao processar venda: {str(e)}"}), 500


@vendas_bp.route("/<int:venda_id>", methods=["GET"], strict_slashes=False)
def obter_venda(venda_id):
    """Obtém detalhes completos de uma venda específica"""
    try:
        venda = Venda.query.options(
            db.joinedload(Venda.itens),
            db.joinedload(Venda.cliente),
            db.joinedload(Venda.funcionario),
        ).get_or_404(venda_id)

        # Buscar movimentações relacionadas a esta venda
        movimentacoes = MovimentacaoEstoque.query.filter_by(venda_id=venda_id).all()

        return (
            jsonify(
                {
                    "venda": {
                        "id": venda.id,
                        "codigo": venda.codigo,
                        "cliente": {
                            "id": venda.cliente.id if venda.cliente else None,
                            "nome": (
                                venda.cliente.nome
                                if venda.cliente
                                else "Consumidor Final"
                            ),
                            "telefone": (
                                venda.cliente.telefone if venda.cliente else None
                            ),
                            "cpf": (
                                venda.cliente.cpf if venda.cliente else None
                            ),
                        },
                        "funcionario": {
                            "id": venda.funcionario.id if venda.funcionario else None,
                            "nome": (
                                venda.funcionario.nome
                                if venda.funcionario
                                else "Não Informado"
                            ),
                            "email": (
                                venda.funcionario.email if venda.funcionario else None
                            ),
                        },
                        "subtotal": float(venda.subtotal),
                        "desconto": float(venda.desconto),
                        "total": float(venda.total),
                        "forma_pagamento": venda.forma_pagamento,
                        "valor_recebido": float(venda.valor_recebido),
                        "troco": float(venda.troco),
                        "status": venda.status,
                        "observacoes": venda.observacoes,
                        "data_criacao": venda.created_at.isoformat(),
                        "data_atualizacao": (
                            venda.updated_at.isoformat() if venda.updated_at else None
                        ),
                        "itens": [
                            {
                                "id": item.id,
                                "produto_id": item.produto_id,
                                "produto_nome": item.produto_nome,
                                "produto_codigo": item.produto_codigo,
                                "quantidade": item.quantidade,
                                "preco_unitario": float(item.preco_unitario),
                                "desconto": float(item.desconto),
                                "total_item": float(item.total_item),
                                "unidade_medida": item.produto_unidade,
                            }
                            for item in venda.itens
                        ],
                        "movimentacoes_estoque": [
                            {
                                "id": mov.id,
                                "produto_id": mov.produto_id,
                                "produto_nome": (
                                    mov.produto.nome
                                    if mov.produto
                                    else "Produto Removido"
                                ),
                                "tipo": mov.tipo,
                                "quantidade": mov.quantidade,
                                "quantidade_anterior": mov.quantidade_anterior,
                                "quantidade_atual": mov.quantidade_atual,
                                "motivo": mov.motivo,
                                "data": mov.created_at.isoformat(),
                            }
                            for mov in movimentacoes
                        ],
                    }
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Erro ao obter venda: {str(e)}")
        return jsonify({"error": f"Erro ao obter venda: {str(e)}"}), 500


@vendas_bp.route("/dia", methods=["GET"], strict_slashes=False)
def vendas_do_dia():
    """Retorna as vendas do dia atual (para dashboard PDV)"""
    try:
        hoje = datetime.now().date()
        amanha = hoje + timedelta(days=1)

        # Vendas do dia
        vendas_hoje = (
            Venda.query.filter(
                Venda.created_at >= hoje,
                Venda.created_at < amanha,
                Venda.status == "finalizada",
            )
            .options(db.joinedload(Venda.funcionario), db.joinedload(Venda.itens))
            .order_by(Venda.created_at.desc())
            .all()
        )

        # Estatísticas do dia
        total_hoje = (
            db.session.query(func.sum(Venda.total))
            .filter(
                Venda.created_at >= hoje,
                Venda.created_at < amanha,
                Venda.status == "finalizada",
            )
            .scalar()
            or 0
        )

        quantidade_vendas = len(vendas_hoje)

        # Vendas por forma de pagamento
        formas_pagamento = (
            db.session.query(
                Venda.forma_pagamento,
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .filter(
                Venda.created_at >= hoje,
                Venda.created_at < amanha,
                Venda.status == "finalizada",
            )
            .group_by(Venda.forma_pagamento)
            .all()
        )

        # Produtos mais vendidos hoje
        produtos_mais_vendidos = (
            db.session.query(
                VendaItem.produto_nome,
                func.sum(VendaItem.quantidade).label("quantidade_total"),
                func.sum(VendaItem.total_item).label("total_vendido"),
            )
            .join(Venda)
            .filter(
                Venda.created_at >= hoje,
                Venda.created_at < amanha,
                Venda.status == "finalizada",
            )
            .group_by(VendaItem.produto_nome)
            .order_by(func.sum(VendaItem.quantidade).desc())
            .limit(10)
            .all()
        )

        return (
            jsonify(
                {
                    "data": hoje.isoformat(),
                    "vendas": [
                        {
                            "id": v.id,
                            "codigo": v.codigo,
                            "cliente": (
                                v.cliente.nome if v.cliente else "Consumidor Final"
                            ),
                            "funcionario": (
                                v.funcionario.nome if v.funcionario else "Não Informado"
                            ),
                            "total": float(v.total),
                            "forma_pagamento": v.forma_pagamento,
                            "hora": v.created_at.strftime("%H:%M"),
                            "quantidade_itens": len(v.itens),
                        }
                        for v in vendas_hoje
                    ],
                    "estatisticas": {
                        "total_vendas": float(total_hoje),
                        "quantidade_vendas": quantidade_vendas,
                        "ticket_medio": (
                            float(total_hoje / quantidade_vendas)
                            if quantidade_vendas > 0
                            else 0
                        ),
                        "formas_pagamento": [
                            {
                                "forma": fp.forma_pagamento,
                                "quantidade": fp.quantidade,
                                "total": float(fp.total),
                            }
                            for fp in formas_pagamento
                        ],
                        "produtos_mais_vendidos": [
                            {
                                "nome": pmv.produto_nome,
                                "quantidade": int(pmv.quantidade_total),
                                "total_vendido": float(pmv.total_vendido),
                            }
                            for pmv in produtos_mais_vendidos
                        ],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Erro ao obter vendas do dia: {str(e)}")
        return jsonify({"error": f"Erro ao obter vendas do dia: {str(e)}"}), 500


@vendas_bp.route("/<int:venda_id>/cancelar", methods=["POST"], strict_slashes=False)
def cancelar_venda(venda_id):
    """Cancela uma venda e devolve os produtos ao estoque"""
    try:
        data = request.get_json()
        motivo = data.get("motivo", "Cancelamento solicitado pelo usuário")
        funcionario_id = data.get(
            "funcionario_id", 1
        )  # ID do funcionário que está cancelando

        # Buscar venda
        venda = Venda.query.options(db.joinedload(Venda.itens)).get_or_404(venda_id)

        # Verificar se já está cancelada
        if venda.status == "cancelada":
            return jsonify({"error": "Esta venda já está cancelada"}), 400

        # Verificar se passou muito tempo (opcional - 24 horas)
        tempo_decorrido = datetime.now() - venda.created_at
        if tempo_decorrido.days > 0:
            return (
                jsonify(
                    {
                        "error": "Vendas com mais de 24 horas não podem ser canceladas automaticamente"
                    }
                ),
                400,
            )

        # Iniciar transação
        db.session.begin_nested()

        try:
            # Para cada item, devolver ao estoque
            for item in venda.itens:
                produto = Produto.query.get(item.produto_id)
                if produto:
                    quantidade_anterior = produto.quantidade
                    produto.quantidade += item.quantidade
                    quantidade_atual = produto.quantidade

                    # Registrar movimentação de entrada (devolução)
                    movimentacao = MovimentacaoEstoque(
                        produto_id=produto.id,
                        tipo="entrada",
                        quantidade=item.quantidade,
                        quantidade_anterior=quantidade_anterior,
                        quantidade_atual=quantidade_atual,
                        motivo=f"Cancelamento da venda #{venda.codigo}",
                        observacoes=f"Devolução por cancelamento. Motivo: {motivo}",
                        venda_id=venda.id,
                        funcionario_id=funcionario_id,
                    )
                    db.session.add(movimentacao)

            # Atualizar status da venda
            venda.status = "cancelada"
            venda.observacoes = f"{venda.observacoes or ''}\n[Cancelada em {datetime.now().strftime('%d/%m/%Y %H:%M')}] Motivo: {motivo}".strip()
            venda.updated_at = datetime.now()

            db.session.commit()

            print(f"✅ Venda {venda.codigo} cancelada com sucesso")

            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Venda cancelada com sucesso",
                        "venda": {
                            "id": venda.id,
                            "codigo": venda.codigo,
                            "status": venda.status,
                            "total": float(venda.total),
                        },
                    }
                ),
                200,
            )

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao cancelar venda: {str(e)}")
            return jsonify({"error": f"Erro ao cancelar venda: {str(e)}"}), 500

    except Exception as e:
        print(f"❌ Erro no processo de cancelamento: {str(e)}")
        return jsonify({"error": f"Erro no processo de cancelamento: {str(e)}"}), 500

# ==================== EXPORTAÇÃO DE VENDAS ====================


@vendas_bp.route("/exportar", methods=["GET"], strict_slashes=False)
def exportar_vendas():
    """Exporta vendas em formato CSV (compatível com Excel).
    
    Query params:
    - formato: 'excel' ou 'csv' (padrão: csv)
    - data_inicio: YYYY-MM-DD
    - data_fim: YYYY-MM-DD
    - status: filtrar por status
    """
    try:
        import io
        import csv

        formato = request.args.get("formato", "csv")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        status = request.args.get("status")

        query = db.session.query(Venda).outerjoin(Cliente).outerjoin(
            Funcionario, Venda.funcionario_id == Funcionario.id
        )

        if data_inicio:
            query = query.filter(Venda.data_venda >= datetime.strptime(data_inicio, "%Y-%m-%d"))
        if data_fim:
            query = query.filter(Venda.data_venda <= datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1))
        if status:
            query = query.filter(Venda.status == status)

        query = query.order_by(Venda.data_venda.desc())
        vendas = query.limit(5000).all()

        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")

        # Header
        writer.writerow([
            "Código", "Data", "Cliente", "Funcionário", "Subtotal",
            "Desconto", "Total", "Forma Pagamento", "Status", "Itens"
        ])

        for v in vendas:
            cliente_nome = ""
            if v.cliente_id:
                cli = Cliente.query.get(v.cliente_id)
                cliente_nome = cli.nome if cli else ""
            func_nome = ""
            if v.funcionario_id:
                func_obj = Funcionario.query.get(v.funcionario_id)
                func_nome = func_obj.nome if func_obj else ""

            itens_count = db.session.query(func.count(VendaItem.id)).filter(
                VendaItem.venda_id == v.id
            ).scalar() or 0

            writer.writerow([
                v.codigo or f"V-{v.id}",
                v.data_venda.strftime("%d/%m/%Y %H:%M") if v.data_venda else "",
                cliente_nome,
                func_nome,
                f"{float(v.subtotal or 0):.2f}",
                f"{float(v.desconto or 0):.2f}",
                f"{float(v.total or 0):.2f}",
                v.forma_pagamento or "",
                v.status or "",
                itens_count,
            ])

        content = output.getvalue()
        output.close()

        if formato == "excel":
            mimetype = "application/vnd.ms-excel"
            ext = "xls"
        else:
            mimetype = "text/csv"
            ext = "csv"

        from flask import Response
        resp = Response(
            "\ufeff" + content,
            mimetype=f"{mimetype}; charset=utf-8",
        )
        resp.headers["Content-Disposition"] = f'attachment; filename="vendas-{datetime.now().strftime("%Y%m%d")}.{ext}"'
        return resp

    except Exception as e:
        print(f"❌ Erro ao exportar vendas: {str(e)}")
        return jsonify({"error": f"Erro ao exportar: {str(e)}"}), 500


# ==================== COMPROVANTE DE VENDA ====================


@vendas_bp.route("/<int:venda_id>/comprovante", methods=["GET"], strict_slashes=False)
def comprovante_venda(venda_id):
    """Gera comprovante de venda em formato texto (para impressão térmica ou PDF).
    
    Retorna um arquivo de texto formatado como cupom fiscal simplificado.
    """
    try:
        venda = Venda.query.get(venda_id)
        if not venda:
            return jsonify({"error": "Venda não encontrada"}), 404

        itens = VendaItem.query.filter_by(venda_id=venda.id).all()

        cliente_nome = "Consumidor Final"
        if venda.cliente_id:
            cli = Cliente.query.get(venda.cliente_id)
            if cli:
                cliente_nome = cli.nome

        func_nome = "N/A"
        if venda.funcionario_id:
            func_obj = Funcionario.query.get(venda.funcionario_id)
            if func_obj:
                func_nome = func_obj.nome

        # Gerar cupom em texto
        largura = 48
        sep = "=" * largura
        sep_fino = "-" * largura

        linhas = []
        linhas.append(sep)
        linhas.append("MERCADINHO SYS".center(largura))
        linhas.append("CUPOM NÃO FISCAL".center(largura))
        linhas.append(sep)
        linhas.append(f"Venda: {venda.codigo or f'V-{venda.id}'}")
        linhas.append(f"Data: {venda.data_venda.strftime('%d/%m/%Y %H:%M') if venda.data_venda else 'N/A'}")
        linhas.append(f"Cliente: {cliente_nome}")
        linhas.append(f"Operador: {func_nome}")
        linhas.append(sep_fino)
        linhas.append(f"{'ITEM':<22} {'QTD':>4} {'UNIT':>9} {'TOTAL':>9}")
        linhas.append(sep_fino)

        for item in itens:
            prod_nome = "Produto"
            if item.produto_id:
                prod = Produto.query.get(item.produto_id)
                if prod:
                    prod_nome = prod.nome[:22]
            qtd = int(item.quantidade or 0)
            preco_unit = float(item.preco_unitario or 0)
            total_item = float(item.total or 0)
            linhas.append(f"{prod_nome:<22} {qtd:>4} {preco_unit:>9.2f} {total_item:>9.2f}")

        linhas.append(sep_fino)
        linhas.append(f"{'Subtotal:':<30} R$ {float(venda.subtotal or 0):>10.2f}")
        if venda.desconto and float(venda.desconto) > 0:
            linhas.append(f"{'Desconto:':<30} R$ {float(venda.desconto):>10.2f}")
        linhas.append(f"{'TOTAL:':<30} R$ {float(venda.total or 0):>10.2f}")
        linhas.append(sep_fino)
        linhas.append(f"Forma de Pagamento: {venda.forma_pagamento or 'N/A'}")
        linhas.append(sep)
        linhas.append("Obrigado pela preferência!".center(largura))
        linhas.append(sep)

        conteudo = "\n".join(linhas)

        from flask import Response
        resp = Response(conteudo, mimetype="text/plain; charset=utf-8")
        resp.headers["Content-Disposition"] = f'attachment; filename="comprovante-{venda.codigo or venda.id}.txt"'
        return resp

    except Exception as e:
        print(f"❌ Erro ao gerar comprovante: {str(e)}")
        return jsonify({"error": f"Erro ao gerar comprovante: {str(e)}"}), 500


# ==================== ROTAS PARA PDV ATIVO (CARRINHO EM ANDAMENTO) ====================


@vendas_bp.route("/pdv/ativo", methods=["POST"])
def iniciar_venda_pdv():
    """Inicia uma nova venda ativa no PDV (carrinho em andamento)"""
    try:
        data = request.get_json()
        funcionario_id = data.get("funcionario_id")
        cliente_id = data.get("cliente_id")

        if not funcionario_id:
            return jsonify({"error": "Funcionário é obrigatório"}), 400

        # Gerar código temporário
        codigo_temp = f"PDV-{datetime.now().strftime('%H%M%S')}-{funcionario_id}"

        # Criar venda com status "em_andamento"
        venda = Venda(
            codigo=codigo_temp,
            cliente_id=cliente_id,
            funcionario_id=funcionario_id,
            subtotal=0,
            desconto=0,
            total=0,
            forma_pagamento="pendente",
            valor_recebido=0,
            troco=0,
            status="em_andamento",
            quantidade_itens=0,
        )

        db.session.add(venda)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "venda_id": venda.id,
                    "codigo_temp": codigo_temp,
                    "message": "Venda iniciada no PDV",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao iniciar venda PDV: {str(e)}")
        return jsonify({"error": f"Erro ao iniciar venda: {str(e)}"}), 500


@vendas_bp.route("/pdv/<int:venda_id>/adicionar-item", methods=["POST"])
def adicionar_item_pdv(venda_id):
    """Adiciona um item ao carrinho de uma venda em andamento"""
    try:
        data = request.get_json()
        produto_id = data.get("produto_id")
        quantidade = data.get("quantidade", 1)

        if not produto_id:
            return jsonify({"error": "Produto é obrigatório"}), 400

        # Buscar venda
        venda = Venda.query.get(venda_id)
        if not venda or venda.status != "em_andamento":
            return jsonify({"error": "Venda não encontrada ou não está ativa"}), 404

        # Buscar produto
        produto = Produto.query.get(produto_id)
        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        if produto.quantidade < quantidade:
            return (
                jsonify(
                    {"error": f"Estoque insuficiente. Disponível: {produto.quantidade}"}
                ),
                400,
            )

        # Verificar se item já existe no carrinho
        item_existente = VendaItem.query.filter_by(
            venda_id=venda_id, produto_id=produto_id
        ).first()

        if item_existente:
            # Atualizar quantidade
            nova_quantidade = item_existente.quantidade + quantidade
            item_existente.quantidade = nova_quantidade
            item_existente.total_item = nova_quantidade * item_existente.preco_unitario
        else:
            # Criar novo item
            venda_item = VendaItem(
                venda_id=venda_id,
                produto_id=produto_id,
                produto_nome=produto.nome,
                produto_codigo=produto.codigo_barras,
                produto_unidade=produto.unidade_medida,
                quantidade=quantidade,
                preco_unitario=produto.preco_venda,
                total_item=quantidade * produto.preco_venda,
                desconto=0,
            )
            db.session.add(venda_item)

        # Recalcular totais da venda
        venda.itens = VendaItem.query.filter_by(venda_id=venda_id).all()
        venda.subtotal = sum(
            item.preco_unitario * item.quantidade for item in venda.itens
        )
        venda.total = venda.subtotal - venda.desconto
        venda.quantidade_itens = sum(item.quantidade for item in venda.itens)

        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "subtotal": venda.subtotal,
                    "total": venda.total,
                    "quantidade_itens": venda.quantidade_itens,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao adicionar item: {str(e)}")
        return jsonify({"error": f"Erro ao adicionar item: {str(e)}"}), 500


@vendas_bp.route("/pdv/<int:venda_id>/remover-item/<int:item_id>", methods=["DELETE"])
def remover_item_pdv(venda_id, item_id):
    """Remove um item do carrinho de uma venda em andamento"""
    try:
        # Buscar item
        item = VendaItem.query.filter_by(id=item_id, venda_id=venda_id).first()
        if not item:
            return jsonify({"error": "Item não encontrado"}), 404

        db.session.delete(item)

        # Recalcular totais da venda
        venda = Venda.query.get(venda_id)
        venda.itens = VendaItem.query.filter_by(venda_id=venda_id).all()
        venda.subtotal = sum(
            item.preco_unitario * item.quantidade for item in venda.itens
        )
        venda.total = venda.subtotal - venda.desconto
        venda.quantidade_itens = sum(item.quantidade for item in venda.itens)

        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Item removido do carrinho",
                    "subtotal": venda.subtotal,
                    "total": venda.total,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao remover item: {str(e)}")
        return jsonify({"error": f"Erro ao remover item: {str(e)}"}), 500


@vendas_bp.route("/pdv/<int:venda_id>/atualizar-quantidade", methods=["PUT"])
def atualizar_quantidade_pdv(venda_id):
    """Atualiza a quantidade de um item no carrinho"""
    try:
        data = request.get_json()
        item_id = data.get("item_id")
        nova_quantidade = data.get("quantidade", 1)

        if nova_quantidade <= 0:
            return jsonify({"error": "Quantidade deve ser maior que 0"}), 400

        # Buscar item
        item = VendaItem.query.filter_by(id=item_id, venda_id=venda_id).first()
        if not item:
            return jsonify({"error": "Item não encontrado"}), 404

        # Verificar estoque
        produto = Produto.query.get(item.produto_id)
        if produto.quantidade < nova_quantidade:
            return (
                jsonify(
                    {"error": f"Estoque insuficiente. Disponível: {produto.quantidade}"}
                ),
                400,
            )

        # Atualizar quantidade
        item.quantidade = nova_quantidade
        item.total_item = nova_quantidade * item.preco_unitario

        # Recalcular totais da venda
        venda = Venda.query.get(venda_id)
        venda.itens = VendaItem.query.filter_by(venda_id=venda_id).all()
        venda.subtotal = sum(
            item.preco_unitario * item.quantidade for item in venda.itens
        )
        venda.total = venda.subtotal - venda.desconto
        venda.quantidade_itens = sum(item.quantidade for item in venda.itens)

        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "subtotal": venda.subtotal,
                    "total": venda.total,
                    "quantidade_itens": venda.quantidade_itens,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao atualizar quantidade: {str(e)}")
        return jsonify({"error": f"Erro ao atualizar quantidade: {str(e)}"}), 500


@vendas_bp.route("/pdv/configuracoes", methods=["GET"])
def obter_configuracoes_pdv():
    """Retorna configurações específicas para o PDV"""
    try:
        # Aqui você buscaria as configurações do estabelecimento
        # Por enquanto, retornamos configurações padrão

        return (
            jsonify(
                {
                    "formas_pagamento": [
                        {"tipo": "dinheiro", "label": "Dinheiro", "taxa": 0},
                        {
                            "tipo": "cartao_credito",
                            "label": "Cartão Crédito",
                            "taxa": 2.5,
                        },
                        {
                            "tipo": "cartao_debito",
                            "label": "Cartão Débito",
                            "taxa": 1.5,
                        },
                        {"tipo": "pix", "label": "PIX", "taxa": 0},
                    ],
                    "permitir_venda_sem_estoque": False,
                    "desconto_maximo_percentual": 10.0,
                    "arredondamento_valores": 0.05,
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Erro ao obter configurações PDV: {str(e)}")
        return jsonify({"error": f"Erro ao obter configurações: {str(e)}"}), 500


@vendas_bp.route("/pdv/calcular-troco", methods=["POST"])
def calcular_troco():
    """Calcula o troco com base no total e valor recebido"""
    try:
        data = request.get_json()
        total = data.get("total", 0)
        valor_recebido = data.get("valor_recebido", 0)

        if valor_recebido < total:
            return (
                jsonify(
                    {
                        "error": "Valor recebido é menor que o total",
                        "troco": 0,
                        "faltante": total - valor_recebido,
                    }
                ),
                400,
            )

        troco = valor_recebido - total

        return (
            jsonify({"troco": troco, "valor_recebido": valor_recebido, "total": total}),
            200,
        )

    except Exception as e:
        print(f"❌ Erro ao calcular troco: {str(e)}")
        return jsonify({"error": f"Erro ao calcular troco: {str(e)}"}), 500


@vendas_bp.route("/pdv/carrinhos-ativos", methods=["GET"])
def listar_carrinhos_ativos():
    """Lista todas as vendas em andamento (carrinhos ativos)"""
    try:
        # Buscar vendas em andamento
        vendas_ativas = Venda.query.filter_by(status="em_andamento").all()

        return (
            jsonify(
                {
                    "carrinhos_ativos": [
                        {
                            "venda_id": v.id,
                            "codigo_temp": v.codigo,
                            "funcionario_id": v.funcionario_id,
                            "cliente_id": v.cliente_id,
                            "total": float(v.total),
                            "quantidade_itens": v.quantidade_itens,
                            "iniciada_em": v.created_at.isoformat(),
                        }
                        for v in vendas_ativas
                    ]
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Erro ao listar carrinhos ativos: {str(e)}")
        return jsonify({"error": f"Erro ao listar carrinhos ativos: {str(e)}"}), 500
