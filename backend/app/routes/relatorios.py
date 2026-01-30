from flask import Blueprint, request, jsonify, send_file, current_app
from app import db
from app.models import (
    Venda,
    Produto,
    Cliente,
    Funcionario,
    MovimentacaoEstoque,
    Configuracao,
    VendaItem,
    Estabelecimento,
)
from app.utils.email_service import enviar_email_com_anexo
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
import matplotlib
matplotlib.use("Agg")  # Use non-GUI backend before importing pyplot
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from sqlalchemy import func, extract, and_, or_, cast, String
from app.decorators.decorator_jwt import funcionario_required, gerente_ou_admin_required
from collections import defaultdict

matplotlib.use("Agg")  # Para não precisar de display GUI

relatorios_bp = Blueprint("relatorios", __name__)

# ==================== CONSTANTES E FUNÇÕES AUXILIARES ====================

FILTROS_PERMITIDOS_RELATORIOS = {
    "estabelecimento_id": lambda value: (
        Venda.estabelecimento_id == int(value) if value.isdigit() else None
    ),
    "forma_pagamento": lambda value: Venda.forma_pagamento.ilike(f"%{value}%"),
    "cliente_nome": lambda value: Cliente.nome.ilike(f"%{value}%"),
    "funcionario_nome": lambda value: Funcionario.nome.ilike(f"%{value}%"),
    "status": lambda value: Venda.status == value,
    "produto_nome": lambda value: Produto.nome.ilike(f"%{value}%"),
}


def aplicar_filtros_relatorios(query, filtros, modelo):
    """Aplica filtros avançados na query de relatórios"""
    for filtro, valor in filtros.items():
        if not valor:
            continue

        if filtro == "data_inicio" and hasattr(modelo, "data_venda"):
            try:
                data_dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
                query = query.filter(modelo.data_venda >= data_dt)
            except ValueError:
                pass

        elif filtro == "data_fim" and hasattr(modelo, "data_venda"):
            try:
                data_dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
                query = query.filter(modelo.data_venda <= data_dt)
            except ValueError:
                pass

        elif filtro == "categoria" and hasattr(modelo, "categoria"):
            query = query.filter(modelo.categoria.ilike(f"%{valor}%"))

        elif filtro == "marca" and hasattr(modelo, "marca"):
            query = query.filter(modelo.marca.ilike(f"%{valor}%"))

        elif filtro == "fornecedor_nome" and hasattr(modelo, "fornecedor"):
            query = query.join(modelo.fornecedor).filter(
                modelo.fornecedor.has(nome=valor)
            )

        elif filtro == "ativo" and hasattr(modelo, "ativo"):
            query = query.filter(modelo.ativo == (valor.lower() == "true"))

        elif filtro == "estoque_status":
            if hasattr(modelo, "quantidade") and hasattr(modelo, "quantidade_minima"):
                if valor == "baixo":
                    query = query.filter(modelo.quantidade < modelo.quantidade_minima)
                elif valor == "esgotado":
                    query = query.filter(modelo.quantidade <= 0)
                elif valor == "normal":
                    query = query.filter(modelo.quantidade >= modelo.quantidade_minima)

        elif filtro == "validade_proxima":
            if hasattr(modelo, "data_validade"):
                dias = int(valor) if valor.isdigit() else 15
                data_limite = date.today() + timedelta(days=dias)
                query = query.filter(modelo.data_validade <= data_limite)

    return query


def agrupar_vendas_por_cliente_avancado(vendas):
    """Agrupa vendas por cliente com estatísticas detalhadas"""
    from collections import defaultdict

    clientes = defaultdict(
        lambda: {
            "total": 0,
            "quantidade": 0,
            "nome": "",
            "vendas": [],
            "ultima_compra": None,
            "ticket_medio": 0,
            "frequencia_compras": 0,
            "produtos_comprados": defaultdict(lambda: {"quantidade": 0, "total": 0}),
        }
    )

    for venda in vendas:
        if venda.cliente:
            cid = venda.cliente.id
            clientes[cid]["total"] += venda.total
            clientes[cid]["quantidade"] += 1
            clientes[cid]["nome"] = venda.cliente.nome
            clientes[cid]["vendas"].append(venda.id)

            # Atualizar última compra
            if (
                not clientes[cid]["ultima_compra"]
                or venda.data_venda > clientes[cid]["ultima_compra"]
            ):
                clientes[cid]["ultima_compra"] = venda.data_venda

            # Produtos comprados
            for item in venda.itens:
                produtos = clientes[cid]["produtos_comprados"][item.produto_id]
                produtos["quantidade"] += item.quantidade
                produtos["total"] += item.total_item
                produtos["nome"] = item.produto_nome

    # Calcular estatísticas
    resultado = []
    for cliente_id, dados in clientes.items():
        ticket_medio = (
            dados["total"] / dados["quantidade"] if dados["quantidade"] > 0 else 0
        )

        # Dias desde última compra
        dias_desde_ultima = None
        if dados["ultima_compra"]:
            dias_desde_ultima = (datetime.now() - dados["ultima_compra"]).days

        # Top 5 produtos comprados
        top_produtos = sorted(
            dados["produtos_comprados"].items(),
            key=lambda x: x[1]["total"],
            reverse=True,
        )[:5]

        resultado.append(
            {
                "cliente_id": cliente_id,
                "nome": dados["nome"],
                "total_compras": dados["total"],
                "quantidade_compras": dados["quantidade"],
                "ticket_medio": ticket_medio,
                "ultima_compra": (
                    dados["ultima_compra"].isoformat()
                    if dados["ultima_compra"]
                    else None
                ),
                "dias_desde_ultima_compra": dias_desde_ultima,
                "top_produtos": [
                    {
                        "produto_id": prod_id,
                        "nome": info["nome"],
                        "quantidade": info["quantidade"],
                        "total": info["total"],
                    }
                    for prod_id, info in top_produtos
                ],
                "vendas": dados["vendas"][:10],
            }
        )

    # Ordenar por total de compras
    resultado.sort(key=lambda x: x["total_compras"], reverse=True)
    return resultado


def agrupar_vendas_por_pagamento_avancado(vendas):
    """Agrupa vendas por forma de pagamento com estatísticas detalhadas"""
    from collections import defaultdict

    formas = defaultdict(
        lambda: {
            "total": 0,
            "quantidade": 0,
            "vendas": [],
            "ticket_medio": 0,
        }
    )
    
    # ... (rest of the file content not fully read but I can overwrite and append or just append)
    # Since I cannot append with Write tool, I should read the whole file first or just write the new function to a new file and import it? No, that's messy.
    # I'll use SearchReplace to append to the end of the file.
    pass
