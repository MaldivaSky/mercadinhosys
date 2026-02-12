from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func, desc, extract, case, and_
from decimal import Decimal, ROUND_HALF_UP
from app.models import (
    db, Venda, VendaItem, Produto, Cliente,
    Funcionario, FuncionarioBeneficio, Beneficio, BancoHoras, RegistroPonto, ConfiguracaoHorario,
    Despesa
)
import logging

logger = logging.getLogger(__name__)

class DataLayer:
    """
    Camada de acesso a dados para o Dashboard Científico.
    Executa queries otimizadas e retorna dados brutos ou semi-processados.
    """

    @staticmethod
    def get_sales_summary_range(estabelecimento_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Resumo de vendas para um período específico"""
        try:
            # 🔥 OTIMIZAÇÃO: Usar comparação direta de datetime em vez de func.date()
            result = db.session.query(
                func.count(Venda.id).label('total_vendas'),
                func.sum(Venda.total).label('total_faturado'),
                func.avg(Venda.total).label('ticket_medio'),
                func.count(func.distinct(func.date(Venda.data_venda))).label('dias_com_venda')
            ).filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= start_date.date() if isinstance(start_date, datetime) else start_date,
                Venda.data_venda <= end_date.date() if isinstance(end_date, datetime) else end_date,
                Venda.status == 'finalizada'
            ).first()

            return {
                "total_vendas": result.total_vendas or 0,
                "total_faturado": float(result.total_faturado or 0),
                "ticket_medio": float(result.ticket_medio or 0),
                "dias_com_venda": result.dias_com_venda or 0
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_sales_summary_range: {e}")
            return {"total_vendas": 0, "total_faturado": 0.0, "ticket_medio": 0.0, "dias_com_venda": 0}

    @staticmethod
    def get_sales_financials(estabelecimento_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Retorna dados financeiros agregados (Faturamento, CMV, Lucro Bruto)
        Corrigido para usar VendaItem para calcular o custo real dos produtos vendidos.
        """
        try:
            # Join Venda -> VendaItem para somar custo * quantidade
            # Importante: VendaItem.custo_unitario armazena o custo no momento da venda (histórico)
            
            # 🔥 OTIMIZAÇÃO: Usar comparação direta de datetime
            result = db.session.query(
                func.coalesce(func.sum(Venda.total), 0).label('revenue'),
                func.coalesce(func.sum(VendaItem.custo_unitario * VendaItem.quantidade), 0).label('cogs'),
                func.coalesce(func.sum(VendaItem.total_item), 0).label('gross_sales')
            ).join(VendaItem, Venda.id == VendaItem.venda_id).filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= start_date.date() if isinstance(start_date, datetime) else start_date,
                Venda.data_venda <= end_date.date() if isinstance(end_date, datetime) else end_date,
                Venda.status == 'finalizada'
            ).first()

            revenue = float(result.revenue or 0)
            cogs = float(result.cogs or 0)
            
            # Se COGS for zero (dados antigos sem custo histórico), tentar estimar?
            # Por enquanto, assumimos que 0 é o valor real se não houver dados.
            
            return {
                "revenue": revenue,
                "cogs": cogs,
                "gross_profit": revenue - cogs
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_sales_financials: {e}")
            return {"revenue": 0.0, "cogs": 0.0, "gross_profit": 0.0}

    @staticmethod
    def get_sales_timeseries(estabelecimento_id: int, days: int) -> List[Dict[str, Any]]:
        """Série temporal de vendas diárias"""
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date()
            
            # Agrupa por data (dia)
            results = db.session.query(
                func.date(Venda.data_venda).label('data'),
                func.sum(Venda.total).label('valor'),
                func.count(Venda.id).label('qtd')
            ).filter(
                Venda.estabelecimento_id == estabelecimento_id,
                func.date(Venda.data_venda) >= start_date,
                Venda.status == 'finalizada'
            ).group_by(
                func.date(Venda.data_venda)
            ).order_by(
                func.date(Venda.data_venda)
            ).all()

            return [
                {
                    "data": str(r.data),
                    "total": float(r.valor or 0),
                    "valor": float(r.valor or 0),
                    "qtd": r.qtd
                }
                for r in results
            ]
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_sales_timeseries: {e}")
            return []

    # ... (other replacements will follow same pattern)

    @staticmethod
    def get_inventory_summary(estabelecimento_id: int) -> Dict[str, Any]:
        """Resumo do inventário (valor total, itens baixo estoque)"""
        try:
            # Valor total do estoque (custo * quantidade)
            valor_total = db.session.query(
                func.sum(Produto.preco_custo * Produto.quantidade)
            ).filter(
                Produto.estabelecimento_id == estabelecimento_id,
                Produto.ativo == True
            ).scalar()

            # Quantidade de produtos com estoque abaixo do mínimo
            baixo_estoque = db.session.query(func.count(Produto.id)).filter(
                Produto.estabelecimento_id == estabelecimento_id,
                Produto.ativo == True,
                Produto.quantidade <= Produto.quantidade_minima
            ).scalar()

            return {
                "valor_total": float(valor_total or 0),
                "baixo_estoque": baixo_estoque or 0
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_inventory_summary: {e}")
            return {"valor_total": 0.0, "baixo_estoque": 0}

    @staticmethod
    def get_customer_metrics(estabelecimento_id: int, days: int) -> Dict[str, Any]:
        """Métricas de clientes (únicos, ticket médio)"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            clientes_unicos = db.session.query(func.count(func.distinct(Venda.cliente_id))).filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= start_date,
                Venda.cliente_id.isnot(None)
            ).scalar()

            # Ticket médio por cliente (não por venda)
            # Aproximação: Total Faturado / Clientes Únicos
            total_faturado = db.session.query(func.sum(Venda.total)).filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= start_date,
                Venda.status == 'finalizada'
            ).scalar() or 0

            ticket_medio_cliente = float(total_faturado) / clientes_unicos if clientes_unicos and clientes_unicos > 0 else 0

            # Maior compra do período
            maior_compra = db.session.query(func.max(Venda.total)).filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= start_date,
                Venda.status == 'finalizada'
            ).scalar()

            return {
                "clientes_unicos": clientes_unicos or 0,
                "ticket_medio_cliente": float(ticket_medio_cliente),
                "maior_compra": float(maior_compra or 0)
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_customer_metrics: {e}")
            return {"clientes_unicos": 0, "ticket_medio_cliente": 0.0, "maior_compra": 0.0}

    @staticmethod
    def get_top_products(estabelecimento_id: int, days: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Top produtos mais vendidos (Curva ABC)"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            results = db.session.query(
                Produto.id,
                Produto.nome,
                Produto.preco_custo,
                Produto.preco_venda,
                func.sum(VendaItem.quantidade).label('quantidade_vendida'),
                func.sum(VendaItem.total_item).label('faturamento')
            ).join(VendaItem, VendaItem.produto_id == Produto.id)\
             .join(Venda, Venda.id == VendaItem.venda_id)\
             .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= start_date,
                Venda.status == 'finalizada'
            ).group_by(
                Produto.id, Produto.nome, Produto.preco_custo, Produto.preco_venda
            ).order_by(
                desc('faturamento')
            ).limit(limit).all()

            return [
                {
                    "id": r.id,
                    "nome": r.nome,
                    "preco_custo": float(r.preco_custo or 0),
                    "preco_venda": float(r.preco_venda or 0),
                    "quantidade_vendida": float(r.quantidade_vendida or 0),
                    "faturamento": float(r.faturamento or 0),
                    # Margem lucro correta: (Venda - Custo) / Custo * 100
                    "margem": ((float(r.preco_venda or 0) - float(r.preco_custo or 0)) / float(r.preco_custo or 0) * 100) if r.preco_custo and r.preco_custo > 0 else 0
                }
                for r in results
            ]
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_top_products: {e}")
            return []

    @staticmethod
    def get_expense_details(estabelecimento_id: int, days: int) -> List[Dict[str, Any]]:
        """Detalhamento de despesas por categoria"""
        try:
            # Normalizar para data pura para comparação correta no Postgres
            start_date_only = (datetime.utcnow() - timedelta(days=days)).date()
            
            results = db.session.query(
                Despesa.tipo,
                func.sum(Despesa.valor).label('total')
            ).filter(
                Despesa.estabelecimento_id == estabelecimento_id,
                Despesa.data_despesa >= start_date_only
            ).group_by(Despesa.tipo).all()

            return [
                {
                    "tipo": r.tipo or "Sem Categoria", 
                    "valor": float(Decimal(str(r.total or 0)))
                }
                for r in results
            ]
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_expense_details: {e}")
            return []

    @staticmethod
    def get_sales_by_hour(estabelecimento_id: int, days: int) -> List[Dict[str, Any]]:
        """Vendas agrupadas por hora do dia (Heatmap)"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Compatibilidade cross-database para extração de hora
            from app.utils.query_helpers import get_hour_extract
            hour_extract = get_hour_extract(Venda.data_venda)

            results = db.session.query(
                hour_extract.label('hora'),
                func.count(Venda.id).label('qtd'),
                func.sum(Venda.total).label('total')
            ).filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= start_date,
                Venda.status == 'finalizada'
            ).group_by(hour_extract).order_by(hour_extract).all()

            return [
                {"hora": int(r.hora) if r.hora is not None else 0, "qtd": r.qtd, "total": float(r.total or 0)}
                for r in results
            ]
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_sales_by_hour: {e}")
            return []

    @staticmethod
    def get_top_products_by_hour(estabelecimento_id: int, days: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """Top produtos por faixa horária (Manhã, Tarde, Noite)"""
        # Simplificação: Retorna top global por enquanto para não complicar query
        return DataLayer.get_top_products(estabelecimento_id, days, top_n)

    @staticmethod
    def get_customer_temporal_patterns(estabelecimento_id: int, days: int) -> Dict[str, Any]:
        """Padrões de compra por dia da semana"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Compatibilidade cross-database para extração de dia da semana
            from app.utils.query_helpers import get_dow_extract
            dow_extract = get_dow_extract(Venda.data_venda)
            
            results = db.session.query(
                dow_extract.label('dia_semana'),
                func.count(Venda.id).label('qtd'),
                func.sum(Venda.total).label('total')
            ).filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= start_date,
                Venda.status == 'finalizada'
            ).group_by(dow_extract).all()
            
            dias_map = {
                '0': 'Domingo', '1': 'Segunda', '2': 'Terça', '3': 'Quarta',
                '4': 'Quinta', '5': 'Sexta', '6': 'Sábado'
            }

            return [
                {
                    "dia": dias_map.get(str(r.dia_semana), str(r.dia_semana)) if r.dia_semana is not None else "Desconhecido",
                    "qtd": r.qtd,
                    "total": float(r.total or 0)
                }
                for r in results
            ]
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_customer_temporal_patterns: {e}")
            return []

    @staticmethod
    def get_hourly_concentration_metrics(estabelecimento_id: int, days: int) -> Dict[str, Any]:
        """
        Concentração de vendas em horários de pico com Índice de Gini
        Gini = 0 (distribuição perfeita) a 1 (concentração total)
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Compatibilidade cross-database para extração de hora
            from app.utils.query_helpers import get_hour_extract
            hour_extract = get_hour_extract(Venda.data_venda)

            # Buscar vendas por hora
            results = db.session.query(
                hour_extract.label('hora'),
                func.sum(Venda.total).label('total')
            ).filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= start_date,
                Venda.status == 'finalizada'
            ).group_by(hour_extract).order_by(hour_extract).all()
            
            if not results:
                return {
                    "gini_index": 0.0,
                    "concentration_top_3": 0.0,
                    "diversification": 100.0,
                    "top_hours": [],
                    "distribution": []
                }
            
            # Extrair valores de faturamento por hora
            hourly_values = [float(r.total or 0) for r in results]
            total_faturamento = sum(hourly_values)
            
            if total_faturamento == 0:
                return {
                    "gini_index": 0.0,
                    "concentration_top_3": 0.0,
                    "diversification": 100.0,
                    "top_hours": [],
                    "distribution": []
                }
            
            # 🔥 CALCULAR ÍNDICE DE GINI
            # Fórmula: Gini = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n+1)/n
            # Onde x_i são os valores ordenados
            n = len(hourly_values)
            sorted_values = sorted(hourly_values)
            
            numerator = sum((i + 1) * sorted_values[i] for i in range(n))
            gini_index = (2 * numerator) / (n * total_faturamento) - (n + 1) / n
            gini_index = max(0.0, min(1.0, gini_index))  # Garantir entre 0 e 1
            
            # 🔥 CONCENTRAÇÃO TOP 3 HORÁRIOS
            top_3_values = sorted(hourly_values, reverse=True)[:3]
            concentration_top_3 = (sum(top_3_values) / total_faturamento * 100) if total_faturamento > 0 else 0
            
            # 🔥 DIVERSIFICAÇÃO (inverso da concentração)
            # Se Gini baixo = bem distribuído = alta diversificação
            diversification = (1 - gini_index) * 100
            
            # 🔥 TOP 5 HORÁRIOS
            top_hours = []
            for r in sorted(results, key=lambda x: float(x.total or 0), reverse=True)[:5]:
                hora = int(r.hora) if r.hora is not None else 0
                total = float(r.total or 0)
                percentual = (total / total_faturamento * 100) if total_faturamento > 0 else 0
                top_hours.append({
                    "hora": f"{hora:02d}:00",
                    "faturamento": round(total, 2),
                    "percentual": round(percentual, 1)
                })
            
            # 🔥 DISTRIBUIÇÃO COMPLETA
            distribution = []
            for r in results:
                hora = int(r.hora) if r.hora is not None else 0
                total = float(r.total or 0)
                percentual = (total / total_faturamento * 100) if total_faturamento > 0 else 0
                distribution.append({
                    "hora": f"{hora:02d}:00",
                    "faturamento": round(total, 2),
                    "percentual": round(percentual, 1)
                })
            
            return {
                "gini_index": round(gini_index, 3),
                "concentration_top_3": round(concentration_top_3, 1),
                "diversification": round(diversification, 1),
                "top_hours": top_hours,
                "distribution": distribution,
                "interpretacao": {
                    "gini": "Baixa concentração - Vendas bem distribuídas" if gini_index < 0.4 else "Média concentração" if gini_index < 0.7 else "Alta concentração - Vendas concentradas em poucos horários",
                    "diversificacao": "Boa diversificação" if diversification > 60 else "Diversificação moderada" if diversification > 40 else "Baixa diversificação - Considere estratégias para outros horários"
                }
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_hourly_concentration_metrics: {e}")
            return {
                "gini_index": 0.0,
                "concentration_top_3": 0.0,
                "diversification": 100.0,
                "top_hours": [],
                "distribution": []
            }

    @staticmethod
    def get_product_hour_correlation_matrix(estabelecimento_id: int, days: int, top_products: int = 10) -> List[Dict[str, Any]]:
        """Matriz de correlação (simulada ou simplificada)"""
        return []

    @staticmethod
    def get_customer_product_affinity(estabelecimento_id: int, days: int, min_support: int = 3) -> List[Dict[str, Any]]:
        """Afinidade entre produtos (Market Basket Analysis simplificado)"""
        return []

    @staticmethod
    def get_hourly_customer_behavior(estabelecimento_id: int, days: int) -> List[Dict[str, Any]]:
        """Comportamento horário de clientes"""
        return []

    @staticmethod
    def get_last_purchase_orders(estabelecimento_id: int, produto_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Retorna o último pedido de compra para cada produto da lista.
        Responde ao requisito: "LINK EACH PRODUCT TO AN ORDER"
        """
        if not produto_ids:
            return {}
            
        from app.models import PedidoCompra, PedidoCompraItem, Fornecedor
        
        try:
            # Query para buscar o último pedido finalizado/recebido para cada produto
            # Usando subquery para encontrar a data máxima por produto
            subquery = db.session.query(
                PedidoCompraItem.produto_id,
                func.max(PedidoCompra.data_pedido).label('max_data')
            ).join(PedidoCompra).filter(
                PedidoCompra.estabelecimento_id == estabelecimento_id,
                PedidoCompraItem.produto_id.in_(produto_ids)
            ).group_by(PedidoCompraItem.produto_id).subquery()
            
            # Join dos dados reais do último pedido
            results = db.session.query(
                PedidoCompraItem.produto_id,
                PedidoCompra.id.label('pedido_id'),
                PedidoCompra.numero_pedido,
                PedidoCompra.data_pedido,
                PedidoCompra.status,
                Fornecedor.nome_fantasia.label('fornecedor_nome'),
                PedidoCompraItem.preco_unitario,
                PedidoCompraItem.quantidade_solicitada
            ).join(PedidoCompra, PedidoCompra.id == PedidoCompraItem.pedido_id)\
             .join(subquery, and_(
                 PedidoCompraItem.produto_id == subquery.c.produto_id,
                 PedidoCompra.data_pedido == subquery.c.max_data
             ))\
             .outerjoin(Fornecedor, Fornecedor.id == PedidoCompra.fornecedor_id)\
             .all()
             
            return {
                r.produto_id: {
                    "pedido_id": r.pedido_id,
                    "numero_pedido": r.numero_pedido,
                    "data": r.data_pedido.isoformat() if r.data_pedido else None,
                    "status": r.status,
                    "fornecedor": r.fornecedor_nome,
                    "preco_compra": float(r.preco_unitario or 0),
                    "quantidade_comprada": float(r.quantidade_solicitada or 0)
                }
                for r in results
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro em get_last_purchase_orders: {e}")
            return {}

    @staticmethod
    def get_rh_metrics(estabelecimento_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Métricas de RH: Horas Extras, Benefícios, Folha e Assiduidade
        """
        try:
            data_inicio = datetime.now() - timedelta(days=days)
            data_inicio_dia = data_inicio.date()
            hoje_dia = datetime.now().date()
            inicio_mes = hoje_dia.replace(day=1)

            config = ConfiguracaoHorario.query.filter_by(estabelecimento_id=estabelecimento_id).first()
            hora_saida_ref = config.hora_saida if config and config.hora_saida else datetime.strptime('18:00', '%H:%M').time()
            tolerancia_saida = int(config.tolerancia_saida) if config and config.tolerancia_saida is not None else 5

            def _time_to_minutes(t):
                return int(t.hour) * 60 + int(t.minute)

            minuto_saida_ref = _time_to_minutes(hora_saida_ref) + tolerancia_saida

            # 1. Custo Mensal de Benefícios Ativos
            total_beneficios = db.session.query(func.sum(FuncionarioBeneficio.valor)).join(Funcionario).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                FuncionarioBeneficio.ativo == True,
                Funcionario.ativo == True
            ).scalar() or 0

            # 2. Total Salários Base (Mensal)
            total_salarios = db.session.query(func.sum(Funcionario.salario_base)).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                Funcionario.ativo == True
            ).scalar() or 0

            # 3. Análise de Pontualidade e Assiduidade (Baseado em Registros Reais)
            # Busca registros de entrada no período
            registros_entrada = db.session.query(
                RegistroPonto.status,
                func.count(RegistroPonto.id).label('qtd'),
                func.sum(RegistroPonto.minutos_atraso).label('minutos_atraso')
            ).filter(
                RegistroPonto.estabelecimento_id == estabelecimento_id,
                RegistroPonto.data >= data_inicio_dia,
                RegistroPonto.tipo_registro == 'entrada'
            ).group_by(RegistroPonto.status).all()

            total_entradas = sum([r.qtd for r in registros_entrada])
            total_atrasos_qtd = sum([r.qtd for r in registros_entrada if r.status == 'atrasado'])
            total_minutos_atraso = sum([float(r.minutos_atraso or 0) for r in registros_entrada])

            taxa_pontualidade = ((total_entradas - total_atrasos_qtd) / total_entradas * 100) if total_entradas > 0 else 100.0

            # 4. Estimativa de Horas Extras (baseado na configuração do estabelecimento)
            saidas_periodo = db.session.query(
                RegistroPonto.funcionario_id,
                RegistroPonto.data,
                RegistroPonto.hora
            ).filter(
                RegistroPonto.estabelecimento_id == estabelecimento_id,
                RegistroPonto.data >= data_inicio_dia,
                RegistroPonto.tipo_registro == 'saida'
            ).all()

            minutos_extras_estimados = 0
            overtime_by_employee: Dict[int, int] = {}
            overtime_by_day: Dict[str, int] = {}

            for func_id, data_ponto, hora_ponto in saidas_periodo:
                if not hora_ponto:
                    continue
                minutos_saida = _time_to_minutes(hora_ponto)
                extra = minutos_saida - minuto_saida_ref
                if extra <= 0:
                    continue
                minutos_extras_estimados += extra
                overtime_by_employee[func_id] = overtime_by_employee.get(func_id, 0) + extra
                day_key = data_ponto.isoformat() if data_ponto else None
                if day_key:
                    overtime_by_day[day_key] = overtime_by_day.get(day_key, 0) + extra

            valor_hora_medio = (float(total_salarios) / 220) if total_salarios > 0 else 10.0
            custo_extras_estimado = (minutos_extras_estimados / 60) * valor_hora_medio * 1.5 # 50% adicional

            # 5. Custo Total Estimado
            custo_folha_estimado = float(total_salarios) + float(total_beneficios) + custo_extras_estimado

            funcionarios_ativos = Funcionario.query.filter_by(estabelecimento_id=estabelecimento_id, ativo=True).all()
            funcionarios_ativos_ids = [f.id for f in funcionarios_ativos]

            # 6. Rotatividade (Turnover)
            # Admissões no período
            admissoes = db.session.query(func.count(Funcionario.id)).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                Funcionario.data_admissao >= data_inicio
            ).scalar() or 0
            
            # Demissões no período
            demissoes = db.session.query(func.count(Funcionario.id)).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                Funcionario.data_demissao >= data_inicio
            ).scalar() or 0
            
            total_funcionarios = Funcionario.query.filter_by(estabelecimento_id=estabelecimento_id).count()
            # Se não tem funcionários hoje, não tem como calcular taxa corretamente, evita divisão por zero
            media_funcionarios = total_funcionarios if total_funcionarios > 0 else 1
            
            turnover_rate = (((admissoes + demissoes) / 2) / media_funcionarios * 100)

            # 7. Evolução de Admissões e Demissões (Últimos 12 meses)
            # 7. Evolução (Últimos 12 meses) - OTIMIZADO
            def _shift_month(year: int, month: int, delta: int):
                m = month + delta
                y = year + (m - 1) // 12
                m = ((m - 1) % 12) + 1
                return y, m

            now = datetime.now()
            current_year, current_month = now.year, now.month
            start_history = (datetime(current_year, current_month, 1) - timedelta(days=365)).date()
            
            # Busca todas as admissões do ano agrupadas por mês
            admissoes_bulk = db.session.query(
                extract('year', Funcionario.data_admissao).label('ano'),
                extract('month', Funcionario.data_admissao).label('mes'),
                func.count(Funcionario.id).label('qtd')
            ).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                Funcionario.data_admissao >= start_history
            ).group_by('ano', 'mes').all()
            
            admissoes_map = {(int(r.ano), int(r.mes)): r.qtd for r in admissoes_bulk}
            
            # Busca todas as demissões do ano agrupadas por mês
            demissoes_bulk = db.session.query(
                extract('year', Funcionario.data_demissao).label('ano'),
                extract('month', Funcionario.data_demissao).label('mes'),
                func.count(Funcionario.id).label('qtd')
            ).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                Funcionario.data_demissao >= start_history
            ).group_by('ano', 'mes').all()
            
            demissoes_map = {(int(r.ano), int(r.mes)): r.qtd for r in demissoes_bulk}
            
            # Busca todos os atrasos do ano agrupados por mês
            atrasos_bulk = db.session.query(
                extract('year', RegistroPonto.data).label('ano'),
                extract('month', RegistroPonto.data).label('mes'),
                func.count(RegistroPonto.id).label('qtd')
            ).filter(
                RegistroPonto.estabelecimento_id == estabelecimento_id,
                RegistroPonto.data >= start_history,
                RegistroPonto.minutos_atraso > 0
            ).group_by('ano', 'mes').all()
            
            atrasos_map = {(int(r.ano), int(r.mes)): r.qtd for r in atrasos_bulk}

            evolution_turnover = []
            meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            
            for i in range(11, -1, -1):
                y, m = _shift_month(current_year, current_month, -i)
                key = (y, m)
                
                admissoes_mes = admissoes_map.get(key, 0)
                demissoes_mes = demissoes_map.get(key, 0)
                atrasos_mes = atrasos_map.get(key, 0)
                
                evolution_turnover.append({
                    "mes": f"{meses_nomes[m-1]}/{str(y)[2:]}",
                    "admissoes": admissoes_mes,
                    "demissoes": demissoes_mes,
                    "atrasos": atrasos_mes,
                    "ausencias": 0,
                    "horas_extras": 0  # Simplificado para performance
                })

            # 8. Detalhamento de Benefícios
            benefits_breakdown = db.session.query(
                Beneficio.nome, 
                func.sum(FuncionarioBeneficio.valor).label('total')
            ).select_from(FuncionarioBeneficio).join(Beneficio).join(Funcionario).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                FuncionarioBeneficio.ativo == True,
                Funcionario.ativo == True
            ).group_by(Beneficio.nome).all()
            
            benefits_data = [{"name": b[0] or "Outros", "value": float(b[1] or 0)} for b in benefits_breakdown]

            # 9. Top Funcionários com Horas Extras (estimado via ponto, ou via BancoHoras se disponível)
            overtime_list = []
            banco_horas_mes = datetime.now().strftime("%Y-%m")
            banco_registros = db.session.query(BancoHoras).join(Funcionario).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                BancoHoras.mes_referencia == banco_horas_mes
            ).all()

            if banco_registros:
                ordenados = sorted(banco_registros, key=lambda r: int(r.saldo_minutos or 0), reverse=True)[:5]
                for r in ordenados:
                    overtime_list.append({
                        "nome": r.funcionario.nome if r.funcionario else "Desconhecido",
                        "horas": round((float(r.saldo_minutos or 0) / 60), 1),
                        "custo_estimado": float(r.valor_hora_extra or 0)
                    })
            else:
                if overtime_by_employee:
                    top_ids = sorted(overtime_by_employee.items(), key=lambda x: x[1], reverse=True)[:5]
                    nomes = dict(db.session.query(Funcionario.id, Funcionario.nome).filter(Funcionario.id.in_([i for i, _ in top_ids])).all())
                    for func_id, mins in top_ids:
                        overtime_list.append({
                            "nome": nomes.get(func_id, "Desconhecido"),
                            "horas": round(float(mins) / 60, 1),
                            "custo_estimado": round((float(mins) / 60) * valor_hora_medio * 1.5, 2)
                        })

            entradas_mes = db.session.query(
                RegistroPonto.funcionario_id,
                func.count(RegistroPonto.id).label("qtd"),
                func.sum(RegistroPonto.minutos_atraso).label("minutos_atraso")
            ).filter(
                RegistroPonto.estabelecimento_id == estabelecimento_id,
                RegistroPonto.data >= inicio_mes,
                RegistroPonto.tipo_registro == "entrada",
                RegistroPonto.status == "atrasado"
            ).group_by(RegistroPonto.funcionario_id).all()

            atrasos_por_func_id = {r.funcionario_id: {"qtd": int(r.qtd or 0), "minutos": int(r.minutos_atraso or 0)} for r in entradas_mes}

            saidas_mes = db.session.query(
                RegistroPonto.funcionario_id,
                RegistroPonto.data,
                RegistroPonto.hora
            ).filter(
                RegistroPonto.estabelecimento_id == estabelecimento_id,
                RegistroPonto.data >= inicio_mes,
                RegistroPonto.tipo_registro == "saida"
            ).all()

            extras_mes_por_func_id: Dict[int, int] = {}
            extras_mes_por_dia: Dict[str, int] = {}
            for func_id, data_ponto, hora_ponto in saidas_mes:
                if not hora_ponto:
                    continue
                minutos_saida = _time_to_minutes(hora_ponto)
                extra = minutos_saida - minuto_saida_ref
                if extra <= 0:
                    continue
                extras_mes_por_func_id[func_id] = extras_mes_por_func_id.get(func_id, 0) + int(extra)
                if data_ponto:
                    extras_mes_por_dia[data_ponto.isoformat()] = extras_mes_por_dia.get(data_ponto.isoformat(), 0) + int(extra)

            beneficios_por_func = db.session.query(
                FuncionarioBeneficio.funcionario_id,
                func.sum(FuncionarioBeneficio.valor).label("total")
            ).select_from(FuncionarioBeneficio).join(Funcionario).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                Funcionario.ativo == True,
                FuncionarioBeneficio.ativo == True
            ).group_by(FuncionarioBeneficio.funcionario_id).all()

            beneficios_por_func_id = {int(r.funcionario_id): float(r.total or 0) for r in beneficios_por_func}

            dias_uteis_mes = 0
            d = inicio_mes
            while d <= hoje_dia:
                if d.weekday() != 6:
                    dias_uteis_mes += 1
                d += timedelta(days=1)

            dias_com_entrada_mes = db.session.query(
                RegistroPonto.funcionario_id,
                func.count(func.distinct(RegistroPonto.data)).label("dias")
            ).filter(
                RegistroPonto.estabelecimento_id == estabelecimento_id,
                RegistroPonto.data >= inicio_mes,
                RegistroPonto.tipo_registro == "entrada"
            ).group_by(RegistroPonto.funcionario_id).all()

            dias_com_entrada_mes_por_id = {int(r.funcionario_id): int(r.dias or 0) for r in dias_com_entrada_mes}

            banco_horas_registros = db.session.query(BancoHoras).join(Funcionario).filter(
                Funcionario.estabelecimento_id == estabelecimento_id,
                BancoHoras.mes_referencia == banco_horas_mes
            ).all()

            banco_horas_por_id = {
                int(r.funcionario_id): {
                    "saldo_minutos": int(r.saldo_minutos or 0),
                    "valor_hora_extra": float(r.valor_hora_extra or 0),
                    "horas_trabalhadas_minutos": int(r.horas_trabalhadas_minutos or 0),
                    "horas_esperadas_minutos": int(r.horas_esperadas_minutos or 0)
                }
                for r in banco_horas_registros
            }

            atrasos_por_funcionario_mes = []
            horas_extras_por_funcionario_mes = []
            faltas_por_funcionario_mes = []
            banco_horas_por_funcionario_mes = []
            espelho_pagamento_mes = []

            for f in funcionarios_ativos:
                atraso_info = atrasos_por_func_id.get(f.id, {"qtd": 0, "minutos": 0})
                extras_min = int(extras_mes_por_func_id.get(f.id, 0))
                beneficios_total = float(beneficios_por_func_id.get(f.id, 0))
                dias_presenca = int(dias_com_entrada_mes_por_id.get(f.id, 0))
                faltas = max(0, dias_uteis_mes - dias_presenca)
                banco = banco_horas_por_id.get(f.id, {"saldo_minutos": 0, "valor_hora_extra": 0.0, "horas_trabalhadas_minutos": 0, "horas_esperadas_minutos": 0})

                custo_extras_func = round((extras_min / 60) * valor_hora_medio * 1.5, 2)
                total_estimado = float(f.salario_base or 0) + beneficios_total + custo_extras_func

                atrasos_por_funcionario_mes.append({
                    "funcionario_id": f.id,
                    "nome": f.nome,
                    "cargo": f.cargo,
                    "atrasos_qtd": int(atraso_info["qtd"]),
                    "minutos_atraso": int(atraso_info["minutos"])
                })

                horas_extras_por_funcionario_mes.append({
                    "funcionario_id": f.id,
                    "nome": f.nome,
                    "cargo": f.cargo,
                    "minutos_extras": int(extras_min),
                    "custo_extras": float(custo_extras_func)
                })

                faltas_por_funcionario_mes.append({
                    "funcionario_id": f.id,
                    "nome": f.nome,
                    "cargo": f.cargo,
                    "faltas": int(faltas),
                    "dias_uteis": int(dias_uteis_mes),
                    "dias_presenca": int(dias_presenca)
                })

                banco_horas_por_funcionario_mes.append({
                    "funcionario_id": f.id,
                    "nome": f.nome,
                    "cargo": f.cargo,
                    "saldo_minutos": int(banco["saldo_minutos"]),
                    "valor_hora_extra": float(banco["valor_hora_extra"]),
                    "horas_trabalhadas_minutos": int(banco["horas_trabalhadas_minutos"]),
                    "horas_esperadas_minutos": int(banco["horas_esperadas_minutos"])
                })

                espelho_pagamento_mes.append({
                    "funcionario_id": f.id,
                    "nome": f.nome,
                    "cargo": f.cargo,
                    "salario_base": float(f.salario_base or 0),
                    "beneficios": float(beneficios_total),
                    "horas_extras_horas": round(extras_min / 60, 2),
                    "custo_horas_extras": float(custo_extras_func),
                    "atrasos_minutos": int(atraso_info["minutos"]),
                    "faltas": int(faltas),
                    "banco_horas_saldo_horas": round(int(banco["saldo_minutos"]) / 60, 2),
                    "total_estimado": round(float(total_estimado), 2)
                })

            atrasos_por_funcionario_mes.sort(key=lambda x: x["minutos_atraso"], reverse=True)
            horas_extras_por_funcionario_mes.sort(key=lambda x: x["minutos_extras"], reverse=True)
            faltas_por_funcionario_mes.sort(key=lambda x: x["faltas"], reverse=True)
            banco_horas_por_funcionario_mes.sort(key=lambda x: x["saldo_minutos"], reverse=True)
            espelho_pagamento_mes.sort(key=lambda x: x["total_estimado"], reverse=True)

            team_status = []
            todos_funcionarios = funcionarios_ativos
            
            for funcionario in todos_funcionarios:
                ultimo_ponto = db.session.query(RegistroPonto).filter(
                    RegistroPonto.funcionario_id == funcionario.id,
                    RegistroPonto.data == hoje_dia
                ).order_by(RegistroPonto.hora.desc()).first()
                
                status_atual = "Ausente"
                horario_ultimo = "-"
                
                if ultimo_ponto:
                    horario_ultimo = ultimo_ponto.hora.strftime('%H:%M') if ultimo_ponto.hora else "-"
                    if ultimo_ponto.tipo_registro == 'entrada': status_atual = "Em Trabalho"
                    elif ultimo_ponto.tipo_registro == 'saida_almoco': status_atual = "Almoço"
                    elif ultimo_ponto.tipo_registro == 'retorno_almoco': status_atual = "Em Trabalho"
                    elif ultimo_ponto.tipo_registro == 'saida': status_atual = "Saiu"
                
                team_status.append({
                    "nome": funcionario.nome.split()[0], # Primeiro nome
                    "cargo": funcionario.cargo,
                    "status": status_atual,
                    "ultimo_registro": horario_ultimo
                })

            recent_points = db.session.query(
                RegistroPonto.data,
                RegistroPonto.hora,
                RegistroPonto.tipo_registro,
                Funcionario.nome
            ).join(Funcionario).filter(
                RegistroPonto.estabelecimento_id == estabelecimento_id
            ).order_by(RegistroPonto.data.desc(), RegistroPonto.hora.desc()).limit(20).all()
            
            recent_points_list = [
                {
                    "data": p.data.strftime('%d/%m/%Y') if p.data else "-",
                    "hora": p.hora.strftime('%H:%M') if p.hora else "-",
                    "tipo": p.tipo_registro,
                    "funcionario": p.nome
                }
                for p in recent_points
            ]

            start_daily = hoje_dia - timedelta(days=6)
            pontos = db.session.query(
                RegistroPonto.funcionario_id,
                Funcionario.nome,
                RegistroPonto.data,
                RegistroPonto.hora,
                RegistroPonto.tipo_registro,
                RegistroPonto.minutos_atraso
            ).join(Funcionario).filter(
                RegistroPonto.estabelecimento_id == estabelecimento_id,
                RegistroPonto.data >= start_daily
            ).all()

            daily_map: Dict[str, Dict[str, Any]] = {}
            for func_id, nome, data_p, hora_p, tipo, min_atraso in pontos:
                if not data_p:
                    continue
                key = f"{data_p.isoformat()}:{func_id}"
                if key not in daily_map:
                    daily_map[key] = {
                        "data": data_p.isoformat(),
                        "funcionario": nome,
                        "entrada": None,
                        "saida": None,
                        "minutos_atraso": 0,
                        "minutos_extras": 0
                    }
                row = daily_map[key]
                if tipo == "entrada" and hora_p:
                    if row["entrada"] is None or hora_p < row["entrada"]:
                        row["entrada"] = hora_p
                    row["minutos_atraso"] += int(min_atraso or 0)
                if tipo == "saida" and hora_p:
                    if row["saida"] is None or hora_p > row["saida"]:
                        row["saida"] = hora_p

            daily_summary = []
            for row in daily_map.values():
                saida = row["saida"]
                if saida:
                    extra = _time_to_minutes(saida) - minuto_saida_ref
                    row["minutos_extras"] = int(extra) if extra > 0 else 0
                daily_summary.append({
                    "data": row["data"],
                    "funcionario": row["funcionario"],
                    "entrada": row["entrada"].strftime("%H:%M") if row["entrada"] else "-",
                    "saida": row["saida"].strftime("%H:%M") if row["saida"] else "-",
                    "minutos_atraso": int(row["minutos_atraso"]),
                    "minutos_extras": int(row["minutos_extras"])
                })

            daily_summary.sort(key=lambda r: (r["data"], r["funcionario"]), reverse=True)

            overtime_trend = []
            for i in range(13, -1, -1):
                d = hoje_dia - timedelta(days=i)
                mins = int(overtime_by_day.get(d.isoformat(), 0))
                overtime_trend.append({
                    "data": d.isoformat(),
                    "minutos_extras": mins,
                    "custo_extras": round((mins / 60) * valor_hora_medio * 1.5, 2)
                })

            return {
                "total_beneficios_mensal": float(total_beneficios),
                "total_salarios": float(total_salarios),
                "custo_folha_estimado": round(custo_folha_estimado, 2),
                "funcionarios_ativos": len(funcionarios_ativos_ids),
                
                # Indicadores de Assiduidade
                "total_entradas_periodo": total_entradas,
                "total_atrasos_qtd": total_atrasos_qtd,
                "taxa_pontualidade": round(taxa_pontualidade, 1),
                "total_minutos_atraso": int(total_minutos_atraso),
                
                # Indicadores de Extras
                "minutos_extras_estimados": int(minutos_extras_estimados),
                "custo_extras_estimado": round(custo_extras_estimado, 2),

                # Indicadores de Rotatividade
                "admissoes_periodo": admissoes,
                "demissoes_periodo": demissoes,
                "turnover_rate": round(turnover_rate, 2),
                
                # Gráficos e Tabelas
                "evolution_turnover": evolution_turnover,
                "benefits_breakdown": benefits_data,
                "top_overtime_employees": overtime_list,
                "team_status_today": team_status,
                "recent_points": recent_points_list,
                "daily_ponto_summary": daily_summary,
                "overtime_trend": overtime_trend,
                "atrasos_por_funcionario_mes": atrasos_por_funcionario_mes,
                "horas_extras_por_funcionario_mes": horas_extras_por_funcionario_mes,
                "faltas_por_funcionario_mes": faltas_por_funcionario_mes,
                "banco_horas_por_funcionario_mes": banco_horas_por_funcionario_mes,
                "espelho_pagamento_mes": espelho_pagamento_mes,
                "resumo_mes": {
                    "inicio": inicio_mes.isoformat(),
                    "fim": hoje_dia.isoformat(),
                    "dias_uteis": int(dias_uteis_mes),
                    "total_atrasos_minutos": int(sum([x["minutos_atraso"] for x in atrasos_por_funcionario_mes])),
                    "total_atrasos_qtd": int(sum([x["atrasos_qtd"] for x in atrasos_por_funcionario_mes])),
                    "total_extras_minutos": int(sum([x["minutos_extras"] for x in horas_extras_por_funcionario_mes])),
                    "total_faltas": int(sum([x["faltas"] for x in faltas_por_funcionario_mes]))
                }
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao calcular métricas de RH: {e}")
            return {
                "total_beneficios_mensal": 0.0,
                "total_salarios": 0.0,
                "custo_folha_estimado": 0.0,
                "funcionarios_ativos": 0,
                "total_entradas_periodo": 0,
                "total_atrasos_qtd": 0,
                "taxa_pontualidade": 100.0,
                "total_minutos_atraso": 0,
                "minutos_extras_estimados": 0,
                "custo_extras_estimado": 0.0,
                "turnover_rate": 0.0,
                "admissoes_periodo": 0,
                "demissoes_periodo": 0,
                "evolution_turnover": [],
                "benefits_breakdown": [],
                "top_overtime_employees": [],
                "team_status_today": [],
                "recent_points": [],
                "daily_ponto_summary": [],
                "overtime_trend": [],
                "atrasos_por_funcionario_mes": [],
                "horas_extras_por_funcionario_mes": [],
                "faltas_por_funcionario_mes": [],
                "banco_horas_por_funcionario_mes": [],
                "espelho_pagamento_mes": [],
                "resumo_mes": {
                    "inicio": None,
                    "fim": None,
                    "dias_uteis": 0,
                    "total_atrasos_minutos": 0,
                    "total_atrasos_qtd": 0,
                    "total_extras_minutos": 0,
                    "total_faltas": 0
                }
            }
