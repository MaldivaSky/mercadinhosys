import React, { useState } from 'react';
import DeliveryDashboard from './DeliveryDashboard';
import DeliveryList from './DeliveryList';
import DriverManagement from './DriverManagement';
import { Truck, Home, Map } from 'lucide-react';

const DeliveryPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'dashboard' | 'list' | 'drivers'>('dashboard');

    return (
        <div className="min-h-screen bg-[#F8FAFC] dark:bg-gray-950">
            {/* Top Navigation */}
            <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-30">
                <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-8">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                                <Truck className="w-5 h-5 text-white" />
                            </div>
                            <span className="font-black text-xl tracking-tighter text-gray-900 dark:text-white">LOGS<span className="text-blue-600">PRO</span></span>
                        </div>

                        <nav className="hidden md:flex items-center gap-1">
                            {[
                                { id: 'dashboard', label: 'Overview', icon: Home },
                                { id: 'list', label: 'Monitoramento', icon: Map },
                                { id: 'drivers', label: 'Frota/Equipe', icon: Truck },
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${activeTab === tab.id
                                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                                        : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800'
                                        }`}
                                >
                                    <tab.icon className="w-4 h-4" />
                                    {tab.label}
                                </button>
                            ))}
                        </nav>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-900/20 rounded-full border border-green-100 dark:border-green-900/30">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                            <span className="text-[10px] font-black text-green-700 dark:text-green-400 uppercase tracking-widest">Servidor Online</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <main className="transition-all duration-500">
                {activeTab === 'dashboard' && <DeliveryDashboard />}
                {activeTab === 'list' && <DeliveryList />}
                {activeTab === 'drivers' && <DriverManagement />}
            </main>
        </div>
    );
};

export default DeliveryPage;
