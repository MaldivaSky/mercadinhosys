describe('Smoke Tests - Critical Flows', () => {
    beforeEach(() => {
        // Clear cookies/local storage to ensure clean state if needed
        cy.clearLocalStorage();
    });

    it('should load the login page', () => {
        cy.visit('/login');
        cy.contains('Entrar no Sistema').should('be.visible');
        cy.get('input[type="email"]').should('be.visible');
        cy.get('input[type="password"]').should('be.visible');
    });

    it('should login successfully', () => {
        cy.visit('/login');

        // Using default credentials from seed (adjust if different)
        cy.get('input[type="email"]').type('admin@mercadinho.com.br');
        cy.get('input[type="password"]').type('admin123');
        cy.get('button[type="submit"]').click();

        // Verify redirection to dashboard
        cy.url().should('include', '/app/dashboard');
        cy.contains('Visão Geral').should('be.visible');
    });

    it('should navigate to Products page and display items', () => {
        // Perform login first (custom command or just repeat for smoke test)
        cy.visit('/login');
        cy.get('input[type="email"]').type('admin@mercadinho.com.br');
        cy.get('input[type="password"]').type('admin123');
        cy.get('button[type="submit"]').click();

        // Navigate to Products
        cy.get('a[href="/app/produtos"]').click();

        // Verify Page Title
        cy.contains('Gestão de Produtos').should('be.visible');

        // Verify Table loads (waiting for API)
        cy.get('table').should('exist');
        // Check if at least one row exists or "Nenhum produto" message if empty, 
        // but better to assert table headers
        cy.contains('th', 'Produto').should('be.visible');
    });
});
