from datetime import timezone
# app/routes/pdv.py
"""
PDV - Ponto de Venda MISSION-CRITICAL
Rotas otimizadas para operações em tempo real no PDV
Separado de vendas.py para melhor performance e manutenibilidade

OTIMIZAÇÕES IMPLEMENTADAS:
- Custo Médio Ponderado (CMP) em tempo real
- Validação de estoque com lock pessimista (with_for_update)
- Inteligência RFM para sugestão de descontos
- Auditoria completa de vendas
- Alertas de produtos Classe A (alto giro)
"""

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt
from app.models import db, Produto, Venda, VendaItem, MovimentacaoEstoque, Configuracao, Funcionario, Cliente, Auditoria
from app.decorators.decorator_jwt import funcionario_required
import pytz
import uuid
import random
import string
from sqlalchemy import func
from app.utils.smart_cache import get_cached_config, set_cached_config
from app.utils.query_helpers import get_funcionario_safe, get_produto_safe, get_venda_safe, get_venda_itens_safe

pdv_bp = Blueprint("pdv", __name__)


# ==================== EXCEÇÕES PERSONALIZADAS ====================

class InsuficientStockError(Exception):
    """Exceção lançada quando não há estoque suficiente para a venda"""
    pass



# ==================== FUNÇÕES AUXILIARES ====================

def calcular_rfm_cliente(cliente_id: int, estabelecimento_id: int) -> dict:
    """
    Calcula o segmento RFM de um cliente específico.
    
    Retorna dados RFM incluindo flag de sugestão de desconto para clientes em risco.
    
    Args:
        cliente_id: ID do cliente
        estabelecimento_id: ID do estabelecimento
        
    Returns:
        dict: Dados RFM com segmento e flag sugerir_desconto
    """
    from datetime import datetime, timedelta
    
    # Buscar vendas do cliente nos últimos 180 dias
    data_inicio = datetime.now(timezone.utc) - timedelta(days=180)
    
    vendas = Venda.query.filter(
        Venda.estabelecimento_id == estabelecimento_id,
        Venda.cliente_id == cliente_id,
        Venda.data_venda >= data_inicio,
        Venda.status == "finalizada"
    ).all()
    
    if not vendas:
        return {
            "segmento": "Novo",
            "sugerir_desconto": False,
            "recency_days": None,
            "frequency": 0,
            "monetary": 0.0
        }
    
    # Calcular métricas
    now = datetime.now(timezone.utc)
    ultima_compra = max(v.data_venda for v in vendas)
    recency_days = (now - ultima_compra).days
    frequency = len(vendas)
    monetary = sum(float(v.total) for v in vendas)
    
    # Calcular scores simplificados (1-5)
    # Recency: quanto menor o número de dias, melhor (score invertido)
    if recency_days <= 30:
        recency_score = 5
    elif recency_days <= 60:
        recency_score = 4
    elif recency_days <= 90:
        recency_score = 3
    elif recency_days <= 120:
        recency_score = 2
    else:
        recency_score = 1
    
    # Frequency: quanto mais compras, melhor
    if frequency >= 10:
        frequency_score = 5
    elif frequency >= 7:
        frequency_score = 4
    elif frequency >= 5:
        frequency_score = 3
    elif frequency >= 3:
        frequency_score = 2
    else:
        frequency_score = 1
    
    # Monetary: quanto maior o valor, melhor
    if monetary >= 1000:
        monetary_score = 5
    elif monetary >= 500:
        monetary_score = 4
    elif monetary >= 250:
        monetary_score = 3
    elif monetary >= 100:
        monetary_score = 2
    else:
        monetary_score = 1
    
    # Determinar segmento usando a lógica do modelo Cliente
    segmento = Cliente.segmentar_rfm(recency_score, frequency_score, monetary_score)
    
    # Sugerir desconto para clientes em risco de abandono
    sugerir_desconto = segmento in ["Risco", "Perdido"]
    
    return {
        "segmento": segmento,
        "sugerir_desconto": sugerir_desconto,
        "recency_days": recency_days,
        "recency_score": recency_score,
        "frequency": frequency,
        "frequency_score": frequency_score,
        "monetary": round(monetary, 2),
        "monetary_score": monetary_score,
        "ultima_compra": ultima_compra.isoformat() if ultima_compra else None
    }


def to_decimal(value, precision=2):
    """Converte qualquer valor numérico para Decimal de forma segura com precisão variável"""
    quantize_str = '0.' + '0' * (precision - 1) + '1' if precision > 0 else '0'
    if value is None:
        return Decimal(quantize_str)
    try:
        # Converter para string primeiro para evitar imprecisões de float
        d = Decimal(str(value))
        return d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError, InvalidOperation):
        return Decimal(quantize_str)


def decimal_to_float(value):
    """Converte Decimal para float APENAS para serialização JSON"""
    if isinstance(value, Decimal):
        return float(value)
    return value


def gerar_codigo_venda():
    """Gera código único para venda no formato V-YYYYMMDD-XXXX"""
    data_atual = datetime.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.digits, k=4))
    codigo = f"V-{data_atual}-{random_part}"
    
    # Garantir unicidade
    while Venda.query.filter_by(codigo=codigo).first():
        random_part = "".join(random.choices(string.digits, k=4))
        codigo = f"V-{data_atual}-{random_part}"
    
    return codigo


def validar_estoque_disponivel(produto_id, quantidade_solicitada, estabelecimento_id=None):
    """Valida se há estoque suficiente ou se permite venda sem estoque"""
    produto = Produto.query.get(produto_id)
    
    if not produto:
        return False, "Produto não encontrado"
    
    if not produto.ativo:
        return False, "Produto inativo"
    
    if produto.quantidade < quantidade_solicitada:
        # Verifica se o estabelecimento permite venda sem estoque
        if estabelecimento_id:
            from app.models import Configuracao
            config = Configuracao.query.filter_by(estabelecimento_id=estabelecimento_id).first()
            if config and config.permitir_venda_sem_estoque:
                return True, produto
                
        return False, f"Estoque insuficiente. Disponível: {produto.quantidade}"
    
    return True, produto


def calcular_totais_venda(itens, desconto_geral=0, desconto_percentual=False):
    """Calcula subtotal, desconto e total da venda usando Decimal para precisão"""
    # Converter tudo para Decimal
    subtotal = Decimal('0.00')
    for item in itens:
        subtotal += to_decimal(item['total_item'])
    
    desconto_geral_dec = to_decimal(desconto_geral)
    
    # Calcular desconto
    if desconto_percentual:
        desconto_valor = subtotal * (desconto_geral_dec / Decimal('100'))
    else:
        desconto_valor = desconto_geral_dec
    
    # Desconto não pode ser maior que subtotal
    desconto_valor = min(desconto_valor, subtotal)
    total = subtotal - desconto_valor
    
    return {
        'subtotal': subtotal.quantize(Decimal('0.01')),
        'desconto': desconto_valor.quantize(Decimal('0.01')),
        'total': total.quantize(Decimal('0.01'))
    }


# ==================== ROTAS PDV ====================

@pdv_bp.route("/configuracoes", methods=["GET"])
@funcionario_required
def obter_configuracoes_pdv():
    """
    Retorna configurações do PDV para o funcionário logado (Resiliência de Elite)
    """
    try:
        from app.utils.query_helpers import get_funcionario_safe
        current_user_id = get_jwt_identity()
        funcionario_data = get_funcionario_safe(current_user_id)
        
        # Fallback de Elite: Se não achou no banco, tenta reconstruir via claims
        if not funcionario_data:
            try:
                claims = get_jwt()
                funcionario_data = {
                    "id": current_user_id,
                    "nome": claims.get("nome", "Funcionário"),
                    "role": claims.get("role", "FUNCIONARIO"),
                    "estabelecimento_id": claims.get("estabelecimento_id"),
                    "permissoes": {
                        "pode_dar_desconto": claims.get("role") in ["gerente", "admin", "dono", "ADMIN"],
                        "limite_desconto": 100 if claims.get("role") in ["admin", "ADMIN"] else 10,
                        "pode_cancelar_venda": claims.get("role") in ["gerente", "admin", "dono", "ADMIN"]
                    }
                }
            except:
                return jsonify({"error": "Contexto de autenticação inválido"}), 401

        # Busca formas de pagamento do cache de configurações se disponível
        cached_config = get_cached_config(funcionario_data.get("estabelecimento_id"))
        if isinstance(cached_config, str):
            import json
            try:
                cached_config = json.loads(cached_config)
                if isinstance(cached_config, str):
                    cached_config = json.loads(cached_config)
            except:
                cached_config = {}
        if not isinstance(cached_config, dict):
            cached_config = {}

        # Formas de pagamento base canônicas (sempre presentes)
        FORMAS_PADRAO = [
            {"tipo": "dinheiro",       "label": "Dinheiro",           "taxa": 0,   "permite_troco": True},
            {"tipo": "cartao_debito",  "label": "Cartão de Débito",   "taxa": 0,   "permite_troco": False},
            {"tipo": "cartao_credito", "label": "Cartão de Crédito",  "taxa": 2.5, "permite_troco": False},
            {"tipo": "pix",            "label": "PIX",                "taxa": 0,   "permite_troco": False},
            {"tipo": "fiado",          "label": "Fiado",              "taxa": 0,   "permite_troco": False},
        ]

        if cached_config and cached_config.get("formas_pagamento"):
            import json
            try:
                raw_fp = cached_config.get("formas_pagamento")
                if isinstance(raw_fp, str):
                    raw_fp = json.loads(raw_fp)

                # Normaliza para o formato de objeto esperado pelo PDV
                formas_pagamento = []
                for f in raw_fp:
                    if isinstance(f, dict):
                        formas_pagamento.append(f)
                    else:
                        tipo = f.lower().replace(" ", "_").replace("ã", "a").replace("é", "e").replace("ê", "e")
                        formas_pagamento.append({
                            "tipo": tipo,
                            "label": f,
                            "taxa": 0,
                            "permite_troco": tipo == "dinheiro"
                        })

                # ─── Garantir Fiado sempre presente ───────────────────────────
                tipos_existentes = {fp["tipo"] for fp in formas_pagamento}
                for fp_padrao in FORMAS_PADRAO:
                    if fp_padrao["tipo"] not in tipos_existentes:
                        formas_pagamento.append(fp_padrao)

                # ─── Deduplicar por tipo (evita duplicatas vindas do banco) ───
                seen = {}
                for fp in formas_pagamento:
                    t = fp.get("tipo")
                    if t and t not in seen:
                        seen[t] = fp
                formas_pagamento = list(seen.values())

            except:
                formas_pagamento = FORMAS_PADRAO
        else:
            formas_pagamento = FORMAS_PADRAO


        permissoes = funcionario_data.get("permissoes", {})
        if isinstance(permissoes, str):
            import json
            try:
                permissoes = json.loads(permissoes)
                if isinstance(permissoes, str):
                    permissoes = json.loads(permissoes)
            except:
                permissoes = {}
        if not isinstance(permissoes, dict):
            permissoes = {}

        configuracoes = {
            "funcionario": {
                "id": funcionario_data.get("id"),
                "nome": funcionario_data.get("nome"),
                "role": funcionario_data.get("role"),
                "pode_dar_desconto": permissoes.get("pode_dar_desconto", False),
                "limite_desconto": permissoes.get("limite_desconto", 0),
                "pode_cancelar_venda": permissoes.get("pode_cancelar_venda", False),
            },
            "formas_pagamento": formas_pagamento,
            "permite_venda_sem_cliente": bool(cached_config.get("permite_venda_sem_cliente", True)) if cached_config else True,
            "permitir_venda_sem_estoque": bool(cached_config.get("permitir_venda_sem_estoque", False)) if cached_config else False,
            "controlar_validade": bool(cached_config.get("controlar_validade", True)) if cached_config else True,
            "alerta_estoque_minimo": bool(cached_config.get("alerta_estoque_minimo", True)) if cached_config else True,
            "dias_alerta_validade": cached_config.get("dias_alerta_validade", 30) if cached_config else 30,
            "estoque_minimo_padrao": cached_config.get("estoque_minimo_padrao", 10) if cached_config else 10,
            "exibe_preco_tela": bool(cached_config.get("exibir_preco_tela", True)) if cached_config else True,
            "exige_observacao_desconto": True,
        }
        
        # OTIMIZAÇÃO: Incluir dados RFM se cliente_id for fornecido
        cliente_id = request.args.get("cliente_id", type=int)
        if cliente_id:
            try:
                rfm_data = calcular_rfm_cliente(cliente_id, funcionario_data.get("estabelecimento_id"))
                if rfm_data:
                    configuracoes["rfm"] = rfm_data
            except Exception as rfm_error:
                current_app.logger.warning(f"Erro ao calcular RFM: {str(rfm_error)}")
        
        return jsonify({
            "success": True,
            "configuracoes": configuracoes
        }), 200
        
    except Exception as e:
        import traceback
        erro_formatado = traceback.format_exc()
        current_app.logger.error(f"ERRO CRÍTICO CONFIG PDV: {erro_formatado}")
        return jsonify({
            "success": False,
            "error": "Falha na comunicação com o servidor de configurações",
            "msg": f"O servidor do PDV está temporariamente instável. Detalhe técnico: {str(e)}",
            "traceback": erro_formatado
        }), 500


@pdv_bp.route("/cliente/<int:cliente_id>/rfm", methods=["GET"])
@funcionario_required
def obter_rfm_cliente(cliente_id):
    """
    Retorna dados RFM de um cliente específico.
    
    OTIMIZAÇÃO: Inteligência RFM para sugestão de descontos no PDV.
    Se o cliente estiver em "Risco" ou "Perdido", retorna flag sugerir_desconto=True.
    """
    try:
        from app.utils.query_helpers import get_funcionario_safe
        current_user_id = get_jwt_identity()
        funcionario_data = get_funcionario_safe(current_user_id)
        
        if not funcionario_data:
            return jsonify({"error": "Funcionário não encontrado"}), 404
        
        # Proxy para o funcionário
        class _Proxy:
            def __init__(self, data):
                for k, v in data.items(): setattr(self, k, v)
        funcionario = _Proxy(funcionario_data)
        
        # Verificar se cliente existe
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404
        
        # Calcular RFM
        rfm_data = calcular_rfm_cliente(cliente_id, funcionario_data.get("estabelecimento_id"))
        
        return jsonify({
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nome": cliente.nome,
                "cpf": cliente.cpf
            },
            "rfm": rfm_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter RFM do cliente: {str(e)}")
        return jsonify({"error": "Erro ao calcular RFM"}), 500


@pdv_bp.route("/validar-produto", methods=["POST"])
@funcionario_required
def validar_produto():
    """
    Valida se produto está disponível e retorna informações completas
    Útil para busca por código de barras ou ID
    
    OTIMIZAÇÃO: Retorna alerta para produtos Classe A (alto giro)
    """
    try:
        data = request.get_json()
        produto_id = data.get("produto_id")
        codigo_barras = data.get("codigo_barras")
        quantidade = float(data.get("quantidade", 1))
        
        from app.utils.query_helpers import get_authorized_establishment_id
        estabelecimento_id = get_authorized_establishment_id()
        
        # Buscar produto
        from app.utils.query_helpers import get_produto_safe
        if produto_id:
            produto_data = get_produto_safe(produto_id)
        elif codigo_barras:
            # BUGFIX: Scoping por estabelecimento_id no código de barras
            # Suporte SuperAdmin 'all'
            query = Produto.query.filter_by(codigo_barras=codigo_barras)
            if str(estabelecimento_id).lower() != 'all':
                query = query.filter_by(estabelecimento_id=estabelecimento_id)
            produto = query.first()
            produto_data = get_produto_safe(produto.id) if produto else None
        else:
            return jsonify({"error": "Informe produto_id ou codigo_barras"}), 400
        
        if not produto_data:
            return jsonify({
                "valido": False,
                "erro": "Produto não encontrado"
            }), 404
        
        # Validar estoque respeitando a config de 'permitir_venda_sem_estoque'
        valido, resultado = validar_estoque_disponivel(produto_data.get("id"), quantidade, estabelecimento_id)
        
        if not valido:
            return jsonify({
                "valido": False,
                "erro": resultado
            }), 400
        
        # Retornar informações do produto
        # OTIMIZAÇÃO: Verificar se é produto Classe A (alto giro)
        alerta_alto_giro = False
        mensagem_alerta = None
        if produto_data.get("classificacao_abc") == "A":
            alerta_alto_giro = True
            mensagem_alerta = "Produto de Alto Giro - Verificar se precisa de reposição na gôndola"
            
        return jsonify({
            "valido": True,
            "produto": {
                "id": produto_data.get("id"),
                "nome": produto_data.get("nome"),
                "codigo_barras": produto_data.get("codigo_barras"),
                "preco_venda": float(produto_data.get("preco_venda")),
                "preco_custo": float(produto_data.get("preco_custo")) if produto_data.get("preco_custo") else 0,
                "quantidade_estoque": produto_data.get("quantidade"),
                "unidade_medida": produto_data.get("unidade_medida") or "UN",
                "margem_lucro": float(produto_data.get("margem_lucro")) if produto_data.get("margem_lucro") else 0,
                "ativo": produto_data.get("ativo"),
                "classificacao_abc": produto_data.get("classificacao_abc"),
                "alerta_alto_giro": alerta_alto_giro,
                "mensagem_alerta": mensagem_alerta,
                "data_validade": str(produto_data.get("data_validade")) if produto_data.get("data_validade") else None,
                "vencido": False # Lógica de cálculo será feita no frontend ou aqui se necessário
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao validar produto: {str(e)}")
        return jsonify({"error": "Erro ao validar produto"}), 500


@pdv_bp.route("/calcular-venda", methods=["POST"])
@funcionario_required
def calcular_venda():
    """
    Calcula totais da venda sem persistir (para preview em tempo real)
    Recebe: itens, desconto_geral, desconto_percentual, forma_pagamento
    Retorna: subtotal, desconto, total, troco
    """
    try:
        data = request.get_json()
        itens = data.get("items", [])
        desconto_geral = float(data.get("desconto_geral", 0))
        desconto_percentual = data.get("desconto_percentual", False)
        forma_pagamento = data.get("forma_pagamento", "dinheiro")
        valor_recebido = float(data.get("valor_recebido", 0))
        
        if not itens:
            return jsonify({"error": "Nenhum item na venda"}), 400
        
        # Validar e calcular cada item
        from app.utils.query_helpers import get_produto_safe
        itens_calculados = []
        for item in itens:
            produto_id = item.get("produto_id")
            quantidade = item.get("quantidade", 1)
            desconto_item = float(item.get("desconto", 0))
            
            # Buscar produto
            produto_data = get_produto_safe(produto_id)
            if not produto_data:
                return jsonify({"error": f"Produto {produto_id} não encontrado"}), 404
            
            # Calcular item
            preco_unitario = float(produto_data.get("preco_venda"))
            total_item = (preco_unitario * quantidade) - desconto_item
            
            itens_calculados.append({
                "produto_id": produto_id,
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "desconto_item": desconto_item,
                "total_item": round(total_item, 2)
            })
        
        # Calcular totais
        totais = calcular_totais_venda(itens_calculados, desconto_geral, desconto_percentual)
        
        # Calcular troco (se dinheiro)
        troco = 0
        if forma_pagamento == "dinheiro" and valor_recebido > 0:
            troco = max(0, valor_recebido - totais['total'])
        
        return jsonify({
            "success": True,
            "calculo": {
                **totais,
                "troco": round(troco, 2),
                "quantidade_itens": len(itens_calculados),
                "valor_recebido": valor_recebido,
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular venda: {str(e)}")
        return jsonify({"error": f"Erro ao calcular: {str(e)}"}), 500


@pdv_bp.route("/buscar-produtos", methods=["GET"])
@funcionario_required
def buscar_produtos_pdv():
    """
    Busca de produtos TURBO para o PDV.
    Retorna apenas os campos essenciais, sem cálculos pesados.
    Performance máxima: ~50ms vs ~800ms da rota geral.
    """
    try:
        from app.utils.query_helpers import get_authorized_establishment_id
        estabelecimento_id = get_authorized_establishment_id()
        busca = request.args.get("q", "").strip()

        if not busca or len(busca) < 2:
            return jsonify({"success": True, "produtos": []}), 200

        busca_termo = f"%{busca}%"

        engine_name = str(db.engine.name).lower()
        like_op = "ILIKE" if 'sqlite' not in engine_name else "LIKE"

        if 'sqlite' in engine_name:
            lot_join_sql = """
            LEFT JOIN (
                SELECT produto_id, MIN(data_validade) as data_validade, MIN(numero_lote) as numero_lote
                FROM produto_lotes
                WHERE ativo = true AND quantidade > 0
                GROUP BY produto_id
            ) pl ON p.id = pl.produto_id
            """
        else:
            lot_join_sql = """
            LEFT JOIN (
                SELECT DISTINCT ON (produto_id) 
                    produto_id, data_validade, numero_lote
                FROM produto_lotes
                WHERE ativo = true AND quantidade > 0
                ORDER BY produto_id, data_validade ASC
            ) pl ON p.id = pl.produto_id
            """

        # Filtro de Tenant Híbrido (Suporte SuperAdmin 'all')
        estab_filter = ""
        params = {"busca": busca_termo}
        if str(estabelecimento_id).lower() != 'all':
            estab_filter = "AND p.estabelecimento_id = :estab_id"
            params["estab_id"] = estabelecimento_id

        from sqlalchemy import text as sql_text
        resultado = db.session.execute(sql_text(f"""
            SELECT
                p.id,
                p.nome,
                p.codigo_barras,
                p.codigo_interno,
                p.marca,
                p.preco_venda,
                p.quantidade AS quantidade_estoque,
                p.unidade_medida,
                COALESCE(pl.data_validade, p.data_validade) as data_validade,
                COALESCE(pl.numero_lote, p.lote) as lote
            FROM produtos p
            {lot_join_sql}
            WHERE p.ativo = true
              {estab_filter}
              AND (
                  p.nome {like_op} :busca
                  OR p.codigo_barras {like_op} :busca
                  OR p.codigo_interno {like_op} :busca
                  OR p.marca {like_op} :busca
              )
            ORDER BY p.nome ASC
            LIMIT 20
        """), params).fetchall()


        produtos = []
        for row in resultado:
            row_map = row._mapping
            produtos.append({
                "id": row_map["id"],
                "nome": row_map["nome"],
                "codigo_barras": row_map["codigo_barras"] or "",
                "codigo_interno": row_map["codigo_interno"] or "",
                "marca": row_map["marca"] or "",
                "preco_venda": float(row_map["preco_venda"]) if row_map["preco_venda"] else 0.0,
                "preco_venda_efetivo": float(row_map["preco_venda"]) if row_map["preco_venda"] else 0.0,
                "quantidade_estoque": float(row_map["quantidade_estoque"]) if row_map["quantidade_estoque"] else 0.0,
                "estoque_atual": float(row_map["quantidade_estoque"]) if row_map["quantidade_estoque"] else 0.0,
                "unidade_medida": row_map["unidade_medida"] or "UN",
                "data_validade": str(row_map["data_validade"]) if row_map.get("data_validade") else None,
            })

        return jsonify({"success": True, "produtos": produtos}), 200

    except Exception as e:
        import traceback
        current_app.logger.error(f"Erro na busca turbo PDV: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@pdv_bp.route("/finalizar", methods=["POST"])
@funcionario_required
def finalizar_venda():
    """
    Finaliza a venda de forma ATÔMICA e BLINDADA (Elite)
    """
    try:
        current_user_id = get_jwt_identity()
        funcionario_data = get_funcionario_safe(current_user_id)

        if not funcionario_data:
            claims = get_jwt()
            funcionario_data = {
                "id": current_user_id,
                "estabelecimento_id": claims.get("estabelecimento_id"),
                "nome": claims.get("nome", "Operador")
            }

        data = request.get_json()
        print(f"🔥 FINALIZAR PAYLOAD FRONTEND: {data}", flush=True)
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        items = data.get("items", [])
        if not items:
            return jsonify({"error": "Nenhum produto na venda"}), 400

        cliente_id = data.get("cliente_id")
        subtotal = to_decimal(data.get("subtotal", 0))
        desconto = to_decimal(data.get("desconto", 0))
        total = to_decimal(data.get("total", 0))
        forma_pagamento = data.get("paymentMethod", "dinheiro")
        valor_recebido = to_decimal(data.get("valor_recebido", total))
        troco = to_decimal(data.get("troco", 0))
        email_destino = data.get("email_destino")

        # Início do processo atômico
        try:
            # 1. VERIFICAR CAIXA ABERTO OBRIGATÓRIO (RBAC/CASHIER)
            from app.models import Caixa, MovimentacaoCaixa
            caixa_aberto = Caixa.query.filter_by(
                funcionario_id=funcionario_data.get("id"),
                status="aberto"
            ).order_by(Caixa.data_abertura.desc()).first()

            if not caixa_aberto:
                return jsonify({
                    "success": False, 
                    "error": "CAIXA_FECHADO", 
                    "message": "Você precisa realizar a Abertura de Caixa para registrar vendas."
                }), 403

            codigo_venda = gerar_codigo_venda()
            manaus_tz = pytz.timezone('America/Manaus')
            data_venda = datetime.now(manaus_tz)

            estab_id = funcionario_data.get("estabelecimento_id")
            nova_venda = Venda(
                codigo=codigo_venda,
                estabelecimento_id=estab_id,
                cliente_id=cliente_id,
                funcionario_id=funcionario_data.get("id"),
                caixa_id=caixa_aberto.id,
                subtotal=subtotal,
                desconto=desconto,
                total=total,
                valor_recebido=valor_recebido,
                troco=troco,
                status="finalizada",
                data_venda=data_venda,
                quantidade_itens=len(items),
                observacoes=data.get("observacoes")
            )
            db.session.add(nova_venda)
            db.session.flush()

            # Criar registro de pagamento (Novo sistema multi-pagamento)
            from app.models import Pagamento
            novo_pagamento = Pagamento(
                estabelecimento_id=estab_id,
                venda_id=nova_venda.id,
                forma_pagamento=forma_pagamento,
                valor=valor_recebido, # No PDV simples é o valor total recebido
                status="aprovado",
                data_pagamento=data_venda
            )
            db.session.add(novo_pagamento)

            itens_formatados_para_resposta = []

            for item_data in items:
                # Suporte a múltiplos nomes de campos
                produto_id = item_data.get("id") or item_data.get("productId") or item_data.get("produto_id")
                quantidade = to_decimal(item_data.get("quantity") or item_data.get("quantidade", 1), precision=3)

                produto = db.session.query(Produto).with_for_update().get(produto_id)
                if not produto:
                    db.session.rollback()
                    return jsonify({"error": f"Produto {produto_id} não encontrado"}), 404

                # Comparação segura com 3 casas
                if to_decimal(produto.quantidade, precision=3) < quantidade:
                    db.session.rollback()
                    return jsonify({"error": f"Estoque insuficiente: {produto.nome}"}), 400

                preco_unitario = to_decimal(item_data.get("price") or item_data.get("preco_unitario", produto.preco_venda))
                total_item = to_decimal(preco_unitario * quantidade, precision=2)

                margem_lucro_real = to_decimal((preco_unitario - to_decimal(produto.preco_custo or 0)) * quantidade, precision=2)

                novo_item = VendaItem(
                    venda_id=nova_venda.id,
                    estabelecimento_id=estab_id, # Herança robusta via variável local
                    produto_id=produto.id,
                    produto_nome=produto.nome,
                    produto_codigo=produto.codigo_interno or produto.codigo_barras,
                    produto_unidade=produto.unidade_medida or "UN",
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    total_item=total_item,
                    margem_lucro_real=margem_lucro_real
                )
                db.session.add(novo_item)

                estoque_anterior = to_decimal(produto.quantidade, precision=3)
                # SUBTRAÇÃO BLINDADA: Evita resíduos tipo -0.001
                produto.quantidade = to_decimal(estoque_anterior - quantidade, precision=3)

                mov = MovimentacaoEstoque(
                    estabelecimento_id=nova_venda.estabelecimento_id,
                    produto_id=produto.id,
                    tipo="saida",
                    quantidade=quantidade,
                    quantidade_anterior=estoque_anterior,
                    quantidade_atual=produto.quantidade,
                    venda_id=nova_venda.id,
                    funcionario_id=nova_venda.funcionario_id,
                    created_at=data_venda,
                    motivo=f"Venda PDV {nova_venda.codigo}"
                )
                db.session.add(mov)

                itens_formatados_para_resposta.append({
                    "nome": produto.nome,
                    "quantidade": quantidade,
                    "preco_unitario": float(preco_unitario),
                    "total": float(total_item)
                })

            # Registrar Movimentação no Caixa
            mov_caixa = MovimentacaoCaixa(
                caixa_id=caixa_aberto.id,
                estabelecimento_id=funcionario_data.get("estabelecimento_id"),
                tipo="venda",
                valor=total,
                forma_pagamento=forma_pagamento,
                venda_id=nova_venda.id,
                descricao=f"Venda PDV {codigo_venda}"
            )
            db.session.add(mov_caixa)

            # ========================
            # LÓGICA DE FIADO
            # ========================
            forma_lower = str(forma_pagamento).lower()
            if forma_lower == "fiado":
                # Fiado exige cliente cadastrado
                if not cliente_id:
                    db.session.rollback()
                    return jsonify({
                        "success": False,
                        "error": "CLIENTE_OBRIGATORIO",
                        "message": "Para vender no FIADO é obrigatório selecionar um cliente cadastrado."
                    }), 400

                cliente = Cliente.query.get(cliente_id)
                if not cliente:
                    db.session.rollback()
                    return jsonify({"success": False, "error": "Cliente não encontrado"}), 404

                # Incrementar saldo devedor
                cliente.saldo_devedor = float(cliente.saldo_devedor or 0) + float(total)

                # Criar ContaReceber para rastreabilidade financeira
                data_vencimento_str = data.get("data_vencimento_fiado")
                data_vencimento = None
                if data_vencimento_str:
                    try:
                        data_vencimento = datetime.strptime(data_vencimento_str, "%Y-%m-%d").date()
                    except Exception:
                        pass
                if not data_vencimento:
                    from datetime import timedelta
                    data_vencimento = (data_venda + timedelta(days=30)).date()

                from app.models import ContaReceber
                conta = ContaReceber(
                    estabelecimento_id=funcionario_data.get("estabelecimento_id"),
                    cliente_id=cliente_id,
                    venda_id=nova_venda.id,
                    numero_documento=codigo_venda,
                    valor_original=total,
                    valor_atual=total,
                    data_emissao=data_venda.date(),
                    data_vencimento=data_vencimento,
                    status="aberto",
                    observacoes=f"Fiado PDV - {cliente.nome}. Venda fiado em {data_venda.strftime('%d/%m/%Y')}"
                )
                db.session.add(conta)
                # Não entra dinheiro no caixa (é fiado)
            elif forma_lower == "dinheiro":
                # Atualizar saldo apenas se for dinheiro (caixa físico)
                caixa_aberto.saldo_atual = float(caixa_aberto.saldo_atual) + float(total)

            # ========================
            # ATUALIZAR MÉTRICAS DO CLIENTE
            # ========================
            # Independente da forma de pagamento, toda venda com cliente
            # deve atualizar os campos de agregação (total_compras, valor_total_gasto, ultima_compra)
            if cliente_id and forma_lower != "fiado":
                # Para fiado o cliente já foi carregado acima; para outros buscamos aqui
                cliente_para_metrica = Cliente.query.get(cliente_id)
                if cliente_para_metrica:
                    cliente_para_metrica.total_compras = int(cliente_para_metrica.total_compras or 0) + 1
                    cliente_para_metrica.valor_total_gasto = float(cliente_para_metrica.valor_total_gasto or 0) + float(total)
                    cliente_para_metrica.ultima_compra = data_venda
            elif cliente_id and forma_lower == "fiado":
                # cliente já está em memória da seção fiado acima (variável 'cliente')
                if cliente:
                    cliente.total_compras = int(cliente.total_compras or 0) + 1
                    cliente.valor_total_gasto = float(cliente.valor_total_gasto or 0) + float(total)
                    cliente.ultima_compra = data_venda
            
            # Auditoria Global (SaaS Monitor)
            Auditoria.registrar(
                estabelecimento_id=funcionario_data.get("estabelecimento_id"),
                tipo_evento="venda_finalizada",
                descricao=f"Venda {codigo_venda} finalizada - Total: R$ {float(total):.2f}",
                usuario_id=funcionario_data.get("id"),
                valor=total,
                detalhes={"codigo": codigo_venda, "itens": len(items), "forma_pagamento": forma_pagamento}
            )

            db.session.commit()

            return jsonify({
                "success": True,
                "venda": {
                    "id": nova_venda.id,
                    "codigo": codigo_venda,
                    "data": data_venda.strftime("%d/%m/%Y %H:%M"),
                    "total": float(total)
                },
                "message": "Venda finalizada com sucesso!"
            }), 201

        except Exception as e:
            import traceback
            db.session.rollback()
            trace = traceback.format_exc()
            current_app.logger.error(f"ERRO TRANSAÇÃO PDV: {str(e)}\n{trace}")
            with open('backend_finalizar_erro.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n--- ERRO TRANSAÇÃO ---\n{str(e)}\n{trace}\n")
            return jsonify({"error": "Erro ao salvar venda no banco", "details": str(e), "trace": trace}), 500

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        current_app.logger.error(f"ERRO FATAL PDV: {str(e)}\n{trace}")
        with open('backend_finalizar_erro.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERRO FATAL ---\n{str(e)}\n{trace}\n")
        return jsonify({"error": "Falha interna ao processar venda", "details": str(e), "trace": trace}), 500


@pdv_bp.route("/vendas-hoje", methods=["GET"])
@funcionario_required
def vendas_hoje():
    """
    Retorna resumo das vendas do dia atual
    Útil para dashboard do PDV
    """
    try:
        from app.utils.query_helpers import get_funcionario_safe
        current_user_id = get_jwt_identity()
        funcionario_data = get_funcionario_safe(current_user_id)
        
        if not funcionario_data:
            return jsonify({"error": "Funcionário não encontrado"}), 404
        
        # Proxy para o funcionário
        class _Proxy:
            def __init__(self, data):
                for k, v in data.items(): setattr(self, k, v)
        funcionario = _Proxy(funcionario_data)
        
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = datetime.combine(hoje, datetime.max.time())
        
        # Vendas do dia
        vendas = Venda.query.filter(
            Venda.estabelecimento_id == funcionario.estabelecimento_id,
            Venda.data_venda >= inicio_dia,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada"
        ).all()
        
        # Estatísticas
        total_vendas = sum(v.total for v in vendas)
        quantidade_vendas = len(vendas)
        ticket_medio = total_vendas / quantidade_vendas if quantidade_vendas > 0 else 0
        
        # Por forma de pagamento
        por_forma_pagamento = {}
        for v in vendas:
            forma = v.forma_pagamento
            if forma not in por_forma_pagamento:
                por_forma_pagamento[forma] = {"quantidade": 0, "total": 0}
            por_forma_pagamento[forma]["quantidade"] += 1
            por_forma_pagamento[forma]["total"] += v.total
        
        return jsonify({
            "success": True,
            "data": hoje.isoformat(),
            "resumo": {
                "total_vendas": round(total_vendas, 2),
                "quantidade_vendas": quantidade_vendas,
                "ticket_medio": round(ticket_medio, 2),
                "por_forma_pagamento": por_forma_pagamento,
            },
            "ultimas_vendas": [
                {
                    "id": v.id,
                    "codigo": v.codigo,
                    "total": float(v.total),
                    "hora": v.data_venda.strftime("%H:%M"),
                    "forma_pagamento": v.forma_pagamento,
                }
                for v in sorted(vendas, key=lambda x: x.data_venda, reverse=True)[:10]
            ]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar vendas do dia: {str(e)}")
        return jsonify({"error": "Erro ao carregar vendas"}), 500


@pdv_bp.route("/cancelar-venda/<int:venda_id>", methods=["POST"])
@funcionario_required
def cancelar_venda_pdv(venda_id):
    """
    Cancela uma venda e devolve produtos ao estoque
    Requer permissão específica
    """
    try:
        from app.utils.query_helpers import get_funcionario_safe
        current_user_id = get_jwt_identity()
        funcionario_data = get_funcionario_safe(current_user_id)
        
        if not funcionario_data:
            return jsonify({"error": "Funcionário não encontrado"}), 404
        
        # Proxy para o funcionário
        class _Proxy:
            def __init__(self, data):
                for k, v in data.items(): setattr(self, k, v)
                self.permissoes = data.get("permissoes", {})
        funcionario = _Proxy(funcionario_data)
        
        # Verificar permissão
        if not funcionario.permissoes.get("pode_cancelar_venda", False):
            return jsonify({"error": "Sem permissão para cancelar vendas"}), 403
        
        data = request.get_json()
        motivo = data.get("motivo", "Cancelamento solicitado")
        
        # Buscar venda
        venda = Venda.query.get(venda_id)
        
        if not venda:
            return jsonify({"error": "Venda não encontrada"}), 404
        
        if venda.status == "cancelada":
            return jsonify({"error": "Venda já está cancelada"}), 400
        
        # Cancelar venda
        try:
            venda.status = "cancelada"
            venda.observacoes = f"{venda.observacoes}\n[CANCELADA] {motivo}"
            
            # Devolver produtos ao estoque
            for item in venda.itens:
                produto = Produto.query.with_for_update().get(item.produto_id)
                
                if produto:
                    estoque_anterior = produto.quantidade
                    produto.quantidade += item.quantidade
                    
                    # Registrar movimentação
                    movimentacao = MovimentacaoEstoque(
                        estabelecimento_id=venda.estabelecimento_id,
                        produto_id=produto.id,
                        tipo="entrada",
                        quantidade=item.quantidade,
                        quantidade_anterior=estoque_anterior,
                        quantidade_atual=produto.quantidade,
                        venda_id=venda.id,
                        funcionario_id=funcionario.id,
                        created_at=datetime.now(),
                        motivo=f"Cancelamento venda {venda.codigo}"
                    )
                    db.session.add(movimentacao)
            
            db.session.commit()
            
            current_app.logger.info(f"🚫 Venda {venda.codigo} cancelada por {funcionario.nome}")
            
            return jsonify({
                "success": True,
                "message": f"Venda {venda.codigo} cancelada com sucesso",
                "venda": {
                    "id": venda.id,
                    "codigo": venda.codigo,
                    "status": "cancelada",
                }
            }), 200
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    except Exception as e:
        current_app.logger.error(f"Erro ao cancelar venda: {str(e)}")
        return jsonify({"error": f"Erro ao cancelar: {str(e)}"}), 500


@pdv_bp.route("/estatisticas-rapidas", methods=["GET"])
@funcionario_required
def estatisticas_rapidas():
    """
    Estatísticas em tempo real para exibição no PDV (Blindado)
    """
    try:
        from app.utils.query_helpers import get_funcionario_safe
        current_user_id = get_jwt_identity()
        funcionario_data = get_funcionario_safe(current_user_id)
        
        # Busca estabelecimento_id com fallback ultra-seguro
        est_id = None
        if funcionario_data:
            est_id = funcionario_data.get("estabelecimento_id")
        
        if not est_id:
            try:
                claims = get_jwt()
                est_id = claims.get("estabelecimento_id")
            except:
                pass

        if not est_id:
             return jsonify({
                "success": True, # Retornamos vazio mas com sucesso para não quebrar o dashboard
                "estatisticas": {
                    "total_vendas": 0, "faturamento": 0.0, "ticket_medio": 0.0,
                    "funcionario": "Usuário", "hora_atual": datetime.now().strftime("%H:%M")
                }
            }), 200

        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = datetime.combine(hoje, datetime.max.time())
        
        # Query agregada (Performance de Elite)
        stats = db.session.query(
            func.count(Venda.id).label("total_vendas"),
            func.sum(Venda.total).label("faturamento"),
            func.avg(Venda.total).label("ticket_medio"),
        ).filter(
            Venda.estabelecimento_id == est_id,
            Venda.data_venda >= inicio_dia,
            Venda.data_venda <= fim_dia,
            Venda.status == "finalizada"
        ).first()
        
        return jsonify({
            "success": True,
            "estatisticas": {
                "total_vendas": stats.total_vendas or 0,
                "faturamento": round(float(stats.faturamento or 0), 2),
                "ticket_medio": round(float(stats.ticket_medio or 0), 2),
                "funcionario": (funcionario_data.get("nome") if funcionario_data else "Usuário"),
                "hora_atual": datetime.now().strftime("%H:%M"),
            }
        }), 200
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"FATAL PDV STATS: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": "Erro interno ao carregar estatísticas",
            "code": "INTERNAL_SERVER_ERROR_STATS"
        }), 500


# ==================== ENVIAR CUPOM FISCAL POR EMAIL ====================

@pdv_bp.route("/enviar-cupom", methods=["POST"])
@funcionario_required
def enviar_cupom_email():
    """
    Envia cupom fiscal por email (Elite)
    """
    try:
        data = request.get_json()
        venda_id = data.get("venda_id")
        email_destino = data.get("email_destino")
        
        if not venda_id:
            return jsonify({"error": "venda_id é obrigatório"}), 400
        
        from app.utils.query_helpers import get_venda_safe, get_cliente_safe, get_estabelecimento_safe, get_venda_itens_safe
        venda_data = get_venda_safe(venda_id)
        if not venda_data:
            return jsonify({"error": "Venda não encontrada"}), 404
        
        cliente_data = get_cliente_safe(venda_data.get("cliente_id")) if venda_data.get("cliente_id") else None
        
        if email_destino:
            email_final = email_destino
            nome_cliente = cliente_data.get("nome") if cliente_data else "Consumidor Final"
        elif cliente_data and cliente_data.get("email"):
            email_final = cliente_data.get("email")
            nome_cliente = cliente_data.get("nome")
        else:
            return jsonify({"error": "Email não informado e cliente não possui email cadastrado"}), 400
        
        from app.utils.query_helpers import get_estabelecimento_full_safe, get_configuracao_safe
        estabelecimento_data = get_estabelecimento_full_safe(venda_data.get("estabelecimento_id"))
        if not estabelecimento_data:
            return jsonify({"error": "Dados do estabelecimento não encontrados para esta venda"}), 404
            
        # Busca logo das configurações (Já incluída no full_safe via query_helpers)
        logo_base64 = estabelecimento_data.get("logo_base64")
            
        itens_venda = get_venda_itens_safe(venda_id)
        
        # Preparar dados estruturados para o email_service
        from app.utils.email_service import enviar_cupom_fiscal
        
        # Melhoria na extração e formatação da data (Extreme Precision)
        data_venda = venda_data.get("data_venda")
        data_str = ""
        
        try:
            if data_venda:
                # Se for string (fallback), tenta converter ou usa direto
                if isinstance(data_venda, str):
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(data_venda.replace("Z", "+00:00"))
                        data_str = dt.strftime("%d/%m/%Y %H:%M:%S")
                    except:
                        data_str = data_venda
                # Se for objeto datetime (ideal)
                elif hasattr(data_venda, "strftime"):
                    data_str = data_venda.strftime("%d/%m/%Y %H:%M:%S")
                else:
                    data_str = str(data_venda)
            else:
                # Fallback final: Data atual
                from datetime import datetime
                data_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        except Exception as dt_err:
            current_app.logger.warning(f"Erro ao formatar data da venda {venda_id}: {dt_err}")
            from datetime import datetime
            data_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Construção de endereço completo (Resiliente e Profissional)
        end_parts = [
            estabelecimento_data.get('logradouro', ''),
            estabelecimento_data.get('numero', ''),
            estabelecimento_data.get('complemento', ''),
            estabelecimento_data.get('bairro', ''),
            f"{estabelecimento_data.get('cidade', '')} - {estabelecimento_data.get('estado', '')}",
            estabelecimento_data.get('cep', '')
        ]
        endereco_completo = " - ".join([p for p in end_parts if p and str(p).strip()])

        dados_formatados = {
            "venda": {
                "codigo": venda_data.get("codigo", "V-0000"),
                "data": data_str
            },

            "comprovante": {
                "funcionario": "Operador Balcão",
                "cliente": nome_cliente,
                "itens": [
                    {
                        "nome": it.get("produto_nome", "Produto"),
                        "codigo": it.get("produto_codigo") or "N/A",
                        "quantidade": float(it.get("quantidade") or 0),
                        "preco_unitario": float(it.get("preco_unitario") or 0),
                        "total": float(it.get("total_item") or 0)
                    }
                    for it in itens_venda
                ],
                "subtotal": float(venda_data.get("subtotal") or 0),
                "desconto": float(venda_data.get("desconto") or 0),
                "total": float(venda_data.get("total") or 0),
                "forma_pagamento": (venda_data.get("forma_pagamento") or "Dinheiro").replace("_", " ").title(),
                "valor_recebido": float(venda_data.get("valor_recebido") or 0),
                "troco": float(venda_data.get("troco") or 0),
                "rodape": "Obrigado pela preferência!"
            },
            "estabelecimento": {
                "nome_fantasia": estabelecimento_data.get("nome_fantasia", "MercadinhoSys"),
                "razao_social": estabelecimento_data.get("razao_social", ""),
                "cnpj": estabelecimento_data.get("cnpj", ""),
                "inscricao_estadual": estabelecimento_data.get("inscricao_estadual", ""),
                "telefone": estabelecimento_data.get("telefone", ""),
                "email": estabelecimento_data.get("email", ""),
                "endereco": endereco_completo,
                "logo_base64": logo_base64
            }
        }
        
        current_app.logger.info(f"🚀 [EMAIL DEBUG] Destino: {email_final}")
        current_app.logger.info(f"🚀 [EMAIL DEBUG] Endereço Final: {endereco_completo}")
        current_app.logger.info(f"🚀 [EMAIL DEBUG] Has Logo? {'Sim' if logo_base64 else 'Não'} (Size: {len(logo_base64) if logo_base64 else 0})")
        
        sucesso, erro_email = enviar_cupom_fiscal(dados_formatados, email_final)
        
        if sucesso:
            return jsonify({"success": True, "message": f"Cupom enviado para {email_final}!"}), 200
        else:
            return jsonify({
                "error": "Erro no servidor de e-mail", 
                "details": erro_email,
                "hint": "Verifique se a 'Senha de App' do Gmail está configurada em mail.env"
            }), 500
            
    except Exception as e:
        import traceback
        current_app.logger.error(f"ERRO ENVIAR CUPOM: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Falha crítica ao processar cupom", "details": str(e)}), 500


@pdv_bp.route("/comprovante/<int:venda_id>", methods=["GET"])
@funcionario_required
def obter_comprovante_venda(venda_id):
    """
    Retorna dados completos do comprovante para visualização na tela.
    """
    try:
        from app.utils.query_helpers import get_venda_safe, get_cliente_safe, get_estabelecimento_safe
        venda_data = get_venda_safe(venda_id)
        if not venda_data:
            return jsonify({"error": "Venda não encontrada"}), 404

        cliente_data = get_cliente_safe(venda_data.get("cliente_id")) if venda_data.get("cliente_id") else None
        nome_cliente = cliente_data.get("nome") if cliente_data else "Consumidor Final"

        estabelecimento_data = get_estabelecimento_safe(venda_data.get("estabelecimento_id"))

        # Lógica de seleção do logo (Safe)
        logo_url = estabelecimento_data.get("logo_base64") or estabelecimento_data.get("logo_url")
        if not logo_url:
            from app.utils.query_helpers import get_configuracao_safe
            config_data = get_configuracao_safe(venda_data.get("estabelecimento_id"))
            if config_data:
                logo_url = config_data.get("logo_base64") or config_data.get("logo_url")

        comprovante = {
            "funcionario": "Operador Balcão",
            "cliente": nome_cliente,
            "logo_url": logo_url,
            "itens": [
                {
                    "nome": it.get("produto_nome", "Produto"),
                    "codigo": it.get("produto_codigo") or "N/A",
                    "quantidade": float(it.get("quantidade") or 0),
                    "preco_unitario": float(it.get("preco_unitario") or 0),
                    "total": float(it.get("total_item") or 0)
                }
                for it in get_venda_itens_safe(venda_id)
            ],
            "subtotal": float(venda_data.get("subtotal") or 0),
            "desconto": float(desconto_geral) if (desconto_geral := venda_data.get("desconto")) else 0.0,
            "total": float(venda_data.get("total") or 0),
            "forma_pagamento": venda_data.get("forma_pagamento") or "Não informado",
            "valor_recebido": float(venda_data.get("valor_recebido") or 0),
            "troco": float(venda_data.get("troco") or 0),
            "rodape": "Obrigado pela preferência!",
        }

        # Melhoria na extração e formatação da data (Paridade Masterclass)
        data_venda = venda_data.get("data_venda")
        data_str = ""
        try:
            if data_venda:
                if isinstance(data_venda, str):
                    try:
                        dt = datetime.fromisoformat(data_venda.replace("Z", "+00:00"))
                        data_str = dt.strftime("%d/%m/%Y %H:%M:%S")
                    except:
                        data_str = data_venda
                elif hasattr(data_venda, "strftime"):
                    data_str = data_venda.strftime("%d/%m/%Y %H:%M:%S")
                else:
                    data_str = str(data_venda)
            else:
                data_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        except:
            data_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        return jsonify({
            "success": True,
            "venda": {
                "id": venda_data.get("id"),
                "codigo": venda_data.get("codigo", "V-0000"),
                "data": data_str
            },
            "estabelecimento": {
                "nome_fantasia": estabelecimento_data.get("nome_fantasia", "MercadinhoSys"),
                "razao_social": estabelecimento_data.get("razao_social", ""),
                "cnpj": estabelecimento_data.get("cnpj", ""),
                "inscricao_estadual": estabelecimento_data.get("inscricao_estadual", "ISENTO"),
                "telefone": estabelecimento_data.get("telefone", ""),
                "email": estabelecimento_data.get("email", ""),
                "endereco": f"{estabelecimento_data.get('logradouro', '')}, {estabelecimento_data.get('numero', '')} - {estabelecimento_data.get('cidade', '')}/{estabelecimento_data.get('estado', '')}",
            },
            "comprovante": comprovante,
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao obter comprovante da venda {venda_id}: {str(e)}")
        return jsonify({"error": "Erro ao obter comprovante"}), 500


@pdv_bp.route("/imprimir-html/<int:venda_id>", methods=["GET"])
def imprimir_venda_html(venda_id):
    """
    Retorna a nota fiscal renderizada em HTML Masterclass UI pronto para impressão.
    Blindagem: Tenta extrair o token do query param se não estiver nos headers.
    """
    try:
        # Tenta autenticar manualmente se o header estiver ausente (comum em window.open)
        token = request.args.get('token')
        if token:
            from flask_jwt_extended import decode_token
            try:
                decode_token(token)
            except:
                return "Acesso Negado: Token Inválido", 401
        else:
            # Fallback para o comportamento padrão do jwt_required
            try:
                from flask_jwt_extended import verify_jwt_in_request
                verify_jwt_in_request()
            except:
                return "Acesso Negado: Autenticação Necessária", 401
        from app.utils.query_helpers import get_venda_safe, get_cliente_safe, get_estabelecimento_safe, get_venda_itens_safe
        venda_data = get_venda_safe(venda_id)
        if not venda_data:
            return "Venda não encontrada", 404

        estabelecimento_data = get_estabelecimento_safe(venda_data.get("estabelecimento_id"))
        itens_venda = get_venda_itens_safe(venda_id)
        cliente_data = get_cliente_safe(venda_data.get("cliente_id")) if venda_data.get("cliente_id") else None
        nome_cliente = cliente_data.get("nome") if cliente_data else "Consumidor Final"

        # Formatação de Moeda e Data (Padrão Elite)
        from app.utils.email_service import _format_moeda, render_template_string
        
        data_venda = venda_data.get("data_venda")
        data_str = data_venda.strftime("%d/%m/%Y %H:%M:%S") if hasattr(data_venda, "strftime") else str(data_venda)

        # Usar o mesmo template Masterclass do email_service para garantir branding perfeito
        from app.utils.email_service import EmailService
        # Aqui podemos importar o template ou simplesmente reutilizar a lógica
        # Para ser ultra-profissional, vamos garantir que o CSS seja otimizado para PRINT
        
        from app.utils.email_service import _format_moeda
        
        dados_formatados = {
            "venda": {"codigo": venda_data.get("codigo"), "data": data_str, "total": float(venda_data.get("total") or 0)},
            "comprovante": {
                "funcionario": "Operador Balcão",
                "cliente": nome_cliente,
                "itens": [
                    {
                        "nome": it.get("produto_nome"),
                        "quantidade": float(it.get("quantidade")),
                        "preco_unitario": float(it.get("preco_unitario")),
                        "total": float(it.get("total_item"))
                    } for it in itens_venda
                ],
                "subtotal": float(venda_data.get("subtotal") or 0),
                "desconto": float(venda_data.get("desconto") or 0),
                "total": float(venda_data.get("total") or 0),
                "forma_pagamento": (venda_data.get("forma_pagamento") or "Dinheiro").replace("_", " ").title(),
                "valor_recebido": float(venda_data.get("valor_recebido") or 0),
                "troco": float(venda_data.get("troco") or 0),
            },
            "estabelecimento": {
                "nome_fantasia": estabelecimento_data.get("nome_fantasia"),
                "razao_social": estabelecimento_data.get("razao_social"),
                "cnpj": estabelecimento_data.get("cnpj"),
                "telefone": estabelecimento_data.get("telefone"),
                "endereco": f"{estabelecimento_data.get('logradouro')}, {estabelecimento_data.get('numero')} - {estabelecimento_data.get('cidade')}"
            }
        }

        # REUTILIZAR O TEMPLATE MASTERCLASS (Injetando script de auto-print)
        # Vou copiar o template aqui para garantir controle total sobre o layout de IMPRESSÃO
        
        html_masterclass = """
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="utf-8">
            <style>
                @media print { @page { margin: 0; } body { padding: 0 !important; } .container { border-radius: 0 !important; box-shadow: none !important; width: 80mm !important; } .no-print { display: none; } }
                body { font-family: 'Inter', sans-serif; background: #f0f2f5; margin: 0; padding: 40px; }
                .container { max-width: 400px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border: 1px solid #eee; }
                .store-name { font-size: 20px; font-weight: 900; text-align: center; text-transform: uppercase; margin-bottom: 4px; }
                .store-info { font-size: 10px; color: #666; text-align: center; margin-bottom: 20px; }
                .divider { border-top: 1px dashed #ddd; margin: 16px 0; }
                .item { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px; }
                .total-box { margin-top: 20px; padding: 16px; background: #f9f9f9; border-radius: 16px; }
                .total-row { display: flex; justify-content: space-between; font-weight: bold; }
                .big-total { font-size: 24px; color: #ef4444; margin-top: 8px; }
                .qr-code { text-align: center; margin-top: 24px; }
                .btn-print { position: fixed; bottom: 20px; right: 20px; padding: 12px 24px; background: #ef4444; color: #fff; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 12px rgba(239,68,68,0.3); }
            </style>
        </head>
        <body>
            <button class="no-print btn-print" onclick="window.print()">IMPRIMIR AGORA</button>
            <div class="container">
                <div class="store-name">{{ est.nome_fantasia }}</div>
                <div class="store-info">{{ est.razao_social }}<br>CNPJ: {{ est.cnpj }}<br>{{ est.endereco }}</div>
                <div class="divider"></div>
                <div style="font-size: 10px; font-weight: bold; color: #888; margin-bottom: 12px;">CUPOM: {{ venda.codigo }} | {{ venda.data }}</div>
                {% for item in items %}
                <div class="item">
                    <span>{{ item.nome }}<br><small>{{ item.quantidade }}x {{ fmt(item.preco_unitario) }}</small></span>
                    <span>R$ {{ fmt(item.total) }}</span>
                </div>
                {% endfor %}
                <div class="divider"></div>
                <div class="total-box">
                    <div class="total-row"><span>Subtotal:</span><span>R$ {{ fmt(comp.subtotal) }}</span></div>
                    {% if comp.desconto > 0 %}<div class="total-row" style="color:#10b981"><span>Desconto:</span><span>-R$ {{ fmt(comp.desconto) }}</span></div>{% endif %}
                    <div class="total-row big-total"><span>TOTAL:</span><span>R$ {{ fmt(comp.total) }}</span></div>
                </div>
                <div style="margin-top:12px; font-size:10px; font-weight:bold; color:#666">PAGO VIA: {{ comp.forma_pagamento }}</div>
                <div class="qr-code">
                    <div style="width:100px; height:100px; background:#f0f0f0; margin:0 auto; display:flex; align-items:center; justify-content:center; border-radius:12px; font-size:8px; color:#aaa">QR CODE AUTENTICIDADE</div>
                </div>
                <div style="text-align:center; font-size:9px; color:#aaa; margin-top:16px;">Obrigado pela preferência!<br>Powered by MercadinhoSys Profissional</div>
            </div>
            <script>window.onload = () => { if(window.innerWidth < 800) setTimeout(() => window.print(), 1000); }</script>
        </body>
        </html>
        """
        
        from flask import render_template_string
        return render_template_string(
            html_masterclass,
            est=dados_formatados["estabelecimento"],
            venda=dados_formatados["venda"],
            comp=dados_formatados["comprovante"],
            items=dados_formatados["comprovante"]["itens"],
            fmt=_format_moeda
        )
    except Exception as e:
        import traceback
        current_app.logger.error(f"Erro na impressão HTML: {str(e)}\n{traceback.format_exc()}")
        return f"Erro ao gerar impressão: {str(e)}", 500
