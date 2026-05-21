# Requirements Document: Dashboard Rendering from Backend

## Introduction

The dashboard needs to render 6 main analytical sections with data fetched from the backend GET /api/dashboard/cientifico?days=30 endpoint. Each section displays specific business metrics and insights with proper data visualization, loading states, error handling, and responsive design. The implementation must handle data transformation from the backend format, manage loading states, and provide interactive modals for detailed information.

## Glossary

- **Dashboard**: The main analytics page displaying business metrics across 6 sections
- **Backend_API**: GET /api/dashboard/cientifico?days=30 endpoint returning comprehensive dashboard data
- **Section**: A major dashboard area containing related metrics (e.g., Análise Detalhada, RH)
- **Card**: A visual component displaying a single metric or group of related metrics
- **Modal**: A dialog component that opens when clicking on anomalies or recommendations for detailed information
- **Loading_State**: Visual feedback (skeleton loaders) shown while data is being fetched
- **Error_State**: User-friendly error message displayed when data fetch fails
- **Responsive_Design**: Layout that adapts to mobile, tablet, and desktop screen sizes
- **Data_Transformation**: Process of converting backend data format to frontend component format
- **Curva_ABC**: Product classification system (A, B, C) based on sales contribution
- **RFM**: Recency, Frequency, Monetary analysis for customer segmentation
- **Anomaly**: Unusual data pattern detected by backend analysis
- **Recommendation**: Suggested action based on data insights
- **Progress_Bar**: Visual indicator showing percentage or ratio (0-100%)
- **Line_Chart**: Graph showing trends over time with multiple data series
- **Skeleton_Loader**: Placeholder animation shown during data loading

## Requirements

### Requirement 1: Fetch Dashboard Data from Backend

**User Story:** As a dashboard user, I want the system to fetch comprehensive dashboard data from the backend, so that I can view all business metrics in one place.

#### Acceptance Criteria

1. WHEN the dashboard page loads THEN the system SHALL fetch data from GET /api/dashboard/cientifico?days=30 endpoint
2. WHEN the fetch request is initiated THEN the system SHALL display loading states for all 6 sections
3. WHEN the data is successfully fetched THEN the system SHALL store the complete response in component state
4. WHEN the fetch completes within 2 seconds THEN the system SHALL display all sections without delay
5. IF the fetch request fails THEN the system SHALL display a user-friendly error message and retry option
6. WHEN the user clicks retry THEN the system SHALL re-fetch the data from the backend
7. WHEN the component unmounts THEN the system SHALL cancel any pending fetch requests

### Requirement 2: Render Análise Detalhada Section

**User Story:** As a business analyst, I want to see detailed product analysis with Curva ABC and RFM metrics, so that I can understand product performance and customer value.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL render the Análise Detalhada section after the Overview section
2. WHEN rendering Curva ABC THEN the system SHALL display 3 cards (A, B, C) with progress bars showing percentage distribution
3. WHEN rendering Curva ABC cards THEN the system SHALL show product count and faturamento (revenue) for each classification
4. WHEN rendering RFM metrics THEN the system SHALL display 3 numbers: Recency (days), Frequency (count), Monetary (total value)
5. WHEN data contains Curva ABC information THEN the system SHALL calculate and display percentual_acumulado for each classification
6. WHEN Curva ABC data is missing THEN the system SHALL display placeholder values with 0% progress
7. WHEN RFM data is missing THEN the system SHALL display "N/A" for each metric

### Requirement 3: Render Análise Temporal Section

**User Story:** As a sales manager, I want to see sales trends over time, so that I can identify patterns and make informed decisions.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL render the Análise Temporal section with a line chart
2. WHEN rendering the line chart THEN the system SHALL display 2 lines: total sales and quantity sold
3. WHEN the chart displays data THEN the system SHALL show dates on X-axis and values on Y-axis
4. WHEN hovering over data points THEN the system SHALL display a tooltip with exact values
5. WHEN tendencia_vendas data is available THEN the system SHALL plot actual vs predicted values
6. WHEN data is missing THEN the system SHALL display an empty chart with "No data available" message
7. WHEN the chart renders THEN the system SHALL be responsive and resize with container

### Requirement 4: Render Insights Científicos Section

**User Story:** As a data analyst, I want to see anomalies and recommendations as clickable cards, so that I can investigate issues and implement improvements.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL render the Insights Científicos section with anomalies and recommendations
2. WHEN rendering anomalies THEN the system SHALL display red cards with anomaly information
3. WHEN rendering recommendations THEN the system SHALL display blue cards with recommendation information
4. WHEN a user clicks on an anomaly card THEN the system SHALL open AnomalyDetailsModal with detailed information
5. WHEN a user clicks on a recommendation card THEN the system SHALL open RecommendationDetailsModal with detailed information
6. WHEN the modal opens THEN the system SHALL display complete details including cause, impact, and suggested actions
7. WHEN the user closes the modal THEN the system SHALL return focus to the dashboard
8. IF anomalies or recommendations are empty THEN the system SHALL display "No insights available" message

### Requirement 5: Render RH Section

**User Story:** As an HR manager, I want to see employee metrics including active employees, hours worked, and payroll, so that I can monitor workforce costs and productivity.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL render the RH section with 3 cards
2. WHEN rendering RH cards THEN the system SHALL display: active_employees, hours_worked, payroll
3. WHEN displaying active_employees THEN the system SHALL show the count of funcionarios_ativos
4. WHEN displaying hours_worked THEN the system SHALL show total horas_trabalhadas for the period
5. WHEN displaying payroll THEN the system SHALL show folha_pagamento total in currency format
6. WHEN RH data is missing THEN the system SHALL display 0 or "N/A" for each metric
7. WHEN the section renders THEN the system SHALL format currency values with proper locale (Brazilian Real)

### Requirement 6: Render Fiados Section

**User Story:** As a credit manager, I want to see credit and receivables metrics, so that I can monitor customer credit exposure and overdue accounts.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL render the Fiados section with 3 cards
2. WHEN rendering Fiados cards THEN the system SHALL display: total_credit (orange), overdue_accounts (red), credit_customers (blue)
3. WHEN displaying total_credit THEN the system SHALL show total_fiado in currency format
4. WHEN displaying overdue_accounts THEN the system SHALL show vencido (overdue amount) in red
5. WHEN displaying credit_customers THEN the system SHALL show quantidade_clientes (customer count)
6. WHEN Fiados data is missing THEN the system SHALL display 0 or "N/A" for each metric
7. WHEN the section renders THEN the system SHALL apply appropriate color coding (orange, red, blue)

### Requirement 7: Render Receivables Section

**User Story:** As a finance manager, I want to see accounts receivable summary metrics, so that I can track outstanding invoices and cash flow.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL render the Receivables section with summary metrics
2. WHEN rendering Receivables THEN the system SHALL display: total_vencido, total_a_vencer, total_recebivel
3. WHEN displaying metrics THEN the system SHALL format all values as currency
4. WHEN Receivables data is missing THEN the system SHALL display 0 or "N/A" for each metric
5. WHEN the section renders THEN the system SHALL show clear labels for each metric

### Requirement 8: Implement Loading States

**User Story:** As a user, I want to see loading indicators while data is being fetched, so that I understand the system is working and not frozen.

#### Acceptance Criteria

1. WHEN the dashboard page loads THEN the system SHALL display skeleton loaders for all 6 sections
2. WHEN data is being fetched THEN the system SHALL show animated skeleton placeholders
3. WHEN a section's data arrives THEN the system SHALL replace skeleton with actual content
4. WHEN all data is loaded THEN the system SHALL remove all skeleton loaders
5. WHEN the fetch takes longer than 3 seconds THEN the system SHALL display a "Loading..." message
6. WHEN the user navigates away THEN the system SHALL cancel skeleton animations

### Requirement 9: Implement Error Handling

**User Story:** As a user, I want to see helpful error messages when something goes wrong, so that I understand what happened and can take action.

#### Acceptance Criteria

1. IF the backend returns an error THEN the system SHALL display a user-friendly error message
2. WHEN an error occurs THEN the system SHALL display a "Retry" button
3. WHEN the user clicks Retry THEN the system SHALL re-fetch the data
4. IF the network is unavailable THEN the system SHALL display "Network error - please check your connection"
5. IF the backend returns invalid data THEN the system SHALL display "Data format error - please refresh the page"
6. WHEN an error is displayed THEN the system SHALL log the error details for debugging
7. WHEN the error is resolved THEN the system SHALL automatically reload the dashboard

### Requirement 10: Implement Responsive Design

**User Story:** As a mobile user, I want the dashboard to work properly on my phone and tablet, so that I can view metrics on any device.

#### Acceptance Criteria

1. WHEN the dashboard renders on mobile (< 640px) THEN the system SHALL stack sections vertically
2. WHEN the dashboard renders on tablet (640px - 1024px) THEN the system SHALL display 2 columns
3. WHEN the dashboard renders on desktop (> 1024px) THEN the system SHALL display optimal layout
4. WHEN cards render on mobile THEN the system SHALL ensure text is readable without horizontal scroll
5. WHEN charts render on mobile THEN the system SHALL adjust font sizes and spacing
6. WHEN modals open on mobile THEN the system SHALL display full-screen or large modal
7. WHEN the viewport resizes THEN the system SHALL re-layout sections without errors

### Requirement 11: Transform Backend Data to Component Format

**User Story:** As a developer, I want the system to properly transform backend data, so that components receive correctly formatted data.

#### Acceptance Criteria

1. WHEN backend data is received THEN the system SHALL map analise_produtos.curva_abc to Curva ABC cards
2. WHEN backend data is received THEN the system SHALL extract RFM metrics from insights_cientificos
3. WHEN backend data is received THEN the system SHALL map analise_temporal.tendencia_vendas to line chart data
4. WHEN backend data is received THEN the system SHALL separate anomalias and recomendacoes into different card arrays
5. WHEN backend data is received THEN the system SHALL map rh metrics to RH section cards
6. WHEN backend data is received THEN the system SHALL map fiado_summary to Fiados section cards
7. WHEN data transformation fails THEN the system SHALL display error message and log transformation error

### Requirement 12: Handle Modal Interactions

**User Story:** As a user, I want to click on anomalies and recommendations to see details, so that I can understand issues and take action.

#### Acceptance Criteria

1. WHEN a user clicks an anomaly card THEN the system SHALL open AnomalyDetailsModal with anomaly data
2. WHEN a user clicks a recommendation card THEN the system SHALL open RecommendationDetailsModal with recommendation data
3. WHEN a modal is open THEN the system SHALL prevent scrolling on the background
4. WHEN a user clicks the close button THEN the system SHALL close the modal and restore focus
5. WHEN a user presses Escape key THEN the system SHALL close the modal
6. WHEN a modal closes THEN the system SHALL not reload the dashboard data
7. WHEN multiple modals could open THEN the system SHALL only display one modal at a time

### Requirement 13: Format and Display Metrics

**User Story:** As a user, I want metrics to be properly formatted and easy to read, so that I can quickly understand the values.

#### Acceptance Criteria

1. WHEN displaying currency values THEN the system SHALL format as Brazilian Real (R$ format)
2. WHEN displaying percentages THEN the system SHALL show with 1 decimal place (e.g., 45.2%)
3. WHEN displaying large numbers THEN the system SHALL use thousand separators (e.g., 1.234.567)
4. WHEN displaying dates THEN the system SHALL use Brazilian date format (DD/MM/YYYY)
5. WHEN displaying time values THEN the system SHALL show hours and minutes (HH:MM)
6. WHEN a value is zero THEN the system SHALL display "0" or "R$ 0,00" appropriately
7. WHEN a value is missing THEN the system SHALL display "N/A" instead of undefined

### Requirement 14: Ensure No Console Errors

**User Story:** As a developer, I want the dashboard to run without console errors, so that the application is stable and professional.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL not produce any console errors
2. WHEN data is fetched THEN the system SHALL not produce any console warnings
3. WHEN sections render THEN the system SHALL not produce any React warnings
4. WHEN modals open/close THEN the system SHALL not produce any console errors
5. WHEN the user interacts with the dashboard THEN the system SHALL not produce any console errors
6. WHEN the viewport resizes THEN the system SHALL not produce any console errors
7. WHEN data is missing THEN the system SHALL handle gracefully without console errors

### Requirement 15: Optimize Performance

**User Story:** As a user, I want the dashboard to load quickly and respond smoothly, so that I have a good experience.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL fetch data within 2 seconds
2. WHEN sections render THEN the system SHALL display content within 100ms of data arrival
3. WHEN the user scrolls THEN the system SHALL maintain 60 FPS without jank
4. WHEN charts render THEN the system SHALL not block the main thread
5. WHEN modals open THEN the system SHALL open within 200ms
6. WHEN the dashboard is idle THEN the system SHALL not consume CPU resources
7. WHEN data updates THEN the system SHALL only re-render affected sections

