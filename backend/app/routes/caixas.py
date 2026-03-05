from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Caixa, MovimentacaoCaixa, Estabelecimento, Funcionario

caixas_bp = Blueprint("caixas", __name__)

@caixas_bp.route("/atual", methods=["GET"])
@jwt_required()
def obter_caixa_atual():
    """Retorna o caixa atualmente aberto para o funcionário logado"""
    try:
        user_id = int(get_jwt_identity())
        
        caixa = Caixa.query.filter_by(
            funcionario_id=user_id,
            status="aberto"
        ).order_by(Caixa.data_abertura.desc()).first()

        if not caixa:
            return jsonify({"success": True, "data": None}), 200

        return jsonify({"success": True, "data": caixa.to_dict()}), 200
    except Exception as e:
        print(f"Erro ao obter caixa atual: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@caixas_bp.route("/abrir", methods=["POST"])
@jwt_required()
def abrir_caixa():
    """Abre um novo caixa para o funcionário logado"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        saldo_inicial = float(data.get("saldo_inicial", 0.0))
        observacoes = data.get("observacoes", "")

        funcionario = Funcionario.query.get(user_id)
        if not funcionario:
            return jsonify({"success": False, "error": "Funcionário não encontrado"}), 404

        # Verificar se já existe caixa aberto
        caixa_existente = Caixa.query.filter_by(
            funcionario_id=user_id,
            status="aberto"
        ).first()

        if caixa_existente:
            return jsonify({
                "success": False, 
                "error": "Você já possui um caixa em aberto. Feche-o antes de abrir um novo."
            }), 400

        # Gerar número de caixa simples
        numero_caixa = f"CX-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id}"

        novo_caixa = Caixa(
            estabelecimento_id=funcionario.estabelecimento_id,
            funcionario_id=user_id,
            numero_caixa=numero_caixa,
            saldo_inicial=saldo_inicial,
            saldo_atual=saldo_inicial,
            status="aberto",
            observacoes=observacoes
        )

        db.session.add(novo_caixa)
        db.session.commit()

        # Registrar a abertura como movimentação inicial
        if saldo_inicial > 0:
            mov = MovimentacaoCaixa(
                caixa_id=novo_caixa.id,
                estabelecimento_id=novo_caixa.estabelecimento_id,
                tipo="abertura",
                valor=saldo_inicial,
                forma_pagamento="DINHEIRO",
                descricao="Saldo Inicial (Abertura de Caixa)",
                observacoes="Lançamento automático de abertura"
            )
            db.session.add(mov)
            db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Caixa aberto com sucesso", 
            "data": novo_caixa.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao abrir caixa: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@caixas_bp.route("/fechar", methods=["POST"])
@jwt_required()
def fechar_caixa():
    """Fecha o caixa atual do funcionário"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        # Valor que o operador contou no caixa
        valor_informado = float(data.get("valor_informado", 0.0))
        observacoes_fechamento = data.get("observacoes", "")

        caixa = Caixa.query.filter_by(
            funcionario_id=user_id,
            status="aberto"
        ).order_by(Caixa.data_abertura.desc()).first()

        if not caixa:
            return jsonify({"success": False, "error": "Nenhum caixa aberto encontrado"}), 404

        # Diferença entre o esperado e o informado (Quebra de Caixa)
        diferenca = valor_informado - float(caixa.saldo_atual)

        caixa.saldo_final = valor_informado
        caixa.data_fechamento = datetime.utcnow()
        caixa.status = "fechado"
        
        obs_geral = f"{caixa.observacoes or ''} | Fechamento: {observacoes_fechamento}"
        if abs(diferenca) > 0.01:
            obs_geral += f" | ATENÇÃO: Quebra de caixa de {'+' if diferenca > 0 else ''}{diferenca:.2f}"
            
        caixa.observacoes = obs_geral
        
        # Registrar movimentacao de fechamento
        mov = MovimentacaoCaixa(
            caixa_id=caixa.id,
            estabelecimento_id=caixa.estabelecimento_id,
            tipo="fechamento",
            valor=valor_informado,
            descricao="Fechamento de Caixa",
            observacoes=f"Diferença apurada: {diferenca:.2f}"
        )
        db.session.add(mov)

        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Caixa fechado com sucesso", 
            "data": caixa.to_dict(),
            "resumo": {
                "saldo_sistema": float(caixa.saldo_atual),
                "valor_informado": valor_informado,
                "diferenca": diferenca
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao fechar caixa: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@caixas_bp.route("/movimentacao", methods=["POST"])
@jwt_required()
def registrar_movimentacao():
    """Registra uma Sangria ou Suprimento"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        tipo = data.get("tipo") # "sangria" ou "suprimento"
        valor = float(data.get("valor", 0.0))
        descricao = data.get("descricao", "")
        observacoes = data.get("observacoes", "")
        forma_pagamento = data.get("forma_pagamento", "DINHEIRO")

        if tipo not in ["sangria", "suprimento"]:
            return jsonify({"success": False, "error": "Tipo inválido. Use 'sangria' ou 'suprimento'"}), 400
            
        if valor <= 0:
            return jsonify({"success": False, "error": "O valor deve ser maior que zero"}), 400

        caixa = Caixa.query.filter_by(
            funcionario_id=user_id,
            status="aberto"
        ).order_by(Caixa.data_abertura.desc()).first()

        if not caixa:
            return jsonify({"success": False, "error": "Nenhum caixa aberto encontrado"}), 404

        mov = MovimentacaoCaixa(
            caixa_id=caixa.id,
            estabelecimento_id=caixa.estabelecimento_id,
            tipo=tipo,
            valor=valor, # mantendo positivo na tabela
            forma_pagamento=forma_pagamento,
            descricao=descricao,
            observacoes=observacoes
        )
        
        # Atualizar saldo atual do caixa
        if tipo == "sangria":
            caixa.saldo_atual = float(caixa.saldo_atual) - valor
        else:
            caixa.saldo_atual = float(caixa.saldo_atual) + valor
            
        db.session.add(mov)
        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Movimentação registrada com sucesso", 
            "data": mov.to_dict(),
            "saldo_atual": float(caixa.saldo_atual)
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar movimentação de caixa: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@caixas_bp.route("/atual/movimentacoes", methods=["GET"])
@jwt_required()
def obter_movimentacoes_caixa_atual():
    """Retorna as movimentações do caixa atualmente aberto para o funcionário logado"""
    try:
        user_id = int(get_jwt_identity())
        
        caixa = Caixa.query.filter_by(
            funcionario_id=user_id,
            status="aberto"
        ).order_by(Caixa.data_abertura.desc()).first()

        if not caixa:
            return jsonify({"success": False, "error": "Nenhum caixa aberto encontrado"}), 404

        movimentacoes = MovimentacaoCaixa.query.filter_by(
            caixa_id=caixa.id
        ).order_by(MovimentacaoCaixa.created_at.desc()).all()

        return jsonify({
            "success": True, 
            "data": [mov.to_dict() for mov in movimentacoes]
        }), 200
    except Exception as e:
        print(f"Erro ao obter movimentações do caixa: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@caixas_bp.route("/atual/resumo", methods=["GET"])
@jwt_required()
def obter_resumo_caixa_atual():
    """Retorna o resumo financeiro do turno: totais por forma de pagamento, sangrias e suprimentos"""
    try:
        user_id = int(get_jwt_identity())

        caixa = Caixa.query.filter_by(
            funcionario_id=user_id,
            status="aberto"
        ).order_by(Caixa.data_abertura.desc()).first()

        if not caixa:
            return jsonify({"success": False, "error": "Nenhum caixa aberto encontrado"}), 404

        from app.models import MovimentacaoCaixa
        from collections import defaultdict

        # ─── Normalização de formas de pagamento ──────────────────────────────
        NORMALIZE_MAP = {
            "dinheiro": "dinheiro",
            "cartao_credito": "cartao_credito",
            "cartao_debito": "cartao_debito",
            "pix": "pix",
            "fiado": "fiado",
            "outros": "outros",
        }

        def normalizar_forma(forma_raw: str) -> str:
            if not forma_raw: return "outros"
            # Remove acentos, espaços e converte para minúsculo
            key = str(forma_raw).strip().lower()
            key = key.replace("é", "e").replace("ê", "e").replace("ã", "a").replace("á", "a")
            
            if "credito" in key: return "cartao_credito"
            if "debito" in key: return "cartao_debito"
            if "pix" in key: return "pix"
            if "dinheiro" in key: return "dinheiro"
            if "fiado" in key: return "fiado"
            
            return "outros"

        # Buscar todas as movimentações do caixa atual
        movimentacoes = MovimentacaoCaixa.query.filter_by(caixa_id=caixa.id).all()
        
        totais_por_forma = defaultdict(lambda: {"quantidade": 0, "total": 0.0})
        
        # Inicializar formas fixas
        FORMAS_FIXAS = ["dinheiro", "cartao_debito", "cartao_credito", "pix", "fiado"]
        for f in FORMAS_FIXAS: totais_por_forma[f]

        total_sangrias = 0.0
        total_suprimentos = 0.0
        total_vendas = 0.0

        for m in movimentacoes:
            valor = float(m.valor or 0)
            tipo = m.tipo.lower()
            
            if tipo == "venda":
                forma = normalizar_forma(m.forma_pagamento)
                totais_por_forma[forma]["quantidade"] += 1
                totais_por_forma[forma]["total"] += valor
                total_vendas += valor
            elif tipo == "sangria":
                total_sangrias += valor
            elif tipo == "suprimento":
                total_suprimentos += valor
            # 'abertura' e 'fechamento' não entram no cálculo de vendas/sangrias/suprimentos fixos

        # Saldo esperado na gaveta (Dinheiro Inicial + Vendas Dinheiro + Suprimentos - Sangrias)
        vendas_dinheiro = totais_por_forma["dinheiro"]["total"]
        saldo_esperado_gaveta = (
            float(caixa.saldo_inicial or 0) 
            + vendas_dinheiro 
            + total_suprimentos 
            - total_sangrias
        )

        return jsonify({
            "success": True,
            "data": {
                "caixa_id": caixa.id,
                "saldo_inicial": float(caixa.saldo_inicial or 0),
                "saldo_atual": float(caixa.saldo_atual or 0),
                "saldo_esperado_gaveta": round(saldo_esperado_gaveta, 2),
                "total_vendas": round(total_vendas, 2),
                "total_sangrias": round(total_sangrias, 2),
                "total_suprimentos": round(total_suprimentos, 2),
                "por_forma_pagamento": dict(totais_por_forma),
                "data_abertura": caixa.data_abertura.isoformat() if caixa.data_abertura else None,
            }
        }), 200
    except Exception as e:
        print(f"Erro ao obter resumo do caixa: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
