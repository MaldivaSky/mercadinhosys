import os

filepath = r"C:\Users\rafae\Dev\mercadinhosys\backend\app\routes\clientes.py"

with open(filepath, 'rb') as f:
    content = f.read()

# Find the corrupted @
idx = content.find(b'@\x00c\x00l\x00i\x00e\x00n\x00t\x00e\x00s\x00')
if idx != -1:
    content = content[:idx]

idx2 = content.find(b'@\x00 \x00c\x00l\x00i\x00e\x00n\x00t\x00e\x00s\x00')
if idx2 != -1:
    content = content[:idx2]

with open(filepath, 'wb') as f:
    f.write(content)

# Append clean text
with open(filepath, 'a', encoding='utf-8') as f:
    f.write("""
@clientes_bp.route("/rfm", methods=["GET"])
@funcionario_required
def obter_rfm():
    try:
        from app.utils.query_helpers import get_authorized_establishment_id
        from app.models import Cliente
        estabelecimento_id = get_authorized_establishment_id()
        dias = request.args.get("dias", 180, type=int)
        
        rfm_data = Cliente.calcular_rfm(estabelecimento_id, days=dias)
        return jsonify({"success": True, "rfm": rfm_data})
    except Exception as e:
        from flask import current_app, jsonify
        current_app.logger.error(f"Erro ao calcular RFM: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao calcular RFM"}), 500
""")
