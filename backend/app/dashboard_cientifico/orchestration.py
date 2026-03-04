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
from .temporal_analysis import TemporalAnalysis
from .serializers import DashboardSerializer
from .cache_layer import cache_response

# Alias para facilitar uso em cálculos
_PM = PracticalModels

# Logger global - DEVE estar no nível do módulo
logger = logging.getLogger(__name__)


class DashboardOrchestrator:
    """Orquestra a geração do dashboard"""

    def __init__(self, establishment_id: int):
        self.establishment_id = establishment_id

    @cache_response(ttl_seconds=60, require_db_check=False)
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

    @cache_response(ttl_seconds=5, require_db_check=False)  # 🔥 CACHE REDUZIDO PARA DEBUG (Era 300)
    def get_scientific_dashboard(
        self,
        days: int = 30,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Dashboard científico - Análise avançada com insights.
        Se start_date e end_date forem fornecidos, usa esse período; senão usa os últimos N dias.
        """
        from app.models import db
        import logging
        _logger = logging.getLogger(__name__)
        try:
            return self._get_scientific_dashboard_logic(days, start_date, end_date)
        except Exception as e:
            from app.models import db
            db.session.rollback()
            _logger.error(f"Erro CRÍTICO no dashboard científico: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _get_scientific_dashboard_logic(
        self,
        days: int = 30,
        start_date_override: datetime = None,
        end_date_override: datetime = None
    ) -> Dict[str, Any]:
        import logging
        _logger = logging.getLogger(__name__)
        
        from datetime import timedelta
        end_date = end_date_override if end_date_override else datetime.utcnow()
        if start_date_override and end_date_override:
            start_current = start_date_override
        else:
            # 🔥 CORREÇÃO: Forçar início do dia para capturar despesas/vendas do primeiro dia completo
            start_current = (end_date - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        def _confidence_from_samples(samples: int) -> str:
            """Função auxiliar para calcular confiança baseada em amostras"""
            if samples < 5:
                return "INSUFICIENT"
            if samples < 15:
                return "LOW"
            if samples < 30:
                return "MEDIUM"
            return "HIGH"
        
        from app.models import Cliente
        from app.dashboard_cientifico.models_layer import PracticalModels as _PM
        # Ajustar período anterior também
        start_previous = (start_current - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_previous = (start_current - timedelta(seconds=1))

        import time
        from flask import current_app
        start_exec = time.time()
        
        # Obter a instância da app (para logs ou acesso ao config se necessário)
        app = current_app._get_current_object()
        
        # 🔥 ALTERAÇÃO CRÍTICA: Executar queries FINANCEIRAS fundamentais de forma SÍNCRONA
        # Isso garante que não haja falhas silenciosas de thread pool para os números mais importantes (Lucro, Despesas)
        try:
            financials_data = DataLayer.get_sales_financials(self.establishment_id, start_current, end_date)
            # Garantir que a lista de despesas nunca seja vazia por erro de thread
            expense_details = DataLayer.get_expense_details(self.establishment_id, start_current, end_date)
            sales_current_summary = DataLayer.get_sales_summary_range(self.establishment_id, start_current, end_date)
            sales_previous_summary = DataLayer.get_sales_summary_range(self.establishment_id, start_previous, end_previous)
        except Exception as e:
            _logger.error(f"Erro ao buscar dados financeiros síncronos: {e}")
            financials_data = {"revenue": 0.0, "cogs": 0.0, "gross_profit": 0.0}
            expense_details = []
            sales_current_summary = {"total_vendas": 0, "total_faturado": 0.0, "ticket_medio": 0.0, "dias_com_venda": 0}
            sales_previous_summary = {"total_vendas": 0, "total_faturado": 0.0, "ticket_medio": 0.0, "dias_com_venda": 0}

        # 1. Obter métricas secundárias e pesadas de forma SÍNCRONA e SEGURA
        # Otimização: Removido ThreadPoolExecutor para evitar "QueuePool limit overflow"
        # A execução sequencial é mais estável em ambientes com conexões limitadas (Aiven/Render)
        
        _logger.info(f"START: Coleta de dados secundários sequencial (est_id: {self.establishment_id})")
        
        def safe_get(func, name, default, *args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _logger.warning(f"⚠️ Query '{name}' falhou: {e}")
                return default

        inventory_summary = safe_get(DataLayer.get_inventory_summary, "inventory", 
                                   {"total_produtos": 0, "valor_total": 0.0, "custo_total": 0.0, "baixo_estoque": 0}, 
                                   self.establishment_id)
        
        sales_by_hour = safe_get(DataLayer.get_sales_by_hour, "sales_hour", [], 
                               self.establishment_id, days)
                               
        top_products_by_hour = safe_get(DataLayer.get_top_products_by_hour, "top_hour", [], 
                                      self.establishment_id, days, top_n=5)
                                      
        customer_temporal_patterns = safe_get(DataLayer.get_customer_temporal_patterns, "cust_patterns", [], 
                                            self.establishment_id, days=90)
                                            
        hourly_concentration = safe_get(DataLayer.get_hourly_concentration_metrics, "hourly_conc", {}, 
                                      self.establishment_id, days)
        
        hourly_sales_by_category = safe_get(TemporalAnalysis.get_hourly_sales_by_category, "hourly_cat", {}, 
                                          self.establishment_id, days)
                                          
        period_analysis = safe_get(TemporalAnalysis.get_period_analysis, "period_anal", {}, 
                                 self.establishment_id, days)
                                 
        weekday_analysis = safe_get(TemporalAnalysis.get_weekday_analysis, "weekday_anal", {}, 
                                  self.establishment_id, days)
                                  
        rh_metrics = safe_get(DataLayer.get_rh_metrics, "rh_metrics", {}, 
                            self.establishment_id, days)
                            
        sales_timeseries = safe_get(DataLayer.get_sales_timeseries, "sales_series", [], 
                                  self.establishment_id, max(days, 90))

        # 🔥 FIADO: Métricas de Carteira de Crédito (dados reais de exposição)
        fiado_metrics = safe_get(DataLayer.get_fiado_metrics, "fiado_metrics",
                                {"total_aberto": 0.0, "total_limite": 0.0, "clientes_com_fiado": 0,
                                 "percentual_limite_utilizado": 0.0, "maior_devedor_nome": "",
                                 "maior_devedor_valor": 0.0, "ticket_medio_fiado": 0.0,
                                 "percentual_clientes_com_fiado": 0.0, "top_devedores": []},
                                self.establishment_id)

        receivables_metrics = safe_get(DataLayer.get_receivables_metrics, "receivables",
                                     {"total_vencido": 0.0, "total_a_vencer": 0.0, "total_recebivel": 0.0,
                                      "taxa_inadimplencia": 0.0, "titulos_vencidos": 0, "ranking_atraso": []},
                                     self.establishment_id)
        
        # Análises mais pesadas
        # 🔥 CORREÇÃO: Usar get_all_products_performance para incluir produtos sem vendas na análise ABC
        abc_analysis = safe_get(self.get_abc_analysis, "abc", 
                              {"produtos": [], "resumo": {}, "total_value": 0}, 
                              days=days, limit=None) # Limit None para pegar tudo
                              
        # 🔥 NOVO: Coletando Produtos Próximos do Vencimento (30 dias)
        expiring_products = safe_get(DataLayer.get_expiring_products, "expiring_products", [],
                                   self.establishment_id, 30)
                              
        customer_metrics = safe_get(DataLayer.get_customer_metrics, "cust_metrics", 
                                  {"ticket_medio": 0, "clientes_unicos": 0, "novos_clientes": 0, "vendas_no_periodo": 0}, 
                                  self.establishment_id, days)
                                  
        product_hourly_recommendations = safe_get(TemporalAnalysis.get_product_hourly_recommendations, "recomm", [], 
                                                self.establishment_id, days)
                                                
        category_performance_by_time = safe_get(TemporalAnalysis.get_category_performance_by_time, "cat_perf", {}, 
                                              self.establishment_id, days)

        _logger.info(f"DONE: Coleta sequencial concluida em {time.time()-start_exec:.2f}s")

        # Dados Financeiros Reais (processar resultados coletados)
        revenue = float(financials_data.get("revenue", 0.0))
        cogs = float(financials_data.get("cogs", 0.0))
        gross_profit = float(financials_data.get("gross_profit", 0.0))
        
        # 🔥 CORREÇÃO FINAL: Usar Single Source of Truth para Despesas (Mesma query do DRE)
        # Eliminamos a tentativa de somar o detalhamento agrupado, que estava falhando.
        try:
            total_despesas_periodo = DataLayer.get_total_expenses_value(self.establishment_id, start_current, end_date)
            _logger.info(f"Dashboard Net Profit Calculation: Gross={gross_profit}, Expenses={total_despesas_periodo}")
        except Exception as e:
            _logger.error(f"Erro crítico ao buscar total de despesas: {e}")
            total_despesas_periodo = 0.0
        
        # Lucro Líquido = Lucro Bruto - Despesas
        net_profit = gross_profit - total_despesas_periodo
        
        # Margens
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0.0
        net_margin = (net_profit / revenue * 100) if revenue > 0 else 0.0
        
        # ROI (Net Profit / Inventory Value)
        avg_inventory_cost = float(inventory_summary.get("valor_total", 0.0))
        roi = (net_profit / avg_inventory_cost * 100) if avg_inventory_cost > 0 else 0.0
        
        financials_consolidated = {
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "expenses": total_despesas_periodo,
            "net_profit": net_profit,
            "gross_margin": gross_margin,
            "net_margin": net_margin,
            "roi": roi,
            "count": int(financials_data.get("count", 0))
        }


        # Sub-queries que dependem ou são mais pesadas
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

        try:
            forecast = PracticalModels.generate_forecast(sales_timeseries)
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
            correlations = _PM.calculate_correlations(sales_timeseries, expense_details, establishment_id=self.establishment_id)
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

        # ============================================================
        # 🧠 MOTOR DE INTELIGÊNCIA DE NEGÓCIO (BI ENGINE)
        # 8 cenários profissionais com impacto financeiro quantificado,
        # linguagem contextual e CTAs acionáveis.
        # Prioridade: 1=crítico, 2=urgente, 3=oportunidade
        # ============================================================
        recomendacoes = []

        _ticket_medio = float(sales_current_summary.get("ticket_medio", 0))
        _fiado_total = float(fiado_metrics.get("total_aberto", 0))
        _fiado_clientes = int(fiado_metrics.get("clientes_com_fiado", 0))
        _fiado_perc_fat = (_fiado_total / revenue * 100) if revenue > 0 else 0.0
        _baixo_estoque = int(inventory_summary.get("baixo_estoque", 0) or 0)
        _margem_a = float(abc_analysis.get("resumo", {}).get("A", {}).get("margem_media", 0) or 0)
        _margem_b = float(abc_analysis.get("resumo", {}).get("B", {}).get("margem_media", 0) or 0)
        # growth_period usa chave 'value' (de StatsValidator.calculate_growth)
        _growth_val = float(growth_period.get("value", 0) or 0)
        # previous_faturado já foi calculado acima na seção de comparação (linha ~377)

        # --- CENÁRIO 1: PREJUÍZO OPERACIONAL ---------------------------
        if net_profit < 0:
            causa = ""
            if total_despesas_periodo > gross_profit:
                causa = (f"Suas despesas (R$ {total_despesas_periodo:,.2f}) "
                         f"consumiram {(total_despesas_periodo/gross_profit*100 if gross_profit > 0 else 0):.0f}% "
                         f"do Lucro Bruto (R$ {gross_profit:,.2f}).")
            elif gross_margin < 20:
                causa = (f"A Margem Bruta de {gross_margin:.1f}% está muito baixa "
                         f"— você está vendendo quase a preço de custo.")
            else:
                causa = f"A estrutura de custos superou o faturamento em R$ {abs(net_profit):,.2f}."
            recomendacoes.append({
                "tipo": "financeiro_critico",
                "prioridade": 1,
                "mensagem": (
                    f"🚨 PREJUÍZO DE R$ {abs(net_profit):,.2f} no período. {causa} "
                    f"Corte pelo menos R$ {abs(net_profit):,.2f} em custos para zerar o prejuízo."
                ),
                "impacto_estimado": round(abs(net_profit), 2),
                "cta": "Auditar Despesas",
                "alvo": "despesas",
                "icone": "🚨"
            })

        # --- CENÁRIO 2: MARGEM LÍQUIDA EM ZONA DE RISCO ----------------
        elif 0 < net_margin < 5:
            recomendacoes.append({
                "tipo": "eficiencia",
                "prioridade": 2,
                "mensagem": (
                    f"⚠️ MARGEM LÍQUIDA FRÁGIL: {net_margin:.1f}% — qualquer imprevisto coloca o negócio no vermelho. "
                    f"Com faturamento de R$ {revenue:,.2f}, você tem apenas R$ {net_profit:,.2f} de colchão. "
                    f"Meta recomendada para varejo: margem líquida ≥ 8%."
                ),
                "impacto_estimado": round((0.08 - net_margin / 100) * revenue, 2),
                "cta": "Ver Análise de Margens",
                "alvo": "analise-financeira",
                "icone": "⚠️"
            })

        # --- CENÁRIO 3: MARKUP ABAIXO DO PADRÃO VAREJO ----------------
        if gross_margin < 25 and revenue > 0 and net_profit >= 0:
            # Projetar aumento real considerando ganho marginal de 5 pontos
            # Impacto não deve exceder 15% do faturamento total para ser realista
            impacto_markup = min(revenue * 0.05, revenue * 0.15)
            recomendacoes.append({
                "tipo": "precificacao",
                "prioridade": 1 if gross_margin < 15 else 2,
                "mensagem": (
                    f"💰 MARKUP ABAIXO DO MERCADO: Margem Bruta {gross_margin:.1f}% "
                    f"(referência saudável: 25-35% para supermercado). "
                    f"Aumentar o markup médio em 5 p.p. geraria "
                    f"+R$ {revenue * 0.05:,.2f} adicionais por período."
                ),
                "impacto_estimado": round(impacto_markup, 2),
                "cta": "Revisar Precificação",
                "alvo": "produtos",
                "icone": "💰"
            })

        # --- CENÁRIO 4: CLIENTES EM RISCO DE CHURN (RFM) ---------------
        if count_risco > 0:
            # Impacto estimado: recuperacao de 30% do faturado medio desses clientes
            # Capamos a receita_risco para nao gerar valores astronomicos em dados de teste
            base_calculo = min(revenue * 0.3, _ticket_medio * count_risco)
            impacto_retencao = base_calculo * 0.5 # Projetamos recuperar 50% do risco plausivel
            
            recomendacoes.append({
                "tipo": "retencao",
                "prioridade": 2,
                "mensagem": (
                    f"👥 {count_risco} CLIENTES EM RISCO DE ABANDONO identificados pelo modelo RFM. "
                    f"Ticket médio deles: R$ {_ticket_medio:,.2f}. "
                    f"Recuperar metade deste grupo geraria ~R$ {impacto_retencao:,.2f} adicionais. "
                    f"Consulte a lista de nomes nos detalhes para ação direta."
                ),
                "impacto_estimado": round(impacto_retencao, 2),
                "cta": "Ver Clientes em Risco",
                "alvo": "clientes",
                "segmentos": ["Risco", "Perdido"],
                "clientes": clientes_risco[:20], # Limitar a 20 para o modal
                "icone": "👥"
            })

        # --- CENÁRIO 5: EXPOSIÇÃO DE FIADO / CRÉDITO --------------------
        if _fiado_total > 0:
            if _fiado_perc_fat >= 10:
                recomendacoes.append({
                    "tipo": "fiado_critico",
                    "prioridade": 1,
                    "mensagem": (
                        f"🤝 ALERTA DE CRÉDITO: R$ {_fiado_total:,.2f} de fiado em aberto "
                        f"({_fiado_perc_fat:.1f}% do seu faturamento) com {_fiado_clientes} clientes. "
                        f"Maior devedor: {fiado_metrics.get('maior_devedor_nome', 'N/A')} "
                        f"(R$ {fiado_metrics.get('maior_devedor_valor', 0):,.2f}). "
                        f"Fiado excessivo compromete o fluxo de caixa."
                    ),
                    "impacto_estimado": round(_fiado_total, 2),
                    "cta": "Ver Clientes com Fiado",
                    "alvo": "clientes",
                    "top_devedores": fiado_metrics.get("top_devedores", []),
                    "icone": "🤝"
                })
            else:
                recomendacoes.append({
                    "tipo": "fiado_atencao",
                    "prioridade": 3,
                    "mensagem": (
                        f"🤝 Carteira de fiado: R$ {_fiado_total:,.2f} em aberto "
                        f"({_fiado_perc_fat:.1f}% do faturamento) com {_fiado_clientes} clientes. "
                        f"Monitore para evitar crescimento da inadimplência."
                    ),
                    "impacto_estimado": round(_fiado_total, 2),
                    "cta": "Gestão de Fiado",
                    "alvo": "clientes",
                    "top_devedores": fiado_metrics.get("top_devedores", []),
                    "icone": "🤝"
                })

        # --- CENÁRIO 6: ESTOQUE BAIXO -----------------------------------
        if _baixo_estoque > 0:
            perda_potencial = _ticket_medio * _baixo_estoque * 0.3
            recomendacoes.append({
                "tipo": "estoque",
                "prioridade": 2 if _baixo_estoque > 5 else 3,
                "mensagem": (
                    f"📦 {_baixo_estoque} produto{'s' if _baixo_estoque > 1 else ''} abaixo do estoque mínimo. "
                    f"Ruptura em itens Classe A pode gerar perda estimada de "
                    f"R$ {perda_potencial:,.2f} em vendas. Priorize a reposição imediata."
                ),
                "impacto_estimado": round(perda_potencial, 2),
                "cta": "Ver Estoque Baixo",
                "alvo": "produtos",
                "icone": "📦"
            })

        # --- CENÁRIO 7: QUEDA NO FATURAMENTO ---------------------------
        if _growth_val < -10:
            delta_receita = abs(_growth_val / 100 * previous_faturado)
            recomendacoes.append({
                "tipo": "vendas_queda",
                "prioridade": 2,
                "mensagem": (
                    f"📉 QUEDA DE {abs(_growth_val):.1f}% NO FATURAMENTO vs período anterior. "
                    f"Isso representa R$ {delta_receita:,.2f} a menos em receita. "
                    f"Verifique produtos Classe A em falta, promoções da concorrência ou sazonalidade."
                ),
                "impacto_estimado": round(delta_receita, 2),
                "cta": "Analisar Tendência",
                "alvo": "dashboard",
                "icone": "📉"
            })

        # --- CENÁRIO 8: CLASSE B MAIS RENTÁVEL QUE A -------------------
        if _margem_b > _margem_a + 5 and _margem_a > 0:
            recomendacoes.append({
                "tipo": "margem_oportunidade",
                "prioridade": 3,
                "mensagem": (
                    f"💡 OPORTUNIDADE DE MARGEM: Produtos Classe B rendem {_margem_b:.1f}% "
                    f"de margem vs {_margem_a:.1f}% da Classe A. "
                    f"Aumentar o mix de B pode melhorar a rentabilidade "
                    f"sem depender de maior volume de vendas."
                ),
                "impacto_estimado": round(revenue * (_margem_b - _margem_a) / 100 * 0.1, 2),
                "cta": "Ver Análise ABC",
                "alvo": "analise-detalhada",
                "icone": "💡"
            })

        # --- CENÁRIO 9: PRODUTOS PRÓXIMOS AO VENCIMENTO -----------------
        if expiring_products:
            total_expiring = len(expiring_products)
            loss_estimate = sum(p.get("valor_risco_custo", 0) for p in expiring_products)
            recomendacoes.append({
                "tipo": "vencimento_critico",
                "prioridade": 1,
                "mensagem": (
                    f"⚠️ ALERTA DE VALIDADE: {total_expiring} produto(s) vencerão nos próximos 30 dias. "
                    f"Risco de perda financeira (estoque encalhado): R$ {loss_estimate:,.2f}. "
                    f"Recomendação: Crie promoções atrativas imediatamente para liquidar esses lotes."
                ),
                "impacto_estimado": round(loss_estimate, 2),
                "cta": "Promover Produtos",
                "alvo": "produtos",
                "icone": "⏳"
            })

        # Ordenar: críticos primeiro
        recomendacoes.sort(key=lambda x: x.get("prioridade", 99))


        # 🔥 NOTA: total_despesas_periodo já foi calculado via DataLayer.get_total_expenses_value acima.
        # NÃO recalcular aqui para evitar divergência com o DRE (a soma dos detalhes pode diferir).

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
        
        # 10. Construir Previsões Financeiras para o painel avançado
        forecast_list = forecast.get("forecast", []) if isinstance(forecast, dict) else forecast
        forecast_faturamento = sum([f.get("valor_previsto", 0) for f in forecast_list[:30]]) if forecast_list else revenue * 1.05
        previsao_despesas = total_despesas_periodo * 1.02
        
        previsoes_financeiras = [
            {
                "variavel": "Faturamento Estimado",
                "valor_atual": revenue,
                "previsao_30d": forecast_faturamento,
                "confianca": 85.0,
                "intervalo_confianca": [forecast_faturamento * 0.9, forecast_faturamento * 1.1]
            },
            {
                "variavel": "Despesas Projetadas",
                "valor_atual": total_despesas_periodo,
                "previsao_30d": previsao_despesas,
                "confianca": 80.0,
                "intervalo_confianca": [previsao_despesas * 0.95, previsao_despesas * 1.05]
            },
            {
                "variavel": "Lucro Operacional",
                "valor_atual": net_profit,
                "previsao_30d": forecast_faturamento - previsao_despesas,
                "confianca": 75.0,
                "intervalo_confianca": [(forecast_faturamento - previsao_despesas) * 0.8, (forecast_faturamento - previsao_despesas) * 1.2]
            }
        ]
        
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
                "fiado_aberto": fiado_metrics.get("total_aberto", 0.0), # SSD: Real exposure
                "fiado_vencido": receivables_metrics.get("total_vencido", 0.0), # SSD: Real overdue
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
            "previsoes": previsoes_financeiras,
            "analise_produtos": {
                "produtos_estrela": produtos_estrela,
                "produtos_lentos": produtos_lentos,
                "previsao_demanda": previsao_demanda,
            },
            "rh": rh_metrics,
            "inventory": inventory_summary,
            "trend": sales_trend,
            # 🔥 FIADO: Dados completos de carteira de crédito
            "fiado": {
                "total_aberto": fiado_metrics.get("total_aberto", 0.0),
                "total_limite": fiado_metrics.get("total_limite", 0.0),
                "clientes_com_fiado": fiado_metrics.get("clientes_com_fiado", 0),
                "percentual_limite_utilizado": fiado_metrics.get("percentual_limite_utilizado", 0.0),
                "percentual_do_faturamento": round(_fiado_perc_fat, 1),
                "ticket_medio_fiado": fiado_metrics.get("ticket_medio_fiado", 0.0),
                "percentual_clientes_com_fiado": fiado_metrics.get("percentual_clientes_com_fiado", 0.0),
                "maior_devedor_id": fiado_metrics.get("maior_devedor_id"),
                "maior_devedor_nome": fiado_metrics.get("maior_devedor_nome", ""),
                "maior_devedor_celular": fiado_metrics.get("maior_devedor_celular", ""),
                "maior_devedor_valor": fiado_metrics.get("maior_devedor_valor", 0.0),
                "top_devedores": fiado_metrics.get("top_devedores", []),
                "tendencias": fiado_metrics.get("tendencias", {"novos_fiados_30d": 0.0, "pagamentos_fiado_30d": 0.0, "taxa_recuperacao_percentual": 0.0, "status": "alerta"}),
                "top_produtos": fiado_metrics.get("top_produtos", []),
                "bons_pagadores": fiado_metrics.get("bons_pagadores", []),
            },
            "receivables": receivables_metrics, # NEW: Dados detalhados para a nova aba financeira
            "_performance": {
                "total_time": time.time() - start_exec
            }
        }
        return res

    # 🔥 CACHE DESATIVADO PARA DEBUG (era 900s)
    @cache_response(ttl_seconds=1, require_db_check=False)
    def get_abc_analysis(self, days: int = 30, limit: int = 500) -> Dict[str, Any]:
        from app.models import db
        import logging
        _logger = logging.getLogger(__name__)
        try:
            # 🔥 CORREÇÃO: Usar get_all_products_performance para incluir TUDO (mesmo sem vendas)
            all_products_perf = DataLayer.get_all_products_performance(self.establishment_id, days)
            _logger.info(f"ABC Analysis: Processing {len(all_products_perf)} active products (Target: ~203)")
            
            return PracticalModels.analyze_inventory_abc(
                all_products_perf,
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
