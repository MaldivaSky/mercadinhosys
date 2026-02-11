import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    Home,
    Package,
    Users,
    ShoppingCart,
    BarChart3,
    Settings,
    CreditCard,
    UserCog,
    FileText,
    Truck,
    Clock,
    Briefcase,
} from 'lucide-react';

const menuItems = [
    { to: '/dashboard', icon: Home, label: 'Dashboard' },
    { to: '/pdv', icon: ShoppingCart, label: 'PDV' },
    { to: '/products', icon: Package, label: 'Produtos' },
    { to: '/suppliers', icon: Truck, label: 'Fornecedores' },
    { to: '/customers', icon: Users, label: 'Clientes' },
    { to: '/sales', icon: CreditCard, label: 'Vendas' },
    { to: '/expenses', icon: FileText, label: 'Despesas' },
    { to: '/employees', icon: UserCog, label: 'Funcionários' },
    { to: '/rh', icon: Briefcase, label: 'RH & Ponto' },
    { to: '/ponto', icon: Clock, label: 'Controle de Ponto' },
    { to: '/reports', icon: BarChart3, label: 'Relatórios' },
    { to: '/settings', icon: Settings, label: 'Configurações' },
];

const Sidebar: React.FC = () => {
    return (
        <aside className="hidden md:block w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 min-h-[calc(100vh-4rem)]">
            <nav className="p-4">
                <ul className="space-y-2">
                    {menuItems.map((item) => (
                        <li key={item.to}>
                            <NavLink
                                to={item.to}
                                className={({ isActive }) =>
                                    `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive
                                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                                    }`
                                }
                            >
                                <item.icon className="w-5 h-5" />
                                <span className="font-medium">{item.label}</span>
                            </NavLink>
                        </li>
                    ))}
                </ul>
            </nav>
        </aside>
    );
};

export default Sidebar;
