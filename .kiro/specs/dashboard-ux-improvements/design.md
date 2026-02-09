# Design Document: Dashboard UX Improvements

## Overview

This design addresses critical UX issues in the MercadinhoSys ERP Dashboard by implementing a global filter panel, reorganizing the layout, and enhancing user interaction patterns. The solution maintains all existing functionality while dramatically improving usability through strategic component architecture and state management.

### Design Principles

1. **Filter-First Architecture**: Global filters positioned prominently at the top, affecting all relevant sections
2. **Progressive Enhancement**: Maintain existing functionality while adding new capabilities
3. **Component Isolation**: Separate filter logic from presentation logic for maintainability
4. **Performance-Conscious**: Efficient re-rendering and state updates
5. **Accessibility-First**: Full keyboard navigation and screen reader support

### Key Design Decisions

- **React Context for Filter State**: Centralized filter state management using React Context API to avoid prop drilling
- **Compound Component Pattern**: Filter panel composed of smaller, reusable filter components
- **CSS Grid for Layout**: Responsive grid system for section organization
- **Sticky Positioning**: Native CSS sticky for filter panel persistence
- **Session Storage**: Browser session storage for filter state persistence

## Architecture

### High-Level Component Structure

```
DashboardPage (Container)
├── DashboardHeader (Existing)
├── GlobalFilterPanel (New)
│   ├── DateRangeFilter
│   ├── QuickPresetButtons
│   ├── ViewModeSelector
│   ├── ABCClassFilter
│   └── ActiveFiltersDisplay
├── DashboardContent (New Wrapper)
│   ├── KPISection (Existing, Enhanced)
│   ├── FinancialAnalysisGroup (New Grouping)
│   │   ├── AnaliseFinanceiraSection
│   │   └── AnaliseTemporalSection
│   ├── ProductAnalysisGroup (New Grouping)
│   │   ├── CurvaABCSection
│   │   ├── ProdutosEstrategicosSection
│   │   └── PrevisaoDemandaSection
│   └── InsightsCientificosSection
└── DashboardFooter (Existing)
```

### State Management Architecture

```typescript
// Filter Context Structure
interface FilterContextValue {
  // Filter State
  dateRange: { start: Date; end: Date };
  viewMode: 'executivo' | 'cientifico';
  abcClass: 'all' | 'A' | 'B' | 'C';
  activePreset: string | null;
  
  // Filter Actions
  setDateRange: (range: { start: Date; end: Date }) => void;
  setViewMode: (mode: 'executivo' | 'cientifico') => void;
  setABCClass: (class: 'all' | 'A' | 'B' | 'C') => void;
  setQuickPreset: (preset: string) => void;
  clearAllFilters: () => void;
  
  // State Indicators
  isLoading: boolean;
  hasActiveFilters: boolean;
}
```

### Data Flow

1. **User Interaction** → Filter component captures input
2. **Filter Update** → Context updates filter state
3. **State Persistence** → Session storage saves filter state
4. **Section Notification** → Sections subscribe to filter changes via context
5. **Data Refetch** → Sections request filtered data from backend
6. **UI Update** → Sections re-render with new data

## Components and Interfaces

### 1. GlobalFilterPanel Component

**Purpose**: Centralized filter control interface positioned at the top of the dashboard

**Props Interface**:
```typescript
interface GlobalFilterPanelProps {
  className?: string;
  sticky?: boolean;
}
```

**Responsibilities**:
- Render all global filter controls
- Manage sticky positioning behavior
- Display active filter summary
- Provide "Clear All" functionality

**Layout Structure**:
- Desktop: Horizontal layout with filters in a single row
- Tablet: Two-row layout with primary filters on top
- Mobile: Collapsible accordion with expandable filter sections

### 2. DateRangeFilter Component

**Purpose**: Allow users to select custom date ranges for analysis

**Props Interface**:
```typescript
interface DateRangeFilterProps {
  value: { start: Date; end: Date };
  onChange: (range: { start: Date; end: Date }) => void;
  minDate?: Date;
  maxDate?: Date;
  disabled?: boolean;
}
```

**Responsibilities**:
- Render date picker interface
- Validate date range (end >= start)
- Format dates for display
- Handle keyboard input
- Emit change events

**Validation Rules**:
- End date must not be before start date
- Dates must be within available data range
- Invalid dates trigger error messages

### 3. QuickPresetButtons Component

**Purpose**: Provide one-click access to common date ranges

**Props Interface**:
```typescript
interface QuickPresetButtonsProps {
  activePreset: string | null;
  onPresetSelect: (preset: string, range: { start: Date; end: Date }) => void;
  disabled?: boolean;
}
```

**Preset Definitions**:
```typescript
const QUICK_PRESETS = [
  { id: 'last7days', label: 'Last 7 Days', days: 7 },
  { id: 'last30days', label: 'Last 30 Days', days: 30 },
  { id: 'last90days', label: 'Last 90 Days', days: 90 },
  { id: 'thisMonth', label: 'This Month', calculation: 'currentMonth' },
  { id: 'lastMonth', label: 'Last Month', calculation: 'previousMonth' },
  { id: 'thisQuarter', label: 'This Quarter', calculation: 'currentQuarter' }
];
```

**Responsibilities**:
- Render preset buttons
- Calculate date ranges for each preset
- Highlight active preset
- Deactivate highlighting when custom dates are set

### 4. ViewModeSelector Component

**Purpose**: Toggle between Executivo and Científico view modes

**Props Interface**:
```typescript
interface ViewModeSelectorProps {
  value: 'executivo' | 'cientifico';
  onChange: (mode: 'executivo' | 'cientifico') => void;
  disabled?: boolean;
}
```

**Responsibilities**:
- Render toggle switch or segmented control
- Emit mode change events
- Display current mode clearly

### 5. ABCClassFilter Component

**Purpose**: Filter product-related sections by ABC classification

**Props Interface**:
```typescript
interface ABCClassFilterProps {
  value: 'all' | 'A' | 'B' | 'C';
  onChange: (class: 'all' | 'A' | 'B' | 'C') => void;
  disabled?: boolean;
  showCounts?: boolean;
  counts?: { A: number; B: number; C: number };
}
```

**Responsibilities**:
- Render class selection buttons or dropdown
- Display product counts per class (optional)
- Emit class change events
- Show "All" option for no filtering

### 6. ActiveFiltersDisplay Component

**Purpose**: Show summary of currently active filters with clear actions

**Props Interface**:
```typescript
interface ActiveFiltersDisplayProps {
  filters: {
    dateRange?: string;
    viewMode?: string;
    abcClass?: string;
  };
  onClearAll: () => void;
  onClearFilter: (filterKey: string) => void;
}
```

**Responsibilities**:
- Display active filter chips/tags
- Provide individual filter removal
- Provide "Clear All" action
- Hide when no filters are active

### 7. FilterContext Provider

**Purpose**: Centralized filter state management accessible to all dashboard sections

**Context Interface**:
```typescript
interface FilterContextValue {
  // State
  dateRange: { start: Date; end: Date };
  viewMode: 'executivo' | 'cientifico';
  abcClass: 'all' | 'A' | 'B' | 'C';
  activePreset: string | null;
  isLoading: boolean;
  hasActiveFilters: boolean;
  
  // Actions
  setDateRange: (range: { start: Date; end: Date }) => void;
  setViewMode: (mode: 'executivo' | 'cientifico') => void;
  setABCClass: (class: 'all' | 'A' | 'B' | 'C') => void;
  setQuickPreset: (preset: string) => void;
  clearAllFilters: () => void;
  resetToDefaults: () => void;
}
```

**Responsibilities**:
- Maintain filter state
- Persist state to session storage
- Restore state on page load
- Notify subscribers of changes
- Manage loading states

### 8. Enhanced Section Components

**Purpose**: Update existing sections to consume filter context

**Pattern for All Sections**:
```typescript
const SectionComponent: React.FC = () => {
  const { dateRange, viewMode, abcClass, isLoading } = useFilterContext();
  
  // Fetch data based on filters
  const { data, loading } = useDashboardData({
    startDate: dateRange.start,
    endDate: dateRange.end,
    abcClass: abcClass !== 'all' ? abcClass : undefined
  });
  
  // Render with loading state or empty state
  if (loading || isLoading) return <LoadingState />;
  if (!data || data.length === 0) return <EmptyState />;
  
  return <SectionContent data={data} />;
};
```

**Sections to Enhance**:
- KPISection (date range filtering)
- CurvaABCSection (ABC class filtering)
- AnaliseTemporalSection (date range filtering)
- AnaliseFinanceiraSection (date range filtering)
- InsightsCientificosSection (date range filtering, view mode)
- ProdutosEstrategicosSection (ABC class filtering, view mode)
- PrevisaoDemandaSection (date range filtering, view mode)

### 9. EmptyState Component

**Purpose**: Provide informative feedback when sections have no data

**Props Interface**:
```typescript
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  suggestions?: string[];
}
```

**Responsibilities**:
- Display icon, title, and descriptive message
- Provide actionable suggestions
- Offer action button (e.g., "Adjust Filters")
- Maintain consistent styling

**Empty State Variants**:
- **No Data for Date Range**: "No data available for the selected period. Try expanding your date range."
- **No Data for ABC Class**: "No products found in Class {X}. Try selecting 'All Products' or a different class."
- **No Data Available**: "Data is not yet available. Please check back later or contact support."

### 10. LoadingState Component

**Purpose**: Provide visual feedback during data fetching

**Props Interface**:
```typescript
interface LoadingStateProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
}
```

**Responsibilities**:
- Display loading spinner or skeleton
- Show optional loading message
- Maintain section dimensions to prevent layout shift

## Data Models

### FilterState Model

```typescript
interface FilterState {
  dateRange: {
    start: Date;
    end: Date;
  };
  viewMode: 'executivo' | 'cientifico';
  abcClass: 'all' | 'A' | 'B' | 'C';
  activePreset: string | null;
}
```

**Default Values**:
```typescript
const DEFAULT_FILTER_STATE: FilterState = {
  dateRange: {
    start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000), // 90 days ago
    end: new Date()
  },
  viewMode: 'executivo',
  abcClass: 'all',
  activePreset: 'last90days'
};
```

### QuickPreset Model

```typescript
interface QuickPreset {
  id: string;
  label: string;
  calculation: 'days' | 'currentMonth' | 'previousMonth' | 'currentQuarter';
  days?: number;
}
```

### DashboardSection Model

```typescript
interface DashboardSection {
  id: string;
  title: string;
  component: React.ComponentType;
  filterDependencies: ('dateRange' | 'viewMode' | 'abcClass')[];
  viewModes: ('executivo' | 'cientifico')[];
  order: number;
  group: 'kpi' | 'financial' | 'product' | 'insights';
}
```

### SessionStorageSchema

```typescript
interface DashboardSessionStorage {
  version: string; // Schema version for migration
  filters: FilterState;
  timestamp: number; // When state was saved
}
```

**Storage Key**: `mercadinhosys_dashboard_filters`

**Persistence Strategy**:
- Save to session storage on every filter change (debounced)
- Load from session storage on component mount
- Validate stored data before applying
- Clear on browser tab close (automatic with session storage)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Date Range Filter Updates All Time-Dependent Sections

*For any* valid date range selection, all time-dependent dashboard sections (KPIs, Análise Temporal, Análise Financeira, Insights Científicos, Previsão de Demanda) should receive and display data filtered to that exact date range.

**Validates: Requirements 2.1**

### Property 2: ABC Classification Filter Affects Only Product Sections

*For any* ABC class selection (A, B, C, or all), only product-related sections (Curva ABC, Produtos Estratégicos, Previsão de Demanda) should filter their data, and all displayed products should match the selected classification.

**Validates: Requirements 2.3, 10.4**

### Property 3: Quick Preset Selection Updates Date Range

*For any* quick preset button (Last 7/30/90 days, This Month, Last Month, This Quarter), clicking the preset should immediately update the Date_Range_Filter to the calculated date range corresponding to that preset.

**Validates: Requirements 2.4, 4.3**

### Property 4: Active Filters Display Reflects Current State

*For any* combination of active filters (date range, view mode, ABC class), the Filter_Panel should display a complete and accurate summary showing all currently applied filters.

**Validates: Requirements 2.6, 8.2**

### Property 5: Filter Changes Trigger Loading Indicators

*For any* filter change (date range, view mode, ABC class), all affected dashboard sections should immediately display loading indicators until data fetching completes.

**Validates: Requirements 2.5, 8.1**

### Property 6: Date Range Validation Prevents Invalid Ranges

*For any* date pair where the end date is before the start date, the Date_Range_Filter should display a validation error and prevent the filter from being applied.

**Validates: Requirements 3.3**

### Property 7: Invalid Date Input Shows Error

*For any* invalid date input (malformed date string, out-of-range date, null date), the System should display an error message and prevent filter application.

**Validates: Requirements 3.4**

### Property 8: Date Display Formatting

*For any* valid date range in the filter state, the displayed date range should be formatted in a human-readable format (e.g., "Jan 1, 2024 - Mar 31, 2024").

**Validates: Requirements 3.6**

### Property 9: Preset Highlighting Reflects Active State

*For any* quick preset, when that preset's date range matches the current Date_Range_Filter value, the preset button should be visually highlighted; when dates are manually adjusted, all preset highlighting should be removed.

**Validates: Requirements 4.4, 4.5**

### Property 10: Filter State Persistence Round-Trip

*For any* valid filter state (date range, view mode, ABC class), saving the state to session storage and then restoring it should produce an equivalent filter state with all fields preserved.

**Validates: Requirements 6.1, 6.2, 6.4**

### Property 11: Restored Filter State Validation

*For any* filter state loaded from session storage, the System should validate all fields (date range validity, view mode enum, ABC class enum) before applying the state, and should fall back to defaults if validation fails.

**Validates: Requirements 6.5**

### Property 12: Empty State Display for No Data

*For any* dashboard section with no data to display, the section should render an Empty_State component containing an icon, a descriptive message, and actionable guidance.

**Validates: Requirements 7.1, 7.2**

### Property 13: Empty State Excludes Loading Indicators

*For any* dashboard section that has completed data fetching and has no data, the Empty_State should be displayed without any loading indicators present.

**Validates: Requirements 7.6**

### Property 14: Clear All Filters Availability

*For any* filter state where at least one filter differs from the default values, the System should display and enable a "Clear All Filters" action.

**Validates: Requirements 8.3**

### Property 15: Loading State Disables Filter Controls

*For any* active loading state (data being fetched), all filter controls in the Filter_Panel should be disabled to prevent conflicting requests.

**Validates: Requirements 8.4**

### Property 16: Completion State Enables Controls

*For any* filter application that completes (successfully or with error), loading indicators should be removed and all filter controls should be re-enabled.

**Validates: Requirements 8.5**

### Property 17: Mobile Feature Parity

*For any* filter control or functionality available on desktop viewport (width >= 768px), the same functionality should be available on mobile viewport (width < 768px), though the UI presentation may differ.

**Validates: Requirements 9.3**

### Property 18: Section-Specific Filter Isolation

*For any* section-specific filter change (e.g., ABC filter within Curva ABC section), only that specific section should be affected, and global filter state should remain unchanged.

**Validates: Requirements 10.5**

### Property 19: Filter Conflict Resolution

*For any* combination of global and section-specific filters that conflict (e.g., global ABC=A, section ABC=B), the more specific (section-level) filter should take precedence for that section.

**Validates: Requirements 10.2**

### Property 20: Combined Filter Application

*For any* section with both global and section-specific filters active, the section should apply both filters in combination (logical AND), showing only data that satisfies all filter criteria.

**Validates: Requirements 10.1**

### Property 21: Selective Section Re-rendering

*For any* filter change, only sections that depend on the changed filter (based on their filterDependencies configuration) should re-render; unaffected sections should not re-render.

**Validates: Requirements 11.2**

### Property 22: ARIA Labels for Filter Controls

*For any* interactive filter control in the Filter_Panel, the control should have appropriate ARIA labels (aria-label, aria-labelledby, or aria-describedby) for screen reader accessibility.

**Validates: Requirements 12.2**

### Property 23: Screen Reader Announcements for Filter Changes

*For any* filter change that updates dashboard data, the System should update ARIA live regions to announce the change to screen readers.

**Validates: Requirements 12.3**

### Property 24: Visible Focus Indicators

*For any* focusable element in the Filter_Panel, when that element receives keyboard focus, a visible focus indicator (outline, border, or background change) should be displayed.

**Validates: Requirements 12.4**

## Error Handling

### Filter Validation Errors

**Date Range Validation**:
- **Error**: End date before start date
- **Handling**: Display inline error message, prevent filter application, maintain previous valid state
- **User Feedback**: "End date must be after start date"

**Date Format Errors**:
- **Error**: Invalid date string or malformed input
- **Handling**: Display inline error message, prevent filter application, highlight invalid field
- **User Feedback**: "Please enter a valid date in MM/DD/YYYY format"

**Date Range Limits**:
- **Error**: Date outside available data range
- **Handling**: Display warning message, allow filter but show empty states in sections
- **User Feedback**: "Data may not be available for dates outside {minDate} - {maxDate}"

### Session Storage Errors

**Storage Quota Exceeded**:
- **Error**: Session storage full
- **Handling**: Log error, continue without persistence, notify user
- **User Feedback**: "Unable to save filter preferences. Your selections will not persist after page refresh."

**Invalid Stored Data**:
- **Error**: Corrupted or invalid data in session storage
- **Handling**: Clear invalid data, fall back to default filter state, log error
- **User Feedback**: None (silent recovery)

**Schema Version Mismatch**:
- **Error**: Stored data from older schema version
- **Handling**: Attempt migration, fall back to defaults if migration fails
- **User Feedback**: None (silent recovery)

### Data Fetching Errors

**Network Error**:
- **Error**: Failed to fetch dashboard data
- **Handling**: Display error state in affected sections, provide retry action
- **User Feedback**: "Unable to load data. Please check your connection and try again."

**Backend Error (5xx)**:
- **Error**: Server error during data fetch
- **Handling**: Display error state, log error details, provide retry action
- **User Feedback**: "A server error occurred. Please try again or contact support if the problem persists."

**Timeout Error**:
- **Error**: Request timeout
- **Handling**: Cancel request, display timeout message, provide retry action
- **User Feedback**: "Request timed out. Please try again."

### Component Errors

**React Error Boundary**:
- **Error**: Unhandled error in component rendering
- **Handling**: Catch error in boundary, display fallback UI, log error
- **User Feedback**: "Something went wrong. Please refresh the page."

**Filter Context Missing**:
- **Error**: Component tries to use filter context outside provider
- **Handling**: Throw descriptive error in development, log error in production
- **User Feedback**: Development only - "useFilterContext must be used within FilterProvider"

## Testing Strategy

### Dual Testing Approach

This feature requires both **unit tests** and **property-based tests** for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, component integration, and error conditions
- **Property tests**: Verify universal properties across all inputs using randomized test data

### Property-Based Testing Configuration

**Library Selection**: 
- **fast-check** for TypeScript/React (recommended for this project)
- Minimum 100 iterations per property test
- Each property test must reference its design document property

**Tag Format**: 
```typescript
// Feature: dashboard-ux-improvements, Property 1: Date Range Filter Updates All Time-Dependent Sections
```

### Unit Testing Focus Areas

**Component Structure Tests**:
- GlobalFilterPanel renders all required filter controls
- Filter controls are in correct DOM order
- KPI section positioned immediately after Filter_Panel
- Financial sections grouped together
- Product sections grouped together

**Interaction Tests**:
- Date picker opens on click
- Preset buttons trigger date range updates
- View mode toggle switches between modes
- ABC class buttons update filter state
- Clear All button resets filters to defaults

**Edge Cases**:
- Empty date input handling
- Leap year date handling
- Timezone edge cases
- Very long date ranges (> 1 year)
- Rapid filter changes (debouncing)

**Error Conditions**:
- Network failure during data fetch
- Invalid session storage data
- Missing required props
- Null/undefined data handling

**Responsive Behavior**:
- Mobile layout at 767px width
- Tablet layout at 768-1023px width
- Desktop layout at 1024px+ width
- Touch target sizes on mobile (minimum 44x44px)

**Accessibility Tests**:
- All controls have ARIA labels
- Keyboard navigation works (Tab, Enter, Arrow keys)
- Focus indicators visible
- Screen reader announcements present
- Color contrast meets WCAG 2.1 AA (4.5:1 for text)

### Property-Based Testing Focus Areas

**Property 1: Date Range Filter Updates**
- Generate random valid date ranges
- Verify all time-dependent sections receive correct dates
- Check that non-time-dependent sections are unaffected

**Property 2: ABC Classification Filter**
- Generate random ABC class selections
- Verify only product sections are filtered
- Check that all displayed products match selected class

**Property 3: Quick Preset Selection**
- Generate random preset selections
- Verify date range updates match preset calculations
- Check that preset highlighting updates correctly

**Property 4: Active Filters Display**
- Generate random filter combinations
- Verify display shows all active filters
- Check that display updates on any filter change

**Property 5: Filter Changes Trigger Loading**
- Generate random filter changes
- Verify loading indicators appear on affected sections
- Check that indicators disappear after data loads

**Property 6: Date Range Validation**
- Generate random date pairs (including invalid ones)
- Verify validation rejects end < start
- Check that error messages appear for invalid ranges

**Property 10: Filter State Persistence Round-Trip**
- Generate random filter states
- Save to session storage and restore
- Verify restored state equals original state

**Property 11: Restored Filter State Validation**
- Generate random stored states (including invalid ones)
- Attempt to restore each state
- Verify validation catches invalid states and falls back to defaults

**Property 12: Empty State Display**
- Generate sections with empty data
- Verify Empty_State component renders
- Check that required elements (icon, message, guidance) are present

**Property 21: Selective Section Re-rendering**
- Generate random filter changes
- Track which sections re-render
- Verify only sections with matching filterDependencies re-render

**Property 22: ARIA Labels**
- Generate list of all filter controls
- Verify each has appropriate ARIA attributes
- Check that labels are descriptive and unique

### Integration Testing

**Filter-to-Section Data Flow**:
- Apply filters and verify correct API calls
- Check that sections receive filtered data
- Verify loading states during transitions

**Multi-Filter Scenarios**:
- Apply date range + ABC class + view mode
- Verify all filters work together correctly
- Check that clearing filters resets all sections

**Session Persistence Flow**:
- Apply filters, refresh page, verify restoration
- Apply filters, close tab, reopen, verify cleared
- Apply filters, navigate away, return, verify persistence

### Performance Testing

**Render Performance**:
- Measure time to first render
- Measure time to interactive
- Verify filter application < 500ms

**Re-render Optimization**:
- Count re-renders on filter change
- Verify memoization prevents unnecessary re-renders
- Check that debouncing reduces update frequency

**Memory Usage**:
- Monitor memory during extended use
- Verify no memory leaks on filter changes
- Check that old data is garbage collected

### Test Coverage Goals

- **Unit Test Coverage**: Minimum 80% code coverage
- **Property Test Coverage**: All 24 correctness properties implemented
- **Integration Test Coverage**: All critical user flows
- **Accessibility Test Coverage**: All WCAG 2.1 AA criteria

### Testing Tools

- **Jest**: Unit test runner
- **React Testing Library**: Component testing
- **fast-check**: Property-based testing
- **jest-axe**: Accessibility testing
- **MSW (Mock Service Worker)**: API mocking
- **@testing-library/user-event**: User interaction simulation

