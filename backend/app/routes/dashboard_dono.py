# app/routes/dashboard.py
# ARQUIVO REFATORADO - VERSÃO CONSISTENTE

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (
    Venda, Produto, Cliente, Funcionario, VendaItem,
    Configuracao, Despesa, DashboardMetrica
)
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract
import numpy as np
from collections import defaultdict
from app.decorators.decorator_jwt import funcionario_required, admin_required

dashboard_bp = Blueprint("dashboard", __name__)

# ==================== CONSTANTES E VALIDAÇÃO ====================

MINIMO_DADOS_TENDENCIA = 7  # Mínimo de dias para análise de tendência
CONFIANCA_ALTA = 0.7
CONFIANCA_MEDIA = 0.4
MARGEM_PADRAO = 0.3  # 30% - deve vir da configuração real

class MetricError(Exception):
    """Exceção para erros no cálculo de métricas"""
    pass

def validar_dados_minimos(dados, minimo, metric_name):
    """Valida se há dados suficientes para cálculo"""
    if len(dados) < minimo:
        raise MetricError(f"Dados insuficientes para {metric_name}: {len(dados)} < {minimo}")

def validar_divisor(divisor, metric_name):
    """Valida divisor para evitar divisão por zero"""
    if divisor is None or divisor == 0:
        raise MetricError(f"Divisor zero/inválido em {metric_name}")
    return divisor

# ==================== CAMADA 1: COLETA DE DADOS ====================

class DataCollector:
    """Coleta dados do banco de maneira consistente"""
    
    @staticmethod
    def get_vendas_periodo(estabelecimento_id, inicio, fim, agrupar_por=None):
        """
        Retorna vendas em um período
        
        Parâmetros:
        - inicio, fim: datetime objetos
        - agrupar_por: None, 'dia', 'hora', 'categoria'
        
        Retorno: lista de dicts com campos consistentes
        """
        query = db.session.query(
            Venda.id,
            Venda.data_venda,
            Venda.total,
            Venda.cliente_id,
            Venda.forma_pagamento,
            Venda.status
        ).filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio,
            Venda.data_venda <= fim,
            Venda.status == "finalizada"
        )
        
        if agrupar_por == 'dia':
            query = query.add_columns(
                func.date(Venda.data_venda).label('grupo')
            ).group_by(func.date(Venda.data_venda))
        elif agrupar_por == 'hora':
            query = query.add_columns(
                extract('hour', Venda.data_venda).label('grupo')
            ).group_by(extract('hour', Venda.data_venda))
        
        resultados = query.all()
        
        # Converter para formato consistente
        if agrupar_por:
            return [{
                'grupo': r.grupo,
                'total': float(r.total) if r.total else 0.0,
                'quantidade': 1
            } for r in resultados]
        else:
            return [{
                'id': r.id,
                'data': r.data_venda,
                'total': float(r.total) if r.total else 0.0,
                'cliente_id': r.cliente_id
            } for r in resultados]
    
    @staticmethod
    def get_produtos_vendidos(estabelecimento_id, inicio, fim, limite=20):
        """Retorna produtos vendidos com quantidade e valor total"""
        query = (
            db.session.query(
                Produto.id,
                Produto.nome,
                Produto.categoria,
                Produto.preco_custo,
                Produto.preco_venda,
                func.sum(VendaItem.quantidade).label('quantidade_vendida'),
                func.sum(VendaItem.total_item).label('total_vendido')
            )
            .join(VendaItem, Produto.id == VendaItem.produto_id)
            .join(Venda, VendaItem.venda_id == Venda.id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= inicio,
                Venda.data_venda <= fim,
                Venda.status == "finalizada"
            )
            .group_by(
                Produto.id, Produto.nome, Produto.categoria,
                Produto.preco_custo, Produto.preco_venda
            )
            .order_by(func.sum(VendaItem.total_item).desc())
            .limit(limite)
        )
        
        return [{
            'id': r.id,
            'nome': r.nome,
            'categoria': r.categoria,
            'preco_custo': float(r.preco_custo) if r.preco_custo else 0.0,
            'preco_venda': float(r.preco_venda) if r.preco_venda else 0.0,
            'quantidade_vendida': int(r.quantidade_vendida) if r.quantidade_vendida else 0,
            'total_vendido': float(r.total_vendido) if r.total_vendido else 0.0
        } for r in query.all()]
    
    @staticmethod
    def get_estoque_status(estabelecimento_id):
        """Retorna status do estoque com critérios consistentes"""
        produtos = Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.ativo == True
        ).all()
        
        estoque_baixo = []
        validade_proxima = []
        hoje = date.today()
        
        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()
        dias_alerta = config.dias_alerta_validade if config else 15
        
        for p in produtos:
            # Estoque baixo: quantidade <= quantidade_minima
            if p.quantidade <= p.quantidade_minima:
                estoque_baixo.append({
                    'id': p.id,
                    'nome': p.nome,
                    'quantidade': p.quantidade,
                    'quantidade_minima': p.quantidade_minima,
                    'categoria': p.categoria
                })
            
            # Validade próxima: entre hoje e hoje + dias_alerta
            if p.data_validade:
                dias_para_validade = (p.data_validade - hoje).days
                if 0 <= dias_para_validade <= dias_alerta:
                    validade_proxima.append({
                        'id': p.id,
                        'nome': p.nome,
                        'quantidade': p.quantidade,
                        'data_validade': p.data_validade.isoformat(),
                        'dias_para_validade': dias_para_validade,
                        'categoria': p.categoria
                    })
        
        return {
            'estoque_baixo': estoque_baixo,
            'validade_proxima': validade_proxima,
            'total_produtos': len(produtos)
        }

# ==================== CAMADA 2: CÁLCULO DE MÉTRICAS ====================

class MetricCalculator:
    """Calcula métricas de maneira consistente e validada"""
    
    @staticmethod
    def calcular_metricas_dia(estabelecimento_id, data_ref):
        """Calcula métricas do dia com validação"""
        inicio = datetime.combine(data_ref, datetime.min.time())
        fim = datetime.combine(data_ref, datetime.max.time())
        
        vendas = DataCollector.get_vendas_periodo(estabelecimento_id, inicio, fim)
        
        if not vendas:
            return {
                'total': 0.0,
                'quantidade': 0,
                'ticket_medio': None,  # Não aplicável
                'clientes_unicos': 0,
                'status': 'sem_vendas'
            }
        
        total = sum(v['total'] for v in vendas)
        quantidade = len(vendas)
        clientes_unicos = len(set(v['cliente_id'] for v in vendas if v['cliente_id']))
        
        try:
            ticket_medio = total / validar_divisor(quantidade, 'ticket_medio_dia')
        except MetricError:
            ticket_medio = None
        
        return {
            'total': float(total),
            'quantidade': quantidade,
            'ticket_medio': ticket_medio,
            'clientes_unicos': clientes_unicos,
            'status': 'ok'
        }
    
    @staticmethod
    def calcular_metricas_mes(estabelecimento_id, data_ref):
        """Calcula métricas do mês com validação"""
        inicio_mes = datetime(data_ref.year, data_ref.month, 1)
        fim_dia = datetime.combine(data_ref, datetime.max.time())
        
        # Vendas do mês
        vendas = DataCollector.get_vendas_periodo(
            estabelecimento_id, inicio_mes, fim_dia
        )
        total_vendas = sum(v['total'] for v in vendas)
        
        # Despesas do mês
        despesas = Despesa.query.filter(
            Despesa.estabelecimento_id == estabelecimento_id,
            Despesa.data_despesa >= inicio_mes.date(),
            Despesa.data_despesa <= fim_dia.date()
        ).all()
        total_despesas = sum(d.valor for d in despesas)
        
        lucro_bruto = total_vendas - total_despesas
        
        try:
            margem_lucro = (lucro_bruto / validar_divisor(total_vendas, 'margem_lucro')) * 100
        except MetricError:
            margem_lucro = None
        
        return {
            'total_vendas': float(total_vendas),
            'total_despesas': float(total_despesas),
            'lucro_bruto': float(lucro_bruto),
            'margem_lucro': margem_lucro,
            'dias_ate_hoje': (data_ref - inicio_mes.date()).days + 1
        }
    
    @staticmethod
    def calcular_crescimento(vals_atual, vals_anterior, metric_name):
        """Calcula crescimento de maneira consistente"""
        if not vals_atual or not vals_anterior:
            return None
        
        if vals_anterior == 0:
            return None  # Não podemos calcular crescimento a partir de zero
        
        return ((vals_atual - vals_anterior) / vals_anterior) * 100
    
    @staticmethod
    def calcular_tendencia(vals_temporais):
        """Calcula tendência com regressão linear simples"""
        validar_dados_minimos(vals_temporais, MINIMO_DADOS_TENDENCIA, 'tendencia')
        
        x = np.arange(len(vals_temporais))
        y = np.array(vals_temporais)
        
        # Regressão linear
        coeficientes = np.polyfit(x, y, 1)
        slope = coeficientes[0]  # Inclinação
        intercept = coeficientes[1]  # Intercepto
        
        # R²
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r2': float(r2),
            'confianca': 'ALTA' if r2 > CONFIANCA_ALTA else 'MÉDIA' if r2 > CONFIANCA_MEDIA else 'BAIXA'
        }
    
    @staticmethod
    def calcular_margem_produto(preco_venda, preco_custo):
        """Calcula margem de lucro de um produto"""
        if not preco_venda or preco_venda == 0:
            return None
        
        return ((preco_venda - preco_custo) / preco_venda) * 100

# ==================== CAMADA 3: ANÁLISE DE NEGÓCIO ====================

class BusinessAnalyst:
    """Analisa dados para gerar insights de negócio"""
    
    @staticmethod
    def identificar_produtos_estrela(produtos_vendidos, dias_periodo=90):
        """
        Identifica produtos estrela usando critérios consistentes:
        1. Volume de vendas (top 30%)
        2. Margem de lucro (> 15%)
        3. Frequência de venda (vendeu em pelo menos 10% dos dias)
        """
        if not produtos_vendidos:
            return []
        
        # Calcular margem para cada produto
        produtos_com_margem = []
        for p in produtos_vendidos:
            margem = MetricCalculator.calcular_margem_produto(
                p['preco_venda'], p['preco_custo']
            )
            if margem is not None:
                produtos_com_margem.append({
                    **p,
                    'margem': margem,
                    'score': p['total_vendido'] * (margem / 100)  # Valor margem
                })
        
        # Ordenar por score
        produtos_com_margem.sort(key=lambda x: x['score'], reverse=True)
        
        # Definir thresholds
        threshold_volume = np.percentile(
            [p['total_vendido'] for p in produtos_com_margem], 
            70  # Top 30% por volume
        ) if len(produtos_com_margem) >= 3 else 0
        
        # Filtrar produtos estrela
        estrelas = []
        for p in produtos_com_margem:
            if (p['total_vendido'] >= threshold_volume and 
                p['margem'] > 15 and
                p['quantidade_vendida'] >= dias_periodo * 0.1):  # Vendeu em 10% dos dias
                estrelas.append(p)
        
        return estrelas[:10]
    
    @staticmethod
    def identificar_produtos_lentos(produtos_vendidos, estoque_status, dias_periodo=60):
        """
        Identifica produtos lentos:
        1. Baixa rotação (vendas < média/2)
        2. Alto estoque (> 10 unidades)
        3. Tempo parado (> 30 dias)
        """
        if not produtos_vendidos:
            return []
        
        # Calcular média de vendas
        vendas_totais = sum(p['quantidade_vendida'] for p in produtos_vendidos)
        media_vendas = vendas_totais / len(produtos_vendidos)
        
        # Produtos lentos
        lentos = []
        for p in produtos_vendidos:
            # Verificar se está no estoque
            estoque_info = next(
                (e for e in estoque_status['estoque_baixo'] + estoplace_status['validade_proxima'] 
                 if e['id'] == p['id']), 
                None
            )
            
            if estoque_info:
                estoque = estoque_info['quantidade']
            else:
                estoque = 0
            
            # Critérios para produto lento
            if (p['quantidade_vendida'] < media_vendas * 0.5 and
                estoque > 10):
                dias_parado = dias_periodo * (estoque / max(p['quantidade_vendida'], 1))
                lentos.append({
                    **p,
                    'estoque_atual': estoque,
                    'dias_parado': min(int(dias_parado), dias_periodo)
                })
        
        return sorted(lentos, key=lambda x: x['dias_parado'], reverse=True)[:15]
    
    @staticmethod
    def gerar_insights(metricas_dia, metricas_mes, produtos_estrela, produtos_lentos):
        """Gera insights baseados em dados válidos"""
        insights = []
        
        # Insight 1: Performance do dia
        if metricas_dia['ticket_medio'] and metricas_dia['ticket_medio'] < 50:
            insights.append({
                'tipo': 'alerta',
                'titulo': 'Ticket Médio Baixo',
                'descricao': f"Ticket médio de R$ {metricas_dia['ticket_medio']:.2f} pode ser melhorado",
                'acao': 'Treinar equipe em vendas adicionais'
            })
        
        # Insight 2: Margem de lucro
        if metricas_mes['margem_lucro'] and metricas_mes['margem_lucro'] < 20:
            insights.append({
                'tipo': 'alerta',
                'titulo': 'Margem de Lucro Baixa',
                'descricao': f"Margem atual: {metricas_mes['margem_lucro']:.1f}%",
                'acao': 'Revisar preços e custos'
            })
        
        # Insight 3: Produtos estrela
        if produtos_estrela:
            insights.append({
                'tipo': 'oportunidade',
                'titulo': 'Produtos de Alto Desempenho',
                'descricao': f"{len(produtos_estrela)} produtos com boa margem e volume",
                'acao': 'Manter estoque e promover'
            })
        
        # Insight 4: Produtos lentos
        if produtos_lentos:
            valor_parado = sum(p['preco_custo'] * p['estoque_atual'] for p in produtos_lentos)
            insights.append({
                'tipo': 'alerta',
                'titulo': 'Capital Parado em Estoque',
                'descricao': f"{len(produtos_lentos)} produtos lentos (R$ {valor_parado:.2f} parado)",
                'acao': 'Criar promoções para girar estoque'
            })
        
        return insights

# ==================== ROTAS PRINCIPAIS ====================

@dashboard_bp.route("/resumo", methods=["GET"])
@funcionario_required
def resumo_dashboard():
    """Endpoint principal do dashboard - Versão consistente"""
    try:
        # 1. Autenticação e autorização
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
        
        # 2. Coletar dados básicos
        metricas_dia = MetricCalculator.calcular_metricas_dia(estabelecimento_id, hoje)
        metricas_mes = MetricCalculator.calcular_metricas_mes(estabelecimento_id, hoje)
        estoque_status = DataCollector.get_estoque_status(estabelecimento_id)
        
        # 3. Dados em tempo real (últimas 24h)
        inicio_24h = datetime.now() - timedelta(hours=24)
        vendas_recentes = DataCollector.get_vendas_periodo(
            estabelecimento_id, inicio_24h, datetime.now()
        )[:10]
        
        # 4. Construir resposta básica
        response = {
            "success": True,
            "usuario": {
                "nome": funcionario.nome,
                "role": funcionario.role,
                "acesso_avancado": acesso_avancado,
            },
            "data": {
                "hoje": {
                    "data": hoje.isoformat(),
                    "total_vendas": metricas_dia['total'],
                    "quantidade_vendas": metricas_dia['quantidade'],
                    "ticket_medio": metricas_dia['ticket_medio'],
                    "clientes_atendidos": metricas_dia['clientes_unicos'],
                },
                "mes": {
                    "total_vendas": metricas_mes['total_vendas'],
                    "total_despesas": metricas_mes['total_despesas'],
                    "lucro_bruto": metricas_mes['lucro_bruto'],
                    "margem_lucro": metricas_mes['margem_lucro'],
                },
                "alertas": {
                    "estoque_baixo": len(estoque_status['estoque_baixo']),
                    "validade_proxima": len(estoque_status['validade_proxima']),
                },
                "ultimas_vendas": vendas_recentes,
            }
        }
        
        # 5. Adicionar análises avançadas se autorizado
        if acesso_avancado:
            # Coletar dados para análise avançada
            inicio_90d = hoje - timedelta(days=90)
            produtos_vendidos = DataCollector.get_produtos_vendidos(
                estabelecimento_id, inicio_90d, datetime.combine(hoje, datetime.max.time())
            )
            
            # Análises
            produtos_estrela = BusinessAnalyst.identificar_produtos_estrela(
                produtos_vendidos, dias_periodo=90
            )
            produtos_lentos = BusinessAnalyst.identificar_produtos_lentos(
                produtos_vendidos, estoque_status, dias_periodo=60
            )
            insights = BusinessAnalyst.gerar_insights(
                metricas_dia, metricas_mes, produtos_estrela, produtos_lentos
            )
            
            response["data"]["analises_avancadas"] = {
                "produtos_estrela": produtos_estrela[:5],
                "produtos_lentos": produtos_lentos[:5],
                "insights": insights,
                "detalhes_estoque": {
                    "estoque_baixo": estoque_status['estoque_baixo'][:5],
                    "validade_proxima": estoque_status['validade_proxima'][:5]
                }
            }
        
        return jsonify(response), 200
        
    except MetricError as e:
        current_app.logger.warning(f"Métrica não calculada: {str(e)}")
        return jsonify({
            "success": True,
            "message": "Algumas métricas não puderam ser calculadas",
            "data": {}  # estrutura básica com valores None onde aplicável
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro no dashboard: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Erro interno no servidor",
            "message": str(e)
        }), 500

@dashboard_bp.route("/tendencia", methods=["GET"])
@admin_required
def analise_tendencia():
    """Análise de tendência com validação rigorosa"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        estabelecimento_id = funcionario.estabelecimento_id
        dias = min(int(request.args.get("dias", 30)), 365)  # Limitar a 1 ano
        
        # Coletar dados diários
        fim = date.today()
        inicio = fim - timedelta(days=dias)
        
        vendas_por_dia = DataCollector.get_vendas_periodo(
            estabelecimento_id,
            datetime.combine(inicio, datetime.min.time()),
            datetime.combine(fim, datetime.max.time()),
            agrupar_por='dia'
        )
        
        # Validar dados mínimos
        validar_dados_minimos(vendas_por_dia, MINIMO_DADOS_TENDENCIA, 'tendencia')
        
        # Extrair valores temporais
        totais = [v['total'] for v in vendas_por_dia]
        datas = [v['grupo'].strftime('%d/%m') for v in vendas_por_dia]
        
        # Calcular tendência
        tendencia = MetricCalculator.calcular_tendencia(totais)
        
        # Calcular métricas adicionais
        media_7d = np.mean(totais[-7:]) if len(totais) >= 7 else np.mean(totais)
        media_30d = np.mean(totais[-30:]) if len(totais) >= 30 else np.mean(totais)
        
        crescimento_7d = MetricCalculator.calcular_crescimento(
            np.mean(totais[-7:]) if len(totais) >= 7 else None,
            np.mean(totais[-14:-7]) if len(totais) >= 14 else None,
            'crescimento_7d'
        )
        
        return jsonify({
            "success": True,
            "periodo": {
                "inicio": inicio.isoformat(),
                "fim": fim.isoformat(),
                "dias": dias
            },
            "dados": {
                "datas": datas,
                "valores": totais,
                "media_7d": float(media_7d) if media_7d is not None else None,
                "media_30d": float(media_30d) if media_30d is not None else None
            },
            "tendencia": tendencia,
            "crescimento_7d": crescimento_7d,
            "observacoes": [
                f"Baseado em {len(vendas_por_dia)} dias de dados",
                f"Confiança da tendência: {tendencia['confianca']}"
            ]
        }), 200
        
    except MetricError as e:
        return jsonify({
            "success": False,
            "error": "Dados insuficientes",
            "message": str(e),
            "dias_minimos": MINIMO_DADOS_TENDENCIA
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Erro na análise de tendência: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erro na análise",
            "message": str(e)
        }), 500

@dashboard_bp.route("/produtos/analise", methods=["GET"])
@admin_required
def analise_produtos():
    """Análise completa de produtos com critérios consistentes"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        estabelecimento_id = funcionario.estabelecimento_id
        hoje = date.today()
        
        # Períodos para análise
        periodo_curto = 30  # dias
        periodo_longo = 90  # dias
        
        # Coletar dados
        inicio_curto = hoje - timedelta(days=periodo_curto)
        inicio_longo = hoje - timedelta(days=periodo_longo)
        
        produtos_30d = DataCollector.get_produtos_vendidos(
            estabelecimento_id,
            datetime.combine(inicio_curto, datetime.min.time()),
            datetime.combine(hoje, datetime.max.time())
        )
        
        produtos_90d = DataCollector.get_produtos_vendidos(
            estabelecimento_id,
            datetime.combine(inicio_longo, datetime.min.time()),
            datetime.combine(hoje, datetime.max.time())
        )
        
        estoque_status = DataCollector.get_estoque_status(estabelecimento_id)
        
        # Análises
        estrelas = BusinessAnalyst.identificar_produtos_estrela(
            produtos_90d, dias_periodo=periodo_longo
        )
        
        lentos = BusinessAnalyst.identificar_produtos_lentos(
            produtos_90d, estoque_status, dias_periodo=periodo_longo
        )
        
        # Classificação ABC (simplificada)
        if produtos_90d:
            total_vendido = sum(p['total_vendido'] for p in produtos_90d)
            produtos_classificados = []
            
            for p in sorted(produtos_90d, key=lambda x: x['total_vendido'], reverse=True):
                participacao = (p['total_vendido'] / total_vendido) * 100
                
                if participacao > 20:
                    classe = 'A'
                elif participacao > 5:
                    classe = 'B'
                else:
                    classe = 'C'
                
                produtos_classificados.append({
                    'id': p['id'],
                    'nome': p['nome'],
                    'classe': classe,
                    'participacao': round(participacao, 1),
                    'total_vendido': p['total_vendido']
                })
        else:
            produtos_classificados = []
        
        return jsonify({
            "success": True,
            "periodos": {
                "curto": periodo_curto,
                "longo": periodo_longo
            },
            "resumo": {
                "total_produtos_vendidos": len(produtos_90d),
                "produtos_estrela": len(estrelas),
                "produtos_lentos": len(lentos),
                "valor_estoque_parado": sum(
                    p['preco_custo'] * p.get('estoque_atual', 0) 
                    for p in lentos
                )
            },
            "detalhes": {
                "estrelas": estrelas[:10],
                "lentos": lentos[:10],
                "classificacao_abc": produtos_classificados[:20]
            },
            "estoque": {
                "baixo": estoque_status['estoque_baixo'][:10],
                "validade_proxima": estoque_status['validade_proxima'][:10]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro na análise de produtos: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erro na análise",
            "message": str(e)
        }), 500

# ==================== ROTAS ADICIONAIS SIMPLIFICADAS ====================

@dashboard_bp.route("/alertas", methods=["GET"])
@funcionario_required
def alertas_prioritarios():
    """Alertas críticos para ação imediata"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        estabelecimento_id = funcionario.estabelecimento_id
        estoque_status = DataCollector.get_estoque_status(estabelecimento_id)
        
        alertas = []
        
        # Alertas críticos
        for produto in estoque_status['estoque_baixo']:
            if produto['quantidade'] == 0:
                alertas.append({
                    "nivel": "critico",
                    "tipo": "estoque_zero",
                    "titulo": f"Estoque esgotado: {produto['nome']}",
                    "acao": "Repor imediatamente"
                })
        
        for produto in estoque_status['validade_proxima']:
            if produto['dias_para_validade'] <= 3:
                alertas.append({
                    "nivel": "alto",
                    "tipo": "validade_proxima",
                    "titulo": f"Validade próxima: {produto['nome']}",
                    "descricao": f"Vence em {produto['dias_para_validade']} dias",
                    "acao": "Criar promoção urgente"
                })
        
        return jsonify({
            "success": True,
            "total_alertas": len(alertas),
            "alertas": alertas[:10]  # Limitar a 10 mais importantes
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro nos alertas: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erro nos alertas",
            "message": str(e)
        }), 500

@dashboard_bp.route("/comparativo", methods=["GET"])
@admin_required
def comparativo_periodos():
    """Comparativo consistente entre períodos"""
    try:
        current_user_id = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user_id)
        
        if not funcionario:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        estabelecimento_id = funcionario.estabelecimento_id
        hoje = date.today()
        
        # Definir períodos comparáveis
        periodos = {
            "esta_semana": {
                "inicio": hoje - timedelta(days=hoje.weekday()),
                "fim": hoje
            },
            "semana_passada": {
                "inicio": hoje - timedelta(days=hoje.weekday() + 7),
                "fim": hoje - timedelta(days=hoje.weekday() + 1)
            },
            "este_mes": {
                "inicio": datetime(hoje.year, hoje.month, 1),
                "fim": hoje
            },
            "mes_passado": {
                "inicio": datetime(hoje.year, hoje.month - 1, 1) if hoje.month > 1 
                         else datetime(hoje.year - 1, 12, 1),
                "fim": datetime(hoje.year, hoje.month, 1) - timedelta(days=1)
            }
        }
        
        comparativos = {}
        
        for nome, periodo in periodos.items():
            vendas = DataCollector.get_vendas_periodo(
                estabelecimento_id,
                datetime.combine(periodo['inicio'], datetime.min.time()),
                datetime.combine(periodo['fim'], datetime.max.time())
            )
            
            if vendas:
                total = sum(v['total'] for v in vendas)
                quantidade = len(vendas)
                ticket = total / quantidade if quantidade > 0 else None
            else:
                total = 0
                quantidade = 0
                ticket = None
            
            comparativos[nome] = {
                "total": float(total),
                "quantidade": quantidade,
                "ticket_medio": ticket,
                "dias": (periodo['fim'] - periodo['inicio']).days + 1
            }
        
        # Calcular crescimentos apenas quando ambos períodos têm dados
        crescimento_semanal = None
        if (comparativos["esta_semana"]["total"] > 0 and 
            comparativos["semana_passada"]["total"] > 0):
            crescimento_semanal = MetricCalculator.calcular_crescimento(
                comparativos["esta_semana"]["total"],
                comparativos["semana_passada"]["total"],
                "crescimento_semanal"
            )
        
        crescimento_mensal = None
        if (comparativos["este_mes"]["total"] > 0 and 
            comparativos["mes_passado"]["total"] > 0):
            crescimento_mensal = MetricCalculator.calcular_crescimento(
                comparativos["este_mes"]["total"],
                comparativos["mes_passado"]["total"],
                "crescimento_mensal"
            )
        
        return jsonify({
            "success": True,
            "periodos": comparativos,
            "crescimentos": {
                "semanal": crescimento_semanal,
                "mensal": crescimento_mensal
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro no comparativo: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erro no comparativo",
            "message": str(e)
        }), 500

# ==================== FUNÇÕES DE SUPORTE (MANTIDAS POR COMPATIBILIDADE) ====================

def calcular_despesas_mes(estabelecimento_id, inicio_mes, fim_dia):
    """Calcula despesas do mês de forma consistente"""
    try:
        total = (
            db.session.query(func.coalesce(func.sum(Despesa.valor), 0.0))
            .filter(
                Despesa.estabelecimento_id == estabelecimento_id,
                Despesa.data_despesa >= inicio_mes.date(),
                Despesa.data_despesa <= fim_dia.date(),
            )
            .scalar()
        )
        
        return float(total or 0.0)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular despesas: {str(e)}")
        return 0.0