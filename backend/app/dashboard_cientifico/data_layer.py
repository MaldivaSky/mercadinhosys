"""
Data Layer - Queries otimizadas com índices e performance
Responsabilidade ÚNICA: Buscar dados do banco de forma eficiente
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from app import db
from app.models import Venda, Produto, Cliente, ItemVenda, Funcionario
from sqlalchemy import func, text, and_
import logging

logger = logging.getLogger(__name__)


class DataLayer:
    """Camada de dados otimizada para performance"""

    # Índices sugeridos (adicionar manualmente ao banco):
    # CREATE INDEX idx_vendas_estabelecimento_data ON venda(estabelecimento_id, data_venda, status);
    # CREATE INDEX idx_produtos_estabelecimento_ativo ON produto(estabelecimento_id, ativo);
    # CREATE INDEX idx_itemvenda_venda_produto ON item_venda(venda_id, produto_id);

    @staticmethod
    def get_sales_summary(estabelecimento_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Resumo de vendas otimizado - 1 query para tudo
        """
        # Data inicial com índice
        data_inicio = datetime.now() - timedelta(days=days)

        # Query única otimizada
        query = text(
            """
            SELECT 
                COUNT(*) as total_vendas,
                COALESCE(SUM(total), 0) as total_faturado,
                COALESCE(AVG(total), 0) as ticket_medio,
                COUNT(DISTINCT DATE(data_venda)) as dias_com_venda,
                MAX(total) as maior_venda,
                MIN(total) as menor_venda
            FROM vendas 
            WHERE estabelecimento_id = :est_id 
                AND data_venda >= :data_inicio 
                AND status = 'finalizada'
        """
        )

        result = db.session.execute(
            query, {"est_id": estabelecimento_id, "data_inicio": data_inicio}
        ).first()

        return {
            "total_vendas": result.total_vendas or 0,
            "total_faturado": float(result.total_faturado or 0),
            "ticket_medio": float(result.ticket_medio or 0),
            "dias_com_venda": result.dias_com_venda or 0,
            "periodo_dias": days,
            "maior_venda": float(result.maior_venda or 0),
            "menor_venda": float(result.menor_venda or 0),
        }

    @staticmethod
    def get_sales_summary_range(
        estabelecimento_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        query = text(
            """
            SELECT 
                COUNT(*) as total_vendas,
                COALESCE(SUM(total), 0) as total_faturado,
                COALESCE(AVG(total), 0) as ticket_medio,
                COUNT(DISTINCT DATE(data_venda)) as dias_com_venda,
                MAX(total) as maior_venda,
                MIN(total) as menor_venda
            FROM vendas 
            WHERE estabelecimento_id = :est_id 
                AND data_venda >= :start_date
                AND data_venda < :end_date
                AND status = 'finalizada'
        """
        )

        result = db.session.execute(
            query,
            {"est_id": estabelecimento_id, "start_date": start_date, "end_date": end_date},
        ).first()

        periodo_dias = max(1, (end_date - start_date).days)

        return {
            "total_vendas": result.total_vendas or 0,
            "total_faturado": float(result.total_faturado or 0),
            "ticket_medio": float(result.ticket_medio or 0),
            "dias_com_venda": result.dias_com_venda or 0,
            "periodo_dias": periodo_dias,
            "maior_venda": float(result.maior_venda or 0),
            "menor_venda": float(result.menor_venda or 0),
        }

    @staticmethod
    def get_sales_timeseries(
        estabelecimento_id: int, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Séries temporais de vendas - Agrupado por dia
        """
        data_inicio = datetime.now() - timedelta(days=days)

        # Query usando índice de data
        results = (
            db.session.query(
                func.date(Venda.data_venda).label("data"),
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
                func.avg(Venda.total).label("ticket_medio"),
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == "finalizada",
            )
            .group_by(func.date(Venda.data_venda))
            .order_by(func.date(Venda.data_venda))
            .all()
        )

        return [
            {
                "data": str(r.data),
                "quantidade": r.quantidade,
                "total": float(r.total or 0),
                "ticket_medio": float(r.ticket_medio or 0),
            }
            for r in results
        ]

    @staticmethod
    def get_inventory_summary(estabelecimento_id: int) -> Dict[str, Any]:
        """
        Resumo de estoque otimizado
        """
        data_inicio = datetime.now() - timedelta(days=365)

        query = text(
            """
            WITH wac AS (
                SELECT
                    produto_id,
                    SUM(quantidade * custo_unitario) / NULLIF(SUM(quantidade), 0) AS custo_medio_ponderado
                FROM movimentacoes_estoque
                WHERE estabelecimento_id = :est_id
                    AND tipo = 'entrada'
                    AND custo_unitario IS NOT NULL
                    AND created_at >= :data_inicio
                GROUP BY produto_id
            ),
            base AS (
                SELECT
                    p.id,
                    p.quantidade,
                    p.preco_venda,
                    p.preco_custo,
                    COALESCE(wac.custo_medio_ponderado, p.preco_custo) AS custo_unitario_base,
                    CASE WHEN wac.custo_medio_ponderado IS NULL THEN 0 ELSE 1 END AS has_wac
                FROM produtos p
                LEFT JOIN wac ON wac.produto_id = p.id
                WHERE p.estabelecimento_id = :est_id
                    AND p.ativo = TRUE
            )
            SELECT
                COUNT(*) as total_produtos,
                SUM(quantidade) as total_unidades,
                SUM(quantidade * preco_venda) as valor_total,
                SUM(quantidade * custo_unitario_base) as custo_total,
                AVG(quantidade) as estoque_medio,
                SUM(CASE WHEN quantidade < 10 THEN 1 ELSE 0 END) as baixo_estoque,
                SUM(CASE WHEN quantidade = 0 THEN 1 ELSE 0 END) as sem_estoque,
                SUM(has_wac) as produtos_com_wac
            FROM base
        """
        )

        result = db.session.execute(
            query, {"est_id": estabelecimento_id, "data_inicio": data_inicio}
        ).first()

        return {
            "total_produtos": result.total_produtos or 0,
            "total_unidades": result.total_unidades or 0,
            "valor_total": float(result.valor_total or 0),
            "custo_total": float(result.custo_total or 0),
            "lucro_potencial": float(
                (result.valor_total or 0) - (result.custo_total or 0)
            ),
            "estoque_medio": float(result.estoque_medio or 0),
            "baixo_estoque": result.baixo_estoque or 0,
            "sem_estoque": result.sem_estoque or 0,
            "produtos_com_wac": int(getattr(result, "produtos_com_wac", 0) or 0),
            "wac_days": 365,
        }

    @staticmethod
    def get_top_products(
        estabelecimento_id: int, days: int = 30, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Top produtos vendidos - Query otimizada com JOIN
        """
        data_inicio = datetime.now() - timedelta(days=days)

        # Usando subquery para performance
        results = (
            db.session.query(
                Produto.id,
                Produto.nome,
                Produto.preco_custo,
                func.sum(ItemVenda.quantidade).label("quantidade_vendida"),
                func.sum(ItemVenda.total_item).label("faturamento"),
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == "finalizada",
            )
            .group_by(Produto.id, Produto.nome, Produto.preco_custo)
            .order_by(func.sum(ItemVenda.total_item).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": r.id,
                "nome": r.nome,
                "categoria": "Geral",  # Temporário
                "quantidade_vendida": int(r.quantidade_vendida or 0),
                "faturamento": float(r.faturamento or 0),
                "preco_custo": float(r.preco_custo or 0),
            }
            for r in results
        ]

    @staticmethod
    def get_customer_metrics(estabelecimento_id: int, days: int = 90) -> Dict[str, Any]:
        """
        Métricas de clientes - Otimizado com índices
        """
        data_inicio = datetime.now() - timedelta(days=days)

        # Query única para múltiplas métricas
        query = text(
            """
            SELECT
                COUNT(DISTINCT cliente_id) as clientes_unicos,
                AVG(total) as ticket_medio_cliente,
                MAX(total) as maior_compra,
                COUNT(*) / COUNT(DISTINCT cliente_id) as frequencia_media
            FROM vendas
            WHERE estabelecimento_id = :est_id
                AND data_venda >= :data_inicio
                AND status = 'finalizada'
                AND cliente_id IS NOT NULL
        """
        )

        result = db.session.execute(
            query, {"est_id": estabelecimento_id, "data_inicio": data_inicio}
        ).first()

        return {
            "clientes_unicos": result.clientes_unicos or 0,
            "ticket_medio_cliente": float(result.ticket_medio_cliente or 0),
            "maior_compra": float(result.maior_compra or 0),
            "frequencia_media": float(result.frequencia_media or 0),
        }

    @staticmethod
    def get_expense_details(estabelecimento_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        Detalhes de despesas agrupadas por categoria
        """
        from app.models import Despesa  # Importação local para evitar ciclo
        
        data_inicio = datetime.now() - timedelta(days=days)
        
        # Query agrupada por categoria
        results = (
            db.session.query(
                Despesa.categoria,
                func.sum(Despesa.valor).label("total_categoria"),
                func.count(Despesa.id).label("qtd_despesas")
            )
            .filter(
                Despesa.estabelecimento_id == estabelecimento_id,
                Despesa.data_despesa >= data_inicio
            )
            .group_by(Despesa.categoria)
            .order_by(func.sum(Despesa.valor).desc())
            .all()
        )
        
        # Calcular total geral para percentuais
        total_geral = sum([float(r.total_categoria or 0) for r in results]) or 1.0
        
        return [
            {
                "tipo": r.categoria or "Outros",
                "valor": float(r.total_categoria or 0),
                "percentual": (float(r.total_categoria or 0) / total_geral) * 100,
                "impacto_lucro": 0.0, # Calculado no orquestrador se necessário
                "tendencia": "estavel" # Placeholder
            }
            for r in results
        ]
