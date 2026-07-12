import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Upload, Store, Users, ChevronRight, Package, Rocket } from 'lucide-react';
import { apiClient } from '../../api/apiClient';
import toast from 'react-hot-toast';

const OnboardingWizard: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    
    // Arquivos
    const [fileProdutos, setFileProdutos] = useState<File | null>(null);
    const [fileClientes, setFileClientes] = useState<File | null>(null);

    // Informações Básicas
    const [storeName, setStoreName] = useState('');

    const steps = [
        { id: 1, title: 'Boas Vindas', icon: Store },
        { id: 2, title: 'Estoque', icon: Package },
        { id: 3, title: 'Clientes (Fiado)', icon: Users },
        { id: 4, title: 'Pronto', icon: Rocket }
    ];

    const nextStep = () => setStep(s => Math.min(4, s + 1));

    const handleUploadProdutos = async () => {
        if (!fileProdutos) {
            nextStep();
            return;
        }

        const formData = new FormData();
        formData.append('arquivo', fileProdutos);

        setLoading(true);
        try {
            const res = await apiClient.post('/produtos/importar', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            if (res.data?.success) {
                toast.success(`Estoque base carregado com sucesso!`);
                nextStep();
            } else {
                toast.error(res.data?.message || "Erro na importação.");
            }
        } catch (e: any) {
            toast.error(e.response?.data?.message || "Falha ao enviar arquivo.");
        } finally {
            setLoading(false);
        }
    };

    const handleUploadClientes = async () => {
        if (!fileClientes) {
            nextStep();
            return;
        }

        const formData = new FormData();
        formData.append('arquivo', fileClientes);

        setLoading(true);
        try {
            const res = await apiClient.post('/clientes/importar', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            if (res.data?.success) {
                toast.success(`Carteira de clientes migrada com sucesso!`);
                nextStep();
            } else {
                toast.error(res.data?.message || "Erro na importação.");
            }
        } catch (e: any) {
            toast.error(e.response?.data?.message || "Falha ao enviar arquivo.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-950/80 backdrop-blur-xl p-4 md:p-8"
        >
            <div className="w-full max-w-4xl bg-slate-900 border border-slate-800 shadow-2xl rounded-3xl overflow-hidden flex flex-col md:flex-row">
                
                {/* Sidebar do Wizard */}
                <div className="w-full md:w-1/3 bg-slate-800/50 p-8 border-r border-slate-800 flex flex-col justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-10">
                            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-600/20">
                                <Rocket className="w-5 h-5 text-white" />
                            </div>
                            <span className="text-xl font-black text-white italic tracking-tight">MercadinhoSyS</span>
                        </div>
                        
                        <div className="space-y-6">
                            {steps.map(s => {
                                const Icon = s.icon;
                                const isActive = step >= s.id;
                                const isCurrent = step === s.id;
                                return (
                                    <div key={s.id} className="flex items-center gap-4">
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                                            isActive 
                                                ? 'bg-blue-600 border-blue-600 text-white' 
                                                : 'bg-slate-800 border-slate-700 text-slate-500'
                                        } ${isCurrent ? 'ring-4 ring-blue-600/20 shadow-lg shadow-blue-500/40' : ''}`}>
                                            {step > s.id ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                                        </div>
                                        <span className={`text-sm font-bold tracking-wide transition-colors ${
                                            isCurrent ? 'text-white' : isActive ? 'text-slate-300' : 'text-slate-500'
                                        }`}>
                                            {s.title}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                    
                    <div className="mt-10">
                        <p className="text-xs text-slate-500 font-medium">Ambiente Seguro (Criptografia 256-bits). Seus dados comerciais nunca serão compartilhados.</p>
                    </div>
                </div>

                {/* Conteúdo do Wizard */}
                <div className="w-full md:w-2/3 p-8 md:p-12 flex flex-col justify-center min-h-[500px]">
                    <AnimatePresence mode="wait">
                        {step === 1 && (
                            <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                                <h2 className="text-3xl font-black text-white mb-2">Bem-vindo ao topo.</h2>
                                <p className="text-slate-400 mb-8 text-lg">Vamos configurar seu ERP de alta performance. Qual o nome fantasia da sua loja?</p>
                                
                                <div className="space-y-6">
                                    <div>
                                        <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-2">Nome Fantasia (Aparecerá nos cupons)</label>
                                        <input 
                                            type="text" 
                                            value={storeName}
                                            onChange={e => setStoreName(e.target.value)}
                                            placeholder="Ex: Mercadinho Dois Irmãos" 
                                            className="w-full p-4 rounded-xl border border-slate-700 bg-slate-800/50 text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-lg font-medium" 
                                        />
                                    </div>
                                    <button 
                                        onClick={nextStep}
                                        disabled={!storeName}
                                        className="w-full py-4 bg-blue-600 text-white rounded-xl font-black uppercase tracking-widest hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        Começar <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            </motion.div>
                        )}

                        {step === 2 && (
                            <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                                <h2 className="text-3xl font-black text-white mb-2">Estoque Base</h2>
                                <p className="text-slate-400 mb-8">Arraste a sua planilha de produtos. Nós já cadastraremos o estoque e os custos automaticamente.</p>
                                
                                <div className="border-2 border-dashed border-slate-700 rounded-2xl p-10 text-center bg-slate-800/30 hover:bg-slate-800 transition-colors relative cursor-pointer group">
                                    <input 
                                        type="file" 
                                        accept=".csv"
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                        onChange={e => setFileProdutos(e.target.files?.[0] || null)}
                                    />
                                    <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4 group-hover:text-blue-500 transition-colors" />
                                    <p className="text-lg font-bold text-slate-300">
                                        {fileProdutos ? fileProdutos.name : "Clique ou arraste seu CSV aqui"}
                                    </p>
                                    <p className="text-sm text-slate-500 mt-2">Padrão: nome, categoria, preco_custo, preco_venda, estoque</p>
                                </div>

                                <div className="mt-8 flex gap-4">
                                    <button 
                                        onClick={handleUploadProdutos}
                                        disabled={loading}
                                        className={`flex-1 py-4 text-white rounded-xl font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 ${fileProdutos ? 'bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                                    >
                                        {loading ? 'Processando...' : fileProdutos ? 'Importar Produtos' : 'Pular Etapa'} <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            </motion.div>
                        )}

                        {step === 3 && (
                            <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                                <h2 className="text-3xl font-black text-white mb-2">Carteira de Clientes</h2>
                                <p className="text-slate-400 mb-8">Não perca o histórico do caderninho. Suba seus clientes e nós geraremos o "Contas a Receber" das dívidas pendentes na hora.</p>
                                
                                <div className="border-2 border-dashed border-slate-700 rounded-2xl p-10 text-center bg-slate-800/30 hover:bg-slate-800 transition-colors relative cursor-pointer group">
                                    <input 
                                        type="file" 
                                        accept=".csv"
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                        onChange={e => setFileClientes(e.target.files?.[0] || null)}
                                    />
                                    <Users className="w-12 h-12 text-slate-500 mx-auto mb-4 group-hover:text-blue-500 transition-colors" />
                                    <p className="text-lg font-bold text-slate-300">
                                        {fileClientes ? fileClientes.name : "Arraste o CSV de Clientes"}
                                    </p>
                                    <p className="text-sm text-slate-500 mt-2">Padrão: nome, cpf, celular, limite_credito, saldo_devedor</p>
                                </div>

                                <div className="mt-8 flex gap-4">
                                    <button 
                                        onClick={handleUploadClientes}
                                        disabled={loading}
                                        className={`flex-1 py-4 text-white rounded-xl font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 ${fileClientes ? 'bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                                    >
                                        {loading ? 'Processando...' : fileClientes ? 'Migrar Dívidas' : 'Pular Etapa'} <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            </motion.div>
                        )}

                        {step === 4 && (
                            <motion.div key="step4" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="text-center">
                                <div className="w-24 h-24 bg-green-500/20 border border-green-500/50 text-green-400 rounded-full flex items-center justify-center mx-auto mb-8 shadow-[0_0_40px_rgba(34,197,94,0.3)]">
                                    <Check className="w-12 h-12" />
                                </div>
                                <h2 className="text-4xl font-black text-white mb-4 italic tracking-tight">Decolagem Autorizada!</h2>
                                <p className="text-slate-400 text-lg mb-10">O motor do seu ERP está aquecido. Vendas, estoque, clientes e financeiro 100% integrados.</p>
                                
                                <button 
                                    onClick={onComplete}
                                    className="w-full py-5 bg-green-600 text-white rounded-xl font-black text-lg uppercase tracking-widest hover:bg-green-700 transition-all shadow-xl shadow-green-600/30 flex items-center justify-center gap-3"
                                >
                                    Abrir Frente de Caixa <Rocket className="w-6 h-6" />
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
    );
};

export default OnboardingWizard;
