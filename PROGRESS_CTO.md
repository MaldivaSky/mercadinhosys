# Progresso — Auditoria CTO / Entrega Completa MercadinhoSys

> Marcas de progresso para retomar exatamente onde parou. Atualizado a cada etapa.
> Legenda: ✅ feito+testado · 🟡 código pronto, falta teste · 🔧 em andamento · ⬜ não iniciado

## Modelo de negócio (travado)
- **Super Admin = Dono do SaaS (Rafael / maldivas)**: `is_super_admin=True`, nível 0, vê todas as lojas. Painel de plataforma.
- **Tenant Admin = Dono da loja (admin1)**: nível 1, preso a 1 `estabelecimento_id`. "O sistema" do lojista.
- Níveis: 1 Admin · 2 Gerente · 3 Caixa · 4 Estoque · 5 RH · 6 Entregador.
- **PIN de estorno**: PIN de segurança do Admin (4-6 díg., hash). Admin repassa ao caixa/gerente para liberar operações reservadas (estorno etc.). Admin pode trocar. Autoriza nível ≤ 2. Registra quem autorizou.

## Credenciais de teste (DEV)
- superadmin: `maldivas` / `***REMOVED-SUPERADMIN-PWD***`
- tenant admin: `admin1` / `admin123`

## Status por bloco

### Bloco A — PIN de cancelamento (Tenant)
- A1 migração pin hash varchar(255) — ✅ (migration `c3d4e5f6a7b8` aplicada e verificada no DB)
- A2 furo de auth no cancelar_venda fechado — ✅ TESTADO (sem PIN→403, PIN errado→403, PIN correto→200)
- A3 persistir PIN no criar/editar funcionário — ✅ TESTADO (PUT /funcionarios/2 grava, hash não vaza)
- A4 frontend PIN numérico 4-6 + bloqueio submit — ✅ (typecheck ok; UI)
- PENDENTE refinamento: campo PIN só para nível ≤ 2; admin trocar o próprio PIN no perfil.

### Bloco B
- B1 filtros rápidos ABC dinâmicos (classe A/C/margem) — ✅ TESTADO (classe_a→5, classe_c→4 produtos)
- B2 motivos de estorno em Settings + dropdown no cancelamento — ✅ TESTADO (GET→PUT→GET persiste; migration `d4e5f6a7b8c9`)
- B3 pressão de caixa (7d) + comprometimento c/ despesas a vencer — ✅ TESTADO (despesa venc+3d → pressão 0→2.04%, obrig_7d=1500)

### Fiscal — decisões: Simples Nacional (CSOSN), entrada+NFC-e em paralelo, gateway Focus NFe (adapter trocável)
- F0 fundações: campos fiscais Estabelecimento + Produto — ✅ migration `e5f6a7b8c9d0`
- F1 IMPORTAR XML de entrada (compra) — ✅ COMPLETO+TESTADO e2e
  - `app/services/fiscal/xml_parser.py` (stdlib, testado), `entrada_service.py`, rota `app/routes/fiscal.py` (`/api/fiscal/entrada/preview|importar|<id>/xml`), modelo `NotaFiscalEntrada`, migration `f6a7b8c9d0e1`.
  - Faz: upsert fornecedor, cria/atualiza produto, entrada estoque + custo médio ponderado, gera conta a pagar (duplicatas), idempotência por chave, guarda XML.
  - Testado: importar 201 (produto+estoque+conta criados), reimportar 400, listar ok.
  - FALTA (frontend): tela em Despesas/Compras para upload do XML (drag-drop) + preview.
- F2 EMISSÃO NFC-e (Simples/CSOSN) via gateway — ✅ COMPLETO+TESTADO e2e (modo simulado)
  - Modelo `DocumentoFiscal` (migration `a7b8c9d0e1f2`); adapters `gateways.py` (Simulado + FocusNFe + factory); `emissao_service.py` (payload CSOSN da Venda, numeração por estab, idempotência); rotas `/api/fiscal/vendas/<id>/nfce`, `/documentos`, `/documentos/<id>/cancelar`.
  - Testado: emitir 201 autorizado (chave 44 díg c/ DV válido, QR), reemitir idempotente, cancelar valida justificativa ≥15 e cancela.
  - PRONTO p/ produção: trocar `estabelecimentos.fiscal_gateway='focusnfe'` + `fiscal_token` (homologação grátis). `requests` já no requirements.
  - FALTA (frontend): botão "Emitir NFC-e" no PDV/Vendas, tela de Documentos Fiscais, Settings fiscais (ambiente/gateway/token/CSC). Integração real Focus NFe (precisa token+certificado A1 no go-live).

## Sync local → Aiven (auditoria + correção)
Problema: gap LOCAL 45.425 vs AIVEN 32.103 vendas — auto-sync nunca funcionou. 3 caminhos, 3 furos:
- CLI `flask push-to-aiven` processava SyncQueue (no-op: MERCADINHO_OFFLINE off). ✅ Corrigido → agora chama `force_sync`.
- Scheduler in-worker (`CloudPushScheduler`) usava `force_sync` (motor certo) mas morria no `gunicorn --reload` e corria entre 2 workers → nunca completou ciclo. ✅ Desligado (SYNC_AUTO_PUSH=false no backend).
- Botão `/sync/replicar` quebrado por `sync_queue.operacao varchar(10)` (não cabia "replicar_para_neon"). ✅ migration `b8c9d0e1f2a3` → varchar(50).
Correção robusta:
- NOVO serviço dedicado `sync` no docker-compose (`python -m scripts.sync_daemon`) — runner único, isolado, sobrevive a reloads. Roda `force_sync` a cada SYNC_PUSH_INTERVAL_SEC (300s).
- `flask sync-status` mostra gap local vs Aiven por tabela.
- Para aplicar: `docker compose up -d backend sync` (recria backend com scheduler off + sobe o daemon).
- MOTOR NOVO `scripts/robust_sync.py`: ordena por FK, filtra órfãos (filho sem pai no Aiven), wrap JSON (Json), upsert em lote SEM fallback linha-a-linha, cursor server-side. CLI/daemon/endpoint apontam pra ele.
  - Resultado: estab 2 (admin1) 100% no Aiven — vendas 32.109, venda_itens 96.362, pagamentos 48.5k. Antes venda_itens/pagamentos = 0 no Aiven (dashboard Vercel zerado) → AGORA preenchido.
  - DIVERGÊNCIA DE SEED (não é bug do sync): Aiven estabelecimentos.id=2 tem o CNPJ que localmente é do id=3 (PKs trocadas entre os dois bancos). Não sobrescrever Aiven sem decisão do dono. Gera órfãos (~10k vendas de estabs divergentes).
  - PENDENTE: contas_pagar falha por FK pedido_compra_id (incluir pedidos_compra no PLAN). Perf futura: watermark incremental por updated_at (hoje varre tudo).
- BUG SEPARADO reportado pelo user: data_venda exibida sem fuso de Brasília (armazenada em UTC). É display no frontend, não sync.

## Hardening de produção (em andamento)
- H1 Paridade de schema local↔Aiven — ✅ VERIFICADO: Aiven já tem fiscal_ambiente, csosn, pin_cancelamento, motivos_estorno, operacao. Só falta `alembic_version` (controle de migration; deploy migra o Aiven). OK.
- H2 Segredos — `config.py` JÁ recusa boot em produção sem SECRET_KEY/JWT (linhas 78-80). ✅ `.env.example` atualizado com AIVEN_DATABASE_URL + vars de sync. PENDENTE (baixo risco): compose usa senha de DB hardcoded em DATABASE_URL (dev) em vez de ${DB_PASSWORD}.
- H3 Observabilidade do sync — ✅ TESTADO: tabela `sync_heartbeat` (migration `c9d0e1f2a3b4`), daemon grava status/total/duração a cada ciclo, `GET /api/sync/health` reporta {sync_saudavel, sync_idade_minutos, heartbeat}. Detecta sync parado (era falha silenciosa).
  - PENDENTE: Sentry init guardado por DSN; disparar alerta (email/webhook) quando sync_saudavel=false.
- H4 senha do DB no compose via ${DB_PASSWORD} — ✅ (backend+sync; `docker compose config` valida).
- H5 JWT refresh/token longo — ✅ JÁ EXISTIA e TESTADO: login emite access 24h + refresh 7d; `/auth/refresh` funciona; interceptor 401 no frontend renova sozinho. Cobre 12h offline.
- H6 rate-limit + backup:
  - Backup Aiven — ✅ TESTADO: `scripts/backup_aiven.py` (pg_dump+gzip+rotação). Rodou: 7.95 MB. Aiven também tem backup gerenciado nativo.
  - Rate-limit login — ✅ TESTADO E FUNCIONANDO (429 comprovado: #1-5=401, #6+=429). 2 causas corrigidas: (1) decorei a função ERRADA — `/api/auth/login` é servido por `auth_multi_tenant.login`, não `auth.py` (movi o decorator pro certo, revertendo auth.py); (2) storage memory:// (per-worker) → Redis via `RATELIMIT_STORAGE_URI` no compose. Limite 5/min por IP.
  - Nota: 5/min por IP. Se uma loja tiver muitos caixas atrás do mesmo IP, considerar afrouxar ou key por IP+usuário.

## Resumo p/ deploy (revisar antes de subir)
- Migrations backend: head único `a7b8c9d0e1f2`. Cadeia linear. Railway: `flask db upgrade`.
- Frontend Vercel: corrigi 4 erros TS6133 (unused) que quebravam `npm run build`. **Rodar `npm run build` 1x p/ confirmar** antes do deploy.

### Settings por Tenant (bug crítico encontrado em uso)
- PUT /configuracao/estabelecimento — ✅ CORRIGIDO+TESTADO (era `claims` indefinido → 500)
- PUT/GET /configuracao/preferencias — ✅ CORRIGIDO+TESTADO (faltava estabelecimento_id → persiste agora)
- POST /configuracao/logo — ✅ CORRIGIDO+TESTADO. 2 bugs: (1) `claims` indefinido; (2) base64 gravado em `logo_url` VARCHAR(500) → truncava (erro em imagens reais). Agora grava só em `logo_base64` (Text). Testado: img 4KB→200, persiste.
- Header não exibia a logo: lia `config.logo_url` (fica null após salvar config). ✅ CORRIGIDO: `HeaderProfessional` lê `logo_base64` primeiro. tsc ok.
- Build Vercel: 4 erros TS6133 (unused) no código commitado do Gemini ✅ CORRIGIDOS (ProductHistoryModal, SupplierHistoryModal). Falta rodar `npm run build` final.
- Causa: bugs pré-existentes. Cada tenant agora grava e mantém info/preferências.

### Deploy
- Migrations: head único `e5f6a7b8c9d0` (Railway OK). Cadeia: c3d4e5f6a7b8 → d4e5f6a7b8c9 → e5f6a7b8c9d0.
- Frontend build (Vercel): a validar com `npm run build`.

### Super Admin / SaaS
- Seletor de perfil no header (ver loja como tenant, read-only) — ⬜
- Painel super admin legível — ⬜

## Próximos passos imediatos
1. Autenticar admin1 e testar: Settings salva motivos_estorno? PIN cadastra? Cancelamento exige PIN?
2. Concluir F0 (migration + Produto + serviço fiscal + rota) e fazer NFC-e funcionar (modo homologação/simulado).
3. Seletor de perfil no header (super admin → ver tenant read-only).
