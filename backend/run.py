import os
from app import create_app
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Cria a aplicação
app = create_app(os.getenv("FLASK_ENV", "default"))

if __name__ == "__main__":
    # Obtém porta do ambiente ou usa 5000
    port = int(os.environ.get("PORT", 5000))

    # Executa em modo desenvolvimento
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
