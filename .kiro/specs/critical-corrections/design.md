# Design Document: Critical Corrections for MercadinhoSys ERP

## Overview

This design document specifies the technical approach for implementing 14 critical corrections across the MercadinhoSys ERP system. The corrections span frontend rendering issues, backend persistence bugs, security vulnerabilities, and missing integrations. The system uses Flask with SQLAlchemy ORM on the backend and React with TypeScript on the frontend, with PostgreSQL for production and SQLite for development.

## Architecture

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MercadinhoSys ERP                           │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend (React/Vite/TypeScript)                                   │
│  ├── Dashboard Components (metrics rendering)                       │
│  ├── PDV Module (MultiPaymentManager)                               │
│  ├── Delivery Module (tracking interface)                           │
│  └── Onboarding Flow                                                │
├─────────────────────────────────────────────────────────────────────┤
│  Backend (Flask/Python/SQLAlchemy)                                  │
│  ├── REST API Routes (28 blueprints)                                │
│  ├── Multi-tenant Middleware                                        │
│  ├── Webhook Handlers (Stripe, Pagar.me)                            │
│  ├── Authentication (JWT/RBAC)                                      │
│  └── Models (Venda, Pagamento, Estabelecimento)                     │
├─────────────────────────────────────────────────────────────────────┤
│  Database Layer                                                     │
│  ├── PostgreSQL (Production multi-tenant)                           │
│  ├── SQLite (Development/Fallback)                                  │
│  └── Redis Cache (Optional)                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Interaction

```
┌──────────────┐    HTTP/REST    ┌──────────────┐
│   Frontend   │ ◄─────────────► │   Backend    │
│  (Port 5173) │                 │  (Port 5000) │
└──────────────┘                 └──────────────┘
                                       │
                                       ▼
                                 ┌──────────────┐
                                 │   Database   │
                                 │ PostgreSQL/  │
                                 │   SQLite     │
                                 └──────────────┘
                                       ▲
                                       │
                                 ┌──────────────┐
                                 │   Webhooks   │
                                 │ Stripe/Pagar │
                                 └──────────────┘
```

## Components and Interfaces

### 1. Dashboard Rendering Components

**Location:** `frontend/mercadinhosys-frontend/src/pages/DashboardPage.tsx`

**Interface: DashboardDataTransformer**
```typescript
interface DashboardDataTransformer {
  transformCurvaABC(data: AnaliseProdutos): CurvaABCCards[];
  transformRFM(insights: InsightsCientificos): RFMMetrics;
  transformRH(rhData: RHMetrics): RHCardData[];
  transformFiados(fiadoData: FiadoSummary): FiadosCardData[];
}
```

**Implementation Approach:**
1. Create data transformation utilities in `frontend/src/utils/dashboardTransformers.ts`
2. Map backend response fields to component props
3. Implement loading states with React Suspense
4. Add error boundaries for each section

**Component Structure:**
```
DashboardPage/
├── OverviewSection.tsx (existing)
├── AnaliseDetalhadaSection.tsx (enhance)
│   ├── CurvaABCCards.tsx
│   └── RFMMetrics.tsx
├── AnaliseTemporalSection.tsx (existing)
├── InsightsCientificosSection.tsx (enhance)
│   ├── AnomalyCard.tsx
│   ├── RecommendationCard.tsx
│   ├── AnomalyDetailsModal.tsx
│   └── RecommendationDetailsModal.tsx
├── RHSection.tsx (new)
└── FiadosSection.tsx (new)
```

### 2. MultiPaymentManager Persistence

**Location:** `frontend/mercadinhosys-frontend/src/features/pdv/components/MultiPaymentManager.tsx`

**Interface: PagamentoPersistence**
```typescript
interface PagamentoItem {
  id: string;
  forma: string;
  valor: number;
  bandeira?: string;
}

interface MultiPaymentPayload {
  pagamentos: PagamentoItem[];
  venda_id: number;
  total: number;
}
```

**Backend Endpoint:** `POST /api/pdv/finalizar`

**Implementation Approach:**
1. Ensure frontend passes `pagamentos` array in finalize request
2. Backend creates Pagamento records for each item in the array
3. Validate sum of payments equals sale total
4. Transaction rollback if any payment fails

**Data Flow:**
```
User adds payment → MultiPaymentManager state → 
PDVPage collects pagamentos → POST /api/pdv/finalizar →
Backend creates Venda + Pagamento records
```

### 3. Delivery Interface

**Location:** `frontend/mercadinhosys-frontend/src/features/delivery/DeliveryPage.tsx`

**Interface: DeliveryAPI**
```typescript
interface Delivery {
  id: number;
  cliente_id: number;
  cliente_nome: string;
  endereco: string;
  status: 'pending' | 'in_transit' | 'delivered' | 'cancelled';
  total: number;
  items: DeliveryItem[];
  created_at: string;
}

interface DeliveryService {
  getPendingDeliveries(): Promise<Delivery[]>;
  updateStatus(id: number, status: string): Promise<void>;
  getDeliveryDetails(id: number): Promise<Delivery>;
}
```

**Backend Routes:** Already exist in `backend/app/routes/delivery.py`

**Implementation Approach:**
1. Create deliveryService.ts with API calls
2. Implement DeliveryPage with status badges and action buttons
3. Add real-time status updates via polling or WebSocket
4. Create delivery detail modal

### 4. Seed Data Enhancement

**Location:** `backend/app/commands.py` or `backend/seed.py`

**Implementation Approach:**
```python
def create_multi_payment_sales(total_sales: int):
    for i in range(total_sales // 10):  # 10% of sales
        venda = create_sale()
        num_payments = random.randint(2, 3)
        remaining = venda.total
        
        for j in range(num_payments - 1):
            payment_amount = random.uniform(remaining * 0.2, remaining * 0.8)
            create_pagamento(venda.id, random_payment_form(), payment_amount)
            remaining -= payment_amount
        
        # Final payment gets the remainder
        create_pagamento(venda.id, random_payment_form(), remaining)
```

### 5. Pagar.me Webhook Handler

**Location:** `backend/app/routes/webhooks.py` (new file)

**Interface: WebhookHandler**
```python
class PagarMeWebhookHandler:
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature using Pagar.me secret"""
        
    def handle_subscription_created(self, data: dict) -> None:
        """Create pending subscription record"""
        
    def handle_payment_succeeded(self, data: dict) -> None:
        """Activate subscription and update plan"""
        
    def handle_payment_failed(self, data: dict) -> None:
        """Mark subscription as past_due"""
```

**Endpoint:** `POST /api/webhooks/pagarme`

**Implementation Approach:**
1. Create dedicated webhook blueprint
2. Implement signature verification
3. Map event types to handler methods
4. Update Estabelecimento.plano field
5. Send notification emails on status changes

### 6. Password Exposure Fix

**Location:** `backend/app/routes/auth.py` and all establishment routes

**Implementation Approach:**
1. Add response filter decorator to strip password fields
2. Or use SQLAlchemy model property `@property` to exclude password from serialization
3. Audit all jsonify() calls returning user/establishment data

**Pattern:**
```python
def sanitize_response(data: dict) -> dict:
    """Remove sensitive fields from response"""
    sensitive_fields = ['password', 'password_hash', 'senha']
    return {k: v for k, v in data.items() if k not in sensitive_fields}
```

### 7. Secret Key Security Fix

**Location:** `backend/config.py`

**Implementation Approach:**
```python
class Config:
    _secret_key = os.environ.get("SECRET_KEY")
    _jwt_secret = os.environ.get("JWT_SECRET_KEY")
    
    # Remove fallbacks for production
    if os.environ.get("FLASK_ENV") == "production":
        if not _secret_key:
            raise ValueError("CRITICAL: SECRET_KEY não configurada no ambiente de produção!")
        if not _jwt_secret:
            raise ValueError("CRITICAL: JWT_SECRET_KEY não configurada no ambiente de produção!")
    
    SECRET_KEY = _secret_key
    JWT_SECRET_KEY = _jwt_secret

class DevelopmentConfig(Config):
    DEBUG = True
    # Only allow fallbacks in development
    SECRET_KEY = Config._secret_key or "dev-fallback-secret-key-12345"
    JWT_SECRET_KEY = Config._jwt_secret or "dev-fallback-jwt-key-67890"
```

### 8. SQL Injection Prevention

**Location:** `backend/app/middleware/multi_tenant.py`

**Current Code (Line 117):**
```python
cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
```

**Issue:** The code already uses `psycopg2.sql.Identifier` which is safe. However, validation should be added.

**Implementation Approach:**
```python
def create_tenant_database(self, estabelecimento_id: int, estabelecimento_nome: str) -> bool:
    """Creates database for new tenant with validated name"""
    
    # Validate estabelecimento_id is numeric
    if not isinstance(estabelecimento_id, int) or estabelecimento_id <= 0:
        raise ValueError("Invalid estabelecimento_id")
    
    # Construct database name with validated input
    db_name = f"tenant_{estabelecimento_id}"
    
    # Use sql.Identifier for safe quoting (already implemented)
    from psycopg2 import sql
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
```

### 9. Test Coverage

**Location:** `backend/app/tests/`

**Test Structure:**
```
backend/app/tests/
├── conftest.py (fixtures)
├── factories.py (test data factories)
├── unit/
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_services.py
├── integration/
│   ├── test_auth_routes.py
│   ├── test_pdv_routes.py
│   ├── test_delivery_routes.py
│   └── test_webhooks.py
└── e2e/
    └── test_complete_flows.py
```

**Frontend Tests:**
```
frontend/tests/
├── unit/
│   ├── DashboardTransformers.test.ts
│   └── MultiPaymentManager.test.tsx
└── e2e/
    └── cypress/
        ├── login.cy.ts
        ├── pdv-sale.cy.ts
        └── delivery.cy.ts
```

### 10. API Documentation

**Location:** `backend/app/swagger/` (already partially exists)

**Implementation Approach:**
1. Use Flask-RESTX or Flasgger for OpenAPI/Swagger
2. Document all 28 blueprints
3. Include request/response schemas
4. Add authentication requirements

**Swagger Configuration:**
```python
from flasgger import Swagger

app.config['SWAGGER'] = {
    'title': 'MercadinhoSys API',
    'version': '2.2.0',
    'description': 'Multi-tenant ERP API for small markets',
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}
```

## Data Models

### Existing Models (No Changes Required)

**Venda Model:**
```python
class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'))
    estabelecimento_id = db.Column(db.Integer, db.ForeignKey('estabelecimentos.id'))
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    desconto = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='finalizada')
    pagamentos = db.relationship('Pagamento', backref='venda', lazy=True)
```

**Pagamento Model:**
```python
class Pagamento(db.Model):
    __tablename__ = 'pagamentos'
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    forma = db.Column(db.String(50), nullable=False)  # dinheiro, pix, cartao_credito, etc.
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    bandeira = db.Column(db.String(50))  # Visa, Mastercard, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Frontend Data Types

**Dashboard Data:**
```typescript
interface DashboardResponse {
  overview: OverviewMetrics;
  analise_produtos: {
    curva_abc: CurvaABCData;
  };
  analise_temporal: {
    tendencia_vendas: TrendData[];
  };
  insights_cientificos: {
    anomalias: Anomaly[];
    recomendacoes: Recommendation[];
  };
  rh: {
    funcionarios_ativos: number;
    horas_trabalhadas: number;
    folha_pagamento: number;
  };
  fiado_summary: {
    total_fiado: number;
    vencido: number;
    quantidade_clientes: number;
  };
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Dashboard Section Rendering Completeness

*For any* valid dashboard data response from the backend, the frontend SHALL render all 6 sections (Overview, Análise Detalhada, Análise Temporal, Insights Científicos, RH, Fiados) and display all required metrics within each section.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.7**

### Property 2: Multi-Payment Sum and Persistence

*For any* sale with multiple payments, the sum of all payment amounts SHALL equal the sale total, and all payments SHALL be persisted to the database atomically with each payment linked to the Venda.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 4.2, 4.3**

### Property 3: Delivery Data Rendering

*For any* delivery data returned from the backend, the Delivery_Component SHALL render cards containing customer name, address, order total, and status, and any status update SHALL trigger an API call to persist the change.

**Validates: Requirements 3.3, 3.5**

### Property 4: Seed Multi-Payment Coverage

*For any* seed execution, at least 10% of created sales SHALL have 2 or more payment methods, payment totals SHALL sum to sale total, and payment methods SHALL be varied across available types.

**Validates: Requirements 4.1, 4.3, 4.4**

### Property 5: Subscription Activation After Payment

*For any* subscription activation webhook (payment.succeeded), the Webhook_Handler SHALL update the establishment.plano field and enable all plan-restricted features.

**Validates: Requirements 5.6**

### Property 6: Password Field Exclusion from Responses

*For any* API response containing establishment or user data (success or error), the response SHALL NOT include any field matching "password" pattern (password, password_hash, senha).

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

### Property 7: Production Security Variables Validation

*For any* production environment startup, the application SHALL raise ValueError if SECRET_KEY or JWT_SECRET_KEY is not configured in the environment before accepting any requests.

**Validates: Requirements 7.1, 7.2, 7.5**

### Property 8: SQL Identifier Safety

*For any* database name passed to CREATE DATABASE, the name SHALL match pattern "tenant_{numeric_id}" and be properly escaped using sql.Identifier to prevent SQL injection.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 9: API Documentation Completeness

*For any* documented API endpoint, the Swagger documentation SHALL include request parameters, request body schema, response schemas, authentication requirements, and error codes.

**Validates: Requirements 10.2, 10.3, 10.5**

### Property 10: CNPJ Validation and Optionality

*For any* CNPJ value provided during onboarding, the Backend_API SHALL validate the format, and the Form_Component SHALL NOT require CNPJ for form submission completion.

**Validates: Requirements 11.2, 11.3**

### Property 11: Single Decorator Implementation

*For any* codebase search, there SHALL exist exactly one definition of the super_admin_required decorator, and the decorator SHALL check is_super_admin claim from JWT token returning HTTP 403 when false.

**Validates: Requirements 12.1, 12.3, 12.4, 12.5**

### Property 12: Single Email Service Implementation

*For any* codebase search, there SHALL exist exactly one email_service module definition, and all email operations SHALL use consistent error handling.

**Validates: Requirements 13.1, 13.3, 13.4, 13.5**

### Property 13: Webhook Error Logging Completeness

*For any* exception during webhook processing, the Webhook_Handler SHALL log the full exception with stack trace and SHALL NOT silently swallow any error without logging.

**Validates: Requirements 14.1, 14.4, 14.5**

## Error Handling

### Frontend Error Handling

**Dashboard Loading Errors:**
1. Network errors: Display "Network error - check connection" with retry button
2. Server errors (5xx): Display "Server temporarily unavailable" with retry button
3. Data format errors: Display "Unable to load dashboard" with refresh link
4. Partial data: Render available sections, show error placeholder for missing sections

**MultiPayment Errors:**
1. Invalid payment amount: Show validation error below input
2. Sum mismatch: Show "Payments must equal sale total" message
3. Persistence failure: Show "Unable to process sale" with retry option

### Backend Error Handling

**Webhook Processing:**
1. Invalid signature: Return HTTP 401, log security event
2. Unknown event type: Log event type, return HTTP 200 (acknowledge)
3. Processing failure: Return HTTP 500 (trigger retry), log full stack trace
4. Database error: Rollback transaction, log error, return HTTP 500

**Multi-Payment Processing:**
1. Payment sum mismatch: Return HTTP 400 with validation message
2. Invalid payment method: Return HTTP 400 with invalid payment type
3. Database failure: Rollback all payments, return HTTP 500

### Error Response Format

```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "Payment total does not match sale total",
  "code": "PAYMENT_SUM_MISMATCH"
}
```

## Testing Strategy

### Unit Tests

**Backend Models:**
- Test Venda total calculation
- Test Pagamento relationship
- Test Estabelecimento plan restrictions

**Frontend Components:**
- Test MultiPaymentManager payment sum calculation
- Test Dashboard data transformation
- Test delivery status formatting

### Integration Tests

**API Routes:**
- Test PDV finalize with single payment
- Test PDV finalize with multiple payments
- Test webhook signature verification
- Test onboarding flow without password exposure

**Database Operations:**
- Test tenant database creation
- Test multi-payment persistence
- Test subscription activation

### Property-Based Tests

**Using pytest with Hypothesis (backend) and fast-check (frontend):**

1. **Payment Sum Property:** For any generated payment list, sum equals sale total
2. **Password Exclusion Property:** For any generated response, password fields absent
3. **SQL Identifier Property:** For any valid ID, generated database name is safe

### E2E Tests (Cypress)

**Critical Flows:**
1. Login → Dashboard renders all sections
2. PDV → Add products → Add multiple payments → Finalize → Verify in database
3. Onboarding → Complete registration → Verify password not in response

### Test Configuration

**Backend (pytest):**
```ini
[pytest]
minversion = 6.0
addopts = -ra -q --cov=app --cov-report=term-missing
testpaths = tests
```

**Frontend (Vitest + Cypress):**
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'tests/']
    }
  }
})
```
