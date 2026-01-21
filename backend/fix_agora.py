# fix_agora.py - SOLUÇÃO RÁPIDA E DIRETA
import os
import sys
import sqlite3
from pathlib import Path

print("🔧 CORRIGINDO BANCO DE DADOS AGORA!")

# 1. Vá para a pasta correta
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"📍 Diretório atual: {os.getcwd()}")

# 2. Crie a pasta instance se não existir
instance_dir = Path("instance")
instance_dir.mkdir(exist_ok=True)
print(f"✅ Pasta 'instance' criada/verificada: {instance_dir.absolute()}")

# 3. Caminho ABSOLUTO do banco
db_path = instance_dir / "mercadinho.db"
print(f"📍 Caminho do banco: {db_path}")

# 4. Delete qualquer banco corrompido
if db_path.exists():
    try:
        os.remove(db_path)
        print("🗑️ Banco antigo removido")
    except:
        pass

# 5. Crie banco SQLite VAZIO
print("📦 Criando banco SQLite vazio...")
conn = sqlite3.connect(db_path)
conn.close()
print(f"✅ Banco criado: {db_path.exists()} ({db_path.stat().st_size} bytes)")

# 6. Verifique permissões
try:
    test_file = instance_dir / "teste.txt"
    with open(test_file, "w") as f:
        f.write("teste")
    os.remove(test_file)
    print("✅ Permissões de escrita OK")
except Exception as e:
    print(f"❌ Problema de permissões: {e}")

print("\n🎯 AGORA EXECUTE ESTE COMANDO:")
print("python criar_usuario_admin.py")
