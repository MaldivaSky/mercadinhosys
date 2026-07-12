import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Upload, Store, Users, ChevronRight, ChevronLeft } from 'lucide-react';
import { apiClient } from '../../api/apiClient';
import toast from 'react-hot-toast';

const OnboardingWizard: React.FC<{ onComplete?: () => void }> = ({ onComplete }) => {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [file, setFile] = useState<File | null>(null);

    const steps = [
        { id: 1, title: 'Loja', icon: Store },
        { id: 2, title: 'Estoque', icon: Upload },
        { id: 3, title: 'Pronto', icon: Check }
    ];

    const nextStep = () => setStep(s => Math.min(3, s + 1));
    const prevStep = () => setStep(s => Math.max(1, s - 1));

    const handleUpload = async () => {
        if (!file) {
            toast.error("Selecione um arquivo CSV ou Excel.");
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        setLoading(true);
        try {
            const res = await apiClient.post('/produtos/import', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            if (res.data?.success) {
                toast.success(`Foram importados ${res.data.detalhes.criados} produtos!`);
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

    const handleComplete = () => {
        if (onComplete) {
            onComplete();
        } else {
            window.location.href = '/dashboard';
        }
    };

    return (
        <div className="max-w-2xl mx-auto p-6 md:p-10 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-2xl">
            {/* PROGRESS BAR */}
            <div className="flex justify-between items-center mb-8 relative">
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-slate-100 dark:bg-slate-800 -z-10 rounded-full overflow-hidden">
                    <motion.div 
                        initial={{ width: 0 }} 
                        animate={{ width: `${((step - 1) / 2) * 100}%` }} 
                        className="h-full bg-blue-600 transition-all duration-300" 
                    />
                </div>
                {steps.map(s => {
                    const Icon = s.icon;
                    const isActive = step >= s.id;
                    const isCurrent = step === s.id;
                    return (
                        <div key={s.id} className="flex flex-col items-center gap-2 bg-white dark:bg-slate-900 px-2">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${
                                isActive 
                                    ? 'bg-blue-600 border-blue-600 text-white' 
                                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-400'
                            } ${isCurrent ? 'ring-4 ring-blue-600/20' : ''}`}>
                                <Icon className="w-5 h-5" />
                            </div>
                            <span className={`text-[10px] font-black uppercase tracking-widest ${isActive ? 'text-blue-600' : 'text-slate-400'}`}>
                                {s.title}
                            </span>
                        </div>
                    );
                })}
            </div>

            {/* CONTENT */}
            <div className="min-h-[300px]">
                <AnimatePresence mode="wait">
                    {step === 1 && (
                        <motion.div key="step1" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
                            <h2 className="text-2xl font-black text-slate-800 dark:text-white mb-2">Bem-vindo ao MercadinhoSyS</h2>
                            <p className="text-sm text-slate-500 mb-6">Vamos configurar as informações básicas da sua loja para começar a usar o PDV.</p>
                            
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-1">Nome da Loja</label>
                                    <input type="text" placeholder="Sua Loja" className="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none transition-all" />
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {step === 2 && (
                        <motion.div key="step2" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
                            <h2 className="text-2xl font-black text-slate-800 dark:text-white mb-2">Importar Estoque</h2>
                            <p className="text-sm text-slate-500 mb-6">Envie sua planilha Excel ou CSV para importar os produtos automaticamente.</p>
                            
                            <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-2xl p-8 text-center bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors relative cursor-pointer group">
                                <input 
                                    type="file" 
                                    accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    onChange={e => setFile(e.target.files?.[0] || null)}
                                />
                                <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4 group-hover:text-blue-500 transition-colors" />
                                <p className="text-sm font-bold text-slate-600 dark:text-slate-300">
                                    {file ? file.name : "Clique ou arraste a planilha aqui"}
                                </p>
                                <p className="text-xs text-slate-400 mt-1">.csv, .xls, .xlsx</p>
                            </div>
                        </motion.div>
                    )}

                    {step === 3 && (
                        <motion.div key="step3" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="text-center">
                            <div className="w-20 h-20 bg-green-100 dark:bg-green-900/30 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                                <Check className="w-10 h-10" />
                            </div>
                            <h2 className="text-2xl font-black text-slate-800 dark:text-white mb-2">Tudo Pronto!</h2>
                            <p className="text-sm text-slate-500 mb-6">Seu ERP e PDV estão configurados. Você já pode realizar sua primeira venda.</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* NAVIGATION BUTTONS */}
            <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800 flex justify-between">
                <button 
                    onClick={prevStep}
                    disabled={step === 1 || loading}
                    className="flex items-center gap-2 px-6 py-3 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-xl font-bold uppercase text-xs tracking-widest hover:bg-slate-200 dark:hover:bg-slate-700 transition-all disabled:opacity-50"
                >
                    <ChevronLeft className="w-4 h-4" /> Voltar
                </button>
                
                {step < 2 ? (
                    <button 
                        onClick={nextStep}
                        className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-bold uppercase text-xs tracking-widest hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/20"
                    >
                        Avançar <ChevronRight className="w-4 h-4" />
                    </button>
                ) : step === 2 ? (
                    <button 
                        onClick={file ? handleUpload : nextStep}
                        disabled={loading}
                        className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-bold uppercase text-xs tracking-widest hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/20"
                    >
                        {loading ? 'Importando...' : file ? 'Importar' : 'Pular Importação'} <ChevronRight className="w-4 h-4" />
                    </button>
                ) : (
                    <button 
                        onClick={handleComplete}
                        className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl font-bold uppercase text-xs tracking-widest hover:bg-green-700 transition-all shadow-lg shadow-green-500/20"
                    >
                        Acessar PDV <Check className="w-4 h-4" />
                    </button>
                )}
            </div>
        </div>
    );
};

export default OnboardingWizard;
