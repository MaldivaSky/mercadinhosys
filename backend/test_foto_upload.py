#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste completo do fluxo de upload de foto
Simula exatamente o que o frontend faz
"""

import requests
import base64
import os
from PIL import Image
import io

# Configurações
API_URL = "http://localhost:5000/api/ponto/registrar"
# Use o username como token (ou deixe vazio para tentar sem autenticação)
TOKEN = "admin"  # Username do funcionário

def criar_imagem_teste():
    """Cria uma imagem de teste em base64"""
    # Cria uma imagem simples
    img = Image.new('RGB', (1280, 720), color='red')
    
    # Converte para base64
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=80)
    img_byte_arr.seek(0)
    
    base64_str = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{base64_str}"
    
    print(f"✅ Imagem de teste criada")
    print(f"   Tamanho base64: {len(base64_str)} caracteres")
    print(f"   Data URL começa com: {data_url[:50]}...")
    
    return data_url

def testar_upload():
    """Testa o upload de foto"""
    
    print("\n" + "="*60)
    print("🧪 TESTE DE UPLOAD DE FOTO")
    print("="*60)
    
    # Cria imagem de teste
    foto_base64 = criar_imagem_teste()
    
    # Dados para registrar ponto
    dados = {
        "tipo_registro": "entrada",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "foto": foto_base64,  # Base64 com data URL
        "dispositivo": "Test Script",
        "observacao": "Teste de upload de foto via API"
    }
    
    print(f"\n💾 Enviando dados para: {API_URL}")
    print(f"   Foto no payload: {'foto' in dados}")
    print(f"   Tamanho do payload (foto): {len(dados['foto'])} caracteres")
    
    try:
        # Headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        }
        
        # Envia requisição
        response = requests.post(API_URL, json=dados, headers=headers)
        
        print(f"\n📡 Resposta do servidor:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response JSON: {response.json()}")
        
        if response.status_code == 201 or response.status_code == 200:
            resultado = response.json()
            if resultado.get('success'):
                print(f"\n✅ SUCESSO!")
                if resultado.get('data'):
                    print(f"   ID: {resultado['data'].get('id')}")
                    print(f"   Foto URL: {resultado['data'].get('foto_url')}")
                    
                    # Verifica se arquivo existe
                    if resultado['data'].get('foto_url'):
                        foto_file = "." + resultado['data'].get('foto_url')
                        if os.path.exists(foto_file):
                            print(f"   ✅ Arquivo existe: {foto_file}")
                            tamanho = os.path.getsize(foto_file)
                            print(f"   Tamanho do arquivo: {tamanho} bytes")
                        else:
                            print(f"   ❌ Arquivo NÃO existe: {foto_file}")
            else:
                print(f"\n❌ Erro: {resultado.get('message')}")
        else:
            print(f"\n❌ Erro HTTP {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Erro ao fazer requisição: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_upload()
