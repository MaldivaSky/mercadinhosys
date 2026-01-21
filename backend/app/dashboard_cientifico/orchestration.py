"""
Orchestration Layer - Orquestra todas as camadas
Foco: Simplicidade e clareza
"""

from typing import Dict, Any
from datetime import datetime
from .data_layer import DataLayer
from .stats_layer import StatsValidator
from .models_layer import PracticalModels
from .serializers import DashboardSerializer
from .cache_layer import cache_response


class DashboardOrchestrator:
    """Orquestra a geração do dashboard"""

    def __init__(self, establishment_id: int):
        self.establishment_id = establishment_id

    @cache_response(ttl_seconds=60)  # Cache de 1 minuto para dashboard
    def get_executive_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """
        Dashboard executivo - Resumo para gestão
        """
        # 1. Coletar dados
        sales_summary = DataLayer.get_sales_summary(self.establishment_id, days)
        sales_timeseries = DataLayer.get_sales_timeseries(self.establishment_id, days)
        inventory_summary = DataLayer.get_inventory_summary(self.establishment_id)
        customer_metrics = DataLayer.get_customer_metrics(self.establishment_id, days)

        # 2. Validar estatisticamente
        # Vendas atuais
        sales_current = StatsValidator.validate_metric(
            [day["total"] for day in sales_timeseries if day["total"] > 0]
        )

        # Vendas anteriores (últimos 30-60 dias)
        if days >= 60:
            sales_previous_data = DataLayer.get_sales_summary(self.establishment_id, 60)
            sales_previous = {
                "value": sales_previous_data["total_faturado"] / 30,
                "sample_size": 30,
            }
        else:
            sales_previous = {
                "value": sales_summary["total_faturado"] / days,
                "sample_size": days,
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
        }

    def get_detailed_analysis(self, metric_type: str, days: int = 90) -> Dict[str, Any]:
        """
        Análise detalhada por tipo de métrica
        """
        if metric_type == "sales":
            data = DataLayer.get_sales_timeseries(self.establishment_id, days)
            analysis = PracticalModels.detect_sales_trend(data)

            return {"data": data, "analysis": analysis, "period": days}

        elif metric_type == "inventory":
            summary = DataLayer.get_inventory_summary(self.establishment_id)
            top_products = DataLayer.get_top_products(self.establishment_id, 90, 100)
            abc_analysis = PracticalModels.analyze_inventory_abc(
                [
                    {
                        "nome": p["nome"],
                        "valor_total": p["faturamento"] * 3,  # Estimativa de estoque
                        "quantidade": p["quantidade_vendida"],
                    }
                    for p in top_products
                ]
            )

            return {
                "summary": summary,
                "abc_analysis": abc_analysis,
                "top_products": top_products[:20],
            }

        else:
            return {"error": f"Tipo de análise não suportado: {metric_type}"}
