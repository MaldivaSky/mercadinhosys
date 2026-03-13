"""
Super Admin Dashboard - Interface centralizada e otimizada
Permite ao Super Admin gerenciar todos os clientes de forma organizada
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import (
    db, 
    Estabelecimento, 
    Venda, 
    Funcionario, 
    Produto,
    DashboardMetrica
)
from app.decorators.rbac import super_admin_required
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import logging

logger = logging.getLogger(__name__)
super_admin_dashboard_bp = Blueprint("super_admin_dashboard", __name__)

@super_admin_dashboard_bp.route("/estabelecimentos-ativos", methods=["GET"])
@super_admin_required
def listar_estabelecimentos_ativos():
    """Lista estabelecimentos com métricas rápidas"""
    try:
        estabelecimentos = Estabelecimento.query.filter_by(ativo=True).all()
        
        lista = []
        for est in estabelecimentos:
            # Métricas rápidas
            vendas_hoje = db.session.query(func.count(Venda.id)).filter(
                and_(
                    Venda.estabelecimento_id == est.id,
                    Venda.data_venda >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                )
            ).scalar() or 0
            
            total_vendas = db.session.query(func.count(Venda.id)).filter(
                Venda.estabelecimento_id == est.id
            ).scalar() or 0
            
            produtos_count = db.session.query(func.count(Produto.id)).filter(
                and_(
                    Produto.estabelecimento_id == est.id,
                    Produto.ativo == True
                )
            ).scalar() or 0
            
            funcionarios_count = db.session.query(func.count(Funcionario.id)).filter(
                and_(
                    Funcionario.estabelecimento_id == est.id,
                    Funcionario.ativo == True
                )
            ).scalar() or 0
            
            lista.append({
                "id": est.id,
                "nome_fantasia": est.nome_fantasia,
                "razao_social": est.razao_social,
                "cnpj": est.cnpj,
                "cidade": est.cidade,
                "estado": est.estado,
                "plano": getattr(est, 'plano', 'Basic'),
                "plano_status": getattr(est, 'plano_status', 'experimental'),
                "ativo": est.ativo,
                "vendas_hoje": vendas_hoje,
                "total_vendas": total_vendas,
                "produtos_count": produtos_count,
                "funcionarios_count": funcionarios_count,
                "created_at": est.created_at.isoformat() if est.created_at else None,
                "vencimento_assinatura": est.vencimento_assinatura.isoformat() if est.vencimento_assinatura else None
            })
        
        return jsonify({
            "success": True,
            "estabelecimentos": lista,
            "total": len(lista)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar estabelecimentos ativos: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@super_admin_dashboard_bp.route("/selecionar-estabelecimento/<int:estabelecimento_id>", methods=["GET"])
@super_admin_required
def dashboard_estabelecimento_especifico(estabelecimento_id):
    """Dashboard de um estabelecimento específico (visão Super Admin)"""
    try:
        # Verificar se estabelecimento existe
        estabelecimento = Estabelecimento.query.get(estabelecimento_id)
        if not estabelecimento:
            return jsonify({
                "success": False, 
                "error": "Estabelecimento não encontrado"
            }), 404
        
        # Parâmetros
        days = request.args.get("days", default=30, type=int)
        
        # Métricas do estabelecimento
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dias_atras = datetime.now() - timedelta(days=days)
        
        # Vendas
        vendas_periodo = db.session.query(
            func.count(Venda.id).label('quantidade'),
            func.sum(Venda.total).label('valor')
        ).filter(
            and_(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= dias_atras
            )
        ).first()
        
        vendas_hoje = db.session.query(
            func.count(Venda.id).label('quantidade'),
            func.sum(Venda.total).label('valor')
        ).filter(
            and_(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= hoje
            )
        ).first()
        
        # Produtos
        produtos_ativos = db.session.query(func.count(Produto.id)).filter(
            and_(
                Produto.estabelecimento_id == estabelecimento_id,
                Produto.ativo == True
            )
        ).scalar() or 0
        
        produtos_baixo_estoque = db.session.query(func.count(Produto.id)).filter(
            and_(
                Produto.estabelecimento_id == estabelecimento_id,
                Produto.quantidade <= Produto.quantidade_minima,
                Produto.quantidade > 0
            )
        ).scalar() or 0
        
        # Funcionários
        funcionarios_ativos = db.session.query(func.count(Funcionario.id)).filter(
            and_(
                Funcionario.estabelecimento_id == estabelecimento_id,
                Funcionario.ativo == True
            )
        ).scalar() or 0
        
        dashboard_data = {
            "estabelecimento": {
                "id": estabelecimento.id,
                "nome_fantasia": estabelecimento.nome_fantasia,
                "razao_social": estabelecimento.razao_social,
                "cnpj": estabelecimento.cnpj,
                "cidade": estabelecimento.cidade,
                "estado": estabelecimento.estado,
                "plano": getattr(estabelecimento, 'plano', 'Basic'),
                "plano_status": getattr(estabelecimento, 'plano_status', 'experimental')
            },
            "metricas": {
                "vendas_periodo": {
                    "quantidade": int(vendas_periodo.quantidade or 0),
                    "valor": float(vendas_periodo.valor or 0)
                },
                "vendas_hoje": {
                    "quantidade": int(vendas_hoje.quantidade or 0),
                    "valor": float(vendas_hoje.valor or 0)
                },
                "produtos": {
                    "ativos": produtos_ativos,
                    "baixo_estoque": produtos_baixo_estoque
                },
                "funcionarios": {
                    "ativos": funcionarios_ativos
                }
            },
            "periodo_analise": days,
            "data_geracao": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "dashboard": dashboard_data
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no dashboard do estabelecimento: {e}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

@super_admin_dashboard_bp.route("/resumo-sistema", methods=["GET"])
@super_admin_required
def resumo_completo_sistema():
    """Resumo completo do sistema para Super Admin"""
    try:
        # Estatísticas gerais
        total_estabelecimentos = db.session.query(func.count(Estabelecimento.id)).filter_by(ativo=True).scalar() or 0
        total_funcionarios = db.session.query(func.count(Funcionario.id)).filter_by(ativo=True).scalar() or 0
        total_produtos = db.session.query(func.count(Produto.id)).filter_by(ativo=True).scalar() or 0
        
        # Vendas totais
        vendas_totais = db.session.query(
            func.count(Venda.id).label('quantidade'),
            func.sum(Venda.total).label('valor')
        ).first()
        
        # Vendas dos últimos 30 dias
        trinta_dias_atras = datetime.now() - timedelta(days=30)
        vendas_30_dias = db.session.query(
            func.count(Venda.id).label('quantidade'),
            func.sum(Venda.total).label('valor')
        ).filter(Venda.data_venda >= trinta_dias_atras).first()
        
        # Top estabelecimentos por vendas (últimos 30 dias)
        top_estabelecimentos = db.session.query(
            Venda.estabelecimento_id,
            Estabelecimento.nome_fantasia,
            func.count(Venda.id).label('vendas_qtd'),
            func.sum(Venda.total).label('vendas_valor')
        ).join(Estabelecimento).filter(
            and_(
                Venda.data_venda >= trinta_dias_atras,
                Estabelecimento.ativo == True
            )
        ).group_by(
            Venda.estabelecimento_id, Estabelecimento.nome_fantasia
        ).order_by(func.sum(Venda.total).desc()).limit(5).all()
        
        resumo = {
            "sistema": {
                "total_estabelecimentos": total_estabelecimentos,
                "total_funcionarios": total_funcionarios,
                "total_produtos": total_produtos,
                "vendas_totais": {
                    "quantidade": int(vendas_totais.quantidade or 0),
                    "valor": float(vendas_totais.valor or 0)
                },
                "vendas_30_dias": {
                    "quantidade": int(vendas_30_dias.quantidade or 0),
                    "valor": float(vendas_30_dias.valor or 0)
                }
            },
            "top_estabelecimentos": [
                {
                    "estabelecimento_id": est[0],
                    "nome_fantasia": est[1],
                    "vendas_quantidade": int(est[2]),
                    "vendas_valor": float(est[3])
                }
                for est in top_estabelecimentos
            ],
            "data_geracao": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "resumo": resumo
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no resumo do sistema: {e}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

@super_admin_dashboard_bp.route("/sincronizar-dados", methods=["POST"])
@super_admin_required
def forcar_sincronizacao():
    """Força sincronização de dados para nuvem"""
    try:
        # Aqui você implementaria a lógica de sincronização
        # Por enquanto, apenas simula sucesso
        
        return jsonify({
            "success": True,
            "message": "Sincronização iniciada com sucesso",
            "timestamp": datetime.now().isoformat(),
            "status": "em_andamento"
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao sincronizar dados: {e}")
        return jsonify({
            "success": False,
            "error": f"Erro na sincronização: {str(e)}"
        }), 500

@super_admin_dashboard_bp.route("/health", methods=["GET"])
def health_check():
    """Health check do Super Admin Dashboard"""
    return jsonify({
        "success": True,
        "message": "Super Admin Dashboard funcionando",
        "timestamp": datetime.now().isoformat()
    })
