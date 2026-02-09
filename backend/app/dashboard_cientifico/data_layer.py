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

    @staticmethod
    def get_sales_by_hour(estabelecimento_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        Vendas agrupadas por hora do dia - Para análise de pico de vendas
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        # Query agrupada por hora
        results = (
            db.session.query(
                func.extract('hour', Venda.data_venda).label('hora'),
                func.count(Venda.id).label('quantidade'),
                func.sum(Venda.total).label('total'),
                func.avg(Venda.total).label('ticket_medio')
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada'
            )
            .group_by(func.extract('hour', Venda.data_venda))
            .order_by(func.extract('hour', Venda.data_venda))
            .all()
        )
        
        # Calcular margem aproximada (assumindo 30% de margem média)
        return [
            {
                "hora": int(r.hora),
                "quantidade": int(r.quantidade or 0),
                "total": float(r.total or 0),
                "ticket_medio": float(r.ticket_medio or 0),
                "lucro": float(r.total or 0) * 0.3,  # Margem aproximada
                "margem": 30.0  # Margem padrão
            }
            for r in results
        ]

    @staticmethod
    def get_top_products_by_hour(estabelecimento_id: int, days: int = 30, top_n: int = 5) -> Dict[int, List[Dict[str, Any]]]:
        """
        Top produtos mais vendidos por hora do dia
        Retorna um dicionário onde a chave é a hora (0-23) e o valor é a lista dos top N produtos
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        # Query para buscar produtos vendidos por hora
        results = (
            db.session.query(
                func.extract('hour', Venda.data_venda).label('hora'),
                Produto.id.label('produto_id'),
                Produto.nome.label('produto_nome'),
                func.sum(ItemVenda.quantidade).label('quantidade_vendida'),
                func.sum(ItemVenda.total_item).label('faturamento')
            )
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada'
            )
            .group_by(
                func.extract('hour', Venda.data_venda),
                Produto.id,
                Produto.nome
            )
            .order_by(
                func.extract('hour', Venda.data_venda),
                func.sum(ItemVenda.total_item).desc()
            )
            .all()
        )
        
        # Organizar por hora
        produtos_por_hora = {}
        for r in results:
            hora = int(r.hora)
            if hora not in produtos_por_hora:
                produtos_por_hora[hora] = []
            
            # Adicionar apenas os top N produtos por hora
            if len(produtos_por_hora[hora]) < top_n:
                produtos_por_hora[hora].append({
                    "produto_id": r.produto_id,
                    "produto_nome": r.produto_nome,
                    "quantidade_vendida": int(r.quantidade_vendida or 0),
                    "faturamento": float(r.faturamento or 0)
                })
        
        return produtos_por_hora

    @staticmethod
    def get_customer_temporal_patterns(estabelecimento_id: int, days: int = 90) -> Dict[str, Any]:
        """
        Análise de padrões temporais de clientes
        Retorna perfis de compra por horário e segmentação temporal
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        # Query para padrões de clientes por horário
        results = (
            db.session.query(
                Cliente.id.label('cliente_id'),
                Cliente.nome.label('cliente_nome'),
                func.extract('hour', Venda.data_venda).label('hora_preferida'),
                func.count(Venda.id).label('total_compras'),
                func.sum(Venda.total).label('total_gasto'),
                func.avg(Venda.total).label('ticket_medio')
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada',
                Cliente.id.isnot(None)
            )
            .group_by(
                Cliente.id,
                Cliente.nome,
                func.extract('hour', Venda.data_venda)
            )
            .all()
        )
        
        # Organizar dados
        clientes_por_horario = {}
        perfis_temporais = {
            'matutino': [],  # 6h-12h
            'vespertino': [],  # 12h-18h
            'noturno': []  # 18h-23h
        }
        
        for r in results:
            hora = int(r.hora_preferida)
            if hora not in clientes_por_horario:
                clientes_por_horario[hora] = {
                    'total_clientes': 0,
                    'faturamento_total': 0,
                    'ticket_medio': 0
                }
            
            clientes_por_horario[hora]['total_clientes'] += 1
            clientes_por_horario[hora]['faturamento_total'] += float(r.total_gasto or 0)
            
            # Classificar cliente por perfil temporal
            cliente_data = {
                'cliente_id': r.cliente_id,
                'cliente_nome': r.cliente_nome,
                'hora_preferida': hora,
                'total_compras': r.total_compras,
                'total_gasto': float(r.total_gasto or 0),
                'ticket_medio': float(r.ticket_medio or 0)
            }
            
            if 6 <= hora < 12:
                perfis_temporais['matutino'].append(cliente_data)
            elif 12 <= hora < 18:
                perfis_temporais['vespertino'].append(cliente_data)
            elif 18 <= hora <= 23:
                perfis_temporais['noturno'].append(cliente_data)
        
        # Calcular ticket médio por horário
        for hora in clientes_por_horario:
            if clientes_por_horario[hora]['total_clientes'] > 0:
                clientes_por_horario[hora]['ticket_medio'] = (
                    clientes_por_horario[hora]['faturamento_total'] / 
                    clientes_por_horario[hora]['total_clientes']
                )
        
        return {
            'clientes_por_horario': clientes_por_horario,
            'perfis_temporais': perfis_temporais,
            'total_clientes_analisados': len(results)
        }

    @staticmethod
    def get_hourly_concentration_metrics(estabelecimento_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Métricas de concentração de faturamento por horário
        Calcula índice de Gini e análise de diversificação
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        # Query para faturamento por horário
        results = (
            db.session.query(
                func.extract('hour', Venda.data_venda).label('hora'),
                func.sum(Venda.total).label('faturamento')
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada'
            )
            .group_by(func.extract('hour', Venda.data_venda))
            .order_by(func.sum(Venda.total).desc())
            .all()
        )
        
        if not results:
            return {
                'gini_index': 0,
                'concentration_ratio': 0,
                'diversification_score': 0,
                'top_hours': []
            }
        
        # Calcular métricas
        faturamentos = [float(r.faturamento or 0) for r in results]
        total_faturamento = sum(faturamentos)
        
        # Top 3 horas (concentração)
        top_3_faturamento = sum(faturamentos[:3]) if len(faturamentos) >= 3 else sum(faturamentos)
        concentration_ratio = (top_3_faturamento / total_faturamento * 100) if total_faturamento > 0 else 0
        
        # Índice de Gini simplificado (0 = perfeita igualdade, 100 = máxima concentração)
        n = len(faturamentos)
        if n > 1 and total_faturamento > 0:
            faturamentos_sorted = sorted(faturamentos)
            cumsum = 0
            for i, val in enumerate(faturamentos_sorted):
                cumsum += (2 * (i + 1) - n - 1) * val
            gini_index = cumsum / (n * total_faturamento) * 100
        else:
            gini_index = 0
        
        # Score de diversificação (inverso da concentração)
        diversification_score = 100 - concentration_ratio
        
        return {
            'gini_index': round(gini_index, 2),
            'concentration_ratio': round(concentration_ratio, 2),
            'diversification_score': round(diversification_score, 2),
            'top_hours': [
                {
                    'hora': int(r.hora),
                    'faturamento': float(r.faturamento or 0),
                    'percentual': (float(r.faturamento or 0) / total_faturamento * 100) if total_faturamento > 0 else 0
                }
                for r in results[:5]
            ]
        }

    @staticmethod
    def get_product_hour_correlation_matrix(estabelecimento_id: int, days: int = 30, top_products: int = 10) -> Dict[str, Any]:
        """
        Matriz de correlação Produto x Horário
        Mostra quais produtos vendem melhor em quais horários
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        # Buscar top produtos
        top_prods = (
            db.session.query(
                Produto.id,
                Produto.nome,
                func.sum(ItemVenda.quantidade).label('total_vendido')
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada'
            )
            .group_by(Produto.id, Produto.nome)
            .order_by(func.sum(ItemVenda.quantidade).desc())
            .limit(top_products)
            .all()
        )
        
        if not top_prods:
            return {'matrix': [], 'products': [], 'hours': []}
        
        produto_ids = [p.id for p in top_prods]
        produto_nomes = {p.id: p.nome for p in top_prods}
        
        # Buscar vendas por produto e horário
        results = (
            db.session.query(
                Produto.id.label('produto_id'),
                func.extract('hour', Venda.data_venda).label('hora'),
                func.sum(ItemVenda.quantidade).label('quantidade'),
                func.sum(ItemVenda.total_item).label('faturamento')
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada',
                Produto.id.in_(produto_ids)
            )
            .group_by(Produto.id, func.extract('hour', Venda.data_venda))
            .all()
        )
        
        # Organizar em matriz
        matrix = {}
        for r in results:
            produto_id = r.produto_id
            hora = int(r.hora)
            if produto_id not in matrix:
                matrix[produto_id] = {}
            matrix[produto_id][hora] = {
                'quantidade': int(r.quantidade or 0),
                'faturamento': float(r.faturamento or 0)
            }
        
        # Normalizar para percentuais (0-100) por produto
        matrix_normalized = []
        for produto_id in produto_ids:
            if produto_id not in matrix:
                continue
            
            total_produto = sum([v['faturamento'] for v in matrix[produto_id].values()])
            if total_produto == 0:
                continue
            
            row = {
                'produto_id': produto_id,
                'produto_nome': produto_nomes[produto_id],
                'horas': {}
            }
            
            for hora in range(24):
                if hora in matrix[produto_id]:
                    percentual = (matrix[produto_id][hora]['faturamento'] / total_produto) * 100
                    row['horas'][hora] = {
                        'percentual': round(percentual, 1),
                        'quantidade': matrix[produto_id][hora]['quantidade'],
                        'faturamento': matrix[produto_id][hora]['faturamento']
                    }
                else:
                    row['horas'][hora] = {
                        'percentual': 0,
                        'quantidade': 0,
                        'faturamento': 0
                    }
            
            matrix_normalized.append(row)
        
        return {
            'matrix': matrix_normalized,
            'products': [{'id': p.id, 'nome': p.nome} for p in top_prods],
            'hours': list(range(24))
        }

    @staticmethod
    def get_customer_product_affinity(estabelecimento_id: int, days: int = 90, min_support: int = 3) -> List[Dict[str, Any]]:
        """
        Análise de afinidade Cliente x Produto
        Identifica quais clientes compram quais produtos com frequência
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        # Query para buscar padrões de compra
        results = (
            db.session.query(
                Cliente.id.label('cliente_id'),
                Cliente.nome.label('cliente_nome'),
                Produto.id.label('produto_id'),
                Produto.nome.label('produto_nome'),
                func.count(Venda.id).label('frequencia_compra'),
                func.sum(ItemVenda.quantidade).label('quantidade_total'),
                func.sum(ItemVenda.total_item).label('faturamento_total'),
                func.avg(ItemVenda.total_item).label('ticket_medio')
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada',
                Cliente.id.isnot(None)
            )
            .group_by(Cliente.id, Cliente.nome, Produto.id, Produto.nome)
            .having(func.count(Venda.id) >= min_support)
            .order_by(func.count(Venda.id).desc())
            .limit(50)
            .all()
        )
        
        return [
            {
                'cliente_id': r.cliente_id,
                'cliente_nome': r.cliente_nome,
                'produto_id': r.produto_id,
                'produto_nome': r.produto_nome,
                'frequencia_compra': r.frequencia_compra,
                'quantidade_total': int(r.quantidade_total or 0),
                'faturamento_total': float(r.faturamento_total or 0),
                'ticket_medio': float(r.ticket_medio or 0),
                'score_afinidade': r.frequencia_compra * float(r.faturamento_total or 0)
            }
            for r in results
        ]

    @staticmethod
    def get_hourly_customer_behavior(estabelecimento_id: int, days: int = 60) -> Dict[str, Any]:
        """
        Comportamento de clientes por horário
        Analisa ticket médio, frequência e preferências por horário
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        results = (
            db.session.query(
                func.extract('hour', Venda.data_venda).label('hora'),
                func.count(func.distinct(Venda.cliente_id)).label('clientes_unicos'),
                func.count(Venda.id).label('total_vendas'),
                func.avg(Venda.total).label('ticket_medio'),
                func.sum(Venda.total).label('faturamento_total')
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada',
                Venda.cliente_id.isnot(None)
            )
            .group_by(func.extract('hour', Venda.data_venda))
            .order_by(func.extract('hour', Venda.data_venda))
            .all()
        )
        
        comportamento_por_hora = []
        for r in results:
            hora = int(r.hora)
            clientes_unicos = r.clientes_unicos or 0
            total_vendas = r.total_vendas or 0
            
            # Calcular frequência média (vendas por cliente)
            frequencia_media = (total_vendas / clientes_unicos) if clientes_unicos > 0 else 0
            
            comportamento_por_hora.append({
                'hora': hora,
                'clientes_unicos': clientes_unicos,
                'total_vendas': total_vendas,
                'ticket_medio': float(r.ticket_medio or 0),
                'faturamento_total': float(r.faturamento_total or 0),
                'frequencia_media': round(frequencia_media, 2),
                'valor_por_cliente': float(r.faturamento_total or 0) / clientes_unicos if clientes_unicos > 0 else 0
            })
        
        return {
            'comportamento_por_hora': comportamento_por_hora,
            'total_horas_analisadas': len(comportamento_por_hora)
        }

    @staticmethod
    def get_product_hour_correlation_matrix(estabelecimento_id: int, days: int = 30, top_products: int = 10) -> Dict[str, Any]:
        """
        Matriz de correlação Produto x Horário
        Mostra quais produtos vendem melhor em quais horários
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        # Buscar top produtos
        top_prods = (
            db.session.query(
                Produto.id,
                Produto.nome,
                func.sum(ItemVenda.quantidade).label('total_vendido')
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada'
            )
            .group_by(Produto.id, Produto.nome)
            .order_by(func.sum(ItemVenda.quantidade).desc())
            .limit(top_products)
            .all()
        )
        
        if not top_prods:
            return {'matrix': [], 'products': [], 'hours': []}
        
        produto_ids = [p.id for p in top_prods]
        produto_nomes = {p.id: p.nome for p in top_prods}
        
        # Buscar vendas por produto e horário
        results = (
            db.session.query(
                Produto.id.label('produto_id'),
                func.extract('hour', Venda.data_venda).label('hora'),
                func.sum(ItemVenda.quantidade).label('quantidade'),
                func.sum(ItemVenda.total_item).label('faturamento')
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada',
                Produto.id.in_(produto_ids)
            )
            .group_by(Produto.id, func.extract('hour', Venda.data_venda))
            .all()
        )
        
        # Organizar em matriz
        matrix = {}
        for r in results:
            produto_id = r.produto_id
            hora = int(r.hora)
            if produto_id not in matrix:
                matrix[produto_id] = {}
            matrix[produto_id][hora] = {
                'quantidade': int(r.quantidade or 0),
                'faturamento': float(r.faturamento or 0)
            }
        
        # Normalizar para percentuais (0-100) por produto
        matrix_normalized = []
        for produto_id in produto_ids:
            if produto_id not in matrix:
                continue
            
            total_produto = sum([v['faturamento'] for v in matrix[produto_id].values()])
            if total_produto == 0:
                continue
            
            row = {
                'produto_id': produto_id,
                'produto_nome': produto_nomes[produto_id],
                'horas': {}
            }
            
            for hora in range(24):
                if hora in matrix[produto_id]:
                    percentual = (matrix[produto_id][hora]['faturamento'] / total_produto) * 100
                    row['horas'][hora] = {
                        'percentual': round(percentual, 1),
                        'quantidade': matrix[produto_id][hora]['quantidade'],
                        'faturamento': matrix[produto_id][hora]['faturamento']
                    }
                else:
                    row['horas'][hora] = {
                        'percentual': 0,
                        'quantidade': 0,
                        'faturamento': 0
                    }
            
            matrix_normalized.append(row)
        
        return {
            'matrix': matrix_normalized,
            'products': [{'id': p.id, 'nome': p.nome} for p in top_prods],
            'hours': list(range(24))
        }

    @staticmethod
    def get_customer_product_affinity(estabelecimento_id: int, days: int = 90, min_support: int = 3) -> List[Dict[str, Any]]:
        """
        Análise de afinidade Cliente x Produto
        Identifica quais clientes compram quais produtos com frequência
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        # Query para buscar padrões de compra
        results = (
            db.session.query(
                Cliente.id.label('cliente_id'),
                Cliente.nome.label('cliente_nome'),
                Produto.id.label('produto_id'),
                Produto.nome.label('produto_nome'),
                func.count(Venda.id).label('frequencia_compra'),
                func.sum(ItemVenda.quantidade).label('quantidade_total'),
                func.sum(ItemVenda.total_item).label('faturamento_total'),
                func.avg(ItemVenda.total_item).label('ticket_medio')
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .join(ItemVenda, ItemVenda.venda_id == Venda.id)
            .join(Produto, Produto.id == ItemVenda.produto_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada',
                Cliente.id.isnot(None)
            )
            .group_by(Cliente.id, Cliente.nome, Produto.id, Produto.nome)
            .having(func.count(Venda.id) >= min_support)
            .order_by(func.count(Venda.id).desc())
            .limit(50)
            .all()
        )
        
        return [
            {
                'cliente_id': r.cliente_id,
                'cliente_nome': r.cliente_nome,
                'produto_id': r.produto_id,
                'produto_nome': r.produto_nome,
                'frequencia_compra': r.frequencia_compra,
                'quantidade_total': int(r.quantidade_total or 0),
                'faturamento_total': float(r.faturamento_total or 0),
                'ticket_medio': float(r.ticket_medio or 0),
                'score_afinidade': r.frequencia_compra * float(r.faturamento_total or 0)
            }
            for r in results
        ]

    @staticmethod
    def get_hourly_customer_behavior(estabelecimento_id: int, days: int = 60) -> Dict[str, Any]:
        """
        Comportamento de clientes por horário
        Analisa ticket médio, frequência e preferências por horário
        """
        data_inicio = datetime.now() - timedelta(days=days)
        
        results = (
            db.session.query(
                func.extract('hour', Venda.data_venda).label('hora'),
                func.count(func.distinct(Venda.cliente_id)).label('clientes_unicos'),
                func.count(Venda.id).label('total_vendas'),
                func.avg(Venda.total).label('ticket_medio'),
                func.sum(Venda.total).label('faturamento_total')
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == 'finalizada',
                Venda.cliente_id.isnot(None)
            )
            .group_by(func.extract('hour', Venda.data_venda))
            .order_by(func.extract('hour', Venda.data_venda))
            .all()
        )
        
        comportamento_por_hora = []
        for r in results:
            hora = int(r.hora)
            clientes_unicos = r.clientes_unicos or 0
            total_vendas = r.total_vendas or 0
            
            # Calcular frequência média (vendas por cliente)
            frequencia_media = (total_vendas / clientes_unicos) if clientes_unicos > 0 else 0
            
            comportamento_por_hora.append({
                'hora': hora,
                'clientes_unicos': clientes_unicos,
                'total_vendas': total_vendas,
                'ticket_medio': float(r.ticket_medio or 0),
                'faturamento_total': float(r.faturamento_total or 0),
                'frequencia_media': round(frequencia_media, 2),
                'valor_por_cliente': float(r.faturamento_total or 0) / clientes_unicos if clientes_unicos > 0 else 0
            })
        
        return {
            'comportamento_por_hora': comportamento_por_hora,
            'total_horas_analisadas': len(comportamento_por_hora)
        }
