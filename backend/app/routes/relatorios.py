from flask import Blueprint, request, jsonify, send_file, current_app
from app import db
from app.models import (
    Venda,
    Produto,
    Cliente,
    Funcionario,
    MovimentacaoEstoque,
    Configuracao,
)
from datetime import datetime, timedelta, date
import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from sqlalchemy import func, extract
from utils.decorator import funcionario_required, admin_required, gerente_ou_admin_required

matplotlib.use("Agg")  # Para não precisar de display GUI

relatorios_bp = Blueprint("relatorios", __name__)


@relatorios_bp.route("/vendas", methods=["GET"])
@gerente_ou_admin_required
def relatorio_vendas():
    """Gera relatório de vendas por período"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        formato = request.args.get("formato", "json")  # json, excel, pdf, csv
        agrupar_por = request.args.get(
            "agrupar_por", "dia"
        )  # dia, semana, mes, produto, funcionario

        # Converter datas
        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio.replace("Z", "+00:00"))
        else:
            data_inicio = datetime.now() - timedelta(days=30)

        if data_fim:
            data_fim = datetime.fromisoformat(data_fim.replace("Z", "+00:00"))
        else:
            data_fim = datetime.now()

        # Validar datas
        if data_fim < data_inicio:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Data final não pode ser anterior à data inicial",
                    }
                ),
                400,
            )

        # Buscar configurações
        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()

        if formato == "excel":
            return gerar_excel_vendas(
                estabelecimento_id, data_inicio, data_fim, agrupar_por
            )
        elif formato == "pdf":
            return gerar_pdf_vendas(
                estabelecimento_id, data_inicio, data_fim, agrupar_por, config
            )
        elif formato == "csv":
            return gerar_csv_vendas(estabelecimento_id, data_inicio, data_fim)
        else:
            # JSON padrão com opção de agrupamento
            return gerar_json_vendas(
                estabelecimento_id, data_inicio, data_fim, agrupar_por
            )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório de vendas: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar relatório de vendas",
                    "message": str(e),
                }
            ),
            500,
        )


def gerar_json_vendas(estabelecimento_id, data_inicio, data_fim, agrupar_por):
    """Gera relatório de vendas em formato JSON com diferentes agrupamentos"""
    # Buscar vendas
    vendas = (
        Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= data_inicio,
            Venda.data_venda <= data_fim,
            Venda.status == "finalizada",
        )
        .options(
            db.joinedload(Venda.cliente),
            db.joinedload(Venda.funcionario),
            db.joinedload(Venda.itens),
        )
        .order_by(Venda.data_venda)
        .all()
    )

    total_vendas = sum(v.total for v in vendas)
    quantidade_vendas = len(vendas)
    ticket_medio = total_vendas / quantidade_vendas if quantidade_vendas > 0 else 0

    resultado = {
        "success": True,
        "periodo": {"inicio": data_inicio.isoformat(), "fim": data_fim.isoformat()},
        "total_vendas": total_vendas,
        "quantidade_vendas": quantidade_vendas,
        "ticket_medio": ticket_medio,
        "vendas": [v.to_dict() for v in vendas],
    }

    # Adicionar agrupamentos se solicitado
    if agrupar_por == "dia":
        resultado["agrupado_por_dia"] = agrupar_vendas_por_dia(vendas)
    elif agrupar_por == "produto":
        resultado["agrupado_por_produto"] = agrupar_vendas_por_produto(vendas)
    elif agrupar_por == "funcionario":
        resultado["agrupado_por_funcionario"] = agrupar_vendas_por_funcionario(vendas)

    return jsonify(resultado), 200

@gerente_ou_admin_required
def agrupar_vendas_por_dia(vendas):
    """Agrupa vendas por dia"""
    from collections import defaultdict

    agrupado = defaultdict(lambda: {"total": 0, "quantidade": 0, "vendas": []})

    for venda in vendas:
        data = venda.data_venda.date()
        agrupado[data]["total"] += venda.total
        agrupado[data]["quantidade"] += 1
        agrupado[data]["vendas"].append(venda.id)

    return [{"data": str(data), **dados} for data, dados in sorted(agrupado.items())]

@gerente_ou_admin_required
def agrupar_vendas_por_produto(vendas):
    """Agrupa vendas por produto"""
    from collections import defaultdict

    produtos = defaultdict(lambda: {"quantidade": 0, "total": 0, "nome": ""})

    for venda in vendas:
        for item in venda.itens:
            produtos[item.produto_id]["quantidade"] += item.quantidade
            produtos[item.produto_id]["total"] += item.total_item
            produtos[item.produto_id]["nome"] = item.produto_nome

    return [{"produto_id": pid, **dados} for pid, dados in produtos.items()]

@gerente_ou_admin_required
def agrupar_vendas_por_funcionario(vendas):
    """Agrupa vendas por funcionário"""
    from collections import defaultdict

    funcionarios = defaultdict(
        lambda: {"total": 0, "quantidade": 0, "nome": "", "vendas": []}
    )

    for venda in vendas:
        if venda.funcionario:
            fid = venda.funcionario.id
            funcionarios[fid]["total"] += venda.total
            funcionarios[fid]["quantidade"] += 1
            funcionarios[fid]["nome"] = venda.funcionario.nome
            funcionarios[fid]["vendas"].append(venda.id)

    return [{"funcionario_id": fid, **dados} for fid, dados in funcionarios.items()]


def gerar_excel_vendas(estabelecimento_id, data_inicio, data_fim, agrupar_por):
    """Gera relatório de vendas em formato Excel"""
    try:
        # Buscar vendas
        vendas = (
            Venda.query.filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.data_venda <= data_fim,
                Venda.status == "finalizada",
            )
            .options(db.joinedload(Venda.cliente), db.joinedload(Venda.funcionario))
            .order_by(Venda.data_venda)
            .all()
        )

        # Criar DataFrame
        dados = []
        for v in vendas:
            dados.append(
                {
                    "Data": v.data_venda.strftime("%d/%m/%Y %H:%M"),
                    "Código": v.codigo,
                    "Cliente": v.cliente.nome if v.cliente else "Consumidor Final",
                    "Funcionário": v.funcionario.nome if v.funcionario else "",
                    "Subtotal": v.subtotal,
                    "Desconto": v.desconto,
                    "Total": v.total,
                    "Pagamento": v.forma_pagamento,
                    "Itens": len(v.itens),
                    "Observações": v.observacoes or "",
                }
            )

        df = pd.DataFrame(dados)

        # Criar Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Dados das vendas
            df.to_excel(writer, sheet_name="Vendas", index=False)

            # Formatar a planilha
            worksheet = writer.sheets["Vendas"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Resumo
            resumo_data = []
            if not df.empty:
                # Formas de pagamento
                pagamentos = (
                    df.groupby("Pagamento")
                    .agg({"Total": "sum", "Código": "count"})
                    .rename(columns={"Total": "Valor Total", "Código": "Quantidade"})
                )

                # Vendas por dia
                df["Data_Dia"] = pd.to_datetime(
                    df["Data"], format="%d/%m/%Y %H:%M"
                ).dt.date
                vendas_por_dia = (
                    df.groupby("Data_Dia")
                    .agg({"Total": "sum", "Código": "count"})
                    .rename(columns={"Total": "Valor Total", "Código": "Quantidade"})
                )

                # Top 10 produtos (precisa dos itens)
                itens_todos = []
                for v in vendas:
                    for item in v.itens:
                        itens_todos.append(
                            {
                                "Produto": item.produto_nome,
                                "Quantidade": item.quantidade,
                                "Total": item.total_item,
                            }
                        )

                if itens_todos:
                    df_itens = pd.DataFrame(itens_todos)
                    top_produtos = (
                        df_itens.groupby("Produto")
                        .agg({"Quantidade": "sum", "Total": "sum"})
                        .sort_values("Quantidade", ascending=False)
                        .head(10)
                    )

                # Criar planilha de resumo
                resumo = pd.DataFrame(
                    [
                        {
                            "Total Vendas": df["Total"].sum() if not df.empty else 0,
                            "Quantidade Vendas": len(df),
                            "Ticket Médio": df["Total"].mean() if not df.empty else 0,
                            "Total Descontos": (
                                df["Desconto"].sum() if not df.empty else 0
                            ),
                            "Período Início": data_inicio.strftime("%d/%m/%Y"),
                            "Período Fim": data_fim.strftime("%d/%m/%Y"),
                        }
                    ]
                )
                resumo.to_excel(writer, sheet_name="Resumo", index=False)

                # Planilha de formas de pagamento
                if not pagamentos.empty:
                    pagamentos.to_excel(writer, sheet_name="Pagamentos")

                # Planilha de vendas por dia
                if not vendas_por_dia.empty:
                    vendas_por_dia.to_excel(writer, sheet_name="Vendas por Dia")

                # Planilha de top produtos
                if itens_todos:
                    top_produtos.to_excel(writer, sheet_name="Top Produtos")

            # Se DataFrame vazio, criar resumo básico
            else:
                resumo = pd.DataFrame(
                    [
                        {
                            "Total Vendas": 0,
                            "Quantidade Vendas": 0,
                            "Ticket Médio": 0,
                            "Total Descontos": 0,
                            "Período Início": data_inicio.strftime("%d/%m/%Y"),
                            "Período Fim": data_fim.strftime("%d/%m/%Y"),
                            "Mensagem": "Nenhuma venda encontrada no período",
                        }
                    ]
                )
                resumo.to_excel(writer, sheet_name="Resumo", index=False)

        output.seek(0)

        nome_arquivo = f"relatorio_vendas_{data_inicio.date()}_a_{data_fim.date()}.xlsx"

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar Excel de vendas: {str(e)}")
        raise


def gerar_pdf_vendas(estabelecimento_id, data_inicio, data_fim, agrupar_por, config):
    """Gera relatório de vendas em formato PDF"""
    try:
        # Buscar vendas
        vendas = (
            Venda.query.filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.data_venda <= data_fim,
                Venda.status == "finalizada",
            )
            .options(
                db.joinedload(Venda.cliente),
                db.joinedload(Venda.funcionario),
                db.joinedload(Venda.itens),
            )
            .order_by(Venda.data_venda.desc())
            .limit(100)
            .all()
        )  # Limitar a 100 vendas no PDF

        # Buscar estabelecimento para cabeçalho
        from app.models import Estabelecimento

        estabelecimento = Estabelecimento.query.get(estabelecimento_id)

        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        elements = []
        styles = getSampleStyleSheet()

        # Estilos customizados
        styles.add(ParagraphStyle(name="Center", alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="Left", alignment=TA_LEFT))
        styles.add(
            ParagraphStyle(name="Right", alignment=TA_LEFT)
        )  # ReportLab usa 2 para direita

        # Cabeçalho
        if estabelecimento:
            elements.append(
                Paragraph(f"<b>{estabelecimento.nome}</b>", styles["Title"])
            )
            elements.append(
                Paragraph(f"CNPJ: {estabelecimento.cnpj}", styles["Normal"])
            )
            if estabelecimento.endereco:
                elements.append(
                    Paragraph(
                        f"{estabelecimento.endereco}, {estabelecimento.cidade}-{estabelecimento.estado}",
                        styles["Normal"],
                    )
                )

        elements.append(Spacer(1, 20))

        # Título do relatório
        elements.append(Paragraph("<b>RELATÓRIO DE VENDAS</b>", styles["Title"]))
        elements.append(
            Paragraph(
                f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(
                f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 20))

        # Resumo estatístico
        total_vendas = sum(v.total for v in vendas)
        quantidade_vendas = len(vendas)
        ticket_medio = total_vendas / quantidade_vendas if quantidade_vendas > 0 else 0
        total_descontos = sum(v.desconto for v in vendas)

        # Formas de pagamento
        formas_pagamento = {}
        for v in vendas:
            forma = v.forma_pagamento
            if forma not in formas_pagamento:
                formas_pagamento[forma] = {"total": 0, "quantidade": 0}
            formas_pagamento[forma]["total"] += v.total
            formas_pagamento[forma]["quantidade"] += 1

        # Tabela de resumo
        resumo_data = [
            ["DESCRIÇÃO", "VALOR"],
            ["Total de Vendas:", f"R$ {total_vendas:,.2f}"],
            ["Quantidade de Vendas:", str(quantidade_vendas)],
            ["Ticket Médio:", f"R$ {ticket_medio:,.2f}"],
            ["Total de Descontos:", f"R$ {total_descontos:,.2f}"],
            ["", ""],
            ["PERÍODO DO RELATÓRIO", ""],
            ["Data Início:", data_inicio.strftime("%d/%m/%Y")],
            ["Data Fim:", data_fim.strftime("%d/%m/%Y")],
        ]

        resumo_table = Table(resumo_data, colWidths=[250, 100])
        resumo_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(config.cor_principal if config else "#4F46E5"),
                    ),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ]
            )
        )

        elements.append(resumo_table)
        elements.append(Spacer(1, 20))

        # Formas de pagamento
        if formas_pagamento:
            elements.append(Paragraph("<b>FORMA DE PAGAMENTO</b>", styles["Heading2"]))
            pagamento_data = [["FORMA DE PAGAMENTO", "QUANTIDADE", "VALOR TOTAL", "%"]]

            for forma, dados in formas_pagamento.items():
                percentual = (
                    (dados["total"] / total_vendas * 100) if total_vendas > 0 else 0
                )
                pagamento_data.append(
                    [
                        forma.title(),
                        str(dados["quantidade"]),
                        f"R$ {dados['total']:,.2f}",
                        f"{percentual:.1f}%",
                    ]
                )

            pagamento_table = Table(pagamento_data, colWidths=[150, 80, 100, 60])
            pagamento_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ]
                )
            )

            elements.append(pagamento_table)
            elements.append(Spacer(1, 20))

        # Lista de vendas (limitada)
        if vendas:
            elements.append(Paragraph("<b>ÚLTIMAS VENDAS</b>", styles["Heading2"]))

            # Limitar a 20 vendas para o PDF
            vendas_exibir = vendas[:20]

            vendas_data = [
                ["DATA/HORA", "CÓDIGO", "CLIENTE", "ITENS", "TOTAL", "PAGAMENTO"]
            ]

            for v in vendas_exibir:
                vendas_data.append(
                    [
                        v.data_venda.strftime("%d/%m/%Y %H:%M"),
                        v.codigo,
                        (
                            v.cliente.nome[:20] + "..."
                            if v.cliente and len(v.cliente.nome) > 20
                            else (v.cliente.nome if v.cliente else "Consumidor Final")
                        ),
                        str(len(v.itens)),
                        f"R$ {v.total:,.2f}",
                        v.forma_pagamento[:15],
                    ]
                )

            vendas_table = Table(vendas_data, colWidths=[80, 70, 100, 40, 60, 70])
            vendas_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.aliceblue],
                        ),
                    ]
                )
            )

            elements.append(vendas_table)

            if len(vendas) > 20:
                elements.append(Spacer(1, 10))
                elements.append(
                    Paragraph(
                        f"* Mostrando 20 de {len(vendas)} vendas. Para ver todas, exporte para Excel.",
                        ParagraphStyle(
                            name="SmallItalic", fontSize=8, fontName="Helvetica-Oblique"
                        ),
                    )
                )

        else:
            elements.append(
                Paragraph(
                    "<b>NENHUMA VENDA ENCONTRADA NO PERÍODO</b>", styles["Heading2"]
                )
            )

        elements.append(Spacer(1, 20))

        # Rodapé
        elements.append(
            Paragraph(
                f"Relatório gerado automaticamente pelo Sistema MercadoSys em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                ParagraphStyle(name="Footer", fontSize=8, fontName="Helvetica"),
            )
        )

        doc.build(elements)
        buffer.seek(0)

        nome_arquivo = f"relatorio_vendas_{data_inicio.date()}_a_{data_fim.date()}.pdf"

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar PDF de vendas: {str(e)}")
        raise


def gerar_csv_vendas(estabelecimento_id, data_inicio, data_fim):
    """Gera relatório de vendas em formato CSV"""
    try:
        # Buscar vendas
        vendas = (
            Venda.query.filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.data_venda <= data_fim,
                Venda.status == "finalizada",
            )
            .options(db.joinedload(Venda.cliente), db.joinedload(Venda.funcionario))
            .order_by(Venda.data_venda)
            .all()
        )

        # Criar CSV
        import csv

        output = io.StringIO()
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        # Cabeçalho
        writer.writerow(
            [
                "DATA",
                "CÓDIGO",
                "CLIENTE",
                "FUNCIONÁRIO",
                "SUBTOTAL",
                "DESCONTO",
                "TOTAL",
                "FORMA PAGAMENTO",
                "ITENS",
                "OBSERVAÇÕES",
            ]
        )

        # Dados
        for v in vendas:
            writer.writerow(
                [
                    v.data_venda.strftime("%d/%m/%Y %H:%M"),
                    v.codigo,
                    v.cliente.nome if v.cliente else "Consumidor Final",
                    v.funcionario.nome if v.funcionario else "",
                    f"{v.subtotal:.2f}",
                    f"{v.desconto:.2f}",
                    f"{v.total:.2f}",
                    v.forma_pagamento,
                    len(v.itens),
                    v.observacoes or "",
                ]
            )

        # Converter para bytes
        output_bytes = io.BytesIO(output.getvalue().encode("utf-8"))
        output_bytes.seek(0)

        nome_arquivo = f"relatorio_vendas_{data_inicio.date()}_a_{data_fim.date()}.csv"

        return send_file(
            output_bytes,
            mimetype="text/csv",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar CSV de vendas: {str(e)}")
        raise


@relatorios_bp.route("/estoque", methods=["GET"])
@gerente_ou_admin_required
def relatorio_estoque():
    """Gera relatório de estoque"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        tipo = request.args.get(
            "tipo", "geral"
        )  # geral, validade, minimo, inativos, custo
        formato = request.args.get("formato", "json")
        categoria = request.args.get("categoria")
        ordenar_por = request.args.get(
            "ordenar_por", "nome"
        )  # nome, quantidade, validade, custo, venda

        query = Produto.query.filter_by(estabelecimento_id=estabelecimento_id)

        if tipo == "validade":
            # Produtos próximos da validade
            dias = int(request.args.get("dias", 15))
            data_alerta = date.today() + timedelta(days=dias)

            query = query.filter(
                Produto.data_validade <= data_alerta,
                Produto.data_validade >= date.today(),
                Produto.quantidade > 0,
            )

        elif tipo == "minimo":
            # Produtos com estoque abaixo do mínimo
            query = query.filter(
                Produto.quantidade <= Produto.quantidade_minima, Produto.ativo == True
            )

        elif tipo == "inativos":
            # Produtos inativos
            query = query.filter(Produto.ativo == False)

        elif tipo == "custo":
            # Produtos por valor de custo
            min_custo = request.args.get("min_custo", type=float)
            max_custo = request.args.get("max_custo", type=float)

            if min_custo:
                query = query.filter(Produto.preco_custo >= min_custo)
            if max_custo:
                query = query.filter(Produto.preco_custo <= max_custo)
            query = query.filter(Produto.ativo == True)

        else:  # geral
            query = query.filter(Produto.ativo == True)

        # Filtrar por categoria
        if categoria:
            query = query.filter(Produto.categoria == categoria)

        # Ordenação
        if ordenar_por == "nome":
            query = query.order_by(Produto.nome)
        elif ordenar_por == "quantidade":
            query = query.order_by(Produto.quantidade)
        elif ordenar_por == "validade":
            query = query.order_by(Produto.data_validade.asc())
        elif ordenar_por == "custo":
            query = query.order_by(Produto.preco_custo.desc())
        elif ordenar_por == "venda":
            query = query.order_by(Produto.preco_venda.desc())
        else:
            query = query.order_by(Produto.nome)

        produtos = query.all()

        if formato == "excel":
            return gerar_excel_estoque(produtos, tipo, estabelecimento_id)
        elif formato == "pdf":
            return gerar_pdf_estoque(produtos, tipo, estabelecimento_id)
        elif formato == "csv":
            return gerar_csv_estoque(produtos, tipo)
        else:
            # JSON padrão
            valor_total_estoque = sum(p.quantidade * p.preco_custo for p in produtos)
            valor_total_venda = sum(p.quantidade * p.preco_venda for p in produtos)
            produtos_abaixo_minimo = sum(
                1 for p in produtos if p.quantidade <= p.quantidade_minima
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "tipo": tipo,
                        "quantidade_produtos": len(produtos),
                        "valor_total_custo": valor_total_estoque,
                        "valor_total_venda": valor_total_venda,
                        "lucro_potencial": valor_total_venda - valor_total_estoque,
                        "produtos_abaixo_minimo": produtos_abaixo_minimo,
                        "produtos": [p.to_dict() for p in produtos],
                    }
                ),
                200,
            )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório de estoque: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar relatório de estoque",
                    "message": str(e),
                }
            ),
            500,
        )


def gerar_excel_estoque(produtos, tipo, estabelecimento_id):
    """Gera relatório de estoque em Excel"""
    try:
        dados = []
        for p in produtos:
            # Calcular dias para validade
            dias_validade = None
            if p.data_validade:
                dias_validade = (p.data_validade - date.today()).days

            # Status do estoque
            status_estoque = "NORMAL"
            if p.quantidade <= 0:
                status_estoque = "ESGOTADO"
            elif p.quantidade <= p.quantidade_minima:
                status_estoque = "BAIXO"
            elif dias_validade is not None and dias_validade <= 15:
                status_estoque = "VALIDADE PRÓXIMA"

            dados.append(
                {
                    "Código": p.codigo_barras or "",
                    "Nome": p.nome,
                    "Categoria": p.categoria or "",
                    "Quantidade": p.quantidade,
                    "Mínimo": p.quantidade_minima,
                    "Status": status_estoque,
                    "Localização": p.localizacao or "",
                    "Preço Custo": p.preco_custo,
                    "Preço Venda": p.preco_venda,
                    "Margem Lucro": (
                        f"{((p.preco_venda - p.preco_custo) / p.preco_custo * 100):.1f}%"
                        if p.preco_custo > 0
                        else "0%"
                    ),
                    "Valor Total Custo": p.quantidade * p.preco_custo,
                    "Valor Total Venda": p.quantidade * p.preco_venda,
                    "Validade": (
                        p.data_validade.strftime("%d/%m/%Y") if p.data_validade else ""
                    ),
                    "Dias Validade": dias_validade if dias_validade else "",
                    "Lote": p.lote or "",
                    "Fornecedor": p.fornecedor.nome if p.fornecedor else "",
                    "Ativo": "Sim" if p.ativo else "Não",
                }
            )

        df = pd.DataFrame(dados)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Planilha principal
            df.to_excel(writer, sheet_name="Estoque", index=False)

            # Formatar a planilha
            worksheet = writer.sheets["Estoque"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Resumo
            if not df.empty:
                # Agrupar por categoria
                if "Categoria" in df.columns and not df["Categoria"].isna().all():
                    por_categoria = (
                        df.groupby("Categoria")
                        .agg(
                            {
                                "Quantidade": "sum",
                                "Valor Total Custo": "sum",
                                "Valor Total Venda": "sum",
                            }
                        )
                        .reset_index()
                    )

                    # Calcular margem por categoria
                    por_categoria["Margem"] = (
                        (
                            por_categoria["Valor Total Venda"]
                            - por_categoria["Valor Total Custo"]
                        )
                        / por_categoria["Valor Total Custo"]
                        * 100
                    )
                    por_categoria.to_excel(
                        writer, sheet_name="Por Categoria", index=False
                    )

                # Produtos abaixo do mínimo
                produtos_baixo = df[df["Status"] == "BAIXO"]
                if not produtos_baixo.empty:
                    produtos_baixo.to_excel(
                        writer, sheet_name="Estoque Baixo", index=False
                    )

                # Produtos próximos da validade
                produtos_validade = df[df["Status"] == "VALIDADE PRÓXIMA"]
                if not produtos_validade.empty:
                    produtos_validade.to_excel(
                        writer, sheet_name="Validade Próxima", index=False
                    )

                # Produtos esgotados
                produtos_esgotados = df[df["Status"] == "ESGOTADO"]
                if not produtos_esgotados.empty:
                    produtos_esgotados.to_excel(
                        writer, sheet_name="Esgotados", index=False
                    )

                # Estatísticas gerais
                total_custo = df["Valor Total Custo"].sum()
                total_venda = df["Valor Total Venda"].sum()
                lucro_potencial = total_venda - total_custo
                margem_media = (
                    (lucro_potencial / total_custo * 100) if total_custo > 0 else 0
                )

                resumo = pd.DataFrame(
                    [
                        {
                            "Total de Produtos": len(df),
                            "Valor Total em Estoque (Custo)": total_custo,
                            "Valor Total em Estoque (Venda)": total_venda,
                            "Lucro Potencial": lucro_potencial,
                            "Margem Média": f"{margem_media:.1f}%",
                            "Produtos Abaixo do Mínimo": len(produtos_baixo),
                            "Produtos Próximos da Validade": len(produtos_validade),
                            "Produtos Esgotados": len(produtos_esgotados),
                            "Produtos Ativos": len(df[df["Ativo"] == "Sim"]),
                        }
                    ]
                )
                resumo.to_excel(writer, sheet_name="Resumo", index=False)

        output.seek(0)

        nome_tipo = {
            "geral": "geral",
            "validade": "validade_proxima",
            "minimo": "estoque_minimo",
            "inativos": "produtos_inativos",
            "custo": "analise_custo",
        }

        nome_arquivo = (
            f"relatorio_estoque_{nome_tipo.get(tipo, 'geral')}_{date.today()}.xlsx"
        )

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar Excel de estoque: {str(e)}")
        raise


def gerar_pdf_estoque(produtos, tipo, estabelecimento_id):
    """Gera relatório de estoque em formato PDF - FUNÇÃO FALTANTE IMPLEMENTADA"""
    try:
        # Buscar estabelecimento
        from app.models import Estabelecimento

        estabelecimento = Estabelecimento.query.get(estabelecimento_id)

        # Buscar configurações
        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()

        # Títulos por tipo
        titulos = {
            "geral": "RELATÓRIO DE ESTOQUE GERAL",
            "validade": "RELATÓRIO DE PRODUTOS PRÓXIMOS DA VALIDADE",
            "minimo": "RELATÓRIO DE PRODUTOS COM ESTOQUE MÍNIMO",
            "inativos": "RELATÓRIO DE PRODUTOS INATIVOS",
            "custo": "ANÁLISE DE CUSTO DO ESTOQUE",
        }

        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        elements = []
        styles = getSampleStyleSheet()

        # Cabeçalho
        if estabelecimento:
            elements.append(
                Paragraph(f"<b>{estabelecimento.nome}</b>", styles["Title"])
            )
            elements.append(
                Paragraph(f"CNPJ: {estabelecimento.cnpj}", styles["Normal"])
            )

        elements.append(Spacer(1, 20))

        # Título do relatório
        elements.append(
            Paragraph(
                f"<b>{titulos.get(tipo, 'RELATÓRIO DE ESTOQUE')}</b>", styles["Title"]
            )
        )
        elements.append(
            Paragraph(
                f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(f"Total de produtos: {len(produtos)}", styles["Normal"])
        )
        elements.append(Spacer(1, 20))

        # Resumo estatístico
        valor_total_custo = sum(p.quantidade * p.preco_custo for p in produtos)
        valor_total_venda = sum(p.quantidade * p.preco_venda for p in produtos)
        lucro_potencial = valor_total_venda - valor_total_custo
        produtos_abaixo_minimo = sum(
            1 for p in produtos if p.quantidade <= p.quantidade_minima
        )
        produtos_esgotados = sum(1 for p in produtos if p.quantidade == 0)

        # Calcular produtos próximos da validade
        produtos_validade_proxima = []
        for p in produtos:
            if p.data_validade:
                dias = (p.data_validade - date.today()).days
                if 0 <= dias <= 15:
                    produtos_validade_proxima.append(p)

        resumo_data = [
            ["DESCRIÇÃO", "VALOR"],
            ["Valor Total (Custo):", f"R$ {valor_total_custo:,.2f}"],
            ["Valor Total (Venda):", f"R$ {valor_total_venda:,.2f}"],
            ["Lucro Potencial:", f"R$ {lucro_potencial:,.2f}"],
            ["Produtos Abaixo do Mínimo:", str(produtos_abaixo_minimo)],
            ["Produtos Esgotados:", str(produtos_esgotados)],
            ["Produtos Próximos da Validade:", str(len(produtos_validade_proxima))],
            ["", ""],
            ["MARGEM MÉDIA", ""],
            [
                "Margem Média:",
                (
                    f"{((valor_total_venda - valor_total_custo) / valor_total_custo * 100):.1f}%"
                    if valor_total_custo > 0
                    else "0%"
                ),
            ],
        ]

        resumo_table = Table(resumo_data, colWidths=[250, 100])
        resumo_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(config.cor_principal if config else "#4F46E5"),
                    ),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ]
            )
        )

        elements.append(resumo_table)
        elements.append(Spacer(1, 20))

        # Lista de produtos (limitada)
        if produtos:
            # Limitar a 50 produtos para o PDF
            produtos_exibir = produtos[:50]

            produtos_data = [
                ["CÓDIGO", "NOME", "QTDE", "MÍN", "CUSTO", "VENDA", "VALIDADE"]
            ]

            for p in produtos_exibir:
                # Formatar validade
                validade_str = ""
                if p.data_validade:
                    dias = (p.data_validade - date.today()).days
                    validade_str = f"{p.data_validade.strftime('%d/%m/%y')}"
                    if dias < 0:
                        validade_str += " (VENCIDO)"
                    elif dias <= 15:
                        validade_str += f" ({dias}d)"

                produtos_data.append(
                    [
                        (
                            p.codigo_barras[:10] + "..."
                            if p.codigo_barras and len(p.codigo_barras) > 10
                            else (p.codigo_barras or "-")
                        ),
                        p.nome[:20] + "..." if len(p.nome) > 20 else p.nome,
                        str(p.quantidade),
                        str(p.quantidade_minima),
                        f"R$ {p.preco_custo:.2f}",
                        f"R$ {p.preco_venda:.2f}",
                        validade_str,
                    ]
                )

            produtos_table = Table(
                produtos_data, colWidths=[60, 120, 40, 40, 60, 60, 80]
            )
            produtos_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.aliceblue],
                        ),
                    ]
                )
            )

            elements.append(produtos_table)

            if len(produtos) > 50:
                elements.append(Spacer(1, 10))
                elements.append(
                    Paragraph(
                        f"* Mostrando 50 de {len(produtos)} produtos. Para ver todos, exporte para Excel.",
                        ParagraphStyle(
                            name="SmallItalic", fontSize=8, fontName="Helvetica-Oblique"
                        ),
                    )
                )

        else:
            elements.append(
                Paragraph("<b>NENHUM PRODUTO ENCONTRADO</b>", styles["Heading2"])
            )

        elements.append(Spacer(1, 20))

        # Se for relatório de validade, adicionar seção especial
        if tipo == "validade" and produtos_validade_proxima:
            elements.append(
                Paragraph(
                    "<b>PRODUTOS PRÓXIMOS DA VALIDADE (≤ 15 DIAS)</b>",
                    styles["Heading2"],
                )
            )

            validade_data = [["PRODUTO", "LOTE", "QTDE", "VALIDADE", "DIAS RESTANTES"]]

            for p in produtos_validade_proxima[:20]:  # Limitar a 20
                dias = (p.data_validade - date.today()).days
                validade_data.append(
                    [
                        p.nome[:25] + "..." if len(p.nome) > 25 else p.nome,
                        p.lote or "-",
                        str(p.quantidade),
                        p.data_validade.strftime("%d/%m/%Y"),
                        str(dias),
                    ]
                )

            validade_table = Table(validade_data, colWidths=[120, 60, 40, 80, 60])
            validade_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.orange),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.lightyellow),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                    ]
                )
            )

            elements.append(validade_table)

        # Rodapé
        elements.append(
            Paragraph(
                f"Relatório gerado automaticamente pelo Sistema MercadoSys em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                ParagraphStyle(name="Footer", fontSize=8, fontName="Helvetica"),
            )
        )

        doc.build(elements)
        buffer.seek(0)

        nome_arquivo = f"relatorio_estoque_{tipo}_{date.today()}.pdf"

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar PDF de estoque: {str(e)}")
        raise


def gerar_csv_estoque(produtos, tipo):
    """Gera relatório de estoque em formato CSV"""
    try:
        import csv

        output = io.StringIO()
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        # Cabeçalho
        writer.writerow(
            [
                "CÓDIGO",
                "NOME",
                "CATEGORIA",
                "QUANTIDADE",
                "MÍNIMO",
                "LOCALIZAÇÃO",
                "PREÇO CUSTO",
                "PREÇO VENDA",
                "MARGEM %",
                "VALOR TOTAL CUSTO",
                "VALOR TOTAL VENDA",
                "VALIDADE",
                "DIAS VALIDADE",
                "LOTE",
                "FORNECEDOR",
                "ATIVO",
            ]
        )

        # Dados
        for p in produtos:
            # Calcular margem
            margem = 0
            if p.preco_custo > 0:
                margem = (p.preco_venda - p.preco_custo) / p.preco_custo * 100

            # Calcular dias para validade
            dias_validade = None
            if p.data_validade:
                dias_validade = (p.data_validade - date.today()).days

            writer.writerow(
                [
                    p.codigo_barras or "",
                    p.nome,
                    p.categoria or "",
                    p.quantidade,
                    p.quantidade_minima,
                    p.localizacao or "",
                    f"{p.preco_custo:.2f}",
                    f"{p.preco_venda:.2f}",
                    f"{margem:.1f}",
                    f"{(p.quantidade * p.preco_custo):.2f}",
                    f"{(p.quantidade * p.preco_venda):.2f}",
                    p.data_validade.strftime("%d/%m/%Y") if p.data_validade else "",
                    dias_validade if dias_validade else "",
                    p.lote or "",
                    p.fornecedor.nome if p.fornecedor else "",
                    "Sim" if p.ativo else "Não",
                ]
            )

        # Converter para bytes
        output_bytes = io.BytesIO(output.getvalue().encode("utf-8"))
        output_bytes.seek(0)

        nome_arquivo = f"relatorio_estoque_{tipo}_{date.today()}.csv"

        return send_file(
            output_bytes,
            mimetype="text/csv",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar CSV de estoque: {str(e)}")
        raise


@relatorios_bp.route("/clientes", methods=["GET"])
@gerente_ou_admin_required
def relatorio_clientes():
    """Gera relatório de clientes"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        formato = request.args.get("formato", "json")  # json, excel, pdf, csv
        tipo = request.args.get("tipo", "todos")  # todos, ativos, inativos, top
        limite = request.args.get("limite", type=int)

        query = Cliente.query.filter_by(estabelecimento_id=estabelecimento_id)

        if tipo == "top":
            # Top clientes por valor de compras
            query = query.order_by(Cliente.total_compras.desc())
            if limite:
                query = query.limit(limite)
        elif tipo == "ativos":
            # Clientes com compras recentes (últimos 30 dias)
            data_limite = datetime.now() - timedelta(days=30)
            query = query.filter(Cliente.ultima_compra >= data_limite)
            query = query.order_by(Cliente.total_compras.desc())
        elif tipo == "inativos":
            # Clientes inativos (sem compras nos últimos 90 dias)
            data_limite = datetime.now() - timedelta(days=90)
            query = query.filter(
                (Cliente.ultima_compra < data_limite)
                | (Cliente.ultima_compra.is_(None))
            )
            query = query.order_by(Cliente.ultima_compra.desc())
        else:  # todos
            query = query.order_by(Cliente.total_compras.desc())

        clientes = query.all()

        if formato == "excel":
            return gerar_excel_clientes(clientes, tipo)
        elif formato == "pdf":
            return gerar_pdf_clientes(clientes, tipo, estabelecimento_id)
        elif formato == "csv":
            return gerar_csv_clientes(clientes, tipo)
        else:
            # JSON padrão
            valor_total_compras = sum(c.total_compras for c in clientes)
            clientes_ativos = (
                sum(
                    1
                    for c in clientes
                    if c.ultima_compra and (datetime.now() - c.ultima_compra).days <= 30
                )
                if clientes
                else 0
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "tipo": tipo,
                        "quantidade_clientes": len(clientes),
                        "valor_total_compras": valor_total_compras,
                        "clientes_ativos": clientes_ativos,
                        "ticket_medio": (
                            valor_total_compras / len(clientes) if clientes else 0
                        ),
                        "clientes": [c.to_dict() for c in clientes],
                    }
                ),
                200,
            )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório de clientes: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar relatório de clientes",
                    "message": str(e),
                }
            ),
            500,
        )


def gerar_excel_clientes(clientes, tipo):
    """Gera relatório de clientes em Excel"""
    try:
        dados = []
        for c in clientes:
            # Calcular dias desde última compra
            dias_ultima_compra = None
            if c.ultima_compra:
                dias_ultima_compra = (datetime.now() - c.ultima_compra).days

            # Status do cliente
            status = "INATIVO"
            if dias_ultima_compra is not None:
                if dias_ultima_compra <= 30:
                    status = "ATIVO"
                elif dias_ultima_compra <= 90:
                    status = "REGULAR"

            dados.append(
                {
                    "Nome": c.nome,
                    "CPF/CNPJ": c.cpf_cnpj or "",
                    "Telefone": c.telefone or "",
                    "Email": c.email or "",
                    "Total Compras": c.total_compras,
                    "Status": status,
                    "Data Cadastro": (
                        c.data_cadastro.strftime("%d/%m/%Y") if c.data_cadastro else ""
                    ),
                    "Última Compra": (
                        c.ultima_compra.strftime("%d/%m/%Y") if c.ultima_compra else ""
                    ),
                    "Dias Última Compra": (
                        dias_ultima_compra if dias_ultima_compra else ""
                    ),
                    "Endereço": c.endereco or "",
                    "Observações": c.observacoes or "",
                }
            )

        df = pd.DataFrame(dados)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Clientes", index=False)

            # Formatar a planilha
            worksheet = writer.sheets["Clientes"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Top 10 clientes
            if not df.empty and len(df) > 10:
                top10 = df.nlargest(10, "Total Compras")
                top10.to_excel(writer, sheet_name="Top 10", index=False)

            # Análise por status
            if not df.empty and "Status" in df.columns:
                por_status = (
                    df.groupby("Status")
                    .agg({"Nome": "count", "Total Compras": "sum"})
                    .rename(
                        columns={"Nome": "Quantidade", "Total Compras": "Valor Total"}
                    )
                )
                por_status["Ticket Médio"] = (
                    por_status["Valor Total"] / por_status["Quantidade"]
                )
                por_status.to_excel(writer, sheet_name="Por Status", index=True)

            # Resumo estatístico
            if not df.empty:
                total_clientes = len(df)
                valor_total = df["Total Compras"].sum()
                ticket_medio = valor_total / total_clientes if total_clientes > 0 else 0

                resumo = pd.DataFrame(
                    [
                        {
                            "Total de Clientes": total_clientes,
                            "Valor Total em Compras": valor_total,
                            "Ticket Médio": ticket_medio,
                            "Clientes Ativos": len(df[df["Status"] == "ATIVO"]),
                            "Clientes Regulares": len(df[df["Status"] == "REGULAR"]),
                            "Clientes Inativos": len(df[df["Status"] == "INATIVO"]),
                            "Período de Análise": tipo.upper(),
                        }
                    ]
                )
                resumo.to_excel(writer, sheet_name="Resumo", index=False)

        output.seek(0)

        nome_arquivo = f"relatorio_clientes_{tipo}_{date.today()}.xlsx"

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar Excel de clientes: {str(e)}")
        raise


def gerar_pdf_clientes(clientes, tipo, estabelecimento_id):
    """Gera relatório de clientes em formato PDF - FUNÇÃO FALTANTE IMPLEMENTADA"""
    try:
        # Buscar estabelecimento
        from app.models import Estabelecimento

        estabelecimento = Estabelecimento.query.get(estabelecimento_id)

        # Buscar configurações
        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()

        # Títulos por tipo
        titulos = {
            "todos": "RELATÓRIO DE CLIENTES",
            "top": "TOP CLIENTES",
            "ativos": "CLIENTES ATIVOS",
            "inativos": "CLIENTES INATIVOS",
        }

        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        elements = []
        styles = getSampleStyleSheet()

        # Cabeçalho
        if estabelecimento:
            elements.append(
                Paragraph(f"<b>{estabelecimento.nome}</b>", styles["Title"])
            )

        elements.append(Spacer(1, 20))

        # Título do relatório
        elements.append(
            Paragraph(
                f"<b>{titulos.get(tipo, 'RELATÓRIO DE CLIENTES')}</b>", styles["Title"]
            )
        )
        elements.append(
            Paragraph(
                f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(f"Total de clientes: {len(clientes)}", styles["Normal"])
        )
        elements.append(Spacer(1, 20))

        # Resumo estatístico
        valor_total_compras = sum(c.total_compras for c in clientes)
        ticket_medio = valor_total_compras / len(clientes) if clientes else 0

        # Calcular status dos clientes
        ativos = 0
        regulares = 0
        inativos = 0

        for c in clientes:
            if c.ultima_compra:
                dias = (datetime.now() - c.ultima_compra).days
                if dias <= 30:
                    ativos += 1
                elif dias <= 90:
                    regulares += 1
                else:
                    inativos += 1
            else:
                inativos += 1

        resumo_data = [
            ["DESCRIÇÃO", "VALOR"],
            ["Valor Total em Compras:", f"R$ {valor_total_compras:,.2f}"],
            ["Ticket Médio:", f"R$ {ticket_medio:,.2f}"],
            ["", ""],
            ["DISTRIBUIÇÃO POR STATUS", ""],
            ["Clientes Ativos (≤ 30 dias):", str(ativos)],
            ["Clientes Regulares (31-90 dias):", str(regulares)],
            ["Clientes Inativos (> 90 dias):", str(inativos)],
            ["", ""],
            ["PERCENTUAL POR STATUS", ""],
            ["Ativos:", f"{(ativos/len(clientes)*100):.1f}%" if clientes else "0%"],
            [
                "Regulares:",
                f"{(regulares/len(clientes)*100):.1f}%" if clientes else "0%",
            ],
            ["Inativos:", f"{(inativos/len(clientes)*100):.1f}%" if clientes else "0%"],
        ]

        resumo_table = Table(resumo_data, colWidths=[250, 100])
        resumo_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(config.cor_principal if config else "#4F46E5"),
                    ),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ]
            )
        )

        elements.append(resumo_table)
        elements.append(Spacer(1, 20))

        # Lista de clientes (limitada)
        if clientes:
            # Limitar a 30 clientes para o PDF
            clientes_exibir = clientes[:30]

            clientes_data = [
                [
                    "NOME",
                    "CPF/CNPJ",
                    "TELEFONE",
                    "TOTAL COMPRAS",
                    "ÚLTIMA COMPRA",
                    "STATUS",
                ]
            ]

            for c in clientes_exibir:
                # Determinar status
                status = "INATIVO"
                if c.ultima_compra:
                    dias = (datetime.now() - c.ultima_compra).days
                    if dias <= 30:
                        status = "ATIVO"
                    elif dias <= 90:
                        status = "REGULAR"

                clientes_data.append(
                    [
                        c.nome[:20] + "..." if len(c.nome) > 20 else c.nome,
                        c.cpf_cnpj or "-",
                        c.telefone or "-",
                        f"R$ {c.total_compras:,.2f}",
                        (
                            c.ultima_compra.strftime("%d/%m/%Y")
                            if c.ultima_compra
                            else "-"
                        ),
                        status,
                    ]
                )

            clientes_table = Table(clientes_data, colWidths=[100, 80, 80, 80, 80, 50])
            clientes_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.aliceblue],
                        ),
                    ]
                )
            )

            elements.append(clientes_table)

            if len(clientes) > 30:
                elements.append(Spacer(1, 10))
                elements.append(
                    Paragraph(
                        f"* Mostrando 30 de {len(clientes)} clientes. Para ver todos, exporte para Excel.",
                        ParagraphStyle(
                            name="SmallItalic", fontSize=8, fontName="Helvetica-Oblique"
                        ),
                    )
                )

        else:
            elements.append(
                Paragraph("<b>NENHUM CLIENTE ENCONTRADO</b>", styles["Heading2"])
            )

        elements.append(Spacer(1, 20))

        # Se for top clientes, adicionar ranking
        if tipo == "top" and clientes:
            elements.append(
                Paragraph("<b>RANKING DOS TOP 10 CLIENTES</b>", styles["Heading2"])
            )

            top10 = sorted(clientes, key=lambda x: x.total_compras, reverse=True)[:10]

            ranking_data = [["POSIÇÃO", "CLIENTE", "VALOR TOTAL"]]

            for i, c in enumerate(top10, 1):
                ranking_data.append(
                    [
                        str(i),
                        c.nome[:25] + "..." if len(c.nome) > 25 else c.nome,
                        f"R$ {c.total_compras:,.2f}",
                    ]
                )

            ranking_table = Table(ranking_data, colWidths=[50, 200, 100])
            ranking_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.lightblue),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                    ]
                )
            )

            elements.append(ranking_table)

        # Rodapé
        elements.append(
            Paragraph(
                f"Relatório gerado automaticamente pelo Sistema MercadoSys em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                ParagraphStyle(name="Footer", fontSize=8, fontName="Helvetica"),
            )
        )

        doc.build(elements)
        buffer.seek(0)

        nome_arquivo = f"relatorio_clientes_{tipo}_{date.today()}.pdf"

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar PDF de clientes: {str(e)}")
        raise


def gerar_csv_clientes(clientes, tipo):
    """Gera relatório de clientes em formato CSV"""
    try:
        import csv

        output = io.StringIO()
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        # Cabeçalho
        writer.writerow(
            [
                "NOME",
                "CPF/CNPJ",
                "TELEFONE",
                "EMAIL",
                "TOTAL COMPRAS",
                "DATA CADASTRO",
                "ÚLTIMA COMPRA",
                "DIAS ÚLTIMA COMPRA",
                "STATUS",
                "ENDEREÇO",
                "OBSERVAÇÕES",
            ]
        )

        # Dados
        for c in clientes:
            # Calcular dias desde última compra
            dias_ultima_compra = None
            status = "INATIVO"

            if c.ultima_compra:
                dias_ultima_compra = (datetime.now() - c.ultima_compra).days
                if dias_ultima_compra <= 30:
                    status = "ATIVO"
                elif dias_ultima_compra <= 90:
                    status = "REGULAR"

            writer.writerow(
                [
                    c.nome,
                    c.cpf_cnpj or "",
                    c.telefone or "",
                    c.email or "",
                    f"{c.total_compras:.2f}",
                    c.data_cadastro.strftime("%d/%m/%Y") if c.data_cadastro else "",
                    c.ultima_compra.strftime("%d/%m/%Y") if c.ultima_compra else "",
                    dias_ultima_compra if dias_ultima_compra else "",
                    status,
                    c.endereco or "",
                    c.observacoes or "",
                ]
            )

        # Converter para bytes
        output_bytes = io.BytesIO(output.getvalue().encode("utf-8"))
        output_bytes.seek(0)

        nome_arquivo = f"relatorio_clientes_{tipo}_{date.today()}.csv"

        return send_file(
            output_bytes,
            mimetype="text/csv",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar CSV de clientes: {str(e)}")
        raise


@relatorios_bp.route("/financeiro", methods=["GET"])
@gerente_ou_admin_required
def relatorio_financeiro():
    """Gera relatório financeiro consolidado"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        mes = request.args.get("mes", type=int)
        ano = request.args.get("ano", type=int)
        formato = request.args.get("formato", "json")

        if not mes or not ano:
            mes = datetime.now().month
            ano = datetime.now().year

        # Definir período do mês
        inicio_mes = datetime(ano, mes, 1)
        if mes == 12:
            fim_mes = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            fim_mes = datetime(ano, mes + 1, 1) - timedelta(days=1)

        # Buscar vendas do mês
        vendas = Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.data_venda >= inicio_mes,
            Venda.data_venda <= fim_mes,
            Venda.status == "finalizada",
        ).all()

        # Calcular totais
        total_vendas = sum(v.total for v in vendas)
        total_descontos = sum(v.desconto for v in vendas)
        quantidade_vendas = len(vendas)

        # Agrupar por forma de pagamento
        formas_pagamento = {}
        for v in vendas:
            forma = v.forma_pagamento
            if forma not in formas_pagamento:
                formas_pagamento[forma] = {"total": 0, "quantidade": 0}
            formas_pagamento[forma]["total"] += v.total
            formas_pagamento[forma]["quantidade"] += 1

        # Calcular por dia da semana
        vendas_por_dia = {}
        for v in vendas:
            dia_semana = v.data_venda.strftime("%A")
            if dia_semana not in vendas_por_dia:
                vendas_por_dia[dia_semana] = {"total": 0, "quantidade": 0}
            vendas_por_dia[dia_semana]["total"] += v.total
            vendas_por_dia[dia_semana]["quantidade"] += 1

        if formato == "excel":
            return gerar_excel_financeiro(
                vendas, inicio_mes, fim_mes, formas_pagamento, vendas_por_dia
            )
        elif formato == "pdf":
            return gerar_pdf_financeiro(
                vendas,
                inicio_mes,
                fim_mes,
                formas_pagamento,
                vendas_por_dia,
                estabelecimento_id,
            )
        else:
            # JSON
            return (
                jsonify(
                    {
                        "success": True,
                        "periodo": {
                            "mes": mes,
                            "ano": ano,
                            "inicio": inicio_mes.isoformat(),
                            "fim": fim_mes.isoformat(),
                        },
                        "total_vendas": total_vendas,
                        "total_descontos": total_descontos,
                        "quantidade_vendas": quantidade_vendas,
                        "ticket_medio": (
                            total_vendas / quantidade_vendas
                            if quantidade_vendas > 0
                            else 0
                        ),
                        "formas_pagamento": formas_pagamento,
                        "vendas_por_dia": vendas_por_dia,
                        "dias_uteis": len(vendas_por_dia),
                    }
                ),
                200,
            )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório financeiro: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar relatório financeiro",
                    "message": str(e),
                }
            ),
            500,
        )


def gerar_excel_financeiro(
    vendas, inicio_mes, fim_mes, formas_pagamento, vendas_por_dia
):
    """Gera relatório financeiro em Excel"""
    try:
        # Criar Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Resumo do mês
            total_vendas = sum(v.total for v in vendas)
            total_descontos = sum(v.desconto for v in vendas)
            quantidade_vendas = len(vendas)
            ticket_medio = (
                total_vendas / quantidade_vendas if quantidade_vendas > 0 else 0
            )

            resumo = pd.DataFrame(
                [
                    {
                        "Período": f"{inicio_mes.strftime('%m/%Y')}",
                        "Total Vendas": total_vendas,
                        "Total Descontos": total_descontos,
                        "Quantidade de Vendas": quantidade_vendas,
                        "Ticket Médio": ticket_medio,
                        "Dias com Vendas": len(vendas_por_dia),
                        "Meta Atingida": "Não Definida",  # Pode ser implementado posteriormente
                    }
                ]
            )
            resumo.to_excel(writer, sheet_name="Resumo", index=False)

            # Formas de pagamento
            if formas_pagamento:
                pagamentos_data = []
                for forma, dados in formas_pagamento.items():
                    percentual = (
                        (dados["total"] / total_vendas * 100) if total_vendas > 0 else 0
                    )
                    pagamentos_data.append(
                        {
                            "Forma de Pagamento": forma.title(),
                            "Quantidade": dados["quantidade"],
                            "Valor Total": dados["total"],
                            "Percentual": f"{percentual:.1f}%",
                        }
                    )

                df_pagamentos = pd.DataFrame(pagamentos_data)
                df_pagamentos.to_excel(
                    writer, sheet_name="Formas Pagamento", index=False
                )

            # Vendas por dia da semana
            if vendas_por_dia:
                dias_data = []
                for dia, dados in vendas_por_dia.items():
                    dias_data.append(
                        {
                            "Dia da Semana": dia,
                            "Quantidade de Vendas": dados["quantidade"],
                            "Valor Total": dados["total"],
                            "Ticket Médio Dia": (
                                dados["total"] / dados["quantidade"]
                                if dados["quantidade"] > 0
                                else 0
                            ),
                        }
                    )

                df_dias = pd.DataFrame(dias_data)
                df_dias.to_excel(writer, sheet_name="Vendas por Dia", index=False)

            # Lista de vendas (limitada)
            if vendas:
                vendas_data = []
                for v in vendas[:100]:  # Limitar a 100 vendas
                    vendas_data.append(
                        {
                            "Data": v.data_venda.strftime("%d/%m/%Y %H:%M"),
                            "Código": v.codigo,
                            "Cliente": (
                                v.cliente.nome if v.cliente else "Consumidor Final"
                            ),
                            "Total": v.total,
                            "Desconto": v.desconto,
                            "Forma Pagamento": v.forma_pagamento,
                            "Itens": len(v.itens),
                        }
                    )

                df_vendas = pd.DataFrame(vendas_data)
                df_vendas.to_excel(writer, sheet_name="Vendas Detalhadas", index=False)

        output.seek(0)

        nome_arquivo = f"relatorio_financeiro_{inicio_mes.strftime('%m_%Y')}.xlsx"

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar Excel financeiro: {str(e)}")
        raise


def gerar_pdf_financeiro(
    vendas, inicio_mes, fim_mes, formas_pagamento, vendas_por_dia, estabelecimento_id
):
    """Gera relatório financeiro em PDF"""
    try:
        # Buscar estabelecimento
        from app.models import Estabelecimento

        estabelecimento = Estabelecimento.query.get(estabelecimento_id)

        # Buscar configurações
        config = Configuracao.query.filter_by(
            estabelecimento_id=estabelecimento_id
        ).first()

        # Calcular totais
        total_vendas = sum(v.total for v in vendas)
        total_descontos = sum(v.desconto for v in vendas)
        quantidade_vendas = len(vendas)
        ticket_medio = total_vendas / quantidade_vendas if quantidade_vendas > 0 else 0

        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        elements = []
        styles = getSampleStyleSheet()

        # Cabeçalho
        if estabelecimento:
            elements.append(
                Paragraph(f"<b>{estabelecimento.nome}</b>", styles["Title"])
            )
            elements.append(
                Paragraph(f"CNPJ: {estabelecimento.cnpj}", styles["Normal"])
            )

        elements.append(Spacer(1, 20))

        # Título do relatório
        elements.append(
            Paragraph("<b>RELATÓRIO FINANCEIRO MENSAL</b>", styles["Title"])
        )
        elements.append(
            Paragraph(f"Período: {inicio_mes.strftime('%m/%Y')}", styles["Normal"])
        )
        elements.append(
            Paragraph(
                f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 20))

        # Resumo financeiro
        resumo_data = [
            ["DESCRIÇÃO", "VALOR"],
            ["Total de Vendas:", f"R$ {total_vendas:,.2f}"],
            ["Total de Descontos:", f"R$ {total_descontos:,.2f}"],
            ["Quantidade de Vendas:", str(quantidade_vendas)],
            ["Ticket Médio:", f"R$ {ticket_medio:,.2f}"],
            [
                "Período Analisado:",
                f"{inicio_mes.strftime('%d/%m/%Y')} a {fim_mes.strftime('%d/%m/%Y')}",
            ],
            ["Dias com Vendas:", str(len(vendas_por_dia))],
        ]

        resumo_table = Table(resumo_data, colWidths=[250, 100])
        resumo_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(config.cor_principal if config else "#4F46E5"),
                    ),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ]
            )
        )

        elements.append(resumo_table)
        elements.append(Spacer(1, 20))

        # Formas de pagamento
        if formas_pagamento:
            elements.append(
                Paragraph(
                    "<b>DISTRIBUIÇÃO POR FORMA DE PAGAMENTO</b>", styles["Heading2"]
                )
            )

            pagamento_data = [["FORMA DE PAGAMENTO", "QUANTIDADE", "VALOR TOTAL", "%"]]

            for forma, dados in formas_pagamento.items():
                percentual = (
                    (dados["total"] / total_vendas * 100) if total_vendas > 0 else 0
                )
                pagamento_data.append(
                    [
                        forma.title(),
                        str(dados["quantidade"]),
                        f"R$ {dados['total']:,.2f}",
                        f"{percentual:.1f}%",
                    ]
                )

            pagamento_table = Table(pagamento_data, colWidths=[120, 80, 100, 60])
            pagamento_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                    ]
                )
            )

            elements.append(pagamento_table)
            elements.append(Spacer(1, 20))

        # Vendas por dia da semana
        if vendas_por_dia:
            elements.append(
                Paragraph("<b>VENDAS POR DIA DA SEMANA</b>", styles["Heading2"])
            )

            # Traduzir dias da semana
            dias_traduzidos = {
                "Monday": "Segunda",
                "Tuesday": "Terça",
                "Wednesday": "Quarta",
                "Thursday": "Quinta",
                "Friday": "Sexta",
                "Saturday": "Sábado",
                "Sunday": "Domingo",
            }

            dias_data = [["DIA DA SEMANA", "QUANTIDADE", "VALOR TOTAL", "TICKET MÉDIO"]]

            for dia, dados in vendas_por_dia.items():
                dia_traduzido = dias_traduzidos.get(dia, dia)
                ticket_dia = (
                    dados["total"] / dados["quantidade"]
                    if dados["quantidade"] > 0
                    else 0
                )
                dias_data.append(
                    [
                        dia_traduzido,
                        str(dados["quantidade"]),
                        f"R$ {dados['total']:,.2f}",
                        f"R$ {ticket_dia:,.2f}",
                    ]
                )

            dias_table = Table(dias_data, colWidths=[100, 80, 100, 80])
            dias_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                    ]
                )
            )

            elements.append(dias_table)

        elements.append(Spacer(1, 20))

        # Rodapé
        elements.append(
            Paragraph(
                f"Relatório gerado automaticamente pelo Sistema MercadoSys em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                ParagraphStyle(name="Footer", fontSize=8, fontName="Helvetica"),
            )
        )

        doc.build(elements)
        buffer.seek(0)

        nome_arquivo = f"relatorio_financeiro_{inicio_mes.strftime('%m_%Y')}.pdf"

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar PDF financeiro: {str(e)}")
        raise


@relatorios_bp.route("/produtos-mais-vendidos", methods=["GET"])
@funcionario_required
def produtos_mais_vendidos():
    """Relatório dos produtos mais vendidos"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        limite = request.args.get("limite", 10, type=int)
        formato = request.args.get("formato", "json")

        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio.replace("Z", "+00:00"))
        else:
            data_inicio = datetime.now() - timedelta(days=30)

        if data_fim:
            data_fim = datetime.fromisoformat(data_fim.replace("Z", "+00:00"))
        else:
            data_fim = datetime.now()

        # Consulta para produtos mais vendidos
        produtos_mais_vendidos = (
            db.session.query(
                VendaItem.produto_id,
                VendaItem.produto_nome,
                func.sum(VendaItem.quantidade).label("quantidade_total"),
                func.sum(VendaItem.total_item).label("total_vendido"),
                func.count(VendaItem.venda_id).label("quantidade_vendas"),
            )
            .join(Venda)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.data_venda <= data_fim,
                Venda.status == "finalizada",
            )
            .group_by(VendaItem.produto_id, VendaItem.produto_nome)
            .order_by(func.sum(VendaItem.quantidade).desc())
            .limit(limite)
            .all()
        )

        if formato == "excel":
            return gerar_excel_produtos_mais_vendidos(
                produtos_mais_vendidos, data_inicio, data_fim
            )
        elif formato == "pdf":
            return gerar_pdf_produtos_mais_vendidos(
                produtos_mais_vendidos, data_inicio, data_fim, estabelecimento_id
            )
        else:
            # JSON
            resultado = []
            for p in produtos_mais_vendidos:
                resultado.append(
                    {
                        "produto_id": p.produto_id,
                        "nome": p.produto_nome,
                        "quantidade_total": int(p.quantidade_total),
                        "total_vendido": (
                            float(p.total_vendido) if p.total_vendido else 0
                        ),
                        "quantidade_vendas": p.quantidade_vendas,
                    }
                )

            return (
                jsonify(
                    {
                        "success": True,
                        "periodo": {
                            "inicio": data_inicio.isoformat(),
                            "fim": data_fim.isoformat(),
                        },
                        "limite": limite,
                        "produtos": resultado,
                    }
                ),
                200,
            )

    except Exception as e:
        current_app.logger.error(
            f"Erro ao gerar relatório de produtos mais vendidos: {str(e)}"
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao gerar relatório de produtos mais vendidos",
                    "message": str(e),
                }
            ),
            500,
        )


def gerar_excel_produtos_mais_vendidos(produtos_mais_vendidos, data_inicio, data_fim):
    """Gera relatório de produtos mais vendidos em Excel"""
    try:
        # Criar DataFrame
        dados = []
        for p in produtos_mais_vendidos:
            dados.append(
                {
                    "Produto": p.produto_nome,
                    "Código Produto": p.produto_id,
                    "Quantidade Vendida": int(p.quantidade_total),
                    "Total Vendido": float(p.total_vendido) if p.total_vendido else 0,
                    "Quantidade de Vendas": p.quantidade_vendas,
                    "Média por Venda": (
                        float(p.total_vendido) / p.quantidade_vendas
                        if p.quantidade_vendas > 0
                        else 0
                    ),
                }
            )

        df = pd.DataFrame(dados)

        # Adicionar ranking
        df.insert(0, "Ranking", range(1, len(df) + 1))

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Produtos Mais Vendidos", index=False)

            # Formatar a planilha
            worksheet = writer.sheets["Produtos Mais Vendidos"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        nome_arquivo = (
            f"produtos_mais_vendidos_{data_inicio.date()}_a_{data_fim.date()}.xlsx"
        )

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(
            f"Erro ao gerar Excel de produtos mais vendidos: {str(e)}"
        )
        raise


def gerar_pdf_produtos_mais_vendidos(
    produtos_mais_vendidos, data_inicio, data_fim, estabelecimento_id
):
    """Gera relatório de produtos mais vendidos em PDF"""
    try:
        # Buscar estabelecimento
        from app.models import Estabelecimento

        estabelecimento = Estabelecimento.query.get(estabelecimento_id)

        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        elements = []
        styles = getSampleStyleSheet()

        # Cabeçalho
        if estabelecimento:
            elements.append(
                Paragraph(f"<b>{estabelecimento.nome}</b>", styles["Title"])
            )

        elements.append(Spacer(1, 20))

        # Título do relatório
        elements.append(
            Paragraph("<b>RELATÓRIO DE PRODUTOS MAIS VENDIDOS</b>", styles["Title"])
        )
        elements.append(
            Paragraph(
                f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(
                f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 20))

        # Tabela de produtos
        if produtos_mais_vendidos:
            produtos_data = [
                ["RANK", "PRODUTO", "QUANTIDADE", "TOTAL VENDIDO", "VENDAS"]
            ]

            for i, p in enumerate(produtos_mais_vendidos, 1):
                produtos_data.append(
                    [
                        str(i),
                        (
                            p.produto_nome[:30] + "..."
                            if len(p.produto_nome) > 30
                            else p.produto_nome
                        ),
                        str(int(p.quantidade_total)),
                        (
                            f"R$ {float(p.total_vendido):,.2f}"
                            if p.total_vendido
                            else "R$ 0,00"
                        ),
                        str(p.quantidade_vendas),
                    ]
                )

            produtos_table = Table(produtos_data, colWidths=[40, 180, 80, 100, 60])
            produtos_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.lightgreen),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                    ]
                )
            )

            elements.append(produtos_table)

            # Estatísticas
            total_quantidade = sum(
                int(p.quantidade_total) for p in produtos_mais_vendidos
            )
            total_vendido = sum(
                float(p.total_vendido)
                for p in produtos_mais_vendidos
                if p.total_vendido
            )

            elements.append(Spacer(1, 20))
            elements.append(Paragraph("<b>ESTATÍSTICAS GERAIS</b>", styles["Heading2"]))

            estatisticas_data = [
                ["Total de Produtos na Lista:", str(len(produtos_mais_vendidos))],
                ["Quantidade Total Vendida:", str(total_quantidade)],
                ["Valor Total Vendido:", f"R$ {total_vendido:,.2f}"],
                [
                    "Média por Produto:",
                    (
                        f"R$ {total_vendido / len(produtos_mais_vendidos):,.2f}"
                        if produtos_mais_vendidos
                        else "R$ 0,00"
                    ),
                ],
            ]

            estatisticas_table = Table(estatisticas_data, colWidths=[200, 100])
            estatisticas_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ]
                )
            )

            elements.append(estatisticas_table)

        else:
            elements.append(
                Paragraph(
                    "<b>NENHUM DADO DE VENDA ENCONTRADO NO PERÍODO</b>",
                    styles["Heading2"],
                )
            )

        elements.append(Spacer(1, 20))

        # Rodapé
        elements.append(
            Paragraph(
                f"Relatório gerado automaticamente pelo Sistema MercadoSys em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                ParagraphStyle(name="Footer", fontSize=8, fontName="Helvetica"),
            )
        )

        doc.build(elements)
        buffer.seek(0)

        nome_arquivo = (
            f"produtos_mais_vendidos_{data_inicio.date()}_a_{data_fim.date()}.pdf"
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=nome_arquivo,
        )

    except Exception as e:
        current_app.logger.error(
            f"Erro ao gerar PDF de produtos mais vendidos: {str(e)}"
        )
        raise


# Adicionar gráficos aos relatórios (opcional)
@relatorios_bp.route("/grafico-vendas", methods=["GET"])
@gerente_ou_admin_required
def gerar_grafico_vendas():
    """Gera gráfico de vendas em formato de imagem"""
    try:
        estabelecimento_id = request.args.get("estabelecimento_id", 1, type=int)
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        tipo = request.args.get("tipo", "linha")  # linha, barra, pizza

        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio.replace("Z", "+00:00"))
        else:
            data_inicio = datetime.now() - timedelta(days=7)

        if data_fim:
            data_fim = datetime.fromisoformat(data_fim.replace("Z", "+00:00"))
        else:
            data_fim = datetime.now()

        # Buscar vendas por dia
        vendas_por_dia = (
            db.session.query(
                func.date(Venda.data_venda).label("data"),
                func.sum(Venda.total).label("total"),
                func.count(Venda.id).label("quantidade"),
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.data_venda <= data_fim,
                Venda.status == "finalizada",
            )
            .group_by(func.date(Venda.data_venda))
            .order_by("data")
            .all()
        )

        # Preparar dados para o gráfico
        datas = [v.data.strftime("%d/%m") for v in vendas_por_dia]
        totais = [float(v.total) for v in vendas_por_dia]
        quantidades = [v.quantidade for v in vendas_por_dia]

        # Criar gráfico
        plt.figure(figsize=(10, 6))

        if tipo == "linha":
            plt.plot(datas, totais, marker="o", linewidth=2, markersize=8)
            plt.title(
                f"Vendas por Dia - {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
            )
            plt.xlabel("Data")
            plt.ylabel("Valor (R$)")
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)

        elif tipo == "barra":
            bars = plt.bar(datas, totais, color="skyblue")
            plt.title(
                f"Vendas por Dia - {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
            )
            plt.xlabel("Data")
            plt.ylabel("Valor (R$)")
            plt.grid(True, alpha=0.3, axis="y")
            plt.xticks(rotation=45)

            # Adicionar valores nas barras
            for bar in bars:
                height = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + max(totais) * 0.01,
                    f"R$ {height:,.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        elif tipo == "pizza":
            # Para pizza, agrupar por forma de pagamento
            formas_pagamento = (
                db.session.query(
                    Venda.forma_pagamento, func.sum(Venda.total).label("total")
                )
                .filter(
                    Venda.estabelecimento_id == estabelecimento_id,
                    Venda.data_venda >= data_inicio,
                    Venda.data_venda <= data_fim,
                    Venda.status == "finalizada",
                )
                .group_by(Venda.forma_pagamento)
                .all()
            )

            labels = [fp.forma_pagamento.title() for fp in formas_pagamento]
            valores = [float(fp.total) for fp in formas_pagamento]

            plt.pie(valores, labels=labels, autopct="%1.1f%%", startangle=90)
            plt.title(
                f"Distribuição por Forma de Pagamento\n{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
            )
            plt.axis(
                "equal"
            )  # Equal aspect ratio ensures that pie is drawn as a circle.

        plt.tight_layout()

        # Salvar gráfico em buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png", dpi=100)
        plt.close()
        img_buffer.seek(0)

        return send_file(
            img_buffer,
            mimetype="image/png",
            as_attachment=False,
            download_name=f"grafico_vendas_{tipo}_{date.today()}.png",
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar gráfico de vendas: {str(e)}")
        return (
            jsonify(
                {"success": False, "error": "Erro ao gerar gráfico", "message": str(e)}
            ),
            500,
        )
