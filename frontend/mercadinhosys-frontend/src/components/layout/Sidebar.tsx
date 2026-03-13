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
    ChevronLeft,
    ChevronRight,
    DollarSign,
    Building2,
    Target,
    Activity
} from 'lucide-react';
import { authService } from '../../features/auth/authService';

const menuItems = [
    { to: '/dashboard', icon: Home, label: 'Dashboard' },
    { to: '/pdv', icon: ShoppingCart, label: 'PDV' },
    { to: '/pdv?manage=true', icon: DollarSign, label: 'Gerenciar Caixa' },
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
    { to: '/estabelecimentos', icon: Building2, label: 'Estabelecimentos' },
    { to: '/monitor', icon: Activity, label: 'Monitor Sistema' },
    { to: '/leads', icon: Target, label: 'Leads SaaS' },
];

interface SidebarProps {
    isCollapsed: boolean;
    setIsCollapsed: (collapsed: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, setIsCollapsed }) => {
    return (
        <aside className={`hidden md:block bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 h-full overflow-y-auto custom-scrollbar transition-all duration-300 ${isCollapsed ? 'w-20' : 'w-64'}`}>
            <div className="p-4 flex justify-end">
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="p-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    title={isCollapsed ? "Expandir menu" : "Recolher menu"}
                >
                    {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
                </button>
            </div>
            <nav className="px-4 pb-4">
                <ul className="space-y-2">
                    {menuItems.filter(item => {
                        const user = authService.getCurrentUser();
                        const role = user?.role?.toLowerCase();
                        const isSuperAdmin = user?.is_super_admin || false;

                        // ====================================================================
                        // BARRARIA DE SEGURANÇA SaaS: Apenas Super Admins podem ver
                        // rotas de administração global do sistema (Leads, Estabelecimentos, Monitor)
                        // Tenant Admins (role='admin') NÃO devem ver estas opções
                        // ====================================================================
                        if (['/estabelecimentos', '/leads', '/monitor'].includes(item.to) && !isSuperAdmin) {
                            return false;
                        }

                        // Se for caixa ou estoquista, aplicamos o filtro seletivo a áreas estritas
                        if (role === 'caixa') {
                            const permitidos = ['/dashboard', '/pdv', '/pdv?manage=true', '/customers', '/ponto', '/settings'];
                            return permitidos.includes(item.to);
                        }

                        if (role === 'estoquista') {
                            const permitidos = ['/dashboard', '/pdv', '/pdv?manage=true', '/products', '/suppliers', '/customers', '/ponto', '/settings'];
                            return permitidos.includes(item.to);
                        }

                        // Funcionário genérico?
                        if (role === 'funcionario') {
                            const bloqueados = ['/sales', '/expenses', '/employees', '/rh', '/ponto-relatorios', '/ponto-diagnostico', '/reports'];
                            return !bloqueados.includes(item.to);
                        }

                        return true;
                    }).map((item) => (
                        <li key={item.to}>
                            <NavLink
                                to={item.to}
                                className={({ isActive }) =>
                                    `flex items-center rounded-lg transition-colors ${isCollapsed ? 'justify-center px-1 py-3' : 'px-4 py-3 space-x-3'} ${isActive
                                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                                    }`
                                }
                            >
                                <item.icon className={`w-5 h-5 flex-shrink-0`} />
                                {!isCollapsed && <span className="font-medium whitespace-nowrap overflow-hidden">{item.label}</span>}
                            </NavLink>
                        </li>
                    ))}
                </ul>
            </nav>
        </aside>
    );
};

export default Sidebar;
