import re

with open('backend/app/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add registrar_direto to Auditoria class
old_method = """    @classmethod
    def registrar(cls, estabelecimento_id, tipo_evento, descricao, usuario_id=None, valor=None, detalhes=None):"""

new_method = """    @classmethod
    def registrar_direto(cls, connection, estabelecimento_id, tipo_evento, descricao, usuario_id=None, valor=None, detalhes=None):
        import json
        from datetime import datetime
        try:
            connection.execute(
                cls.__table__.insert().values(
                    estabelecimento_id=estabelecimento_id,
                    tipo_evento=tipo_evento,
                    descricao=descricao,
                    usuario_id=usuario_id,
                    valor=valor,
                    detalhes_json=detalhes, # SQLAlchemy Core handles dict to JSON
                    data_evento=datetime.now()
                )
            )
        except Exception as e:
            pass

    @classmethod
    def registrar(cls, estabelecimento_id, tipo_evento, descricao, usuario_id=None, valor=None, detalhes=None):"""

if "def registrar_direto" not in content:
    content = content.replace(old_method, new_method)

with open('backend/app/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Models.py patched")
