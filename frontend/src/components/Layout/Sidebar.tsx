import React from 'react';
import {
    LayoutDashboard,
    ShoppingCart,
    Package,
    Users,
    BarChart3,
    Bell,
    Settings,
    CreditCard,
    FileText,
    Calendar,
    X,
    LogOut
} from 'lucide-react';

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
    onNavigate: (page: 'dashboard' | 'pdv') => void; // Adicione esta linha
}

interface MenuItem {
    icon: React.ReactNode;
    label: string;
    active: boolean;
    page: 'dashboard' | 'pdv'; // Adicione esta linha
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, onNavigate }) => {
    const menuItems: MenuItem[] = [
        { icon: <LayoutDashboard className="h-5 w-5" />, label: 'Dashboard', active: true, page: 'dashboard' },
        { icon: <ShoppingCart className="h-5 w-5" />, label: 'Ponto de Venda', active: false, page: 'pdv' },
        { icon: <Package className="h-5 w-5" />, label: 'Estoque', active: false, page: 'dashboard' },
        { icon: <Users className="h-5 w-5" />, label: 'Clientes', active: false, page: 'dashboard' },
        { icon: <CreditCard className="h-5 w-5" />, label: 'Fornecedores', active: false, page: 'dashboard' },
        { icon: <BarChart3 className="h-5 w-5" />, label: 'Relatórios', active: false, page: 'dashboard' },
        { icon: <FileText className="h-5 w-5" />, label: 'Vendas', active: false, page: 'dashboard' },
        { icon: <Calendar className="h-5 w-5" />, label: 'Agenda', active: false, page: 'dashboard' },
        { icon: <Bell className="h-5 w-5" />, label: 'Alertas', active: false, page: 'dashboard' },
    ];

    const configItems = [
        { icon: <Settings className="h-5 w-5" />, label: 'Configurações' },
        { icon: <LogOut className="h-5 w-5" />, label: 'Sair' },
    ];

    return (
        <>
            {/* Overlay para mobile */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
                    onClick={onClose}
                />
            )}

            {/* Sidebar */}
            <aside className={`
        fixed md:relative top-0 left-0 h-full w-64 bg-white shadow-xl z-50
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        md:translate-x-0 md:block md:w-64
      `}>
                {/* Header da Sidebar */}
                <div className="p-4 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <div className="h-10 w-10 bg-azul-principal text-white rounded-lg flex items-center justify-center">
                                <ShoppingCart className="h-6 w-6" />
                            </div>
                            <div>
                                <h2 className="font-bold text-gray-800">MercadoSys</h2>
                                <p className="text-xs text-gray-500">Sistema completo</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="md:hidden p-2 hover:bg-gray-100 rounded-lg"
                        >
                            <X className="h-5 w-5 text-gray-500" />
                        </button>
                    </div>
                </div>

                {/* Navegação Principal */}
                <nav className="p-4">
                    <div className="mb-6">
                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                            Menu Principal
                        </h3>
                        <ul className="space-y-1">
                            {menuItems.map((item, index) => (
                                <li key={index}>
                                    <button
                                        onClick={() => onNavigate(item.page)}
                                        className={`
                      w-full text-left flex items-center space-x-3 p-3 rounded-lg
                      transition-colors duration-200
                      ${item.active
                                                ? 'bg-blue-50 text-azul-principal font-semibold'
                                                : 'text-gray-700 hover:bg-gray-100'
                                            }
                    `}
                                    >
                                        <div className={item.active ? 'text-azul-principal' : 'text-gray-500'}>
                                            {item.icon}
                                        </div>
                                        <span>{item.label}</span>
                                        {item.active && (
                                            <div className="ml-auto h-2 w-2 bg-azul-principal rounded-full" />
                                        )}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Menu de Configuração */}
                    <div>
                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                            Configurações
                        </h3>
                        <ul className="space-y-1">
                            {configItems.map((item, index) => (
                                <li key={index}>
                                    <button
                                        className="w-full text-left flex items-center space-x-3 p-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors duration-200"
                                    >
                                        <div className="text-gray-500">
                                            {item.icon}
                                        </div>
                                        <span>{item.label}</span>
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>
                </nav>

                {/* Status do Sistema */}
                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-700">Status</p>
                            <div className="flex items-center space-x-2">
                                <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                                <span className="text-xs text-green-600">Online</span>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-xs text-gray-500">v1.0.0</p>
                            <p className="text-xs text-gray-400">Beta</p>
                        </div>
                    </div>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;