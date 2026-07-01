from flask import Blueprint, jsonify, request, g
from app.models import db, TabelaPreco, TabelaPrecoItem, Rota, PedidoVenda, PedidoVendaItem, Cliente, Produto, MetaVendedor, ProdutoFoco, Funcionario
from datetime import datetime, timezone
import calendar as cal_lib
from sqlalchemy import func

bp = Blueprint("sfa", __name__)


def _estab_id():
    """Retorna o estabelecimento_id do token JWT (g) ou query param."""
    return getattr(g, "estabelecimento_id", None) or request.args.get("estabelecimento_id")


# ─────────────────────────────────────────────
#  SYNC DATA (Download do Roteiro para o App)
# ─────────────────────────────────────────────
@bp.route("/sfa/sync-data", methods=["GET"])
def sync_data():
    """Baixa o roteiro do dia, clientes, produtos e tabelas do vendedor para o PWA."""
    try:
        vendedor_id = request.args.get("vendedor_id")
        estab_id = _estab_id()

        if not vendedor_id and not estab_id:
            return jsonify({"status": "error", "message": "vendedor_id ou token necessário"}), 400

        # 1. Rotas do vendedor (usa SQL direto para contornar o filtro automático de tenant)
        from sqlalchemy import text
        if vendedor_id:
            q_rotas = db.session.execute(
                text("SELECT id, nome, dia_semana, ativa FROM rotas WHERE vendedor_id = :vid AND (deleted_at IS NULL)"),
                {"vid": vendedor_id}
            ).mappings().all()
        else:
            q_rotas = []

        rota_ids = [r["id"] for r in q_rotas]

        # 2. Clientes dessas rotas (com dados completos)
        clientes_rows = []
        if rota_ids:
            placeholders = ",".join(str(i) for i in rota_ids)
            clientes_rows = db.session.execute(
                text(f"""
                    SELECT id, nome, telefone, celular, email,
                           logradouro, numero, complemento, bairro, cidade, estado, cep,
                           limite_credito, saldo_devedor, tabela_preco_id, rota_id,
                           ultima_compra, ativo
                    FROM clientes
                    WHERE rota_id IN ({placeholders}) AND (deleted_at IS NULL)
                    LIMIT 100
                """)
            ).mappings().all()

        # 3. Produtos do estabelecimento
        produtos_rows = []
        if estab_id:
            produtos_rows = db.session.execute(
                text("""
                    SELECT id, nome, descricao, preco_venda, preco_custo,
                           quantidade, unidade_medida, codigo_barras, imagem_url,
                           categoria_id, ativo, marca
                    FROM produtos
                    WHERE estabelecimento_id = :eid AND ativo = TRUE
                    LIMIT 500
                """),
                {"eid": estab_id}
            ).mappings().all()

        # 4. Tabelas de Preço
        tabelas_rows = []
        if estab_id:
            tabelas_rows = db.session.execute(
                text("SELECT id, nome, ativa FROM tabelas_preco WHERE estabelecimento_id = :eid AND ativa = TRUE"),
                {"eid": estab_id}
            ).mappings().all()

        # 5. Itens das Tabelas
        tabelas_itens_rows = []
        if tabelas_rows:
            tab_ids = ",".join(str(t["id"]) for t in tabelas_rows)
            tabelas_itens_rows = db.session.execute(
                text(f"SELECT tabela_id, produto_id, preco_venda, preco_minimo FROM tabela_preco_itens WHERE tabela_id IN ({tab_ids})")
            ).mappings().all()

        def to_plain(row):
            return dict(row)

        return jsonify({
            "status": "success",
            "data": {
                "rotas": [to_plain(r) for r in q_rotas],
                "clientes": [to_plain(c) for c in clientes_rows],
                "produtos": [to_plain(p) for p in produtos_rows],
                "tabelas_preco": [to_plain(t) for t in tabelas_rows],
                "tabelas_preco_itens": [to_plain(i) for i in tabelas_itens_rows],
            }
        }), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────────
#  KPI DO VENDEDOR
# ─────────────────────────────────────────────
@bp.route("/sfa/kpi/vendedor", methods=["GET"])
def kpi_vendedor():
    """Retorna os indicadores cruciais para o Vendedor (Metas, Positivação, Foco)"""
    try:
        from sqlalchemy import text

        vendedor_id = request.args.get("vendedor_id")
        if not vendedor_id:
            return jsonify({"status": "error", "message": "vendedor_id é obrigatório"}), 400

        hoje = datetime.now(timezone.utc).date()
        ano, mes = hoje.year, hoje.month

        # 1. Meta do Vendedor (raw SQL para evitar filtro automático de tenant)
        meta_row = db.session.execute(
            text("SELECT meta_faturamento, meta_positivacao FROM metas_vendedor WHERE vendedor_id = :vid AND mes = :mes AND ano = :ano LIMIT 1"),
            {"vid": vendedor_id, "mes": mes, "ano": ano}
        ).mappings().first()

        meta_faturamento = float(meta_row["meta_faturamento"]) if meta_row else 0.0
        meta_positivacao = int(meta_row["meta_positivacao"]) if meta_row else 0

        # 2. Vendas do mês atual deste vendedor (raw SQL)
        pedidos_rows = db.session.execute(
            text("""
                SELECT id, total, cliente_id
                FROM pedidos_venda
                WHERE vendedor_id = :vid
                  AND EXTRACT(month FROM data_emissao) = :mes
                  AND EXTRACT(year FROM data_emissao) = :ano
                  AND status != 'cancelado'
                  AND (deleted_at IS NULL)
            """),
            {"vid": vendedor_id, "mes": mes, "ano": ano}
        ).mappings().all()

        faturamento_realizado = sum(float(p["total"]) for p in pedidos_rows)
        clientes_positivados = len(set(p["cliente_id"] for p in pedidos_rows if p["cliente_id"]))

        # 3. Base de clientes na rota do vendedor
        base_row = db.session.execute(
            text("""
                SELECT COUNT(c.id) as total
                FROM clientes c
                JOIN rotas r ON c.rota_id = r.id
                WHERE r.vendedor_id = :vid AND (c.deleted_at IS NULL)
            """),
            {"vid": vendedor_id}
        ).mappings().first()
        base_clientes = int(base_row["total"]) if base_row else 0

        # 4. Tendência Matemática
        _, ultimo_dia_mes = cal_lib.monthrange(ano, mes)
        dias_corridos = max(hoje.day, 1)
        tendencia = (faturamento_realizado / dias_corridos) * ultimo_dia_mes

        # 5. Produto Foco
        foco_rows = db.session.execute(
            text("""
                SELECT pf.produto_id
                FROM produtos_foco pf
                WHERE pf.data_inicio <= :hoje AND pf.data_fim >= :hoje AND pf.ativo = TRUE
            """),
            {"hoje": hoje}
        ).mappings().all()

        foco_vendido = 0.0
        if foco_rows:
            foco_ids = ",".join(str(f["produto_id"]) for f in foco_rows)
            itens_foco = db.session.execute(
                text(f"""
                    SELECT COALESCE(SUM(pvi.quantidade), 0) as total
                    FROM pedido_venda_itens pvi
                    JOIN pedidos_venda pv ON pv.id = pvi.pedido_id
                    WHERE pv.vendedor_id = :vid
                      AND EXTRACT(month FROM pv.data_emissao) = :mes
                      AND EXTRACT(year FROM pv.data_emissao) = :ano
                      AND pv.status != 'cancelado'
                      AND pvi.produto_id IN ({foco_ids})
                """),
                {"vid": vendedor_id, "mes": mes, "ano": ano}
            ).mappings().first()
            foco_vendido = float(itens_foco["total"]) if itens_foco else 0.0

        # 6. Histórico dos últimos pedidos do vendedor
        historico = db.session.execute(
            text("""
                SELECT pv.id, pv.codigo, pv.total, pv.status, pv.data_emissao, c.nome as cliente_nome
                FROM pedidos_venda pv
                LEFT JOIN clientes c ON c.id = pv.cliente_id
                WHERE pv.vendedor_id = :vid AND (pv.deleted_at IS NULL)
                ORDER BY pv.data_emissao DESC
                LIMIT 10
            """),
            {"vid": vendedor_id}
        ).mappings().all()

        return jsonify({
            "status": "success",
            "data": {
                "meta": {
                    "faturamento": meta_faturamento,
                    "positivacao": meta_positivacao or base_clientes
                },
                "realizado": {
                    "faturamento": faturamento_realizado,
                    "tendencia": round(tendencia, 2),
                    "dias_corridos": dias_corridos,
                    "total_dias": ultimo_dia_mes
                },
                "carteira": {
                    "base_clientes": base_clientes,
                    "positivados": clientes_positivados,
                    "nao_compraram": max(0, base_clientes - clientes_positivados)
                },
                "produto_foco": {
                    "total_itens_vendidos": foco_vendido,
                },
                "historico_pedidos": [dict(h) for h in historico]
            }
        }), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────────
#  SYNC PEDIDOS (POST — Vendedor envia pedidos)
# ─────────────────────────────────────────────
@bp.route("/sfa/sync-pedidos", methods=["POST"])
def sync_pedidos():
    """Recebe pedidos feitos offline (Pré-Venda) e persiste no banco."""
    try:
        data = request.json
        pedidos = data.get("pedidos", [])
        estab_id = _estab_id()

        synced = []
        for p_data in pedidos:
            offline_uuid = p_data.get("offline_uuid")

            if offline_uuid:
                existente = db.session.execute(
                    db.text("SELECT id, codigo FROM pedidos_venda WHERE offline_uuid = :uuid LIMIT 1"),
                    {"uuid": offline_uuid}
                ).mappings().first()
                if existente:
                    synced.append(existente["codigo"])
                    continue

            novo_pedido = PedidoVenda(
                estabelecimento_id=estab_id or p_data.get("estabelecimento_id"),
                cliente_id=p_data.get("cliente_id"),
                vendedor_id=p_data.get("vendedor_id"),
                codigo=p_data.get("codigo", f"PED-SFA-{int(datetime.utcnow().timestamp())}"),
                status="pendente",
                subtotal=p_data.get("subtotal", 0),
                desconto=p_data.get("desconto", 0),
                total=p_data.get("total", 0),
                condicao_pagamento=p_data.get("condicao_pagamento"),
                observacoes=p_data.get("observacoes"),
                offline_uuid=offline_uuid,
                data_emissao=datetime.utcnow()
            )
            db.session.add(novo_pedido)
            db.session.flush()

            for i_data in p_data.get("itens", []):
                item = PedidoVendaItem(
                    estabelecimento_id=novo_pedido.estabelecimento_id,
                    pedido_id=novo_pedido.id,
                    produto_id=i_data.get("produto_id"),
                    quantidade=i_data.get("quantidade"),
                    preco_unitario=i_data.get("preco_unitario"),
                    desconto=i_data.get("desconto", 0),
                    total_item=i_data.get("total_item")
                )
                db.session.add(item)

            synced.append(novo_pedido.codigo)

        db.session.commit()
        return jsonify({"status": "success", "message": f"{len(synced)} pedidos sincronizados", "pedidos_sincronizados": synced}), 200
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────────
#  PEDIDOS DO VENDEDOR (Listagem e Detalhes)
# ─────────────────────────────────────────────
@bp.route("/sfa/pedidos", methods=["GET"])
def listar_pedidos_vendedor():
    """Lista pedidos do vendedor com filtro de status."""
    try:
        from sqlalchemy import text
        vendedor_id = request.args.get("vendedor_id")
        status = request.args.get("status")

        sql = """
            SELECT pv.id, pv.codigo, pv.total, pv.status, pv.data_emissao,
                   pv.condicao_pagamento, pv.observacoes, pv.cliente_id,
                   c.nome as cliente_nome
            FROM pedidos_venda pv
            LEFT JOIN clientes c ON c.id = pv.cliente_id
            WHERE pv.vendedor_id = :vid AND (pv.deleted_at IS NULL)
        """
        params = {"vid": vendedor_id}
        if status:
            sql += " AND pv.status = :status"
            params["status"] = status
        sql += " ORDER BY pv.data_emissao DESC LIMIT 50"

        rows = db.session.execute(text(sql), params).mappings().all()
        return jsonify({"status": "success", "data": [dict(r) for r in rows]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/sfa/pedidos/<int:pedido_id>/aprovar", methods=["POST"])
def aprovar_pedido(pedido_id):
    """Backoffice aprova o pedido, reserva limite de crédito e abate estoque."""
    try:
        pedido = PedidoVenda.query.get(pedido_id)
        if not pedido:
            return jsonify({"status": "error", "message": "Pedido não encontrado"}), 404

        if pedido.status != "pendente":
            return jsonify({"status": "error", "message": f"Pedido já está {pedido.status}"}), 400

        cliente = Cliente.query.get(pedido.cliente_id)
        if cliente:
            limite_disponivel = float(cliente.limite_credito or 0) - float(cliente.saldo_devedor or 0)
            if float(pedido.total) > limite_disponivel:
                return jsonify({"status": "error", "message": "Limite de crédito excedido"}), 400
            cliente.saldo_devedor = float(cliente.saldo_devedor or 0) + float(pedido.total)

        for item in pedido.itens:
            produto = Produto.query.get(item.produto_id)
            if produto:
                produto.movimentar_estoque(float(item.quantidade), "saida", f"Pedido {pedido.codigo}", pedido.vendedor_id)

        pedido.status = "faturado"
        db.session.commit()
        return jsonify({"status": "success", "message": "Pedido aprovado e faturado"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────────
#  SFA MANAGEMENT (ADMIN — Gestão de Rotas/Metas)
# ─────────────────────────────────────────────
@bp.route("/sfa/admin/metas", methods=["GET", "POST"])
def admin_metas():
    try:
        estabelecimento_id = getattr(g, "estabelecimento_id", None) or request.args.get("estabelecimento_id", 1)

        if request.method == "POST":
            data = request.json
            vendedor_id = data.get("vendedor_id")
            mes = data.get("mes")
            ano = data.get("ano")
            meta_faturamento = data.get("meta_faturamento", 0)
            meta_positivacao = data.get("meta_positivacao", 0)

            existing = MetaVendedor.query.filter_by(
                vendedor_id=vendedor_id, mes=mes, ano=ano,
                estabelecimento_id=estabelecimento_id
            ).first()

            if existing:
                existing.meta_faturamento = meta_faturamento
                existing.meta_positivacao = meta_positivacao
            else:
                nova = MetaVendedor(
                    estabelecimento_id=estabelecimento_id,
                    vendedor_id=vendedor_id, mes=mes, ano=ano,
                    meta_faturamento=meta_faturamento,
                    meta_positivacao=meta_positivacao
                )
                db.session.add(nova)
            db.session.commit()
            return jsonify({"status": "success", "message": "Meta salva"}), 200
        else:
            mes = request.args.get("mes", datetime.now().month)
            ano = request.args.get("ano", datetime.now().year)
            metas = MetaVendedor.query.filter_by(
                estabelecimento_id=estabelecimento_id, mes=mes, ano=ano
            ).all()
            return jsonify({"status": "success", "data": [m.to_dict() for m in metas]}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/sfa/admin/rotas", methods=["GET", "POST", "PUT"])
def admin_rotas():
    try:
        estabelecimento_id = getattr(g, "estabelecimento_id", None) or request.args.get("estabelecimento_id", 1)

        if request.method in ("POST", "PUT"):
            data = request.json
            rota_id = data.get("id")

            if rota_id:
                rota = Rota.query.get(rota_id)
                if not rota:
                    return jsonify({"status": "error", "message": "Rota não encontrada"}), 404
                rota.nome = data.get("nome", rota.nome)
                rota.vendedor_id = data.get("vendedor_id", rota.vendedor_id)
                rota.dia_semana = data.get("dia_semana", rota.dia_semana)
                rota.ativa = data.get("ativa", rota.ativa)
            else:
                rota = Rota(
                    estabelecimento_id=estabelecimento_id,
                    nome=data.get("nome"),
                    vendedor_id=data.get("vendedor_id"),
                    dia_semana=data.get("dia_semana", 0),
                    ativa=data.get("ativa", True)
                )
                db.session.add(rota)
            db.session.commit()
            return jsonify({"status": "success", "message": "Rota salva", "data": rota.to_dict()}), 200
        else:
            rotas = Rota.query.filter_by(estabelecimento_id=estabelecimento_id).all()
            return jsonify({"status": "success", "data": [r.to_dict() for r in rotas]}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/sfa/admin/rotas/<int:rota_id>", methods=["DELETE"])
def delete_rota(rota_id):
    try:
        rota = Rota.query.get(rota_id)
        if not rota:
            return jsonify({"status": "error", "message": "Rota não encontrada"}), 404
        db.session.delete(rota)
        db.session.commit()
        return jsonify({"status": "success", "message": "Rota removida"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/sfa/admin/focos", methods=["GET", "POST"])
def admin_focos():
    try:
        estabelecimento_id = getattr(g, "estabelecimento_id", None) or request.args.get("estabelecimento_id", 1)

        if request.method == "POST":
            data = request.json
            foco = ProdutoFoco(
                estabelecimento_id=estabelecimento_id,
                produto_id=data.get("produto_id"),
                data_inicio=data.get("data_inicio"),
                data_fim=data.get("data_fim"),
                meta_quantidade=data.get("meta_quantidade"),
                ativo=data.get("ativo", True)
            )
            db.session.add(foco)
            db.session.commit()
            return jsonify({"status": "success", "message": "Produto foco criado", "data": foco.to_dict()}), 200
        else:
            focos = ProdutoFoco.query.filter_by(estabelecimento_id=estabelecimento_id).all()
            return jsonify({"status": "success", "data": [f.to_dict() for f in focos]}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/sfa/admin/focos/<int:foco_id>", methods=["DELETE"])
def delete_foco(foco_id):
    try:
        foco = ProdutoFoco.query.get(foco_id)
        if not foco:
            return jsonify({"status": "error", "message": "Foco não encontrado"}), 404
        db.session.delete(foco)
        db.session.commit()
        return jsonify({"status": "success", "message": "Foco removido"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/sfa/tabelas", methods=["GET"])
def get_tabelas():
    try:
        tabelas = TabelaPreco.query.all()
        return jsonify({"status": "success", "data": [t.to_dict() for t in tabelas]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/sfa/rotas", methods=["GET"])
def get_rotas():
    try:
        vendedor_id = request.args.get("vendedor_id")
        q = Rota.query
        if vendedor_id:
            q = q.filter_by(vendedor_id=vendedor_id)
        rotas = q.all()
        return jsonify({"status": "success", "data": [r.to_dict() for r in rotas]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
