/**
 * FilterContext - Global filter state for dashboard reactive filtering
 * 
 * Provides centralized filter state management across dashboard sections.
 * Implements localStorage persistence for filter state across navigation.
 * 
 * Requirements: AC 3.5
 * Task: 3.3.2 Create filter state context
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface DashboardFilters {
  startDate?: Date;
  endDate?: Date;
  categoryIds?: number[];
  segment?: string;
}

interface FilterContextType {
  filters: DashboardFilters;
  setFilters: (filters: DashboardFilters) => void;
  resetFilters: () => void;
  updateFilter: (key: keyof DashboardFilters, value: any) => void;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

const DEFAULT_FILTERS: DashboardFilters = {
  startDate: undefined,
  endDate: undefined,
  categoryIds: undefined,
  segment: undefined,
};

const STORAGE_KEY = 'dashboard_filters';

/**
 * FilterProvider Component
 * 
 * AC 3.3.1: Implement localStorage persistence
 * AC 3.3.2: Create filter state context
 * AC 3.5: Filter state persists when navigating between dashboard sections
 */
export const FilterProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [filters, setFiltersState] = useState<DashboardFilters>(DEFAULT_FILTERS);

  // Load filters from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Convert ISO strings back to Date objects
        const restored: DashboardFilters = {
          ...parsed,
          startDate: parsed.startDate ? new Date(parsed.startDate) : undefined,
          endDate: parsed.endDate ? new Date(parsed.endDate) : undefined,
        };
        setFiltersState(restored);
      }
    } catch (error) {
      console.warn('Failed to load filters from localStorage:', error);
    }
  }, []);

  // Persist filters to localStorage whenever they change
  const setFilters = (newFilters: DashboardFilters) => {
    try {
      // Convert Date objects to ISO strings for storage
      const toStore = {
        ...newFilters,
        startDate: newFilters.startDate?.toISOString(),
        endDate: newFilters.endDate?.toISOString(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
      setFiltersState(newFilters);
    } catch (error) {
      console.error('Failed to persist filters to localStorage:', error);
      // Still update state even if persistence fails
      setFiltersState(newFilters);
    }
  };

  const resetFilters = () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
      setFiltersState(DEFAULT_FILTERS);
    } catch (error) {
      console.error('Failed to reset filters:', error);
      setFiltersState(DEFAULT_FILTERS);
    }
  };

  const updateFilter = (key: keyof DashboardFilters, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
  };

  return (
    <FilterContext.Provider value={{ filters, setFilters, resetFilters, updateFilter }}>
      {children}
    </FilterContext.Provider>
  );
};

/**
 * useFilters Hook
 * 
 * AC 3.5: Filter state persists when navigating between dashboard sections
 */
export const useFilters = (): FilterContextType => {
  const context = useContext(FilterContext);
  if (context === undefined) {
    throw new Error('useFilters must be used within FilterProvider');
  }
  return context;
};
