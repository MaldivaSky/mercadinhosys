#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificação de saúde do banco PostgreSQL/Neon (nuvem).
Confere conexão, migrações aplicadas e colunas críticas (ex.: margem_lucro_real).
Uso: no backend, com .env carregado (DATABASE_URL ou NEON_DATABASE_URL)
  python check_db_health.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def get_db_url():
    for key in ["AIVEN_DATABASE_URL", "NEON_DATABASE_URL", "DATABASE_URL_TARGET", "DB_PRIMARY", "DATABASE_URL", "POSTGRES_URL"]:
        url = os.environ.get(key)
        if url:
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
    return None


def main():
    db_url = get_db_url()
    if not db_url:
        print("❌ Nenhuma URL de banco configurada (AIVEN_DATABASE_URL, DATABASE_URL, etc.)")
        sys.exit(1)

    # Evitar imprimir senha
    safe_url = db_url.split("@")[-1] if "@" in db_url else "***"
    print(f"🔍 Verificando banco: ...@{safe_url}")
    print()

    try:
        engine = create_engine(db_url)
    except Exception as e:
        print(f"❌ Erro ao criar engine: {e}")
        sys.exit(1)

    errors = []
    warnings = []
    from sqlalchemy import create_engine, text

    with engine.connect() as conn:
        # 1) Conexão
        try:
            conn.execute(text("SELECT 1"))
            print("✅ Conexão: OK")
        except Exception as e:
            print(f"❌ Conexão: FALHOU - {e}")
            sys.exit(1)

        # 2) Alembic (migrações)
        try:
            r = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = r.fetchone()
            if row:
                print(f"✅ Migrações: aplicadas (revisão atual: {row[0]})")
            else:
                warnings.append("Tabela alembic_version vazia — nenhuma migração aplicada.")
                print("⚠️ Migrações: tabela alembic_version vazia (rode: flask db upgrade)")
        except Exception as e:
            errors.append(f"alembic_version: {e}")
            print(f"❌ Migrações: tabela alembic_version ausente ou erro — {e}")
            print("   → Solução: no servidor (Render), o start.sh deve rodar 'flask db upgrade'.")
            print("   → Localmente contra Neon: export DATABASE_URL=<sua_url_neon> && flask db upgrade")

        # 3) Tabelas críticas
        required_tables = ["estabelecimentos", "funcionarios", "produtos", "vendas", "venda_itens", "configuracoes"]
        for table in required_tables:
            try:
                conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                print(f"✅ Tabela: {table}")
            except Exception as e:
                errors.append(f"Tabela {table}: {e}")
                print(f"❌ Tabela: {table} — {e}")

        # 4) Tabela historico_precos (migração add_historico_precos)
        try:
            conn.execute(text("SELECT 1 FROM historico_precos LIMIT 1"))
            print("✅ Tabela: historico_precos")
        except Exception as e:
            warnings.append(f"historico_precos: {e}")
            print(f"⚠️ Tabela historico_precos ausente — {e}")
            print("   → Rode: flask db upgrade")

        # 5) Coluna margem_lucro_real em venda_itens (migração add_margem_lucro_real)
        try:
            conn.execute(text("SELECT margem_lucro_real FROM venda_itens LIMIT 1"))
            print("✅ Coluna: venda_itens.margem_lucro_real")
        except Exception as e:
            errors.append(f"venda_itens.margem_lucro_real: {e}")
            print(f"❌ Coluna venda_itens.margem_lucro_real ausente — {e}")
            print("   → Rode: flask db upgrade (revisão add_margem_lucro_real)")

    print()
    if errors:
        print("============================================================")
        print("❌ SAÚDE DO BANCO: FALHOU")
        print("   Corrija os itens acima e rode novamente.")
        print("   Em produção (Render): confira se start.sh executa 'flask db upgrade'.")
        print("============================================================")
        sys.exit(1)
    if warnings:
        print("============================================================")
        print("⚠️ SAÚDE: OK com avisos (ver acima)")
        print("============================================================")
        sys.exit(0)
    print("============================================================")
    print("✅ SAÚDE DO BANCO: OK — schema alinhado com o código.")
    print("============================================================")
    sys.exit(0)


if __name__ == "__main__":
    main()
