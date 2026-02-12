# 🔧 Solução para Problema de Login

## Problema
Não consegue fazer login com `admin` / `admin123` - aparece "credenciais inválidas".

## Solução Rápida

### Opção 1: Script Automático (Recomendado)

```powershell
# 1. Ativar ambiente virtual
cd backend
.\venv\Scripts\Activate.ps1

# 2. Executar script de correção
python resolver_login.py
```

Este script vai:
- ✅ Verificar se o admin existe
- ✅ Criar o admin se não existir
- ✅ Corrigir a senha para `admin123`
- ✅ Testar o login

### Opção 2: Corrigir Senha Manualmente

```powershell
# 1. Ativar ambiente virtual
cd backend
.\venv\Scripts\Activate.ps1

# 2. Executar script de correção de senha
python fix_admin_password.py
```

### Opção 3: Recriar Banco Completo

```powershell
# 1. Ativar ambiente virtual
cd backend
.\venv\Scripts\Activate.ps1

# 2. Recriar banco e popular dados
python seed_test.py --reset --local
```

## Verificar se Funcionou

Após executar qualquer script, teste o login:

1. Abra o frontend (http://localhost:5173 ou sua URL)
2. Tente fazer login com:
   - **Username:** `admin`
   - **Senha:** `admin123`

## Se Ainda Não Funcionar

Execute este comando para ver detalhes do problema:

```powershell
python seed_test.py --test-login
```

Isso vai mostrar:
- Se o admin existe
- Se a senha está correta
- Qualquer erro no banco de dados

## Problemas Comuns

### 1. "Admin não encontrado"
**Solução:** Execute `python seed_test.py --reset --local`

### 2. "Senha incorreta"
**Solução:** Execute `python fix_admin_password.py`

### 3. "Estabelecimento não encontrado"
**Solução:** Execute `python seed_test.py --reset --local`

## Contato

Se nenhuma solução funcionar, verifique:
- ✅ Ambiente virtual está ativado
- ✅ Banco de dados está acessível
- ✅ Dependências instaladas (`pip install -r requirements.txt`)
