import React from 'react';
import { Card, CardContent } from '../../../components/ui/card';
import { Sparkline } from './Sparkline';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { Skeleton } from '../../../components/ui/skeleton';

interface StatCardProps {
  title: string;
  value: string | number;
  trend?: number;
  trendLabel?: string;
  sparklineData?: { value: number }[];
  icon?: React.ElementType;
  loading?: boolean;
  color?: 'indigo' | 'emerald' | 'rose' | 'blue' | 'purple';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  trend,
  trendLabel,
  sparklineData,
  icon: Icon,
  loading = false,
  color = 'indigo'
}) => {
  if (loading) {
    return (
      <Card className="rounded-2xl border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
        <CardContent className="p-6">
          <div className="flex justify-between items-start mb-4">
            <Skeleton className="h-4 w-24 bg-gray-200 dark:bg-slate-800" />
            <Skeleton className="h-8 w-8 rounded-lg bg-gray-200 dark:bg-slate-800" />
          </div>
          <Skeleton className="h-8 w-32 mb-2 bg-gray-200 dark:bg-slate-800" />
          <Skeleton className="h-4 w-16 bg-gray-200 dark:bg-slate-800" />
          <div className="mt-4 h-10">
            <Skeleton className="h-full w-full bg-gray-100 dark:bg-slate-800/50" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Define colors based on prop
  const colors = {
    indigo: { text: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-50 dark:bg-indigo-900/20', stroke: '#4f46e5' },
    emerald: { text: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/20', stroke: '#10b981' },
    rose: { text: 'text-rose-600 dark:text-rose-400', bg: 'bg-rose-50 dark:bg-rose-900/20', stroke: '#f43f5e' },
    blue: { text: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20', stroke: '#3b82f6' },
    purple: { text: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-50 dark:bg-purple-900/20', stroke: '#8b5cf6' },
  };

  const activeColor = colors[color];
  const isPositive = trend && trend > 0;
  const isNegative = trend && trend < 0;
  const isNeutral = !trend || trend === 0;

  return (
    <Card className="rounded-2xl border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
      <CardContent className="p-6 relative">
        <div className="flex justify-between items-start z-10 relative">
          <div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{value}</h3>
          </div>
          {Icon && (
            <div className={`p-2 rounded-lg ${activeColor.bg}`}>
              <Icon className={`w-5 h-5 ${activeColor.text}`} />
            </div>
          )}
        </div>

        {trend !== undefined && (
          <div className="flex items-center mt-2 gap-2">
            <div className={`flex items-center text-xs font-semibold px-2 py-0.5 rounded-full
              ${isPositive ? 'text-emerald-700 bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400' : 
                isNegative ? 'text-rose-700 bg-rose-100 dark:bg-rose-900/30 dark:text-rose-400' : 
                'text-gray-600 bg-gray-100 dark:bg-slate-800 dark:text-gray-400'}`}>
              {isPositive ? <ArrowUpRight className="w-3 h-3 mr-1" /> : 
               isNegative ? <ArrowDownRight className="w-3 h-3 mr-1" /> : 
               <Minus className="w-3 h-3 mr-1" />}
              {Math.abs(trend)}%
            </div>
            {trendLabel && (
              <span className="text-xs text-gray-400 dark:text-gray-500">{trendLabel}</span>
            )}
          </div>
        )}

        <div className="mt-4 -mx-2 opacity-50 hover:opacity-100 transition-opacity">
          {sparklineData && <Sparkline data={sparklineData} color={activeColor.stroke} height={40} />}
        </div>
      </CardContent>
    </Card>
  );
};
