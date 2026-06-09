# Requirements Document: Critical Corrections for MercadinhoSys ERP

## Introduction

MercadinhoSys is a multi-tenant ERP system for small markets with Flask + PostgreSQL/SQLite backend and React/Vite frontend. The system is approximately 80% complete but has critical gaps that prevent professional distribution. This document specifies requirements for 14 critical corrections across security vulnerabilities, functional bugs, and missing integrations.

## Glossary

- **Dashboard**: Main analytics page displaying business KPIs across 6 sections (Overview, Análise Detalhada, Análise Temporal, Insights Científicos, RH, Fiados)
- **MultiPaymentManager**: React component for managing sales with multiple payment methods
- **PagamentoItem**: Data structure representing a single payment with id, forma (type), valor (amount), and bandeira (card brand)
- **Delivery_Module**: Premium feature for delivery tracking and management
- **Seed_Data**: Database initialization script that creates test/demo data
- **Pagar.me_Webhook**: Payment gateway webhook for subscription activation
- **Onboarding_Flow**: New tenant registration and setup process
- **Tenant_Database**: Isolated PostgreSQL database per establishment in multi-tenant mode
- **Secret_Key**: Cryptographic key for session encryption and JWT signing
- **SQL_Injection**: Security vulnerability allowing malicious SQL execution
- **Stripe_Webhook**: Event handler for Stripe payment events
- **Super_Admin**: System administrator with cross-tenant access

## Requirements

### Requirement 1: Dashboard Metrics Rendering

**User Story:** As a business owner, I want to see all KPIs rendered on the dashboard, so that I can make informed decisions about my business.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the Dashboard_Component SHALL render all 6 sections: Overview, Análise Detalhada, Análise Temporal, Insights Científicos, RH, and Fiados
2. WHEN the RH section renders THEN the Dashboard_Component SHALL display active_employees count, hours_worked total, and payroll amount
3. WHEN the Fiados section renders THEN the Dashboard_Component SHALL display total_fiado (credit), vencido (overdue), and quantidade_clientes (credit customers)
4. WHEN backend data is received THEN the Dashboard_Component SHALL map analise_produtos.curva_abc to Curva ABC cards with progress bars
5. WHEN a user clicks on an anomaly card THEN the Dashboard_Component SHALL open AnomalyDetailsModal with complete details including cause, impact, and suggested actions
6. WHEN a user clicks on a recommendation card THEN the Dashboard_Component SHALL open RecommendationDetailsModal with detailed information
7. WHEN backend returns error THEN the Dashboard_Component SHALL display user-friendly error message with retry option

### Requirement 2: MultiPaymentManager Persistence

**User Story:** As a cashier, I want to complete sales using multiple payment methods, so that I can serve customers who want to split payment across different methods.

#### Acceptance Criteria

1. WHEN a user adds multiple payments THEN the MultiPaymentManager SHALL track each payment as a PagamentoItem with unique id, forma, valor, and optional bandeira
2. WHEN total paid equals or exceeds sale total THEN the MultiPaymentManager SHALL enable the finalize button
3. WHEN a sale is finalized with multiple payments THEN the Backend_API SHALL persist each payment to the Pagamento table linked to the Venda
4. WHEN a user removes a payment THEN the MultiPaymentManager SHALL recalculate total paid and remaining balance
5. WHEN the sale is completed THEN the Backend_API SHALL record all payment methods in the database for reporting
6. IF payment data is invalid THEN the Backend_API SHALL return error code 400 with specific validation message

### Requirement 3: Delivery Interface Functionality

**User Story:** As a delivery manager, I want to manage delivery orders through a functional interface, so that I can track and fulfill customer deliveries.

#### Acceptance Criteria

1. WHEN a user navigates to the delivery page THEN the Delivery_Component SHALL display a list of pending deliveries
2. WHEN a delivery is selected THEN the Delivery_Component SHALL show delivery details including customer address, order items, and status
3. WHEN a delivery status is updated THEN the Delivery_Component SHALL call the backend API to persist the change
4. WHEN delivery tracking is accessed THEN the Delivery_Component SHALL display real-time status updates
5. WHEN the backend returns delivery data THEN the Delivery_Component SHALL render delivery cards with customer name, address, and order total
6. IF delivery API returns empty list THEN the Delivery_Component SHALL display "No pending deliveries" message

### Requirement 4: Seed Data for Multiple Payments

**User Story:** As a developer, I want realistic test data with multiple payment methods, so that I can properly test the multi-payment sales flow.

#### Acceptance Criteria

1. WHEN the seed script runs THEN the Seed_Script SHALL create sales with 2 or more payment methods for at least 10% of total sales
2. WHEN multi-payment sales are created THEN the Seed_Script SHALL create corresponding Pagamento records linked to each Venda
3. WHEN the seed completes THEN each multi-payment sale SHALL have payment totals that sum to the sale total
4. WHEN payment methods are assigned THEN the Seed_Script SHALL vary methods across dinheiro, pix, cartao_debito, cartao_credito, and fiado
5. WHEN multi-payment sales are created THEN the Seed_Script SHALL set realistic payment amounts that reflect real-world split patterns

### Requirement 5: Pagar.me Webhook Implementation

**User Story:** As a SaaS platform operator, I want subscription webhooks to activate tenant plans, so that paying customers receive their purchased features immediately.

#### Acceptance Criteria

1. WHEN Pagar.me sends a subscription.created webhook THEN the Webhook_Handler SHALL create a pending subscription record for the establishment
2. WHEN Pagar.me sends a payment.succeeded webhook THEN the Webhook_Handler SHALL activate the subscription and update establishment.plano
3. WHEN Pagar.me sends a payment.failed webhook THEN the Webhook_Handler SHALL mark the subscription as past_due and notify the tenant admin
4. WHEN webhook signature is invalid THEN the Webhook_Handler SHALL reject the request with HTTP 401 and log the security event
5. WHEN webhook processing fails THEN the Webhook_Handler SHALL return HTTP 500 to trigger Pagar.me retry mechanism
6. WHEN subscription is activated THEN the Webhook_Handler SHALL enable all plan-restricted features for the establishment

### Requirement 6: Password Removal from Onboarding Response

**User Story:** As a security-conscious administrator, I want passwords removed from API responses, so that credentials are never exposed in transit or logs.

#### Acceptance Criteria

1. WHEN onboarding completes successfully THEN the Onboarding_API SHALL return establishment data without the password field
2. WHEN an establishment is queried THEN the Backend_API SHALL exclude password_hash from all JSON responses
3. WHEN an error occurs during onboarding THEN the Onboarding_API SHALL NOT include password in error response
4. WHEN establishment data is serialized THEN the Response_Builder SHALL filter out any fields matching "password" pattern
5. WHEN admin users are listed THEN the Backend_API SHALL exclude password_hash from user objects

### Requirement 7: Secret Key Hardcoded Fallback Removal

**User Story:** As a DevOps engineer, I want secret keys without hardcoded fallbacks, so that production deployments fail fast when keys are not configured.

#### Acceptance Criteria

1. WHEN FLASK_ENV is production THEN the Config_Class SHALL raise ValueError if SECRET_KEY is not set in environment
2. WHEN FLASK_ENV is production THEN the Config_Class SHALL raise ValueError if JWT_SECRET_KEY is not set in environment
3. WHEN FLASK_ENV is development THEN the Config_Class MAY use fallback keys but SHALL log a security warning
4. WHEN FLASK_ENV is testing THEN the Config_Class MAY use fixed test keys for reproducibility
5. WHEN the application starts in production mode THEN the Config_Class SHALL validate all required security variables before accepting requests

### Requirement 8: SQL Injection Prevention in Database Creation

**User Story:** As a security auditor, I want the database creation to use parameterized queries, so that malicious input cannot execute arbitrary SQL.

#### Acceptance Criteria

1. WHEN creating a tenant database THEN the MultiTenantManager SHALL use psycopg2.sql.Identifier to safely quote the database name
2. WHEN the estabelecimento_nome contains special characters THEN the SQL execution SHALL NOT allow SQL injection through identifier manipulation
3. WHEN database name is constructed THEN the MultiTenantManager SHALL validate the format matches expected pattern "tenant_{id}"
4. WHEN database creation fails THEN the MultiTenantManager SHALL log the error without exposing sensitive connection details
5. WHEN the database name is passed to CREATE DATABASE THEN the system SHALL use sql.SQL().format() with sql.Identifier() rather than string concatenation

### Requirement 9: Automated Test Coverage

**User Story:** As a developer, I want comprehensive automated tests, so that regressions are detected before reaching production.

#### Acceptance Criteria

1. WHEN unit tests run THEN the Test_Suite SHALL cover all model methods including edge cases
2. WHEN integration tests run THEN the Test_Suite SHALL test all API routes including authentication, authorization, and error handling
3. WHEN E2E tests run THEN the Test_Suite SHALL cover critical flows: login, PDV sale, product management, and customer operations
4. WHEN tests execute THEN each test SHALL be independent and not depend on execution order
5. WHEN test coverage is measured THEN the Test_Suite SHALL achieve minimum 80% code coverage
6. WHEN a test fails THEN the Test_Suite SHALL provide clear failure message with expected vs actual values

### Requirement 10: API Documentation

**User Story:** As an API consumer, I want comprehensive API documentation, so that I can integrate with the system efficiently.

#### Acceptance Criteria

1. WHEN accessing /api/docs THEN the API_Documentation SHALL display Swagger/OpenAPI UI with all endpoints
2. WHEN viewing an endpoint THEN the API_Documentation SHALL show request parameters, request body schema, and response schemas
3. WHEN viewing authentication-required endpoints THEN the API_Documentation SHALL indicate required headers and authentication method
4. WHEN the API changes THEN the API_Documentation SHALL be updated to reflect the changes
5. WHEN viewing error responses THEN the API_Documentation SHALL document all possible error codes and their meanings

### Requirement 11: CNPJ Placeholder Removal

**User Story:** As a new tenant, I want valid default data in the checkout form, so that I can complete onboarding without validation errors.

#### Acceptance Criteria

1. WHEN the onboarding form loads THEN the Form_Component SHALL display an empty CNPJ field or valid placeholder format
2. WHEN CNPJ is optional THEN the Form_Component SHALL NOT require CNPJ for checkout completion
3. WHEN CNPJ is provided THEN the Backend_API SHALL validate CNPJ format before accepting
4. WHEN a placeholder is shown THEN the Form_Component SHALL use "00.000.000/0000-00" format to guide user input

### Requirement 12: Duplicate Decorator Consolidation

**User Story:** As a security developer, I want a single authoritative super_admin_required decorator, so that security logic is not bypassed due to inconsistent implementations.

#### Acceptance Criteria

1. WHEN super_admin_required decorator is used THEN the Decorator_Module SHALL import from a single canonical location
2. WHEN multiple decorators exist with similar names THEN the Development_Team SHALL consolidate to one implementation
3. WHEN the decorator is applied THEN the Decorator SHALL check is_super_admin claim from JWT token
4. WHEN is_super_admin is false THEN the Decorator SHALL return HTTP 403 Forbidden
5. WHEN decorator implementations are searched THEN the Codebase SHALL contain exactly one definition of super_admin_required

### Requirement 13: Redundant Code Elimination

**User Story:** As a maintainer, I want a single email_service implementation, so that bug fixes apply consistently across the application.

#### Acceptance Criteria

1. WHEN email functionality is needed THEN the Application_Code SHALL import from a single email_service module
2. WHEN duplicate email implementations exist THEN the Development_Team SHALL consolidate to one canonical implementation
3. WHEN the canonical email_service is updated THEN all callers SHALL benefit from the update
4. WHEN email sending fails THEN the email_service SHALL provide consistent error handling across all use cases
5. WHEN searching for email implementations THEN the Codebase SHALL contain exactly one email_service definition

### Requirement 14: Stripe Webhook Exception Handling

**User Story:** As a developer, I want webhook errors to be properly logged, so that I can debug payment processing issues in production.

#### Acceptance Criteria

1. WHEN Stripe webhook processing raises an exception THEN the Webhook_Handler SHALL log the full exception with stack trace
2. WHEN webhook signature verification fails THEN the Webhook_Handler SHALL log the failure reason and return HTTP 400
3. WHEN webhook event type is unknown THEN the Webhook_Handler SHALL log the event type for investigation and return HTTP 200
4. WHEN webhook processing succeeds THEN the Webhook_Handler SHALL log key events for audit trail
5. WHEN an exception is caught THEN the Webhook_Handler SHALL NOT silently swallow the error without logging
