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
    Busca configurações via SQL direto.
    Estratégia Híbrida (Elite):
    1. Tenta buscar TUDO em uma única query (Performance Máxima).
    2. Se falhar (ex: coluna nova não existe), busca item a item (Resiliência Máxima).
    """
    try:
        if not estab_id: return None
        
        # --- TENTATIVA 1: FAST PATH (1 Query) ---
        try:
            # Tenta buscar todas as colunas conhecidas de uma vez
            sql_fast = """
                SELECT 
                    id, estabelecimento_id, 
                    logo_url, logo_base64, cor_principal, tema_escuro, 
                    emitir_nfe, emitir_nfce, formas_pagamento,
                    controlar_validade, alerta_estoque_minimo, dias_alerta_validade, estoque_minimo_padrao,
                    exibir_preco_tela, permitir_venda_sem_estoque, desconto_maximo_percentual,
                    desconto_maximo_funcionario, arredondamento_valores, tempo_sessao_minutos,
                    tentativas_senha_bloqueio, alertas_email, alertas_whatsapp
                FROM configuracoes 
                WHERE estabelecimento_id = :eid 
                LIMIT 1
            """
            row = db.session.execute(text(sql_fast), {"eid": estab_id}).fetchone()
            
            if row:
                # Se sucesso, monta o dict direto (Fast!)
                import json
                formas_pagamento = row[8]
                if isinstance(formas_pagamento, str):
                    try: formas_pagamento = json.loads(formas_pagamento)
                    except: pass

                return {
                    "id": row[0],
                    "estabelecimento_id": row[1],
                    "logo_url": row[2],
                    "logo_base64": row[3],
                    "cor_principal": row[4] or "#007bff",
                    "tema_escuro": bool(row[5]),
                    "emitir_nfe": bool(row[6]),
                    "emitir_nfce": bool(row[7]),
                    "formas_pagamento": formas_pagamento,
                    "controlar_validade": bool(row[9]),
                    "alerta_estoque_minimo": bool(row[10]),
                    "dias_alerta_validade": row[11],
                    "estoque_minimo_padrao": row[12],
                    "exibir_preco_tela": bool(row[13]),
                    "permitir_venda_sem_estoque": bool(row[14]),
                    "desconto_maximo_percentual": float(row[15]) if row[15] is not None else 10.0,
                    "desconto_maximo_funcionario": float(row[16]) if row[16] is not None else 10.0,
                    "arredondamento_valores": bool(row[17]),
                    "tempo_sessao_minutos": row[18],
                    "tentativas_senha_bloqueio": row[19],
                    "alertas_email": bool(row[20]),
                    "alertas_whatsapp": bool(row[21])
                }
        except Exception as e_fast:
            # logger.debug(f"Fast path config falhou (provável schema drift): {e_fast}")
            pass

        # --- TENTATIVA 2: SAFE PATH (Fallback Resiliente) ---
        # Se chegou aqui, a query completa falhou.
        
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
                return r[0] if r and r[0] is not None else default
            except:
                return default

        res["logo_url"] = _fetch_col("logo_url")
        res["logo_base64"] = _fetch_col("logo_base64")
        res["cor_principal"] = _fetch_col("cor_principal", "#007bff")
        res["tema_escuro"] = _fetch_col("tema_escuro", False)
        res["emitir_nfe"] = _fetch_col("emitir_nfe", False)
        res["emitir_nfce"] = _fetch_col("emitir_nfce", True)
        res["formas_pagamento"] = _fetch_col("formas_pagamento")
        
        # Campos de Estoque
        res["controlar_validade"] = _fetch_col("controlar_validade", True)
        res["alerta_estoque_minimo"] = _fetch_col("alerta_estoque_minimo", True)
        res["dias_alerta_validade"] = _fetch_col("dias_alerta_validade", 30)
        res["estoque_minimo_padrao"] = _fetch_col("estoque_minimo_padrao", 10)
        
        # PDV
        res["exibir_preco_tela"] = _fetch_col("exibir_preco_tela", True)
        res["permitir_venda_sem_estoque"] = _fetch_col("permitir_venda_sem_estoque", False)
        res["desconto_maximo_percentual"] = float(_fetch_col("desconto_maximo_percentual", 10.0))
        res["desconto_maximo_funcionario"] = float(_fetch_col("desconto_maximo_funcionario", 10.0))
        res["arredondamento_valores"] = _fetch_col("arredondamento_valores", True)
        
        # Sistema
        res["tempo_sessao_minutos"] = _fetch_col("tempo_sessao_minutos", 30)
        res["tentativas_senha_bloqueio"] = _fetch_col("tentativas_senha_bloqueio", 3)
        res["alertas_email"] = _fetch_col("alertas_email", False)
        res["alertas_whatsapp"] = _fetch_col("alertas_whatsapp", False)
        
        if isinstance(res["formas_pagamento"], str):
            import json
            try: res["formas_pagamento"] = json.loads(res["formas_pagamento"])
            except: pass
        
        return res

    except Exception as e:
        logger.error(f"Erro em get_configuracao_safe: {e}")
        return None

def get_funcionario_safe(func_id):
    """
    Busca o funcionário via SQL direto, evitando colunas ausentes.
    Blindagem de Elite: Aceita func_id como ID (int/str) ou Username.
    """
    try:
        if not func_id: return None
        
        # Tentativa 1: Por ID (Assume que func_id pode ser um ID numérico)
        row = None
        try:
            # Força cast para int se for puramente numérico para evitar erros de tipo no Postgres
            if str(func_id).isdigit():
                row = db.session.execute(
                    text("SELECT id, nome, email, username, estabelecimento_id, cargo FROM funcionarios WHERE id = :fid"),
                    {"fid": int(func_id)}
                ).fetchone()
        except Exception:
            row = None

        # Tentativa 2: Por Username (Se a primeira falhou ou func_id é string literal)
        if not row:
            row = db.session.execute(
                text("SELECT id, nome, email, username, estabelecimento_id, cargo FROM funcionarios WHERE username = :funame"),
                {"funame": str(func_id)}
            ).fetchone()

        if not row:
            logger.warning(f"[get_funcionario_safe] Funcionário não encontrado: {func_id}")
            return None

        res = {
            "id": row[0],
            "nome": row[1],
            "email": row[2],
            "login": row[3], # Mantido para compatibilidade interna
            "username": row[3],
            "estabelecimento_id": row[4],
            "cargo": row[5]
        }

        def _fetch_col(col, default=None):
            try:
                # Se col for login, tenta username primeiro
                target_col = col
                if col == "login": target_col = "username"
                
                r = db.session.execute(
                    text(f"SELECT {target_col} FROM funcionarios WHERE id = :fid"),
                    {"fid": func_id}
                ).fetchone()
                return r[0] if r else default
            except:
                return default

        res["role"] = _fetch_col("role", "FUNCIONARIO")
        res["ativo"] = _fetch_col("ativo", True)
        res["permissoes_json"] = _fetch_col("permissoes_json")

        res["salario"] = _fetch_col("salario")
        res["data_demissao"] = _fetch_col("data_demissao")
        res["foto_url"] = _fetch_col("foto_url")
        
        # Parse permissoes_json if exists
        try:
            import json
            res["permissoes"] = json.loads(res["permissoes_json"]) if res.get("permissoes_json") else {
                "pdv": True, "estoque": True, "compras": False, "financeiro": False, "configuracoes": False
            }
        except:
            res["permissoes"] = {"pdv": True, "estoque": True, "compras": False, "financeiro": False, "configuracoes": False}
        
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
            text("SELECT id, codigo, total, subtotal, desconto, forma_pagamento, cliente_id, funcionario_id, estabelecimento_id, data_venda, valor_recebido, troco FROM vendas WHERE id = :vid"),
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
            "data_venda": row[9],
            "valor_recebido": row[10],
            "troco": row[11]
        }
    except Exception as e:
        logger.error(f"Erro em get_venda_safe: {e}")
        return None

def get_venda_itens_safe(venda_id):
    """
    Busca os itens de uma venda via SQL direto com dados básicos do produto.
    """
    try:
        if not venda_id: return []
        
        sql = """
            SELECT vi.id, vi.produto_id, vi.quantidade, vi.preco_unitario, vi.total_item,
                   p.nome as produto_nome, p.codigo_barras
            FROM venda_itens vi
            JOIN produtos p ON vi.produto_id = p.id
            WHERE vi.venda_id = :vid
        """
        rows = db.session.execute(text(sql), {"vid": venda_id}).fetchall()
        
        return [
            {
                "id": r[0],
                "produto_id": r[1],
                "quantidade": r[2],
                "preco_unitario": r[3],
                "total_item": r[4],
                "produto_nome": r[5],
                "produto_codigo": r[6]
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Erro em get_venda_itens_safe: {e}")
        return []



def get_estabelecimento_full_safe(estabelecimento_id):
    """
    Busca dados completos do estabelecimento via SQL direto, com fallbacks para colunas opcionais.
    Ensina o sistema a retornar a verdade completa (CEP, Complemento, Estado) para o Frontend.
    """
    try:
        # Busca dinâmica de colunas para evitar erros de schema e garantir todos os campos
        # Incluímos um LEFT JOIN com configuracoes para pegar a logo_base64 oficial
        sql = """
            SELECT e.id, e.nome_fantasia, e.razao_social, e.cnpj, e.telefone, e.email, 
                   e.logradouro, e.numero, e.bairro, e.cidade, e.estado, e.cep, e.complemento, e.inscricao_estadual,
                   c.logo_base64
            FROM estabelecimentos e
            LEFT JOIN configuracoes c ON c.estabelecimento_id = e.id
            WHERE e.id = :eid LIMIT 1
        """
        row = db.session.execute(text(sql), {"eid": estabelecimento_id}).fetchone()
        
        if not row: return None
        
        # Mapeamento robusto por índice (baseado no SELECT acima)
        return {
            "id": row[0],
            "nome_fantasia": row[1],
            "razao_social": row[2],
            "cnpj": row[3],
            "telefone": row[4],
            "email": row[5],
            "logradouro": row[6],
            "numero": row[7],
            "bairro": row[8],
            "cidade": row[9],
            "estado": row[10],
            "cep": row[11],
            "complemento": row[12],
            "inscricao_estadual": row[13],
            "logo_base64": row[14]
        }
    except Exception as e:
        # Fallback de emergência caso alguma coluna (ex: cep) ainda não esteja no banco
        from flask import current_app
        current_app.logger.error(f"⚠️ SQL Full Safe falhou: {e}. Tentando modo resiliente.")
        return get_estabelecimento_safe(estabelecimento_id)

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
