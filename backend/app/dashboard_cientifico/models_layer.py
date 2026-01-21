"""
Models Layer - Algoritmos científicos práticos
Foco: Utilidade imediata sem complexidade excessiva
"""

from typing import List, Dict, Any, Optional
import statistics
from collections import defaultdict


class PracticalModels:
    """Modelos científicos práticos para negócio"""

    @staticmethod
    def detect_sales_trend(daily_sales: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detecta tendência de vendas de forma prática
        """
        if len(daily_sales) < 7:
            return {
                "trend": "indeterminate",
                "reason": f"Dados insuficientes ({len(daily_sales)} dias)",
            }

        # Extrair valores ordenados por data
        values = [day["total"] for day in daily_sales if "total" in day]

        if len(values) < 7:
            return {"trend": "indeterminate", "reason": "Valores insuficientes"}

        # Método simples: comparar primeira vs segunda metade
        split = len(values) // 2
        first_half = values[:split]
        second_half = values[split:]

        avg_first = statistics.mean(first_half) if first_half else 0
        avg_second = statistics.mean(second_half) if second_half else 0

        # Determinar tendência
        if avg_second > avg_first * 1.2:  # 20% de crescimento
            trend = "up"
            strength = "strong" if avg_second > avg_first * 1.5 else "moderate"
        elif avg_second < avg_first * 0.8:  # 20% de queda
            trend = "down"
            strength = "strong" if avg_second < avg_first * 0.5 else "moderate"
        else:
            trend = "stable"
            strength = "neutral"

        # Melhor e pior dia da semana (simples)
        weekday_sales = defaultdict(list)
        for day in daily_sales:
            if "data" in day:
                try:
                    # Extrair dia da semana (0=segunda, 6=domingo)
                    from datetime import datetime

                    date_obj = datetime.strptime(day["data"], "%Y-%m-%d")
                    weekday = date_obj.weekday()
                    weekday_sales[weekday].append(day["total"])
                except:
                    continue

        best_day = None
        worst_day = None
        if weekday_sales:
            avg_by_weekday = {
                day: statistics.mean(sales) for day, sales in weekday_sales.items()
            }
            best_day = max(avg_by_weekday.items(), key=lambda x: x[1])
            worst_day = min(avg_by_weekday.items(), key=lambda x: x[1])

        return {
            "trend": trend,
            "strength": strength,
            "avg_first_half": float(avg_first),
            "avg_second_half": float(avg_second),
            "growth_percent": (
                ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0
            ),
            "best_day": (
                {
                    "day": (
                        [
                            "Segunda",
                            "Terça",
                            "Quarta",
                            "Quinta",
                            "Sexta",
                            "Sábado",
                            "Domingo",
                        ][best_day[0]]
                        if best_day
                        else None
                    ),
                    "avg_sales": float(best_day[1]) if best_day else 0,
                }
                if best_day
                else None
            ),
            "worst_day": (
                {
                    "day": (
                        [
                            "Segunda",
                            "Terça",
                            "Quarta",
                            "Quinta",
                            "Sexta",
                            "Sábado",
                            "Domingo",
                        ][worst_day[0]]
                        if worst_day
                        else None
                    ),
                    "avg_sales": float(worst_day[1]) if worst_day else 0,
                }
                if worst_day
                else None
            ),
            "confidence": (
                "high"
                if len(values) >= 30
                else "medium" if len(values) >= 15 else "low"
            ),
        }

    @staticmethod
    def analyze_inventory_abc(
        products: List[Dict[str, Any]], top_n: int = 50
    ) -> Dict[str, Any]:
        """
        Análise ABC simplificada mas eficaz
        """
        if not products:
            return {
                "total_value": 0,
                "category_a": [],
                "category_b": [],
                "category_c": [],
                "insights": ["Nenhum produto para análise"],
            }

        # Calcular valor total do estoque
        total_value = sum(p.get("valor_total", 0) for p in products)

        if total_value == 0:
            return {
                "total_value": 0,
                "category_a": [],
                "category_b": [],
                "category_c": [],
                "insights": ["Estoque sem valor monetário"],
            }

        # Ordenar por valor (decrescente)
        sorted_products = sorted(
            [p for p in products if p.get("valor_total", 0) > 0],
            key=lambda x: x.get("valor_total", 0),
            reverse=True,
        )

        # Classificar ABC (80/15/5)
        category_a = []
        category_b = []
        category_c = []
        cumulative_value = 0

        for product in sorted_products[:top_n]:  # Limitar para performance
            product_value = product.get("valor_total", 0)
            cumulative_value += product_value
            cumulative_percent = (cumulative_value / total_value) * 100

            product_with_abc = {**product, "cumulative_percent": cumulative_percent}

            if cumulative_percent <= 80:
                category_a.append(product_with_abc)
            elif cumulative_percent <= 95:
                category_b.append(product_with_abc)
            else:
                category_c.append(product_with_abc)

        # Gerar insights práticos
        insights = []
        if category_a:
            top_5 = category_a[:5]
            insights.append(
                f"Top 5 produtos (Classe A): {', '.join([p.get('nome', '')[:20] for p in top_5])}"
            )

            # Verificar se poucos produtos concentram muito valor
            if len(category_a) < len(products) * 0.2:  # Menos de 20% dos produtos
                insights.append(
                    f"Apenas {len(category_a)} produtos concentram 80% do valor do estoque"
                )

        if (
            category_c and len(category_c) > len(products) * 0.5
        ):  # Mais de 50% dos produtos
            insights.append(
                f"{len(category_c)} produtos (Classe C) representam apenas 5% do valor - oportunidade para reduzir variedade"
            )

        # Combinar todos os produtos classificados
        all_products = []
        for product in category_a + category_b + category_c:
            all_products.append({
                "id": product.get("id", 0),  # Adicionar ID se disponível
                "nome": product.get("nome", ""),
                "faturamento": product.get("valor_total", 0),
                "percentual_acumulado": product.get("cumulative_percent", 0),
                "classificacao": "A" if product in category_a else ("B" if product in category_b else "C"),
                "quantidade_vendida": product.get("quantidade", 0),
                "margem": 0  # Placeholder, pode ser calculado depois
            })

        # Calcular resumo por classe
        resumo = {
            "A": {
                "quantidade": len(category_a),
                "faturamento_total": sum(p.get("valor_total", 0) for p in category_a),
                "percentual": (sum(p.get("valor_total", 0) for p in category_a) / total_value * 100) if total_value > 0 else 0
            },
            "B": {
                "quantidade": len(category_b),
                "faturamento_total": sum(p.get("valor_total", 0) for p in category_b),
                "percentual": (sum(p.get("valor_total", 0) for p in category_b) / total_value * 100) if total_value > 0 else 0
            },
            "C": {
                "quantidade": len(category_c),
                "faturamento_total": sum(p.get("valor_total", 0) for p in category_c),
                "percentual": (sum(p.get("valor_total", 0) for p in category_c) / total_value * 100) if total_value > 0 else 0
            }
        }

        return {
            "classificacao": "ABC Analysis",
            "produtos": all_products,
            "resumo": resumo,
            "pareto_80_20": resumo["A"]["percentual"] >= 75,  # Verificar se segue lei de Pareto
            "total_value": float(total_value),
            "total_products": len(products),
            "insights": insights,
        }

    @staticmethod
    def calculate_health_score(
        sales_data: Dict[str, Any],
        inventory_data: Dict[str, Any],
        customer_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calcula score de saúde do negócio (0-100)
        Simples mas efetivo
        """
        score = 50  # Score base

        factors = []

        # Fator 1: Vendas (0-30 pontos)
        if sales_data.get("total_vendas", 0) > 0:
            # Vendas consistentes (dias com venda / total dias)
            consistency = sales_data.get("dias_com_venda", 0) / sales_data.get(
                "periodo_dias", 1
            )
            if consistency >= 0.9:
                score += 25
                factors.append("Vendas consistentes (+25)")
            elif consistency >= 0.7:
                score += 15
                factors.append("Vendas razoavelmente consistentes (+15)")
            elif consistency >= 0.5:
                score += 5
                factors.append("Vendas moderadas (+5)")

        # Fator 2: Estoque (0-20 pontos)
        baixo_estoque = inventory_data.get("baixo_estoque", 0)
        total_produtos = inventory_data.get("total_produtos", 1)
        percent_baixo = baixo_estoque / total_produtos if total_produtos > 0 else 0

        if percent_baixo < 0.1:  # Menos de 10% com estoque baixo
            score += 20
            factors.append("Estoque bem gerenciado (+20)")
        elif percent_baixo < 0.3:  # Menos de 30%
            score += 10
            factors.append("Estoque razoável (+10)")
        elif percent_baixo < 0.5:  # Menos de 50%
            score += 5
            factors.append("Estoque precisa atenção (+5)")
        else:
            factors.append("Estoque crítico (0)")

        # Fator 3: Rentabilidade (0-20 pontos)
        lucro_potencial = inventory_data.get("lucro_potencial", 0)
        valor_total = inventory_data.get("valor_total", 1)
        margem = lucro_potencial / valor_total if valor_total > 0 else 0

        if margem > 0.3:  # Mais de 30% de margem
            score += 20
            factors.append("Boa margem de lucro (+20)")
        elif margem > 0.2:  # Mais de 20%
            score += 15
            factors.append("Margem razoável (+15)")
        elif margem > 0.1:  # Mais de 10%
            score += 10
            factors.append("Margem moderada (+10)")
        elif margem > 0:
            score += 5
            factors.append("Margem baixa (+5)")
        else:
            factors.append("Sem margem (0)")

        # Fator 4: Clientes (0-10 pontos)
        clientes_unicos = customer_data.get("clientes_unicos", 0)
        if clientes_unicos > 50:
            score += 10
            factors.append("Base de clientes sólida (+10)")
        elif clientes_unicos > 20:
            score += 7
            factors.append("Base de clientes razoável (+7)")
        elif clientes_unicos > 10:
            score += 5
            factors.append("Base de clientes pequena (+5)")
        else:
            factors.append("Base de clientes muito pequena (0)")

        # Fator 5: Ticket médio (0-10 pontos)
        ticket_medio = sales_data.get("ticket_medio", 0)
        if ticket_medio > 100:
            score += 10
            factors.append("Ticket médio alto (+10)")
        elif ticket_medio > 50:
            score += 7
            factors.append("Ticket médio razoável (+7)")
        elif ticket_medio > 20:
            score += 5
            factors.append("Ticket médio baixo (+5)")
        else:
            factors.append("Ticket médio muito baixo (0)")

        # Garantir score entre 0-100
        score = max(0, min(100, score))

        # Classificar saúde
        if score >= 80:
            health = "EXCELENTE"
            color = "green"
        elif score >= 60:
            health = "BOA"
            color = "blue"
        elif score >= 40:
            health = "REGULAR"
            color = "yellow"
        elif score >= 20:
            health = "FRACA"
            color = "orange"
        else:
            health = "CRÍTICA"
            color = "red"

        # Principais recomendações
        recommendations = []
        if score < 60:
            recommendations.append("Focar em aumentar consistência das vendas")
        if percent_baixo > 0.3:
            recommendations.append("Repor produtos com estoque baixo")
        if clientes_unicos < 20:
            recommendations.append("Investir em captação de novos clientes")
        if ticket_medio < 30:
            recommendations.append("Treinar equipe em vendas adicionais")

        return {
            "score": int(score),
            "health": health,
            "color": color,
            "factors": factors,
            "recommendations": recommendations[:3],  # Top 3 recomendações
            "summary": f"Saúde {health.lower()} ({score}/100)",
        }
