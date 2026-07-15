# Plano de Lançamento SaaS

## Objetivo

Levar o MercadinhoSys de soft launch para 100 assinantes com base sólida de produto, operação e suporte.

## Posicionamento

MercadinhoSys deve ser vendido como:

`ERP especializado para mercadinhos, conveniências e mini mercados`

Não como ERP genérico.

## Planos oficiais

### Gratuito

Perfil ideal:
- loja piloto;
- operação pequena;
- validação inicial do sistema.

Recursos liberados:
- 1 usuário administrador;
- PDV e gestão de caixa;
- produtos;
- clientes;
- fornecedores;
- dashboard com visão executiva;
- configurações essenciais.

Recursos bloqueados:
- Consultor M-IA;
- compras & doca;
- vendas analíticas e histórico gerencial;
- fiscal;
- RH e ponto;
- relatórios avançados;
- auditoria;
- delivery;
- SFA;
- despesas avançadas;
- múltiplos usuários.

Limites recomendados:
- 1 usuário ativo;
- até 100 produtos;
- até 200 clientes;
- até 50 fornecedores.

### Pro

Perfil ideal:
- operação em produção;
- loja com rotina diária;
- uso fiscal e gestão mais completa.

Recursos:
- acesso completo aos módulos comerciais;
- múltiplos usuários;
- relatórios avançados;
- consultor inteligente;
- RH, fiscal, auditoria e expansões.

Preço:
- `R$ 99,90 / mês`

## Prioridades técnicas antes de escalar aquisição

1. Padronizar toda a stack em `Gratuito` e `Pro`.
2. Revisar onboarding e billing ponta a ponta.
3. Adicionar monitoramento de erros e uptime.
4. Formalizar backup e restore testado.
5. Fechar páginas legais e canais oficiais.
6. Preparar onboarding comercial e técnico.

## Meta por fases

### Fase 1: 1 a 3 clientes

- 1 cliente piloto grátis;
- 2 clientes pagantes assistidos;
- implantação manual e acompanhada;
- coleta de feedback semanal.

### Fase 2: 4 a 10 clientes

- consolidar playbook de implantação;
- reduzir suporte reativo;
- medir uso real por módulo;
- validar cobrança recorrente e inadimplência.

### Fase 3: 11 a 30 clientes

- iniciar campanhas mais consistentes;
- criar base pública de ajuda;
- formalizar SLA;
- subir monitoramento e alertas.

### Fase 4: 31 a 100 clientes

- reforçar infraestrutura;
- revisar custos por tenant;
- automatizar onboarding;
- profissionalizar CS e suporte.

## Infraestrutura

Para os 10 primeiros clientes, a stack atual pode servir em modo controlado, mas com atenção para:
- banco;
- picos simultâneos de PDV;
- logs e storage;
- filas de webhook e integrações fiscais.

Antes de 30 clientes ativos, revisar:
- CPU e memória do backend;
- storage do banco;
- política de retenção de logs;
- contingência de indisponibilidade.

## Checklist comercial mínimo

- domínio `.com.br`;
- e-mail profissional;
- landing coerente com os dois planos;
- política de privacidade;
- termos de uso;
- proposta comercial;
- processo de implantação;
- roteiro de demonstração.

## Métricas de decisão

Só acelerar aquisição se estes pontos estiverem saudáveis:
- churn sob controle;
- onboarding concluído em até 2 dias úteis;
- suporte inicial reduzindo;
- cobrança funcionando sem intervenção manual frequente;
- estabilidade operacional em horário comercial.
