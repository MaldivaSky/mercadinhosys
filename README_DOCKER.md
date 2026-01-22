# 🐳 MercadinhoSys - Docker & DevOps

Sistema completo de gestão empresarial com infraestrutura DevOps moderna.

## 🚀 Quick Start (1 comando!)

```bash
make install
```

Isso vai:
1. Criar arquivo `.env` a partir do `.env.example`
2. Build das imagens Docker
3. Subir todos os containers (Backend, Frontend, PostgreSQL, Redis)
4. Rodar migrations do banco
5. Popular com dados de teste

**Acesse:**
- Frontend: http://localhost
- Backend API: http://localhost:5000
- API Docs: http://localhost:5000/api

## 📋 Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- Make (opcional, mas recomendado)

## 🛠️ Comandos Disponíveis

### Gerenciamento de Containers

```bash
make up          # Sobe todos os containers
make down        # Para todos os containers
make restart     # Reinicia todos os containers
make logs        # Mostra logs em tempo real
make ps          # Lista containers em execução
```

### Desenvolvimento

```bash
make dev         # Modo desenvolvimento (hot reload)
make test        # Roda todos os testes
make test-coverage  # Testes com coverage
make shell-backend  # Abre shell no container do backend
make shell-db    # Abre psql no banco
```

### Banco de Dados

```bash
make migrate     # Roda migrations
make migrate-create  # Cria nova migration
make seed        # Popula banco com dados de teste
make backup      # Faz backup do banco
make restore FILE=backup.sql  # Restaura backup
```

### Manutenção

```bash
make clean       # Remove containers e volumes
make update      # Atualiza imagens e reinicia
make health      # Verifica saúde dos serviços
make stats       # Mostra estatísticas dos containers
```

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Frontend   │  │   Backend    │  │  PostgreSQL  │  │
│  │   (Nginx)    │  │   (Flask)    │  │              │  │
│  │   Port 80    │  │   Port 5000  │  │   Port 5432  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                    mercadinhosys-network                 │
│                                                           │
│  ┌──────────────┐                                        │
│  │    Redis     │  (Cache & Sessions)                    │
│  │  Port 6379   │                                        │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

## 📦 Volumes Persistentes

- `postgres_data`: Dados do PostgreSQL
- `backend_uploads`: Arquivos enviados pelos usuários
- `backend_logs`: Logs da aplicação
- `backend_backups`: Backups automáticos
- `redis_data`: Cache do Redis

## 🔒 Segurança

### Variáveis de Ambiente Sensíveis

**NUNCA commite o arquivo `.env` no Git!**

Gere chaves seguras:

```bash
# Secret Key
python -c "import secrets; print(secrets.token_hex(32))"

# JWT Secret
python -c "import secrets; print(secrets.token_hex(32))"
```

### Secrets no GitHub Actions

Configure no GitHub: `Settings > Secrets and variables > Actions`

Secrets necessários:
- `DOCKER_USERNAME`: Usuário do Docker Hub
- `DOCKER_PASSWORD`: Senha do Docker Hub
- `DEPLOY_HOST`: IP do servidor de produção
- `DEPLOY_USER`: Usuário SSH
- `DEPLOY_SSH_KEY`: Chave privada SSH

## 🧪 CI/CD Pipeline

O pipeline roda automaticamente em cada push/PR:

### 1. Backend Tests
- ✅ Linting com flake8
- ✅ Formatação com black
- ✅ Imports com isort
- ✅ Testes com pytest
- ✅ Coverage report

### 2. Frontend Tests
- ✅ Linting com ESLint
- ✅ Type checking com TypeScript
- ✅ Testes unitários
- ✅ Build de produção

### 3. Docker Build
- ✅ Build das imagens
- ✅ Push para Docker Hub
- ✅ Cache otimizado

### 4. Security Scan
- ✅ Scan de vulnerabilidades com Trivy
- ✅ Upload para GitHub Security

### 5. Deploy (main branch)
- ✅ Deploy automático via SSH
- ✅ Zero downtime

## 🚀 Deploy em Produção

### Opção 1: Docker Compose (Servidor único)

```bash
# No servidor
git clone https://github.com/seu-usuario/mercadinhosys.git
cd mercadinhosys
cp .env.example .env
# Edite .env com valores de produção
make prod
```

### Opção 2: Kubernetes (Escalável)

```bash
# Aplicar manifests
kubectl apply -f k8s/

# Verificar pods
kubectl get pods -n mercadinhosys

# Logs
kubectl logs -f deployment/backend -n mercadinhosys
```

### Opção 3: Docker Swarm (Cluster)

```bash
# Inicializar swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml mercadinhosys

# Verificar serviços
docker service ls
```

## 📊 Monitoramento

### Health Checks

Todos os serviços têm health checks configurados:

```bash
# Backend
curl http://localhost:5000/api/health

# Frontend
curl http://localhost/health

# PostgreSQL
docker-compose exec postgres pg_isready
```

### Logs Centralizados

```bash
# Todos os logs
make logs

# Apenas backend
make logs-backend

# Apenas frontend
make logs-frontend

# Apenas banco
make logs-db
```

### Métricas

```bash
# Estatísticas em tempo real
make stats

# Uso de disco
docker system df
```

## 🔧 Troubleshooting

### Container não sobe

```bash
# Ver logs detalhados
docker-compose logs backend

# Verificar configuração
docker-compose config

# Rebuild forçado
docker-compose build --no-cache backend
```

### Banco de dados não conecta

```bash
# Verificar se PostgreSQL está rodando
docker-compose ps postgres

# Testar conexão
docker-compose exec postgres pg_isready

# Ver logs do banco
docker-compose logs postgres
```

### Porta já em uso

```bash
# Verificar o que está usando a porta
lsof -i :5000  # Backend
lsof -i :80    # Frontend

# Matar processo
kill -9 <PID>
```

### Limpar tudo e recomeçar

```bash
make clean-all
make install
```

## 📚 Documentação Adicional

- [API Documentation](http://localhost:5000/api)
- [Swagger UI](http://localhost:5000/swagger)
- [Architecture Decisions](./docs/architecture.md)
- [Contributing Guide](./CONTRIBUTING.md)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Add nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

O CI/CD vai rodar automaticamente e validar seu código!

## 📝 Licença

Este projeto está sob a licença MIT.

## 🆘 Suporte

- Issues: https://github.com/seu-usuario/mercadinhosys/issues
- Email: suporte@mercadinhosys.com
- Docs: https://docs.mercadinhosys.com

---

**Desenvolvido com ❤️ usando Docker, Flask, React e boas práticas DevOps**
