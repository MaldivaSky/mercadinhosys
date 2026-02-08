
import sqlite3
import os

db_path = os.path.join("backend", "mercadinho.db")
if not os.path.exists(db_path):
    print(f"❌ Banco não encontrado em {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Contar vendas totais
cursor.execute("SELECT COUNT(*) FROM vendas")
total = cursor.fetchone()[0]
print(f"Total de vendas: {total}")

# Ver distribuição de datas (top 10 dias)
cursor.execute("SELECT DATE(data_venda), COUNT(*) FROM vendas GROUP BY DATE(data_venda) ORDER BY DATE(data_venda) DESC LIMIT 10")
print("\nTop 10 dias com vendas:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} vendas")

# Ver Ponto de Equilíbrio inputs
cursor.execute("SELECT SUM(valor) FROM despesas")
despesas = cursor.fetchone()[0]
print(f"\nTotal despesas (histórico): {despesas}")

cursor.execute("SELECT SUM(total) FROM vendas")
receita = cursor.fetchone()[0]
print(f"Total receita (histórico): {receita}")

conn.close()
