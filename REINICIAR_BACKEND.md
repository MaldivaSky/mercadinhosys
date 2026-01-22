# 🔄 COMO REINICIAR O BACKEND CORRETAMENTE

## PROBLEMA
O backend está rodando com código antigo em memória. Mesmo que você tenha modificado os arquivos, o Flask não recarrega automaticamente todas as mudanças (especialmente decorators e imports).

## SOLUÇÃO

### 1. PARAR O BACKEND
No terminal onde o backend está rodando:
- Pressione `Ctrl + C` para parar o servidor

### 2. LIMPAR CACHE PYTHON (IMPORTANTE!)
```bash
cd backend
Remove-Item -Recurse -Force __pycache__
Remove-Item -Recurse -Force app/__pycache__
Remove-Item -Recurse -Force app/routes/__pycache__
Remove-Item -Recurse -Force app/decorators/__pycache__
```

### 3. REINICIAR O BACKEND
```bash
cd backend
venv\Scripts\activate
python run.py
```

### 4. VERIFICAR SE CARREGOU CORRETAMENTE
Você deve ver no terminal:
```
INFO:app:✅ Blueprint fornecedores registrado em /api/fornecedores
```

## TESTE RÁPIDO

Após reiniciar, teste no navegador ou Postman:

**URL:** `http://127.0.0.1:5000/api/fornecedores?por_pagina=10`

**Headers:**
```
Authorization: Bearer <seu_token_jwt>
```

**Resposta esperada:**
```json
{
  "success": true,
  "fornecedores": [...],
  "total": 8
}
```

## SE AINDA DER ERRO 500

1. Olhe o terminal do backend - ele mostra o erro exato
2. Copie o erro e me envie
3. Ou verifique o arquivo `backend/logs/app.log`

## ALTERNATIVA: USAR CÓDIGO TEMPORÁRIO

Se quiser testar rapidamente, substitua o conteúdo de `backend/app/routes/fornecedores.py` pelo conteúdo de `backend/app/routes/fornecedores_temp.py` que tem logs detalhados e tratamento de erro melhor.
