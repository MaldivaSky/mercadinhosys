from flask import Blueprint, request, jsonify, send_file
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
from app import db
from app.models import Venda, Produto, Cliente

relatorios_bp = Blueprint("relatorios", __name__)


@relatorios_bp.route("/vendas/periodo", methods=["GET"])
def relatorio_vendas_periodo():
    """Gera relatório de vendas por período"""
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    formato = request.args.get("formato", "json")  # json, excel, pdf

    # Converter datas
    data_inicio = (
        datetime.fromisoformat(data_inicio)
        if data_inicio
        else datetime.now() - timedelta(days=30)
    )
    data_fim = datetime.fromisoformat(data_fim) if data_fim else datetime.now()

    # Consulta otimizada
    vendas = Venda.query.filter(
        Venda.created_at >= data_inicio, Venda.created_at <= data_fim
    ).all()

    if formato == "excel":
        # Criar DataFrame
        dados = []
        for v in vendas:
            dados.append(
                {
                    "Data": v.created_at.strftime("%d/%m/%Y %H:%M"),
                    "Código": v.codigo,
                    "Cliente": v.cliente.nome if v.cliente else "Consumidor Final",
                    "Subtotal": v.subtotal,
                    "Desconto": v.desconto,
                    "Total": v.total,
                    "Pagamento": v.forma_pagamento,
                    "Itens": len(v.itens),
                }
            )

        df = pd.DataFrame(dados)

        # Criar Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Vendas", index=False)

            # Adicionar resumo
            resumo = pd.DataFrame(
                [
                    {
                        "Total Vendas": df["Total"].sum(),
                        "Média por Venda": df["Total"].mean(),
                        "Total Descontos": df["Desconto"].sum(),
                        "Quantidade de Vendas": len(df),
                    }
                ]
            )
            resumo.to_excel(writer, sheet_name="Resumo", index=False)

        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"relatorio_vendas_{data_inicio.date()}_a_{data_fim.date()}.xlsx",
        )

    # Retornar JSON por padrão
    return jsonify(
        {
            "periodo": {"inicio": data_inicio.isoformat(), "fim": data_fim.isoformat()},
            "total_vendas": sum(v.total for v in vendas),
            "quantidade_vendas": len(vendas),
            "ticket_medio": sum(v.total for v in vendas) / len(vendas) if vendas else 0,
            "vendas": [v.to_dict() for v in vendas],
        }
    )
