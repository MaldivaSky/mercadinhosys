// src/features/pdv/components/PDVSkeleton.tsx
import React from 'react';

const PDVSkeleton: React.FC = () => {
    return (
        <div className="animate-pulse space-y-4 p-4 lg:p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
            <div className="h-16 bg-white dark:bg-gray-800 rounded-xl mb-6 shadow-sm"></div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div className="lg:col-span-8 space-y-4">
                    <div className="h-32 bg-white dark:bg-gray-800 rounded-2xl shadow-sm"></div>
                    <div className="h-[400px] bg-white dark:bg-gray-800 rounded-2xl shadow-sm"></div>
                </div>

                <div className="lg:col-span-4 space-y-6">
                    <div className="h-40 bg-white dark:bg-gray-800 rounded-2xl shadow-sm"></div>
                    <div className="h-80 bg-white dark:bg-gray-800 rounded-2xl shadow-sm"></div>
                    <div className="h-24 bg-white dark:bg-gray-800 rounded-2xl shadow-sm"></div>
                </div>
            </div>
        </div>
    );
};

export default PDVSkeleton;
