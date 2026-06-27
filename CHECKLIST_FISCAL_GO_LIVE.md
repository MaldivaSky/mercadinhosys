# Checklist Oficial — Ativação Fiscal (NFC-e) para Go-Live

> Estado do software: **terreno pronto**. Emissão, listagem, cancelamento,
> configuração de credenciais (tela), numeração por loja, idempotência e o
> adapter Focus NFe já estão implementados e cobertos por testes e2e (modo
> simulado). Para emitir nota **com valor fiscal real**, falta apenas plugar as
> credenciais de cada loja, conforme abaixo.

---

## 1. De quem são as credenciais?

A NFC-e é emitida **sob o CNPJ da loja (lojista/tenant)**. Logo, as credenciais
são **sempre do cliente**, nunca suas:

| Item | De quem | Onde se obtém |
|---|---|---|
| Certificado Digital **A1** (`.pfx`) | Do CNPJ da loja | Autoridade certificadora (Serasa, Certisign, etc.) |
| **CSC** + **CSC ID** (idToken) | Da loja | Portal da SEFAZ do estado da loja (seção NFC-e) |
| Inscrição Estadual + Regime (CSOSN) | Da loja | Contabilidade da loja |
| **Token do gateway** (Focus NFe) | Você gera | Conta Focus NFe (ver modelo abaixo) |

**Você (dono do SaaS) controla a conta no gateway**, não emite nota no seu nome.

### Modelo recomendado: conta master sua (white-label)
1. Você abre **uma** conta na Focus NFe.
2. Para cada loja, cadastra a empresa na sua conta Focus (envia o A1 do cliente).
3. A Focus devolve **um token por empresa** → você cola esse token no sistema da loja.
4. O lojista só te entrega A1 + CSC. Custo do gateway entra no plano dele.

> Alternativa (modelo B): cada loja abre a própria conta Focus e cola o token.
> O sistema suporta os dois — muda só quem digita o token.

---

## 2. Passo a passo de ativação (por loja)

1. **Homologação primeiro** (obrigatório, gratuito e sem valor fiscal):
   - Em **Configurações → Fiscal (NFC-e)**, defina:
     - Ambiente: **Homologação**
     - Gateway: **Focus NFe**
     - Token do Gateway: *(token de homologação da empresa na Focus)*
     - CSC / ID do CSC: *(de homologação, obtidos na SEFAZ)*
     - Série NFC-e: normalmente `1`
     - Regime Tributário: **Simples Nacional** (default)
   - Faça uma venda de teste e clique **Emitir NFC-e** na tela de Vendas.
   - Confira em **Fiscal → Notas Emitidas (NFC-e)**: status `autorizado`, chave de
     44 dígitos, QR Code e link da DANFE.

2. **Cadastro fiscal dos produtos** (crítico para nota válida):
   - Cada produto precisa de **NCM correto** (8 dígitos), e idealmente CFOP e CSOSN.
   - O **NCM é preenchido automaticamente** ao escanear o código de barras (vem
     do Cosmos); fica visível e editável no cadastro do produto.
   - 🔒 **Trava de produção:** o sistema **recusa emitir** em produção qualquer
     venda com produto sem NCM válido (vazio, zeros ou < 8 dígitos), em vez de
     usar um NCM-default errado. A mensagem lista os produtos a corrigir.
   - A correção tributária final (NCM/CSOSN/CFOP) é responsabilidade da
     contabilidade do lojista.

3. **Virada para produção**:
   - Troque para credenciais de **produção** (token, CSC, CSC ID de produção) e
     Ambiente: **Produção**.
   - Trava de segurança: em produção o sistema **recusa emitir** se o gateway
     real não estiver configurado (não cai em simulado silencioso).
   - Emita 1 nota real de baixo valor e confirme no portal da SEFAZ.

---

## 3. O que JÁ está pronto no software (não precisa fazer)

- ✅ Tela de credenciais por loja: **Configurações → Fiscal (NFC-e)**.
- ✅ Botão **Emitir NFC-e** na tela de Vendas.
- ✅ **Fiscal → Notas Emitidas**: lista, status, chave, cancelamento (com
  justificativa ≥ 15 caracteres, exigência SEFAZ).
- ✅ **Fiscal → Entrada**: importação de XML de compra (estoque + custo + contas a pagar).
- ✅ Adapter Focus NFe real (homologação/produção), numeração por loja, idempotência.
- ✅ Trava: produção nunca emite em modo simulado por engano.
- ✅ Isolamento multi-tenant das notas (cada loja só vê as suas).

---

## 4. Limites conhecidos / responsabilidades

- **Correção tributária** (NCM, CSOSN, CFOP, alíquotas) é responsabilidade da
  contabilidade do lojista. O sistema fornece defaults para o caso típico de
  mercadinho no Simples; não substitui o contador.
- **CPF na nota**: o consumidor pode informar CPF na venda (opcional). Não é
  obrigatório para NFC-e abaixo do limite estadual.
- **Certificado A1** vence (normalmente 1 ano) — renovação é tarefa recorrente
  do lojista; a nota falha se o certificado expirar na Focus.
- **NF-e modelo 55** (entre empresas) não é o foco; o fluxo aqui é NFC-e
  (modelo 65, venda ao consumidor).

---

## 5. Resumo de 1 linha

Software pronto. Para cada loja: **homologar na Focus → testar → cadastrar NCM
dos produtos → virar produção**. Suas únicas tarefas externas: abrir conta Focus
NFe e coletar A1 + CSC de cada lojista.
