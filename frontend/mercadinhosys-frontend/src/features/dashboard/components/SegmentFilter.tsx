/**
 * SegmentFilter Component
 * 
 * Provides RFM customer segment filtering with preset segments.
 * Implements reactive filtering for customer analytics.
 * 
 * Requirements: AC 3.3
 * Task: 3.2.3 Create SegmentFilter component
 */

import React, { useState } from 'react';
import './SegmentFilter.css';

interface Segment {
  id: string;
  label: string;
  description: string;
  color: string;
}

interface SegmentFilterProps {
  onSegmentChange: (segment: string | undefined) => void;
  selectedSegment?: string;
}

const RFM_SEGMENTS: Segment[] = [
  {
    id: 'all',
    label: 'All Customers',
    description: 'View all customer segments',
    color: '#666',
  },
  {
    id: 'champions',
    label: 'Champions',
    description: 'High frequency, high value, recent',
    color: '#4CAF50',
  },
  {
    id: 'loyal',
    label: 'Loyal',
    description: 'High frequency, high value',
    color: '#2196F3',
  },
  {
    id: 'potential',
    label: 'Potential',
    description: 'Medium frequency, medium value',
    color: '#FF9800',
  },
  {
    id: 'at_risk',
    label: 'At Risk',
    description: 'Used to buy frequently',
    color: '#FF5722',
  },
  {
    id: 'lost',
    label: 'Lost',
    description: 'Haven\'t purchased recently',
    color: '#9E9E9E',
  },
];

export const SegmentFilter: React.FC<SegmentFilterProps> = ({
  onSegmentChange,
  selectedSegment = 'all',
}) => {
  const [showSegments, setShowSegments] = useState(false);

  const handleSegmentSelect = (segmentId: string) => {
    onSegmentChange(segmentId === 'all' ? undefined : segmentId);
    setShowSegments(false);
  };

  const selectedSegmentData = RFM_SEGMENTS.find(
    (s) => s.id === (selectedSegment || 'all')
  );

  return (
    <div className="segment-filter">
      <div className="filter-header">
        <label>Customer Segment (RFM)</label>
        <button
          className="toggle-button"
          onClick={() => setShowSegments(!showSegments)}
        >
          {showSegments ? '▲' : '▼'}
        </button>
      </div>

      {showSegments && (
        <div className="segment-dropdown">
          {RFM_SEGMENTS.map((segment) => (
            <div
              key={segment.id}
              className={`segment-option ${
                (selectedSegment || 'all') === segment.id ? 'selected' : ''
              }`}
              onClick={() => handleSegmentSelect(segment.id)}
            >
              <div className="segment-indicator" style={{ color: segment.color }}>
                ●
              </div>
              <div className="segment-content">
                <div className="segment-label">{segment.label}</div>
                <div className="segment-description">{segment.description}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedSegmentData && (
        <div className="selected-segment">
          <span style={{ color: selectedSegmentData.color }}>●</span>
          {selectedSegmentData.label}
        </div>
      )}
    </div>
  );
};
