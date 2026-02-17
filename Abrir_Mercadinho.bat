@echo off
:: Inicia os containers sem mostrar janelas de log
docker-compose up -d
:: Aguarda o banco de dados respirar
timeout /t 7
:: Abre o navegador em "Modo Aplicativo"
start chrome --app=http://localhost:80
exit