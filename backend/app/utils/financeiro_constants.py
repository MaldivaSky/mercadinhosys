"""Fonte única das categorias de Despesa que são ESPELHOS de outros módulos:
- "Fornecedores"/"Boleto de Mercadoria": criadas automaticamente ao pagar um
  boleto (ContaPagar é a fonte da verdade desses valores);
- "Folha de Pagamento"/"Benefícios": lançamentos manuais/seed de pessoal (a
  fonte da verdade é o cálculo real de folha do RH, que já inclui benefícios).

Essas despesas continuam VISÍVEIS na listagem (rastreabilidade), mas ficam
FORA de qualquer agregado/indicador (cards, DRE, dashboard científico) — do
contrário o mesmo dinheiro conta duas vezes.
"""
from sqlalchemy import func, or_

CATEGORIAS_INTEGRADAS = (
    "fornecedores",
    "folha de pagamento",
    "boleto de mercadoria",
    "benefícios",
    "beneficios",
)

# Subconjunto usado na visão de CAIXA: pagamento manual de salário É desembolso
# real (fica de fora só o boleto de mercadoria, coberto por ContaPagar.pago).
CATEGORIAS_ESPELHO_BOLETO = ("fornecedores", "boleto de mercadoria")


def sem_categorias_integradas(query, categoria_col):
    """Aplica o filtro de exclusão das categorias espelhadas a um query que
    referencia `categoria_col` (normalmente Despesa.categoria)."""
    return query.filter(
        or_(categoria_col.is_(None),
            func.lower(func.trim(categoria_col)).notin_(CATEGORIAS_INTEGRADAS))
    )
