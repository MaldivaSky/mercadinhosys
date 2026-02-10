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
    def detect_sales_trend(
        daily_sales: List[Dict[str, Any]],
        smoothing_window: Optional[int] = None,
        trim_ratio: float = 0.1,
        outlier_z: float = 6.0,
    ) -> Dict[str, Any]:
        """
        Detecta tendência de vendas de forma prática
        """
        def _safe_float(value: Any) -> Optional[float]:
            try:
                if value is None:
                    return None
                return float(value)
            except (TypeError, ValueError):
                return None

        def _simple_moving_average(values: List[float], window: int) -> List[float]:
            if window <= 1:
                return list(values)
            if len(values) < window:
                return list(values)

            smoothed: List[float] = []
            for i in range(window - 1, len(values)):
                chunk = values[i - window + 1 : i + 1]
                smoothed.append(statistics.mean(chunk))
            return smoothed

        def _trimmed_mean(values: List[float], ratio: float) -> float:
            if not values:
                return 0.0
            if ratio <= 0:
                return float(statistics.mean(values))

            sorted_vals = sorted(values)
            k = int(len(sorted_vals) * ratio)
            if len(sorted_vals) - 2 * k <= 0:
                k = 0
            trimmed = sorted_vals[k : len(sorted_vals) - k]
            return float(statistics.mean(trimmed)) if trimmed else 0.0

        def _winsorize_by_mad(values: List[float], z: float) -> Dict[str, Any]:
            if not values:
                return {"values": [], "lower": None, "upper": None, "capped": 0}
            if z <= 0:
                return {"values": list(values), "lower": None, "upper": None, "capped": 0}

            med = float(statistics.median(values))
            deviations = [abs(v - med) for v in values]
            mad = float(statistics.median(deviations)) if deviations else 0.0
            if mad == 0:
                return {"values": list(values), "lower": None, "upper": None, "capped": 0}

            scale = 1.4826 * mad
            lower = max(0.0, med - z * scale)
            upper = med + z * scale

            capped = 0
            clipped: List[float] = []
            for v in values:
                cv = v
                if v < lower:
                    cv = lower
                elif v > upper:
                    cv = upper
                if cv != v:
                    capped += 1
                clipped.append(cv)

            return {"values": clipped, "lower": lower, "upper": upper, "capped": capped}

        if len(daily_sales) < 7:
            return {
                "trend": "indeterminate",
                "reason": f"Dados insuficientes ({len(daily_sales)} dias)",
            }

        values_with_dates = []
        can_sort_by_date = True
        try:
            from datetime import datetime
        except Exception:
            datetime = None
            can_sort_by_date = False

        for idx, day in enumerate(daily_sales):
            if "total" not in day:
                continue
            total = _safe_float(day.get("total"))
            if total is None:
                continue

            date_obj = None
            if can_sort_by_date and datetime and isinstance(day.get("data"), str):
                try:
                    date_obj = datetime.strptime(day["data"], "%Y-%m-%d")
                except Exception:
                    can_sort_by_date = False
                    date_obj = None
            values_with_dates.append((idx, date_obj, total))

        if can_sort_by_date:
            values_with_dates.sort(key=lambda x: x[1])
        else:
            values_with_dates.sort(key=lambda x: x[0])

        values = [v for _, __, v in values_with_dates]

        if len(values) < 7:
            return {"trend": "indeterminate", "reason": "Valores insuficientes"}

        raw_split = len(values) // 2
        raw_first_half = values[:raw_split]
        raw_second_half = values[raw_split:]
        avg_first_raw = float(statistics.mean(raw_first_half)) if raw_first_half else 0.0
        avg_second_raw = (
            float(statistics.mean(raw_second_half)) if raw_second_half else 0.0
        )
        median_first_raw = (
            float(statistics.median(raw_first_half)) if raw_first_half else 0.0
        )
        median_second_raw = (
            float(statistics.median(raw_second_half)) if raw_second_half else 0.0
        )

        n = len(values)
        if smoothing_window is None:
            smoothing_window = 7 if n >= 28 else 5 if n >= 14 else 3
        smoothing_window = max(1, int(smoothing_window))

        winsor = _winsorize_by_mad(values, outlier_z)
        values_for_smoothing = winsor["values"]

        smoothed_values = _simple_moving_average(values_for_smoothing, smoothing_window)
        if len(smoothed_values) < 4:
            smoothed_values = list(values_for_smoothing)

        split = len(smoothed_values) // 2
        first_half = smoothed_values[:split]
        second_half = smoothed_values[split:]

        avg_first = median_first_raw
        avg_second = median_second_raw
        smoothed_median_first = (
            float(statistics.median(first_half)) if first_half else 0.0
        )
        smoothed_median_second = (
            float(statistics.median(second_half)) if second_half else 0.0
        )
        avg_first_trimmed = _trimmed_mean(first_half, trim_ratio) if first_half else 0.0
        avg_second_trimmed = (
            _trimmed_mean(second_half, trim_ratio) if second_half else 0.0
        )

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
                    total = _safe_float(day.get("total"))
                    if total is None:
                        continue
                    weekday_sales[weekday].append(total)
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
            "avg_first_half_trimmed": float(avg_first_trimmed),
            "avg_second_half_trimmed": float(avg_second_trimmed),
            "avg_first_half_raw": float(avg_first_raw),
            "avg_second_half_raw": float(avg_second_raw),
            "median_first_half_raw": float(median_first_raw),
            "median_second_half_raw": float(median_second_raw),
            "smoothed_median_first_half": float(smoothed_median_first),
            "smoothed_median_second_half": float(smoothed_median_second),
            "smoothing_window": int(smoothing_window),
            "trim_ratio": float(trim_ratio),
            "outlier_cap_lower": winsor["lower"],
            "outlier_cap_upper": winsor["upper"],
            "outliers_capped": int(winsor["capped"]),
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
        products: List[Dict[str, Any]],
        top_n: Optional[int] = 50,
        return_all_products: bool = False,
    ) -> Dict[str, Any]:
        """
        Análise ABC simplificada mas eficaz
        """
        def _safe_float(value: Any) -> float:
            try:
                if value is None:
                    return 0.0
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        def _empty_result(message: str, total_products: int) -> Dict[str, Any]:
            resumo = {
                "A": {"quantidade": 0, "faturamento_total": 0.0, "percentual": 0.0, "margem_media": 0.0},
                "B": {"quantidade": 0, "faturamento_total": 0.0, "percentual": 0.0, "margem_media": 0.0},
                "C": {"quantidade": 0, "faturamento_total": 0.0, "percentual": 0.0, "margem_media": 0.0},
                "TODOS": {"quantidade": 0, "faturamento_total": 0.0, "percentual": 100.0, "margem_media": 0.0},
            }
            return {
                "classificacao": "ABC Analysis",
                "produtos": [],
                "resumo": resumo,
                "pareto_80_20": False,
                "total_value": 0.0,
                "total_products": total_products,
                "total_products_considered": 0,
                "returned_products": 0,
                "is_truncated": False,
                "insights": [message],
            }

        if not products:
            return _empty_result("Nenhum produto para análise", 0)

        # Calcular valor total do estoque
        total_value = sum(max(0.0, _safe_float(p.get("valor_total", 0))) for p in products)

        if total_value == 0:
            return _empty_result("Estoque sem valor monetário", len(products))

        # Ordenar por valor (decrescente)
        sorted_products = sorted(
            [p for p in products if _safe_float(p.get("valor_total", 0)) > 0],
            key=lambda x: _safe_float(x.get("valor_total", 0)),
            reverse=True,
        )

        total_value_considered = sum(_safe_float(p.get("valor_total", 0)) for p in sorted_products)
        if total_value_considered <= 0:
            return _empty_result("Estoque sem valor monetário", len(products))

        # Classificar ABC (80/15/5)
        cumulative_value = 0
        lucro_por_classe = {"A": 0.0, "B": 0.0, "C": 0.0}
        faturamento_por_classe = {"A": 0.0, "B": 0.0, "C": 0.0}
        quantidade_por_classe = {"A": 0, "B": 0, "C": 0}
        all_products = []

        for product in sorted_products:
            faturamento = _safe_float(product.get("valor_total", 0))
            cumulative_value += faturamento
            cumulative_percent = (cumulative_value / total_value_considered) * 100

            if cumulative_percent <= 80:
                classe = "A"
            elif cumulative_percent <= 95:
                classe = "B"
            else:
                classe = "C"

            quantidade = _safe_float(product.get("quantidade_vendida", product.get("quantidade", 0)))
            preco_custo = _safe_float(product.get("preco_custo", 0))
            custo_total = quantidade * preco_custo
            lucro = faturamento - custo_total
            margem = (lucro / faturamento * 100) if faturamento > 0 else 0

            faturamento_por_classe[classe] += faturamento
            lucro_por_classe[classe] += lucro
            quantidade_por_classe[classe] += 1

            all_products.append(
                {
                    "id": product.get("id", 0),
                    "nome": product.get("nome", ""),
                    "faturamento": faturamento,
                    "percentual_acumulado": cumulative_percent,
                    "classificacao": classe,
                    "quantidade_vendida": quantidade,
                    "margem": margem,
                }
            )

        # Gerar insights práticos
        insights = []
        if all_products:
            top_5 = all_products[:5]
            insights.append(
                f"Top 5 produtos (Classe A): {', '.join([p.get('nome', '')[:20] for p in top_5])}"
            )

            # Verificar se poucos produtos concentram muito valor
            if quantidade_por_classe["A"] < len(sorted_products) * 0.2:  # Menos de 20% dos produtos
                insights.append(
                    f"Apenas {quantidade_por_classe['A']} produtos concentram 80% do valor do estoque"
                )

        if len(sorted_products) > 0 and quantidade_por_classe["C"] > len(sorted_products) * 0.5:
            insights.append(
                f"{quantidade_por_classe['C']} produtos (Classe C) representam apenas 5% do valor - oportunidade para reduzir variedade"
            )

        if return_all_products or top_n is None or int(top_n) <= 0:
            produtos_saida = all_products
            is_truncated = False
        else:
            produtos_saida = all_products[: int(top_n)]
            is_truncated = len(produtos_saida) < len(all_products)

        # Calcular resumo por classe com margem média
        resumo = {
            "A": {
                "quantidade": quantidade_por_classe["A"],
                "faturamento_total": faturamento_por_classe["A"],
                "percentual": (faturamento_por_classe["A"] / total_value_considered * 100) if total_value_considered > 0 else 0,
                "margem_media": (lucro_por_classe["A"] / faturamento_por_classe["A"] * 100) if faturamento_por_classe["A"] > 0 else 0
            },
            "B": {
                "quantidade": quantidade_por_classe["B"],
                "faturamento_total": faturamento_por_classe["B"],
                "percentual": (faturamento_por_classe["B"] / total_value_considered * 100) if total_value_considered > 0 else 0,
                "margem_media": (lucro_por_classe["B"] / faturamento_por_classe["B"] * 100) if faturamento_por_classe["B"] > 0 else 0
            },
            "C": {
                "quantidade": quantidade_por_classe["C"],
                "faturamento_total": faturamento_por_classe["C"],
                "percentual": (faturamento_por_classe["C"] / total_value_considered * 100) if total_value_considered > 0 else 0,
                "margem_media": (lucro_por_classe["C"] / faturamento_por_classe["C"] * 100) if faturamento_por_classe["C"] > 0 else 0
            },
            "TODOS": {
                "quantidade": len(sorted_products),
                "faturamento_total": total_value_considered,
                "percentual": 100.0,
                "margem_media": ((lucro_por_classe["A"] + lucro_por_classe["B"] + lucro_por_classe["C"]) / total_value_considered * 100) if total_value_considered > 0 else 0
            }
        }

        return {
            "classificacao": "ABC Analysis",
            "produtos": produtos_saida,
            "resumo": resumo,
            "pareto_80_20": resumo["A"]["percentual"] >= 75,  # Verificar se segue lei de Pareto
            "total_value": float(total_value_considered),
            "total_products": len(products),
            "total_products_considered": len(sorted_products),
            "returned_products": len(produtos_saida),
            "is_truncated": is_truncated,
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
