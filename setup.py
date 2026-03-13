#!/usr/bin/env python3
"""
🚀 MercadinhoSys - Setup Automatizado v5.0
Arquitetura Híbrida: Local + Nuvem + Backup
"""

import os
import sys
import secrets
import subprocess
from pathlib import Path

def print_header(title):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    """Imprime passo formatado"""
    print(f"\n📋 [{step}] {description}")

def run_command(command, check=True):
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip()

def check_prerequisites():
    """Verifica pré-requisitos"""
    print_step("1", "Verificando pré-requisitos...")
    
    # Verificar Python
    python_version = sys.version_info
    if python_version < (3, 9):
        print("❌ Python 3.9+ é necessário")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Verificar pip
    try:
        import pip
        print("✅ pip disponível")
    except ImportError:
        print("❌ pip não encontrado")
        return False
    
    # Verificar Node.js (opcional)
    try:
        stdout, _ = run_command("node --version")
        print(f"✅ Node.js {stdout}")
    except:
        print("⚠️ Node.js não encontrado (opcional para frontend)")
    
    return True

def create_directory_structure():
    """Cria estrutura de diretórios"""
    print_step("2", "Criando estrutura de diretórios...")
    
    directories = [
        "backend/instance",
        "backend/logs",
        "backups",
        "uploads",
        "uploads/avatars",
        "uploads/products",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Diretório criado: {directory}")

def setup_environment():
    """Configura ambiente e .env"""
    print_step("3", "Configurando ambiente...")
    
    # Verificar se .env existe
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            # Copiar .env.example para .env
            with open(env_example, 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            # Gerar chaves seguras
            secret_key = secrets.token_hex(32)
            jwt_secret = secrets.token_hex(32)
            sync_token = secrets.token_hex(32)
            
            # Substituir placeholders
            env_content = env_content.replace("gerar-chave-secreta-64-chars-aqui-CHANGE-ME", secret_key)
            env_content = env_content.replace("gerar-chave-jwt-64-chars-aqui-CHANGE-ME", jwt_secret)
            env_content = env_content.replace("gerar-token-32-chars-aqui-CHANGE-ME", sync_token)
            
            # Salvar .env
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print("✅ .env criado com chaves seguras")
        else:
            print("❌ .env.example não encontrado")
            return False
    else:
        print("✅ .env já existe")
    
    return True

def install_dependencies():
    """Instala dependências Python"""
    print_step("4", "Instalando dependências Python...")
    
    requirements_files = [
        "requirements.txt",
        "requirements-dev.txt"
    ]
    
    for req_file in requirements_files:
        if Path(req_file).exists():
            print(f"📦 Instalando {req_file}...")
            stdout, stderr = run_command(f"pip install -r {req_file}")
            if stderr and "ERROR" in stderr.upper():
                print(f"⚠️ Erro em {req_file}: {stderr}")
            else:
                print(f"✅ {req_file} instalado")
        else:
            print(f"⚠️ {req_file} não encontrado")

def setup_database():
    """Configura banco de dados"""
    print_step("5", "Configurando banco de dados...")
    
    # Verificar modo atual
    app_mode = os.getenv("APP_MODE", "local")
    print(f"📊 Modo atual: {app_mode}")
    
    if app_mode == "local":
        # Criar banco SQLite
        try:
            from app import create_app, db
            
            app = create_app()
            with app.app_context():
                # Criar tabelas
                db.create_all()
                print("✅ Banco SQLite criado com sucesso")
                
                # Verificar se está vazio
                from app.models import Estabelecimento
                if Estabelecimento.query.count() == 0:
                    print("📋 Banco está vazio - Execute o seed para popular")
                else:
                    print("✅ Banco já possui dados")
                    
        except Exception as e:
            print(f"❌ Erro ao configurar banco: {e}")
            return False
    
    return True

def run_seed():
    """Executa seed de dados"""
    print_step("6", "Executando seed de dados...")
    
    seed_files = [
        "seed_main_v5.py",
        "seed_main.py"
    ]
    
    for seed_file in seed_files:
        if Path(seed_file).exists():
            print(f"🌱 Executando {seed_file}...")
            stdout, stderr = run_command(f"python {seed_file}")
            
            if "SEED CONCLUÍDO COM SUCESSO" in stdout:
                print("✅ Seed executado com sucesso")
                return True
            else:
                print(f"❌ Erro no seed: {stderr}")
                return False
    
    print("⚠️ Nenhum arquivo de seed encontrado")
    return False

def setup_git():
    """Configura Git"""
    print_step("7", "Configurando Git...")
    
    # Verificar se é repositório Git
    if not Path(".git").exists():
        print("❌ Este não é um repositório Git")
        return False
    
    # Verificar .gitignore
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        print("❌ .gitignore não encontrado")
        return False
    
    # Verificar se .env está no .gitignore
    with open(gitignore, 'r', encoding='utf-8') as f:
        gitignore_content = f.read()
    
    if ".env" not in gitignore_content:
        print("⚠️ .env não está no .gitignore - Adicionando...")
        with open(gitignore, 'a', encoding='utf-8') as f:
            f.write("\n# Security - Never commit\n.env\n")
    
    print("✅ Git configurado")
    return True

def test_application():
    """Testa aplicação"""
    print_step("8", "Testando aplicação...")
    
    try:
        # Testar import
        from app import create_app
        app = create_app()
        
        # Testar health check
        with app.test_client() as client:
            response = client.get('/api/auth/health')
            if response.status_code == 200:
                print("✅ Health check funcionando")
            else:
                print(f"⚠️ Health check retornou {response.status_code}")
        
        print("✅ Aplicação testada com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar aplicação: {e}")
        return False

def show_next_steps():
    """Mostra próximos passos"""
    print_step("9", "Próximos passos...")
    
    print("\n🎉 Setup concluído com sucesso!")
    print("\n📋 Para começar:")
    print("1. Configure suas credenciais no arquivo .env")
    print("2. Configure AIVEN_DATABASE_URL para nuvem")
    print("3. Execute: python run.py")
    print("4. Acesse: http://localhost:5000")
    
    print("\n👑 Credenciais de acesso:")
    print("   Super Admin: maldivas | Mald1v@$")
    print("   Estab. 1: admin1 | admin123")
    print("   Estab. 2: admin2 | admin123")
    
    print("\n📊 Modos de operação:")
    print("   Local (SQLite): export APP_MODE=local")
    print("   Nuvem (PostgreSQL): export APP_MODE=cloud")
    
    print("\n🔄 Sincronização:")
    print("   - Local: SQLite → Nuvem (automático)")
    print("   - Nuvem: PostgreSQL direto")
    
    print("\n📚 Documentação:")
    print("   - PLANO_ALINHAMENTO.md")
    print("   - README.md")
    print("   - .env.example")

def main():
    """Função principal"""
    print_header("MERCADINHOSYS SETUP AUTOMATIZADO v5.0")
    
    steps = [
        ("Verificando pré-requisitos", check_prerequisites),
        ("Criando estrutura de diretórios", create_directory_structure),
        ("Configurando ambiente", setup_environment),
        ("Instalando dependências", install_dependencies),
        ("Configurando banco de dados", setup_database),
        ("Executando seed de dados", run_seed),
        ("Configurando Git", setup_git),
        ("Testando aplicação", test_application)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ Erro em '{step_name}': {e}")
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n❌ Setup falhou nos seguintes passos: {', '.join(failed_steps)}")
        print("\n🔧 Verifique os erros acima e execute novamente")
        return False
    else:
        show_next_steps()
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
