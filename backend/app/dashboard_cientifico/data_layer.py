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
                COALESCE(SUM(valor_total), 0) as total_faturado,
                COALESCE(AVG(valor_total), 0) as ticket_medio,
                COUNT(DISTINCT DATE(data_venda)) as dias_com_venda,
                MAX(valor_total) as maior_venda,
                MIN(valor_total) as menor_venda
            FROM venda 
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
                func.sum(Venda.valor_total).label("total"),
                func.avg(Venda.valor_total).label("ticket_medio"),
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
        # Query única com índices
        query = text(
            """
            SELECT 
                COUNT(*) as total_produtos,
                SUM(quantidade_estoque) as total_unidades,
                SUM(quantidade_estoque * preco_venda) as valor_total,
                SUM(quantidade_estoque * preco_custo) as custo_total,
                AVG(quantidade_estoque) as estoque_medio,
                SUM(CASE WHEN quantidade_estoque < 10 THEN 1 ELSE 0 END) as baixo_estoque,
                SUM(CASE WHEN quantidade_estoque = 0 THEN 1 ELSE 0 END) as sem_estoque
            FROM produto 
            WHERE estabelecimento_id = :est_id 
                AND ativo = TRUE
        """
        )

        result = db.session.execute(query, {"est_id": estabelecimento_id}).first()

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
                Produto.nome,
                Produto.categoria,
                func.sum(ItemVenda.quantidade).label("quantidade_vendida"),
                func.sum(ItemVenda.subtotal).label("faturamento"),
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == "finalizada",
            )
            .group_by(Produto.id, Produto.nome, Produto.categoria)
            .order_by(func.sum(ItemVenda.subtotal).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "nome": r.nome,
                "categoria": r.categoria,
                "quantidade_vendida": int(r.quantidade_vendida or 0),
                "faturamento": float(r.faturamento or 0),
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
                AVG(valor_total) as ticket_medio_cliente,
                MAX(valor_total) as maior_compra,
                COUNT(*) / COUNT(DISTINCT cliente_id) as frequencia_media
            FROM venda 
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
