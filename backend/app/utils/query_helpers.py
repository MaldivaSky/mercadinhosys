from sqlalchemy import func, extract, text
from app.models import db
import logging
import traceback

logger = logging.getLogger(__name__)

def get_hour_extract(column):
    """
    Returns the dialect-specific expression to extract the hour.
    Casts to Integer for cross-database consistency.
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.cast(func.strftime('%H', column), db.Integer)
    return func.cast(extract('hour', column), db.Integer)

def get_dow_extract(column):
    """
    Returns the dialect-specific expression to extract the day of week (0-6).
    PostgreSQL: 'dow' (0=Sunday)
    SQLite: '%w' (0=Sunday)
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.cast(func.strftime('%w', column), db.Integer)
    return func.cast(extract('dow', column), db.Integer)

def get_year_extract(column):
    """
    Returns the dialect-specific expression to extract the year.
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.cast(func.strftime('%Y', column), db.Integer)
    return func.cast(extract('year', column), db.Integer)

def get_month_extract(column):
    """
    Returns the dialect-specific expression to extract the month (1-12).
    """
    engine_name = db.engine.name
    if engine_name == 'sqlite':
        return func.cast(func.strftime('%m', column), db.Integer)
    return func.cast(extract('month', column), db.Integer)

def get_estabelecimento_safe(estab_id):
    """
    Busca o estabelecimento via SQL direto, evitando colunas ausentes.
    Retorna um dicionário com os dados ou None se não encontrado.
    """
    try:
        if not estab_id: return None
        
        # Colunas core garantidas
        row = db.session.execute(
            text("SELECT id, nome_fantasia, razao_social, cnpj, telefone, email, ativo FROM estabelecimentos WHERE id = :eid"),
            {"eid": estab_id}
        ).fetchone()

        if not row: return None

        res = {
            "id": row[0],
            "nome_fantasia": row[1],
            "razao_social": row[2],
            "cnpj": row[3],
            "telefone": row[4],
            "email": row[5],
            "ativo": row[6]
        }

        # Busca colunas extras de forma isolada
        def _fetch_col(col, default=None):
            try:
                r = db.session.execute(
                    text(f"SELECT {col} FROM estabelecimentos WHERE id = :eid"),
                    {"eid": estab_id}
                ).fetchone()
                return r[0] if r else default
            except:
                return default

        res["plano"] = _fetch_col("plano", "Basic")
        res["plano_status"] = _fetch_col("plano_status", "experimental")
        res["vencimento_assinatura"] = _fetch_col("vencimento_assinatura")
        res["cep"] = _fetch_col("cep", "00000-000")
        res["logradouro"] = _fetch_col("logradouro")
        res["numero"] = _fetch_col("numero")
        res["bairro"] = _fetch_col("bairro")
        res["cidade"] = _fetch_col("cidade")
        res["estado"] = _fetch_col("estado")
        res["pais"] = _fetch_col("pais", "Brasil")
        
        return res
    except Exception as e:
        logger.error(f"Erro em get_estabelecimento_safe: {e}")
        return None

def get_configuracao_safe(estab_id):
    """
    Busca configurações via SQL direto, evitando colunas ausentes.
    """
    try:
        if not estab_id: return None
        
        row = db.session.execute(
            text("SELECT id, estabelecimento_id FROM configuracoes WHERE estabelecimento_id = :eid"),
            {"eid": estab_id}
        ).fetchone()

        if not row: return None

        res = {
            "id": row[0],
            "estabelecimento_id": row[1]
        }

        def _fetch_col(col, default=None):
            try:
                r = db.session.execute(
                    text(f"SELECT {col} FROM configuracoes WHERE estabelecimento_id = :eid"),
                    {"eid": estab_id}
                ).fetchone()
                return r[0] if r else default
            except:
                return default

        res["logo_url"] = _fetch_col("logo_url")
        res["logo_base64"] = _fetch_col("logo_base64")
        res["cor_principal"] = _fetch_col("cor_principal", "#2563eb")
        res["tema_escuro"] = _fetch_col("tema_escuro", False)
        res["emitir_nfe"] = _fetch_col("emitir_nfe", False)
        res["emitir_nfce"] = _fetch_col("emitir_nfce", True)
        res["formas_pagamento"] = _fetch_col("formas_pagamento")
        
        return res
    except Exception as e:
        logger.error(f"Erro em get_configuracao_safe: {e}")
        return None

def get_funcionario_safe(func_id):
    """
    Busca o funcionário via SQL direto, evitando colunas ausentes.
    """
    try:
        if not func_id: return None
        
        row = db.session.execute(
            text("SELECT id, nome, email, login, estabelecimento_id, cargo, ativo FROM funcionarios WHERE id = :fid"),
            {"fid": func_id}
        ).fetchone()

        if not row: return None

        res = {
            "id": row[0],
            "nome": row[1],
            "email": row[2],
            "login": row[3],
            "estabelecimento_id": row[4],
            "cargo": row[5],
            "ativo": row[6]
        }

        def _fetch_col(col, default=None):
            try:
                r = db.session.execute(
                    text(f"SELECT {col} FROM funcionarios WHERE id = :fid"),
                    {"fid": func_id}
                ).fetchone()
                return r[0] if r else default
            except:
                return default

        res["salario"] = _fetch_col("salario")
        res["data_demissao"] = _fetch_col("data_demissao")
        res["foto_url"] = _fetch_col("foto_url")
        
        return res
    except Exception as e:
        logger.error(f"Erro em get_funcionario_safe: {e}")
        return None

def get_produto_safe(prod_id):
    """
    Busca o produto via SQL direto, evitando colunas ausentes.
    """
    try:
        if not prod_id: return None
        
        row = db.session.execute(
            text("SELECT id, nome, preco_venda, preco_custo, quantidade, ativo, estabelecimento_id FROM produtos WHERE id = :pid"),
            {"pid": prod_id}
        ).fetchone()

        if not row: return None

        res = {
            "id": row[0],
            "nome": row[1],
            "preco_venda": row[2],
            "preco_custo": row[3],
            "quantidade": row[4],
            "ativo": row[5],
            "estabelecimento_id": row[6]
        }

        def _fetch_col(col, default=None):
            try:
                r = db.session.execute(
                    text(f"SELECT {col} FROM produtos WHERE id = :pid"),
                    {"pid": prod_id}
                ).fetchone()
                return r[0] if r else default
            except:
                return default

        res["codigo_barras"] = _fetch_col("codigo_barras")
        res["margem_lucro"] = _fetch_col("margem_lucro")
        res["classificacao_abc"] = _fetch_col("classificacao_abc")
        res["unidade_medida"] = _fetch_col("unidade_medida", "UN")
        res["categoria_id"] = _fetch_col("categoria_id")
        
        return res
    except Exception as e:
        logger.error(f"Erro em get_produto_safe: {e}")
        return None

def get_cliente_safe(cli_id):
    """
    Busca o cliente via SQL direto.
    """
    try:
        if not cli_id: return None
        row = db.session.execute(
            text("SELECT id, nome, email, cpf, telefone, estabelecimento_id FROM clientes WHERE id = :cid"),
            {"cid": cli_id}
        ).fetchone()
        if not row: return None
        return {
            "id": row[0],
            "nome": row[1],
            "email": row[2],
            "cpf": row[3],
            "telefone": row[4],
            "estabelecimento_id": row[5]
        }
    except Exception as e:
        logger.error(f"Erro em get_cliente_safe: {e}")
        return None

def get_venda_safe(venda_id):
    """
    Busca a venda via SQL direto.
    """
    try:
        if not venda_id: return None
        row = db.session.execute(
            text("SELECT id, codigo, total, subtotal, desconto, forma_pagamento, cliente_id, funcionario_id, estabelecimento_id, data_venda FROM vendas WHERE id = :vid"),
            {"vid": venda_id}
        ).fetchone()
        if not row: return None
        return {
            "id": row[0],
            "codigo": row[1],
            "total": row[2],
            "subtotal": row[3],
            "desconto": row[4],
            "forma_pagamento": row[5],
            "cliente_id": row[6],
            "funcionario_id": row[7],
            "estabelecimento_id": row[8],
            "data_venda": row[9]
        }
    except Exception as e:
        logger.error(f"Erro em get_venda_safe: {e}")
        return None

def get_first_estabelecimento_id_safe():
    """
    Busca o ID do primeiro estabelecimento via SQL direto.
    """
    try:
        row = db.session.execute(text("SELECT id FROM estabelecimentos LIMIT 1")).fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Erro em get_first_estabelecimento_id_safe: {e}")
        return None
