from app import create_app, db
from app.models import Configuracao

app = create_app()

with app.app_context():
    config = Configuracao.query.first()
    if config:
        print(f"Config ID: {config.id}")
        if config.logo_base64:
            print(f"Logo Base64 FOUND. Length: {len(config.logo_base64)}")
            print(f"Start: {config.logo_base64[:50]}...")
        else:
            print("Logo Base64 is EMPTY or NULL")
            
        print(f"Logo URL: {config.logo_url}")
    else:
        print("No Configuracao found!")
