"""
Dashboard Routes - Blueprint limpo e simples
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.dashboard_cientifico import DashboardOrchestrator
from app.models import Funcionario, RegistroPonto
from app.decorators.decorator_jwt import gerente_ou_admin_required
import logging
from datetime import datetime
from sqlalchemy import and_

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)


def make_dashboard_cache_key():
    """
    Gera chave de cache única por estabelecimento.
    Permite que o cache seja compartilhado entre usuários do mesmo estabelecimento.
    """
    try:
        claims = get_jwt()
        est_id = claims.get("estabelecimento_id")
        return f"dashboard_cientifico_v1:{est_id}"
    except Exception:
        return None  # Não cacheia se falhar ao pegar ID


def get_establishment_id():
    """
    Obtém ID do estabelecimento diretamente das Claims do JWT (sem consulta ao banco).
    Garante integridade e performance.
    """
    claims = get_jwt()
    est_id = claims.get("estabelecimento_id")
    
    if est_id is None:
        # Fallback apenas para logs de erro, não tenta query no banco
        raise ValueError("Token inválido: estabelecimento_id não encontrado nas claims")
        
    return int(est_id)


@dashboard_bp.route("/cientifico", methods=["GET"])
@gerente_ou_admin_required
def dashboard_cientifico():
    """
    Endpoint para o Dashboard Científico.
    Suporta filtro por dias OU por datas específicas.
    """
    try:
        logger.info("🔥 Iniciando dashboard_cientifico endpoint")
        
        # 1. Obter contexto seguro (já validado pelo decorator)
        estabelecimento_id = get_establishment_id()
        logger.info(f"✅ Estabelecimento ID: {estabelecimento_id}")
        
        # 🔥 NOVO: Suportar filtro por datas específicas
        start_date_str = request.args.get('start_date', default=None, type=str)
        end_date_str = request.args.get('end_date', default=None, type=str)
        days = request.args.get('days', default=30, type=int)
        
        start_date_obj = None
        end_date_obj = None
        
        if start_date_str and end_date_str:
            try:
                from datetime import datetime as dt
                start_date_obj = dt.fromisoformat(start_date_str.replace('Z', '').replace('+00:00', ''))
                end_date_obj = dt.fromisoformat(end_date_str.replace('Z', '').replace('+00:00', ''))
                days = (end_date_obj - start_date_obj).days
                if days < 1:
                    days = 1
                logger.info(f"📊 Dashboard com datas específicas: {start_date_str} a {end_date_str} ({days} dias)")
            except Exception as date_err:
                logger.warning(f"Datas inválidas: {date_err}, usando days={days}")
                start_date_obj = None
                end_date_obj = None
        else:
            logger.info(f"📊 Dashboard solicitado para {days} dias")
        
        if days < 1:
            days = 1
        elif days > 365:
            days = 365
        
        orchestrator = DashboardOrchestrator(estabelecimento_id)
        data = orchestrator.get_scientific_dashboard(
            days=days,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        if not data.get("success", True):
            logger.error(f"❌ Orchestrator returned success=False: {data.get('error')}")
            return jsonify(data), 500

        logger.info(f"✅ Dashboard retornou com sucesso")

        # 4. Resposta Padronizada
        return jsonify({
            "success": True,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0",
                "cache_strategy": "smartcache",
                "period_days": days
            },
            "data": data
        }), 200
        
    except Exception as e:
        # Log detalhado para debug de infraestrutura
        import traceback
        logger.error(f"❌ Erro Crítico Dashboard Científico: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        # Diferenciação básica de erros (poderia ser expandida)
        error_msg = str(e)
        status_code = 500
        
        # Se for erro de conexão ou infra, mantém 500.
        # Se fosse erro de negócio conhecido, poderia ser 400/422.
        
        if "Banco de dados indisponível" in str(e):
            status_code = 503

        return jsonify({
            "success": False,
            "error": "Erro interno ao processar indicadores",
            "details": error_msg if current_app.debug else "Contate o suporte"
        }), status_code


@dashboard_bp.route("/rh/ponto/historico", methods=["GET"])
@gerente_ou_admin_required
def rh_ponto_historico():
    try:
        estabelecimento_id = get_establishment_id()

        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        funcionario_id = request.args.get("funcionario_id", type=int)
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=25, type=int)

        query = RegistroPonto.query.join(Funcionario).filter(
            RegistroPonto.estabelecimento_id == estabelecimento_id
        )

        if data_inicio:
            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            query = query.filter(RegistroPonto.data >= data_inicio_obj)
        if data_fim:
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d").date()
            query = query.filter(RegistroPonto.data <= data_fim_obj)
        if funcionario_id:
            query = query.filter(RegistroPonto.funcionario_id == funcionario_id)

        query = query.order_by(RegistroPonto.data.desc(), RegistroPonto.hora.desc())

        paginated = query.paginate(page=page, per_page=min(max(per_page, 1), 200), error_out=False)
        items = [r.to_dict() for r in paginated.items]

        return jsonify({
            "success": True,
            "data": {
                "items": items,
                "page": paginated.page,
                "per_page": paginated.per_page,
                "total": paginated.total,
                "pages": paginated.pages
            }
        }), 200

    except Exception as e:
        logger.error(f"Erro rh_ponto_historico: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500


@dashboard_bp.route("/rh/ponto/espelho", methods=["GET"])
@gerente_ou_admin_required
def rh_ponto_espelho():
    """
    Endpoint para gerar espelho de ponto de um funcionário específico.
    Retorna registros diários agrupados com resumo do período.
    """
    try:
        from collections import defaultdict
        from sqlalchemy import func
        
        estabelecimento_id = get_establishment_id()
        
        funcionario_id = request.args.get("funcionario_id", type=int)
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        
        if not funcionario_id or not data_inicio or not data_fim:
            return jsonify({
                "success": False,
                "message": "Parâmetros obrigatórios: funcionario_id, data_inicio, data_fim"
            }), 400
        
        # Buscar funcionário
        funcionario = Funcionario.query.filter_by(
            id=funcionario_id,
            estabelecimento_id=estabelecimento_id
        ).first()
        
        if not funcionario:
            return jsonify({
                "success": False,
                "message": "Funcionário não encontrado"
            }), 404
        
        # Converter datas
        data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d").date()
        
        # Buscar registros
        registros = RegistroPonto.query.filter(
            and_(
                RegistroPonto.funcionario_id == funcionario_id,
                RegistroPonto.estabelecimento_id == estabelecimento_id,
                RegistroPonto.data >= data_inicio_obj,
                RegistroPonto.data <= data_fim_obj
            )
        ).order_by(RegistroPonto.data, RegistroPonto.hora).all()
        
        # Agrupar por dia
        registros_por_dia = defaultdict(list)
        for r in registros:
            registros_por_dia[r.data].append(r)
        
        # Processar registros diários
        registros_diarios = []
        total_dias_trabalhados = 0
        total_atrasos = 0
        total_minutos_atraso = 0
        total_horas_extras = 0
        total_horas_trabalhadas = 0
        
        for data, regs in sorted(registros_por_dia.items()):
            entrada = None
            saida = None
            intervalo_inicio = None
            intervalo_fim = None
            minutos_atraso = 0
            minutos_extras = 0
            observacao = None
            
            for r in regs:
                if r.tipo_registro == 'entrada':
                    entrada = r.hora.strftime('%H:%M') if r.hora else None
                    minutos_atraso = r.minutos_atraso or 0
                elif r.tipo_registro == 'saida_almoco' or r.tipo_registro == 'saida':
                    saida = r.hora.strftime('%H:%M') if r.hora else None
                    minutos_extras = r.minutos_extras or 0 if hasattr(r, 'minutos_extras') else 0
                elif r.tipo_registro == 'retorno_almoco' or r.tipo_registro == 'intervalo_inicio':
                    intervalo_inicio = r.hora.strftime('%H:%M') if r.hora else None
                elif r.tipo_registro == 'intervalo_fim':
                    intervalo_fim = r.hora.strftime('%H:%M') if r.hora else None
                
                if r.observacao:
                    observacao = r.observacao
            
            # Calcular horas trabalhadas (simplificado)
            horas_trabalhadas = 0
            if entrada and saida:
                try:
                    entrada_time = datetime.strptime(entrada, '%H:%M')
                    saida_time = datetime.strptime(saida, '%H:%M')
                    diff = (saida_time - entrada_time).total_seconds() / 60
                    
                    # Descontar intervalo se houver
                    if intervalo_inicio and intervalo_fim:
                        intervalo_inicio_time = datetime.strptime(intervalo_inicio, '%H:%M')
                        intervalo_fim_time = datetime.strptime(intervalo_fim, '%H:%M')
                        intervalo_minutos = (intervalo_fim_time - intervalo_inicio_time).total_seconds() / 60
                        diff -= intervalo_minutos
                    
                    horas_trabalhadas = max(0, diff)
                except:
                    horas_trabalhadas = 0
            
            registros_diarios.append({
                "data": data.isoformat(),
                "entrada": entrada,
                "saida": saida,
                "intervalo_inicio": intervalo_inicio,
                "intervalo_fim": intervalo_fim,
                "minutos_atraso": minutos_atraso,
                "minutos_extras": minutos_extras,
                "horas_trabalhadas": horas_trabalhadas,
                "observacao": observacao
            })
            
            if entrada or saida:
                total_dias_trabalhados += 1
            if minutos_atraso > 0:
                total_atrasos += 1
                total_minutos_atraso += minutos_atraso
            total_horas_extras += minutos_extras / 60
            total_horas_trabalhadas += horas_trabalhadas / 60
        
        # Calcular média
        media_horas_dia = total_horas_trabalhadas / total_dias_trabalhados if total_dias_trabalhados > 0 else 0
        
        return jsonify({
            "success": True,
            "data": {
                "funcionario_id": funcionario.id,
                "nome": funcionario.nome,
                "cargo": funcionario.cargo,
                "registros_diarios": registros_diarios,
                "resumo": {
                    "total_dias_trabalhados": total_dias_trabalhados,
                    "total_atrasos": total_atrasos,
                    "total_minutos_atraso": total_minutos_atraso,
                    "total_horas_extras": round(total_horas_extras, 2),
                    "total_horas_trabalhadas": round(total_horas_trabalhadas, 2),
                    "media_horas_dia": round(media_horas_dia, 2)
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro rh_ponto_espelho: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500






@dashboard_bp.route("/executivo", methods=["GET"])
@gerente_ou_admin_required
def dashboard_executivo():
    try:
        estabelecimento_id = get_establishment_id()
        days = request.args.get("days", default=30, type=int)
        orchestrator = DashboardOrchestrator(estabelecimento_id)
        dashboard_data = orchestrator.get_executive_dashboard(days)
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Erro no dashboard executivo: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/analise/<tipo>", methods=["GET"])
@gerente_ou_admin_required
def analise_detalhada(tipo: str):
    try:
        estabelecimento_id = get_establishment_id()
        days = request.args.get("days", default=90, type=int)
        orchestrator = DashboardOrchestrator(estabelecimento_id)
        analysis_data = orchestrator.get_detailed_analysis(tipo, days)
        return jsonify({"success": True, "analysis_type": tipo, "data": analysis_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/status", methods=["GET"])
@jwt_required()
def dashboard_status():
    return jsonify({"status": "operational"})
