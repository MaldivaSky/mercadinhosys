# app/routes/rh.py
# Módulo de RH - Justificativas de ponto e Benefícios de funcionários

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt, jwt_required
from datetime import datetime, date
from decimal import Decimal
import os

from app.models import (
    db,
    Funcionario,
    Beneficio,
    FuncionarioBeneficio,
    JustificativaPonto,
)
from app.decorators.decorator_jwt import funcionario_required

rh_bp = Blueprint("rh", __name__)


# ============================================
# JUSTIFICATIVAS DE PONTO
# ============================================


@rh_bp.route("/justificativas", methods=["GET"])
@funcionario_required
def listar_justificativas():
    """Lista justificativas de ponto com filtros opcionais."""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")

        query = JustificativaPonto.query.filter_by(
            estabelecimento_id=estabelecimento_id
        )

        # Filtros opcionais
        funcionario_id = request.args.get("funcionario_id")
        tipo = request.args.get("tipo")
        status = request.args.get("status")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")

        if funcionario_id:
            query = query.filter(JustificativaPonto.funcionario_id == funcionario_id)
        if tipo:
            query = query.filter(JustificativaPonto.tipo == tipo)
        if status:
            query = query.filter(JustificativaPonto.status == status)
        if data_inicio:
            query = query.filter(
                JustificativaPonto.data >= datetime.strptime(data_inicio, "%Y-%m-%d").date()
            )
        if data_fim:
            query = query.filter(
                JustificativaPonto.data <= datetime.strptime(data_fim, "%Y-%m-%d").date()
            )

        justificativas = query.order_by(JustificativaPonto.created_at.desc()).all()

        return jsonify({
            "success": True,
            "data": [j.to_dict() for j in justificativas],
            "total": len(justificativas),
            "resumo": {
                "pendentes": sum(1 for j in justificativas if j.status == "pendente"),
                "aprovados": sum(1 for j in justificativas if j.status == "aprovado"),
                "rejeitados": sum(1 for j in justificativas if j.status == "rejeitado"),
            },
        })

    except Exception as e:
        current_app.logger.error(f"Erro ao listar justificativas: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@rh_bp.route("/justificativas", methods=["POST"])
@funcionario_required
def criar_justificativa():
    """Cria uma nova justificativa de ponto."""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")

        # Suporta tanto JSON quanto multipart/form-data
        if request.content_type and "multipart/form-data" in request.content_type:
            funcionario_id = request.form.get("funcionario_id")
            tipo = request.form.get("tipo")
            data_str = request.form.get("data")
            motivo = request.form.get("motivo")
            documento = request.files.get("documento")
        else:
            data = request.get_json()
            funcionario_id = data.get("funcionario_id")
            tipo = data.get("tipo")
            data_str = data.get("data")
            motivo = data.get("motivo")
            documento = None

        if not all([funcionario_id, tipo, data_str, motivo]):
            return jsonify({
                "success": False,
                "message": "Campos obrigatórios: funcionario_id, tipo, data, motivo",
            }), 400

        # Salvar documento se enviado
        documento_url = None
        if documento:
            upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER", "uploads"), "justificativas")
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"just_{funcionario_id}_{data_str}_{documento.filename}"
            filepath = os.path.join(upload_dir, filename)
            documento.save(filepath)
            documento_url = f"/uploads/justificativas/{filename}"

        justificativa = JustificativaPonto(
            estabelecimento_id=estabelecimento_id,
            funcionario_id=int(funcionario_id),
            tipo=tipo,
            data=datetime.strptime(data_str, "%Y-%m-%d").date(),
            motivo=motivo,
            documento_url=documento_url,
            status="pendente",
        )

        db.session.add(justificativa)
        db.session.commit()

        return jsonify({
            "success": True,
            "data": justificativa.to_dict(),
            "message": "Justificativa criada com sucesso",
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar justificativa: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@rh_bp.route("/justificativas/<int:justificativa_id>/responder", methods=["PUT"])
@funcionario_required
def responder_justificativa(justificativa_id):
    """Aprova ou rejeita uma justificativa (apenas gerente/admin)."""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        user_id = claims.get("funcionario_id")
        role = claims.get("role", "")

        if role not in ("ADMIN", "GERENTE"):
            return jsonify({
                "success": False,
                "message": "Apenas gerentes ou administradores podem responder justificativas",
            }), 403

        justificativa = JustificativaPonto.query.filter_by(
            id=justificativa_id,
            estabelecimento_id=estabelecimento_id,
        ).first()

        if not justificativa:
            return jsonify({"success": False, "message": "Justificativa não encontrada"}), 404

        data = request.get_json()
        acao = data.get("acao")  # 'aprovar' ou 'rejeitar'

        if acao == "aprovar":
            justificativa.status = "aprovado"
        elif acao == "rejeitar":
            justificativa.status = "rejeitado"
            justificativa.motivo_rejeicao = data.get("motivo_rejeicao", "")
        else:
            return jsonify({"success": False, "message": "Ação deve ser 'aprovar' ou 'rejeitar'"}), 400

        justificativa.aprovador_id = user_id
        justificativa.data_resposta = datetime.utcnow()

        db.session.commit()

        return jsonify({
            "success": True,
            "data": justificativa.to_dict(),
            "message": f"Justificativa {justificativa.status} com sucesso",
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao responder justificativa: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ============================================
# BENEFÍCIOS
# ============================================


@rh_bp.route("/beneficios", methods=["GET"])
@funcionario_required
def listar_beneficios():
    """Lista benefícios atribuídos a funcionários."""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")

        funcionario_id = request.args.get("funcionario_id")
        ativo = request.args.get("ativo")

        query = db.session.query(FuncionarioBeneficio).join(
            Beneficio, FuncionarioBeneficio.beneficio_id == Beneficio.id
        ).join(
            Funcionario, FuncionarioBeneficio.funcionario_id == Funcionario.id
        ).filter(
            Beneficio.estabelecimento_id == estabelecimento_id
        )

        if funcionario_id:
            query = query.filter(FuncionarioBeneficio.funcionario_id == funcionario_id)
        if ativo is not None:
            query = query.filter(FuncionarioBeneficio.ativo == (ativo in ("true", "True", "1")))

        registros = query.all()

        result = []
        for fb in registros:
            result.append({
                "id": fb.id,
                "funcionario_id": fb.funcionario_id,
                "funcionario_nome": fb.funcionario.nome if fb.funcionario else None,
                "funcionario_cargo": fb.funcionario.cargo if fb.funcionario else None,
                "beneficio_id": fb.beneficio_id,
                "nome_beneficio": fb.beneficio.nome if fb.beneficio else None,
                "descricao": fb.beneficio.descricao if fb.beneficio else None,
                "tipo": fb.beneficio.nome.lower().replace(" ", "_") if fb.beneficio else None,
                "valor_mensal": float(fb.valor) if fb.valor else 0.0,
                "data_inicio": fb.data_inicio.isoformat() if fb.data_inicio else None,
                "ativo": fb.ativo,
            })

        return jsonify({
            "success": True,
            "data": result,
            "total": len(result),
        })

    except Exception as e:
        current_app.logger.error(f"Erro ao listar benefícios: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@rh_bp.route("/beneficios", methods=["POST"])
@funcionario_required
def criar_beneficio_funcionario():
    """Atribui um benefício a um funcionário."""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")

        data = request.get_json()
        funcionario_id = data.get("funcionario_id")
        nome_beneficio = data.get("nome_beneficio")
        valor_mensal = data.get("valor_mensal", 0)
        data_inicio = data.get("data_inicio")

        if not funcionario_id or not nome_beneficio:
            return jsonify({
                "success": False,
                "message": "Campos obrigatórios: funcionario_id, nome_beneficio",
            }), 400

        # Buscar ou criar o benefício
        beneficio = Beneficio.query.filter_by(
            estabelecimento_id=estabelecimento_id,
            nome=nome_beneficio,
        ).first()

        if not beneficio:
            beneficio = Beneficio(
                estabelecimento_id=estabelecimento_id,
                nome=nome_beneficio,
                descricao=data.get("observacao", ""),
                valor_padrao=Decimal(str(valor_mensal)) if valor_mensal else Decimal("0"),
                ativo=True,
            )
            db.session.add(beneficio)
            db.session.flush()

        fb = FuncionarioBeneficio(
            funcionario_id=int(funcionario_id),
            beneficio_id=beneficio.id,
            valor=Decimal(str(valor_mensal)) if valor_mensal else Decimal("0"),
            data_inicio=datetime.strptime(data_inicio, "%Y-%m-%d").date() if data_inicio else date.today(),
            ativo=True,
        )
        db.session.add(fb)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Benefício atribuído com sucesso",
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar benefício: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@rh_bp.route("/banco-horas", methods=["GET"])
@funcionario_required
def listar_banco_horas():
    """Lista banco de horas dos funcionários."""
    try:
        from app.models import BancoHoras

        claims = get_jwt()
        estabelecimento_id = claims.get("estabelecimento_id")
        funcionario_id = request.args.get("funcionario_id")
        mes_referencia = request.args.get("mes_referencia")

        query = db.session.query(BancoHoras).join(
            Funcionario, BancoHoras.funcionario_id == Funcionario.id
        ).filter(
            Funcionario.estabelecimento_id == estabelecimento_id
        )

        if funcionario_id:
            query = query.filter(BancoHoras.funcionario_id == funcionario_id)
        if mes_referencia:
            query = query.filter(BancoHoras.mes_referencia == mes_referencia)

        registros = query.order_by(BancoHoras.mes_referencia.desc()).all()

        result = []
        for bh in registros:
            saldo_horas = bh.saldo_minutos / 60.0
            result.append({
                "id": bh.id,
                "funcionario_id": bh.funcionario_id,
                "funcionario_nome": bh.funcionario.nome if bh.funcionario else None,
                "funcionario_cargo": bh.funcionario.cargo if bh.funcionario else None,
                "mes_referencia": bh.mes_referencia,
                "saldo_minutos": bh.saldo_minutos,
                "saldo_horas": round(saldo_horas, 1),
                "saldo_formatado": f"{'+' if saldo_horas >= 0 else ''}{saldo_horas:.1f}h",
                "valor_hora_extra": float(bh.valor_hora_extra) if bh.valor_hora_extra else 0,
                "horas_trabalhadas": round(bh.horas_trabalhadas_minutos / 60.0, 1) if bh.horas_trabalhadas_minutos else 0,
                "horas_esperadas": round(bh.horas_esperadas_minutos / 60.0, 1) if bh.horas_esperadas_minutos else 0,
                "status": "positivo" if bh.saldo_minutos > 0 else "negativo" if bh.saldo_minutos < 0 else "zerado",
            })

        return jsonify({
            "success": True,
            "data": result,
            "total": len(result),
        })

    except Exception as e:
        current_app.logger.error(f"Erro ao listar banco de horas: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
