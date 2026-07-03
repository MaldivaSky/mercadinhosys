/**
 * CategoryFilter Component
 * 
 * Provides multi-select dropdown for product category filtering.
 * Fetches categories from API and implements reactive filtering.
 * 
 * Requirements: AC 3.2
 * Task: 3.2.2 Create CategoryFilter component
 */

import React, { useState, useEffect } from 'react';
import './CategoryFilter.css';

interface Category {
  id: number;
  name: string;
}

interface CategoryFilterProps {
  onCategoryChange: (categoryIds: number[] | undefined) => void;
  selectedCategoryIds?: number[];
  isLoading?: boolean;
}

export const CategoryFilter: React.FC<CategoryFilterProps> = ({
  onCategoryChange,
  selectedCategoryIds = [],
  isLoading = false,
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch categories from API
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        // Assuming there's a categories API endpoint
        const response = await fetch('/api/categories', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch categories');
        }

        const data = await response.json();
        setCategories(data.data || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching categories:', err);
        setError('Failed to load categories');
        // Provide some default categories if fetch fails
        setCategories([
          { id: 1, name: 'Grocery' },
          { id: 2, name: 'Beverages' },
          { id: 3, name: 'Household' },
          { id: 4, name: 'Personal Care' },
          { id: 5, name: 'Electronics' },
        ]);
      }
    };

    fetchCategories();
  }, []);

  const handleCategoryChange = (categoryId: number) => {
    const newSelectedIds = selectedCategoryIds.includes(categoryId)
      ? selectedCategoryIds.filter((id) => id !== categoryId)
      : [...selectedCategoryIds, categoryId];

    // Convert empty array to undefined (meaning all categories)
    onCategoryChange(newSelectedIds.length > 0 ? newSelectedIds : undefined);
  };

  const handleSelectAll = () => {
    const allIds = categories.map((c) => c.id);
    onCategoryChange(allIds.length > 0 ? allIds : undefined);
  };

  const handleClearAll = () => {
    onCategoryChange(undefined);
  };

  const selectedCount = selectedCategoryIds.length;
  const totalCount = categories.length;
  const isAllSelected = selectedCount === totalCount && totalCount > 0;

  return (
    <div className="category-filter">
      <div className="filter-header">
        <label>Categories</label>
        <button
          className="toggle-button"
          onClick={() => setShowDropdown(!showDropdown)}
          disabled={isLoading}
        >
          {showDropdown ? '▲' : '▼'}
        </button>
      </div>

      {showDropdown && (
        <div className="filter-dropdown">
          {isLoading && <div className="loading">Loading categories...</div>}

          {error && <div className="error">{error}</div>}

          {!isLoading && categories.length > 0 && (
            <>
              <div className="dropdown-controls">
                <button className="control-btn" onClick={handleSelectAll}>
                  Select All
                </button>
                <button className="control-btn" onClick={handleClearAll}>
                  Clear
                </button>
              </div>

              <div className="category-list">
                {categories.map((category) => (
                  <label key={category.id} className="category-item">
                    <input
                      type="checkbox"
                      checked={selectedCategoryIds.includes(category.id)}
                      onChange={() => handleCategoryChange(category.id)}
                    />
                    <span>{category.name}</span>
                  </label>
                ))}
              </div>
            </>
          )}

          {!isLoading && categories.length === 0 && (
            <div className="empty">No categories available</div>
          )}
        </div>
      )}

      {selectedCount > 0 && (
        <div className="selected-summary">
          {isAllSelected ? (
            'All categories'
          ) : (
            <>
              {selectedCount} of {totalCount} selected
            </>
          )}
        </div>
      )}
    </div>
  );
};
