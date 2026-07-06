import React, { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { authService } from '../auth/authService';
import { Smartphone, ShieldCheck, MapPin, Navigation, Info } from 'lucide-react';

const PortalEntregador: React.FC = () => {
    const [qrValue, setQrValue] = useState<string>('');
    const user = authService.getCurrentUser();

    useEffect(() => {
        const token = authService.getToken();
        // Construindo o Deep Link. Em produção, isso apontaria para o scheme do app (ex: mercadinhosys://rastreador)
        // ou para a URL do PWA. Usaremos a URL do Expo Web para Dev.
        const appUrl = `http://localhost:8081/?token=${token}`;
        setQrValue(appUrl);
    }, []);

    return (
        <div className="flex flex-col items-center justify-center py-12 px-4 max-w-4xl mx-auto">
            
            <div className="text-center mb-10">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 dark:bg-blue-900/30 text-blue-600 rounded-full mb-6">
                    <Navigation className="w-10 h-10" />
                </div>
                <h1 className="text-4xl font-black tracking-tight text-gray-900 dark:text-white mb-4">
                    Olá, {user?.nome || 'Entregador'}!
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
                    Para iniciar sua rota, você precisa acessar o <b>Painel do Entregador</b> no seu celular.
                    Escaneie o QR Code abaixo com a câmera do seu telefone para abrir o aplicativo instantaneamente e de forma segura, sem precisar digitar senhas.
                </p>
            </div>

            <div className="bg-white dark:bg-gray-800 p-8 rounded-3xl shadow-xl border border-gray-100 dark:border-gray-700 w-full flex flex-col md:flex-row items-center gap-10">
                
                {/* QR Code Section */}
                <div className="flex-1 flex flex-col items-center justify-center p-6 bg-gray-50 dark:bg-gray-900/50 rounded-2xl border border-gray-100 dark:border-gray-700">
                    <div className="bg-white p-4 rounded-2xl shadow-sm mb-6">
                        {qrValue ? (
                            <QRCodeSVG 
                                value={qrValue} 
                                size={220} 
                                level="H"
                                fgColor="#1e293b"
                                bgColor="#ffffff"
                                imageSettings={{
                                    src: "/vite.svg", // Opcional: Logo central
                                    x: undefined,
                                    y: undefined,
                                    height: 40,
                                    width: 40,
                                    excavate: true,
                                }}
                            />
                        ) : (
                            <div className="w-[220px] h-[220px] bg-gray-100 animate-pulse rounded-xl" />
                        )}
                    </div>
                    <p className="text-sm font-bold text-gray-500 uppercase tracking-widest text-center">
                        Aponte a câmera do celular
                    </p>
                </div>

                {/* Benefícios Section */}
                <div className="flex-1 space-y-6">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                        Por que usar o App?
                    </h3>
                    
                    <div className="flex items-start gap-4">
                        <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 rounded-xl flex items-center justify-center shrink-0">
                            <ShieldCheck className="w-5 h-5" />
                        </div>
                        <div>
                            <h4 className="font-bold text-gray-900 dark:text-white">Autenticação Segura</h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                O QR Code contém uma chave temporária. Você não precisa digitar e-mail e senha no celular, o acesso é instantâneo.
                            </p>
                        </div>
                    </div>

                    <div className="flex items-start gap-4">
                        <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 text-blue-600 rounded-xl flex items-center justify-center shrink-0">
                            <MapPin className="w-5 h-5" />
                        </div>
                        <div>
                            <h4 className="font-bold text-gray-900 dark:text-white">Auditoria de KM (Reembolso)</h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                O app registra seus KMs rodados offline. Sem internet? Não tem problema. Ele guarda tudo e garante que você receba o reembolso exato do seu deslocamento.
                            </p>
                        </div>
                    </div>

                    <div className="flex items-start gap-4">
                        <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 text-purple-600 rounded-xl flex items-center justify-center shrink-0">
                            <Smartphone className="w-5 h-5" />
                        </div>
                        <div>
                            <h4 className="font-bold text-gray-900 dark:text-white">Bateria Otimizada</h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                Design 100% focado em Dark Mode. Seu celular não vai descarregar no meio da rota. Além disso, botões integrados ao WhatsApp agilizam a sua entrega!
                            </p>
                        </div>
                    </div>
                </div>

            </div>
            
            <div className="mt-8 flex items-center gap-3 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 p-4 rounded-xl max-w-2xl text-sm">
                <Info className="w-5 h-5 shrink-0" />
                <p>
                    <strong>Atenção:</strong> Mantenha o GPS do celular ligado para contabilizar a distância. O acesso é pessoal e intransferível.
                </p>
            </div>

        </div>
    );
};

export default PortalEntregador;
