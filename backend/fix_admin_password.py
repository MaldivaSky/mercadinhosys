"""
Script para corrigir a senha do admin diretamente no banco de dados.
Execute este script para garantir que o admin tenha a senha 'admin123'.
"""

import os
import sys

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Funcionario, Estabelecimento
from werkzeug.security import generate_password_hash, check_password_hash

def fix_admin_password():
    """Corrige a senha do admin para 'admin123'"""
    app = create_app(os.getenv("FLASK_ENV", "default"))
    
    with app.app_context():
        print("=" * 60)
        print("🔧 CORRIGINDO SENHA DO ADMIN")
        print("=" * 60)
        
        # Buscar admin por username
        admin = Funcionario.query.filter_by(username="admin").first()
        
        if not admin:
            print("❌ ERRO: Usuário 'admin' não encontrado!")
            print("\n📋 Buscando todos os funcionários...")
            funcionarios = Funcionario.query.all()
            if funcionarios:
                print(f"   Encontrados {len(funcionarios)} funcionários:")
                for f in funcionarios:
                    print(f"   - ID: {f.id}, Username: {f.username}, Email: {f.email}, Ativo: {f.ativo}")
            else:
                print("   Nenhum funcionário encontrado no banco!")
                print("\n💡 Execute o seed primeiro: python seed_test.py --reset --local")
            return False
        
        print(f"✅ Admin encontrado:")
        print(f"   ID: {admin.id}")
        print(f"   Nome: {admin.nome}")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Role: {admin.role}")
        print(f"   Ativo: {admin.ativo}")
        print(f"   Status: {admin.status}")
        print(f"   Estabelecimento ID: {admin.estabelecimento_id}")
        
        # Verificar estabelecimento
        estabelecimento = Estabelecimento.query.get(admin.estabelecimento_id)
        if estabelecimento:
            print(f"   Estabelecimento: {estabelecimento.nome_fantasia}")
        else:
            print(f"   ⚠️ Estabelecimento ID {admin.estabelecimento_id} não encontrado!")
        
        # Verificar senha atual
        print("\n🔐 Verificando senha atual...")
        senha_atual_ok = admin.check_senha("admin123")
        print(f"   Senha 'admin123' funciona? {senha_atual_ok}")
        
        if senha_atual_ok:
            print("\n✅ Senha já está correta! Nada a fazer.")
            return True
        
        # Corrigir senha
        print("\n🔧 Corrigindo senha para 'admin123'...")
        admin.set_senha("admin123")
        
        # Verificar se funcionou
        senha_nova_ok = admin.check_senha("admin123")
        if not senha_nova_ok:
            print("❌ ERRO: A senha não foi definida corretamente!")
            print(f"   Hash gerado: {admin.senha_hash[:50]}...")
            return False
        
        # Salvar no banco
        try:
            db.session.commit()
            print("✅ Senha corrigida e salva no banco!")
            
            # Verificar novamente após commit
            db.session.refresh(admin)
            senha_final_ok = admin.check_senha("admin123")
            if senha_final_ok:
                print("✅ Confirmação: Senha funciona após commit!")
                print("\n" + "=" * 60)
                print("✅ SUCESSO! Agora você pode fazer login com:")
                print("   Username: admin")
                print("   Senha: admin123")
                print("=" * 60)
                return True
            else:
                print("❌ ERRO: Senha não funciona após commit!")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO ao salvar no banco: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = fix_admin_password()
    sys.exit(0 if success else 1)
