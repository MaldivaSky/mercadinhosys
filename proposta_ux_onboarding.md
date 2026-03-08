# Proposta Estratégica: Experiência do Usuário (UX) & Sucesso do Cliente (CS)

Como CEO e CTO, nosso foco é **atrito zero** para o cliente e **controle total** para o administrador. Abaixo, as diretrizes para o novo fluxo de onboarding:

## 1. O E-mail de Boas-Vindas (Primeira Impressão)

O e-mail não deve ser apenas "aqui está sua senha". Deve ser um convite para o sucesso do negócio dele.

**Assunto**: 🚀 Seu Mercadinho está pronto para decolar! | Acesso ao MercadinhoSys

**Texto do E-mail**:
> Olá, **[Nome do Cliente]**!
>
> É um prazer ter o **[Nome da Loja]** como nosso parceiro. Você acaba de contratar um ecossistema de gestão inteligente projetado para maximizar seus lucros e organizar sua operação.
>
> ### 🔑 Seus Dados de Acesso:
> - **URL do Sistema**: [Link da Vercel ou Domínio]
> - **Usuário**: [Username]
> - **Senha Temporária**: `[SenhaAleatoria]`
>
> *(Recomendamos alterar sua senha no primeiro acesso para total segurança)*.
>
> ### 🧭 Próximos Passos:
> Ao entrar, você verá o nosso **Tour de Boas-Vindas**. Ele te guiará nos primeiros passos:
> 1. Como cadastrar seu primeiro produto.
> 2. Como abrir o caixa e realizar a primeira venda.
> 3. Como configurar seu logotipo.
>
> Se precisar de ajuda, nosso suporte está disponível via [Canal de Suporte].
>
> Vamos crescer juntos?
> **Equipe Maldivas Sistemas**

---

## 2. Tour de Usabilidade (O Guia "Entendi")

Em vez de documentos PDF chatos, usaremos o conceito de **"Interactive Guided Tour"**.

**Funcionamento**:
- Detectamos o `primeiro_acesso = true` no login.
- Um overlay sutil escurece o fundo e destaca botões específicos (ex: Botão de Vendas).
- Um balão (Tooltip) aparece com o texto:
  - *"Este é o seu PDV. Aqui você realiza vendas em menos de 10 segundos. Clique em **Entendi** para continuar."*
- **Sequência sugerida**:
  1. **Dashboard principal**: Onde ele vê o lucro do dia.
  2. **Estoque**: Como alimentar o sistema.
  3. **Caixa**: Onde o dinheiro entra.
  4. **Configurações**: Onde ele customiza a loja.

---

## 3. Experiência do Administrador Global (CEO/CTO View)

Para você (`maldivas`), a interface será focada em **Gestão de Saúde da Operação**.

**Recursos do Dashboard Global**:
- **Lista de Inquilinos (Tenants)**: Tabela com Nome, CNPJ, Status (Ativo/Suspenso), Faturamento Total e Plano.
- **Botão de Destruição (Delete)**: Exclusão com confirmação em duas etapas (proteção contra erro humano).
- **Log de Saúde**: Monitor de erros 500 em tempo real (para você saber se algum cliente está tendo problemas antes mesmo dele te ligar).
- **Painel de Prazos**: Alertas de mensalidades vencidas ou planos expirando.

---

## 4. O que eu tenho em mente para implementar:

1.  **Backend**: Criar o serviço de e-mail integrado (usando o Mailtrap ou SMTP real).
2.  **Frontend**: Criar o componente `WelcomeTour.tsx` que gerencia os estados do guia interativo.
3.  **Frontend**: Criar a `TenantsPage.tsx` dentro da área de Monitoramento, com as ações de Criar/Editar/Deletar contas.

**O que você acha dessa abordagem? Se aprovar, começo a codificar o Tour de Boas-Vindas.**
