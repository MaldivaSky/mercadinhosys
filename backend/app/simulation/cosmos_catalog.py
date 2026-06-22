"""
Cosmos Catalog — Catálogo de produtos com EANs reais brasileiros.

A API Cosmos (Bluesoft) tem limite baixo de requisições. Esta camada:
  1. Mantém uma curadoria de 24 EANs reais de produtos brasileiros populares.
  2. Permite enriquecer via Cosmos UMA única vez, salvando em cache JSON.
  3. Funciona 100% offline usando os metadados locais como fallback.

Uso:
    from app.simulation.cosmos_catalog import CosmosCatalog
    catalog = CosmosCatalog.load(fetch=False)   # offline (usa cache/local)
    catalog = CosmosCatalog.load(fetch=True)    # consome quota Cosmos 1x e salva cache
"""
import os
import json
from decimal import Decimal

CACHE_PATH = os.path.join(os.path.dirname(__file__), "cosmos_cache.json")
COSMOS_URL = "https://api.cosmos.bluesoft.com.br/gtins/{gtin}.json"
COSMOS_TOKEN = os.environ.get("COSMOS_TOKEN") or "MVsiut1dwhg12WGhPuTD9Q"

# Limite de segurança para nunca estourar a quota da Cosmos.
COSMOS_MAX_CALLS = 24


# ---------------------------------------------------------------------------
# Curadoria de 24 EANs reais de produtos brasileiros.
# "forn": tipo de fornecedor especializado que distribui o produto.
# "p": preço de venda de referência (R$). "ncm": classificação fiscal.
# ---------------------------------------------------------------------------
REAL_SKUS = [
    # ── Bebidas (Distribuidora de Bebidas) ──
    {"ean": "7894900011517", "n": "Coca-Cola Original 2L",            "marca": "Coca-Cola",  "cat": "Bebidas",    "un": "UN", "p": 12.90, "ncm": "22021000", "forn": "bebidas"},
    {"ean": "7894900700044", "n": "Coca-Cola Zero 2L",               "marca": "Coca-Cola",  "cat": "Bebidas",    "un": "UN", "p": 12.90, "ncm": "22021000", "forn": "bebidas"},
    {"ean": "7891991010917", "n": "Guaraná Antarctica 2L",          "marca": "Antarctica", "cat": "Bebidas",    "un": "UN", "p": 10.50, "ncm": "22021000", "forn": "bebidas"},
    {"ean": "7891149102129", "n": "Cerveja Skol Lata 350ml",        "marca": "Skol",       "cat": "Bebidas",    "un": "UN", "p": 3.80,  "ncm": "22030000", "forn": "bebidas"},
    {"ean": "7896045104314", "n": "Água Mineral Indaiá 500ml",      "marca": "Indaiá",     "cat": "Bebidas",    "un": "UN", "p": 2.50,  "ncm": "22011000", "forn": "bebidas"},

    # ── Mercearia (Distribuidora de Secos e Molhados) ──
    {"ean": "7896006711152", "n": "Arroz Tio João Tipo 1 5kg",      "marca": "Tio João",   "cat": "Mercearia",  "un": "PC", "p": 28.90, "ncm": "10063011", "forn": "mercearia"},
    {"ean": "7896006733105", "n": "Feijão Carioca Camil 1kg",       "marca": "Camil",      "cat": "Mercearia",  "un": "UN", "p": 8.45,  "ncm": "07133399", "forn": "mercearia"},
    {"ean": "7891910000197", "n": "Açúcar União Refinado 1kg",      "marca": "União",      "cat": "Mercearia",  "un": "UN", "p": 4.80,  "ncm": "17019900", "forn": "mercearia"},
    {"ean": "7891107101621", "n": "Óleo de Soja Liza 900ml",        "marca": "Liza",       "cat": "Mercearia",  "un": "UN", "p": 6.90,  "ncm": "15079011", "forn": "mercearia"},
    {"ean": "7896089012736", "n": "Café Pilão Tradicional 500g",    "marca": "Pilão",      "cat": "Mercearia",  "un": "UN", "p": 19.90, "ncm": "09012100", "forn": "mercearia"},
    {"ean": "7896036090244", "n": "Macarrão Espaguete Renata 500g", "marca": "Renata",     "cat": "Mercearia",  "un": "UN", "p": 4.50,  "ncm": "19021900", "forn": "mercearia"},
    {"ean": "7896102501445", "n": "Molho de Tomate Pomarola 340g",  "marca": "Pomarola",   "cat": "Mercearia",  "un": "UN", "p": 3.90,  "ncm": "21032010", "forn": "mercearia"},
    {"ean": "7891150015005", "n": "Maionese Hellmann's 500g",       "marca": "Hellmann's", "cat": "Mercearia",  "un": "UN", "p": 14.50, "ncm": "21039011", "forn": "mercearia"},

    # ── Laticínios (Distribuidora de Frios e Laticínios) ──
    {"ean": "7891000000427", "n": "Leite Condensado Moça 395g",     "marca": "Moça",       "cat": "Laticínios", "un": "UN", "p": 8.90,  "ncm": "04029900", "forn": "laticinios"},
    {"ean": "7891000053508", "n": "Leite em Pó Ninho 380g",         "marca": "Ninho",      "cat": "Laticínios", "un": "UN", "p": 22.90, "ncm": "04022110", "forn": "laticinios"},
    {"ean": "7898215152330", "n": "Leite UHT Integral Italac 1L",   "marca": "Italac",     "cat": "Laticínios", "un": "UN", "p": 5.45,  "ncm": "04012010", "forn": "laticinios"},
    {"ean": "7891097002007", "n": "Manteiga Aviação com Sal 200g",  "marca": "Aviação",    "cat": "Laticínios", "un": "UN", "p": 16.90, "ncm": "04051000", "forn": "laticinios"},

    # ── Limpeza / Higiene (Distribuidora de Limpeza) ──
    {"ean": "7891150064393", "n": "Sabão em Pó OMO Lavagem 1.6kg",  "marca": "OMO",        "cat": "Limpeza",    "un": "PC", "p": 26.90, "ncm": "34022000", "forn": "limpeza"},
    {"ean": "7896098900116", "n": "Detergente Ypê Neutro 500ml",    "marca": "Ypê",        "cat": "Limpeza",    "un": "UN", "p": 2.59,  "ncm": "34022000", "forn": "limpeza"},
    {"ean": "7891022100014", "n": "Esponja de Aço Bombril 8un",     "marca": "Bombril",    "cat": "Limpeza",    "un": "PC", "p": 3.90,  "ncm": "73239900", "forn": "limpeza"},
    {"ean": "7891024134925", "n": "Creme Dental Colgate Total 90g", "marca": "Colgate",    "cat": "Higiene",    "un": "UN", "p": 9.90,  "ncm": "33061000", "forn": "limpeza"},
    {"ean": "7891150080929", "n": "Sabonete Dove Original 90g",     "marca": "Dove",       "cat": "Higiene",    "un": "UN", "p": 4.50,  "ncm": "34011190", "forn": "limpeza"},

    # ── Snacks / Biscoitos (Distribuidora de Doces) ──
    {"ean": "7622300989750", "n": "Biscoito Recheado Oreo 90g",     "marca": "Oreo",       "cat": "Snacks",     "un": "UN", "p": 3.90,  "ncm": "19053100", "forn": "doces"},
    {"ean": "7892840222949", "n": "Chocolate Bis Lacta 126g",       "marca": "Lacta",      "cat": "Snacks",     "un": "UN", "p": 6.50,  "ncm": "18063220", "forn": "doces"},
]


# ---------------------------------------------------------------------------
# Fontes de EANs candidatos para o harvester diário.
#   1) Curados: EANs reais verificados (alta taxa de acerto na Cosmos).
#   2) Gerador por prefixo GS1 Brasil: prefixos de fabricantes reais — o item
#      de 5 dígitos é variado e o check-digit recalculado. Descobre produtos
#      reais ao longo do tempo (misses são registrados p/ não reconsultar).
# ---------------------------------------------------------------------------
GS1_BR_PREFIXES = [
    "7891000",  # Nestlé
    "7894900",  # Coca-Cola
    "7891910",  # União
    "7891149",  # Ambev
    "7896089",  # JDE / Café Pilão
    "7891991",  # Antarctica
    "7896006",  # Camil
    "7891107",  # Cargill / Liza
    "7891150",  # Unilever
    "7896098",  # Ypê
    "7891022",  # Bombril
    "7891024",  # Colgate-Palmolive
    "7898080",  # Italac
    "7896045",  # Indaiá
    "7892840",  # Mondelez Brasil
    "7896036",  # Renata
]


def ean13_check_digit(base12: str) -> str:
    """Calcula o dígito verificador EAN-13 de uma base de 12 dígitos."""
    soma = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(base12))
    return str((10 - (soma % 10)) % 10)


def ean13_is_valid(ean: str) -> bool:
    """Valida um EAN-13 completo (13 dígitos numéricos + check-digit correto)."""
    if not ean or not ean.isdigit() or len(ean) != 13:
        return False
    return ean13_check_digit(ean[:12]) == ean[12]


def normalize_ean(ean: str) -> str:
    """Garante EAN-13 estruturalmente válido. Recalcula o check-digit se preciso."""
    digits = "".join(c for c in str(ean) if c.isdigit())
    if len(digits) >= 13:
        digits = digits[:13]
        return digits if ean13_is_valid(digits) else digits[:12] + ean13_check_digit(digits[:12])
    digits = digits.rjust(12, "0")[:12]
    return digits + ean13_check_digit(digits)


def curated_candidate_eans():
    """EANs reais curados (normalizados)."""
    seen, out = set(), []
    for s in REAL_SKUS:
        e = normalize_ean(s["ean"])
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def iter_candidate_eans(skip: set, quantidade: int, allow_generated: bool = True, seed: int = None):
    """
    Gera até `quantidade` EANs candidatos ainda não consultados (fora de `skip`).
    Prioriza os curados; depois usa o gerador por prefixo GS1 (se permitido).
    """
    import random as _r
    rng = _r.Random(seed)
    entregues = []

    # 1) Curados primeiro (alta taxa de acerto)
    for e in curated_candidate_eans():
        if len(entregues) >= quantidade:
            return entregues
        if e not in skip:
            skip.add(e)
            entregues.append(e)

    if not allow_generated:
        return entregues

    # 2) Gerador por prefixo GS1 — tenta itens aleatórios dentro de cada prefixo
    tentativas, max_tentativas = 0, quantidade * 500
    while len(entregues) < quantidade and tentativas < max_tentativas:
        tentativas += 1
        prefixo = rng.choice(GS1_BR_PREFIXES)
        item = str(rng.randint(0, 99999)).zfill(12 - len(prefixo))
        base12 = (prefixo + item)[:12]
        ean = base12 + ean13_check_digit(base12)
        if ean not in skip:
            skip.add(ean)
            entregues.append(ean)
    return entregues


class CosmosCatalog:
    """Catálogo de produtos com EANs reais, com enriquecimento Cosmos opcional."""

    def __init__(self, skus):
        self.skus = skus

    def __iter__(self):
        return iter(self.skus)

    def __len__(self):
        return len(self.skus)

    # -- carregamento -------------------------------------------------------
    @classmethod
    def load(cls, fetch: bool = False):
        """
        Retorna o catálogo enriquecido.
        fetch=False  -> usa cosmos_cache.json se existir, senão metadados locais.
        fetch=True   -> consulta a Cosmos (1x, máx COSMOS_MAX_CALLS) e grava o cache.
        """
        base = cls._base_skus()

        if fetch:
            enriched = cls._fetch_and_cache(base)
            return cls(enriched)

        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r", encoding="utf-8") as fh:
                    cached = json.load(fh)
                if cached:
                    print(f"[COSMOS] Catálogo carregado do cache ({len(cached)} itens).")
                    return cls(cached)
            except Exception as e:
                print(f"[COSMOS] Falha ao ler cache ({e}). Usando metadados locais.")

        print(f"[COSMOS] Usando metadados locais ({len(base)} EANs reais, sem consumir quota).")
        return cls(base)

    @staticmethod
    def _base_skus():
        """Normaliza os EANs e devolve a curadoria local."""
        out = []
        for s in REAL_SKUS:
            item = dict(s)
            item["ean"] = normalize_ean(s["ean"])
            item["fonte"] = "local"
            item["imagem"] = ""
            item["marca"] = s.get("marca", "")  # mantém a marca real curada (Cosmos pode sobrescrever no fetch)
            out.append(item)
        return out

    @classmethod
    def _fetch_and_cache(cls, base):
        """Consulta a Cosmos respeitando o limite e grava o resultado em cache."""
        try:
            import requests
        except ImportError:
            print("[COSMOS] 'requests' indisponível. Mantendo metadados locais.")
            return base

        headers = {
            "X-Cosmos-Token": COSMOS_TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "MercadinhoSys-Seeder",
        }
        enriched, calls = [], 0
        for item in base:
            data = dict(item)
            if calls < COSMOS_MAX_CALLS:
                calls += 1
                try:
                    resp = requests.get(COSMOS_URL.format(gtin=item["ean"]), headers=headers, timeout=10)
                    if resp.status_code == 200:
                        j = resp.json()
                        data["n"] = j.get("description") or item["n"]
                        data["marca"] = (j.get("brand") or {}).get("name", "")
                        data["imagem"] = j.get("thumbnail") or ""
                        data["ncm"] = ((j.get("ncm") or {}).get("code") or item["ncm"])
                        data["fonte"] = "cosmos"
                        print(f"[COSMOS] OK {item['ean']} -> {data['n']}")
                    elif resp.status_code == 429:
                        print("[COSMOS] Limite (429) atingido. Interrompendo chamadas.")
                        calls = COSMOS_MAX_CALLS  # bloqueia novas chamadas
                    else:
                        print(f"[COSMOS] {item['ean']} status {resp.status_code}; usando local.")
                except Exception as e:
                    print(f"[COSMOS] Erro {item['ean']} ({e}); usando local.")
            enriched.append(data)

        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as fh:
                json.dump(enriched, fh, ensure_ascii=False, indent=2)
            print(f"[COSMOS] Cache gravado em {CACHE_PATH} ({calls} chamadas usadas).")
        except Exception as e:
            print(f"[COSMOS] Falha ao gravar cache: {e}")

        return enriched
