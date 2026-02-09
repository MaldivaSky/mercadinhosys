# Implementation Plan: Dashboard UX Improvements

## Overview

This implementation plan transforms the MercadinhoSys ERP Dashboard UX by introducing a global filter panel, reorganizing the layout, and enhancing user interaction patterns. The approach is incremental, building from foundational components to full integration, with testing at each stage to ensure correctness.

## Tasks

- [ ] 1. Create Filter Context and State Management Infrastructure
  - Create `FilterContext.tsx` with React Context for centralized filter state
  - Implement `FilterProvider` component with state management hooks
  - Define `FilterState` interface and default values
  - Implement session storage persistence utilities (save/load/validate)
  - Add debouncing for session storage writes
  - _Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.4, 6.5_

- [ ]* 1.1 Write property test for filter state persistence round-trip
  - **Property 10: Filter State Persistence Round-Trip**
  - **Validates: Requirements 6.1, 6.2, 6.4**

- [ ]* 1.2 Write property test for restored filter state validation
  - **Property 11: Restored Filter State Validation**
  - **Validates: Requirements 6.5**

- [ ] 2. Implement Date Range Filter Component
  - Create `DateRangeFilter.tsx` component with start/end date inputs
  - Integrate date picker library (react-datepicker or similar)
  - Implement date range validation (end >= start)
  - Add error message display for invalid ranges
  - Support keyboard input and calendar selection
  - Format dates for human-readable display
  - Connect to FilterContext for state updates
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ]* 2.1 Write property test for date range validation
  - **Property 6: Date Range Validation Prevents Invalid Ranges**
  - **Validates: Requirements 3.3**

- [ ]* 2.2 Write property test for invalid date input handling
  - **Property 7: Invalid Date Input Shows Error**
  - **Validates: Requirements 3.4**

- [ ]* 2.3 Write property test for date display formatting
  - **Property 8: Date Display Formatting**
  - **Validates: Requirements 3.6**

- [ ]* 2.4 Write unit tests for DateRangeFilter edge cases
  - Test leap year handling
  - Test timezone edge cases
  - Test empty input handling
  - _Requirements: 3.3, 3.4_

- [ ] 3. Implement Quick Preset Buttons Component
  - Create `QuickPresetButtons.tsx` component
  - Define preset configurations (Last 7/30/90 days, This Month, Last Month, This Quarter)
  - Implement date calculation logic for each preset
  - Add preset highlighting for active preset
  - Implement deactivation of highlighting on manual date changes
  - Connect to FilterContext for date range updates
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 3.1 Write property test for preset selection updates date range
  - **Property 3: Quick Preset Selection Updates Date Range**
  - **Validates: Requirements 2.4, 4.3**

- [ ]* 3.2 Write property test for preset highlighting
  - **Property 9: Preset Highlighting Reflects Active State**
  - **Validates: Requirements 4.4, 4.5**

- [ ]* 3.3 Write unit tests for preset date calculations
  - Test each preset calculation
  - Test edge cases (month boundaries, quarter boundaries)
  - _Requirements: 4.2, 4.3_

- [ ] 4. Implement View Mode Selector and ABC Class Filter Components
  - Create `ViewModeSelector.tsx` component with toggle/segmented control
  - Create `ABCClassFilter.tsx` component with class selection buttons
  - Add optional product count display for ABC classes
  - Connect both components to FilterContext
  - Implement proper styling and visual feedback
  - _Requirements: 2.2, 2.3_

- [ ]* 4.1 Write property test for ABC classification filtering
  - **Property 2: ABC Classification Filter Affects Only Product Sections**
  - **Validates: Requirements 2.3, 10.4**

- [ ] 5. Implement Active Filters Display Component
  - Create `ActiveFiltersDisplay.tsx` component
  - Display active filter chips/tags with filter summaries
  - Implement individual filter removal actions
  - Implement "Clear All Filters" action
  - Hide component when no filters are active
  - Connect to FilterContext for filter state and actions
  - _Requirements: 2.6, 8.2, 8.3_

- [ ]* 5.1 Write property test for active filters display
  - **Property 4: Active Filters Display Reflects Current State**
  - **Validates: Requirements 2.6, 8.2**

- [ ]* 5.2 Write property test for clear all filters availability
  - **Property 14: Clear All Filters Availability**
  - **Validates: Requirements 8.3**

- [ ] 6. Implement Global Filter Panel Component
  - Create `GlobalFilterPanel.tsx` as container component
  - Compose all filter components (DateRangeFilter, QuickPresetButtons, ViewModeSelector, ABCClassFilter, ActiveFiltersDisplay)
  - Implement sticky positioning with CSS
  - Create responsive layouts (desktop, tablet, mobile)
  - Add mobile collapsible sections for complex filters
  - Implement loading state that disables all controls
  - Add proper spacing and visual separation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 6.1 Write property test for mobile feature parity
  - **Property 17: Mobile Feature Parity**
  - **Validates: Requirements 9.3**

- [ ]* 6.2 Write unit tests for GlobalFilterPanel structure
  - Test all filter controls are present
  - Test sticky positioning behavior
  - Test responsive layouts at different breakpoints
  - Test touch target sizes on mobile
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 9.1, 9.4_

- [ ] 7. Checkpoint - Ensure filter components work in isolation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement Loading State and Empty State Components
  - Create `LoadingState.tsx` component with spinner/skeleton
  - Create `EmptyState.tsx` component with icon, message, and guidance
  - Define empty state variants (no data for date range, no data for ABC class, no data available)
  - Implement consistent styling across variants
  - Add action buttons for empty states (e.g., "Adjust Filters")
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

- [ ]* 8.1 Write property test for empty state display
  - **Property 12: Empty State Display for No Data**
  - **Validates: Requirements 7.1, 7.2**

- [ ]* 8.2 Write property test for empty state excludes loading indicators
  - **Property 13: Empty State Excludes Loading Indicators**
  - **Validates: Requirements 7.6**

- [ ]* 8.3 Write unit tests for empty state variants
  - Test date range empty state message
  - Test ABC class empty state message
  - Test general empty state message
  - _Requirements: 7.3, 7.4_

- [ ] 9. Enhance Existing Dashboard Sections to Consume Filter Context
  - Update `DashboardPage.tsx` to wrap content with FilterProvider
  - Create custom hook `useFilteredData` for sections to consume filter state
  - Update KPISection to filter by date range
  - Update CurvaABCSection to filter by ABC class and date range
  - Update AnaliseTemporalSection to filter by date range
  - Update AnaliseFinanceiraSection to filter by date range
  - Update InsightsCientificosSection to filter by date range and view mode
  - Update ProdutosEstrategicosSection to filter by ABC class and view mode
  - Update PrevisaoDemandaSection to filter by date range and view mode
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 9.1 Write property test for date range filter updates sections
  - **Property 1: Date Range Filter Updates All Time-Dependent Sections**
  - **Validates: Requirements 2.1**

- [ ]* 9.2 Write property test for section-specific filter isolation
  - **Property 18: Section-Specific Filter Isolation**
  - **Validates: Requirements 10.5**

- [ ]* 9.3 Write property test for combined filter application
  - **Property 20: Combined Filter Application**
  - **Validates: Requirements 10.1**

- [ ] 10. Implement Loading State Management for Sections
  - Add loading state tracking to FilterContext
  - Update sections to show LoadingState component during data fetch
  - Implement loading indicators on filter changes
  - Disable filter controls during loading
  - Re-enable controls after loading completes
  - _Requirements: 2.5, 8.1, 8.4, 8.5_

- [ ]* 10.1 Write property test for filter changes trigger loading
  - **Property 5: Filter Changes Trigger Loading Indicators**
  - **Validates: Requirements 2.5, 8.1**

- [ ]* 10.2 Write property test for loading state disables controls
  - **Property 15: Loading State Disables Filter Controls**
  - **Validates: Requirements 8.4**

- [ ]* 10.3 Write property test for completion state enables controls
  - **Property 16: Completion State Enables Controls**
  - **Validates: Requirements 8.5**

- [ ] 11. Implement Dashboard Layout Reorganization
  - Create `DashboardContent.tsx` wrapper component
  - Create `FinancialAnalysisGroup.tsx` grouping component
  - Create `ProductAnalysisGroup.tsx` grouping component
  - Update `DashboardPage.tsx` to use new layout structure
  - Position GlobalFilterPanel below header, above all sections
  - Position KPISection immediately below GlobalFilterPanel
  - Group financial sections (AnaliseFinanceira, AnaliseTemporal) together
  - Group product sections (CurvaABC, ProdutosEstrategicos, PrevisaoDemanda) together
  - Implement responsive grid layout with consistent spacing
  - _Requirements: 1.1, 5.3, 5.4, 5.5, 5.6_

- [ ]* 11.1 Write unit tests for layout structure
  - Test GlobalFilterPanel positioned before sections
  - Test KPISection positioned after GlobalFilterPanel
  - Test financial sections grouped together
  - Test product sections grouped together
  - Test responsive grid at different breakpoints
  - _Requirements: 1.1, 5.3, 5.4, 5.5, 5.6_

- [ ] 12. Checkpoint - Ensure layout and filtering work together
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement Performance Optimizations
  - Add React.memo to filter components to prevent unnecessary re-renders
  - Implement useMemo for expensive calculations (preset date calculations, filter summaries)
  - Add useCallback for filter action handlers
  - Implement debouncing for date input changes
  - Add batching for multiple filter changes
  - Optimize section re-rendering to only update affected sections
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ]* 13.1 Write property test for selective section re-rendering
  - **Property 21: Selective Section Re-rendering**
  - **Validates: Requirements 11.2**

- [ ]* 13.2 Write unit tests for performance optimizations
  - Test debouncing reduces update frequency
  - Test memoization prevents recalculation
  - Test batching combines multiple updates
  - _Requirements: 11.1, 11.3, 11.4_

- [ ] 14. Implement Accessibility Features
  - Add ARIA labels to all filter controls
  - Implement keyboard navigation (Tab, Enter, Arrow keys, Escape)
  - Add visible focus indicators to all interactive elements
  - Implement ARIA live regions for filter change announcements
  - Add keyboard shortcuts for common actions
  - Ensure WCAG 2.1 Level AA contrast ratios for all text and controls
  - Test with screen reader (NVDA or JAWS)
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ]* 14.1 Write property test for ARIA labels on filter controls
  - **Property 22: ARIA Labels for Filter Controls**
  - **Validates: Requirements 12.2**

- [ ]* 14.2 Write property test for screen reader announcements
  - **Property 23: Screen Reader Announcements for Filter Changes**
  - **Validates: Requirements 12.3**

- [ ]* 14.3 Write property test for visible focus indicators
  - **Property 24: Visible Focus Indicators**
  - **Validates: Requirements 12.4**

- [ ]* 14.4 Write unit tests for accessibility features
  - Test keyboard navigation works
  - Test focus indicators are visible
  - Test ARIA live regions update
  - Test keyboard shortcuts trigger actions
  - Test color contrast meets WCAG 2.1 AA
  - _Requirements: 12.1, 12.4, 12.5, 12.6_

- [ ] 15. Implement Section-Specific Filter Integration
  - Update CurvaABCSection to support both global and section-specific ABC filters
  - Implement filter conflict resolution (section-specific takes precedence)
  - Add visual distinction between global and section-specific filters
  - Ensure section-specific filters only affect their section
  - Maintain independent state for section-specific filters
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 15.1 Write property test for filter conflict resolution
  - **Property 19: Filter Conflict Resolution**
  - **Validates: Requirements 10.2**

- [ ]* 15.2 Write unit tests for section-specific filter integration
  - Test global + section filters combine correctly
  - Test section filter precedence
  - Test section filter isolation
  - _Requirements: 10.1, 10.2, 10.4, 10.5_

- [ ] 16. Implement Error Handling and Edge Cases
  - Add error boundaries for component errors
  - Implement network error handling for data fetching
  - Add timeout handling for slow requests
  - Implement session storage error handling (quota exceeded, invalid data)
  - Add schema version migration for stored filter state
  - Handle missing FilterContext gracefully
  - Add retry actions for failed data fetches
  - _Requirements: All (error handling is cross-cutting)_

- [ ]* 16.1 Write unit tests for error handling
  - Test network error displays error state
  - Test timeout shows timeout message
  - Test session storage quota exceeded
  - Test invalid stored data recovery
  - Test error boundary catches component errors
  - _Requirements: All (error handling)_

- [ ] 17. Final Integration and Polish
  - Integrate GlobalFilterPanel into DashboardPage
  - Verify all sections respond correctly to all filters
  - Test all filter combinations work together
  - Verify session persistence works across page refreshes
  - Test responsive behavior on actual devices (mobile, tablet, desktop)
  - Verify loading states and empty states display correctly
  - Test accessibility with keyboard-only navigation
  - Polish styling and animations
  - _Requirements: All_

- [ ]* 17.1 Write integration tests for complete filter workflows
  - Test apply filters → refresh page → filters restored
  - Test date range + ABC class + view mode together
  - Test clear all filters resets everything
  - Test mobile responsive behavior
  - _Requirements: All_

- [ ] 18. Final Checkpoint - Comprehensive Testing
  - Run all unit tests and property tests
  - Run integration tests
  - Run accessibility tests with jest-axe
  - Verify all 24 correctness properties pass
  - Test on multiple browsers (Chrome, Firefox, Safari, Edge)
  - Test on multiple devices (desktop, tablet, mobile)
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (24 total)
- Unit tests validate specific examples, edge cases, and error conditions
- Integration tests validate complete user workflows
- All filter components should be built with accessibility in mind from the start
- Performance optimizations should be implemented early to avoid refactoring later
- Session storage persistence should be tested thoroughly to ensure reliability

