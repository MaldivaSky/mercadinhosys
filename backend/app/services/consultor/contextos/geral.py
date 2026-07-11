from app.services.consultor.contextos.financeiro import montar_contexto as montar_financeiro
from app.services.consultor.contextos.vendas import montar_contexto as montar_vendas
from app.services.consultor.contextos.estoque import montar_contexto as montar_estoque
from app.services.consultor.contextos.rh import montar_contexto as montar_rh
from app.services.consultor.contextos.compras import montar_contexto as montar_compras

def montar_contexto(estabelecimento_id: int, is_manager: bool = True) -> dict:
    """Monta o contexto Geral compilando resumos dos outros módulos.
    Utilizado para o dashboard principal ou consultas amplas.
    """
    financeiro = montar_financeiro(estabelecimento_id, is_manager)
    vendas = montar_vendas(estabelecimento_id, is_manager)
    estoque = montar_estoque(estabelecimento_id, is_manager)
    rh = montar_rh(estabelecimento_id, is_manager)
    compras = montar_compras(estabelecimento_id, is_manager)
    
    # Montamos um resumo enxuto para não estourar tokens
    return {
        "financeiro": {
            "receita_mes_atual": financeiro.get("receita_mes_atual"),
            "despesas_mes_atual": financeiro.get("total_despesas_mes_atual"),
            "resultado_mes_atual": financeiro.get("resultado_mes_atual"),
            "boletos_atrasados": financeiro.get("total_boletos_atrasados"),
        },
        "vendas": {
            "faturamento_hoje": vendas.get("hoje", {}).get("faturamento"),
            "ticket_medio_hoje": vendas.get("hoje", {}).get("ticket_medio"),
            "faturamento_semana": vendas.get("semana", {}).get("faturamento"),
        },
        "estoque": {
            "produtos_ativos": estoque.get("produtos_ativos_qtd"),
            "alertas_estoque_minimo_qtd": len(estoque.get("alertas_estoque_minimo", [])),
            "custo_total_parado": estoque.get("custo_total_parado"),
            "produtos_margem_baixa": estoque.get("detalhes_produtos_margem_baixa", []),
        },
        "rh": {
            "custo_folha_mes_atual": rh.get("custo_folha", {}).get("mes_atual"),
            "percentual_faturamento": rh.get("custo_folha_percentual_faturamento"),
            "funcionarios_desempenho": rh.get("funcionarios_desempenho_mes", []),
            "pontos_batidos_hoje": rh.get("pontos_batidos_hoje", []),
        },
        "compras": {
            "pedidos_em_aberto": compras.get("pedidos_em_aberto_qtd"),
            "top_fornecedores": compras.get("top_fornecedores_mes_atual", []),
            "boletos_por_fornecedor": compras.get("boletos_abertos_por_fornecedor", []),
            "alertas_compras": compras.get("itens_abaixo_minimo_para_comprar", []),
            "prazo_medio_entrega": compras.get("prazo_medio_entrega_dias", 0.0),
        }
    }
