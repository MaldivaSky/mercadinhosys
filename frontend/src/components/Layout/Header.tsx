import React from 'react';
import { ShoppingCart, Bell, User, Menu, Search } from 'lucide-react';

interface HeaderProps {
    onMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
    return (
        <header className="bg-azul-principal text-white shadow-lg">
            <div className="container mx-auto px-4 py-3">
                <div className="flex items-center justify-between">
                    {/* Logo e Menu Mobile */}
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={onMenuClick}
                            className="md:hidden p-2 hover:bg-blue-700 rounded-lg"
                            aria-label="Abrir menu"
                        >
                            <Menu className="h-6 w-6" />
                        </button>

                        <div className="flex items-center space-x-3">
                            <div className="bg-white text-azul-principal p-2 rounded-lg shadow">
                                <ShoppingCart className="h-6 w-6" />
                            </div>
                            <div>
                                <h1 className="text-xl md:text-2xl font-bold">MercadoSys</h1>
                                <p className="text-blue-200 text-sm hidden md:block">Sistema de Gestão para Mercadinhos</p>
                            </div>
                        </div>
                    </div>

                    {/* Barra de Busca (Desktop) */}
                    <div className="hidden md:flex flex-1 max-w-2xl mx-8">
                        <div className="relative w-full">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                            <input
                                type="text"
                                placeholder="Buscar produtos, clientes, vendas..."
                                className="w-full pl-10 pr-4 py-2 rounded-lg text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    {/* Ícones do lado direito */}
                    <div className="flex items-center space-x-4">
                        {/* Notificações */}
                        <button className="relative p-2 hover:bg-blue-700 rounded-lg">
                            <Bell className="h-6 w-6" />
                            <span className="absolute -top-1 -right-1 bg-laranja-alerta text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                                3
                            </span>
                        </button>

                        {/* Usuário */}
                        <div className="hidden md:flex items-center space-x-3">
                            <div className="text-right">
                                <p className="font-semibold">Rafael Silva</p>
                                <p className="text-sm text-blue-200">Gerente</p>
                            </div>
                            <div className="h-10 w-10 bg-white text-azul-principal rounded-full flex items-center justify-center font-bold shadow">
                                RS
                            </div>
                        </div>

                        {/* Ícone de usuário mobile */}
                        <button className="md:hidden p-2 hover:bg-blue-700 rounded-lg">
                            <User className="h-6 w-6" />
                        </button>
                    </div>
                </div>

                {/* Barra de Busca Mobile */}
                <div className="mt-3 md:hidden">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                        <input
                            type="text"
                            placeholder="Buscar..."
                            className="w-full pl-10 pr-4 py-2 rounded-lg text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;