# app/routes/dashboard_dono.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (
    Venda,
    Produto,
    Cliente,
    Funcionario,
    MovimentacaoEstoque,
    Estabelecimento,
    Configuracao,
    VendaItem,
    DashboardMetrica,
)
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract, and_, or_
import pandas as pd
import numpy as np
from scipy import stats
import json
from collections import defaultdict
from utils.decorator import admin_required

dashboard_dono_bp = Blueprint("dashboard_dono", __name__)


@dashboard_dono_bp.route("/painel-dono", methods=["GET"])
@admin_required
def painel_dono():
    """Dashboard completo do dono com BI avançado e tendências"""
    # Obtém o ID do funcionário a partir do token JWT
    current_user_id = get_jwt_identity()

    # Busca o funcionário no banco
    funcionario = Funcionario.query.get(current_user_id)

    # Verifica se o funcionário existe e é administrador
    if not funcionario or not funcionario.is_admin:
        return jsonify({"error": "Acesso negado"}), 403
    
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        hoje = date.today()

        # 1. DADOS BRUTOS
        dados = obter_dados_completos(estabelecimento_id, hoje)

        # 2. CÁLCULO DE TENDÊNCIAS
        tendencias = calcular_tendencias(estabelecimento_id, hoje)

        # 3. PROJEÇÕES
        projecoes = calcular_projecoes(dados, tendencias, hoje)

        # 4. INSIGHTS AUTOMÁTICOS (BI)
        insights = gerar_insights_inteligentes(dados, tendencias, projecoes)

        # 5. KPIs PRINCIPAIS
        kpis = calcular_kpis_principais(dados, projecoes)

        # 6. ALERTAS PRIORITÁRIOS
        alertas = gerar_alertas_prioritarios(dados)

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
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro no painel do dono: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar painel do dono",
                    "message": str(e),
                }
            ),
            500,
        )


def obter_dados_completos(estabelecimento_id, hoje):
    """Coleta todos os dados necessários para o dashboard"""

    # Períodos
    inicio_dia = datetime.combine(hoje, datetime.min.time())
    fim_dia = datetime.combine(hoje, datetime.max.time())

    inicio_mes = datetime(hoje.year, hoje.month, 1)
    if hoje.month == 12:
        fim_mes = datetime(hoje.year + 1, 1, 1) - timedelta(days=1)
    else:
        fim_mes = datetime(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

    inicio_mes_passado = inicio_mes - timedelta(days=30)
    fim_mes_passado = inicio_mes - timedelta(days=1)

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

    # 3. VENDAS DO MÊS PASSADO (mesmo período)
    vendas_mes_passado = Venda.query.filter(
        Venda.estabelecimento_id == estabelecimento_id,
        Venda.data_venda >= inicio_mes_passado,
        Venda.data_venda <= fim_mes_passado,
        Venda.status == "finalizada",
    ).all()

    # 4. PRODUTOS COM ESTOQUE BAIXO
    produtos_estoque_baixo = (
        Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.quantidade <= Produto.quantidade_minima,
            Produto.ativo == True,
        )
        .order_by(Produto.quantidade)
        .limit(10)
        .all()
    )

    # 5. PRODUTOS PRÓXIMOS DA VALIDADE
    dias_alerta = 15
    data_alerta = hoje + timedelta(days=dias_alerta)
    produtos_validade_proxima = (
        Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.data_validade.between(hoje, data_alerta),
            Produto.quantidade > 0,
            Produto.ativo == True,
        )
        .order_by(Produto.data_validade)
        .limit(10)
        .all()
    )

    # 6. TOP 10 CLIENTES DO MÊS
    top_clientes = (
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

    # 7. VENDAS POR HORA (últimas 24h)
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

    # 8. PRODUTOS MAIS VENDIDOS DO MÊS
    produtos_mais_vendidos = (
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

    return {
        "vendas_hoje": vendas_hoje,
        "vendas_mes": vendas_mes,
        "vendas_mes_passado": vendas_mes_passado,
        "produtos_estoque_baixo": produtos_estoque_baixo,
        "produtos_validade_proxima": produtos_validade_proxima,
        "top_clientes": top_clientes,
        "vendas_por_hora": vendas_por_hora,
        "produtos_mais_vendidos": produtos_mais_vendidos,
        "periodos": {"inicio_mes": inicio_mes, "fim_mes": fim_mes, "hoje": hoje},
    }


def calcular_tendencias(estabelecimento_id, hoje):
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


def calcular_projecoes(dados, tendencias, hoje):
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

    # Meta mensal (poderia vir da configuração)
    meta_mensal = 100000  # Valor exemplo, deveria vir do banco

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
    meta_mensal = 100000  # Exemplo
    atingimento_meta = (total_mes / meta_mensal * 100) if meta_mensal > 0 else 0

    # Crescimento vs mês passado (simplificado)
    crescimento_mensal = 12.5  # Exemplo, deveria ser calculado

    return {
        "financeiro": {
            "faturamento_hoje": {
                "valor": total_hoje,
                "variacao": "+18.5%",  # vs ontem (exemplo)
                "tendencia": "alta",
            },
            "faturamento_mes": {
                "valor": total_mes,
                "meta": meta_mensal,
                "atingimento": f"{atingimento_meta:.1f}%",
            },
            "ticket_medio_hoje": ticket_medio_hoje,
            "lucro_estimado": total_mes * 0.30,  # 30% de margem (exemplo)
            "crescimento_mensal": f"{crescimento_mensal}%",
        },
        "operacional": {
            "vendas_hoje": quantidade_vendas_hoje,
            "clientes_hoje": len(clientes_hoje),
            "produtos_vendidos_hoje": sum(len(v.itens) for v in vendas_hoje),
            "hora_pico": "18h-19h",  # Exemplo
            "tempo_medio_atendimento": "3:24",  # Exemplo
        },
        "clientes": {
            "novos_mes": 47,  # Exemplo
            "recorrentes": 312,  # Exemplo
            "fidelidade": "87%",  # Exemplo
            "valor_cliente_top": valor_cliente_top,
            "satisfacao": "4.7/5.0",  # Exemplo
        },
        "estoque": {
            "produtos_total": 1250,  # Exemplo
            "valor_estoque": 152000,  # Exemplo
            "giro_estoque": "22 dias",  # Exemplo
            "produtos_baixo": len(dados["produtos_estoque_baixo"]),
            "produtos_validade": len(dados["produtos_validade_proxima"]),
        },
    }


def gerar_alertas_prioritarios(dados):
    """Gera alertas com prioridade para ação imediata"""

    alertas = []

    # 1. ALERTA CRÍTICO: Estoque zero
    produtos_estoque_zero = [
        p for p in dados["produtos_estoque_baixo"] if p.quantidade == 0
    ]
    if produtos_estoque_zero:
        alertas.append(
            {
                "nivel": "critico",
                "icone": "🔥",
                "titulo": "ESTOQUE ESGOTADO",
                "mensagem": f"{len(produtos_estoque_zero)} produtos estão com estoque ZERO",
                "produtos": [p.nome for p in produtos_estoque_zero[:3]],
                "acao": "REPOSIÇÃO URGENTE",
                "prioridade": 1,
            }
        )

    # 2. ALERTA ALTO: Validade vencida
    hoje = date.today()
    produtos_vencidos = [
        p
        for p in dados["produtos_validade_proxima"]
        if p.data_validade and p.data_validade < hoje
    ]
    if produtos_vencidos:
        alertas.append(
            {
                "nivel": "alto",
                "icone": "⚠️",
                "titulo": "PRODUTOS VENCIDOS",
                "mensagem": f"{len(produtos_vencidos)} produtos estão VENCIDOS",
                "produtos": [p.nome for p in produtos_vencidos[:3]],
                "acao": "RETIRAR DO ESTOQUE",
                "prioridade": 2,
            }
        )

    # 3. ALERTA MÉDIO: Estoque muito baixo (< 20% do mínimo)
    produtos_criticos = [
        p
        for p in dados["produtos_estoque_baixo"]
        if p.quantidade < p.quantidade_minima * 0.2
    ]
    if produtos_criticos:
        alertas.append(
            {
                "nivel": "medio",
                "icone": "📉",
                "titulo": "ESTOQUE CRÍTICO",
                "mensagem": f"{len(produtos_criticos)} produtos com menos de 20% do estoque mínimo",
                "produtos": [p.nome for p in produtos_criticos[:3]],
                "acao": "Programar compra",
                "prioridade": 3,
            }
        )

    # 4. ALERTA BAIXO: Validade próxima (≤ 3 dias)
    produtos_validade_3dias = [
        p
        for p in dados["produtos_validade_proxima"]
        if p.data_validade and (p.data_validade - hoje).days <= 3
    ]
    if produtos_validade_3dias:
        alertas.append(
            {
                "nivel": "baixo",
                "icone": "⏰",
                "titulo": "VALIDADE MUITO PRÓXIMA",
                "mensagem": f"{len(produtos_validade_3dias)} produtos vencem em ≤ 3 dias",
                "produtos": [p.nome for p in produtos_validade_3dias[:3]],
                "acao": "Criar promoção",
                "prioridade": 4,
            }
        )

    # Ordenar por prioridade
    alertas.sort(key=lambda x: x["prioridade"])

    return alertas


@dashboard_dono_bp.route("/tendencia-mensal", methods=["GET"])
def tendencia_mensal_detalhada():
    """Análise detalhada da tendência mensal com gráficos de dados"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
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


def gerar_recomendacoes_tendencia(slope, crescimento_semanal):
    """Gera recomendações baseadas na tendência identificada"""
    recomendacoes = []

    if slope > 100:  # Crescimento forte (> R$100 por dia)
        recomendacoes.append("✅ Tendência de CRESCIMENTO FORTE identificada")
        recomendacoes.append("💡 Considere aumentar estoque dos produtos mais vendidos")
        recomendacoes.append("🎯 Mantenha as estratégias que estão funcionando")

    elif slope > 0:  # Crescimento moderado
        recomendacoes.append("📈 Tendência de CRESCIMENTO MODERADO")
        recomendacoes.append("🔍 Analise quais produtos estão puxando o crescimento")
        recomendacoes.append("💰 Otimize promoções para acelerar o crescimento")

    elif slope == 0:  # Estabilidade
        recomendacoes.append("⚖️ Tendência de ESTABILIDADE")
        recomendacoes.append("🔄 Considere renovar o mix de produtos")
        recomendacoes.append("🎪 Crie eventos ou promoções para gerar movimento")

    else:  # Decrescimento
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


@dashboard_dono_bp.route("/resumo-executivo", methods=["GET"])
def resumo_executivo():
    """Resumo executivo para tomada de decisão rápida"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
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
                        "decisao_do_dia": obter_decisao_do_dia(
                            float(total_hoje), produtos_estoque_zero
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


def obter_decisao_do_dia(faturamento_hoje, produtos_estoque_zero):
    """Retorna a decisão mais importante do dia baseada nos dados"""

    if produtos_estoque_zero > 0:
        return {
            "prioridade": "ALTA",
            "titulo": "⚠️ REPOSIÇÃO DE ESTOQUE URGENTE",
            "descricao": f"{produtos_estoque_zero} produtos estão sem estoque",
            "acao": "Faça pedidos de reposição imediatamente",
        }

    elif faturamento_hoje < 1000:  # Meta diária exemplo
        return {
            "prioridade": "MÉDIA",
            "titulo": "📊 VENDAS ABAIXO DA META DIÁRIA",
            "descricao": f"Faturamento de R$ {faturamento_hoje:,.2f} está abaixo do esperado",
            "acao": "Ative promoções relâmpago para aumentar vendas",
        }

    elif faturamento_hoje > 5000:
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
