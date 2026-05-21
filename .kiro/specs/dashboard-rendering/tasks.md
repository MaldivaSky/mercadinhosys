# Implementation Plan: Dashboard Rendering from Backend

## Overview

This implementation plan breaks down the dashboard rendering feature into discrete coding tasks. The approach follows a data-driven architecture: fetch backend data → transform to component format → render 6 sections with loading states → handle errors and interactions. Each task builds incrementally, with testing integrated throughout to catch issues early.

## Tasks

- [ ] 1. Set up data fetching and state management
  - Create fetch function for GET /api/dashboard/cientifico?days=30 endpoint
  - Implement loading and error state management
  - Add abort controller for cleanup on unmount
  - Set up retry logic with exponential backoff
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [ ]* 1.1 Write property test for data fetch completion
  - **Property 1: Data Fetch Completes Successfully**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [ ] 2. Implement data transformation layer
  - Create transformation functions for each section (Curva ABC, RFM, Temporal, Insights, RH, Fiados, Receivables)
  - Map backend data structure to component format
  - Handle missing/null values with appropriate defaults
  - Add error handling for malformed data
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ]* 2.1 Write property test for data transformation
  - **Property 15: Data Transformation Preserves All Values**
  - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6**

- [ ] 3. Implement loading states with skeleton loaders
  - Create skeleton loader components for each section
  - Display skeletons while data is loading
  - Replace skeletons with actual content when data arrives
  - Add timeout message if fetch takes > 3 seconds
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ]* 3.1 Write property test for loading state display
  - **Property 2: Loading States Display During Fetch**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [ ] 4. Implement error handling and retry logic
  - Display user-friendly error messages for different error types
  - Show retry button on error
  - Log error details for debugging
  - Handle network errors, invalid data, and timeouts
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ]* 4.1 Write unit tests for error handling
  - Test network error message display
  - Test invalid data error message display
  - Test retry button functionality
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 5. Implement Análise Detalhada section (Curva ABC + RFM)
  - Create CurvaABCCards component with 3 cards (A, B, C)
  - Display progress bars with percentual_acumulado values
  - Show product count and revenue for each classification
  - Create RFMMetrics component displaying Recency, Frequency, Monetary
  - Format metrics appropriately (days, count, currency)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 13.1, 13.2, 13.3_

- [ ]* 5.1 Write property test for Curva ABC rendering
  - **Property 3: Curva ABC Cards Render Correctly**
  - **Validates: Requirements 2.2, 2.3, 2.5**

- [ ]* 5.2 Write property test for RFM metrics
  - **Property 4: RFM Metrics Display Correctly**
  - **Validates: Requirements 2.4, 2.6, 2.7**

- [ ] 6. Implement Análise Temporal section (Line Chart)
  - Create LineChart component with 2 series (total sales, quantity)
  - Configure X-axis (dates) and Y-axis (values)
  - Add tooltip on hover showing exact values
  - Make chart responsive and resize with container
  - Handle empty data with "No data available" message
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ]* 6.1 Write property test for line chart rendering
  - **Property 5: Line Chart Renders with Two Series**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [ ]* 6.2 Write unit test for chart responsiveness
  - Test chart resizes with container
  - Test empty data message displays
  - _Requirements: 3.6, 3.7_

- [ ] 7. Implement Insights Científicos section (Anomalies + Recommendations)
  - Create AnomalyCard component (red cards, clickable)
  - Create RecommendationCard component (blue cards, clickable)
  - Implement click handlers to open corresponding modals
  - Display "No insights available" when empty
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

- [ ]* 7.1 Write property test for anomaly card rendering
  - **Property 6: Anomaly Cards Are Clickable**
  - **Validates: Requirements 4.2, 4.4, 4.5**

- [ ]* 7.2 Write property test for recommendation card rendering
  - **Property 7: Recommendation Cards Are Clickable**
  - **Validates: Requirements 4.3, 4.5, 4.6**

- [ ] 8. Implement modal interactions
  - Wire AnomalyDetailsModal to open on anomaly card click
  - Wire RecommendationDetailsModal to open on recommendation card click
  - Implement modal close handlers (close button, Escape key)
  - Prevent background scrolling when modal is open
  - Ensure only one modal displays at a time
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

- [ ]* 8.1 Write unit tests for modal interactions
  - Test modal opens with correct data
  - Test modal closes on button click
  - Test modal closes on Escape key
  - Test background scroll is prevented
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 9. Implement RH section (3 cards)
  - Create RHCard component displaying active_employees, hours_worked, payroll
  - Format hours as HH:MM
  - Format payroll as Brazilian Real currency
  - Display 0 or "N/A" for missing data
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [ ]* 9.1 Write property test for RH section rendering
  - **Property 8: RH Section Displays Three Cards**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [ ] 10. Implement Fiados section (3 colored cards)
  - Create FiadosCard component with 3 cards: total_credit (orange), overdue_accounts (red), credit_customers (blue)
  - Format currency values as Brazilian Real
  - Apply correct color coding to each card
  - Display 0 or "N/A" for missing data
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [ ]* 10.1 Write property test for Fiados section rendering
  - **Property 9: Fiados Section Displays Three Colored Cards**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

- [ ] 11. Implement Receivables section (Summary metrics)
  - Create ReceivablesMetrics component displaying total_vencido, total_a_vencer, total_recebivel
  - Format all values as Brazilian Real currency
  - Display clear labels for each metric
  - Display 0 or "N/A" for missing data
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 11.1 Write property test for Receivables section rendering
  - **Property 10: Receivables Section Displays Summary Metrics**
  - **Validates: Requirements 7.1, 7.2, 7.3**

- [ ] 12. Implement formatting utilities
  - Create formatCurrency function (Brazilian Real with proper separators)
  - Create formatPercentage function (1 decimal place)
  - Create formatDate function (DD/MM/YYYY)
  - Create formatTime function (HH:MM)
  - Create formatNumber function (thousand separators)
  - Handle zero and missing values appropriately
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

- [ ]* 12.1 Write property tests for formatting functions
  - **Property 12: Currency Formatting Is Consistent**
  - **Validates: Requirements 13.1, 13.4, 13.6**

- [ ] 13. Implement responsive design
  - Create responsive layout that stacks vertically on mobile (< 640px)
  - Create 2-column layout on tablet (640px - 1024px)
  - Create optimal layout on desktop (> 1024px)
  - Ensure text is readable without horizontal scroll on mobile
  - Adjust font sizes and spacing for mobile charts
  - Display full-screen modals on mobile
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ]* 13.1 Write property test for responsive layout
  - **Property 13: Responsive Layout Adapts to Viewport**
  - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

- [ ] 14. Implement console error prevention
  - Review all components for potential console errors
  - Add proper null/undefined checks
  - Use optional chaining and nullish coalescing
  - Verify no React warnings during render
  - Test modal interactions for errors
  - Test viewport resize for errors
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

- [ ]* 14.1 Write property test for error-free execution
  - **Property 14: Modal Opens and Closes Without Errors**
  - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**

- [ ] 15. Implement performance optimizations
  - Optimize data fetch to complete within 2 seconds
  - Optimize render to display content within 100ms of data arrival
  - Ensure 60 FPS during scroll
  - Prevent main thread blocking during chart render
  - Optimize modal open time to < 200ms
  - Implement lazy loading for sections if needed
  - Only re-render affected sections on data updates
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

- [ ]* 15.1 Write performance tests
  - Measure data fetch time
  - Measure render time after data arrival
  - Measure FPS during scroll
  - Measure modal open time
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 16. Checkpoint - Ensure all tests pass
  - Run all unit tests and verify they pass
  - Run all property-based tests with minimum 100 iterations
  - Verify no console errors or warnings
  - Check responsive design on multiple screen sizes
  - Verify all sections render correctly with sample data
  - Ask the user if questions arise.

- [ ] 17. Integration and final wiring
  - Wire all 6 sections together in DashboardPage
  - Ensure data flows correctly from fetch → transform → render
  - Verify modal state management works correctly
  - Test error recovery flow
  - Test retry functionality
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [ ]* 17.1 Write integration tests
  - Test full dashboard load flow
  - Test modal interactions
  - Test error recovery
  - Test responsive behavior
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [ ] 18. Final checkpoint - Ensure all tests pass
  - Run all tests (unit, property, integration)
  - Verify no console errors or warnings
  - Test on multiple browsers and screen sizes
  - Verify performance metrics are met
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests use minimum 100 iterations for comprehensive coverage
- All formatting functions should handle edge cases (zero, negative, missing values)
- Responsive design should be tested on actual devices or browser dev tools
- Performance metrics should be measured using React DevTools Profiler and Lighthouse
- Error messages should be user-friendly and actionable
- All modals should be accessible (keyboard navigation, screen readers)

