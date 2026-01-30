import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    User, LogOut, Settings, Moon, Sun, ChevronDown, 
    Menu as MenuIcon, X 
} from 'lucide-react';
import { useConfig } from '../../contexts/ConfigContext';
import logo from '../../../logoprincipal.png';

const HeaderProfessional = () => {
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const navigate = useNavigate();
    const { config, updateConfig } = useConfig();

    const user = useMemo(() => {
        try {
            return JSON.parse(localStorage.getItem('user_data') || '{}');
        } catch {
            return {};
        }
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        window.dispatchEvent(new Event('auth-change'));
        navigate('/login');
    };

    const toggleTheme = async () => {
        if (config) {
            await updateConfig({ tema_escuro: !config.tema_escuro });
        }
    };

    const userInitial = user.nome ? user.nome[0].toUpperCase() : '?';
    
    // Usar logo do config ou fallback
    const getLogoUrl = () => {
        if (!config?.logo_url) return logo;
        
        // Se for base64 (preview), usar direto
        if (config.logo_url.startsWith('data:')) return config.logo_url;
        
        // Se for URL do servidor
        if (config.logo_url.startsWith('http')) return config.logo_url;
        
        // Se for caminho relativo
        return `http://localhost:5000${config.logo_url}`;
    };
    
    const logoUrl = getLogoUrl();

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-white dark:bg-gray-900 dark:border-gray-800 shadow-sm">
            <div className="container mx-auto px-4">
                <div className="flex h-16 items-center justify-between">
                    {/* Logo */}
                    <div className="flex items-center gap-3">
                        <img 
                            src={logoUrl} 
                            alt="Logo" 
                            className="h-10 w-auto rounded-lg object-contain"
                            onError={(e) => {
                                e.currentTarget.src = logo;
                            }}
                        />
                        <span className="hidden md:block text-xl font-bold text-gray-900 dark:text-white">
                            MercadinhoSys
                        </span>
                    </div>

                    {/* Desktop Actions */}
                    <div className="hidden md:flex items-center gap-3">
                        {/* Theme Toggle */}
                        <button
                            onClick={toggleTheme}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            title="Alternar tema"
                        >
                            {config?.tema_escuro ? (
                                <Sun className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                            ) : (
                                <Moon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                            )}
                        </button>

                        {/* User Menu */}
                        <div className="relative">
                            <button
                                onClick={() => setUserMenuOpen(!userMenuOpen)}
                                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            >
                                {user.foto_url ? (
                                    <img 
                                        src={user.foto_url} 
                                        alt={user.nome}
                                        className="w-8 h-8 rounded-full object-cover"
                                    />
                                ) : (
                                    <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-semibold">
                                        {userInitial}
                                    </div>
                                )}
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                                    {user.nome || 'Usuário'}
                                </span>
                                <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
                            </button>

                            {/* Dropdown Menu */}
                            {userMenuOpen && (
                                <>
                                    <div 
                                        className="fixed inset-0 z-40" 
                                        onClick={() => setUserMenuOpen(false)}
                                    />
                                    <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50">
                                        {/* User Info */}
                                        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                                                {user.nome || 'Usuário'}
                                            </p>
                                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                                {user.email || user.usuario || 'Sem email'}
                                            </p>
                                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                                {user.cargo || user.role || 'Cargo não definido'}
                                            </p>
                                        </div>

                                        {/* Menu Items */}
                                        <button
                                            onClick={() => {
                                                setUserMenuOpen(false);
                                                navigate('/settings');
                                            }}
                                            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                                        >
                                            <Settings className="w-4 h-4" />
                                            Configurações
                                        </button>

                                        <button
                                            onClick={() => {
                                                setUserMenuOpen(false);
                                                navigate('/profile');
                                            }}
                                            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                                        >
                                            <User className="w-4 h-4" />
                                            Meu Perfil
                                        </button>

                                        <div className="border-t border-gray-200 dark:border-gray-700 my-1" />

                                        <button
                                            onClick={handleLogout}
                                            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                        >
                                            <LogOut className="w-4 h-4" />
                                            Sair
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Mobile Menu Button */}
                    <button
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        className="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                    >
                        {mobileMenuOpen ? (
                            <X className="w-6 h-6 text-gray-600 dark:text-gray-300" />
                        ) : (
                            <MenuIcon className="w-6 h-6 text-gray-600 dark:text-gray-300" />
                        )}
                    </button>
                </div>

                {/* Mobile Menu */}
                {mobileMenuOpen && (
                    <div className="md:hidden border-t border-gray-200 dark:border-gray-800 py-4">
                        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-800">
                            {user.foto_url ? (
                                <img 
                                    src={user.foto_url} 
                                    alt={user.nome}
                                    className="w-10 h-10 rounded-full object-cover"
                                />
                            ) : (
                                <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-semibold">
                                    {userInitial}
                                </div>
                            )}
                            <div>
                                <p className="text-sm font-medium text-gray-900 dark:text-white">
                                    {user.nome || 'Usuário'}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                    {user.cargo || user.role || 'Cargo não definido'}
                                </p>
                            </div>
                        </div>

                        <div className="py-2">
                            <button
                                onClick={toggleTheme}
                                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                            >
                                {config?.tema_escuro ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                                {config?.tema_escuro ? 'Tema Claro' : 'Tema Escuro'}
                            </button>

                            <button
                                onClick={() => {
                                    setMobileMenuOpen(false);
                                    navigate('/settings');
                                }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                            >
                                <Settings className="w-5 h-5" />
                                Configurações
                            </button>

                            <button
                                onClick={() => {
                                    setMobileMenuOpen(false);
                                    navigate('/profile');
                                }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                            >
                                <User className="w-5 h-5" />
                                Meu Perfil
                            </button>

                            <button
                                onClick={handleLogout}
                                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                            >
                                <LogOut className="w-5 h-5" />
                                Sair
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </header>
    );
};

export default HeaderProfessional;
