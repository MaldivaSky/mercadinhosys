# app/services/view_schema_service.py
"""
Motor de Renderização Contextual (Context-Aware Rendering Engine).

O frontend NÃO decide o que exibir: ele renderiza o View Schema resolvido aqui.
A resolução é uma cascata de 3 níveis:

  1. Global (Sistema)  → tabela view_registry (seed a partir deste catálogo).
                         Define QUAIS campos/métricas existem e para quais
                         segmentos valem.
  2. Tenant (Loja)     → Estabelecimento.segmento + overrides em
                         Estabelecimento.configuracoes_json["view_schema"]
                         (ligar/desligar campos e métricas, opções custom).
  3. Produto           → atributos_json, tipo_item, controlar_estoque e
                         controlar_validade de cada produto (aplicado pelo
                         frontend por item; o schema informa as regras).

Nada de "if validade" hardcoded em tela: quem quiser saber se validade existe
pergunta ao schema.
"""
import json
import time

from app import db
from app.models import Estabelecimento, ViewRegistry

# ==============================================================================
# SEGMENTOS DE NEGÓCIO
# ==============================================================================
SEGMENTOS = {
    "mercearia": {
        "nome": "Mercearia / Supermercado",
        "descricao": "Alimentos e bebidas, com controle de validade e lotes (FIFO).",
        "icone": "shopping-basket",
        "flags": {
            "usa_validade": True, "usa_lotes": True, "usa_servicos": False,
            "usa_grade": False, "usa_dimensoes": False, "usa_embalagens": True,
        },
        "unidades": ["un", "kg", "g", "l", "ml", "cx", "pct", "fardo", "duzia", "bandeja"],
        "exemplos": {
            "nome": "Ex: Arroz Tio João 5kg",
            "categoria": "Ex: Alimentos, Bebidas, Limpeza...",
            "marca": "Ex: Nestlé",
        },
    },
    "vestuario": {
        "nome": "Vestuário / Moda",
        "descricao": "Roupas e calçados: coleções, tamanhos, cores e grades.",
        "icone": "shirt",
        "flags": {
            "usa_validade": False, "usa_lotes": False, "usa_servicos": False,
            "usa_grade": True, "usa_dimensoes": False, "usa_embalagens": False,
        },
        "unidades": ["un", "par", "conjunto", "kit"],
        "exemplos": {
            "nome": "Ex: Camiseta Básica Algodão",
            "categoria": "Ex: Camisetas, Calças, Vestidos...",
            "marca": "Ex: Hering",
        },
    },
    "construcao": {
        "nome": "Material de Construção",
        "descricao": "Caixas, fardos, tonéis e medidas (largura, espessura, polegadas, diâmetro).",
        "icone": "hammer",
        "flags": {
            "usa_validade": False, "usa_lotes": False, "usa_servicos": False,
            "usa_grade": False, "usa_dimensoes": True, "usa_embalagens": True,
        },
        "unidades": ["un", "cx", "pct", "fardo", "tonel", "barrica", "saco", "lata",
                     "galao", "balde", "rolo", "barra", "m", "m2", "m3", "kg", "t", "milheiro"],
        "exemplos": {
            "nome": "Ex: Cimento CP-II 50kg",
            "categoria": "Ex: Cimento, Tintas, Ferragens...",
            "marca": "Ex: Votorantim",
        },
    },
    "autopecas": {
        "nome": "Moto Peças / Oficina",
        "descricao": "Peças com compatibilidade de veículo e serviços (troca de óleo, reparo, mecânica).",
        "icone": "wrench",
        "flags": {
            "usa_validade": False, "usa_lotes": False, "usa_servicos": True,
            "usa_grade": False, "usa_dimensoes": True, "usa_embalagens": False,
        },
        "unidades": ["un", "par", "kit", "jogo", "l", "ml", "m"],
        "exemplos": {
            "nome": "Ex: Kit Relação CG 160",
            "categoria": "Ex: Motor, Suspensão, Elétrica...",
            "marca": "Ex: Honda",
            "nome_servico": "Ex: Troca de óleo com filtro",
            "categoria_servico": "Ex: Manutenção, Mecânica...",
        },
    },
    "generico": {
        "nome": "Comércio Geral",
        "descricao": "Perfil neutro: liga tudo que precisar pelas configurações.",
        "icone": "store",
        "flags": {
            "usa_validade": True, "usa_lotes": True, "usa_servicos": True,
            "usa_grade": False, "usa_dimensoes": False, "usa_embalagens": True,
        },
        "unidades": ["un", "kg", "g", "l", "ml", "cx", "pct", "fardo", "duzia",
                     "par", "kit", "m", "m2", "rolo"],
        "exemplos": {
            "nome": "Ex: Nome do item",
            "categoria": "Ex: Categoria do produto",
            "marca": "Ex: Marca / Fabricante",
            "nome_servico": "Ex: Nome do serviço",
            "categoria_servico": "Ex: Categoria do serviço",
        },
    },
}

# Fallback aplicado a todo segmento sem par nome_servico/categoria_servico
# explícito: reaproveita os exemplos de produto (evita repetir os mesmos 2
# textos em cada segmento que habilita serviços).
_EXEMPLOS_SERVICO_PADRAO = {
    "nome_servico": "Ex: Nome do serviço",
    "categoria_servico": "Ex: Categoria do serviço",
}
for _seg in SEGMENTOS.values():
    for _chave, _valor in _EXEMPLOS_SERVICO_PADRAO.items():
        _seg["exemplos"].setdefault(_chave, _valor)

SEGMENTO_PADRAO = "mercearia"

# ==============================================================================
# CATÁLOGO GLOBAL DE CAMPOS (seed do view_registry, escopo='campo')
#
# origem: 'coluna'   → campo nativo da tabela produtos (o form só liga/desliga)
#         'atributo' → persiste em produtos.atributos_json (dinâmico)
# tipos:  text | textarea | number | select | multiselect | boolean | date
# aplica_tipo_item: limita o campo a 'produto' ou 'servico' (ausente = ambos)
# ==============================================================================
CAMPOS_PADRAO = [
    # ---- Núcleo (colunas nativas, visíveis em todo segmento) ----
    {"chave": "codigo_barras", "label": "Código de Barras", "tipo": "text", "grupo": "identificacao",
     "origem": "coluna", "segmentos": ["*"], "aplica_tipo_item": ["produto"], "ordem": 10},
    {"chave": "marca", "label": "Marca / Fabricante", "tipo": "text", "grupo": "identificacao",
     "origem": "coluna", "segmentos": ["*"], "ordem": 20},
    {"chave": "unidade_medida", "label": "Unidade de Medida", "tipo": "select", "grupo": "identificacao",
     "origem": "coluna", "segmentos": ["*"], "aplica_tipo_item": ["produto"], "ordem": 30},
    {"chave": "fiscal", "label": "Tributação (NFC-e / NF-e)", "tipo": "grupo_fiscal", "grupo": "fiscal",
     "origem": "coluna", "segmentos": ["*"], "aplica_tipo_item": ["produto"], "ordem": 40},
    {"chave": "quantidade_minima", "label": "Qtd. Mínima (Alerta)", "tipo": "number", "grupo": "estoque",
     "origem": "coluna", "segmentos": ["*"], "aplica_tipo_item": ["produto"], "ordem": 50},
    {"chave": "controlar_validade", "label": "Controlar Validade", "tipo": "boolean", "grupo": "estoque",
     "origem": "coluna", "segmentos": ["mercearia", "generico"], "aplica_tipo_item": ["produto"], "ordem": 60},
    {"chave": "imagem_url", "label": "URL da Imagem", "tipo": "text", "grupo": "detalhes",
     "origem": "coluna", "segmentos": ["*"], "ordem": 70},

    # ---- Vestuário ----
    {"chave": "colecao", "label": "Coleção", "tipo": "text", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["vestuario"], "placeholder": "Ex: Verão 2026", "ordem": 100},
    {"chave": "genero", "label": "Gênero", "tipo": "select", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["vestuario"],
     "opcoes": ["Unissex", "Feminino", "Masculino", "Infantil"], "ordem": 110},
    {"chave": "tamanhos", "label": "Grade de Tamanhos", "tipo": "multiselect", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["vestuario"],
     "opcoes": ["PP", "P", "M", "G", "GG", "XG", "34", "36", "38", "40", "42", "44", "46", "48"],
     "ajuda": "Tamanhos disponíveis desta peça (grade).", "ordem": 120},
    {"chave": "cores", "label": "Cores", "tipo": "multiselect", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["vestuario"],
     "opcoes": ["Preto", "Branco", "Cinza", "Azul", "Vermelho", "Verde", "Amarelo", "Rosa", "Marrom", "Bege", "Estampado"],
     "permite_custom": True, "ordem": 130},
    {"chave": "tecido", "label": "Tecido / Material", "tipo": "text", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["vestuario"], "placeholder": "Ex: Algodão, Jeans, Poliéster", "ordem": 140},

    # ---- Construção: embalagem e dimensões ----
    {"chave": "embalagem", "label": "Tipo de Embalagem", "tipo": "select", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["construcao", "mercearia", "generico"],
     "opcoes": ["Unidade", "Caixa", "Fardo", "Pacote", "Tonel", "Barrica", "Saco", "Lata", "Galão", "Balde", "Rolo", "Barra", "Milheiro"],
     "ordem": 200},
    {"chave": "itens_por_embalagem", "label": "Itens por Embalagem", "tipo": "number", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["construcao", "mercearia", "generico"],
     "ajuda": "Fator de conversão: quantas unidades avulsas compõem a embalagem.", "ordem": 210},
    {"chave": "largura_mm", "label": "Largura", "tipo": "number", "grupo": "dimensoes",
     "origem": "atributo", "segmentos": ["construcao"], "unidade": "mm", "ordem": 220},
    {"chave": "espessura_mm", "label": "Espessura", "tipo": "number", "grupo": "dimensoes",
     "origem": "atributo", "segmentos": ["construcao"], "unidade": "mm", "ordem": 230},
    {"chave": "comprimento_m", "label": "Comprimento", "tipo": "number", "grupo": "dimensoes",
     "origem": "atributo", "segmentos": ["construcao"], "unidade": "m", "ordem": 240},
    {"chave": "diametro_pol", "label": "Diâmetro", "tipo": "number", "grupo": "dimensoes",
     "origem": "atributo", "segmentos": ["construcao", "autopecas"], "unidade": "pol", "ordem": 250},
    {"chave": "raio_mm", "label": "Raio", "tipo": "number", "grupo": "dimensoes",
     "origem": "atributo", "segmentos": ["construcao"], "unidade": "mm", "ordem": 260},
    {"chave": "peso_kg", "label": "Peso", "tipo": "number", "grupo": "dimensoes",
     "origem": "atributo", "segmentos": ["construcao", "autopecas"], "unidade": "kg", "ordem": 270},

    # ---- Moto peças ----
    {"chave": "montadora", "label": "Montadora", "tipo": "select", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["autopecas"],
     "opcoes": ["Honda", "Yamaha", "Suzuki", "Kawasaki", "BMW", "Shineray", "Haojue", "Royal Enfield", "Outra"],
     "permite_custom": True, "aplica_tipo_item": ["produto"], "ordem": 300},
    {"chave": "veiculo_compativel", "label": "Veículos Compatíveis", "tipo": "text", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["autopecas"],
     "placeholder": "Ex: CG 160 2016+, Fazer 250", "aplica_tipo_item": ["produto"], "ordem": 310},
    {"chave": "numero_oem", "label": "Código OEM / Original", "tipo": "text", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["autopecas"], "aplica_tipo_item": ["produto"], "ordem": 320},
    {"chave": "posicao", "label": "Posição", "tipo": "select", "grupo": "atributos",
     "origem": "atributo", "segmentos": ["autopecas"],
     "opcoes": ["Dianteira", "Traseira", "Esquerda", "Direita", "Motor", "Transmissão", "Elétrica"],
     "aplica_tipo_item": ["produto"], "ordem": 330},

    # ---- Serviços (qualquer segmento com usa_servicos) ----
    {"chave": "duracao_minutos", "label": "Duração Estimada", "tipo": "number", "grupo": "servico",
     "origem": "atributo", "segmentos": ["autopecas", "generico"], "unidade": "min",
     "aplica_tipo_item": ["servico"], "ordem": 400},
    {"chave": "garantia_dias", "label": "Garantia", "tipo": "number", "grupo": "servico",
     "origem": "atributo", "segmentos": ["autopecas", "generico"], "unidade": "dias",
     "aplica_tipo_item": ["servico"], "ordem": 410},
    {"chave": "exige_agendamento", "label": "Exige Agendamento", "tipo": "boolean", "grupo": "servico",
     "origem": "atributo", "segmentos": ["autopecas", "generico"],
     "aplica_tipo_item": ["servico"], "ordem": 420},
]

# ==============================================================================
# CATÁLOGO GLOBAL DE MÉTRICAS / KPIs (seed do view_registry, escopo='metrica')
#
# escopo_ui: 'card'   → cards principais da página de produtos
#            'painel' → painéis analíticos (ABC, giro, validade)
# fonte: caminho (dot-path) dentro do objeto de estatísticas do backend
# ==============================================================================
METRICAS_PADRAO = [
    {"chave": "total_produtos", "titulo": "Total Produtos", "subtitulo": "Catálogo completo",
     "escopo_ui": "card", "fonte": "total_produtos", "formato": "int", "icone": "package",
     "tema": "blue", "filtro": "all", "segmentos": ["*"], "ordem": 10},
    {"chave": "estoque_normal", "titulo": "Estoque Normal", "subtitulo": "% do total",
     "escopo_ui": "card", "fonte": "produtos_normal", "formato": "int", "icone": "target",
     "tema": "emerald", "filtro": "normal", "segmentos": ["*"], "ordem": 20},
    {"chave": "baixo_estoque", "titulo": "Baixo Estoque", "subtitulo": "Requer atenção",
     "escopo_ui": "card", "fonte": "produtos_baixo_estoque", "formato": "int", "icone": "alert",
     "tema": "amber", "filtro": "baixo", "segmentos": ["*"], "ordem": 30},
    {"chave": "esgotados", "titulo": "Esgotados", "subtitulo": "Crítico",
     "escopo_ui": "card", "fonte": "produtos_esgotados", "formato": "int", "icone": "activity",
     "tema": "rose", "filtro": "esgotado", "segmentos": ["*"], "ordem": 40},
    {"chave": "valor_estoque", "titulo": "Valor Estoque", "subtitulo": "Capital investido",
     "escopo_ui": "card", "fonte": "valor_total_estoque", "formato": "moeda", "icone": "dollar",
     "tema": "purple", "filtro": "valor", "segmentos": ["*"], "ordem": 50},
    {"chave": "margem_media", "titulo": "Margem Média", "subtitulo": "Rentabilidade",
     "escopo_ui": "card", "fonte": "margem_media", "formato": "percent", "icone": "pie",
     "tema": "indigo", "filtro": "margem", "segmentos": ["*"], "ordem": 60},
    {"chave": "servicos", "titulo": "Serviços", "subtitulo": "Catálogo de serviços",
     "escopo_ui": "card", "fonte": "total_servicos", "formato": "int", "icone": "wrench",
     "tema": "cyan", "filtro": "servicos", "segmentos": ["autopecas", "generico"], "ordem": 70},

    {"chave": "analise_abc", "titulo": "Classificação ABC", "subtitulo": "Análise de Pareto (80/20)",
     "escopo_ui": "painel", "fonte": "classificacao_abc", "formato": "painel", "icone": "bar",
     "tema": "blue", "segmentos": ["*"], "ordem": 100},
    {"chave": "analise_giro", "titulo": "Giro de Estoque", "subtitulo": "Velocidade de venda",
     "escopo_ui": "painel", "fonte": "giro_estoque", "formato": "painel", "icone": "zap",
     "tema": "emerald", "segmentos": ["*"], "ordem": 110},
    {"chave": "analise_validade", "titulo": "Controle de Validade", "subtitulo": "Vencimentos por janela",
     "escopo_ui": "painel", "fonte": "validade", "formato": "painel", "icone": "clock",
     "tema": "amber", "segmentos": ["mercearia", "generico"], "ordem": 120},
]

# Cache leve do schema resolvido (o registry muda raramente; overrides invalidam).
_CACHE_TTL_SEGUNDOS = 60
_schema_cache = {}


def invalidar_cache_view_schema(estabelecimento_id=None):
    if estabelecimento_id is None:
        _schema_cache.clear()
    else:
        _schema_cache.pop(int(estabelecimento_id), None)


def garantir_registry_seed():
    """Popula o view_registry a partir do catálogo em código quando vazio (idempotente)."""
    if ViewRegistry.query.count() > 0:
        return False
    for definicao in CAMPOS_PADRAO:
        d = dict(definicao)
        segmentos = d.pop("segmentos", ["*"])
        ordem = d.pop("ordem", 0)
        db.session.add(ViewRegistry(escopo="campo", chave=d["chave"], ordem=ordem,
                                    definicao_json=json.dumps(d, ensure_ascii=False),
                                    segmentos_json=json.dumps(segmentos, ensure_ascii=False)))
    for definicao in METRICAS_PADRAO:
        d = dict(definicao)
        segmentos = d.pop("segmentos", ["*"])
        ordem = d.pop("ordem", 0)
        db.session.add(ViewRegistry(escopo="metrica", chave=d["chave"], ordem=ordem,
                                    definicao_json=json.dumps(d, ensure_ascii=False),
                                    segmentos_json=json.dumps(segmentos, ensure_ascii=False)))
    db.session.commit()
    invalidar_cache_view_schema()
    return True


def _overrides_do_tenant(estabelecimento) -> dict:
    """Nível 2 da cascata: overrides salvos no JSON de configurações do tenant."""
    try:
        overrides = (estabelecimento.configuracoes or {}).get("view_schema") or {}
        return overrides if isinstance(overrides, dict) else {}
    except Exception:
        return {}


def _linha_vale_para(linha: ViewRegistry, segmento: str, habilitados: set, ocultos: set) -> bool:
    if not linha.ativo:
        return False
    if linha.chave in ocultos:
        return False
    if linha.chave in habilitados:
        return True
    segmentos = linha.segmentos
    return "*" in segmentos or segmento in segmentos


def resolver_view_schema(estabelecimento: Estabelecimento = None, segmento: str = None) -> dict:
    """
    Resolve a cascata Global → Tenant e devolve o View Schema pronto p/ renderizar.
    Sem estabelecimento (ex.: super admin na visão 'all'), resolve só o nível
    Global para o segmento informado, sem overrides e sem cache.
    """
    cache_key = int(estabelecimento.id) if estabelecimento is not None else None
    if cache_key is not None:
        em_cache = _schema_cache.get(cache_key)
        if em_cache and (time.time() - em_cache[0]) < _CACHE_TTL_SEGUNDOS:
            return em_cache[1]

    garantir_registry_seed()

    if estabelecimento is not None:
        segmento = estabelecimento.segmento
    segmento = (segmento or SEGMENTO_PADRAO).lower()
    if segmento not in SEGMENTOS:
        segmento = SEGMENTO_PADRAO
    info_segmento = SEGMENTOS[segmento]

    overrides = _overrides_do_tenant(estabelecimento) if estabelecimento is not None else {}
    campos_ocultos = set(overrides.get("campos_ocultos") or [])
    campos_habilitados = set(overrides.get("campos_habilitados") or [])
    metricas_ocultas = set(overrides.get("metricas_ocultas") or [])
    metricas_habilitadas = set(overrides.get("metricas_habilitadas") or [])
    obrigatorios = overrides.get("obrigatorios") or {}
    opcoes_custom = overrides.get("opcoes") or {}

    linhas = ViewRegistry.query.order_by(ViewRegistry.ordem.asc(), ViewRegistry.chave.asc()).all()

    campos, metricas = [], []
    for linha in linhas:
        if linha.escopo == "campo":
            if not _linha_vale_para(linha, segmento, campos_habilitados, campos_ocultos):
                continue
            campo = dict(linha.definicao)
            campo["chave"] = linha.chave
            campo["ordem"] = linha.ordem
            if linha.chave in obrigatorios:
                campo["obrigatorio"] = bool(obrigatorios[linha.chave])
            if linha.chave in opcoes_custom and isinstance(opcoes_custom[linha.chave], list):
                campo["opcoes"] = opcoes_custom[linha.chave]
            campos.append(campo)
        elif linha.escopo == "metrica":
            if not _linha_vale_para(linha, segmento, metricas_habilitadas, metricas_ocultas):
                continue
            metrica = dict(linha.definicao)
            metrica["chave"] = linha.chave
            metrica["ordem"] = linha.ordem
            metricas.append(metrica)

    flags = dict(info_segmento["flags"])
    # Validade some do segmento? Então o campo/painel não sobrevive nem por override de flag.
    unidades = overrides.get("unidades") if isinstance(overrides.get("unidades"), list) else None

    schema = {
        "segmento": {"chave": segmento, "nome": info_segmento["nome"],
                     "descricao": info_segmento["descricao"], "icone": info_segmento["icone"],
                     "exemplos": info_segmento["exemplos"]},
        "flags": flags,
        "unidades": unidades or info_segmento["unidades"],
        "tipos_item": (["produto", "servico"] if flags.get("usa_servicos") else ["produto"]),
        "campos": campos,
        "metricas": metricas,
        "grupos": [
            {"chave": "identificacao", "label": "Identificação"},
            {"chave": "fiscal", "label": "Tributação (NFC-e / NF-e)"},
            {"chave": "precificacao", "label": "Precificação e Lucro"},
            {"chave": "estoque", "label": "Controle de Estoque"},
            {"chave": "atributos", "label": "Atributos do Segmento"},
            {"chave": "dimensoes", "label": "Dimensões e Medidas"},
            {"chave": "servico", "label": "Dados do Serviço"},
            {"chave": "detalhes", "label": "Imagem e Detalhes"},
        ],
    }

    if cache_key is not None:
        _schema_cache[cache_key] = (time.time(), schema)
    return schema


def campos_de_atributo(schema: dict, tipo_item: str = "produto") -> dict:
    """Campos de origem 'atributo' aplicáveis ao tipo de item, indexados por chave."""
    resultado = {}
    for campo in schema.get("campos", []):
        if campo.get("origem") != "atributo":
            continue
        aplica = campo.get("aplica_tipo_item")
        if aplica and tipo_item not in aplica:
            continue
        resultado[campo["chave"]] = campo
    return resultado


def sanitizar_atributos(schema: dict, atributos, tipo_item: str = "produto") -> dict:
    """
    Valida os atributos dinâmicos contra o schema resolvido do tenant.
    Chaves desconhecidas são descartadas; valores são coagidos ao tipo do campo.
    """
    if not isinstance(atributos, dict):
        return {}
    validos = campos_de_atributo(schema, tipo_item)
    limpos = {}
    for chave, valor in atributos.items():
        campo = validos.get(chave)
        if campo is None or valor is None or valor == "":
            continue
        tipo = campo.get("tipo")
        try:
            if tipo == "number":
                limpos[chave] = float(valor)
            elif tipo == "boolean":
                limpos[chave] = bool(valor)
            elif tipo == "multiselect":
                if isinstance(valor, list):
                    itens = [str(v).strip() for v in valor if str(v).strip()]
                    if itens:
                        limpos[chave] = itens[:50]
            else:  # text, textarea, select, date
                texto = str(valor).strip()
                if texto:
                    limpos[chave] = texto[:500]
        except (TypeError, ValueError):
            continue
    return limpos
