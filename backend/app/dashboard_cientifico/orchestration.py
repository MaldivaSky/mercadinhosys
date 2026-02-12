"""
Orchestration Layer - Orquestra todas as camadas
Foco: Simplicidade e clareza
"""

from typing import Dict, Any
from datetime import datetime
import logging
from .data_layer import DataLayer
from .stats_layer import StatsValidator
from .models_layer import PracticalModels
from .serializers import DashboardSerializer
from .cache_layer import cache_response

# Logger global - DEVE estar no nível do módulo
logger = logging.getLogger(__name__)


class DashboardOrchestrator:
    """Orquestra a geração do dashboard"""

    def __init__(self, establishment_id: int):
        self.establishment_id = establishment_id

    @cache_response(ttl_seconds=60, require_db_check=True)
    def get_executive_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """
        Dashboard executivo - Resumo para gestão
        """
        # 1. Coletar dados
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_current = end_date - timedelta(days=days)
        start_previous = end_date - timedelta(days=days * 2)
        end_previous = end_date - timedelta(days=days)

        sales_summary = DataLayer.get_sales_summary_range(
            self.establishment_id, start_current, end_date
        )
        sales_summary_previous = DataLayer.get_sales_summary_range(
            self.establishment_id, start_previous, end_previous
        )
        sales_timeseries = DataLayer.get_sales_timeseries(self.establishment_id, days)
        inventory_summary = DataLayer.get_inventory_summary(self.establishment_id)
        customer_metrics = DataLayer.get_customer_metrics(self.establishment_id, days)
        rh_metrics = DataLayer.get_rh_metrics(self.establishment_id, days)

        def _confidence_from_samples(samples: int) -> str:
            if samples < 5:
                return "INSUFICIENT"
            if samples < 15:
                return "LOW"
            if samples < 30:
                return "MEDIUM"
            return "HIGH"

        sales_current = {
            "value": sales_summary.get("total_faturado", 0),
            "confidence": _confidence_from_samples(sales_summary.get("total_vendas", 0)),
            "sample_size": sales_summary.get("total_vendas", 0),
            "warnings": [],
        }

        sales_previous = {
            "value": sales_summary_previous.get("total_faturado", 0),
            "confidence": _confidence_from_samples(
                sales_summary_previous.get("total_vendas", 0)
            ),
            "sample_size": sales_summary_previous.get("total_vendas", 0),
            "warnings": [],
        }

        # Calcular crescimento
        growth = StatsValidator.calculate_growth(
            current_value=sales_current.get("value", 0),
            previous_value=sales_previous.get("value", 0),
            current_samples=sales_current.get("sample_size", 0),
            previous_samples=sales_previous.get("sample_size", 0),
        )

        # 3. Análises científicas
        trend_analysis = PracticalModels.detect_sales_trend(sales_timeseries)

        # Análise ABC do estoque
        top_products = DataLayer.get_top_products(self.establishment_id, days, 50)
        abc_analysis = PracticalModels.analyze_inventory_abc(
            [
                {
                    "nome": p["nome"],
                    "valor_total": p["faturamento"],
                    "quantidade": p["quantidade_vendida"],
                }
                for p in top_products
            ]
        )

        # Score de saúde
        health_score = PracticalModels.calculate_health_score(
            sales_summary, inventory_summary, customer_metrics
        )

        # 4. Serializar para frontend
        serializer = DashboardSerializer()

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "period_days": days,
            "summary": {
                "revenue": serializer.serialize_metric(sales_current),
                "growth": serializer.serialize_growth(growth),
                "avg_ticket": serializer.serialize_metric(
                    {
                        "value": sales_summary["ticket_medio"],
                        "confidence": "HIGH",
                        "sample_size": sales_summary["total_vendas"],
                    }
                ),
                "active_days": {
                    "value": sales_summary["dias_com_venda"],
                    "display": f"{sales_summary['dias_com_venda']}/{days} dias",
                    "status": "high_confidence",
                },
            },
            "inventory": {
                "total_value": {
                    "value": inventory_summary["valor_total"],
                    "display": f"R$ {inventory_summary['valor_total']:,.0f}",
                    "status": "high_confidence",
                },
                "low_stock_alert": {
                    "value": inventory_summary["baixo_estoque"],
                    "display": f"{inventory_summary['baixo_estoque']} produtos",
                    "status": (
                        "warning" if inventory_summary["baixo_estoque"] > 0 else "ok"
                    ),
                },
                "abc_analysis": abc_analysis,
            },
            "trend": serializer.serialize_trend(trend_analysis),
            "health": serializer.serialize_health_score(health_score),
            "top_products": top_products[:5],
            "customer_metrics": {
                "unique_customers": customer_metrics["clientes_unicos"],
                "avg_ticket_customer": customer_metrics["ticket_medio_cliente"],
                "max_purchase": customer_metrics["maior_compra"],
            },
            "rh": rh_metrics,
            "charts": {
                "sales_trend": sales_timeseries,
            },
        }

    @cache_response(ttl_seconds=300, require_db_check=True)  # 5 minutos de cache (otimizado)
    def get_scientific_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """
        Dashboard científico - Análise avançada com insights
        """
        from app.models import db
        import logging
        _logger = logging.getLogger(__name__)
        try:
            # 🔥 RESET TRANSACTION: Garante que erros de requests anteriores não envenenem este dashboard
            db.session.rollback()
            return self._get_scientific_dashboard_logic(days)
        except Exception as e:
            db.session.rollback()
            _logger.error(f"Erro CRÍTICO no dashboard científico: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _get_scientific_dashboard_logic(self, days: int = 30) -> Dict[str, Any]:
        # Garantir que logger está disponível - sempre criar novo para evitar problemas
        import logging
        _logger = logging.getLogger(__name__)
        
        def _confidence_from_samples(samples: int) -> str:
            """Função auxiliar para calcular confiança baseada em amostras"""
            if samples < 5:
                return "INSUFICIENT"
            if samples < 15:
                return "LOW"
            if samples < 30:
                return "MEDIUM"
            return "HIGH"
        
        from datetime import timedelta
        from app.models import Cliente
        from app.dashboard_cientifico.models_layer import PracticalModels as _PM
        end_date = datetime.utcnow()
        start_current = end_date - timedelta(days=days)
        start_previous = end_date - timedelta(days=days * 2)
        end_previous = end_date - timedelta(days=days)

        import time
        start_exec = time.time()
        # 1. Obter resumos básicos
        try:
            t0 = time.time()
            sales_current_summary = DataLayer.get_sales_summary_range(
                self.establishment_id, start_current, end_date
            )
            _logger.info(f"⏱️ get_sales_summary_range: {time.time()-t0:.2f}s")
            
            t0 = time.time()
            financials = DataLayer.get_sales_financials(self.establishment_id, start_current, end_date)
            _logger.info(f"⏱️ get_sales_financials: {time.time()-t0:.2f}s")
            
            t0 = time.time()
            inventory_summary = DataLayer.get_inventory_summary(self.establishment_id)
            _logger.info(f"⏱️ get_inventory_summary: {time.time()-t0:.2f}s")
            
            t0 = time.time()
            # Obter séries temporais para modelos preditivos e correlações
            timeseries_days = max(90, days * 2) # Pegar mais dados para tendências melhores
            sales_timeseries = DataLayer.get_sales_timeseries(self.establishment_id, timeseries_days)
            _logger.info(f"⏱️ get_sales_timeseries: {time.time()-t0:.2f}s")
            
            t0 = time.time()
            expense_details = DataLayer.get_expense_details(self.establishment_id, timeseries_days)
            _logger.info(f"⏱️ get_expense_details: {time.time()-t0:.2f}s")
        except Exception as e:
            _logger.error(f"Erro ao obter dados base do dashboard: {e}")
            # Fallbacks já tratados nas chamadas individuais, mas garante fluxo
            pass

        try:
            t0 = time.time()
            sales_previous_summary = DataLayer.get_sales_summary_range(
                self.establishment_id, start_previous, end_previous
            )
            _logger.info(f"⏱️ get_sales_summary_range (prev): {time.time()-t0:.2f}s")
        except Exception as e:
            _logger.error(f"Erro ao obter resumo de vendas anterior: {e}")
            sales_previous_summary = {"total_vendas": 0, "total_faturado": 0.0, "ticket_medio": 0.0, "dias_com_venda": 0}

        try:
            inventory_summary = DataLayer.get_inventory_summary(self.establishment_id)
        except Exception as e:
            _logger.error(f"Erro ao obter resumo de estoque: {e}")
            inventory_summary = {"total_produtos": 0, "valor_total": 0.0, "custo_total": 0.0, "itens_baixo_estoque": 0}
        
        # 🔥 ADICIONADO: Detalhes de despesas
        try:
            expense_details = DataLayer.get_expense_details(self.establishment_id, days)
        except Exception as e:
            _logger.error(f"Erro ao obter detalhes de despesas: {e}")
            expense_details = []
        
        # 🔥 NOVO: Dados Financeiros Reais (Faturamento, CMV, Lucro Bruto)
        try:
            financials_data = DataLayer.get_sales_financials(
                self.establishment_id, start_current, end_date
            )
        except Exception as e:
            _logger.error(f"Erro ao obter dados financeiros: {e}")
            financials_data = {"revenue": 0.0, "cogs": 0.0, "gross_profit": 0.0}
        
        revenue = float(financials_data.get("revenue", 0.0))
        cogs = float(financials_data.get("cogs", 0.0))
        gross_profit = float(financials_data.get("gross_profit", 0.0))
        
        # 🔥 CORREÇÃO: Calcular total de despesas para o período
        try:
            total_despesas_periodo = sum([float(exp.get("total", 0) if "total" in exp else exp.get("valor", 0)) for exp in expense_details])
        except Exception:
            total_despesas_periodo = 0.0
        
        # Lucro Líquido = Lucro Bruto - Despesas
        net_profit = gross_profit - total_despesas_periodo
        
        # Margens
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0.0
        net_margin = (net_profit / revenue * 100) if revenue > 0 else 0.0
        
        # ROI (Baseado no custo do estoque médio ou CMV?) 
        avg_inventory_cost = float(inventory_summary.get("valor_total", 0.0))
        roi = (gross_profit / avg_inventory_cost * 100) if avg_inventory_cost > 0 else 0.0
        
        financials_consolidated = {
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "expenses": total_despesas_periodo,
            "net_profit": net_profit,
            "gross_margin": round(gross_margin, 2),
            "net_margin": round(net_margin, 2),
            "roi": round(roi, 2)
        }

        # 2. Obter dados analíticos (horários, clientes)
        try:
            sales_by_hour = DataLayer.get_sales_by_hour(self.establishment_id, days)
        except Exception as e:
            _logger.warning(f"Erro ao obter vendas por hora: {e}")
            sales_by_hour = []

        try:
            top_products_by_hour = DataLayer.get_top_products_by_hour(self.establishment_id, days, top_n=5)
        except Exception as e:
            _logger.warning(f"Erro ao obter top produtos por hora: {e}")
            top_products_by_hour = []

        try:
            customer_temporal_patterns = DataLayer.get_customer_temporal_patterns(self.establishment_id, days=90)
        except Exception as e:
            _logger.warning(f"Erro ao obter padrões de clientes: {e}")
            customer_temporal_patterns = []

        try:
            hourly_concentration = DataLayer.get_hourly_concentration_metrics(self.establishment_id, days)
        except Exception as e:
            _logger.warning(f"Erro ao obter concentração horária: {e}")
            hourly_concentration = {}

        try:
            product_hour_matrix = DataLayer.get_product_hour_correlation_matrix(self.establishment_id, days, top_products=10)
        except Exception as e:
            _logger.warning(f"Erro ao obter matriz de correlação: {e}")
            product_hour_matrix = []

        try:
            customer_product_affinity = DataLayer.get_customer_product_affinity(self.establishment_id, days=90, min_support=3)
        except Exception as e:
            _logger.warning(f"Erro ao obter afinidade de clientes: {e}")
            customer_product_affinity = []

        try:
            hourly_customer_behavior = DataLayer.get_hourly_customer_behavior(self.establishment_id, days=60)
        except Exception as e:
            _logger.warning(f"Erro ao obter comportamento de clientes: {e}")
            hourly_customer_behavior = []

        # 🔥 NOVO: Análises Temporais Avançadas
        from .temporal_analysis import TemporalAnalysis
        try:
            hourly_sales_by_category = TemporalAnalysis.get_hourly_sales_by_category(self.establishment_id, days)
        except Exception: hourly_sales_by_category = {}
        
        try:
            period_analysis = TemporalAnalysis.get_period_analysis(self.establishment_id, days)
        except Exception: period_analysis = {}
        
        try:
            weekday_analysis = TemporalAnalysis.get_weekday_analysis(self.establishment_id, days)
        except Exception: weekday_analysis = {}
        
        try:
            product_hourly_recommendations = TemporalAnalysis.get_product_hourly_recommendations(self.establishment_id, days)
        except Exception: product_hourly_recommendations = []
        
        try:
            category_performance_by_time = TemporalAnalysis.get_category_performance_by_time(self.establishment_id, days)
        except Exception: category_performance_by_time = {}

        # 3. Análise ABC e RFM
        try:
            abc_analysis = self.get_abc_analysis(days=days, limit=500)
        except Exception as e:
            _logger.error(f"Erro na análise ABC: {e}")
            abc_analysis = {"produtos": [], "resumo": {}, "total_value": 0}
            
        try:
            customer_metrics = DataLayer.get_customer_metrics(self.establishment_id, days)
        except Exception:
            customer_metrics = {"ticket_medio": 0, "clientes_unicos": 0, "novos_clientes": 0, "vendas_no_periodo": 0}

        try:
            rh_metrics = DataLayer.get_rh_metrics(self.establishment_id, days)
        except Exception as e:
            _logger.warning(f"Erro ao obter métricas de RH: {e}")
            rh_metrics = {}
        
        # 4. Timeseries e Forecast
        try:
            timeseries_days = max(days, 90)
            sales_timeseries = DataLayer.get_sales_timeseries(self.establishment_id, timeseries_days)
            _logger.info(f"📊 Timeseries retornado: {len(sales_timeseries)} dias de dados")
        except Exception as e:
            _logger.error(f"Erro ao carregar timeseries: {e}")
            sales_timeseries = []
        
        try:
            forecast = PracticalModels.generate_forecast(sales_timeseries) if sales_timeseries else []
        except Exception as e:
            _logger.warning(f"Erro ao gerar forecast: {e}")
            forecast = []

        # 5. Métricas de Comparação
        # 🔥 CORREÇÃO: Usar a MESMA fonte de dados (get_sales_summary_range) para ambos os períodos
        # Anteriormente, current usava get_sales_financials (JOIN inflado) e previous usava get_sales_summary_range
        # Isso causava comparações assimétricas e crescimento incorreto
        current_faturado = float(sales_current_summary.get("total_faturado", 0))
        previous_faturado = float(sales_previous_summary.get("total_faturado", 0))
        
        sales_current_metric = {
            "value": current_faturado,
            "confidence": _confidence_from_samples(
                sales_current_summary.get("total_vendas", 0)
            ),
            "sample_size": sales_current_summary.get("total_vendas", 0),
            "warnings": [],
        }
        sales_previous_metric = {
            "value": previous_faturado,
            "confidence": _confidence_from_samples(
                sales_previous_summary.get("total_vendas", 0)
            ),
            "sample_size": sales_previous_summary.get("total_vendas", 0),
            "warnings": [],
        }

        try:
            growth_period = StatsValidator.calculate_growth(
                current_value=sales_current_metric.get("value", 0),
                previous_value=sales_previous_metric.get("value", 0),
                current_samples=sales_current_metric.get("sample_size", 0),
                previous_samples=sales_previous_metric.get("sample_size", 0),
            )
        except Exception:
            growth_period = {"value": 0.0, "display": "0%", "status": "no_data", "is_positive": False, "icon": "minus"}


        growth_homologo_week = None
        if days >= 14:
            start_week_current = end_date - timedelta(days=7)
            start_week_previous = end_date - timedelta(days=14)
            end_week_previous = end_date - timedelta(days=7)
            week_current = DataLayer.get_sales_summary_range(
                self.establishment_id, start_week_current, end_date
            )
            week_previous = DataLayer.get_sales_summary_range(
                self.establishment_id, start_week_previous, end_week_previous
            )
            growth_homologo_week = StatsValidator.calculate_growth(
                current_value=week_current.get("total_faturado", 0),
                previous_value=week_previous.get("total_faturado", 0),
                current_samples=week_current.get("total_vendas", 0),
                previous_samples=week_previous.get("total_vendas", 0),
            )

        try:
            sales_trend = _PM.detect_sales_trend(sales_timeseries)
        except Exception as e:
            _logger.warning(f"Erro ao detectar tendência de vendas: {e}")
            sales_trend = {"direction": "neutral", "slope": 0, "is_statistically_significant": False}
        
        # 🔥 NOVO: Calcular correlações estatísticas
        try:
            correlations = _PM.calculate_correlations(sales_timeseries, expense_details)
        except Exception as e:
            _logger.warning(f"Erro ao calcular correlações: {e}")
            correlations = []
        
        # 🔥 NOVO: Detectar anomalias
        try:
            anomalies = _PM.detect_anomalies(sales_timeseries, expense_details)
        except Exception as e:
            _logger.warning(f"Erro ao detectar anomalias: {e}")
            anomalies = []

        # abc_analysis já foi calculado acima
        rfm_analysis = self.get_rfm_analysis(window_days=180)
        
        # 🔥 NOVO: Produtos Estrela (Top 10 da Classe A com melhor margem)
        produtos_estrela = []
        if abc_analysis and abc_analysis.get("produtos"):
            produtos_classe_a = [p for p in abc_analysis["produtos"] if p.get("classificacao") == "A"]
            # Ordenar por margem e pegar top 10
            produtos_classe_a_sorted = sorted(
                produtos_classe_a,
                key=lambda x: x.get("margem", 0),
                reverse=True
            )[:10]
            
            for p in produtos_classe_a_sorted:
                produtos_estrela.append({
                    "id": p.get("id", 0),
                    "nome": p.get("nome", ""),
                    "classificacao": "A",
                    "margem": p.get("margem", 0),
                    "market_share": p.get("percentual_acumulado", 0),
                    "total_vendido": p.get("quantidade_vendida", 0),
                    "custo_unitario": p.get("preco_custo", 0),
                    "preco_venda": p.get("preco_venda", 0) if "preco_venda" in p else 0,
                    "lucro_total": p.get("faturamento", 0) * (p.get("margem", 0) / 100),
                    "roi": (p.get("margem", 0) / 100) if p.get("preco_custo", 0) > 0 else 0,
                    "elasticidade": 0,
                    "faturamento": p.get("faturamento", 0),
                    "quantidade_vendida": p.get("quantidade_vendida", 0)
                })
        
        # 🔥 NOVO: Produtos Lentos (Classe C ou produtos com menor desempenho)
        produtos_lentos = []
        if abc_analysis and abc_analysis.get("produtos"):
            from app.models import Produto
            
            # Tentar pegar Classe C primeiro
            produtos_classe_c = [p for p in abc_analysis["produtos"] if p.get("classificacao") == "C"]
            
            # Se não tiver Classe C, pegar os 10 piores da Classe B
            if not produtos_classe_c:
                produtos_classe_b = [p for p in abc_analysis["produtos"] if p.get("classificacao") == "B"]
                produtos_lentos_candidatos = sorted(
                    produtos_classe_b,
                    key=lambda x: x.get("quantidade_vendida", 0)
                )[:10]
            else:
                # Pegar os 10 piores da classe C
                produtos_lentos_candidatos = sorted(
                    produtos_classe_c,
                    key=lambda x: x.get("quantidade_vendida", 0)
                )[:10]
            
            produto_ids_lentos = [p.get("id") for p in produtos_lentos_candidatos if p.get("id")]
            
            # 🔥 CORREÇÃO: Buscar produtos do banco com todos os dados necessários
            produtos_db_lentos = Produto.query.filter(
                Produto.estabelecimento_id == self.establishment_id,
                Produto.id.in_(produto_ids_lentos)
            ).all()
            
            # Criar mapa com estoque E preço de custo do banco (dados reais)
            produtos_db_map = {
                p.id: {
                    'estoque': p.quantidade,
                    'preco_custo': float(p.preco_custo) if p.preco_custo else 0.0
                } 
                for p in produtos_db_lentos
            }
            
            for p in produtos_lentos_candidatos:
                produto_id = p.get("id", 0)
                qtd_vendida = p.get("quantidade_vendida", 0)
                
                # 🔥 CORREÇÃO: Pegar estoque e preço de custo REAIS do banco
                produto_db_data = produtos_db_map.get(produto_id, {'estoque': 0, 'preco_custo': 0})
                estoque_atual = produto_db_data['estoque']
                preco_custo = produto_db_data['preco_custo']
                
                # Se preco_custo do banco for 0, tentar pegar do ABC
                if preco_custo == 0:
                    preco_custo = p.get("preco_custo", 0)
                
                # Calcular giro de estoque (vendas / estoque médio)
                # Para produtos lentos, o giro será baixo
                giro_estoque = (qtd_vendida / estoque_atual) if estoque_atual > 0 else 0
                
                demanda_diaria = qtd_vendida / days if days > 0 else 0

                # Calcular dias de estoque parado
                # Se estoque <= 0, dias de estoque é 0 (esgotado, não encalhado)
                if estoque_atual <= 0:
                    dias_estoque = 0
                elif demanda_diaria > 0:
                    dias_estoque = estoque_atual / demanda_diaria
                else:
                    dias_estoque = 999 # Infinito (tem estoque mas não tem saída)
                
                # 🔥 CORREÇÃO: Custo do capital parado = preço de custo × estoque atual
                custo_parado = preco_custo * estoque_atual
                
                # 🔥 CORREÇÃO: Perda mensal = 1% do capital parado (custo de oportunidade)
                perda_mensal = custo_parado * 0.01
                
                produtos_lentos.append({
                    "id": produto_id,
                    "nome": p.get("nome", ""),
                    "quantidade": qtd_vendida,
                    "total_vendido": p.get("faturamento", 0),
                    "dias_estoque": round(dias_estoque, 0) if dias_estoque < 999 else 999,
                    "giro_estoque": round(giro_estoque, 2),
                    "custo_parado": round(custo_parado, 2),
                    "perda_mensal": round(perda_mensal, 2),
                    "estoque_atual": estoque_atual,
                    "margem": p.get("margem", 0),
                    "classificacao": p.get("classificacao", "B")
                })
        
        # 🔥 NOVO: Previsão de Demanda (Top 20 produtos com previsão)
        previsao_demanda = []
        if abc_analysis and abc_analysis.get("produtos"):
            from app.models import Produto
            
            top_20_produtos = abc_analysis["produtos"][:20]
            produto_ids = [p.get("id") for p in top_20_produtos if p.get("id")]
            
            # Buscar estoque real dos produtos
            produtos_db = Produto.query.filter(
                Produto.estabelecimento_id == self.establishment_id,
                Produto.id.in_(produto_ids)
            ).all()
            
            estoque_map = {p.id: p.quantidade for p in produtos_db}
            
            for p in top_20_produtos:
                produto_id = p.get("id", 0)
                qtd_vendida = p.get("quantidade_vendida", 0)
                demanda_diaria = qtd_vendida / days if days > 0 else 0
                estoque_atual = estoque_map.get(produto_id, 0)
                
                # Calcular giro de estoque
                giro_estoque = (qtd_vendida / estoque_atual) if estoque_atual > 0 else 0
                
                previsao_demanda.append({
                    "id": produto_id,
                    "produto_nome": p.get("nome", ""),
                    "nome": p.get("nome", ""),
                    "estoque_atual": estoque_atual,
                    "demanda_diaria_prevista": round(demanda_diaria, 2),
                    "risco_ruptura": (estoque_atual / demanda_diaria < 7) if demanda_diaria > 0 else False,
                    "margem_lucro": p.get("margem", 0),
                    "custo_estoque": p.get("preco_custo", 0) * estoque_atual,
                    "giro_estoque": round(giro_estoque, 2),
                    "classificação_abc": p.get("classificacao", "C"),
                    "variavel": p.get("nome", ""),
                    "valor_atual": p.get("faturamento", 0),
                    "previsao_30d": p.get("faturamento", 0) * 1.1,  # Previsão simples: +10%
                    "confianca": 75.0,
                    "intervalo_confianca": [
                        p.get("faturamento", 0) * 0.9,
                        p.get("faturamento", 0) * 1.3
                    ]
                })

        risco_ids = [
            c["cliente_id"]
            for c in rfm_analysis.get("customers", [])
            if c.get("segment") in {"Risco", "Perdido"}
        ][:50]
        clientes_risco = []
        if risco_ids:
            rows = (
                Cliente.query.filter(
                    Cliente.estabelecimento_id == self.establishment_id,
                    Cliente.id.in_(risco_ids),
                )
                .all()
            )
            by_id = {int(c.id): c for c in rows}
            for cid in risco_ids:
                cli = by_id.get(int(cid))
                if not cli:
                    continue
                clientes_risco.append(
                    {"id": int(cli.id), "nome": cli.nome, "celular": cli.celular}
                )

        segments = rfm_analysis.get("segments", {}) or {}
        count_risco = int(segments.get("Risco", 0) or 0) + int(
            segments.get("Perdido", 0) or 0
        )

        recomendacoes = []
        if count_risco > 0:
            recomendacoes.append(
                {
                    "tipo": "retencao",
                    "mensagem": f"{count_risco} clientes em risco de abandono identificados.",
                    "cta": "Clique para gerar lista de WhatsApp",
                    "alvo": "clientes",
                    "segmentos": ["Risco", "Perdido"],
                    "clientes": clientes_risco,
                }
            )

        baixo_estoque = int(inventory_summary.get("baixo_estoque", 0) or 0)
        if baixo_estoque > 0:
            recomendacoes.append(
                {
                    "tipo": "estoque",
                    "mensagem": f"{baixo_estoque} produtos com estoque baixo. Repor para evitar ruptura.",
                    "cta": "Ver lista de estoque baixo",
                    "alvo": "produtos",
                }
            )

        if growth_period.get("growth") is not None and growth_period.get("growth") < -10:
            recomendacoes.append(
                {
                    "tipo": "vendas",
                    "mensagem": "Queda relevante no faturamento versus período equivalente.",
                    "cta": "Analisar produtos e clientes por período",
                    "alvo": "dashboard",
                }
            )

        margem_a = float(abc_analysis.get("resumo", {}).get("A", {}).get("margem_media", 0) or 0)
        margem_b = float(abc_analysis.get("resumo", {}).get("B", {}).get("margem_media", 0) or 0)
        if margem_b > margem_a + 5:
            recomendacoes.append(
                {
                    "tipo": "margem",
                    "mensagem": "Classe B com margem média maior que a Classe A. Priorize reposição e exposição dos B rentáveis.",
                    "cta": "Filtrar produtos por margem",
                    "alvo": "produtos",
                }
            )

        # 🔥 CORREÇÃO: Calcular total de despesas para o período
        total_despesas_periodo = sum([float(exp.get("valor", 0)) for exp in expense_details])
        
        # 🔥 NOVO: "LINK EACH PRODUCT TO AN ORDER"
        # Coletar todos os IDs de produtos em destaque para buscar última compra de forma eficiente (1 única query)
        todos_mais_vendidos_ids = set()
        for p in produtos_estrela: 
            if p.get('id'): todos_mais_vendidos_ids.add(p['id'])
        for p in produtos_lentos: 
            if p.get('id'): todos_mais_vendidos_ids.add(p['id'])
        for p in previsao_demanda: 
            if p.get('id'): todos_mais_vendidos_ids.add(p['id'])
        
        last_orders = DataLayer.get_last_purchase_orders(self.establishment_id, list(todos_mais_vendidos_ids))
        
        # Injetar dados de última compra nos produtos para o dashboard
        for p in produtos_estrela:
            pid = p.get("id")
            p["ultima_compra"] = last_orders.get(pid) if pid else None
        for p in produtos_lentos:
            pid = p.get("id")
            p["ultima_compra"] = last_orders.get(pid) if pid else None
        for p in previsao_demanda:
            pid = p.get("id")
            p["ultima_compra"] = last_orders.get(pid) if pid else None
        
        # 11. Montar objeto final
        res = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "period_days": int(days),
            "summary": {
                "sales_current": DashboardSerializer.serialize_metric(sales_current_metric),
                "sales_previous": DashboardSerializer.serialize_metric(sales_previous_metric),
                "growth_period": DashboardSerializer.serialize_growth(growth_period),
                "growth": DashboardSerializer.serialize_growth(growth_period),  # 🔥 ALIAS para compatibilidade frontend
                "growth_homologo_week": (
                    DashboardSerializer.serialize_growth(growth_homologo_week)
                    if growth_homologo_week
                    else {"value": None, "display": "--", "status": "no_data", "is_positive": False, "icon": "minus"}
                ),
                "revenue": revenue,
                "expenses": total_despesas_periodo,
                "gross_profit": gross_profit,
                "net_profit": net_profit,
                "inventory_value": inventory_summary.get("valor_total", 0),
                "low_stock_count": inventory_summary.get("baixo_estoque", 0),
                "avg_ticket": {
                    "value": sales_current_summary.get("ticket_medio", 0),
                    "display": f"R$ {sales_current_summary.get('ticket_medio', 0):,.2f}",
                    "status": "high_confidence",
                },
                "unique_customers": customer_metrics.get("clientes_unicos", 0),
            },
            "financials": financials_consolidated,
            "timeseries": sales_timeseries,
            "forecast": forecast,
            "expenses": expense_details,
            "total_despesas": total_despesas_periodo,
            "sales_by_hour": sales_by_hour,
            "top_products_by_hour": top_products_by_hour,
            "customer_temporal_patterns": customer_temporal_patterns,
            "hourly_concentration": hourly_concentration,
            "product_hour_matrix": product_hour_matrix,
            "customer_product_affinity": customer_product_affinity,
            "hourly_customer_behavior": hourly_customer_behavior,
            "hourly_sales_by_category": hourly_sales_by_category,
            "period_analysis": period_analysis,
            "weekday_analysis": weekday_analysis,
            "product_hourly_recommendations": product_hourly_recommendations,
            "category_performance_by_time": category_performance_by_time,
            "abc": abc_analysis,
            "rfm": {"segments": segments, "window_days": rfm_analysis.get("window_days", 180)},
            "recomendacoes": recomendacoes,
            "correlations": correlations,
            "anomalies": anomalies,
            "produtos_estrela": produtos_estrela,
            "produtos_lentos": produtos_lentos,
            "previsao_demanda": previsao_demanda,
            "rh": rh_metrics,
            "inventory": inventory_summary,
            "trend": sales_trend,
            "_performance": {
                "total_time": time.time() - start_exec
            }
        }
        return res

    @cache_response(ttl_seconds=900, require_db_check=True)
    def get_abc_analysis(self, days: int = 30, limit: int = 500) -> Dict[str, Any]:
        from app.models import db
        try:
            top_products = DataLayer.get_top_products(self.establishment_id, days, int(limit))
            return PracticalModels.analyze_inventory_abc(
                [
                    {
                        "id": p.get("id", 0),
                        "nome": p.get("nome", ""),
                        "valor_total": p.get("faturamento", 0),
                        "quantidade": p.get("quantidade_vendida", 0),
                        "preco_custo": p.get("preco_custo", 0),
                    }
                    for p in top_products
                ],
                top_n=None,  # Retornar TODOS os produtos, não limitar
                return_all_products=True,  # Forçar retorno de todos
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro na análise ABC: {e}")
            return {"produtos": [], "resumo": {}, "total_value": 0}

    @cache_response(ttl_seconds=900, require_db_check=True)
    def get_rfm_analysis(self, window_days: int = 180) -> Dict[str, Any]:
        from app.models import Cliente, db
        try:
            return Cliente.calcular_rfm(self.establishment_id, days=int(window_days))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro na análise RFM: {e}")
            return {"customers": [], "segments": {}}
