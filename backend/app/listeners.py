from sqlalchemy import event, inspect
from app.models import db, AuditoriaSincronia, Auditoria
import json
from flask import g
from datetime import datetime

# Tabelas que devem ser sincronizadas com a nuvem (Integridade de Dados)
TABELAS_SINCRONIZAVEIS = [
    "produtos", "categorias_produto", "fornecedores", "clientes", 
    "vendas", "venda_itens", "pagamentos", "movimentacao_estoque",
    "caixas", "transacoes_caixa", "funcionarios", "estabelecimentos",
    "despesas", "contas_pagar", "estoque_lotes"
]

# Tabelas que aparecem no MONITOR do Super Admin (Inteligência de Negócio)
# Filtramos apenas o que é "Vital" para a Holding ver em tempo real.
TABELAS_MONITOR_MASTER = {
    "vendas": "Venda Realizada",
    "pedidos_compra": "Novo Pedido de Compra",
    "despesas": "Nova Despesa Registrada",
    "produtos": "Alteração em Produto/Preço",
    "clientes": "Movimentação de Cliente",
    "movimentacao_estoque": "Ajuste de Estoque (Perda/Ganho)",
    "movimentacoes_caixa": "Intervenção de Caixa (Sangria/Suprimento)",
}

def object_to_dict(obj):
    """Converte objeto SQLAlchemy para dict de forma segura"""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    
    # Fallback para inspeção de colunas
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

def registrar_evento_forense(mapper, connection, target, operacao):
    """
    Hook global para Auditoria Forense e Sincronia.
    Captura o estado do objeto para reconstrução total e auditoria.
    """
    # Evitar recursão ou processamento em simulação massiva
    import os
    if isinstance(target, (Auditoria, AuditoriaSincronia)) or \
       os.environ.get("FLASK_ENV") == "simulation" or \
       os.environ.get("SYNC_IN_PROGRESS") == "1":
        return

    estabelecimento_id = getattr(target, 'estabelecimento_id', None)
    if not estabelecimento_id and target.__tablename__ == 'estabelecimentos':
        estabelecimento_id = target.id

    if not estabelecimento_id:
        return

    # 1. Preparar Payload (Estado Atual)
    try:
        payload = object_to_dict(target)
        
        # 2. Registrar na Sincronia (se aplicável) - Mantém tudo sincronizável
        if target.__tablename__ in TABELAS_SINCRONIZAVEIS:
            AuditoriaSincronia.registrar_mutacao(
                estabelecimento_id=estabelecimento_id,
                tabela=target.__tablename__,
                registro_id=target.id,
                operacao=operacao,
                payload=payload
            )

        # 3. Registrar na Auditoria Forense (MONITOR SaaS)
        # SÓ REGISTRA SE ESTIVER NA LISTA DE INTERESSE DO MASTER
        if target.__tablename__ in TABELAS_MONITOR_MASTER:
            # Tenta pegar o usuário do contexto global (g)
            usuario_id = getattr(g, 'user_id', None)
            
            # Mapeamento para nome amigável
            label_tabela = TABELAS_MONITOR_MASTER.get(target.__tablename__, target.__tablename__.title())
            
            # Descrição Inteligente baseada na operação
            if operacao == 'INSERT':
                descricao = f"{label_tabela} (ID: {target.id}) detectada no sistema."
                if target.__tablename__ == 'vendas':
                     descricao = f"Venda #{getattr(target, 'codigo', target.id)} finalizada com sucesso."
                elif target.__tablename__ == 'despesas':
                     descricao = f"Despesa registrada: {getattr(target, 'descricao', 'Sem descrição')}."
            elif operacao == 'UPDATE':
                descricao = f"Alteração realizada em {label_tabela} (ID: {target.id})."
                if target.__tablename__ == 'produtos':
                     descricao = f"Atualização de dados/preço no produto: {getattr(target, 'nome', target.id)}."
            else:
                descricao = f"Exclusão de {label_tabela} (ID: {target.id})."

            tipo_evento = f"{target.__tablename__}_{operacao.lower()}"
            
            # O campo 'valor' da Auditoria pode ser preenchido se a tabela tiver 'valor' ou 'total'
            valor = getattr(target, 'total', getattr(target, 'valor', getattr(target, 'valor_original', None)))

            Auditoria.registrar(
                estabelecimento_id=estabelecimento_id,
                tipo_evento=tipo_evento,
                descricao=descricao,
                usuario_id=usuario_id,
                valor=valor,
                detalhes={
                    "operacao": operacao,
                    "tabela": target.__tablename__,
                    "registro_id": target.id,
                    "timestamp": datetime.now().isoformat(),
                    "data": payload
                }
            )

    except Exception as e:
        print(f"Erro no Listener Forense: {str(e)}")

def setup_listeners():
    """Configura os listeners de Auditoria Forense para todos os modelos relevantes"""
    # Itera sobre todos os modelos registrados no SQLAlchemy
    for model_class in db.Model.__subclasses__():
        # Ignorar as tabelas de log e tabelas não-sincronizáveis para evitar loop e ruído
        if not hasattr(model_class, '__tablename__'): continue
        
        t_name = model_class.__tablename__
        if t_name in ['auditoria', 'auditoria_sincronia', 'sync_log', 'sync_queue', 'login_history']:
            continue
            
        event.listen(model_class, 'after_insert', lambda m, c, t: registrar_evento_forense(m, c, t, 'INSERT'))
        event.listen(model_class, 'after_update', lambda m, c, t: registrar_evento_forense(m, c, t, 'UPDATE'))
        event.listen(model_class, 'after_delete', lambda m, c, t: registrar_evento_forense(m, c, t, 'DELETE'))

    print("Muralha Forense: Listeners de Auditoria e Sincronia (Business Intellingence) ativados!")

