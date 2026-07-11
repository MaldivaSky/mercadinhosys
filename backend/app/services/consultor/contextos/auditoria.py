from app.models import Auditoria, db
from sqlalchemy import desc

def montar_contexto(estabelecimento_id: int, is_manager: bool = True) -> dict:
    """Monta o contexto de Auditoria e Logs para o consultor IA.
    Acesso restrito apenas para administradores e gestores.
    """
    if not is_manager:
        return {"aviso": "Acesso negado. Apenas gestores podem visualizar os logs de auditoria."}

    contexto = {}

    q = Auditoria.query
    if str(estabelecimento_id).lower() != 'all':
        q = q.filter(Auditoria.estabelecimento_id == estabelecimento_id)

    # 1. Últimos 30 logs de auditoria
    ultimos_logs = q.order_by(desc(Auditoria.data_evento)).limit(30).all()
    
    contexto["ultimos_logs"] = [
        {
            "data_hora": log.data_evento.strftime("%d/%m/%Y %H:%M:%S") if log.data_evento else "",
            "usuario": log.usuario.nome if log.usuario else "Sistema",
            "evento": log.tipo_evento,
            "descricao": log.descricao
        }
        for log in ultimos_logs
    ]

    return contexto
