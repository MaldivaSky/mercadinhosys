"""
Models Layer - Algoritmos científicos práticos
Foco: Utilidade imediata sem complexidade excessiva
"""

from typing import List, Dict, Any, Optional
import statistics
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


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
    def generate_forecast(
        sales_timeseries: List[Dict[str, Any]], days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Gera previsão simples de vendas (Média Móvel ou Regressão Linear Simples)
        """
        try:
            if not sales_timeseries or len(sales_timeseries) < 7:
                return {
                    "forecast": [],
                    "confidence": "low",
                    "method": "insufficient_data",
                }

            # Extrair valores
            values = []
            dates = []
            for day in sales_timeseries:
                if day.get("total") is not None:
                    values.append(float(day["total"]))
                    dates.append(day.get("data"))

            if not values:
                return {"forecast": [], "confidence": "low", "method": "no_data"}

            # Método simples: Média dos últimos dias com peso
            # Peso maior para dias mais recentes
            recent_values = values[-14:]  # Últimas 2 semanas
            
            # Previsão linear simples (tendência)
            n = len(recent_values)
            if n < 2:
                avg = sum(recent_values) / n if n > 0 else 0
                return {
                    "forecast": [{"day": i + 1, "value": avg} for i in range(days_ahead)],
                    "confidence": "low",
                    "method": "simple_average"
                }
            
            x = list(range(n))
            y = recent_values
            
            # Regressão linear simples: y = mx + c
            # Evitar numpy para manter dependências leves se possível, mas statistics é stdlib
            x_mean = statistics.mean(x)
            y_mean = statistics.mean(y)
            
            numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
            denominator = sum((xi - x_mean) ** 2 for xi in x)
            
            slope = numerator / denominator if denominator != 0 else 0
            intercept = y_mean - slope * x_mean
            
            # Gerar previsões
            forecast = []
            last_date_str = dates[-1]
            try:
                from datetime import datetime, timedelta
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
            except:
                from datetime import datetime
                last_date = datetime.now()

            for i in range(days_ahead):
                # Prever dia n + 1 + i
                # x futuro começa em n
                future_x = n + i
                predicted_value = slope * future_x + intercept
                
                # Não prever vendas negativas
                predicted_value = max(0, predicted_value)
                
                future_date = last_date + timedelta(days=i + 1)
                
                forecast.append({
                    "data": future_date.strftime("%Y-%m-%d"),
                    "valor_previsto": round(predicted_value, 2),
                    "lower_bound": round(max(0, predicted_value * 0.8), 2),
                    "upper_bound": round(predicted_value * 1.2, 2)
                })

            return {
                "forecast": forecast,
                "confidence": "medium",
                "method": "linear_regression_simple",
                "trend": "up" if slope > 0 else "down" if slope < 0 else "flat"
            }

        except Exception as e:
            logger.error(f"Erro ao gerar previsão: {e}")
            return {"forecast": [], "confidence": "low", "error": str(e)}

    @staticmethod
    def calculate_correlations(
        sales_timeseries: List[Dict[str, Any]],
        expense_details: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Calcula correlações REAIS baseadas em dados do banco de dados.
        Sem simulações, sem dados fake.
        """
        from app.models import db, Venda, VendaItem, Produto
        from datetime import datetime, timedelta
        import numpy as np
        from sqlalchemy import func
        
        correlations: List[Dict[str, Any]] = []
        
        try:
            start_date = datetime.utcnow() - timedelta(days=90)
            
            # 1️⃣ CORRELAÇÃO REAL: Vendas vs Despesas (Pearson)
            if sales_timeseries and expense_details:
                try:
                    # Extrair valores de vendas por dia
                    vendas_valores = []

                    datas_vendas = []
                    for day in sales_timeseries:
                        if day.get('total') is not None:
                            vendas_valores.append(float(day['total']))
                            datas_vendas.append(day.get('data'))
                    
                    # Extrair valores de despesas por dia (agregado)
                    despesas_por_data = {}
                    for exp in expense_details:
                        data = exp.get('data', '')
                        valor = float(exp.get('valor', 0))
                        if data not in despesas_por_data:
                            despesas_por_data[data] = 0
                        despesas_por_data[data] += valor
                    
                    # Alinhar datas
                    despesas_valores = []
                    for data in datas_vendas:
                        despesas_valores.append(despesas_por_data.get(data, 0))
                    
                    # Calcular correlação de Pearson
                    if len(vendas_valores) >= 3 and len(set(vendas_valores)) > 1 and len(set(despesas_valores)) > 1:
                        vendas_array = np.array(vendas_valores)
                        despesas_array = np.array(despesas_valores)
                        
                        corr = np.corrcoef(vendas_array, despesas_array)[0, 1]
                        
                        if not np.isnan(corr):
                            correlations.append({
                                "variavel1": "Vendas Diárias",
                                "variavel2": "Despesas Diárias",
                                "correlacao": float(corr),
                                "significancia": 0.05,
                                "tipo": "pearson",
                                "insight": f"Correlação {'positiva' if corr > 0 else 'negativa'}: Quando vendas {'aumentam' if corr > 0 else 'diminuem'}, despesas tendem a {'aumentar' if corr > 0 else 'diminuir'}"
                            })
                except Exception as e:
                    logger.warning(f"Erro ao calcular correlação vendas-despesas: {e}")
            
            # 2️⃣ CORRELAÇÃO REAL: Quantidade de Vendas vs Ticket Médio
            try:
                vendas_por_dia = db.session.query(
                    func.date(Venda.data_venda).label('data'),
                    func.count(Venda.id).label('qtd_vendas'),
                    func.avg(Venda.total).label('ticket_medio')
                ).filter(
                    Venda.data_venda >= start_date,
                    Venda.status == 'finalizada'
                ).group_by(func.date(Venda.data_venda)).all()
                
                if len(vendas_por_dia) >= 3:
                    qtds = np.array([float(v.qtd_vendas or 0) for v in vendas_por_dia])
                    tickets = np.array([float(v.ticket_medio or 0) for v in vendas_por_dia])
                    
                    if len(set(qtds)) > 1 and len(set(tickets)) > 1:
                        corr = np.corrcoef(qtds, tickets)[0, 1]
                        
                        if not np.isnan(corr):
                            correlations.append({
                                "variavel1": "Quantidade de Vendas",
                                "variavel2": "Ticket Médio",
                                "correlacao": float(corr),
                                "significancia": 0.05,
                                "tipo": "pearson",
                                "insight": f"Dias com mais vendas têm tickets {'maiores' if corr > 0 else 'menores'} (correlação {abs(corr):.2f})"
                            })
            except Exception as e:
                db.session.rollback()
                logger.warning(f"Erro ao calcular correlação qtd-ticket: {e}")
            
            # 3️⃣ CORRELAÇÃO REAL: Estoque vs Vendas (Produtos)
            try:
                produtos_stats = db.session.query(
                    Produto.id,
                    Produto.quantidade,
                    func.sum(VendaItem.quantidade).label('vendido')
                ).join(VendaItem, VendaItem.produto_id == Produto.id)\
                .join(Venda, Venda.id == VendaItem.venda_id)\
                .filter(
                    Produto.ativo == True,
                    Venda.data_venda >= start_date,
                    Venda.status == 'finalizada'
                ).group_by(Produto.id).all()
                
                if len(produtos_stats) >= 5:
                    estoques = np.array([float(p.quantidade or 0) for p in produtos_stats])
                    vendidos = np.array([float(p.vendido or 0) for p in produtos_stats])
                    
                    if len(set(estoques)) > 1 and len(set(vendidos)) > 1:
                        corr = np.corrcoef(estoques, vendidos)[0, 1]
                        
                        if not np.isnan(corr):
                            correlations.append({
                                "variavel1": "Estoque Atual",
                                "variavel2": "Quantidade Vendida",
                                "correlacao": float(corr),
                                "significancia": 0.05,
                                "tipo": "pearson",
                                "insight": f"Produtos com mais estoque {'vendem mais' if corr > 0 else 'vendem menos'} (possível efeito de disponibilidade)"
                            })
            except Exception as e:
                db.session.rollback()
                logger.warning(f"Erro ao calcular correlação estoque-vendas: {e}")
            
            # 4️⃣ CORRELAÇÃO REAL: Margem de Lucro vs Quantidade Vendida
            try:
                produtos_margem = db.session.query(
                    Produto.id,
                    Produto.margem_lucro,
                    func.sum(VendaItem.quantidade).label('vendido')
                ).join(VendaItem, VendaItem.produto_id == Produto.id)\
                .join(Venda, Venda.id == VendaItem.venda_id)\
                .filter(
                    Produto.ativo == True,
                    Produto.margem_lucro > 0,
                    Venda.data_venda >= start_date,
                    Venda.status == 'finalizada'
                ).group_by(Produto.id).all()
                
                if len(produtos_margem) >= 5:
                    margens = np.array([float(p.margem_lucro or 0) for p in produtos_margem])
                    vendidos = np.array([float(p.vendido or 0) for p in produtos_margem])
                    
                    if len(set(margens)) > 1 and len(set(vendidos)) > 1:
                        corr = np.corrcoef(margens, vendidos)[0, 1]
                        
                        if not np.isnan(corr):
                            correlations.append({
                                "variavel1": "Margem de Lucro",
                                "variavel2": "Quantidade Vendida",
                                "correlacao": float(corr),
                                "significancia": 0.05,
                                "tipo": "pearson",
                                "insight": f"Produtos com {'maior' if corr > 0 else 'menor'} margem vendem {'mais' if corr > 0 else 'menos'} unidades"
                            })
            except Exception as e:
                db.session.rollback()
                logger.warning(f"Erro ao calcular correlação margem-vendas: {e}")
            
            # Ordenar por valor absoluto de correlação
            correlations.sort(key=lambda x: abs(x["correlacao"]), reverse=True)
            
            return correlations[:5]  # Top 5 correlações
            
        except Exception as e:
            logger.error(f"Erro ao calcular correlações: {e}")
            return []

    @staticmethod
    def detect_anomalies(
        sales_timeseries: List[Dict[str, Any]],
        expense_details: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        from app.utils.utils import detectar_anomalias

        if not sales_timeseries:
            return []

        sales_series = []
        dates = []
        for day in sales_timeseries:
            try:
                total = day.get("total")
                if total is None:
                    continue
                sales_series.append(float(total))
                dates.append(day.get("data"))
            except (TypeError, ValueError):
                continue

        if len(sales_series) < 3:
            return []

        # Try/Except para proteção contra erros na função utilitária
        try:
            anomaly_indices = detectar_anomalias(sales_series)
        except Exception as e:
            logger.error(f"Erro ao detectar anomalias: {e}")
            return []

        anomalies: List[Dict[str, Any]] = []
        for idx in anomaly_indices:
            if idx < 0 or idx >= len(sales_series):
                continue

            date_str = dates[idx] if idx < len(dates) else None
            value = sales_series[idx]
            mean_value = sum(sales_series) / len(sales_series) if sales_series else 0.0

            direction = "alta" if value > mean_value else "baixa"
            impact = abs(value - mean_value)

            anomalies.append(
                {
                    "tipo": f"venda_{direction}",
                    "descricao": f"Vendas {direction} atípicas em {date_str or 'dia desconhecido'}",
                    "impacto": float(impact),
                    "causa_provavel": "variação pontual de demanda",
                }
            )

        return anomalies

    @staticmethod
    def calculate_health_score(financas: Any) -> float:
        """Score de saúde do negócio (simples)"""
        try:
            score = 70.0  # Base
            
            # Margem positiva aumenta score
            if financas and hasattr(financas, 'get'):
                gross_profit = float(financas.get('gross_profit', 0) or 0)
                revenue = float(financas.get('revenue', 0) or 0)
                if revenue > 0:
                    margin = gross_profit / revenue
                    if margin > 0.3: score += 10
                    elif margin > 0.1: score += 5
                    elif margin < 0: score -= 20
            
            return min(100.0, max(0.0, score))
        except Exception as e:
            logger.error(f"Erro ao calcular score: {e}")
            return 50.0
