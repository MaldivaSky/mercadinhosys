import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from run import app
from app.models import db, StatusPedidoLogistica, Funcionario, Estabelecimento

with app.app_context():
    # Limpa tudo
    db.session.execute(db.text('DELETE FROM status_pedido_logistica'))
    
    # Pega todos os estabelecimentos para garantir que o Admin logado veja a moto
    estabelecimentos = Estabelecimento.query.all()
    
    if not estabelecimentos:
        print("Nenhum estabelecimento encontrado.")
        sys.exit(1)
        
    for est in estabelecimentos:
        # Pega ou cria um funcionario_id qualquer pra esse estabelecimento
        func = Funcionario.query.filter_by(estabelecimento_id=est.id).first()
        func_id = func.id if func else 1

        # Guarulhos SP (Próximo ao CEP 07064-020)
        # Lat: -23.4475, Lon: -46.5450
        
        evento = StatusPedidoLogistica(
            estabelecimento_id=est.id,
            venda_id=1,
            funcionario_id=func_id,
            status="EM_ROTA",
            latitude=-23.4475,
            longitude=-46.5450,
            timestamp=datetime.utcnow()
        )
        db.session.add(evento)

    db.session.commit()
    print("Motos simuladas em Guarulhos com sucesso para TODOS os estabelecimentos!")
