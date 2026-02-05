#!/usr/bin/env python
from app import create_app, db
from app.models import RegistroPonto, Funcionario
from datetime import datetime, date
import os
import base64

app = create_app()
with app.app_context():
    func = Funcionario.query.first()
    if func:
        # Criar diretório de uploads se não existir
        upload_dir = os.path.join('uploads', 'pontos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Criar uma imagem PNG mínima em base64
        tiny_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        # Decodificar e salvar
        filename = f"ponto_{func.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(tiny_png))
        
        foto_url = f"/uploads/pontos/{filename}"
        
        # Deletar registros de hoje se existirem para teste limpo
        RegistroPonto.query.filter_by(
            funcionario_id=func.id,
            data=date.today()
        ).delete()
        
        # Criar registro COM foto
        reg = RegistroPonto(
            funcionario_id=func.id,
            estabelecimento_id=func.estabelecimento_id,
            data=date.today(),
            hora=datetime.now().time(),
            tipo_registro='entrada',
            latitude=-23.5505,
            longitude=-46.6333,
            localizacao_endereco='São Paulo, SP',
            foto_url=foto_url,
            status='normal',
            minutos_atraso=0
        )
        
        db.session.add(reg)
        db.session.commit()
        
        print(f"✅ SUCESSO! Registro criado COM FOTO!")
        print(f"   ID: {reg.id}")
        print(f"   Funcionário: {func.nome}")
        print(f"   Foto URL: {reg.foto_url}")
        print(f"   Arquivo: {filepath}")
        print(f"\n   Verifique em http://localhost:5173/ponto-historico")
    else:
        print("❌ Nenhum funcionário encontrado")
