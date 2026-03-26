import os
import sys
import time
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine, text

# =====================================================================
# MercadinhoSys - High Performance Sync to Aiven (Hybrid Logic)
# Sincronização em massa idempotente do Docker Local -> Aiven Cloud.
# =====================================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    pass

def _parse_url(url, force_no_ssl=False):
    """Parse URL postgres para dict de parâmetros psycopg2."""
    if not url: return {}
    url = url.replace("postgresql://", "postgres://", 1) if url.startswith("postgresql://") else url
    url_body = url[len("postgres://"):]
    params_str = ""
    if "?" in url_body:
        url_body, params_str = url_body.split("?", 1)

    user_pass, rest = url_body.split("@", 1)
    user, password = (user_pass.split(":", 1) + [""])[:2]
    host_port, dbname = (rest.rsplit("/", 1) + ["postgres"])[:2]
    host, port = (host_port.rsplit(":", 1) + ["5432"])[:2]

    kw = dict(host=host, port=int(port), user=user, password=password,
              dbname=dbname, connect_timeout=30)
    
    params = {}
    for p in params_str.split("&"):
        if "=" in p:
            k, v = p.split("=", 1)
            params[k] = v

    if force_no_ssl:
        kw["sslmode"] = "disable"
    elif "sslmode" in params:
        kw["sslmode"] = params["sslmode"]

    return kw

def force_sync(app=None, silent=False):
    """
    Sincroniza todos os dados do banco local para o Aiven.
    ESTRATÉGIA: Psycopg2 Bulk Upsert (idempotente).
    """
    def log(msg):
        if not silent: print(msg)

    local_url = os.environ.get("DATABASE_URL")
    aiven_url = os.environ.get("AIVEN_DATABASE_URL")

    if not local_url or not aiven_url:
        log("❌ Erro: DATABASE_URL ou AIVEN_DATABASE_URL não encontradas.")
        return {"success": False, "erro": "Configuração ausente"}

    log("\n" + "="*65)
    log("  🚀 MERCADINHOSYS — HIGH-PERFORMANCE HYBRID SYNC")
    log("="*65)

    try:
        lconn = psycopg2.connect(**_parse_url(local_url, force_no_ssl=True))
        aconn = psycopg2.connect(**_parse_url(aiven_url))
        lconn.autocommit = True
        log("  ✅ Conexões OK.")
    except Exception as e:
        log(f"  ❌ Erro de conexão: {e}")
        return {"success": False, "erro": str(e)}

    lcur = lconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    acur = aconn.cursor()

    # Ordem de Tabelas (Precedência de FK)
    TABLES = [
        "estabelecimentos", "fornecedores", "categorias_produto",
        "funcionarios", "configuracoes", "configuracoes_horario",
        "clientes", "produtos", "produto_lotes", "estoque_lotes",
        "caixas", "vendas", "venda_itens", "pagamentos",
        "movimentacao_estoque", "despesas", "contas_pagar", "contas_receber",
        "fiados", "registros_ponto", "movimentacoes_caixa",
        "pedidos_compra", "pedidos_compra_itens",
        "motoristas", "veiculos", "taxas_entrega", "entregas",
        "beneficios", "funcionario_beneficios", "dashboard_metricas"
    ]

    # Verificar quais existem no Aiven
    acur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    aconn.commit()
    aiven_tables = {r[0] for r in acur.fetchall()}

    log("\n  ⏳ Sincronizando tabelas...")
    log(f"  {'Tabela':<35} {'Local':>8} {'Sync':>8}")
    log("  " + "-"*55)

    total_records = 0
    BATCH_SIZE = 1000

    for table in TABLES:
        if table not in aiven_tables:
            continue
        
        try:
            lcur.execute(f'SELECT count(*) as c FROM "{table}"')
            count = lcur.fetchone()['c']
            if count == 0:
                log(f"  {'  ' + table:<35} {'0':>8} {'—':>8}")
                continue

            # Pegar colunas
            lcur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND table_schema='public'")
            cols = [r['column_name'] for r in lcur.fetchall()]
            
            # Sanitizar colunas (Aiven pode estar desatualizado)
            acur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND table_schema='public'")
            aconn.commit()
            aiven_cols = {r[0] for r in acur.fetchall()}
            
            valid_cols = [c for c in cols if c in aiven_cols]
            if not valid_cols: continue
            
            cols_str = ", ".join([f'"{c}"' for c in valid_cols])
            ph = ", ".join(["%s"] * len(valid_cols))
            
            has_id = "id" in valid_cols
            if has_id:
                # OTIMIZAÇÃO: Ignorar colunas virtuais ou de auditoria se necessário
                upd = ", ".join([f'"{c}"=EXCLUDED."{c}"' for c in valid_cols if c != 'id'])
                upsert = f"ON CONFLICT (id) DO UPDATE SET {upd}" if upd else "ON CONFLICT (id) DO NOTHING"
            else:
                upsert = "ON CONFLICT DO NOTHING"

            synced = 0
            offset = 0
            order = "ORDER BY id" if has_id else ""
            
            while offset < count:
                lcur.execute(f'SELECT {cols_str} FROM "{table}" {order} LIMIT %s OFFSET %s', (BATCH_SIZE, offset))
                rows = lcur.fetchall()
                if not rows: break
                
                # Pre-processar para JSON e Deduplicar
                seen = set()
                data = []
                for r in rows:
                    if has_id:
                        if r['id'] in seen: continue
                        seen.add(r['id'])
                    
                    row_data = []
                    for c in valid_cols:
                        val = r[c]
                        if isinstance(val, (dict, list)):
                            val = psycopg2.extras.Json(val)
                        row_data.append(val)
                    data.append(tuple(row_data))

                try:
                    acur.executemany(f'INSERT INTO "{table}" ({cols_str}) VALUES ({ph}) {upsert}', data)
                    aconn.commit()
                    synced += len(data)
                except Exception as e:
                    aconn.rollback()
                    log(f"    ⚠️ Erro no Batch {table}: {str(e)[:50]}")
                    # Fallback row-by-row
                    for row_tuple in data:
                        try:
                            acur.execute(f'INSERT INTO "{table}" ({cols_str}) VALUES ({ph}) {upsert}', row_tuple)
                            aconn.commit()
                            synced += 1
                        except: aconn.rollback()

                offset += BATCH_SIZE

            total_records += synced
            log(f"  {'  ' + table:<35} {count:>8} {synced:>8}")

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            log(f"  ❌ ERRO CRÍTICO NA TABELA {table}:")
            log(error_msg)
            # Continuar para a próxima tabela mesmo se uma falhar
            continue

    log("  " + "-"*55)
    log(f"  🏆 TOTAL SINCRONIZADO: {total_records} registros.\n")
    
    lcur.close(); lconn.close()
    acur.close(); aconn.close()
    
    return {"success": True, "total_registros": total_records}

if __name__ == "__main__":
    force_sync()
