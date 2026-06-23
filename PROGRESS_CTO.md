# Progresso — Auditoria CTO / Entrega Completa MercadinhoSys

> Marcas de progresso para retomar exatamente onde parou. Atualizado a cada etapa.
> Legenda: ✅ feito+testado · 🟡 código pronto, falta teste · 🔧 em andamento · ⬜ não iniciado

## Modelo de negócio (travado)
- **Super Admin = Dono do SaaS (Rafael / maldivas)**: `is_super_admin=True`, nível 0, vê todas as lojas. Painel de plataforma.
- **Tenant Admin = Dono da loja (admin1)**: nível 1, preso a 1 `estabelecimento_id`. "O sistema" do lojista.
- Níveis: 1 Admin · 2 Gerente · 3 Caixa · 4 Estoque · 5 RH · 6 Entregador.
- **PIN de estorno**: PIN de segurança do Admin (4-6 díg., hash). Admin repassa ao caixa/gerente para liberar operações reservadas (estorno etc.). Admin pode trocar. Autoriza nível ≤ 2. Registra quem autorizou.

## Credenciais de teste (DEV)
- superadmin: `maldivas` / `Mald1v@$`
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
