# Design Document: Dashboard Rendering from Backend

## Overview

The dashboard rendering system fetches comprehensive business metrics from the backend GET /api/dashboard/cientifico?days=30 endpoint and renders 6 main analytical sections. The design emphasizes data transformation, progressive rendering with loading states, responsive layout, and interactive modals for detailed insights. The system handles errors gracefully, formats metrics appropriately, and maintains performance through efficient data flow and component optimization.

## Architecture

### Data Flow

```
Backend API (/api/dashboard/cientifico?days=30)
    ↓
Fetch with Loading State
    ↓
Data Transformation Layer
    ├─ Transform Curva ABC data
    ├─ Extract RFM metrics
    ├─ Map temporal trends
    ├─ Separate anomalies/recommendations
    ├─ Map RH metrics
    └─ Map Fiados/Receivables data
    ↓
Component State Management
    ↓
Render 6 Sections
    ├─ Análise Detalhada (Curva ABC + RFM)
    ├─ Análise Temporal (Line Chart)
    ├─ Insights Científicos (Anomalies + Recommendations)
    ├─ RH (3 cards)
    ├─ Fiados (3 cards)
    └─ Receivables (Summary metrics)
    ↓
User Interactions
    ├─ Click Anomaly → Open AnomalyDetailsModal
    ├─ Click Recommendation → Open RecommendationDetailsModal
    └─ Retry on Error → Re-fetch data
```

### Component Hierarchy

```
DashboardPage
├─ LoadingState (Skeleton Loaders)
├─ ErrorState (Error Message + Retry)
├─ AnaliseDetalhadaSection
│  ├─ CurvaABCCards (3 cards with progress bars)
│  └─ RFMMetrics (3 numbers)
├─ AnaliseTemporal
│  └─ LineChart (2 lines: total, quantity)
├─ InsightsCientificosSection
│  ├─ AnomalyCards (Red, clickable)
│  ├─ RecommendationCards (Blue, clickable)
│  └─ Modals
│     ├─ AnomalyDetailsModal
│     └─ RecommendationDetailsModal
├─ RHSection
│  ├─ ActiveEmployeesCard
│  ├─ HoursWorkedCard
│  └─ PayrollCard
├─ FiadosSection
│  ├─ TotalCreditCard (Orange)
│  ├─ OverdueAccountsCard (Red)
│  └─ CreditCustomersCard (Blue)
└─ ReceivablesSection
   ├─ TotalOverdueMetric
   ├─ TotalDueMetric
   └─ TotalReceivableMetric
```

## Components and Interfaces

### Main Component: DashboardPage

**Purpose**: Orchestrates data fetching, transformation, and rendering of all 6 dashboard sections.

**Key Responsibilities**:
- Fetch data from backend on mount
- Manage loading and error states
- Transform backend data to component format
- Render all 6 sections
- Handle modal state management
- Implement retry logic

**State Management**:
```typescript
interface DashboardState {
  data: DashboardData | null;
  loading: boolean;
  error: string | null;
  selectedAnomaly: AnomalyData | null;
  selectedRecommendation: RecommendationData | null;
  anomalyModalOpen: boolean;
  recommendationModalOpen: boolean;
}
```

### Section Components

#### 1. AnaliseDetalhadaSection

**Purpose**: Display Curva ABC classification and RFM metrics.

**Props**:
```typescript
interface AnaliseDetalhadaSectionProps {
  curvaABC: CurvaABC;
  rfm: RFMMetrics;
  loading: boolean;
}
```

**Rendering Logic**:
- 3 cards for A, B, C classifications
- Each card shows: count, revenue, percentage with progress bar
- RFM section shows: Recency (days), Frequency (count), Monetary (currency)
- Fallback to 0% progress if data missing

#### 2. AnaliseTemporal

**Purpose**: Display sales trends over time with line chart.

**Props**:
```typescript
interface AnaliseTemporalProps {
  tendenciaVendas: TendenciaVenda[];
  loading: boolean;
}
```

**Rendering Logic**:
- Line chart with 2 series: total sales, quantity
- X-axis: dates, Y-axis: values
- Tooltip on hover showing exact values
- Responsive container that resizes with parent
- Empty state message if no data

#### 3. InsightsCientificosSection

**Purpose**: Display anomalies and recommendations as clickable cards.

**Props**:
```typescript
interface InsightsCientificosSectionProps {
  anomalias: AnomalyData[];
  recomendacoes: RecommendationData[];
  onAnomalyClick: (anomaly: AnomalyData) => void;
  onRecommendationClick: (rec: RecommendationData) => void;
  loading: boolean;
}
```

**Rendering Logic**:
- Red cards for anomalies (clickable)
- Blue cards for recommendations (clickable)
- Each card shows: title, description, severity/type
- Click handler opens corresponding modal
- Empty state if no insights

#### 4. RHSection

**Purpose**: Display HR metrics (active employees, hours worked, payroll).

**Props**:
```typescript
interface RHSectionProps {
  rhMetrics: RHMetrics;
  loading: boolean;
}
```

**Rendering Logic**:
- 3 cards: active_employees, hours_worked, payroll
- Format currency for payroll (Brazilian Real)
- Format hours as HH:MM
- Show 0 or N/A if missing

#### 5. FiadosSection

**Purpose**: Display credit and receivables metrics.

**Props**:
```typescript
interface FiadosSectionProps {
  fiadoSummary: FiadoSummary;
  loading: boolean;
}
```

**Rendering Logic**:
- 3 cards with color coding: orange (total), red (overdue), blue (customers)
- Format currency values
- Show customer count
- Empty state if no data

#### 6. ReceivablesSection

**Purpose**: Display accounts receivable summary.

**Props**:
```typescript
interface ReceivablesSectionProps {
  receivables: ReceivablesSummary;
  loading: boolean;
}
```

**Rendering Logic**:
- Display 3 metrics: total_vencido, total_a_vencer, total_recebivel
- Format all as currency
- Clear labels for each metric

### Modal Components

#### AnomalyDetailsModal

**Purpose**: Display detailed information about detected anomalies.

**Props**:
```typescript
interface AnomalyDetailsModalProps {
  anomaly: AnomalyData | null;
  isOpen: boolean;
  onClose: () => void;
}
```

**Features**:
- Severity badge (Alta, Média, Baixa)
- Description and impact
- Deviation percentage and confidence
- Recommended actions
- Investigation steps
- Resolution timeline

#### RecommendationDetailsModal

**Purpose**: Display detailed recommendations for optimization.

**Props**:
```typescript
interface RecommendationDetailsModalProps {
  recommendation: RecommendationData | null;
  isOpen: boolean;
  onClose: () => void;
}
```

**Features**:
- Recommendation title and description
- Expected impact
- Complexity level
- Implementation steps
- Success metrics

## Data Models

### Backend Response Structure

```typescript
interface DashboardData {
  success: boolean;
  usuario: {
    nome: string;
    role: string;
    acesso_avancado: boolean;
  };
  data: {
    analise_produtos: {
      curva_abc: CurvaABC;
      produtos_estrela: ProdutoEstrela[];
      produtos_lentos: ProdutoLento[];
    };
    analise_temporal: {
      tendencia_vendas: TendenciaVenda[];
      vendas_por_hora: VendaHora[];
    };
    insights_cientificos: {
      anomalias: AnomalyData[];
      recomendacoes: RecommendationData[];
      correlacoes: Correlacao[];
    };
    rh: RHMetrics;
    fiado_summary: FiadoSummary;
    receivables: ReceivablesSummary;
  };
}
```

### Curva ABC Data

```typescript
interface CurvaABC {
  classificacao: string;
  produtos: Array<{
    id: number;
    nome: string;
    faturamento: number;
    percentual_acumulado: number;
    classificacao: 'A' | 'B' | 'C';
    quantidade_vendida: number;
    margem: number;
  }>;
  resumo: {
    A: { quantidade: number; faturamento_total: number; percentual: number };
    B: { quantidade: number; faturamento_total: number; percentual: number };
    C: { quantidade: number; faturamento_total: number; percentual: number };
  };
}
```

### RFM Metrics

```typescript
interface RFMMetrics {
  recency: number;      // Days since last purchase
  frequency: number;    // Number of purchases
  monetary: number;     // Total value
}
```

### Temporal Data

```typescript
interface TendenciaVenda {
  data: string;         // YYYY-MM-DD
  total: number;        // Total sales
  quantidade: number;   // Quantity sold
  previsao?: number;    // Predicted value
}
```

### Anomaly Data

```typescript
interface AnomalyData {
  tipo: string;
  descricao: string;
  severidade: 'Alta' | 'Média' | 'Baixa';
  desvio: number;       // Percentage deviation
  confianca: number;    // Confidence percentage
  impacto_estimado: number;
  acao_recomendada: string;
  passos_investigacao: string[];
}
```

### RH Metrics

```typescript
interface RHMetrics {
  funcionarios_ativos: number;
  horas_trabalhadas: number;
  folha_pagamento: number;
  // Additional fields...
}
```

### Fiado Summary

```typescript
interface FiadoSummary {
  total_fiado: number;
  quantidade_clientes: number;
  vencido: number;
  a_vencer: number;
}
```

### Receivables Summary

```typescript
interface ReceivablesSummary {
  total_vencido: number;
  total_a_vencer: number;
  total_recebivel: number;
}
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Data Fetch Completes Successfully

*For any* dashboard page load, fetching data from the backend endpoint should complete and return a valid DashboardData object with all required sections.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Loading States Display During Fetch

*For any* data fetch operation, skeleton loaders should be visible while data is being retrieved and should be replaced with actual content once data arrives.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 3: Curva ABC Cards Render Correctly

*For any* valid Curva ABC data, the system should render exactly 3 cards (A, B, C) with progress bars showing percentual_acumulado values between 0-100%.

**Validates: Requirements 2.2, 2.3, 2.5**

### Property 4: RFM Metrics Display Correctly

*For any* valid RFM data, the system should display 3 numbers: Recency (days), Frequency (count), Monetary (currency format).

**Validates: Requirements 2.4, 2.6, 2.7**

### Property 5: Line Chart Renders with Two Series

*For any* valid temporal data, the line chart should display exactly 2 lines representing total sales and quantity, with proper X-axis (dates) and Y-axis (values).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 6: Anomaly Cards Are Clickable

*For any* anomaly card displayed, clicking it should open AnomalyDetailsModal with the corresponding anomaly data.

**Validates: Requirements 4.2, 4.4, 4.5**

### Property 7: Recommendation Cards Are Clickable

*For any* recommendation card displayed, clicking it should open RecommendationDetailsModal with the corresponding recommendation data.

**Validates: Requirements 4.3, 4.5, 4.6**

### Property 8: RH Section Displays Three Cards

*For any* valid RH metrics, the system should render exactly 3 cards displaying: active_employees (count), hours_worked (formatted), payroll (currency).

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

### Property 9: Fiados Section Displays Three Colored Cards

*For any* valid Fiado summary data, the system should render exactly 3 cards with correct color coding: orange (total_credit), red (overdue_accounts), blue (credit_customers).

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

### Property 10: Receivables Section Displays Summary Metrics

*For any* valid receivables data, the system should display 3 metrics: total_vencido, total_a_vencer, total_recebivel, all formatted as currency.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 11: Error Handling Shows Retry Option

*For any* failed data fetch, the system should display an error message and a retry button that re-fetches the data.

**Validates: Requirements 1.5, 1.6, 9.1, 9.2, 9.3**

### Property 12: Currency Formatting Is Consistent

*For any* currency value displayed, the system should format it as Brazilian Real (R$ format) with proper thousand separators and 2 decimal places.

**Validates: Requirements 13.1, 13.4, 13.6**

### Property 13: Responsive Layout Adapts to Viewport

*For any* viewport size change, the dashboard should re-layout sections appropriately: vertical stack on mobile, 2 columns on tablet, optimal layout on desktop.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

### Property 14: Modal Opens and Closes Without Errors

*For any* modal interaction (open/close), the system should not produce console errors and should properly manage focus and background scrolling.

**Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**

### Property 15: Data Transformation Preserves All Values

*For any* backend response, transforming the data to component format should preserve all numeric values and not introduce NaN or undefined values.

**Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6**

## Error Handling

### Fetch Errors

**Scenario**: Backend returns error or network is unavailable

**Handling**:
1. Catch error in try-catch block
2. Set error state with user-friendly message
3. Display error UI with retry button
4. Log error details for debugging
5. On retry, clear error state and re-fetch

**Error Messages**:
- Network error: "Network error - please check your connection"
- Invalid data: "Data format error - please refresh the page"
- Server error: "Server error - please try again later"
- Timeout: "Request timed out - please try again"

### Data Transformation Errors

**Scenario**: Backend data doesn't match expected format

**Handling**:
1. Validate data structure before transformation
2. Use optional chaining and nullish coalescing
3. Provide default values for missing fields
4. Log transformation errors
5. Display partial data with missing sections marked as "N/A"

### Component Rendering Errors

**Scenario**: Component fails to render

**Handling**:
1. Use Error Boundary to catch React errors
2. Display error message to user
3. Provide option to reload page
4. Log error stack trace

## Testing Strategy

### Unit Testing

**Test Coverage**:
- Data transformation functions (Curva ABC, RFM, temporal, etc.)
- Formatting functions (currency, dates, percentages)
- Modal open/close logic
- Error state handling
- Responsive layout breakpoints

**Example Tests**:
```typescript
describe('Data Transformation', () => {
  test('transforms Curva ABC data correctly', () => {
    const backendData = { /* ... */ };
    const result = transformCurvaABC(backendData);
    expect(result).toHaveLength(3);
    expect(result[0].classificacao).toBe('A');
  });

  test('formats currency as Brazilian Real', () => {
    const result = formatCurrency(1234.56);
    expect(result).toBe('R$ 1.234,56');
  });

  test('modal opens with correct data', () => {
    const { getByText } = render(
      <AnomalyDetailsModal anomaly={mockAnomaly} isOpen={true} onClose={jest.fn()} />
    );
    expect(getByText(mockAnomaly.descricao)).toBeInTheDocument();
  });
});
```

### Property-Based Testing

**Property Tests**:
1. **Data Fetch Round Trip**: Fetch data, transform, render, verify all values present
2. **Curva ABC Invariant**: Sum of A+B+C percentages equals 100%
3. **RFM Metrics Validity**: All RFM values are non-negative numbers
4. **Chart Data Consistency**: Chart displays same data as source
5. **Modal State Consistency**: Opening modal doesn't affect dashboard data
6. **Responsive Layout Invariant**: Layout changes don't lose data
7. **Error Recovery**: After error, retry successfully fetches data
8. **Currency Format Idempotence**: Formatting twice produces same result
9. **Timestamp Consistency**: All timestamps in same format
10. **Empty Data Handling**: Missing data doesn't cause crashes

**Example Property Test**:
```typescript
describe('Dashboard Properties', () => {
  test('Curva ABC percentages sum to 100%', () => {
    fc.assert(
      fc.property(fc.array(fc.record({
        classificacao: fc.constantFrom('A', 'B', 'C'),
        percentual_acumulado: fc.integer({ min: 0, max: 100 })
      })), (data) => {
        const result = transformCurvaABC(data);
        const sum = result.reduce((acc, item) => acc + item.percentual, 0);
        expect(sum).toBe(100);
      })
    );
  });

  test('Currency formatting is consistent', () => {
    fc.assert(
      fc.property(fc.integer({ min: 0, max: 1000000 }), (value) => {
        const formatted = formatCurrency(value);
        expect(formatted).toMatch(/^R\$ [\d.,]+$/);
      })
    );
  });
});
```

### Integration Testing

**Test Scenarios**:
1. Full dashboard load: fetch → transform → render all sections
2. Modal interaction: click anomaly → open modal → close modal
3. Error recovery: fetch fails → show error → click retry → success
4. Responsive behavior: resize viewport → layout adapts
5. Data updates: fetch new data → sections update

### Performance Testing

**Metrics**:
- Data fetch time: < 2 seconds
- Render time: < 100ms after data arrival
- Chart render: < 500ms
- Modal open: < 200ms
- Scroll performance: 60 FPS

**Tools**: React DevTools Profiler, Lighthouse, Web Vitals

