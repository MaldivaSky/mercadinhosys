from app import create_app, db
from app.models import Estabelecimento, Configuracao

app = create_app()

with app.app_context():
    estabs = Estabelecimento.query.all()
    print(f"Total de estabelecimentos: {len(estabs)}")
    
    for estab in estabs:
        print(f"--- Estabelecimento ID: {estab.id} ---")
        print(f"Nome: {estab.nome_fantasia}")
        
        config = estab.configuracao
        if config:
            print(f"Configuração ID: {config.id}")
            print(f"Logo URL: {config.logo_url}")
            if config.logo_base64:
                b64 = config.logo_base64
                print(f"Logo Base64: Presente (Length: {len(b64)})")
                print(f"Preview: {b64[:30]}...{b64[-10:]}")
            else:
                print("Logo Base64: None")
        else:
            print("Configuração: NÃO ENCONTRADA (None)")
