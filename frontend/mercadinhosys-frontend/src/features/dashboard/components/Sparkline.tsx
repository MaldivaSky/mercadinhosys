import React from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface SparklineProps {
  data: { value: number }[];
  color?: string;
  height?: number;
}

export const Sparkline: React.FC<SparklineProps> = ({ 
  data, 
  color = "#4f46e5", // indigo-600 default
  height = 40 
}) => {
  if (!data || data.length === 0) return null;

  return (
    <div style={{ height, width: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
