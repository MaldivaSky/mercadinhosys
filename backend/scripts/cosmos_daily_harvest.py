"""
Cosmos Daily Harvest — Coletor diário do catálogo mestre de produtos.

Todo dia consome o limite da API Cosmos (padrão 24 chamadas) para cadastrar
produtos com EAN REAL na tabela global `catalogo_mestre`. Operação ADITIVA e
SEGURA: nunca apaga ou reseta dados — apenas insere novos registros.

  - Pula EANs já consultados (encontrados ou 404) para não desperdiçar quota.
  - Para imediatamente se a Cosmos devolver 429 (limite atingido).
  - Registra 404 como 'nao_encontrado' para nunca reconsultar o mesmo EAN.

Uso:
    python scripts/cosmos_daily_harvest.py                 # 24 EANs (padrão)
    python scripts/cosmos_daily_harvest.py --limit 24
    python scripts/cosmos_daily_harvest.py --no-generated  # só EANs curados
"""
import os
import sys
import json
import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation

# ── setup de paths e ambiente ──────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

import requests
from app import create_app
from app.models import db, CatalogoMestre
from app.simulation.cosmos_catalog import iter_candidate_eans, COSMOS_TOKEN, COSMOS_URL, COSMOS_MAX_CALLS

DEFAULT_LIMIT = int(os.environ.get("COSMOS_DAILY_LIMIT", "24"))


def _to_decimal(v):
    try:
        return Decimal(str(v)) if v not in (None, "", 0) else None
    except (InvalidOperation, TypeError):
        return None


def fetch_one(ean: str):
    """Consulta um EAN na Cosmos. Retorna (http_status, dados|None)."""
    headers = {
        "X-Cosmos-Token": COSMOS_TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "MercadinhoSys-Harvester",
    }
    resp = requests.get(COSMOS_URL.format(gtin=ean), headers=headers, timeout=15)
    if resp.status_code == 200:
        return 200, resp.json()
    return resp.status_code, None


def parse_cosmos(ean: str, j: dict) -> dict:
    """Extrai campos relevantes da resposta da Cosmos (best-effort)."""
    brand = j.get("brand") or {}
    ncm = j.get("ncm") or {}
    gpc = j.get("gpc") or {}
    category = j.get("category") or {}
    return {
        "ean": ean,
        "nome": j.get("description") or j.get("title") or "",
        "marca": brand.get("name") or "",
        "fabricante": brand.get("name") or "",
        "ncm": (ncm.get("code") or "")[:8],
        "categoria": gpc.get("description") or category.get("name") or "Geral",
        "unidade": "UN",
        "preco_referencia": _to_decimal(j.get("avg_price") or j.get("max_price")),
        "imagem_url": j.get("thumbnail") or "",
    }


def run(limit: int, allow_generated: bool):
    app = create_app()
    with app.app_context():
        # Garante a existência da tabela (idempotente, não apaga nada)
        CatalogoMestre.__table__.create(bind=db.engine, checkfirst=True)

        # EANs já consultados (encontrados + não encontrados) → não reconsultar
        skip = {row[0] for row in db.session.query(CatalogoMestre.ean).all()}
        antes = len(skip)
        print(f"[HARVEST] Catálogo atual: {antes} EANs já consultados.")

        limite_efetivo = min(limit, COSMOS_MAX_CALLS)
        seed = int(datetime.now().strftime("%Y%m%d"))  # determinístico por dia
        candidatos = iter_candidate_eans(skip, limite_efetivo, allow_generated, seed=seed)
        print(f"[HARVEST] {len(candidatos)} EANs candidatos para consultar hoje (limite {limite_efetivo}).")

        encontrados, nao_encontrados, chamadas = 0, 0, 0
        for ean in candidatos:
            chamadas += 1
            try:
                status, j = fetch_one(ean)
            except requests.RequestException as e:
                print(f"[HARVEST] {ean} erro de rede ({e}); abortando para preservar quota.")
                break

            if status == 429:
                print("[HARVEST] Limite diário da Cosmos atingido (429). Encerrando.")
                break

            if status == 200 and j:
                dados = parse_cosmos(ean, j)
                db.session.add(CatalogoMestre(
                    **dados, fonte="cosmos", status="encontrado",
                    payload_json=json.dumps(j, ensure_ascii=False)[:50000],
                    consultado_em=datetime.utcnow(),
                ))
                encontrados += 1
                print(f"[HARVEST] OK  {ean} -> {dados['nome'][:50]}")
            else:
                db.session.add(CatalogoMestre(
                    ean=ean, fonte="cosmos", status="nao_encontrado",
                    consultado_em=datetime.utcnow(),
                ))
                nao_encontrados += 1
                print(f"[HARVEST] --  {ean} (HTTP {status})")

            db.session.commit()  # commit incremental: nunca perde o que já coletou

        total = db.session.query(CatalogoMestre).filter_by(status="encontrado").count()
        print("\n" + "=" * 60)
        print(f"[HARVEST] Chamadas: {chamadas} | Encontrados hoje: {encontrados} | 404: {nao_encontrados}")
        print(f"[HARVEST] Catálogo mestre agora tem {total} produtos reais.")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Harvester diário do catálogo Cosmos")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Máximo de chamadas Cosmos hoje")
    parser.add_argument("--no-generated", action="store_true", help="Usar apenas EANs curados (sem gerador GS1)")
    args = parser.parse_args()
    run(limit=args.limit, allow_generated=not args.no_generated)


if __name__ == "__main__":
    main()
