import React, { useState, useEffect } from 'react';
import {
    Users,
    Mail,
    MessageCircle,
    Calendar,
    ArrowRight,
    Search,
    Filter,
    RefreshCw
} from 'lucide-react';
import { Lead } from '../../types';
import { apiClient } from '../../api/apiClient';
import { toast } from 'react-hot-toast';

const LeadDashboard: React.FC = () => {
    const [leads, setLeads] = useState<Lead[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchLeads = async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/saas/leads');
            if (response.data.success) {
                setLeads(response.data.data);
            }
        } catch (error) {
            console.error('Erro ao buscar leads:', error);
            toast.error('Erro ao carregar lista de interessados.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLeads();
    }, []);

    const filteredLeads = leads.filter(lead =>
        lead.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.whatsapp.includes(searchTerm)
    );

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-3xl font-black text-gray-900 dark:text-white flex items-center gap-3">
                        <Users className="w-10 h-10 text-blue-600" />
                        Gestão de Leads
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Acompanhe os interessados capturados através da Landing Page.
                    </p>
                </div>
                <button
                    onClick={fetchLeads}
                    disabled={loading}
                    className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-2 rounded-xl text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all font-bold shadow-sm"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Atualizar
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-blue-600 rounded-3xl p-6 text-white shadow-xl shadow-blue-500/20">
                    <p className="text-blue-100 font-bold uppercase tracking-widest text-xs mb-2">Total de Leads</p>
                    <h3 className="text-4xl font-black">{leads.length}</h3>
                </div>
                <div className="bg-emerald-600 rounded-3xl p-6 text-white shadow-xl shadow-emerald-500/20">
                    <p className="text-emerald-100 font-bold uppercase tracking-widest text-xs mb-2">Consultas Pendentes</p>
                    <h3 className="text-4xl font-black">{leads.length}</h3>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                    <p className="text-gray-400 font-bold uppercase tracking-widest text-xs mb-2">Origem Landing Page</p>
                    <h3 className="text-4xl font-black text-gray-900 dark:text-white">100%</h3>
                </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-[2.5rem] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex flex-col md:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Buscar por nome, email ou whatsapp..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-gray-50 dark:bg-gray-900 border-none rounded-2xl py-4 pl-12 pr-6 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 transition-all"
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-gray-50 dark:bg-gray-900/50">
                                <th className="px-6 py-5 text-xs font-black text-gray-400 uppercase tracking-widest">Lead</th>
                                <th className="px-6 py-5 text-xs font-black text-gray-400 uppercase tracking-widest">Contato</th>
                                <th className="px-6 py-5 text-xs font-black text-gray-400 uppercase tracking-widest">Data</th>
                                <th className="px-6 py-5 text-xs font-black text-gray-400 uppercase tracking-widest text-right">Ação</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                            {loading ? (
                                Array(3).fill(0).map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={4} className="px-6 py-8 bg-gray-50/50 dark:bg-gray-800/50"></td>
                                    </tr>
                                ))
                            ) : filteredLeads.length > 0 ? (
                                filteredLeads.map((lead) => (
                                    <tr key={lead.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-colors">
                                        <td className="px-6 py-6">
                                            <div className="flex items-center gap-3">
                                                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-2xl flex items-center justify-center font-black text-xl">
                                                    {lead.nome.charAt(0).toUpperCase()}
                                                </div>
                                                <div>
                                                    <p className="font-bold text-gray-900 dark:text-white uppercase text-sm tracking-tight">{lead.nome}</p>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400">{lead.origem}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-6">
                                            <div className="space-y-1">
                                                <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                                                    <Mail className="w-4 h-4 text-gray-400" />
                                                    {lead.email}
                                                </div>
                                                <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                                                    <MessageCircle className="w-4 h-4 text-emerald-500" />
                                                    {lead.whatsapp}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-6">
                                            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                                                <Calendar className="w-4 h-4" />
                                                {new Date(lead.data_cadastro).toLocaleDateString('pt-BR', {
                                                    day: '2-digit',
                                                    month: 'long',
                                                    year: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </div>
                                        </td>
                                        <td className="px-6 py-6 text-right">
                                            <a
                                                href={`https://wa.me/${lead.whatsapp.replace(/\D/g, '')}?text=Olá ${lead.nome}, sou do MercadinhoSys. Recebemos seu interesse em nosso sistema.`}
                                                target="_blank"
                                                rel="noreferrer"
                                                className="inline-flex items-center gap-2 bg-emerald-500 text-white px-5 py-2.5 rounded-xl font-bold text-sm hover:bg-emerald-600 hover:scale-105 active:scale-95 transition-all shadow-lg shadow-emerald-500/20"
                                            >
                                                Atender
                                                <ArrowRight className="w-4 h-4" />
                                            </a>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={4} className="px-6 py-20 text-center">
                                        <div className="max-w-xs mx-auto">
                                            <Search className="w-12 h-12 text-gray-200 dark:text-gray-700 mx-auto mb-4" />
                                            <p className="text-gray-400 font-bold uppercase tracking-widest text-xs">Nenhum lead encontrado</p>
                                            <p className="text-gray-500 dark:text-gray-500 text-sm mt-2">Os interessados que se cadastrarem na Landing Page aparecerão aqui.</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default LeadDashboard;
