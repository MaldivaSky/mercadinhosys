# app/routes/dashboard.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (
    DashboardMetrica,
    Venda,
    Produto,
    Cliente,
    Funcionario,
    MovimentacaoEstoque,
    Estabelecimento,
)
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract
from app.decorator import funcionario_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/resumo", methods=["GET"])
@funcionario_required
def resumo_dashboard():
    current_user = get_jwt_identity()

    if not current_user.get('is_admin'):    
        return jsonify({"error": "Acesso negado"}), 403
    """Retorna resumo completo para o dashboard"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        hoje = date.today()

        # Verificar se já temos métricas calculadas para hoje
        metrica = DashboardMetrica.query.filter_by(
            estabelecimento_id=estabelecimento_id, data_referencia=hoje
        ).first()

        if not metrica:
            # Calcular métricas na hora (pode ser lento, ideal é ter job agendado)
            metrica = calcular_metricas_hoje(estabelecimento_id, hoje)

        # Dados adicionais em tempo real
        vendas_hoje = Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id,
            func.date(Venda.data_venda) == hoje,
            Venda.status == "finalizada",
        ).all()

        # Produtos com estoque baixo
        produtos_estoque_baixo = (
            Produto.query.filter(
                Produto.estabelecimento_id == estabelecimento_id,
                Produto.quantidade <= Produto.quantidade_minima,
                Produto.ativo == True,
            )
            .limit(10)
            .all()
        )

        # Produtos próximos da validade
        dias_alerta = 15  # Buscar da configuração depois
        data_alerta = hoje + timedelta(days=dias_alerta)

        produtos_validade_proxima = (
            Produto.query.filter(
                Produto.estabelecimento_id == estabelecimento_id,
                Produto.data_validade.between(hoje, data_alerta),
                Produto.quantidade > 0,
                Produto.ativo == True,
            )
            .order_by(Produto.data_validade)
            .limit(10)
            .all()
        )

        # Vendas por hora (últimas 24 horas)
        hora_inicio = datetime.now() - timedelta(hours=24)

        vendas_por_hora = (
            db.session.query(
                extract("hour", Venda.data_venda).label("hora"),
                func.count(Venda.id).label("quantidade"),
                func.sum(Venda.total).label("total"),
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= hora_inicio,
                Venda.status == "finalizada",
            )
            .group_by(extract("hour", Venda.data_venda))
            .order_by("hora")
            .all()
        )

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "hoje": {
                            "data": hoje.isoformat(),
                            "total_vendas": metrica.total_vendas_dia,
                            "quantidade_vendas": metrica.quantidade_vendas_dia,
                            "ticket_medio": metrica.ticket_medio_dia,
                            "clientes_atendidos": metrica.clientes_atendidos_dia,
                        },
                        "mes": {
                            "total_vendas": metrica.total_vendas_mes,
                            "total_despesas": metrica.total_despesas_mes,
                            "lucro_bruto": metrica.lucro_bruto_mes,
                        },
                        "alertas": {
                            "estoque_baixo": [
                                {
                                    "id": p.id,
                                    "nome": p.nome,
                                    "quantidade": p.quantidade,
                                    "quantidade_minima": p.quantidade_minima,
                                    "localizacao": p.localizacao,
                                }
                                for p in produtos_estoque_baixo
                            ],
                            "validade_proxima": [
                                {
                                    "id": p.id,
                                    "nome": p.nome,
                                    "data_validade": (
                                        p.data_validade.isoformat()
                                        if p.data_validade
                                        else None
                                    ),
                                    "dias_restantes": (
                                        (p.data_validade - hoje).days
                                        if p.data_validade
                                        else None
                                    ),
                                    "quantidade": p.quantidade,
                                    "lote": p.lote,
                                }
                                for p in produtos_validade_proxima
                            ],
                        },
                        "vendas_por_hora": [
                            {
                                "hora": int(vph.hora),
                                "quantidade": vph.quantidade,
                                "total": float(vph.total) if vph.total else 0,
                            }
                            for vph in vendas_por_hora
                        ],
                        "ultimas_vendas": [
                            {
                                "id": v.id,
                                "codigo": v.codigo,
                                "cliente": (
                                    v.cliente.nome if v.cliente else "Consumidor Final"
                                ),
                                "total": v.total,
                                "forma_pagamento": v.forma_pagamento,
                                "hora": v.data_venda.strftime("%H:%M"),
                            }
                            for v in vendas_hoje[:5]  # Últimas 5 vendas
                        ],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar resumo do dashboard: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar resumo do dashboard",
                    "message": str(e),
                }
            ),
            500,
        )


def calcular_metricas_hoje(estabelecimento_id, data_referencia):
    """Calcula métricas do dashboard para um dia específico"""
    try:
        # Início e fim do dia
        inicio_dia = datetime.combine(data_referencia, datetime.min.time())
        fim_dia = datetime.combine(data_referencia, datetime.max.time())

        # Início do mês
        inicio_mes = datetime(data_referencia.year, data_referencia.month, 1)

        # Vendas do dia
        vendas_dia = Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_dia,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada",
        ).all()

        total_vendas_dia = sum(v.total for v in vendas_dia)
        quantidade_vendas_dia = len(vendas_dia)
        ticket_medio_dia = (
            total_vendas_dia / quantidade_vendas_dia if quantidade_vendas_dia > 0 else 0
        )

        # Clientes atendidos no dia
        clientes_atendidos_dia = len(
            set(v.cliente_id for v in vendas_dia if v.cliente_id)
        )

        # Vendas do mês (até a data de referência)
        vendas_mes = Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada",
        ).all()

        total_vendas_mes = sum(v.total for v in vendas_mes)

        # TODO: Calcular despesas do mês (precisa de tabela de despesas)
        total_despesas_mes = 0
        lucro_bruto_mes = total_vendas_mes - total_despesas_mes

        # Top produtos do dia
        from app.models import VendaItem

        top_produtos = (
            db.session.query(
                VendaItem.produto_id,
                VendaItem.produto_nome,
                func.sum(VendaItem.quantidade).label("quantidade_total"),
                func.sum(VendaItem.total_item).label("total_vendido"),
            )
            .join(Venda)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= inicio_dia,
                Venda.data_venda <= fim_dia,
                Venda.status == "finalizada",
            )
            .group_by(VendaItem.produto_id, VendaItem.produto_nome)
            .order_by(func.sum(VendaItem.quantidade).desc())
            .limit(5)
            .all()
        )

        top_produtos_json = [
            {
                "produto_id": tp.produto_id,
                "nome": tp.produto_nome,
                "quantidade_total": int(tp.quantidade_total),
                "total_vendido": float(tp.total_vendido) if tp.total_vendido else 0,
            }
            for tp in top_produtos
        ]

        # Buscar ou criar métrica
        metrica = DashboardMetrica.query.filter_by(
            estabelecimento_id=estabelecimento_id, data_referencia=data_referencia
        ).first()

        if not metrica:
            metrica = DashboardMetrica(
                estabelecimento_id=estabelecimento_id, data_referencia=data_referencia
            )

        # Atualizar métricas
        metrica.total_vendas_dia = total_vendas_dia
        metrica.quantidade_vendas_dia = quantidade_vendas_dia
        metrica.ticket_medio_dia = ticket_medio_dia
        metrica.clientes_atendidos_dia = clientes_atendidos_dia
        metrica.total_vendas_mes = total_vendas_mes
        metrica.total_despesas_mes = total_despesas_mes
        metrica.lucro_bruto_mes = lucro_bruto_mes
        metrica.top_produtos_json = top_produtos_json

        db.session.add(metrica)
        db.session.commit()

        return metrica

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao calcular métricas: {str(e)}")
        raise


@dashboard_bp.route("/vendas-periodo", methods=["GET"])
def vendas_por_periodo():
    """Retorna vendas agregadas por período para gráficos"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        periodo = request.args.get("periodo", "dia")  # dia, semana, mes, ano
        dias = int(request.args.get("dias", 7))

        hoje = date.today()
        data_inicio = hoje - timedelta(days=dias - 1)

        resultados = []

        if periodo == "dia":
            # Agrupar por dia
            for i in range(dias):
                data_atual = data_inicio + timedelta(days=i)
                inicio_dia = datetime.combine(data_atual, datetime.min.time())
                fim_dia = datetime.combine(data_atual, datetime.max.time())

                vendas_dia = Venda.query.filter(
                    Venda.estabelecimento_id == estabelecimento_id,
                    Venda.data_venda >= inicio_dia,
                    Venda.data_venda <= fim_dia,
                    Venda.status == "finalizada",
                ).all()

                total_dia = sum(v.total for v in vendas_dia)
                quantidade_dia = len(vendas_dia)

                resultados.append(
                    {
                        "data": data_atual.isoformat(),
                        "total": total_dia,
                        "quantidade": quantidade_dia,
                        "ticket_medio": (
                            total_dia / quantidade_dia if quantidade_dia > 0 else 0
                        ),
                    }
                )

        elif periodo == "hora":
            # Últimas 24 horas por hora
            hora_inicio = datetime.now() - timedelta(hours=24)

            vendas_por_hora = (
                db.session.query(
                    extract("hour", Venda.data_venda).label("hora"),
                    func.count(Venda.id).label("quantidade"),
                    func.sum(Venda.total).label("total"),
                )
                .filter(
                    Venda.estabelecimento_id == estabelecimento_id,
                    Venda.data_venda >= hora_inicio,
                    Venda.status == "finalizada",
                )
                .group_by(extract("hour", Venda.data_venda))
                .order_by("hora")
                .all()
            )

            for vph in vendas_por_hora:
                resultados.append(
                    {
                        "hora": int(vph.hora),
                        "total": float(vph.total) if vph.total else 0,
                        "quantidade": vph.quantidade,
                    }
                )

        return (
            jsonify(
                {"success": True, "periodo": periodo, "dias": dias, "data": resultados}
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao obter vendas por período: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao obter vendas por período",
                    "message": str(e),
                }
            ),
            500,
        )
