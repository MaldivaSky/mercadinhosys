
from app import create_app, db
from app.models import Configuracao, Estabelecimento
import base64
import os

app = create_app()

def upload_logo():
    logo_path = r"C:\Users\rafae\OneDrive\Desktop\mercadinhosys\frontend\mercadinhosys-frontend\logoico.png"
    
    if not os.path.exists(logo_path):
        print(f"❌ Arquivo não encontrado: {logo_path}")
        return

    with app.app_context():
        # Pegar o primeiro estabelecimento/configuração (assumindo single-tenant ou demo)
        config = Configuracao.query.first()
        
        if not config:
            print("⚠️ Nenhuma configuração encontrada. Criando uma padrão...")
            estab = Estabelecimento.query.first()
            if not estab:
                print("❌ Nenhum estabelecimento encontrado. Abortando.")
                return
            config = Configuracao(estabelecimento_id=estab.id)
            db.session.add(config)
        
        # Ler imagem e converter para base64
        try:
            with open(logo_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode('utf-8')
                full_data_uri = f"data:image/png;base64,{encoded}"
                
                # Salvar no campo logo_base64 (que é Text e suporta grandes strings)
                config.logo_base64 = full_data_uri
                # Limpar logo_url para evitar conflitos ou usar como fallback vazio
                config.logo_url = None 
                
                db.session.commit()
                print("✅ Logo convertida e salva no banco de dados com sucesso!")
                print(f"   Tamanho da string: {len(full_data_uri)} caracteres")
                print(f"   Estabelecimento ID: {config.estabelecimento_id}")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar logo: {str(e)}")

if __name__ == "__main__":
    upload_logo()
