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

### Fiscal
- F0 fundações: campos fiscais Estabelecimento + Produto — ✅ migration `e5f6a7b8c9d0` aplicada (login voltou a 200)
  - FALTA: serviço `app/services/fiscal/` (adapter gateway), rota `fiscal.py`, modelo `DocumentoFiscal`/`CertificadoDigital`, emissão NFC-e em modo simulado, teste e2e.

### Super Admin / SaaS
- Seletor de perfil no header (ver loja como tenant, read-only) — ⬜
- Painel super admin legível — ⬜

## Próximos passos imediatos
1. Autenticar admin1 e testar: Settings salva motivos_estorno? PIN cadastra? Cancelamento exige PIN?
2. Concluir F0 (migration + Produto + serviço fiscal + rota) e fazer NFC-e funcionar (modo homologação/simulado).
3. Seletor de perfil no header (super admin → ver tenant read-only).
