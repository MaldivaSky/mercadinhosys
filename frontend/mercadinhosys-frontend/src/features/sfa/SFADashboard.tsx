import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/apiClient';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { MapPin, UserCircle, RefreshCcw, ShoppingCart, DollarSign, Clock } from 'lucide-react';
import { showToast } from '../../utils/toast';

export default function SFADashboard() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [clientes, setClientes] = useState<any[]>([]);
    const [resumo, setResumo] = useState({ visitados: 0, total: 0, vendas_hoje: 0 });

    const loadData = async () => {
        try {
            setLoading(true);
            const res = await apiClient.get('/sfa/sync-data');
            
            if (res.data?.status === 'success') {
                const clientesData = res.data.data.clientes || [];
                setClientes(clientesData);
                
                // Salvar offline para o fluxo de pedido
                localStorage.setItem('@sfa_clientes', JSON.stringify(clientesData));
                localStorage.setItem('@sfa_produtos', JSON.stringify(res.data.data.produtos || []));
                localStorage.setItem('@sfa_tabelas', JSON.stringify(res.data.data.tabelas_preco || []));
                localStorage.setItem('@sfa_tabelas_itens', JSON.stringify(res.data.data.tabelas_preco_itens || []));
                
                setResumo({
                    visitados: 0,
                    total: clientesData.length,
                    vendas_hoje: 0
                });
                showToast.success('Roteiro atualizado com sucesso!');
            }
        } catch (error) {
            console.error('Erro ao sincronizar SFA:', error);
            // Fallback offline
            const offlineClientes = localStorage.getItem('@sfa_clientes');
            if (offlineClientes) {
                setClientes(JSON.parse(offlineClientes));
                showToast.update('Você está offline. Exibindo dados locais.');
            } else {
                showToast.error('Erro ao carregar roteiro.');
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const iniciarAtendimento = (cliente: any) => {
        navigate('/sfa/pedido', { state: { cliente } });
    };

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] bg-slate-50 dark:bg-slate-950 -m-6 p-4 overflow-y-auto">
            <div className="flex justify-between items-center mb-6 pt-2">
                <div>
                    <h1 className="text-2xl font-black text-slate-800 dark:text-slate-100">
                        Meu Roteiro
                    </h1>
                    <p className="text-sm text-slate-500">Força de Vendas SFA</p>
                </div>
                <Button variant="outline" size="icon" onClick={loadData} disabled={loading}>
                    <RefreshCcw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                </Button>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-lg shadow-blue-500/20">
                    <CardContent className="p-4 flex flex-col justify-between">
                        <div className="flex justify-between items-start mb-2">
                            <Clock className="w-6 h-6 opacity-80" />
                            <span className="text-xs font-medium bg-white/20 px-2 py-1 rounded-full">Hoje</span>
                        </div>
                        <div>
                            <p className="text-3xl font-black">{resumo.visitados} / {resumo.total}</p>
                            <p className="text-sm opacity-90 mt-1">Clientes Visitados</p>
                        </div>
                    </CardContent>
                </Card>
                
                <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white border-0 shadow-lg shadow-emerald-500/20">
                    <CardContent className="p-4 flex flex-col justify-between">
                        <div className="flex justify-between items-start mb-2">
                            <DollarSign className="w-6 h-6 opacity-80" />
                            <span className="text-xs font-medium bg-white/20 px-2 py-1 rounded-full">Hoje</span>
                        </div>
                        <div>
                            <p className="text-3xl font-black">R$ {resumo.vendas_hoje.toFixed(2)}</p>
                            <p className="text-sm opacity-90 mt-1">Vendas Totais</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="mb-4">
                <h2 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2 mb-3">
                    <MapPin className="w-5 h-5 text-blue-500" />
                    Clientes na Rota ({clientes.length})
                </h2>
                
                {loading && clientes.length === 0 ? (
                    <div className="flex justify-center p-8">
                        <RefreshCcw className="w-8 h-8 animate-spin text-blue-500" />
                    </div>
                ) : clientes.length === 0 ? (
                    <Card className="border-dashed">
                        <CardContent className="flex flex-col items-center justify-center py-10 text-slate-500">
                            <MapPin className="w-12 h-12 mb-3 text-slate-300" />
                            <p>Nenhum cliente no seu roteiro hoje.</p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-3 pb-20">
                        {clientes.map((c, idx) => (
                            <Card key={c.id || idx} className="overflow-hidden hover:shadow-md transition-shadow">
                                <CardContent className="p-0">
                                    <div className="p-4 flex items-start gap-3">
                                        <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                                            <UserCircle className="w-8 h-8 text-slate-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="font-bold text-slate-900 dark:text-white truncate">{c.nome}</h3>
                                            <p className="text-xs text-slate-500 truncate">{c.endereco_completo || c.cidade + '/' + c.estado}</p>
                                            
                                            <div className="flex items-center gap-3 mt-2 text-xs font-medium">
                                                <span className="text-emerald-600 bg-emerald-50 dark:bg-emerald-500/10 dark:text-emerald-400 px-2 py-0.5 rounded">
                                                    Limite: R$ {parseFloat(c.limite_credito || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                                </span>
                                                {c.saldo_devedor > 0 && (
                                                    <span className="text-amber-600 bg-amber-50 dark:bg-amber-500/10 dark:text-amber-400 px-2 py-0.5 rounded">
                                                        Devedor: R$ {parseFloat(c.saldo_devedor || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="bg-slate-50 dark:bg-slate-900/50 p-3 px-4 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center">
                                        <div className="text-xs text-slate-500">
                                            Última compra: {c.ultima_compra ? new Date(c.ultima_compra).toLocaleDateString() : 'N/A'}
                                        </div>
                                        <Button 
                                            size="sm" 
                                            onClick={() => iniciarAtendimento(c)}
                                            className="bg-blue-600 hover:bg-blue-700 shadow-sm"
                                        >
                                            <ShoppingCart className="w-4 h-4 mr-2" />
                                            Fazer Pedido
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
