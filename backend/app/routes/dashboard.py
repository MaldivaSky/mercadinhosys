# app/routes/dashboard.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, cache
from app.models import (
    DashboardMetrica,
    Venda,
    Produto,
    Cliente,
    Funcionario,
    MovimentacaoEstoque,
    Estabelecimento,
    VendaItem,
    Configuracao,
    Despesa,
)
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract, case, text, and_, or_
from sqlalchemy.sql import label
import numpy as np
import pandas as pd
from scipy import stats
from collections import defaultdict
import json
from app.decorators.decorator_jwt import funcionario_required, admin_required
from app.utils.utils import (
    calcular_tendencia,
    calcular_moving_average,
    detectar_anomalias,
    calcular_classificacao_abc,
    calcular_rfm_score,
    calcular_seasonal_decomposition,
    detectar_padroes_sazonais,
    calcular_correlacao_cruzada,
    gerar_insight_automatico,
)

dashboard_bp = Blueprint("dashboard", __name__)

# ==================== DASHBOARD GERAL (TODOS OS FUNCIONÁRIOS) ====================


@dashboard_bp.route("/resumo", methods=["GET"])
@funcionario_required
def resumo_dashboard():
    """Retorna resumo completo para o dashboard com análises avançadas"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)

        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        estabelecimento_id = funcionario.estabelecimento_id
        hoje = date.today()

        # Verificar permissões
        is_admin = funcionario.role in ["admin", "dono", "gerente"]
        acesso_avancado = is_admin or funcionario.permissoes.get(
            "acesso_dashboard_avancado", False
        )

        # Verificar se já temos métricas calculadas para hoje
        metrica = DashboardMetrica.query.filter_by(
            estabelecimento_id=estabelecimento_id, data_referencia=hoje
        ).first()

        if not metrica:
            metrica = calcular_metricas_avancadas(estabelecimento_id, hoje)

        # Dados em tempo real
        dados_realtime = obter_dados_tempo_real(
            estabelecimento_id, hoje, acesso_avancado
        )

        # Análises preditivas (apenas para acesso avançado)
        previsoes = {}
        insights = []
        analises_avancadas = {}

        if acesso_avancado:
            previsoes = gerar_previsoes(estabelecimento_id)
            insights = gerar_insights_automaticos(estabelecimento_id, metrica)
            analises_avancadas = {
                "analise_clientes": {
                    "segmentacao": segmentar_clientes(estabelecimento_id),
                    "top_clientes": identificar_top_clientes(
                        estabelecimento_id, limite=10
                    ),
                },
                "analise_produtos": {
                    "top_produtos": (
                        json.loads(metrica.top_produtos_json)
                        if metrica.top_produtos_json
                        else []
                    ),
                    "produtos_estrela": identificar_produtos_estrela(
                        estabelecimento_id
                    ),
                    "cross_selling": [],  # analisar_cross_selling(estabelecimento_id) - Desabilitado temporariamente
                },
                "kpis_avancados": {
                    "customer_lifetime_value": calcular_clv(estabelecimento_id),
                    "churn_rate": calcular_taxa_churn(estabelecimento_id),
                    "repeat_customer_rate": calcular_taxa_repeticao(estabelecimento_id),
                    "average_order_value": metrica.ticket_medio_dia,
                    "conversion_rate": calcular_taxa_conversao(estabelecimento_id),
                },
            }

        response_data = {
            "success": True,
            "usuario": {
                "nome": funcionario.nome,
                "role": funcionario.role,
                "acesso_avancado": acesso_avancado,
            },
            "data": {
                "hoje": {
                    "data": hoje.isoformat(),
                    "total_vendas": metrica.total_vendas_dia,
                    "quantidade_vendas": metrica.quantidade_vendas_dia,
                    "ticket_medio": metrica.ticket_medio_dia,
                    "clientes_atendidos": metrica.clientes_atendidos_dia,
                    "crescimento_vs_ontem": metrica.crescimento_vs_ontem,
                    "meta_atingida": (
                        metrica.meta_atingida_dia
                        if hasattr(metrica, "meta_atingida_dia")
                        else None
                    ),
                },
                "mes": {
                    "total_vendas": metrica.total_vendas_mes,
                    "total_despesas": metrica.total_despesas_mes,
                    "lucro_bruto": metrica.lucro_bruto_mes,
                    "margem_lucro": (
                        metrica.margem_lucro_mes
                        if hasattr(metrica, "margem_lucro_mes")
                        else None
                    ),
                    "crescimento_mensal": metrica.crescimento_mensal,
                },
                "alertas": {
                    "estoque_baixo": dados_realtime["estoque_baixo"],
                    "validade_proxima": dados_realtime["validade_proxima"],
                },
                "analise_temporal": {
                    "vendas_por_hora": dados_realtime["vendas_por_hora"],
                    "vendas_por_categoria": dados_realtime.get("vendas_por_categoria", []),
                    "vendas_ultimos_7_dias": dados_realtime.get("vendas_ultimos_7_dias", []),
                    "clientes_novos_mes": dados_realtime.get("clientes_novos_mes", 0),
                },
                "ultimas_vendas": dados_realtime["ultimas_vendas"][:10],
                "metricas_comparativas": {
                    "vs_ontem": comparar_com_ontem(estabelecimento_id),
                    "vs_semana_passada": comparar_com_semana_passada(
                        estabelecimento_id
                    ),
                },
            },
        }

        # Adicionar análises avançadas apenas se tiver permissão
        if acesso_avancado:
            response_data["data"]["previsoes"] = previsoes
            response_data["data"]["insights"] = insights
            response_data["data"].update(analises_avancadas)

            # Análises do dono (apenas para admin)
            if is_admin:
                config = Configuracao.query.filter_by(
                    estabelecimento_id=estabelecimento_id
                ).first()
                meta_diaria = config.meta_vendas_diaria if config else 1000
                response_data["data"]["dono"] = {
                    "projecoes": calcular_projecoes(estabelecimento_id, hoje),
                    "alertas_prioritarios": gerar_alertas_prioritarios_detalhados(
                        estabelecimento_id
                    ),
                    "resumo_executivo": gerar_resumo_executivo(
                        estabelecimento_id, hoje
                    ),
                    "meta_diaria": meta_diaria,
                }

        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(
            f"Erro ao gerar resumo do dashboard: {str(e)}", exc_info=True
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar resumo do dashboard",
                    "message": str(e),
                }
            ),
            500,
        )


# ==================== DASHBOARD DO DONO/ADMIN (ANÁLISES AVANÇADAS) ====================


@dashboard_bp.route("/painel-admin", methods=["GET"])
@admin_required
def painel_admin():
    """Dashboard completo para administradores com BI avançado"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)

        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        estabelecimento_id = funcionario.estabelecimento_id
        hoje = date.today()

        # 1. DADOS BRUTOS
        dados = obter_dados_completos(estabelecimento_id, hoje)

        # 2. CÁLCULO DE TENDÊNCIAS
        tendencias = calcular_tendencias_avancadas(estabelecimento_id, hoje)

        # 3. PROJEÇÕES
        projecoes = calcular_projecoes_detalhadas(dados, tendencias, hoje)

        # 4. INSIGHTS AUTOMÁTICOS (BI)
        insights = gerar_insights_inteligentes(dados, tendencias, projecoes)

        # 5. KPIs PRINCIPAIS
        kpis = calcular_kpis_principais(dados, projecoes)

        # 6. ALERTAS PRIORITÁRIOS
        alertas = gerar_alertas_prioritarios_detalhados(estabelecimento_id)

        return (
            jsonify(
                {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "periodo": {
                        "hoje": hoje.isoformat(),
                        "mes_atual": hoje.strftime("%B/%Y"),
                        "dia_semana": hoje.strftime("%A"),
                    },
                    "kpis": kpis,
                    "tendencias": tendencias,
                    "projecoes": projecoes,
                    "insights": insights,
                    "alertas": alertas,
                    "detalhes": {
                        "vendas": dados.get("vendas_hoje", []),
                        "produtos": dados.get("produtos_estoque_baixo", []),
                        "clientes": dados.get("top_clientes", []),
                    },
                    "analises_avancadas": {
                        "sazonalidade": analisar_sazonalidade(estabelecimento_id),
                        "segmentacao_cliente": segmentar_clientes(estabelecimento_id),
                        "classificacao_abc": calcular_classificacao_abc_estoque(
                            estabelecimento_id
                        ),
                        "correlacao_vendas": analisar_correlacao_vendas(
                            estabelecimento_id
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro no painel admin: {str(e)}", exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar painel admin",
                    "message": str(e),
                }
            ),
            500,
        )


@dashboard_bp.route("/tendencia-mensal", methods=["GET"])
@admin_required
def tendencia_mensal_detalhada():
    """Análise detalhada da tendência mensal com gráficos de dados"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)

        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        estabelecimento_id = funcionario.estabelecimento_id
        hoje = date.today()
        inicio_mes = datetime(hoje.year, hoje.month, 1)

        # Vendas diárias do mês
        vendas_diarias = (
            db.session.query(
                func.date(Venda.data_venda).label("data"),
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
                func.avg(Venda.total).label("ticket_medio"),
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= inicio_mes,
                Venda.status == "finalizada",
            )
            .group_by(func.date(Venda.data_venda))
            .order_by("data")
            .all()
        )

        # Converter para arrays
        datas = [v.data.strftime("%d/%m") for v in vendas_diarias]
        totais = [float(v.total) for v in vendas_diarias]
        quantidades = [v.quantidade for v in vendas_diarias]
        tickets = [float(v.ticket_medio) for v in vendas_diarias]

        # Calcular métricas de tendência
        if len(totais) >= 2:
            # Regressão linear
            dias_numericos = list(range(len(totais)))
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                dias_numericos, totais
            )

            # Previsão para próximos dias
            dias_futuros = dias_numericos + [
                dias_numericos[-1] + i for i in range(1, 8)
            ]
            previsoes = [intercept + slope * d for d in dias_futuros]

            # Crescimento percentual
            if len(totais) >= 7:
                primeira_semana = np.mean(totais[:7]) if len(totais) >= 7 else 0
                ultima_semana = np.mean(totais[-7:]) if len(totais) >= 7 else 0
                crescimento_semanal = (
                    ((ultima_semana - primeira_semana) / primeira_semana * 100)
                    if primeira_semana > 0
                    else 0
                )
            else:
                crescimento_semanal = 0

            # Dias da semana com melhor desempenho
            desempenho_dia_semana = {}
            for v in vendas_diarias:
                dia_semana = v.data.strftime("%A")
                if dia_semana not in desempenho_dia_semana:
                    desempenho_dia_semana[dia_semana] = []
                desempenho_dia_semana[dia_semana].append(float(v.total))

            media_por_dia = {
                dia: np.mean(valores) for dia, valores in desempenho_dia_semana.items()
            }

            return (
                jsonify(
                    {
                        "success": True,
                        "dados_grafico": {
                            "datas": datas,
                            "totais": totais,
                            "quantidades": quantidades,
                            "tickets_medios": tickets,
                            "previsoes": previsoes[-7:],  # Últimas previsões
                            "tendencia_linear": [
                                intercept + slope * d for d in dias_numericos
                            ],
                        },
                        "analise": {
                            "inclinacao": slope,
                            "r_quadrado": r_value**2,
                            "crescimento_semanal": f"{crescimento_semanal:.1f}%",
                            "previsao_fim_mes": previsoes[-1],
                            "confiabilidade": (
                                "ALTA"
                                if r_value**2 > 0.7
                                else "MÉDIA" if r_value**2 > 0.4 else "BAIXA"
                            ),
                            "melhor_dia": (
                                max(media_por_dia, key=media_por_dia.get)
                                if media_por_dia
                                else None
                            ),
                            "pior_dia": (
                                min(media_por_dia, key=media_por_dia.get)
                                if media_por_dia
                                else None
                            ),
                        },
                        "recomendacoes": gerar_recomendacoes_tendencia(
                            slope, crescimento_semanal
                        ),
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "mensagem": "Dados insuficientes para análise de tendência",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro na análise de tendência: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro na análise de tendência",
                    "message": str(e),
                }
            ),
            500,
        )


@dashboard_bp.route("/resumo-executivo", methods=["GET"])
@admin_required
def resumo_executivo():
    """Resumo executivo para tomada de decisão rápida"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)

        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        estabelecimento_id = funcionario.estabelecimento_id
        hoje = date.today()

        # Dados rápidos
        inicio_mes = datetime(hoje.year, hoje.month, 1)
        inicio_dia = datetime.combine(hoje, datetime.min.time())

        # Totais do dia
        total_hoje = (
            db.session.query(func.sum(Venda.total))
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= inicio_dia,
                Venda.status == "finalizada",
            )
            .scalar()
            or 0
        )

        # Totais do mês
        total_mes = (
            db.session.query(func.sum(Venda.total))
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= inicio_mes,
                Venda.status == "finalizada",
            )
            .scalar()
            or 0
        )

        # Alertas críticos
        produtos_estoque_zero = Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.quantidade == 0,
            Produto.ativo == True,
        ).count()

        produtos_vencidos = Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.data_validade < hoje,
            Produto.quantidade > 0,
        ).count()

        # Clientes hoje
        clientes_hoje = (
            db.session.query(func.count(func.distinct(Venda.cliente_id)))
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= inicio_dia,
                Venda.status == "finalizada",
            )
            .scalar()
            or 0
        )

        # Configuração para meta
        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()
        meta_diaria = config.meta_vendas_diaria if config else 1000

        return (
            jsonify(
                {
                    "success": True,
                    "resumo": {
                        "data": hoje.strftime("%d/%m/%Y"),
                        "hora": datetime.now().strftime("%H:%M"),
                        "faturamento_hoje": float(total_hoje),
                        "faturamento_mes": float(total_mes),
                        "clientes_hoje": clientes_hoje,
                        "alertas_criticos": produtos_estoque_zero + produtos_vencidos,
                        "status_operacional": (
                            "NORMAL" if produtos_estoque_zero == 0 else "ATENÇÃO"
                        ),
                        "meta_diaria": meta_diaria,
                        "atingimento_meta": (
                            (total_hoje / meta_diaria * 100) if meta_diaria > 0 else 0
                        ),
                        "decisao_do_dia": obter_decisao_do_dia(
                            float(total_hoje), produtos_estoque_zero, meta_diaria
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro no resumo executivo: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro no resumo executivo",
                    "message": str(e),
                }
            ),
            500,
        )


# ==================== FUNÇÕES COMPARTILHADAS ====================


def calcular_metricas_avancadas(estabelecimento_id, data_referencia):
    """Calcula métricas avançadas do dashboard com análises preditivas"""
    try:
        inicio_dia = datetime.combine(data_referencia, datetime.min.time())
        fim_dia = datetime.combine(data_referencia, datetime.max.time())
        inicio_mes = datetime(data_referencia.year, data_referencia.month, 1)

        # Vendas do dia com análise temporal
        vendas_dia = Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_dia,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada",
        ).all()

        total_vendas_dia = sum(v.total for v in vendas_dia)
        quantidade_vendas_dia = len(vendas_dia)
        ticket_medio_dia = (
            total_vendas_dia / quantidade_vendas_dia if quantidade_vendas_dia > 0 else 0
        )

        # Análise por horário
        vendas_por_hora = analisar_vendas_por_hora(vendas_dia)

        # Clientes atendidos com segmentação
        clientes_ids = [v.cliente_id for v in vendas_dia if v.cliente_id]
        clientes_atendidos_dia = len(set(clientes_ids))

        # Vendas do mês com projeção
        vendas_mes = Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada",
        ).all()

        total_vendas_mes = sum(v.total for v in vendas_mes)

        # Calcular despesas do mês (se existir tabela de despesas)
        total_despesas_mes = calcular_despesas_mes(
            estabelecimento_id, inicio_mes, fim_dia
        )
        lucro_bruto_mes = total_vendas_mes - total_despesas_mes
        margem_lucro_mes = (
            (lucro_bruto_mes / total_vendas_mes * 100) if total_vendas_mes > 0 else 0
        )

        # Top produtos com análise RFM
        top_produtos = calcular_top_produtos_avancado(
            estabelecimento_id, inicio_dia, fim_dia
        )

        # Análise de tendência
        crescimento_vs_ontem = calcular_crescimento_diario(
            estabelecimento_id, data_referencia
        )
        crescimento_mensal = calcular_crescimento_mensal(
            estabelecimento_id, data_referencia
        )

        # Buscar ou criar métrica
        metrica = DashboardMetrica.query.filter_by(
            estabelecimento_id=estabelecimento_id, data_referencia=data_referencia
        ).first()

        if not metrica:
            metrica = DashboardMetrica(
                estabelecimento_id=estabelecimento_id, data_referencia=data_referencia
            )

        # Atualizar métricas avançadas
        metrica.total_vendas_dia = total_vendas_dia
        metrica.quantidade_vendas_dia = quantidade_vendas_dia
        metrica.ticket_medio_dia = ticket_medio_dia
        metrica.clientes_atendidos_dia = clientes_atendidos_dia
        metrica.total_vendas_mes = total_vendas_mes
        metrica.total_despesas_mes = total_despesas_mes
        metrica.lucro_bruto_mes = lucro_bruto_mes
        metrica.margem_lucro_mes = margem_lucro_mes
        metrica.crescimento_vs_ontem = crescimento_vs_ontem
        metrica.crescimento_mensal = crescimento_mensal
        metrica.top_produtos_json = json.dumps(top_produtos)
        metrica.vendas_por_hora_json = json.dumps(vendas_por_hora)
        metrica.data_calculo = datetime.now()

        db.session.add(metrica)
        db.session.commit()

        return metrica

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao calcular métricas avançadas: {str(e)}", exc_info=True
        )
        raise


def obter_dados_completos(estabelecimento_id, hoje):
    """Coleta todos os dados necessários para o dashboard"""
    inicio_dia = datetime.combine(hoje, datetime.min.time())
    fim_dia = datetime.combine(hoje, datetime.max.time())
    inicio_mes = datetime(hoje.year, hoje.month, 1)

    # 1. VENDAS DO DIA
    vendas_hoje = (
        Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_dia,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada",
        )
        .options(db.joinedload(Venda.cliente), db.joinedload(Venda.itens))
        .all()
    )

    # 2. VENDAS DO MÊS (até hoje)
    vendas_mes = Venda.query.filter(
        Venda.estabelecimento_id == estabelecimento_id,
        Venda.data_venda >= inicio_mes,
        Venda.data_venda <= fim_dia,
        Venda.status == "finalizada",
    ).all()

    # 3. PRODUTOS COM ESTOQUE BAIXO
    produtos_estoque_baixo = [
        {
            "id": p.id,
            "nome": p.nome,
            "quantidade": p.quantidade,
            "quantidade_minima": p.quantidade_minima,
            "categoria": p.categoria
        }
        for p in Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.quantidade <= Produto.quantidade_minima,
            Produto.ativo == True,
        )
        .order_by(Produto.quantidade)
        .limit(10)
        .all()
    ]

    # 4. PRODUTOS PRÓXIMOS DA VALIDADE
    config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()
    dias_alerta = config.dias_alerta_validade if config else 15
    data_alerta = hoje + timedelta(days=dias_alerta)

    produtos_validade_proxima = [
        {
            "id": p.id,
            "nome": p.nome,
            "data_validade": p.data_validade.isoformat() if p.data_validade else None,
            "quantidade": p.quantidade,
            "categoria": p.categoria
        }
        for p in Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.data_validade.between(hoje, data_alerta),
            Produto.quantidade > 0,
            Produto.ativo == True,
        )
        .order_by(Produto.data_validade)
        .limit(10)
        .all()
    ]

    # 5. TOP 10 CLIENTES DO MÊS
    top_clientes_query = (
        db.session.query(
            Cliente,
            func.sum(Venda.total).label("total_compras_mes"),
            func.count(Venda.id).label("quantidade_compras"),
        )
        .join(Venda)
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada",
        )
        .group_by(Cliente.id)
        .order_by(func.sum(Venda.total).desc())
        .limit(10)
        .all()
    )
    
    top_clientes = [
        {
            "id": c.id,
            "nome": c.nome,
            "email": c.email,
            "total_compras": float(total),
            "quantidade_compras": int(qtd)
        }
        for c, total, qtd in top_clientes_query
    ]

    # 6. VENDAS POR HORA (últimas 24h)
    hora_inicio = datetime.now() - timedelta(hours=24)
    vendas_por_hora = (
        db.session.query(
            extract("hour", Venda.data_venda).label("hora"),
            func.count(Venda.id).label("quantidade"),
            func.sum(Venda.total).label("total"),
        )
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= hora_inicio,
            Venda.status == "finalizada",
        )
        .group_by(extract("hour", Venda.data_venda))
        .order_by("hora")
        .all()
    )

    # 7. PRODUTOS MAIS VENDIDOS DO MÊS
    produtos_mais_vendidos_query = (
        db.session.query(
            Produto,
            func.sum(VendaItem.quantidade).label("quantidade_vendida"),
            func.sum(VendaItem.total_item).label("total_vendido"),
        )
        .join(VendaItem, Produto.id == VendaItem.produto_id)
        .join(Venda)
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada",
        )
        .group_by(Produto.id)
        .order_by(func.sum(VendaItem.quantidade).desc())
        .limit(10)
        .all()
    )
    
    produtos_mais_vendidos = [
        {
            "id": p.id,
            "nome": p.nome,
            "categoria": p.categoria,
            "quantidade_vendida": int(qtd),
            "total_vendido": float(total)
        }
        for p, qtd, total in produtos_mais_vendidos_query
    ]

    return {
        "vendas_hoje": vendas_hoje,
        "vendas_mes": vendas_mes,
        "produtos_estoque_baixo": produtos_estoque_baixo,
        "produtos_validade_proxima": produtos_validade_proxima,
        "top_clientes": top_clientes,
        "vendas_por_hora": vendas_por_hora,
        "produtos_mais_vendidos": produtos_mais_vendidos,
        "periodos": {"inicio_mes": inicio_mes, "fim_mes": fim_dia, "hoje": hoje},
    }


def calcular_tendencias_avancadas(estabelecimento_id, hoje):
    """Calcula tendências de vendas usando análise estatística"""
    inicio_30_dias = hoje - timedelta(days=30)

    # Buscar vendas dos últimos 30 dias
    vendas_30_dias = Venda.query.filter(
        Venda.estabelecimento_id == estabelecimento_id,
        Venda.data_venda >= inicio_30_dias,
        Venda.data_venda <= datetime.combine(hoje, datetime.max.time()),
        Venda.status == "finalizada",
    ).all()

    if len(vendas_30_dias) < 5:
        return {"erro": "Dados insuficientes para análise"}

    # Organizar vendas por dia
    vendas_por_dia = defaultdict(float)
    for venda in vendas_30_dias:
        dia = venda.data_venda.date()
        vendas_por_dia[dia] += venda.total

    # Converter para listas ordenadas
    dias = sorted(vendas_por_dia.keys())
    valores = [vendas_por_dia[dia] for dia in dias]

    # Calcular regressão linear para tendência
    if len(dias) > 1:
        # Converter datas para números (dias desde o início)
        dias_numericos = [(dia - dias[0]).days for dia in dias]

        # Regressão linear
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            dias_numericos, valores
        )

        # Tendência atual (último valor vs tendência)
        ultimo_dia = dias_numericos[-1]
        valor_esperado = intercept + slope * ultimo_dia
        valor_real = valores[-1]
        desvio_percentual = (
            ((valor_real - valor_esperado) / valor_esperado * 100)
            if valor_esperado != 0
            else 0
        )

        # Classificar tendência
        if slope > 0:
            tendencia_direcao = "CRESCENTE"
            intensidade = (
                abs(slope) / np.mean(valores) * 100 if np.mean(valores) > 0 else 0
            )
        elif slope < 0:
            tendencia_direcao = "DECRESCENTE"
            intensidade = (
                abs(slope) / np.mean(valores) * 100 if np.mean(valores) > 0 else 0
            )
        else:
            tendencia_direcao = "ESTÁVEL"
            intensidade = 0

        # Calcular média móvel (7 dias)
        media_movel = []
        if len(valores) >= 7:
            for i in range(6, len(valores)):
                media_movel.append(np.mean(valores[i - 6 : i + 1]))

        # Identificar padrões sazonais (dias da semana)
        vendas_por_dia_semana = defaultdict(list)
        for dia, valor in zip(dias, valores):
            dia_semana = dia.strftime("%A")
            vendas_por_dia_semana[dia_semana].append(valor)

        media_por_dia_semana = {}
        for dia_semana, valores_dia in vendas_por_dia_semana.items():
            if valores_dia:
                media_por_dia_semana[dia_semana] = np.mean(valores_dia)

        # Dia mais forte e mais fraco
        dia_mais_forte = (
            max(media_por_dia_semana, key=media_por_dia_semana.get)
            if media_por_dia_semana
            else None
        )
        dia_mais_fraco = (
            min(media_por_dia_semana, key=media_por_dia_semana.get)
            if media_por_dia_semana
            else None
        )

        return {
            "tendencia_direcao": tendencia_direcao,
            "intensidade_tendencia": f"{intensidade:.1f}%",
            "coeficiente_angular": slope,
            "r_quadrado": r_value**2,
            "desvio_atual_percentual": f"{desvio_percentual:.1f}%",
            "media_30_dias": np.mean(valores),
            "desvio_padrao": np.std(valores),
            "coeficiente_variacao": (
                (np.std(valores) / np.mean(valores) * 100)
                if np.mean(valores) > 0
                else 0
            ),
            "media_movel_7_dias": media_movel[-1] if media_movel else None,
            "dia_mais_forte": dia_mais_forte,
            "dia_mais_fraco": dia_mais_fraco,
            "media_por_dia_semana": media_por_dia_semana,
            "previsao_amanha": valor_esperado + slope,  # Previsão para amanhã
            "confiabilidade_previsao": (
                "ALTA" if r_value**2 > 0.7 else "MÉDIA" if r_value**2 > 0.4 else "BAIXA"
            ),
        }

    return {"erro": "Não foi possível calcular tendência"}


def calcular_projecoes_detalhadas(dados, tendencias, hoje):
    """Calcula projeções para o final do mês"""
    vendas_mes = dados["vendas_mes"]
    total_mes = sum(v.total for v in vendas_mes)

    # Dias do mês
    dias_no_mes = (
        dados["periodos"]["fim_mes"].date() - dados["periodos"]["inicio_mes"].date()
    ).days + 1
    dias_passados = (hoje - dados["periodos"]["inicio_mes"].date()).days + 1
    dias_restantes = dias_no_mes - dias_passados

    # Média diária atual
    if dias_passados > 0:
        media_diaria = total_mes / dias_passados
    else:
        media_diaria = 0

    # Projeções baseadas em diferentes cenários
    projecoes = {
        "cenario_otimista": {
            "descricao": "Crescimento de 10% na média diária",
            "media_diaria": media_diaria * 1.10,
            "projecao_final": total_mes + (media_diaria * 1.10 * dias_restantes),
        },
        "cenario_realista": {
            "descricao": "Manutenção da média atual",
            "media_diaria": media_diaria,
            "projecao_final": total_mes + (media_diaria * dias_restantes),
        },
        "cenario_pessimista": {
            "descricao": "Queda de 10% na média diária",
            "media_diaria": media_diaria * 0.90,
            "projecao_final": total_mes + (media_diaria * 0.90 * dias_restantes),
        },
        "cenario_tendencia": {
            "descricao": "Baseado na tendência atual",
            "media_diaria": media_diaria
            * (1 + tendencias.get("coeficiente_angular", 0) / 100),
            "projecao_final": total_mes
            + (
                media_diaria
                * (1 + tendencias.get("coeficiente_angular", 0) / 100)
                * dias_restantes
            ),
        },
    }

    # Meta mensal
    config = Configuracao.query.filter_by(
        estabelecimento_id=(
            dados["vendas_mes"][0].estabelecimento_id if dados["vendas_mes"] else 1
        )
    ).first()
    meta_mensal = config.meta_vendas_mensal if config else 30000

    # Probabilidade de atingir a meta
    projecao_realista = projecoes["cenario_realista"]["projecao_final"]
    probabilidade_meta = (
        min(100, (projecao_realista / meta_mensal * 100)) if meta_mensal > 0 else 0
    )

    # Recomendações baseadas nas projeções
    recomendacoes = []
    if probabilidade_meta < 70:
        recomendacoes.append("Aumente promoções para atingir a meta mensal")
    if projecao_realista < total_mes * 1.1:  # Crescimento mínimo de 10%
        recomendacoes.append("Considere estratégias para incrementar vendas")

    return {
        "dias": {
            "total_mes": dias_no_mes,
            "passados": dias_passados,
            "restantes": dias_restantes,
            "percentual_percorrido": (
                (dias_passados / dias_no_mes * 100) if dias_no_mes > 0 else 0
            ),
        },
        "vendas": {
            "total_ate_hoje": total_mes,
            "media_diaria": media_diaria,
            "necessidade_diaria_restante": (
                (meta_mensal - total_mes) / dias_restantes if dias_restantes > 0 else 0
            ),
        },
        "meta": {
            "valor": meta_mensal,
            "atingido_percentual": (
                (total_mes / meta_mensal * 100) if meta_mensal > 0 else 0
            ),
            "probabilidade_atingir": probabilidade_meta,
            "diferenca": meta_mensal - total_mes,
        },
        "projecoes": projecoes,
        "recomendacoes": recomendacoes,
    }


def gerar_insights_inteligentes(dados, tendencias, projecoes):
    """Gera insights automáticos baseados em análise de dados"""
    insights = []

    # 1. Insight de Vendas
    vendas_hoje = dados["vendas_hoje"]
    total_hoje = sum(v.total for v in vendas_hoje)

    if total_hoje > 0:
        # Comparar com média histórica
        media_30_dias = tendencias.get("media_30_dias", 0)
        if media_30_dias > 0:
            variacao = (total_hoje - media_30_dias) / media_30_dias * 100

            if variacao > 20:
                insights.append(
                    {
                        "tipo": "positivo",
                        "titulo": "🚀 DESTAQUE DO DIA!",
                        "descricao": f"As vendas de hoje estão {variacao:.1f}% acima da média dos últimos 30 dias!",
                        "acao": "Mantenha o ritmo!",
                    }
                )
            elif variacao < -20:
                insights.append(
                    {
                        "tipo": "negativo",
                        "titulo": "⚠️ ATENÇÃO NAS VENDAS",
                        "descricao": f"As vendas de hoje estão {abs(variacao):.1f}% abaixo da média histórica.",
                        "acao": "Verifique promoções e estoque",
                    }
                )

    # 2. Insight de Horário de Pico
    vendas_por_hora = dados["vendas_por_hora"]
    if vendas_por_hora:
        hora_pico = max(vendas_por_hora, key=lambda x: x.total)
        insights.append(
            {
                "tipo": "informacao",
                "titulo": "⏰ HORÁRIO DE PICO IDENTIFICADO",
                "descricao": f"O horário com maior movimento é às {int(hora_pico.hora)}h com R$ {hora_pico.total:,.2f}",
                "acao": "Aumente a equipe neste horário",
            }
        )

    # 3. Insight de Produtos
    produtos_mais_vendidos = dados["produtos_mais_vendidos"]
    if len(produtos_mais_vendidos) >= 3:
        # Verificar se há concentração em poucos produtos
        totais = [p.total_vendido for _, _, p in produtos_mais_vendidos[:3]]
        total_top3 = sum(totais)
        total_todos = sum(p.total_vendido for _, _, p in produtos_mais_vendidos)

        if total_todos > 0:
            concentracao = total_top3 / total_todos * 100
            if concentracao > 60:
                insights.append(
                    {
                        "tipo": "alerta",
                        "titulo": "🎯 CONCENTRAÇÃO DE VENDAS",
                        "descricao": f"Os 3 produtos mais vendidos representam {concentracao:.1f}% do faturamento do mês",
                        "acao": "Diversifique o mix de produtos",
                    }
                )

    # 4. Insight de Clientes
    top_clientes = dados["top_clientes"]
    if top_clientes:
        cliente_top = top_clientes[0]
        insights.append(
            {
                "tipo": "positivo",
                "titulo": "⭐ CLIENTE OURO",
                "descricao": f"{cliente_top[0].nome} já gastou R$ {cliente_top[1]:,.2f} este mês em {cliente_top[2]} compras",
                "acao": "Ofereça benefícios para fidelização",
            }
        )

    # 5. Insight de Meta
    probabilidade_meta = projecoes["meta"].get("probabilidade_atingir", 0)
    if probabilidade_meta > 90:
        insights.append(
            {
                "tipo": "positivo",
                "titulo": "🏆 META EM ALTA PROBABILIDADE",
                "descricao": f"{probabilidade_meta:.0f}% de chance de bater a meta mensal!",
                "acao": "Comemore com a equipe!",
            }
        )
    elif probabilidade_meta < 50:
        insights.append(
            {
                "tipo": "negativo",
                "titulo": "📉 META EM RISCO",
                "descricao": f"Apenas {probabilidade_meta:.0f}% de chance de atingir a meta mensal",
                "acao": "Reuna a equipe para estratégias",
            }
        )

    # 6. Insight de Estoque
    produtos_baixo = dados["produtos_estoque_baixo"]
    if produtos_baixo:
        insights.append(
            {
                "tipo": "critico",
                "titulo": "📦 ESTOQUE BAIXO",
                "descricao": f"{len(produtos_baixo)} produtos estão abaixo do estoque mínimo",
                "acao": "Faça pedido de reposição urgente",
            }
        )

    # 7. Insight de Validade
    produtos_validade = dados["produtos_validade_proxima"]
    if produtos_validade:
        insights.append(
            {
                "tipo": "alerta",
                "titulo": "⏳ VALIDADE PRÓXIMA",
                "descricao": f"{len(produtos_validade)} produtos vencem em breve",
                "acao": "Crie promoções para evitar perda",
            }
        )

    return insights


def calcular_kpis_principais(dados, projecoes):
    """Calcula os KPIs principais para exibição"""
    vendas_hoje = dados["vendas_hoje"]
    vendas_mes = dados["vendas_mes"]
    top_clientes = dados["top_clientes"]

    # Totais
    total_hoje = sum(v.total for v in vendas_hoje)
    total_mes = sum(v.total for v in vendas_mes)

    # Médias
    quantidade_vendas_hoje = len(vendas_hoje)
    ticket_medio_hoje = (
        total_hoje / quantidade_vendas_hoje if quantidade_vendas_hoje > 0 else 0
    )

    quantidade_vendas_mes = len(vendas_mes)
    ticket_medio_mes = (
        total_mes / quantidade_vendas_mes if quantidade_vendas_mes > 0 else 0
    )

    # Clientes únicos hoje
    clientes_hoje = set(v.cliente_id for v in vendas_hoje if v.cliente_id)

    # Valor do cliente top
    valor_cliente_top = top_clientes[0][1] if top_clientes else 0

    # Meta
    config = Configuracao.query.filter_by(
        estabelecimento_id=(
            dados["vendas_mes"][0].estabelecimento_id if dados["vendas_mes"] else 1
        )
    ).first()
    meta_mensal = config.meta_vendas_mensal if config else 30000
    atingimento_meta = (total_mes / meta_mensal * 100) if meta_mensal > 0 else 0

    # Crescimento vs mês passado
    crescimento_mensal = calcular_crescimento_mensal(
        dados["vendas_mes"][0].estabelecimento_id if dados["vendas_mes"] else 1,
        date.today(),
    )

    return {
        "financeiro": {
            "faturamento_hoje": {
                "valor": total_hoje,
                "variacao": f"{calcular_crescimento_diario(dados['vendas_mes'][0].estabelecimento_id if dados['vendas_mes'] else 1, date.today())}%",
                "tendencia": "alta" if total_hoje > 0 else "estavel",
            },
            "faturamento_mes": {
                "valor": total_mes,
                "meta": meta_mensal,
                "atingimento": f"{atingimento_meta:.1f}%",
            },
            "ticket_medio_hoje": ticket_medio_hoje,
            "lucro_estimado": total_mes * 0.30,  # 30% de margem
            "crescimento_mensal": f"{crescimento_mensal}%",
        },
        "operacional": {
            "vendas_hoje": quantidade_vendas_hoje,
            "clientes_hoje": len(clientes_hoje),
            "produtos_vendidos_hoje": sum(len(v.itens) for v in vendas_hoje),
            "hora_pico": obter_hora_pico(dados["vendas_por_hora"]),
        },
        "clientes": {
            "novos_mes": contar_novos_clientes(
                dados["vendas_mes"][0].estabelecimento_id if dados["vendas_mes"] else 1
            ),
            "recorrentes": contar_clientes_recorrentes(
                dados["vendas_mes"][0].estabelecimento_id if dados["vendas_mes"] else 1
            ),
            "fidelidade": calcular_taxa_fidelidade(
                dados["vendas_mes"][0].estabelecimento_id if dados["vendas_mes"] else 1
            ),
            "valor_cliente_top": valor_cliente_top,
        },
        "estoque": {
            "produtos_total": contar_produtos_ativos(
                dados["vendas_mes"][0].estabelecimento_id if dados["vendas_mes"] else 1
            ),
            "valor_estoque": calcular_valor_estoque(
                dados["vendas_mes"][0].estabelecimento_id if dados["vendas_mes"] else 1
            ),
            "produtos_baixo": len(dados["produtos_estoque_baixo"]),
            "produtos_validade": len(dados["produtos_validade_proxima"]),
        },
    }


def gerar_alertas_prioritarios_detalhados(estabelecimento_id):
    """Gera alertas com prioridade para ação imediata"""
    hoje = date.today()
    alertas = []

    # 1. ALERTA CRÍTICO: Estoque zero
    produtos_estoque_zero = (
        Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.quantidade == 0,
            Produto.ativo == True,
        )
        .limit(5)
        .all()
    )

    if produtos_estoque_zero:
        alertas.append(
            {
                "nivel": "critico",
                "icone": "🔥",
                "titulo": "ESTOQUE ESGOTADO",
                "mensagem": f"{len(produtos_estoque_zero)} produtos estão com estoque ZERO",
                "produtos": [p.nome for p in produtos_estoque_zero],
                "acao": "REPOSIÇÃO URGENTE",
                "prioridade": 1,
            }
        )

    # 2. ALERTA ALTO: Validade vencida
    produtos_vencidos = (
        Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.data_validade < hoje,
            Produto.quantidade > 0,
            Produto.ativo == True,
        )
        .limit(5)
        .all()
    )

    if produtos_vencidos:
        alertas.append(
            {
                "nivel": "alto",
                "icone": "⚠️",
                "titulo": "PRODUTOS VENCIDOS",
                "mensagem": f"{len(produtos_vencidos)} produtos estão VENCIDOS",
                "produtos": [p.nome for p in produtos_vencidos],
                "acao": "RETIRAR DO ESTOQUE",
                "prioridade": 2,
            }
        )

    # Ordenar por prioridade
    alertas.sort(key=lambda x: x["prioridade"])
    return alertas


# ==================== FUNÇÕES AUXILIARES ====================


def obter_dados_tempo_real(estabelecimento_id, hoje, acesso_avancado=False):
    """Obtém dados em tempo real para o dashboard"""
    inicio_dia = datetime.combine(hoje, datetime.min.time())
    fim_dia = datetime.combine(hoje, datetime.max.time())
    inicio_mes = datetime(hoje.year, hoje.month, 1)

    # Vendas do dia
    vendas_hoje_query = (
        Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_dia,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada",
        )
        .order_by(Venda.data_venda.desc())
        .limit(20)
        .all()
    )
    
    vendas_hoje = [
        {
            "id": v.id,
            "codigo": v.codigo,
            "cliente": v.cliente.nome if v.cliente else "Consumidor Final",
            "total": float(v.total),
            "forma_pagamento": v.forma_pagamento,
            "data_venda": v.data_venda.isoformat() if v.data_venda else None,
            "status": v.status
        }
        for v in vendas_hoje_query
    ]

    # Produtos com estoque baixo
    produtos_estoque_baixo = [
        {
            "id": p.id,
            "nome": p.nome,
            "quantidade": p.quantidade,
            "quantidade_minima": p.quantidade_minima,
            "categoria": p.categoria
        }
        for p in Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.quantidade <= Produto.quantidade_minima,
            Produto.ativo == True,
        )
        .limit(10)
        .all()
    ]

    # Produtos próximos da validade
    config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()
    dias_alerta = config.dias_alerta_validade if config else 15
    data_alerta = hoje + timedelta(days=dias_alerta)

    produtos_validade_proxima = [
        {
            "id": p.id,
            "nome": p.nome,
            "data_validade": p.data_validade.isoformat() if p.data_validade else None,
            "quantidade": p.quantidade,
            "categoria": p.categoria
        }
        for p in Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.data_validade.between(hoje, data_alerta),
            Produto.quantidade > 0,
            Produto.ativo == True,
        )
        .order_by(Produto.data_validade)
        .limit(10)
        .all()
    ]

    # Vendas por hora (últimas 24 horas)
    hora_inicio = datetime.now() - timedelta(hours=24)

    vendas_por_hora = (
        db.session.query(
            extract("hour", Venda.data_venda).label("hora"),
            func.count(Venda.id).label("quantidade"),
            func.sum(Venda.total).label("total"),
        )
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= hora_inicio,
            Venda.status == "finalizada",
        )
        .group_by(extract("hour", Venda.data_venda))
        .order_by("hora")
        .all()
    )

    # NOVO: Vendas por categoria (mês atual)
    vendas_por_categoria_query = (
        db.session.query(
            Produto.categoria,
            func.sum(VendaItem.total_item).label("total")
        )
        .join(VendaItem, Produto.id == VendaItem.produto_id)
        .join(Venda)
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada"
        )
        .group_by(Produto.categoria)
        .order_by(func.sum(VendaItem.total_item).desc())
        .all()
    )

    vendas_por_categoria = [
        {
            "categoria": cat if cat else "Sem Categoria",
            "total": float(total) if total else 0.0
        }
        for cat, total in vendas_por_categoria_query
    ]

    # NOVO: Vendas últimos 7 dias
    vendas_ultimos_7_dias = []
    for i in range(6, -1, -1):  # 6 dias atrás até hoje
        dia = hoje - timedelta(days=i)
        inicio = datetime.combine(dia, datetime.min.time())
        fim = datetime.combine(dia, datetime.max.time())
        
        total_dia = db.session.query(
            func.sum(Venda.total)
        ).filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda.between(inicio, fim),
            Venda.status == "finalizada"
        ).scalar() or 0
        
        vendas_ultimos_7_dias.append({
            "data": dia.isoformat(),
            "total": float(total_dia)
        })

    # NOVO: Clientes novos do mês
    clientes_novos_mes = Cliente.query.filter(
        Cliente.estabelecimento_id == estabelecimento_id,
        Cliente.data_cadastro >= inicio_mes
    ).count()

    return {
        "vendas_hoje": vendas_hoje,
        "estoque_baixo": produtos_estoque_baixo,
        "validade_proxima": produtos_validade_proxima,
        "vendas_por_hora": [
            {
                "hora": int(vph.hora),
                "quantidade": vph.quantidade,
                "total": float(vph.total) if vph.total else 0,
            }
            for vph in vendas_por_hora
        ],
        "vendas_por_categoria": vendas_por_categoria,
        "vendas_ultimos_7_dias": vendas_ultimos_7_dias,
        "clientes_novos_mes": clientes_novos_mes,
        "ultimas_vendas": vendas_hoje[:10],
    }


def calcular_top_produtos_avancado(estabelecimento_id, inicio, fim, limite=10):
    """Calcula top produtos com métricas avançadas"""
    produtos = (
        db.session.query(
            VendaItem.produto_id,
            VendaItem.produto_nome,
            func.sum(VendaItem.quantidade).label("quantidade_total"),
            func.sum(VendaItem.total_item).label("total_vendido"),
            func.avg(VendaItem.preco_unitario).label("preco_medio"),
            func.count(func.distinct(Venda.id)).label("frequencia_vendas"),
            label(
                "margem_contribuicao", func.sum(VendaItem.total_item) * 0.3
            ),  # Exemplo: 30% de margem
        )
        .join(Venda)
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio,
            Venda.data_venda <= fim,
            Venda.status == "finalizada",
        )
        .group_by(VendaItem.produto_id, VendaItem.produto_nome)
        .order_by(func.sum(VendaItem.total_item).desc())
        .limit(limite)
        .all()
    )

    return [
        {
            "produto_id": p.produto_id,
            "nome": p.produto_nome,
            "quantidade_total": int(p.quantidade_total),
            "total_vendido": float(p.total_vendido) if p.total_vendido else 0,
            "preco_medio": float(p.preco_medio) if p.preco_medio else 0,
            "frequencia_vendas": p.frequencia_vendas,
            "margem_estimada": (
                float(p.margem_contribuicao) if p.margem_contribuicao else 0
            ),
        }
        for p in produtos
    ]


def analisar_vendas_por_hora(vendas):
    """Analisa padrão de vendas por hora"""
    horas = defaultdict(lambda: {"quantidade": 0, "total": 0.0, "ticket_medio": 0.0})

    for venda in vendas:
        hora = venda.data_venda.hour
        horas[hora]["quantidade"] += 1
        horas[hora]["total"] += float(venda.total)

    # Calcular ticket médio por hora
    for hora in horas:
        if horas[hora]["quantidade"] > 0:
            horas[hora]["ticket_medio"] = (
                horas[hora]["total"] / horas[hora]["quantidade"]
            )

    return dict(horas)


def calcular_clv(estabelecimento_id, periodo_dias=90):
    """Calcula Customer Lifetime Value"""
    data_limite = date.today() - timedelta(days=periodo_dias)

    resultado = (
        db.session.query(
            Venda.cliente_id,
            func.count(Venda.id).label("frequencia"),
            func.avg(Venda.total).label("valor_medio"),
            func.sum(Venda.total).label("valor_total"),
        )
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= data_limite,
            Venda.status == "finalizada",
            Venda.cliente_id.isnot(None),
        )
        .group_by(Venda.cliente_id)
        .all()
    )

    if not resultado:
        return 0

    valores_clv = []
    for r in resultado:
        clv = (r.valor_medio or 0) * (r.frequencia or 1) * 0.3 * 12
        valores_clv.append(clv)

    return sum(valores_clv) / len(valores_clv) if valores_clv else 0


def segmentar_clientes(estabelecimento_id):
    """Segmenta clientes usando análise RFM"""
    data_limite = date.today() - timedelta(days=90)

    clientes_rfm = (
        db.session.query(
            Venda.cliente_id,
            label("recencia", func.max(Venda.data_venda)),
            label("frequencia", func.count(Venda.id)),
            label("valor_monetario", func.sum(Venda.total)),
        )
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= data_limite,
            Venda.status == "finalizada",
            Venda.cliente_id.isnot(None),
        )
        .group_by(Venda.cliente_id)
        .all()
    )

    segmentos = {
        "champions": [],
        "loyal": [],
        "potential": [],
        "new": [],
        "at_risk": [],
        "lost": [],
    }

    for cliente in clientes_rfm:
        dias_recencia = (date.today() - cliente.recencia.date()).days

        if dias_recencia <= 7 and cliente.frequencia >= 10:
            segmentos["champions"].append(cliente.cliente_id)
        elif dias_recencia <= 30 and cliente.frequencia >= 5:
            segmentos["loyal"].append(cliente.cliente_id)
        elif dias_recencia <= 90 and cliente.frequencia >= 2:
            segmentos["potential"].append(cliente.cliente_id)
        elif dias_recencia <= 7:
            segmentos["new"].append(cliente.cliente_id)
        elif dias_recencia <= 180:
            segmentos["at_risk"].append(cliente.cliente_id)
        else:
            segmentos["lost"].append(cliente.cliente_id)

    return {
        "total_clientes": sum(len(v) for v in segmentos.values()),
        "segmentos": segmentos,
    }


def gerar_previsoes(estabelecimento_id, dias_previsao=7):
    """Gera previsões de vendas usando média móvel"""
    data_inicio = date.today() - timedelta(days=30)

    historico = (
        db.session.query(
            func.date(Venda.data_venda).label("data"),
            func.sum(Venda.total).label("total"),
        )
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= data_inicio,
            Venda.status == "finalizada",
        )
        .group_by(func.date(Venda.data_venda))
        .order_by(func.date(Venda.data_venda))
        .all()
    )

    if len(historico) < 7:
        return {"previsao": [], "confianca": 0}

    series = [float(h.total) for h in historico]
    previsao = calcular_moving_average(series, window=7, forecast_days=dias_previsao)

    datas_previsao = [
        date.today() + timedelta(days=i + 1) for i in range(dias_previsao)
    ]

    return {
        "previsao": [
            {"data": d.isoformat(), "valor": float(p)}
            for d, p in zip(datas_previsao, previsao)
        ],
        "confianca": calcular_confianca_previsao(series, previsao),
        "tendencia": calcular_tendencia(series),
    }


def analisar_cross_selling(estabelecimento_id):
    """Analisa padrões de cross-selling entre produtos"""
    query = text(
        """
        SELECT 
            p1.nome as produto1,
            p2.nome as produto2,
            COUNT(*) as frequencia
        FROM venda_item vi1
        JOIN venda_item vi2 ON vi1.venda_id = vi2.venda_id 
            AND vi1.produto_id < vi2.produto_id
        JOIN produto p1 ON vi1.produto_id = p1.id
        JOIN produto p2 ON vi2.produto_id = p2.id
        JOIN venda v ON vi1.venda_id = v.id
        WHERE v.estabelecimento_id = :estabelecimento_id
            AND v.status = 'finalizada'
            AND v.data_venda >= date('now', '-30 days')
        GROUP BY vi1.produto_id, vi2.produto_id
        HAVING frequencia >= 5
        ORDER BY frequencia DESC
        LIMIT 10
    """
    )

    resultado = db.session.execute(query, {"estabelecimento_id": estabelecimento_id})

    return [
        {
            "produto1": row.produto1,
            "produto2": row.produto2,
            "frequencia": row.frequencia,
            "suporte": row.frequencia / 100,
        }
        for row in resultado
    ]


def identificar_produtos_estrela(estabelecimento_id):
    """Identifica produtos estrela usando matriz BCG"""
    produtos = (
        db.session.query(
            Produto.id,
            Produto.nome,
            label("crescimento", func.sum(VendaItem.quantidade)),
            label(
                "market_share",
                func.sum(VendaItem.quantidade)
                / func.sum(func.sum(VendaItem.quantidade)).over()
                * 100,
            ),
        )
        .join(VendaItem, Produto.id == VendaItem.produto_id)
        .join(Venda, VendaItem.venda_id == Venda.id)
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= date.today() - timedelta(days=90),
            Venda.status == "finalizada",
        )
        .group_by(Produto.id, Produto.nome)
        .all()
    )

    estrelas = []
    for p in produtos:
        if p.crescimento > 50 and p.market_share > 5:
            estrelas.append(
                {
                    "produto_id": p.id,
                    "nome": p.nome,
                    "crescimento": float(p.crescimento),
                    "market_share": float(p.market_share),
                }
            )

    return estrelas[:5]


def gerar_insights_automaticos(estabelecimento_id, metrica):
    """Gera insights automáticos baseados em dados"""
    insights = []

    if metrica.vendas_por_hora_json:
        vendas_hora = json.loads(metrica.vendas_por_hora_json)

        # `analisar_vendas_por_hora` pode retornar dict vazio quando não há vendas.
        # Também tolera formatos inesperados para evitar 500 no dashboard.
        if isinstance(vendas_hora, dict) and vendas_hora:
            hora_pico = max(
                vendas_hora.items(),
                key=lambda item: (
                    (item[1] or {}).get("quantidade", 0)
                    if isinstance(item[1], dict)
                    else 0
                ),
            )[0]
            insights.append(
                f"🚀 **Horário de Pico**: {hora_pico}:00h - Considere aumentar a equipe neste horário"
            )

    if metrica.ticket_medio_dia < 50:
        insights.append(
            "💰 **Oportunidade de Upsell**: Ticket médio baixo - Considere treinar a equipe para venda cruzada"
        )

    produtos_lentos = identificar_produtos_lentos(estabelecimento_id)
    if produtos_lentos:
        insights.append(
            f"📦 **Estoque Parado**: {len(produtos_lentos)} produtos com baixa movimentação - Considere promoções"
        )

    return insights


def calcular_crescimento_diario(estabelecimento_id, data):
    """Calcula crescimento vs dia anterior"""
    ontem = data - timedelta(days=1)

    hoje_total = (
        db.session.query(func.sum(Venda.total))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            func.date(Venda.data_venda) == data,
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    ontem_total = (
        db.session.query(func.sum(Venda.total))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            func.date(Venda.data_venda) == ontem,
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    if ontem_total == 0:
        return 100 if hoje_total > 0 else 0

    return round(((hoje_total - ontem_total) / ontem_total) * 100, 2)


def calcular_crescimento_mensal(estabelecimento_id, data):
    """Calcula crescimento vs mês anterior"""
    inicio_mes_atual = datetime(data.year, data.month, 1)
    if data.month == 1:
        inicio_mes_anterior = datetime(data.year - 1, 12, 1)
    else:
        inicio_mes_anterior = datetime(data.year, data.month - 1, 1)

    fim_mes_anterior = inicio_mes_atual - timedelta(days=1)

    mes_atual_total = (
        db.session.query(func.sum(Venda.total))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes_atual,
            Venda.data_venda <= datetime.combine(data, datetime.max.time()),
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    mes_anterior_total = (
        db.session.query(func.sum(Venda.total))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes_anterior,
            Venda.data_venda <= fim_mes_anterior,
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    if mes_anterior_total == 0:
        return 100 if mes_atual_total > 0 else 0

    return round(((mes_atual_total - mes_anterior_total) / mes_anterior_total) * 100, 2)


def identificar_top_clientes(estabelecimento_id, limite=10):
    """Identifica os melhores clientes"""
    inicio_mes = datetime(date.today().year, date.today().month, 1)

    top_clientes = (
        db.session.query(
            Cliente.id,
            Cliente.nome,
            func.sum(Venda.total).label("total_gasto"),
            func.count(Venda.id).label("quantidade_compras"),
            func.max(Venda.data_venda).label("ultima_compra"),
        )
        .join(Venda, Cliente.id == Venda.cliente_id)
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes,
            Venda.status == "finalizada",
        )
        .group_by(Cliente.id, Cliente.nome)
        .order_by(func.sum(Venda.total).desc())
        .limit(limite)
        .all()
    )

    return [
        {
            "cliente_id": c.id,
            "nome": c.nome,
            "total_gasto": float(c.total_gasto),
            "quantidade_compras": c.quantidade_compras,
            "ultima_compra": c.ultima_compra.isoformat() if c.ultima_compra else None,
        }
        for c in top_clientes
    ]


def calcular_taxa_churn(estabelecimento_id):
    """Calcula taxa de churn de clientes"""
    data_limite = date.today() - timedelta(days=90)

    total_clientes = (
        db.session.query(func.count(func.distinct(Venda.cliente_id)))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= date.today() - timedelta(days=180),
            Venda.status == "finalizada",
            Venda.cliente_id.isnot(None),
        )
        .scalar()
        or 0
    )

    clientes_inativos = (
        db.session.query(func.count(func.distinct(Venda.cliente_id)))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda < data_limite,
            Venda.status == "finalizada",
            Venda.cliente_id.isnot(None),
        )
        .scalar()
        or 0
    )

    if total_clientes == 0:
        return 0

    return round((clientes_inativos / total_clientes) * 100, 2)


def calcular_taxa_repeticao(estabelecimento_id):
    """Calcula taxa de clientes recorrentes"""
    data_limite = date.today() - timedelta(days=30)

    clientes_totais = (
        db.session.query(func.count(func.distinct(Venda.cliente_id)))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= data_limite,
            Venda.status == "finalizada",
            Venda.cliente_id.isnot(None),
        )
        .scalar()
        or 0
    )

    clientes_recorrentes = (
        db.session.query(Venda.cliente_id, func.count(Venda.id).label("compras"))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= data_limite,
            Venda.status == "finalizada",
            Venda.cliente_id.isnot(None),
        )
        .group_by(Venda.cliente_id)
        .having(func.count(Venda.id) > 1)
        .count()
    )

    if clientes_totais == 0:
        return 0

    return round((clientes_recorrentes / clientes_totais) * 100, 2)


def calcular_taxa_conversao(estabelecimento_id):
    """Calcula taxa de conversão (simplificada)"""
    # Esta é uma versão simplificada - em um sistema real,
    # você teria dados de visitantes/tentativas de compra
    total_vendas = (
        db.session.query(func.count(Venda.id))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= date.today() - timedelta(days=7),
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    # Estimativa: assumindo 10x mais visitas do que vendas
    visitas_estimadas = total_vendas * 10

    if visitas_estimadas == 0:
        return 0

    return round((total_vendas / visitas_estimadas) * 100, 2)


def comparar_com_ontem(estabelecimento_id):
    """Compara com o dia anterior"""
    hoje = date.today()
    ontem = hoje - timedelta(days=1)

    hoje_total = (
        db.session.query(func.sum(Venda.total))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            func.date(Venda.data_venda) == hoje,
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    ontem_total = (
        db.session.query(func.sum(Venda.total))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            func.date(Venda.data_venda) == ontem,
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    return {
        "hoje": hoje_total,
        "ontem": ontem_total,
        "variacao": calcular_crescimento_diario(estabelecimento_id, hoje),
        "tendencia": "alta" if hoje_total > ontem_total else "baixa",
    }


def comparar_com_semana_passada(estabelecimento_id):
    """Compara com a semana passada"""
    hoje = date.today()
    semana_atual_inicio = hoje - timedelta(days=hoje.weekday())
    semana_anterior_inicio = semana_atual_inicio - timedelta(days=7)
    semana_anterior_fim = semana_atual_inicio - timedelta(days=1)

    semana_atual_total = (
        db.session.query(func.sum(Venda.total))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= semana_atual_inicio,
            Venda.data_venda <= datetime.combine(hoje, datetime.max.time()),
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    semana_anterior_total = (
        db.session.query(func.sum(Venda.total))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= semana_anterior_inicio,
            Venda.data_venda
            <= datetime.combine(semana_anterior_fim, datetime.max.time()),
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    if semana_anterior_total == 0:
        variacao = 100 if semana_atual_total > 0 else 0
    else:
        variacao = round(
            ((semana_atual_total - semana_anterior_total) / semana_anterior_total)
            * 100,
            2,
        )

    return {
        "semana_atual": semana_atual_total,
        "semana_anterior": semana_anterior_total,
        "variacao": variacao,
        "tendencia": "alta" if semana_atual_total > semana_anterior_total else "baixa",
    }


def calcular_projecoes(estabelecimento_id, hoje):
    """Calcula projeções simplificadas"""
    inicio_mes = datetime(hoje.year, hoje.month, 1)

    vendas_mes = Venda.query.filter(
        Venda.estabelecimento_id == estabelecimento_id,
        Venda.data_venda >= inicio_mes,
        Venda.data_venda <= datetime.combine(hoje, datetime.max.time()),
        Venda.status == "finalizada",
    ).all()

    total_mes = sum(v.total for v in vendas_mes)

    # Dias do mês
    if hoje.month == 12:
        fim_mes = datetime(hoje.year + 1, 1, 1) - timedelta(days=1)
    else:
        fim_mes = datetime(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

    dias_no_mes = (fim_mes.date() - inicio_mes.date()).days + 1
    dias_passados = (hoje - inicio_mes.date()).days + 1
    dias_restantes = dias_no_mes - dias_passados

    # Média diária
    if dias_passados > 0:
        media_diaria = total_mes / dias_passados
    else:
        media_diaria = 0

    # Projeção
    projecao = total_mes + (media_diaria * dias_restantes)

    return {
        "total_ate_hoje": total_mes,
        "media_diaria": media_diaria,
        "dias_restantes": dias_restantes,
        "projecao_mes": projecao,
        "dias_passados": dias_passados,
        "percentual_percorrido": (
            (dias_passados / dias_no_mes * 100) if dias_no_mes > 0 else 0
        ),
    }


def gerar_resumo_executivo(estabelecimento_id, hoje):
    """Gera resumo executivo"""
    inicio_dia = datetime.combine(hoje, datetime.min.time())

    total_hoje = (
        db.session.query(func.sum(Venda.total))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_dia,
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    clientes_hoje = (
        db.session.query(func.count(func.distinct(Venda.cliente_id)))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_dia,
            Venda.status == "finalizada",
        )
        .scalar()
        or 0
    )

    produtos_estoque_zero = Produto.query.filter(
        Produto.estabelecimento_id == estabelecimento_id,
        Produto.quantidade == 0,
        Produto.ativo == True,
    ).count()

    config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()
    meta_diaria = config.meta_vendas_diaria if config else 1000

    return {
        "faturamento_hoje": float(total_hoje),
        "clientes_hoje": clientes_hoje,
        "alertas_criticos": produtos_estoque_zero,
        "meta_diaria": meta_diaria,
        "atingimento_meta": (total_hoje / meta_diaria * 100) if meta_diaria > 0 else 0,
        "status": "NORMAL" if produtos_estoque_zero == 0 else "ATENÇÃO",
    }


def obter_decisao_do_dia(faturamento_hoje, produtos_estoque_zero, meta_diaria):
    """Retorna a decisão mais importante do dia baseada nos dados"""
    if produtos_estoque_zero > 0:
        return {
            "prioridade": "ALTA",
            "titulo": "⚠️ REPOSIÇÃO DE ESTOQUE URGENTE",
            "descricao": f"{produtos_estoque_zero} produtos estão sem estoque",
            "acao": "Faça pedidos de reposição imediatamente",
        }
    elif faturamento_hoje < meta_diaria * 0.5:  # Menos de 50% da meta
        return {
            "prioridade": "MÉDIA",
            "titulo": "📊 VENDAS ABAIXO DA META DIÁRIA",
            "descricao": f"Faturamento de R$ {faturamento_hoje:,.2f} está abaixo do esperado",
            "acao": "Ative promoções relâmpago para aumentar vendas",
        }
    elif faturamento_hoje > meta_diaria * 1.5:  # Mais de 150% da meta
        return {
            "prioridade": "BAIXA",
            "titulo": "🎉 DIA EXCELENTE!",
            "descricao": f"Faturamento de R$ {faturamento_hoje:,.2f} superou expectativas",
            "acao": "Recompense a equipe e analise o que deu certo",
        }
    else:
        return {
            "prioridade": "BAIXA",
            "titulo": "✅ OPERAÇÃO NORMAL",
            "descricao": "Tudo funcionando dentro do esperado",
            "acao": "Foque em melhorias de processos",
        }


def gerar_recomendacoes_tendencia(slope, crescimento_semanal):
    """Gera recomendações baseadas na tendência identificada"""
    recomendacoes = []

    if slope > 100:
        recomendacoes.append("✅ Tendência de CRESCIMENTO FORTE identificada")
        recomendacoes.append("💡 Considere aumentar estoque dos produtos mais vendidos")
        recomendacoes.append("🎯 Mantenha as estratégias que estão funcionando")
    elif slope > 0:
        recomendacoes.append("📈 Tendência de CRESCIMENTO MODERADO")
        recomendacoes.append("🔍 Analise quais produtos estão puxando o crescimento")
        recomendacoes.append("💰 Otimize promoções para acelerar o crescimento")
    elif slope == 0:
        recomendacoes.append("⚖️ Tendência de ESTABILIDADE")
        recomendacoes.append("🔄 Considere renovar o mix de produtos")
        recomendacoes.append("🎪 Crie eventos ou promoções para gerar movimento")
    else:
        recomendacoes.append("⚠️ Tendência de DECRESCIMENTO identificada")
        recomendacoes.append("🚨 Reveja estratégias de preço e promoção")
        recomendacoes.append("📊 Analise concorrência e preferências dos clientes")

    if crescimento_semanal > 10:
        recomendacoes.append(
            f"🚀 Crescimento semanal de {crescimento_semanal:.1f}% - EXCELENTE!"
        )
    elif crescimento_semanal < -5:
        recomendacoes.append(
            f"📉 Queda semanal de {abs(crescimento_semanal):.1f}% - ATENÇÃO!"
        )

    return recomendacoes


# ==================== FUNÇÕES AUXILIARES DE KPIs ====================


def obter_hora_pico(vendas_por_hora):
    """Retorna a hora de pico"""
    if not vendas_por_hora:
        return "N/A"

    hora_pico = max(vendas_por_hora, key=lambda x: x.total)
    return f"{int(hora_pico.hora)}h-{int(hora_pico.hora)+1}h"


def contar_novos_clientes(estabelecimento_id):
    """Conta novos clientes no mês"""
    inicio_mes = datetime(date.today().year, date.today().month, 1)

    return (
        db.session.query(func.count(func.distinct(Venda.cliente_id)))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes,
            Venda.status == "finalizada",
            Venda.cliente_id.isnot(None),
            ~Cliente.id.in_(
                db.session.query(Venda.cliente_id)
                .filter(
                    Venda.estabelecimento_id == estabelecimento_id,
                    Venda.data_venda < inicio_mes,
                    Venda.status == "finalizada",
                )
                .subquery()
            ),
        )
        .scalar()
        or 0
    )


def contar_clientes_recorrentes(estabelecimento_id):
    """Conta clientes recorrentes"""
    data_limite = date.today() - timedelta(days=30)

    return (
        db.session.query(Venda.cliente_id)
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= data_limite,
            Venda.status == "finalizada",
            Venda.cliente_id.isnot(None),
        )
        .group_by(Venda.cliente_id)
        .having(func.count(Venda.id) > 1)
        .count()
    )


def calcular_taxa_fidelidade(estabelecimento_id):
    """Calcula taxa de fidelidade"""
    total_clientes = (
        db.session.query(func.count(func.distinct(Venda.cliente_id)))
        .filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= date.today() - timedelta(days=30),
            Venda.status == "finalizada",
            Venda.cliente_id.isnot(None),
        )
        .scalar()
        or 0
    )

    clientes_recorrentes = contar_clientes_recorrentes(estabelecimento_id)

    if total_clientes == 0:
        return "0%"

    return f"{(clientes_recorrentes / total_clientes * 100):.1f}%"


def contar_produtos_ativos(estabelecimento_id):
    """Conta produtos ativos"""
    return Produto.query.filter(
        Produto.estabelecimento_id == estabelecimento_id, Produto.ativo == True
    ).count()


def calcular_valor_estoque(estabelecimento_id):
    """Calcula valor total do estoque"""
    produtos = Produto.query.filter(
        Produto.estabelecimento_id == estabelecimento_id, Produto.ativo == True
    ).all()

    return sum(p.quantidade * p.preco_custo for p in produtos)


def identificar_produtos_lentos(estabelecimento_id):
    """Identifica produtos com baixa movimentação"""
    data_limite = date.today() - timedelta(days=90)

    produtos_lentos = (
        db.session.query(Produto)
        .outerjoin(VendaItem, Produto.id == VendaItem.produto_id)
        .outerjoin(Venda, VendaItem.venda_id == Venda.id)
        .filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.ativo == True,
            or_(Venda.data_venda < data_limite, Venda.id.is_(None)),
        )
        .group_by(Produto.id)
        .having(
            func.sum(VendaItem.quantidade).is_(None)
            | (func.sum(VendaItem.quantidade) < 10)
        )
        .limit(10)
        .all()
    )

    return [
        {"id": p.id, "nome": p.nome, "quantidade": p.quantidade, "ultima_venda": None}
        for p in produtos_lentos
    ]


def calcular_confianca_previsao(series_historica, previsao):
    """Calcula confiança da previsão"""
    if len(series_historica) < 7:
        return 0

    # Cálculo simplificado da confiança
    variacao = (
        np.std(series_historica) / np.mean(series_historica)
        if np.mean(series_historica) > 0
        else 1
    )
    confianca = max(0, 100 - (variacao * 100))

    return round(min(confianca, 100), 2)


# ==================== ROTAS ADICIONAIS PARA GRÁFICOS ====================


@dashboard_bp.route("/vendas-periodo", methods=["GET"])
@funcionario_required
def vendas_por_periodo():
    """Retorna vendas agregadas por período para gráficos"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)

        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        estabelecimento_id = funcionario.estabelecimento_id
        periodo = request.args.get("periodo", "dia")
        dias = int(request.args.get("dias", 7))
        incluir_tendencia = (
            request.args.get("incluir_tendencia", "true").lower() == "true"
        )

        hoje = date.today()
        data_inicio = hoje - timedelta(days=dias - 1)

        resultados = []
        totais_diarios = []

        if periodo == "dia":
            for i in range(dias):
                data_atual = data_inicio + timedelta(days=i)
                inicio_dia = datetime.combine(data_atual, datetime.min.time())
                fim_dia = datetime.combine(data_atual, datetime.max.time())

                vendas_dia = Venda.query.filter(
                    Venda.estabelecimento_id == estabelecimento_id,
                    Venda.data_venda >= inicio_dia,
                    Venda.data_venda <= fim_dia,
                    Venda.status == "finalizada",
                ).all()

                total_dia = sum(v.total for v in vendas_dia)
                quantidade_dia = len(vendas_dia)
                ticket_medio = total_dia / quantidade_dia if quantidade_dia > 0 else 0

                totais_diarios.append(total_dia)

                resultados.append(
                    {
                        "data": data_atual.isoformat(),
                        "total": total_dia,
                        "quantidade": quantidade_dia,
                        "ticket_medio": ticket_medio,
                        "dia_semana": data_atual.strftime("%A"),
                        "clientes_unicos": len(
                            set(v.cliente_id for v in vendas_dia if v.cliente_id)
                        ),
                    }
                )

        # Calcular tendência se solicitado
        if incluir_tendencia and len(totais_diarios) >= 3:
            tendencia = calcular_tendencia(totais_diarios)
            resultados.append(
                {
                    "analise": {
                        "tendencia": tendencia["direcao"],
                        "inclinacao": tendencia["inclinacao"],
                        "r_quadrado": tendencia["r_quadrado"],
                        "previsao_amanha": tendencia["previsao"],
                    }
                }
            )

        return (
            jsonify(
                {
                    "success": True,
                    "periodo": periodo,
                    "dias": dias,
                    "data": resultados,
                    "estatisticas": {
                        "media_diaria": (
                            sum(totais_diarios) / len(totais_diarios)
                            if totais_diarios
                            else 0
                        ),
                        "desvio_padrao": (
                            np.std(totais_diarios) if totais_diarios else 0
                        ),
                        "maximo": max(totais_diarios) if totais_diarios else 0,
                        "minimo": min(totais_diarios) if totais_diarios else 0,
                        "crescimento_total": (
                            (
                                (totais_diarios[-1] - totais_diarios[0])
                                / totais_diarios[0]
                                * 100
                            )
                            if totais_diarios and totais_diarios[0] > 0
                            else 0
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao obter vendas por período: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao obter vendas por período",
                    "message": str(e),
                }
            ),
            500,
        )


@dashboard_bp.route("/analise-preditiva", methods=["GET"])
@admin_required
def analise_preditiva():
    """Análise preditiva avançada"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)

        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        estabelecimento_id = funcionario.estabelecimento_id

        # Previsão de demanda
        previsao_demanda = prever_demanda_produtos(estabelecimento_id)

        # Análise de sazonalidade
        sazonalidade = analisar_sazonalidade_detalhada(estabelecimento_id)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "previsao_demanda": previsao_demanda,
                        "sazonalidade": sazonalidade,
                        "recomendacoes": gerar_recomendacoes_predicao(
                            previsao_demanda, sazonalidade
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro na análise preditiva: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro na análise preditiva",
                    "message": str(e),
                }
            ),
            500,
        )


# ==================== FUNÇÕES STUB (PARA IMPLEMENTAÇÃO FUTURA) ====================


def calcular_despesas_mes(estabelecimento_id, inicio_mes, fim_dia):
    """Calcula despesas do mês usando a tabela de despesas."""
    try:
        inicio_date = inicio_mes.date() if hasattr(inicio_mes, "date") else inicio_mes
        fim_date = fim_dia.date() if hasattr(fim_dia, "date") else fim_dia

        total = (
            db.session.query(func.coalesce(func.sum(Despesa.valor), 0.0))
            .filter(
                Despesa.estabelecimento_id == estabelecimento_id,
                Despesa.data_despesa >= inicio_date,
                Despesa.data_despesa <= fim_date,
            )
            .scalar()
        )

        return float(total or 0.0)

    except Exception as e:
        current_app.logger.error(f"Erro ao calcular despesas do mês: {str(e)}")
        return 0.0


def prever_demanda_produtos(estabelecimento_id):
    """Previsão simples de demanda por produto baseada em histórico recente.

    Estratégia (v1):
    - Usa os últimos 60 dias de vendas finalizadas.
    - Seleciona os produtos com maior quantidade vendida.
    - Para cada produto, calcula série diária e prevê 7 dias via média móvel.
    """
    try:
        hoje = date.today()
        inicio = hoje - timedelta(days=60)

        # Quantidade vendida por produto no período (para escolher top N)
        top_produtos = (
            db.session.query(
                VendaItem.produto_id.label("produto_id"),
                func.sum(VendaItem.quantidade).label("qtd"),
            )
            .join(Venda, Venda.id == VendaItem.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.status == "finalizada",
                Venda.data_venda >= inicio,
            )
            .group_by(VendaItem.produto_id)
            .order_by(func.sum(VendaItem.quantidade).desc())
            .limit(20)
            .all()
        )

        if not top_produtos:
            return {
                "periodo_dias": 60,
                "forecast_dias": 7,
                "produtos": [],
                "observacao": "Sem vendas suficientes para previsão",
            }

        produto_ids = [int(p.produto_id) for p in top_produtos if p.produto_id]

        # Série diária por produto
        vendas_diarias = (
            db.session.query(
                VendaItem.produto_id.label("produto_id"),
                func.date(Venda.data_venda).label("data"),
                func.sum(VendaItem.quantidade).label("quantidade"),
            )
            .join(Venda, Venda.id == VendaItem.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.status == "finalizada",
                Venda.data_venda >= inicio,
                VendaItem.produto_id.in_(produto_ids),
            )
            .group_by(VendaItem.produto_id, func.date(Venda.data_venda))
            .all()
        )

        # Indexar por produto -> {data: qtd}
        por_produto = defaultdict(dict)
        for row in vendas_diarias:
            if not row.produto_id or not row.data:
                continue
            por_produto[int(row.produto_id)][row.data] = int(row.quantidade or 0)

        produtos = Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.id.in_(produto_ids),
        ).all()
        produtos_map = {int(p.id): p for p in produtos}

        datas = [inicio + timedelta(days=i) for i in range((hoje - inicio).days + 1)]

        previsoes = []
        for produto_id in produto_ids:
            produto = produtos_map.get(int(produto_id))
            if not produto:
                continue

            serie = [float(por_produto[produto_id].get(d, 0)) for d in datas]
            forecast = calcular_moving_average(serie, window=7, forecast_days=7)
            forecast_7d = [float(x) for x in forecast[-7:]] if forecast else [0.0] * 7

            demanda_diaria_prevista = float(np.mean(forecast_7d)) if forecast_7d else 0.0
            estoque_atual = int(produto.quantidade or 0)

            previsoes.append(
                {
                    "produto_id": int(produto.id),
                    "produto_nome": produto.nome,
                    "estoque_atual": estoque_atual,
                    "demanda_diaria_prevista": round(demanda_diaria_prevista, 2),
                    "previsao_7_dias": [round(v, 2) for v in forecast_7d],
                    "risco_ruptura": estoque_atual < (demanda_diaria_prevista * 7),
                }
            )

        return {
            "periodo_dias": 60,
            "forecast_dias": 7,
            "produtos": previsoes,
        }

    except Exception as e:
        current_app.logger.error(f"Erro ao prever demanda de produtos: {str(e)}")
        return {"status": "erro", "message": str(e)}


def analisar_sazonalidade_detalhada(estabelecimento_id):
    """Análise detalhada de sazonalidade (v1).

    Retorna um heatmap simples (dia da semana x hora) usando os últimos 90 dias.
    """
    try:
        hoje = date.today()
        inicio = hoje - timedelta(days=90)

        rows = (
            db.session.query(
                extract("dow", Venda.data_venda).label("dow"),
                extract("hour", Venda.data_venda).label("hour"),
                func.sum(Venda.total).label("total"),
                func.count(Venda.id).label("quantidade"),
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.status == "finalizada",
                Venda.data_venda >= inicio,
            )
            .group_by(extract("dow", Venda.data_venda), extract("hour", Venda.data_venda))
            .all()
        )

        # heatmap[dow][hour] = {total, quantidade}
        heatmap = {str(d): {str(h): {"total": 0.0, "quantidade": 0} for h in range(24)} for d in range(7)}
        for r in rows:
            d = int(r.dow) if r.dow is not None else 0
            h = int(r.hour) if r.hour is not None else 0
            heatmap[str(d)][str(h)] = {
                "total": float(r.total or 0.0),
                "quantidade": int(r.quantidade or 0),
            }

        return {
            "periodo_dias": 90,
            "heatmap_dow_hora": heatmap,
        }

    except Exception as e:
        current_app.logger.error(f"Erro na sazonalidade detalhada: {str(e)}")
        return {"status": "erro", "message": str(e)}


def gerar_recomendacoes_predicao(previsao_demanda, sazonalidade):
    """Gera recomendações baseadas em predições"""
    try:
        recomendacoes = []

        produtos = (previsao_demanda or {}).get("produtos", [])
        if produtos:
            riscos = [p for p in produtos if p.get("risco_ruptura")]
            if riscos:
                top_risco = sorted(
                    riscos,
                    key=lambda p: (p.get("demanda_diaria_prevista", 0) - (p.get("estoque_atual", 0) / 7)),
                    reverse=True,
                )
                recomendacoes.append(
                    f"Repor estoque: {min(5, len(top_risco))} produto(s) com risco de ruptura nos próximos 7 dias"
                )

        if not recomendacoes:
            recomendacoes.append("Sem recomendações críticas no momento")

        return recomendacoes

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar recomendações: {str(e)}")
        return ["Erro ao gerar recomendações"]


def analisar_sazonalidade(estabelecimento_id):
    """Análise de sazonalidade (v1) com agregações semanais e mensais."""
    try:
        hoje = date.today()
        inicio = hoje - timedelta(days=180)

        # Padrão semanal (0=domingo no Postgres; no SQLite costuma seguir 0=domingo também via strftime)
        semanal_rows = (
            db.session.query(
                extract("dow", Venda.data_venda).label("dow"),
                func.sum(Venda.total).label("total"),
                func.count(Venda.id).label("quantidade"),
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.status == "finalizada",
                Venda.data_venda >= inicio,
            )
            .group_by(extract("dow", Venda.data_venda))
            .all()
        )

        padrao_semanal = {
            str(int(r.dow)): {
                "total": float(r.total or 0.0),
                "quantidade": int(r.quantidade or 0),
            }
            for r in semanal_rows
        }

        # Sazonalidade mensal
        mensal_rows = (
            db.session.query(
                extract("month", Venda.data_venda).label("mes"),
                func.sum(Venda.total).label("total"),
                func.count(Venda.id).label("quantidade"),
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.status == "finalizada",
                Venda.data_venda >= inicio,
            )
            .group_by(extract("month", Venda.data_venda))
            .all()
        )

        sazonalidade_mensal = {
            str(int(r.mes)): {
                "total": float(r.total or 0.0),
                "quantidade": int(r.quantidade or 0),
            }
            for r in mensal_rows
        }

        return {
            "periodo_dias": 180,
            "padrao_semanal": padrao_semanal,
            "sazonalidade_mensal": sazonalidade_mensal,
        }

    except Exception as e:
        current_app.logger.error(f"Erro ao analisar sazonalidade: {str(e)}")
        return {"padrao_semanal": {}, "sazonalidade_mensal": {}, "erro": str(e)}


def calcular_classificacao_abc_estoque(estabelecimento_id):
    """Classificação ABC (v1) por faturamento de itens vendidos nos últimos 90 dias.

    Se não houver vendas no período, usa valor em estoque (preço_custo * quantidade).
    """
    try:
        hoje = date.today()
        inicio = hoje - timedelta(days=90)

        # Faturamento por produto
        rows = (
            db.session.query(
                VendaItem.produto_id.label("produto_id"),
                func.sum(VendaItem.total_item).label("valor"),
            )
            .join(Venda, Venda.id == VendaItem.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.status == "finalizada",
                Venda.data_venda >= inicio,
            )
            .group_by(VendaItem.produto_id)
            .all()
        )

        metodo = "faturamento_90d"
        valores_map = {int(r.produto_id): float(r.valor or 0.0) for r in rows if r.produto_id}

        # Fallback: valor em estoque
        if not valores_map:
            metodo = "valor_estoque"
            produtos = Produto.query.filter_by(estabelecimento_id=estabelecimento_id).all()
            valores_map = {
                int(p.id): float((p.preco_custo or 0.0) * (p.quantidade or 0)) for p in produtos
            }
        else:
            produtos = Produto.query.filter(
                Produto.estabelecimento_id == estabelecimento_id,
                Produto.id.in_(list(valores_map.keys())),
            ).all()

        if not valores_map:
            return {"metodo": metodo, "classificacao": [], "resumo": {"A": 0, "B": 0, "C": 0}}

        produto_map = {int(p.id): p for p in produtos}
        ids = list(valores_map.keys())
        valores = [valores_map[i] for i in ids]
        classes = calcular_classificacao_abc(valores)

        itens = []
        for produto_id, classe, valor in sorted(
            zip(ids, classes, valores), key=lambda t: t[2], reverse=True
        ):
            produto = produto_map.get(int(produto_id))
            itens.append(
                {
                    "produto_id": int(produto_id),
                    "produto_nome": produto.nome if produto else None,
                    "valor": round(float(valor or 0.0), 2),
                    "classe": classe,
                }
            )

        resumo = {
            "A": sum(1 for i in itens if i["classe"] == "A"),
            "B": sum(1 for i in itens if i["classe"] == "B"),
            "C": sum(1 for i in itens if i["classe"] == "C"),
        }

        return {
            "metodo": metodo,
            "periodo_dias": 90,
            "resumo": resumo,
            "classificacao": itens,
        }

    except Exception as e:
        current_app.logger.error(f"Erro na classificação ABC do estoque: {str(e)}")
        return {"classificacao": [], "erro": str(e)}


def analisar_correlacao_vendas(estabelecimento_id):
    """Análise de correlação (v1) entre variáveis numéricas das vendas.

    Usa os últimos 180 dias de vendas finalizadas e retorna as maiores correlações.
    """
    try:
        hoje = date.today()
        inicio = hoje - timedelta(days=180)

        vendas = (
            db.session.query(
                Venda.total.label("total"),
                Venda.desconto.label("desconto"),
                extract("hour", Venda.data_venda).label("hora"),
                extract("dow", Venda.data_venda).label("dow"),
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.status == "finalizada",
                Venda.data_venda >= inicio,
            )
            .all()
        )

        if len(vendas) < 10:
            return {
                "periodo_dias": 180,
                "correlacoes": [],
                "observacao": "Amostra insuficiente para correlação (mínimo ~10 vendas)",
            }

        df = pd.DataFrame(
            [
                {
                    "total": float(v.total or 0.0),
                    "desconto": float(v.desconto or 0.0),
                    "hora": float(v.hora or 0.0),
                    "dow": float(v.dow or 0.0),
                }
                for v in vendas
            ]
        )

        # Correlação de Pearson entre colunas numéricas
        corr = df.corr(numeric_only=True)

        pares = []
        cols = list(corr.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                x = cols[i]
                y = cols[j]
                coef = corr.loc[x, y]
                if pd.isna(coef):
                    continue
                pares.append({"variavel_x": x, "variavel_y": y, "coef": float(coef)})

        # Ordenar por |coef| desc e filtrar um pouco de ruído
        pares = sorted(pares, key=lambda p: abs(p["coef"]), reverse=True)
        pares = [p for p in pares if abs(p["coef"]) >= 0.2][:10]

        return {
            "periodo_dias": 180,
            "correlacoes": pares,
        }

    except Exception as e:
        current_app.logger.error(f"Erro na correlação de vendas: {str(e)}")
        return {"correlacoes": [], "erro": str(e)}
