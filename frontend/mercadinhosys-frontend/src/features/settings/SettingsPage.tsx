import React, { useEffect, useState } from 'react';
import { 
    Settings, Building, ShoppingCart, Package, Shield, Save, 
    Upload, Bell, Printer, DollarSign 
} from 'lucide-react';
import settingsService, { Configuracao, Estabelecimento } from './settingsService';
import { toast } from 'react-hot-toast';

// Componentes de UI reutilizáveis (poderiam estar em arquivos separados)
const SectionTitle = ({ title, icon: Icon }: { title: string, icon: any }) => (
    <div className="flex items-center space-x-2 mb-4 border-b pb-2 border-gray-200 dark:border-gray-700">
        <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200">{title}</h3>
    </div>
);

const InputField = ({ label, value, onChange, type = "text", placeholder = "", disabled = false }: any) => (
    <div className="flex flex-col space-y-1">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>
        <input 
            type={type} 
            value={value} 
            onChange={onChange} 
            disabled={disabled}
            placeholder={placeholder}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white transition-colors"
        />
    </div>
);

const SwitchField = ({ label, checked, onChange, description }: any) => (
    <div className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors border-gray-200 dark:border-gray-700">
        <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{label}</span>
            {description && <span className="text-xs text-gray-500 dark:text-gray-400">{description}</span>}
        </div>
        <button 
            onClick={() => onChange(!checked)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${checked ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-600'}`}
        >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'}`} />
        </button>
    </div>
);

const SettingsPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState('geral');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    
    const [config, setConfig] = useState<Configuracao>({
        id: 0, estabelecimento_id: 0, cor_principal: '#2563eb', tema_escuro: false,
        emitir_nfe: false, emitir_nfce: true, impressao_automatica: false, tipo_impressora: 'termica_80mm',
        exibir_preco_tela: true, permitir_venda_sem_estoque: false, desconto_maximo_percentual: 10,
        desconto_maximo_funcionario: 10, arredondamento_valores: true, formas_pagamento: [],
        controlar_validade: true, alerta_estoque_minimo: true, dias_alerta_validade: 30, estoque_minimo_padrao: 10,
        tempo_sessao_minutos: 30, tentativas_senha_bloqueio: 3, alertas_email: false, alertas_whatsapp: false
    });

    const [estab, setEstab] = useState<Estabelecimento>({
        id: 0, nome_fantasia: '', razao_social: '', cnpj: '', telefone: '', email: '',
        cep: '', logradouro: '', numero: '', bairro: '', cidade: '', estado: ''
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [configData, estabData] = await Promise.all([
                settingsService.getConfig(),
                settingsService.getEstabelecimento()
            ]);
            setConfig(configData);
            setEstab(estabData);
        } catch (error) {
            console.error("Erro ao carregar configurações:", error);
            toast.error("Erro ao carregar configurações.");
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            await Promise.all([
                settingsService.updateConfig(config),
                settingsService.updateEstabelecimento(estab)
            ]);
            toast.success("Configurações salvas com sucesso!");
        } catch (error) {
            console.error("Erro ao salvar:", error);
            toast.error("Erro ao salvar alterações.");
        } finally {
            setSaving(false);
        }
    };

    const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            try {
                const url = await settingsService.uploadLogo(e.target.files[0]);
                setConfig({ ...config, logo_url: url });
                toast.success("Logo atualizada com sucesso!");
            } catch (error) {
                toast.error("Erro ao fazer upload da logo.");
            }
        }
    };

    const tabs = [
        { id: 'geral', label: 'Geral', icon: Settings },
        { id: 'estabelecimento', label: 'Estabelecimento', icon: Building },
        { id: 'vendas', label: 'Vendas & PDV', icon: ShoppingCart },
        { id: 'estoque', label: 'Estoque', icon: Package },
        { id: 'sistema', label: 'Sistema & Segurança', icon: Shield },
    ];

    if (loading) {
        return <div className="flex justify-center items-center h-screen text-gray-500">Carregando configurações...</div>;
    }

    return (
        <div className="container mx-auto p-4 max-w-6xl">
            
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
                        <Settings className="w-8 h-8 text-blue-600" />
                        Configurações do Sistema
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">Gerencie todos os parâmetros do seu ERP</p>
                </div>
                <button 
                    onClick={handleSave} 
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 shadow-lg"
                >
                    {saving ? <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div> : <Save className="w-5 h-5" />}
                    {saving ? 'Salvando...' : 'Salvar Alterações'}
                </button>
            </div>

            <div className="flex flex-col md:flex-row gap-6">
                {/* Sidebar de Abas */}
                <div className="w-full md:w-64 flex-shrink-0">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden sticky top-4">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 px-4 py-4 text-left transition-colors border-l-4 ${
                                    activeTab === tab.id 
                                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-600' 
                                    : 'text-gray-600 dark:text-gray-400 border-transparent hover:bg-gray-50 dark:hover:bg-gray-700'
                                }`}
                            >
                                <tab.icon className="w-5 h-5" />
                                <span className="font-medium">{tab.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Conteúdo Principal */}
                <div className="flex-1 space-y-6">
                    
                    {/* ABA GERAL */}
                    {activeTab === 'geral' && (
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 space-y-6 animate-fadeIn">
                            <SectionTitle title="Aparência e Identidade" icon={Settings} />
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="col-span-2 flex items-center gap-4 p-4 border rounded-lg border-gray-200 dark:border-gray-700">
                                    <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden border border-gray-300 relative group">
                                        {config.logo_url ? (
                                            <img src={`http://localhost:5000${config.logo_url}`} alt="Logo" className="w-full h-full object-contain" />
                                        ) : (
                                            <Building className="w-8 h-8 text-gray-400" />
                                        )}
                                        <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                                            <label className="cursor-pointer text-white text-xs text-center p-1">
                                                Alterar
                                                <input type="file" className="hidden" accept="image/*" onChange={handleLogoUpload} />
                                            </label>
                                        </div>
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-gray-800 dark:text-white">Logo do Estabelecimento</h4>
                                        <p className="text-sm text-gray-500">Recomendado: 200x200px (PNG ou JPG)</p>
                                        <label className="mt-2 inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-sm cursor-pointer transition-colors">
                                            <Upload className="w-4 h-4" /> Upload
                                            <input type="file" className="hidden" accept="image/*" onChange={handleLogoUpload} />
                                        </label>
                                    </div>
                                </div>

                                <InputField 
                                    label="Cor Principal (Hex)" 
                                    type="color"
                                    value={config.cor_principal} 
                                    onChange={(e: any) => setConfig({...config, cor_principal: e.target.value})} 
                                />

                                <SwitchField 
                                    label="Modo Escuro" 
                                    description="Ativar tema escuro por padrão"
                                    checked={config.tema_escuro}
                                    onChange={(val: boolean) => setConfig({...config, tema_escuro: val})}
                                />
                            </div>
                        </div>
                    )}

                    {/* ABA ESTABELECIMENTO */}
                    {activeTab === 'estabelecimento' && (
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 space-y-6 animate-fadeIn">
                            <SectionTitle title="Dados da Empresa" icon={Building} />
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <InputField label="Nome Fantasia" value={estab.nome_fantasia} onChange={(e: any) => setEstab({...estab, nome_fantasia: e.target.value})} />
                                <InputField label="Razão Social" value={estab.razao_social} onChange={(e: any) => setEstab({...estab, razao_social: e.target.value})} />
                                <InputField label="CNPJ" value={estab.cnpj} onChange={(e: any) => setEstab({...estab, cnpj: e.target.value})} />
                                <InputField label="Inscrição Estadual" value={estab.inscricao_estadual || ''} onChange={(e: any) => setEstab({...estab, inscricao_estadual: e.target.value})} />
                                <InputField label="Telefone" value={estab.telefone} onChange={(e: any) => setEstab({...estab, telefone: e.target.value})} />
                                <InputField label="E-mail" value={estab.email} onChange={(e: any) => setEstab({...estab, email: e.target.value})} />
                            </div>

                            <SectionTitle title="Endereço" icon={Building} />
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="md:col-span-1">
                                    <InputField label="CEP" value={estab.cep} onChange={(e: any) => setEstab({...estab, cep: e.target.value})} />
                                </div>
                                <div className="md:col-span-2">
                                    <InputField label="Logradouro" value={estab.logradouro} onChange={(e: any) => setEstab({...estab, logradouro: e.target.value})} />
                                </div>
                                <InputField label="Número" value={estab.numero} onChange={(e: any) => setEstab({...estab, numero: e.target.value})} />
                                <InputField label="Bairro" value={estab.bairro} onChange={(e: any) => setEstab({...estab, bairro: e.target.value})} />
                                <InputField label="Cidade" value={estab.cidade} onChange={(e: any) => setEstab({...estab, cidade: e.target.value})} />
                                <InputField label="Estado (UF)" value={estab.estado} onChange={(e: any) => setEstab({...estab, estado: e.target.value})} />
                            </div>
                        </div>
                    )}

                    {/* ABA VENDAS */}
                    {activeTab === 'vendas' && (
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 space-y-6 animate-fadeIn">
                            <SectionTitle title="Ponto de Venda (PDV)" icon={ShoppingCart} />
                            
                            <div className="space-y-4">
                                <SwitchField 
                                    label="Impressão Automática" 
                                    description="Imprimir cupom automaticamente ao finalizar venda"
                                    checked={config.impressao_automatica}
                                    onChange={(val: boolean) => setConfig({...config, impressao_automatica: val})}
                                />
                                
                                <SwitchField 
                                    label="Exibir Preço na Tela" 
                                    description="Mostrar preço unitário grande na tela de venda"
                                    checked={config.exibir_preco_tela}
                                    onChange={(val: boolean) => setConfig({...config, exibir_preco_tela: val})}
                                />

                                <SwitchField 
                                    label="Permitir Venda Sem Estoque" 
                                    description="Autorizar vendas mesmo com estoque zerado ou negativo"
                                    checked={config.permitir_venda_sem_estoque}
                                    onChange={(val: boolean) => setConfig({...config, permitir_venda_sem_estoque: val})}
                                />
                                
                                <SwitchField 
                                    label="Arredondamento de Valores" 
                                    description="Arredondar centavos automaticamente no total"
                                    checked={config.arredondamento_valores}
                                    onChange={(val: boolean) => setConfig({...config, arredondamento_valores: val})}
                                />
                            </div>

                            <SectionTitle title="Notas Fiscais" icon={Printer} />
                            <div className="space-y-4">
                                <SwitchField 
                                    label="Emitir NFC-e" 
                                    description="Habilitar emissão de Nota Fiscal de Consumidor Eletrônica"
                                    checked={config.emitir_nfce}
                                    onChange={(val: boolean) => setConfig({...config, emitir_nfce: val})}
                                />
                                <SwitchField 
                                    label="Emitir NF-e" 
                                    description="Habilitar emissão de Nota Fiscal Eletrônica (Grande porte)"
                                    checked={config.emitir_nfe}
                                    onChange={(val: boolean) => setConfig({...config, emitir_nfe: val})}
                                />
                            </div>

                            <SectionTitle title="Limites e Descontos" icon={DollarSign} />
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <InputField 
                                    label="Desconto Máximo (%)" 
                                    type="number" 
                                    value={config.desconto_maximo_percentual} 
                                    onChange={(e: any) => setConfig({...config, desconto_maximo_percentual: parseFloat(e.target.value)})} 
                                />
                                <InputField 
                                    label="Desconto Máx. Funcionário (%)" 
                                    type="number" 
                                    value={config.desconto_maximo_funcionario} 
                                    onChange={(e: any) => setConfig({...config, desconto_maximo_funcionario: parseFloat(e.target.value)})} 
                                />
                            </div>
                        </div>
                    )}

                    {/* ABA ESTOQUE */}
                    {activeTab === 'estoque' && (
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 space-y-6 animate-fadeIn">
                            <SectionTitle title="Controle de Estoque" icon={Package} />
                            
                            <div className="space-y-4">
                                <SwitchField 
                                    label="Controlar Validade" 
                                    description="Exigir data de validade para produtos perecíveis"
                                    checked={config.controlar_validade}
                                    onChange={(val: boolean) => setConfig({...config, controlar_validade: val})}
                                />
                                
                                <SwitchField 
                                    label="Alerta de Estoque Mínimo" 
                                    description="Notificar quando produtos atingirem nível crítico"
                                    checked={config.alerta_estoque_minimo}
                                    onChange={(val: boolean) => setConfig({...config, alerta_estoque_minimo: val})}
                                />
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                <InputField 
                                    label="Dias para Alerta de Validade" 
                                    type="number"
                                    value={config.dias_alerta_validade} 
                                    onChange={(e: any) => setConfig({...config, dias_alerta_validade: parseInt(e.target.value)})} 
                                />
                                <InputField 
                                    label="Estoque Mínimo Padrão" 
                                    type="number"
                                    value={config.estoque_minimo_padrao} 
                                    onChange={(e: any) => setConfig({...config, estoque_minimo_padrao: parseInt(e.target.value)})} 
                                />
                            </div>
                        </div>
                    )}

                    {/* ABA SISTEMA */}
                    {activeTab === 'sistema' && (
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 space-y-6 animate-fadeIn">
                            <SectionTitle title="Segurança" icon={Shield} />
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <InputField 
                                    label="Tempo de Sessão (minutos)" 
                                    type="number"
                                    value={config.tempo_sessao_minutos} 
                                    onChange={(e: any) => setConfig({...config, tempo_sessao_minutos: parseInt(e.target.value)})} 
                                />
                                <InputField 
                                    label="Tentativas de Senha antes do Bloqueio" 
                                    type="number"
                                    value={config.tentativas_senha_bloqueio} 
                                    onChange={(e: any) => setConfig({...config, tentativas_senha_bloqueio: parseInt(e.target.value)})} 
                                />
                            </div>

                            <SectionTitle title="Notificações" icon={Bell} />
                            <div className="space-y-4">
                                <SwitchField 
                                    label="Alertas por E-mail" 
                                    description="Receber relatórios e alertas críticos por e-mail"
                                    checked={config.alertas_email}
                                    onChange={(val: boolean) => setConfig({...config, alertas_email: val})}
                                />
                                <SwitchField 
                                    label="Alertas via WhatsApp" 
                                    description="Integração para envio de alertas via WhatsApp"
                                    checked={config.alertas_whatsapp}
                                    onChange={(val: boolean) => setConfig({...config, alertas_whatsapp: val})}
                                />
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};

export default SettingsPage;
