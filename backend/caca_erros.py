import os

print("🕵️ INICIANDO VARREDURA POR 'requestzer'...")
found = False

# Caminha por todas as pastas do projeto
for root, dirs, files in os.walk("app"):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if "requestzer" in line:
                            print(f"🚨 ENCONTRADO! Arquivo: {path} | Linha: {i+1}")
                            print(f"   Conteúdo: {line.strip()}")
                            found = True
            except Exception as e:
                pass  # Ignora erros de leitura

if not found:
    print("✅ Nenhum 'requestzer' encontrado. O problema é sobrenatural (Cache).")
else:
    print("🎯 Corrija os arquivos acima e o sistema vai rodar!")
print("🕵️ VARREDURA FINALIZADA.")