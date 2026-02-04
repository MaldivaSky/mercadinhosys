import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    User, LogOut, Settings, Moon, Sun, ChevronDown, 
    Menu as MenuIcon, X 
} from 'lucide-react';
import { useConfig } from '../../contexts/ConfigContext';
import logo from '../../../logoprincipal.png';
import { authService } from '../../features/auth/authService';
import { API_CONFIG } from '../../api/apiConfig';

const HeaderProfessional = () => {
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [profileModalOpen, setProfileModalOpen] = useState(false);
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [changingPassword, setChangingPassword] = useState(false);
    const [passwordError, setPasswordError] = useState<string | null>(null);
    const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
    const passwordChecks = useMemo(() => {
        const pwd = newPassword;
        const checks = {
            length: pwd.length >= 8,
            upper: /[A-Z]/.test(pwd),
            lower: /[a-z]/.test(pwd),
            number: /[0-9]/.test(pwd),
            special: /[^A-Za-z0-9]/.test(pwd),
            match: pwd === confirmPassword
        };
        return checks;
    }, [newPassword, confirmPassword]);
    const navigate = useNavigate();
    const { config, updateConfig } = useConfig();

    const user = useMemo(() => {
        try {
            return JSON.parse(localStorage.getItem('user_data') || '{}');
        } catch {
            return {};
        }
    }, []);

    const [showChangePassword, setShowChangePassword] = useState(false);
    const [showEditProfile, setShowEditProfile] = useState(false);
    const [editNome, setEditNome] = useState<string>(typeof user.nome === 'string' ? user.nome : '');
    const [editEmail, setEditEmail] = useState<string>(typeof user.email === 'string' ? user.email : '');
    const [editTelefone, setEditTelefone] = useState<string>(typeof user.telefone === 'string' ? user.telefone : '');
    const [editFotoUrl, setEditFotoUrl] = useState<string>(typeof user.foto_url === 'string' ? user.foto_url : '');
    const [savingProfile, setSavingProfile] = useState(false);
    const [profileError, setProfileError] = useState<string | null>(null);
    const [profileSuccess, setProfileSuccess] = useState<string | null>(null);

    const userInitial = useMemo(() => {
        return user.nome ? user.nome.charAt(0).toUpperCase() : 'U';
    }, [user.nome]);

    // Calcular logo URL dinamicamente baseado no config
    const logoUrl = useMemo(() => {
        // Preferir base64 quando disponível (evita mixed content)
        if (config?.logo_base64) {
            return config.logo_base64;
        }
        if (!config?.logo_url) {
            return logo;
        }
        
        // Se for base64 (preview), usar direto
        if (config.logo_url.startsWith('data:')) {
            return config.logo_url;
        }
        
        // Se for URL do servidor
        if (config.logo_url.startsWith('http')) {
            return config.logo_url;
        }
        
        // Se for caminho relativo, anexar à origem do backend (sem /api)
        const apiOrigin = API_CONFIG.BASE_URL.replace(/\/api$/, '');
        return `${apiOrigin}${config.logo_url}`;
    }, [config?.logo_url, config?.logo_base64]);

    const toggleTheme = async () => {
        try {
            await updateConfig({ tema_escuro: !config?.tema_escuro });
        } catch (error) {
            console.error('Erro ao alternar tema:', error);
        }
    };

    const handleLogout = () => {
        setUserMenuOpen(false);
        setMobileMenuOpen(false);
        authService.logout();
        navigate('/login');
    };

    const handleChangePassword = async () => {
        setPasswordError(null);
        setPasswordSuccess(null);
        if (!currentPassword || !newPassword || !confirmPassword) {
            setPasswordError('Preencha todos os campos');
            return;
        }
        if (!(passwordChecks.length && passwordChecks.upper && passwordChecks.lower && passwordChecks.number && passwordChecks.special)) {
            setPasswordError('A senha deve ter 8+ caracteres, maiúscula, minúscula, número e símbolo');
            return;
        }
        if (!passwordChecks.match) {
            setPasswordError('A confirmação não coincide com a nova senha');
            return;
        }
        setChangingPassword(true);
        try {
            const result = await authService.changePassword(currentPassword, newPassword);
            setPasswordSuccess(result.message || 'Senha alterada com sucesso');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
            setShowChangePassword(false);
            handleLogout();
        } catch (e) {
            const err = e as Error;
            setPasswordError(err.message);
        } finally {
            setChangingPassword(false);
        }
    };

    const handleUpdateProfile = async () => {
        setProfileError(null);
        setProfileSuccess(null);
        if (!editNome.trim()) {
            setProfileError('Nome é obrigatório');
            return;
        }
        if (editEmail && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(editEmail)) {
            setProfileError('Email inválido');
            return;
        }
        setSavingProfile(true);
        try {
            const payload: { nome?: string; email?: string; telefone?: string; foto_url?: string } = {};
            if (editNome !== user.nome) payload.nome = editNome.trim();
            if (editEmail !== user.email) payload.email = editEmail.trim();
            if (editTelefone !== user.telefone) payload.telefone = editTelefone.trim();
            if (editFotoUrl !== user.foto_url) payload.foto_url = editFotoUrl.trim();
            const result = await authService.updateProfile(payload);
            const updated = { ...user, ...result.data };
            localStorage.setItem('user_data', JSON.stringify(updated));
            window.dispatchEvent(new Event('auth-change'));
            setProfileSuccess(result.message || 'Perfil atualizado');
            setShowEditProfile(false);
        } catch (e) {
            const err = e as Error;
            setProfileError(err.message);
        } finally {
            setSavingProfile(false);
        }
    };

    return (
        <>
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
                                                setProfileModalOpen(true);
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
                                    setProfileModalOpen(true);
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
        {/* Modal de Perfil */}
        {profileModalOpen && (  
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4">
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md">
                    <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Meu Perfil</h3>
                        <button
                            onClick={() => setProfileModalOpen(false)}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                            aria-label="Fechar"
                        >
                            <X className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                        </button>
                    </div>
                    <div className="px-5 py-4 space-y-4">
                        <div className="flex items-center gap-3">
                            {user.foto_url ? (
                                <img src={user.foto_url} alt={user.nome} className="w-12 h-12 rounded-full object-cover" />
                            ) : (
                                <div className="w-12 h-12 rounded-full bg-primary text-white flex items-center justify-center font-semibold">
                                    {userInitial}
                                </div>
                            )}
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400">Nome</p>
                                <p className="font-medium text-gray-900 dark:text-white">{user.nome || '-'}</p>
                            </div>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Username</p>
                            <p className="font-medium text-gray-900 dark:text-white">{user.username || user.usuario || '-'}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
                            <p className="font-medium text-gray-900 dark:text-white">{user.email || '-'}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Nível de Permissão</p>
                            <p className="font-medium text-gray-900 dark:text-white">{user.role || user.cargo || '-'}</p>
                        </div>

                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                            <button
                                onClick={() => setShowEditProfile(!showEditProfile)}
                                className="w-full text-left px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-sm font-medium text-gray-800 dark:text-gray-200 transition"
                            >
                                Editar Dados
                            </button>
                            {showEditProfile && (
                                <div className="mt-3 space-y-3">
                                    {profileError && (
                                        <div className="px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
                                            {profileError}
                                        </div>
                                    )}
                                    {profileSuccess && (
                                        <div className="px-3 py-2 rounded-lg bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm">
                                            {profileSuccess}
                                        </div>
                                    )}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Nome</label>
                                            <input
                                                type="text"
                                                value={editNome}
                                                onChange={(e) => setEditNome(e.target.value)}
                                                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Email</label>
                                            <input
                                                type="email"
                                                value={editEmail}
                                                onChange={(e) => setEditEmail(e.target.value)}
                                                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Telefone</label>
                                            <input
                                                type="text"
                                                value={editTelefone}
                                                onChange={(e) => setEditTelefone(e.target.value)}
                                                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Foto URL</label>
                                            <input
                                                type="text"
                                                value={editFotoUrl}
                                                onChange={(e) => setEditFotoUrl(e.target.value)}
                                                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={() => setShowEditProfile(false)}
                                            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                                        >
                                            Cancelar
                                        </button>
                                        <button
                                            onClick={handleUpdateProfile}
                                            disabled={savingProfile}
                                            className={`px-4 py-2 rounded-lg font-medium transition ${
                                                savingProfile
                                                    ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                                                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                                            }`}
                                        >
                                            {savingProfile ? 'Salvando...' : 'Salvar'}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                            <button
                                onClick={() => setShowChangePassword(!showChangePassword)}
                                className="w-full text-left px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-sm font-medium text-gray-800 dark:text-gray-200 transition"
                            >
                                Alterar Senha
                            </button>
                            {showChangePassword && (
                                <div className="mt-3 space-y-3">
                                    {passwordError && (
                                        <div className="px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
                                            {passwordError}
                                        </div>
                                    )}
                                    {passwordSuccess && (
                                        <div className="px-3 py-2 rounded-lg bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm">
                                            {passwordSuccess}
                                        </div>
                                    )}
                                    <div>
                                        <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Senha Atual</label>
                                        <input
                                            type="password"
                                            value={currentPassword}
                                            onChange={(e) => setCurrentPassword(e.target.value)}
                                            className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                        />
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Nova Senha</label>
                                            <input
                                                type="password"
                                                value={newPassword}
                                                onChange={(e) => setNewPassword(e.target.value)}
                                                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Confirmar Nova Senha</label>
                                            <input
                                                type="password"
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                            />
                                        </div>
                                    </div>
                                    <div className="text-xs space-y-1">
                                        <div className={`${passwordChecks.length ? 'text-green-600 dark:text-green-300' : 'text-gray-500 dark:text-gray-400'}`}>• 8+ caracteres</div>
                                        <div className={`${passwordChecks.upper ? 'text-green-600 dark:text-green-300' : 'text-gray-500 dark:text-gray-400'}`}>• Letra maiúscula</div>
                                        <div className={`${passwordChecks.lower ? 'text-green-600 dark:text-green-300' : 'text-gray-500 dark:text-gray-400'}`}>• Letra minúscula</div>
                                        <div className={`${passwordChecks.number ? 'text-green-600 dark:text-green-300' : 'text-gray-500 dark:text-gray-400'}`}>• Número</div>
                                        <div className={`${passwordChecks.special ? 'text-green-600 dark:text-green-300' : 'text-gray-500 dark:text-gray-400'}`}>• Símbolo</div>
                                        <div className={`${passwordChecks.match ? 'text-green-600 dark:text-green-300' : 'text-gray-500 dark:text-gray-400'}`}>• Confirmação coincide</div>
                                    </div>
                                    <div className="flex justify-end">
                                        <button
                                            onClick={handleChangePassword}
                                            disabled={changingPassword || !(passwordChecks.length && passwordChecks.upper && passwordChecks.lower && passwordChecks.number && passwordChecks.special && passwordChecks.match)}
                                            className={`px-4 py-2 rounded-lg font-medium transition ${
                                                changingPassword
                                                    ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                                                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                                            }`}
                                        >
                                            {changingPassword ? 'Alterando...' : 'Salvar nova senha'}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="px-5 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
                        <button
                            onClick={() => setProfileModalOpen(false)}
                            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        >
                            Fechar
                        </button>
                    </div>
                </div>
            </div>
        )}
        </>
    );
};

export default HeaderProfessional;
