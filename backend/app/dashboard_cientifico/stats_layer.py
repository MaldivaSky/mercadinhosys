"""
Stats Layer - Validação estatística prática e rigorosa
Foco: Precisão sem overengineering
"""

from typing import List, Optional, Tuple, Dict, Any
from enum import Enum, auto
import statistics
import math


class ConfidenceLevel(Enum):
    """Níveis de confiança simplificados para o frontend"""

    INSUFICIENT = auto()  # Dados insuficientes
    LOW = auto()  # Baixa confiança
    MEDIUM = auto()  # Confiança moderada
    HIGH = auto()  # Alta confiança


class StatsValidator:
    """Validador estatístico prático"""

    @staticmethod
    def validate_metric(values: List[float], min_samples: int = 5) -> Dict[str, Any]:
        """
        Valida uma métrica de forma prática
        Retorna dict pronto para frontend
        """
        if not values or len(values) < min_samples:
            return {
                "value": None,
                "confidence": ConfidenceLevel.INSUFICIENT.name,
                "sample_size": len(values) if values else 0,
                "warning": f"Mínimo {min_samples} amostras necessárias",
            }

        # Remover outliers extremos (evitar distorção)
        clean_values = StatsValidator._remove_extreme_outliers(values)

        # Calcular estatísticas básicas
        mean = statistics.mean(clean_values)
        median = statistics.median(clean_values)

        # Determinar confiança
        confidence = StatsValidator._determine_confidence(clean_values)

        # Validar realismo do valor
        validated_value, warnings = StatsValidator._validate_realism(mean, clean_values)

        return {
            "value": float(validated_value),
            "median": float(median),
            "confidence": confidence.name,
            "sample_size": len(clean_values),
            "warnings": warnings,
            "is_reliable": confidence.value >= ConfidenceLevel.MEDIUM.value,
        }

    @staticmethod
    def _remove_extreme_outliers(values: List[float]) -> List[float]:
        """Remove apenas outliers extremos (3x desvio padrão)"""
        if len(values) < 3:
            return values

        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0

        if stdev == 0:
            return values

        # Manter valores dentro de 3 desvios padrão
        lower = mean - 3 * stdev
        upper = mean + 3 * stdev

        return [v for v in values if lower <= v <= upper]

    @staticmethod
    def _determine_confidence(values: List[float]) -> ConfidenceLevel:
        """Determina nível de confiança de forma prática"""
        n = len(values)

        if n < 5:
            return ConfidenceLevel.INSUFICIENT
        elif n < 15:
            return ConfidenceLevel.LOW
        elif n < 30:
            # Verificar variabilidade
            if len(values) > 1:
                cv = statistics.stdev(values) / statistics.mean(values) * 100
                if cv > 100:  # Alta variabilidade
                    return ConfidenceLevel.LOW
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.HIGH

    @staticmethod
    def _validate_realism(
        value: float, all_values: List[float]
    ) -> Tuple[float, List[str]]:
        """Valida se o valor é realista para o contexto"""
        warnings = []

        # Para valores monetários (vendas)
        if value < 0:
            warnings.append("Valor negativo - ajustado para 0")
            return 0.0, warnings

        # Para percentuais (crescimento)
        if abs(value) > 1000:  # Crescimento > 1000%
            warnings.append(f"Valor extremo ({value:.1f}%) - interpretar com cautela")

        return value, warnings

    @staticmethod
    def calculate_growth(
        current_value: float,
        previous_value: float,
        current_samples: int,
        previous_samples: int,
    ) -> Dict[str, Any]:
        """
        Calcula crescimento de forma segura e prática
        """
        # Verificar amostras mínimas
        if current_samples < 5 or previous_samples < 5:
            return {
                "growth": None,
                "confidence": ConfidenceLevel.INSUFICIENT.name,
                "warning": "Amostras insuficientes para cálculo de crescimento",
            }

        # Evitar divisão por zero
        if previous_value == 0:
            if current_value > 0:
                return {
                    "growth": 100.0,  # Convenção: de 0 para positivo = 100%
                    "confidence": ConfidenceLevel.LOW.name,
                    "warning": "Crescimento calculado sobre base zero",
                }
            else:
                return {
                    "growth": 0.0,
                    "confidence": ConfidenceLevel.LOW.name,
                    "warning": "Valores zerados",
                }

        # Calcular crescimento
        growth = ((current_value - previous_value) / abs(previous_value)) * 100

        # Clamp: não permitir valores absurdos
        if growth > 500:  # Máximo 500%
            growth = 500
            warning = "Crescimento limitado a 500% (valor extremo)"
        elif growth < -100:  # Mínimo -100% (perda total)
            growth = -100
            warning = "Queda limitada a -100% (valor extremo)"
        else:
            warning = None

        # Determinar confiança baseada no tamanho das amostras
        min_samples = min(current_samples, previous_samples)
        if min_samples >= 30:
            confidence = ConfidenceLevel.HIGH
        elif min_samples >= 15:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        result = {
            "growth": float(growth),
            "confidence": confidence.name,
            "is_positive": growth > 0,
            "is_significant": abs(growth)
            > 10,  # Crescimento > 10% considerado significativo
        }

        if warning:
            result["warning"] = warning

        return result
