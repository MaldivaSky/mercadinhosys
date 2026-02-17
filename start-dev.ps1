# Script para facilitar a execução do MercadinhoSYS no Docker (Modo Desenvolvimento)

Write-Host "--- Iniciando MercadinhoSYS no Docker (Modo Dev) ---" -ForegroundColor Cyan

# 1. Verifica se o Docker está rodando
if (!(Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Aviso: Certifique-tse de que o Docker Desktop está aberto." -ForegroundColor Yellow
}

# 2. Escolha do Banco de Dados
Write-Host "`nQual banco de dados deseja usar para desenvolvimento?" -ForegroundColor Cyan
Write-Host "1. Postgres (Recomendado - Completo)"
Write-Host "2. SQLite (Leve - Simples)"
$dbChoice = Read-Host "Escolha (1 ou 2)"

if ($dbChoice -eq "2") {
    $env:DATABASE_URL = "sqlite:///instance/mercadinho.db"
    Write-Host "[!] Usando SQLite (Leve)..." -ForegroundColor Yellow
}
else {
    $env:DATABASE_URL = "postgresql://mercadinho_user:mercadinho_secure_pass_2024@postgres:5432/mercadinhosys"
    Write-Host "[!] Usando Postgres..." -ForegroundColor Blue
}

# 3. Pergunta se o usuário deseja limpar dados antigos
$limpar = Read-Host "`nDeseja limpar os containers e volumes antigos antes de subir? (S/N)"
if ($limpar -eq "S" -or $limpar -eq "s") {
    Write-Host "Limpando ambiente..." -ForegroundColor Gray
    docker-compose -f docker-compose.dev.yml down -v
}

# 4. Sobe os containers
Write-Host "Subindo os containers e compilando as imagens (isso pode demorar na primeira vez)..." -ForegroundColor Green
docker-compose -f docker-compose.dev.yml up --build

Write-Host "`n--- Ambiente pronto! ---" -ForegroundColor Green
Write-Host "Acesse o sistema em: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Para parar o sistema, pressione Ctrl+C neste terminal." -ForegroundColor Gray
