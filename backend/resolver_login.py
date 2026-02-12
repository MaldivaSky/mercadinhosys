"""
Script completo para resolver problemas de login do admin.
Este script:
1. Verifica se o admin existe
2. Corrige a senha se necessário
3. Testa o login
4. Executa o seed se necessário
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

def resolver_login():
    """Resolve problemas de login do admin"""
    app = create_app(os.getenv("FLASK_ENV", "default"))
    
    with app.app_context():
        print("=" * 70)
        print("🔧 RESOLVEDOR DE PROBLEMAS DE LOGIN")
        print("=" * 70)
        
        # 1. Verificar se admin existe
        admin = Funcionario.query.filter_by(username="admin").first()
        
        if not admin:
            print("\n❌ Usuário 'admin' não encontrado!")
            print("\n💡 Executando seed para criar o admin...")
            
            # Importar e executar seed
            try:
                from seed_test import seed_funcionarios, ensure_estabelecimento
                from faker import Faker
                
                fake = Faker("pt_BR")
                estabelecimento = Estabelecimento.query.first()
                
                if not estabelecimento:
                    print("   Criando estabelecimento...")
                    estabelecimento = ensure_estabelecimento(fake, 1)
                
                print("   Criando funcionários...")
                funcionarios = seed_funcionarios(fake, estabelecimento.id)
                
                admin = Funcionario.query.filter_by(username="admin").first()
                if admin:
                    print("✅ Admin criado com sucesso!")
                else:
                    print("❌ Erro ao criar admin!")
                    return False
            except Exception as e:
                print(f"❌ Erro ao executar seed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # 2. Verificar e corrigir senha
        print(f"\n✅ Admin encontrado: {admin.nome} (ID: {admin.id})")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Role: {admin.role}")
        print(f"   Ativo: {admin.ativo}")
        
        # Verificar senha atual
        senha_ok = admin.check_senha("admin123")
        print(f"\n🔐 Testando senha 'admin123'...")
        
        if senha_ok:
            print("✅ Senha já está correta!")
        else:
            print("❌ Senha incorreta. Corrigindo...")
            admin.set_senha("admin123")
            
            try:
                db.session.commit()
                db.session.refresh(admin)
                
                # Verificar novamente
                if admin.check_senha("admin123"):
                    print("✅ Senha corrigida com sucesso!")
                else:
                    print("❌ Erro: Senha ainda não funciona após correção!")
                    return False
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao salvar senha: {e}")
                return False
        
        # 3. Verificar estabelecimento
        estabelecimento = Estabelecimento.query.get(admin.estabelecimento_id)
        if not estabelecimento:
            print(f"\n⚠️ Estabelecimento ID {admin.estabelecimento_id} não encontrado!")
            print("   Isso pode causar problemas no login.")
        else:
            print(f"\n✅ Estabelecimento: {estabelecimento.nome_fantasia}")
        
        # 4. Teste final
        print("\n" + "=" * 70)
        print("🧪 TESTE FINAL DE LOGIN")
        print("=" * 70)
        
        admin_final = Funcionario.query.filter_by(username="admin").first()
        if admin_final and admin_final.check_senha("admin123"):
            print("✅✅✅ SUCESSO TOTAL! ✅✅✅")
            print("\n📋 Credenciais para login:")
            print("   Username: admin")
            print("   Senha: admin123")
            print("\n💡 Agora você pode fazer login no sistema!")
            print("=" * 70)
            return True
        else:
            print("❌ Teste final falhou!")
            return False

if __name__ == "__main__":
    success = resolver_login()
    sys.exit(0 if success else 1)
