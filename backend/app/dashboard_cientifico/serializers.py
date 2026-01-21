"""
Serializers Layer - Transforma dados técnicos em formato amigável
Foco: Frontend não precisa entender estatística
"""

from typing import Dict, Any, List
from .stats_layer import ConfidenceLevel


class DashboardSerializer:
    """Serializa dados para o frontend de forma amigável"""

    @staticmethod
    def serialize_metric(metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma métrica estatística em algo simples para frontend
        """
        if (
            not metric_data
            or metric_data.get("confidence") == ConfidenceLevel.INSUFICIENT.name
        ):
            return {
                "value": None,
                "display": "--",
                "status": "no_data",
                "tooltip": "Dados insuficientes para cálculo",
            }

        value = metric_data.get("value")
        confidence = metric_data.get("confidence")

        # Mapear confiança técnica para status amigável
        if confidence == ConfidenceLevel.LOW.name:
            status = "low_confidence"
            display = f"~{value:,.0f}" if value else "--"
            tooltip = "Baixa confiança - baseado em poucos dados"
        elif confidence == ConfidenceLevel.MEDIUM.name:
            status = "medium_confidence"
            display = f"{value:,.0f}" if value else "--"
            tooltip = "Confiança moderada"
        else:  # HIGH
            status = "high_confidence"
            display = f"{value:,.0f}" if value else "--"
            tooltip = "Alta confiança"

        return {
            "value": value,
            "display": display,
            "status": status,
            "tooltip": tooltip,
            "sample_size": metric_data.get("sample_size", 0),
            "has_warning": len(metric_data.get("warnings", [])) > 0,
        }

    @staticmethod
    def serialize_growth(growth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serializa dados de crescimento"""
        if not growth_data or growth_data.get("growth") is None:
            return {
                "value": None,
                "display": "--",
                "status": "no_data",
                "is_positive": False,
                "icon": "minus",
            }

        growth = growth_data["growth"]
        confidence = growth_data.get("confidence", "LOW")

        # Determinar status baseado na confiança e valor
        if confidence == ConfidenceLevel.INSUFICIENT.name:
            status = "no_data"
            display = "--"
            icon = "minus"
        elif confidence == ConfidenceLevel.LOW.name:
            status = "low_confidence"
            display = f"{growth:+.1f}%"
            icon = "trending_up" if growth > 0 else "trending_down"
        else:
            status = "high_confidence"
            display = f"{growth:+.1f}%"
            icon = "trending_up" if growth > 0 else "trending_down"

        # Adicionar emoji para impacto visual
        if growth > 20:
            emoji = "🚀"
        elif growth > 10:
            emoji = "📈"
        elif growth > 0:
            emoji = "↗️"
        elif growth < -10:
            emoji = "⚠️"
        elif growth < 0:
            emoji = "↘️"
        else:
            emoji = "➡️"

        return {
            "value": growth,
            "display": f"{emoji} {display}",
            "status": status,
            "is_positive": growth > 0,
            "icon": icon,
            "is_significant": growth_data.get("is_significant", False),
            "tooltip": growth_data.get("warning", "Crescimento calculado"),
        }

    @staticmethod
    def serialize_trend(trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serializa análise de tendência"""
        if not trend_data or trend_data.get("trend") == "indeterminate":
            return {
                "direction": "unknown",
                "display": "Tendência indefinida",
                "color": "gray",
                "icon": "help",
                "summary": "Dados insuficientes para determinar tendência",
            }

        trend = trend_data["trend"]
        strength = trend_data.get("strength", "neutral")

        # Mapear para frontend
        if trend == "up":
            if strength == "strong":
                color = "green"
                icon = "trending_up"
                display = "Forte alta"
                summary = "Vendas em crescimento consistente"
            else:
                color = "light-green"
                icon = "trending_up"
                display = "Alta moderada"
                summary = "Vendas em leve crescimento"
        elif trend == "down":
            if strength == "strong":
                color = "red"
                icon = "trending_down"
                display = "Forte queda"
                summary = "Vendas em declínio consistente"
            else:
                color = "orange"
                icon = "trending_down"
                display = "Queda moderada"
                summary = "Vendas em leve declínio"
        else:  # stable
            color = "blue"
            icon = "trending_flat"
            display = "Estável"
            summary = "Vendas se mantêm constantes"

        return {
            "direction": trend,
            "display": display,
            "color": color,
            "icon": icon,
            "summary": summary,
            "growth_percent": trend_data.get("growth_percent", 0),
            "confidence": trend_data.get("confidence", "low"),
            "best_day": trend_data.get("best_day"),
            "worst_day": trend_data.get("worst_day"),
        }

    @staticmethod
    def serialize_health_score(health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serializa score de saúde do negócio"""
        score = health_data.get("score", 0)
        health = health_data.get("health", "UNKNOWN")
        color = health_data.get("color", "gray")

        # Gerar gráfico simples (array de 10 elementos)
        bar_count = min(10, max(1, score // 10))
        progress_bar = ["●" if i < bar_count else "○" for i in range(10)]

        return {
            "score": score,
            "health": health,
            "color": color,
            "display": f"{score}/100",
            "progress": "".join(progress_bar),
            "summary": health_data.get("summary", ""),
            "recommendations": health_data.get("recommendations", []),
            "factors": health_data.get("factors", []),
        }
