# Implementation Plan: Critical Corrections for MercadinhoSys ERP

## Overview

This implementation plan breaks down 14 critical corrections into discrete coding tasks. The tasks are organized by priority: security fixes first, then functional bugs, then quality improvements. Each task builds on previous work and includes optional testing sub-tasks.

## Tasks

- [x] 1. Fix Secret Key Hardcoded Fallbacks (Security Critical)
  - Remove hardcoded fallback keys from DevelopmentConfig and TestingConfig
  - Add production validation that raises ValueError if SECRET_KEY or JWT_SECRET_KEY not set
  - Add logging warning when fallbacks are used in development
  - _Requirements: 7.1, 7.2, 7.3, 7.5_
  
  - [ ]* 1.1 Write unit tests for secret key validation
    - **Property 7: Production Security Variables Validation**
    - **Validates: Requirements 7.1, 7.2, 7.5**

- [ ] 2. Remove Password from API Responses (Security Critical)
  - Create response sanitization utility to filter password fields
  - Apply sanitization to all establishment and user routes
  - Audit auth.py and onboarding routes for password exposure
  - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ]* 2.1 Write property tests for password exclusion
    - **Property 6: Password Field Exclusion from Responses**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

- [ ] 3. Fix SQL Injection in Database Creation (Security Critical)
  - Add validation for estabelecimento_id format in create_tenant_database
  - Ensure psycopg2.sql.Identifier is used consistently
  - Add error logging without exposing connection details
  - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [ ]* 3.1 Write property tests for SQL identifier safety
    - **Property 8: SQL Identifier Safety**
    - **Validates: Requirements 8.1, 8.2, 8.3**

- [ ] 4. Consolidate Duplicate Decorators (Security)
  - Search codebase for all super_admin_required definitions
  - Consolidate to single canonical implementation
  - Update all imports to use canonical location
  - Ensure decorator checks is_super_admin claim and returns 403 when false
  - _Requirements: 12.1, 12.3, 12.4, 12.5_
  
  - [ ]* 4.1 Write unit tests for super_admin_required decorator
    - **Property 11: Single Decorator Implementation**
    - **Validates: Requirements 12.3, 12.4**

- [ ] 5. Consolidate Duplicate Email Service (Code Quality)
  - Search codebase for duplicate email_service implementations
  - Consolidate to single canonical module
  - Ensure consistent error handling across all callers
  - Update all imports
  - _Requirements: 13.1, 13.3, 13.4, 13.5_

- [ ] 6. Implement Pagar.me Webhook Handler (Critical Integration)
  - Create backend/app/routes/webhooks.py blueprint
  - Implement signature verification using Pagar.me secret
  - Implement handlers for subscription.created, payment.succeeded, payment.failed
  - Update establishment.plano on successful payment
  - Register webhook blueprint in __init__.py
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [ ]* 6.1 Write unit tests for webhook handlers
    - **Property 5: Subscription Activation After Payment**
    - **Validates: Requirements 5.2, 5.6**

- [ ] 7. Fix Stripe Webhook Exception Handling (Debug)
  - Remove try/except that swallows exceptions
  - Add proper logging with stack traces for all webhook events
  - Return HTTP 400 for signature failures, HTTP 200 for unknown events
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_
  
  - [ ]* 7.1 Write unit tests for webhook error logging
    - **Property 13: Webhook Error Logging Completeness**
    - **Validates: Requirements 14.1, 14.4, 14.5**

- [ ] 8. Fix MultiPaymentManager Persistence (Critical Functional)
  - Verify frontend passes pagamentos array to /api/pdv/finalizar
  - Update backend to create Pagamento records for each payment item
  - Add validation that payment sum equals sale total
  - Implement atomic transaction with rollback on failure
  - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 8.1 Write property tests for multi-payment persistence
    - **Property 2: Multi-Payment Sum and Persistence**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [ ] 9. Update Seed Script for Multi-Payment Sales (Test Data)
  - Modify seed to create sales with 2+ payment methods for 10% of sales
  - Ensure payment totals sum to sale total
  - Vary payment methods across available types
  - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 9.1 Write property tests for seed multi-payment coverage
    - **Property 4: Seed Multi-Payment Coverage**
    - **Validates: Requirements 4.1, 4.3, 4.4**

- [ ] 10. Implement Dashboard RH and Fiados Sections (Functional)
  - Create RHSection component with 3 cards (active_employees, hours_worked, payroll)
  - Create FiadosSection component with 3 cards (total_fiado, vencido, quantidade_clientes)
  - Add data transformation for rh and fiado_summary from backend
  - Format currency values as Brazilian Real
  - _Requirements: 1.2, 1.3_
  
  - [ ]* 10.1 Write property tests for dashboard rendering
    - **Property 1: Dashboard Section Rendering Completeness**
    - **Validates: Requirements 1.1, 1.2, 1.3**

- [ ] 11. Implement Dashboard Analysis Modals (Functional)
  - Create AnomalyDetailsModal component
  - Create RecommendationDetailsModal component
  - Wire modal opening to anomaly/recommendation card clicks
  - Display cause, impact, and suggested actions
  - _Requirements: 1.5, 1.6_

- [ ] 12. Implement Delivery Interface (Functional)
  - Create deliveryService.ts with API calls
  - Implement DeliveryPage with pending deliveries list
  - Add status badges and action buttons
  - Implement delivery detail view
  - Connect to existing backend routes
  - _Requirements: 3.1, 3.2, 3.3, 3.5_
  
  - [ ]* 12.1 Write property tests for delivery data rendering
    - **Property 3: Delivery Data Rendering**
    - **Validates: Requirements 3.3, 3.5**

- [ ] 13. Fix CNPJ Placeholder in Onboarding (Data Quality)
  - Update onboarding form to use valid placeholder format "00.000.000/0000-00"
  - Make CNPJ field optional for form completion
  - Add backend validation for CNPJ format when provided
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ] 14. Implement Swagger API Documentation (Quality)
  - Configure Flasgger in backend app
  - Document all 28 blueprints with OpenAPI annotations
  - Include request/response schemas and authentication requirements
  - Document error codes for each endpoint
  - _Requirements: 10.1, 10.2, 10.3, 10.5_
  
  - [ ]* 14.1 Write property tests for API documentation completeness
    - **Property 9: API Documentation Completeness**
    - **Validates: Requirements 10.2, 10.3, 10.5**

- [ ] 15. Checkpoint - Ensure all critical fixes pass tests
  - Run all unit tests and property tests
  - Verify security fixes work correctly
  - Test multi-payment flow end-to-end
  - Ask user if questions arise

- [ ] 16. Set up Testing Infrastructure (Quality Foundation)
  - Configure pytest with coverage reporting
  - Set up test fixtures and factories
  - Configure Vitest for frontend unit tests
  - Set up Cypress for E2E tests
  - Create test database configuration
  - _Requirements: 9.1, 9.4, 9.5_

- [ ] 17. Write Backend Unit Tests (Quality)
  - Write unit tests for Venda and Pagamento models
  - Write unit tests for authentication routes
  - Write unit tests for PDV routes
  - Write unit tests for webhook routes
  - _Requirements: 9.1_

- [ ] 18. Write Frontend Unit Tests (Quality)
  - Write tests for MultiPaymentManager component
  - Write tests for Dashboard transformation utilities
  - Write tests for Delivery components
  - _Requirements: 9.1_

- [ ] 19. Write E2E Tests (Quality)
  - Write Cypress test for login flow
  - Write Cypress test for PDV sale with multiple payments
  - Write Cypress test for dashboard rendering
  - _Requirements: 9.3_

- [ ] 20. Final Checkpoint - Ensure all tests pass
  - Run full test suite
  - Verify test coverage meets 80% target
  - Run E2E tests
  - Ask user if questions arise

## Notes

- Tasks 1-7 address security issues and should be completed first
- Tasks 8-13 address functional bugs and missing features
- Tasks 14-19 are quality improvements that can run in parallel
- Tasks marked with `*` are optional test tasks that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
