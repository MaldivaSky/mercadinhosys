import os
from pathlib import Path

# Caminho atual
current_dir = Path(__file__).parent

# Cria pasta instance
instance_dir = current_dir / "instance"
instance_dir.mkdir(exist_ok=True)

# Cria arquivo do banco vazio (se não existir)
db_file = instance_dir / "mercadinho.db"
if not db_file.exists():
    db_file.touch()
    print(f"✅ Arquivo do banco criado: {db_file}")
else:
    print(f"✅ Arquivo do banco já existe: {db_file}")

# Verifica permissões
print(f"📁 Caminho completo: {db_file.absolute()}")
print(
    f"🔒 Permissões: {'Acessível' if os.access(db_file, os.W_OK) else 'SEM PERMISSÃO'}"
)
