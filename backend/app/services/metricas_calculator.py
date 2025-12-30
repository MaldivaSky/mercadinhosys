import schedule
import time
from datetime import datetime, timedelta
from app import db
from app.models import DashboardMetrica, Venda, Produto


def calcular_metricas_diarias():
    """Job que roda diariamente para calcular métricas do dashboard"""
    hoje = datetime.now().date()

    # Buscar todos os estabelecimentos
    estabelecimentos = Estabelecimento.query.all()

    for estab in estabelecimentos:
        # Calcular vendas do dia
        total_vendas = (
            db.session.query(db.func.sum(Venda.total))
            .filter(
                Venda.estabelecimento_id == estab.id,
                db.func.date(Venda.created_at) == hoje,
            )
            .scalar()
            or 0
        )

        # Calcular quantidade de vendas
        qtd_vendas = Venda.query.filter(
            Venda.estabelecimento_id == estab.id, db.func.date(Venda.created_at) == hoje
        ).count()

        # Buscar ou criar métrica
        metrica = DashboardMetrica.query.filter_by(
            estabelecimento_id=estab.id, data_referencia=hoje
        ).first()

        if not metrica:
            metrica = DashboardMetrica(
                estabelecimento_id=estab.id, data_referencia=hoje
            )

        metrica.total_vendas_dia = total_vendas
        metrica.quantidade_vendas_dia = qtd_vendas
        metrica.ticket_medio_dia = total_vendas / qtd_vendas if qtd_vendas > 0 else 0

        # Calcular produtos próximos da validade
        dias_alerta = (
            estab.configuracoes.dias_alerta_validade if estab.configuracoes else 15
        )
        data_alerta = hoje + timedelta(days=dias_alerta)

        produtos_validade = (
            Produto.query.filter(
                Produto.estabelecimento_id == estab.id,
                Produto.data_validade <= data_alerta,
                Produto.data_validade >= hoje,
            )
            .limit(5)
            .all()
        )

        metrica.produtos_validade_json = [
            {
                "id": p.id,
                "nome": p.nome,
                "validade": p.data_validade.isoformat(),
                "dias_restantes": (p.data_validade - hoje).days,
                "quantidade": p.quantidade,
            }
            for p in produtos_validade
        ]

        db.session.add(metrica)

    db.session.commit()
    print(f"✅ Métricas calculadas para {len(estabelecimentos)} estabelecimentos")


# Agendar job para rodar todo dia às 23:59
schedule.every().day.at("23:59").do(calcular_metricas_diarias)
