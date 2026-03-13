/**
 * MercadinhoSys - Componentes Skeleton
 * Loading states elegantes para melhor UX
 */

import React from 'react';

interface SkeletonProps {
  className?: string;
  height?: string | number;
  width?: string | number;
  variant?: 'text' | 'circular' | 'rectangular';
  animation?: 'pulse' | 'wave' | 'none';
}

/**
 * Componente Skeleton base
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  height = '1em',
  width = '100%',
  variant = 'text',
  animation = 'pulse'
}) => {
  const getSkeletonClass = () => {
    const base = 'skeleton';
    const classes = [base];
    
    classes.push(`${base}--${variant}`);
    if (animation !== 'none') {
      classes.push(`${base}--${animation}`);
    }
    
    return classes.join(' ');
  };

  const style = {
    height: typeof height === 'number' ? `${height}px` : height,
    width: typeof width === 'number' ? `${width}px` : width,
  };

  return (
    <div
      className={`${getSkeletonClass()} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
};

/**
 * Skeleton para cards
 */
export const CardSkeleton: React.FC<{ showAvatar?: boolean }> = ({ 
  showAvatar = false 
}) => (
  <div className="skeleton-card">
    {showAvatar && (
      <Skeleton 
        variant="circular" 
        width={40} 
        height={40} 
        className="skeleton-card__avatar" 
      />
    )}
    <div className="skeleton-card__content">
      <Skeleton height={20} width="60%" className="skeleton-card__title" />
      <Skeleton height={16} width="40%" className="skeleton-card__subtitle" />
      <Skeleton height={14} width="80%" className="skeleton-card__text" />
      <Skeleton height={14} width="70%" className="skeleton-card__text" />
    </div>
  </div>
);

/**
 * Skeleton para tabelas
 */
export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4
}) => (
  <div className="skeleton-table">
    <div className="skeleton-table__header">
      {Array.from({ length: columns }).map((_, index) => (
        <Skeleton 
          key={`header-${index}`}
          height={20} 
          width="100%" 
          className="skeleton-table__header-cell" 
        />
      ))}
    </div>
    <div className="skeleton-table__body">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={`row-${rowIndex}`} className="skeleton-table__row">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton 
              key={`cell-${rowIndex}-${colIndex}`}
              height={16} 
              width="100%" 
              className="skeleton-table__cell" 
            />
          ))}
        </div>
      ))}
    </div>
  </div>
);

/**
 * Skeleton para gráficos
 */
export const ChartSkeleton: React.FC<{ type?: 'bar' | 'line' | 'doughnut' }> = ({
  type = 'bar'
}) => {
  const getSkeletonContent = () => {
    switch (type) {
      case 'doughnut':
        return (
          <div className="skeleton-chart--doughnut">
            <Skeleton variant="circular" width={200} height={200} />
            <div className="skeleton-chart--doughnut__legend">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="skeleton-chart--doughnut__legend-item">
                  <Skeleton width={12} height={12} variant="rectangular" />
                  <Skeleton width={60} height={14} />
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'line':
        return (
          <div className="skeleton-chart--line">
            <div className="skeleton-chart--line__header">
              <Skeleton width={120} height={20} />
              <Skeleton width={80} height={16} />
            </div>
            <div className="skeleton-chart--line__content">
              {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton 
                  key={index} 
                  height={100} 
                  width="100%" 
                  variant="rectangular" 
                />
              ))}
            </div>
          </div>
        );
      
      case 'bar':
      default:
        return (
          <div className="skeleton-chart--bar">
            <div className="skeleton-chart--bar__header">
              <Skeleton width={120} height={20} />
              <Skeleton width={80} height={16} />
            </div>
            <div className="skeleton-chart--bar__content">
              {Array.from({ length: 6 }).map((_, index) => (
                <div key={index} className="skeleton-chart--bar__item">
                  <Skeleton 
                    height={Math.random() * 100 + 50} 
                    width="100%" 
                    variant="rectangular" 
                  />
                </div>
              ))}
            </div>
          </div>
        );
    }
  };

  return (
    <div className="skeleton-chart">
      {getSkeletonContent()}
    </div>
  );
};

/**
 * Skeleton para listas de produtos/clientes
 */
export const ListItemSkeleton: React.FC<{ showAvatar?: boolean }> = ({
  showAvatar = false
}) => (
  <div className="skeleton-list-item">
    {showAvatar && (
      <Skeleton 
        variant="rectangular" 
        width={50} 
        height={50} 
        className="skeleton-list-item__avatar" 
      />
    )}
    <div className="skeleton-list-item__content">
      <Skeleton height={18} width="70%" className="skeleton-list-item__title" />
      <Skeleton height={14} width="50%" className="skeleton-list-item__subtitle" />
      <div className="skeleton-list-item__meta">
        <Skeleton height={12} width={30} />
        <Skeleton height={12} width={40} />
        <Skeleton height={12} width={60} />
      </div>
    </div>
    <div className="skeleton-list-item__actions">
      <Skeleton width={32} height={32} variant="rectangular" />
      <Skeleton width={32} height={32} variant="rectangular" />
    </div>
  </div>
);

/**
 * Skeleton para dashboard cards
 */
export const DashboardCardSkeleton: React.FC<{ showChart?: boolean }> = ({
  showChart = false
}) => (
  <div className="skeleton-dashboard-card">
    <div className="skeleton-dashboard-card__header">
      <Skeleton height={16} width="60%" />
      <Skeleton width={24} height={24} variant="circular" />
    </div>
    <div className="skeleton-dashboard-card__content">
      <Skeleton height={32} width="40%" className="skeleton-dashboard-card__value" />
      <Skeleton height={12} width="30%" className="skeleton-dashboard-card__label" />
    </div>
    {showChart && (
      <div className="skeleton-dashboard-card__chart">
        <Skeleton height={60} width="100%" variant="rectangular" />
      </div>
    )}
  </div>
);

/**
 * Wrapper para conteúdo com loading state
 */
export const SkeletonWrapper: React.FC<{
  loading: boolean;
  children: React.ReactNode;
  skeleton: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ loading, children, skeleton, fallback }) => {
  if (loading) {
    return <>{skeleton}</>;
  }
  
  if (fallback && !children) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
};

export default {
  Skeleton,
  CardSkeleton,
  TableSkeleton,
  ChartSkeleton,
  ListItemSkeleton,
  DashboardCardSkeleton,
  SkeletonWrapper
};
