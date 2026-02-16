# ✅ SOLUÇÃO: "Funcionário não encontrado"

## 🎯 PROBLEMA IDENTIFICADO

O erro **"Funcionário não encontrado"** ocorre porque:

1. ✅ O token JWT é válido (não retorna 401)
2. ✅ A rota existe (não retorna 404)
3. ❌ O `funcionario_id` dentro do token não existe no banco Neon
4. ❌ Você fez login no localhost (SQLite) mas está usando Vercel (Neon)

### Por que isso acontece?

- **Localhost**: Usa SQLite com IDs sequenciais (1, 2, 3...)
- **Vercel/Render**: Usa PostgreSQL/Neon com IDs diferentes
- **Token JWT**: Contém o ID do banco onde você fez login

Quando você faz login no localhost e depois acessa o Vercel, o token tem um ID que não existe no Neon.

## 🔧 SOLUÇÃO RÁPIDA

### PASSO 1: Fazer Logout no Vercel

1. Acesse: https://mercadinhosys.vercel.app
2. Clique no seu nome/avatar no canto superior direito
3. Clique em **Sair** ou **Logout**

**OU** execute no console (F12):

```javascript
localStorage.clear()
sessionStorage.clear()
location.reload()
```

### PASSO 2: Fazer Login Novamente

1. Faça login com suas credenciais
2. O backend do Render vai gerar um novo token com o ID correto do Neon
3. Tente acessar o PDV novamente

## 🔍 VERIFICAR SE O BANCO NEON TEM USUÁRIOS

Se após o logout/login ainda não funcionar, o banco Neon pode estar vazio. Vamos popular:

### OPÇÃO 1: Popular via Script (RECOMENDADO)

```bash
# No seu terminal local
cd backend
python seed_neon.py
```

Este script vai:
- Criar tabelas no Neon
- Inserir usuário admin padrão
- Inserir dados de teste (produtos, clientes, etc)

### OPÇÃO 2: Criar Usuário Manualmente

Se o script não funcionar, crie via Python:

```python
# No terminal local
cd backend
python

# Cole este código:
from app import create_app, db
from app.models import Funcionario
from werkzeug.security import generate_password_hash
import os

# Configurar para usar Neon (use a URL do seu .env, nunca commite a senha)
# Antes: from dotenv import load_dotenv; load_dotenv()
os.environ['DATABASE_URL'] = os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL')

app = create_app('production')

with app.app_context():
    # Criar admin
    admin = Funcionario(
        nome='Admin',
        email='admin@mercadinho.com',
        senha=generate_password_hash('admin123'),
        role='ADMIN',
        status='ativo',
        estabelecimento_id=1,
        permissoes={
            'pode_dar_desconto': True,
            'limite_desconto': 100,
            'pode_cancelar_venda': True
        }
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"✅ Admin criado com ID: {admin.id}")
```

### OPÇÃO 3: Verificar Usuários no Neon

Execute este script para ver quais usuários existem:

```python
# No terminal local
cd backend
python

# Cole este código (com .env carregado ou export DATABASE_URL antes):
from dotenv import load_dotenv
load_dotenv()
from app import create_app, db
from app.models import Funcionario
import os

os.environ['DATABASE_URL'] = os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL')

app = create_app('production')

with app.app_context():
    funcionarios = Funcionario.query.all()
    
    if not funcionarios:
        print("❌ Nenhum funcionário encontrado no banco Neon!")
        print("Execute: python seed_neon.py")
    else:
        print(f"✅ {len(funcionarios)} funcionários encontrados:")
        for f in funcionarios:
            print(f"  - ID: {f.id} | Nome: {f.nome} | Email: {f.email} | Role: {f.role}")
```

## 🧪 TESTE COMPLETO

Após popular o banco, teste no console do Vercel:

```javascript
// 1. Limpar tokens antigos
localStorage.clear()

// 2. Fazer login
fetch('https://mercadinhosys.onrender.com/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'admin@mercadinho.com',
    senha: 'admin123'
  })
})
.then(r => r.json())
.then(data => {
  console.log('✅ Login:', data)
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)
  
  // 3. Testar PDV
  return fetch('https://mercadinhosys.onrender.com/api/pdv/configuracoes', {
    headers: {
      'Authorization': 'Bearer ' + data.access_token
    }
  })
})
.then(r => r.json())
.then(data => console.log('✅ PDV:', data))
.catch(err => console.error('❌ Erro:', err))
```

## 📋 CHECKLIST

- [ ] Fiz logout no Vercel
- [ ] Limpei localStorage/sessionStorage
- [ ] Executei `seed_neon.py` para popular o banco
- [ ] Fiz login novamente no Vercel
- [ ] Testei acessar o PDV
- [ ] Não há mais erro "Funcionário não encontrado"

## 🚨 SE AINDA NÃO FUNCIONAR

Execute no console do Vercel:

```javascript
// Verificar token atual
const token = localStorage.getItem('access_token')
if (token) {
  const payload = JSON.parse(atob(token.split('.')[1]))
  console.log('Token payload:', payload)
  console.log('User ID no token:', payload.sub)
  console.log('Token expira em:', new Date(payload.exp * 1000))
}
```

Me envie o resultado para eu analisar!

## 🎯 RESUMO

**Problema**: Token com ID de funcionário que não existe no Neon

**Solução**: 
1. Logout no Vercel
2. Popular banco Neon (`python seed_neon.py`)
3. Login novamente no Vercel

**Tempo estimado**: 5 minutos

---

**Após seguir os passos, me avise se funcionou!**
