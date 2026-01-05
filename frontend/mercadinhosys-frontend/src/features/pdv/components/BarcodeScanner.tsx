import React, { useState, useEffect, useRef } from 'react';
import { Camera, X, Scan, Keyboard } from 'lucide-react';

interface BarcodeScannerProps {
    onScan: (codigo: string) => void;
    onClose: () => void;
}

const BarcodeScanner: React.FC<BarcodeScannerProps> = ({ onScan, onClose }) => {
    const [modoEntrada, setModoEntrada] = useState<'camera' | 'manual'>('manual');
    const [codigoManual, setCodigoManual] = useState('');
    const [erro, setErro] = useState<string | null>(null);
    const [cameraAtiva, setCameraAtiva] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);
    const streamRef = useRef<MediaStream | null>(null);

    // Cleanup da câmera ao desmontar
    useEffect(() => {
        return () => {
            pararCamera();
        };
    }, []);

    // Iniciar câmera
    const iniciarCamera = async () => {
        try {
            setErro(null);

            // Pedir permissão para câmera
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment', // Câmera traseira em celulares
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                }
            });

            streamRef.current = stream;

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                videoRef.current.play();
                setCameraAtiva(true);
            }

            // TODO: Integrar biblioteca de leitura de código de barras
            // Sugestões: 
            // - quagga2 (mais popular)
            // - @zxing/library (ZXing TypeScript)
            // - html5-qrcode
            
            setErro('Scanner de câmera em desenvolvimento. Use entrada manual por enquanto.');
            
        } catch (error: any) {
            console.error('Erro ao acessar câmera:', error);
            setErro(`Erro ao acessar câmera: ${error.message}`);
            setModoEntrada('manual');
        }
    };

    // Parar câmera
    const pararCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        setCameraAtiva(false);
    };

    // Mudar modo
    const handleModoChange = (modo: 'camera' | 'manual') => {
        setModoEntrada(modo);
        setErro(null);

        if (modo === 'camera') {
            iniciarCamera();
        } else {
            pararCamera();
        }
    };

    // Enviar código manual
    const handleEnviarManual = (e: React.FormEvent) => {
        e.preventDefault();
        
        if (codigoManual.trim()) {
            onScan(codigoManual.trim());
            setCodigoManual('');
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                            <Scan className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-800 dark:text-white">
                                Scanner de Código de Barras
                            </h2>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                Use a câmera ou digite manualmente
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
                    >
                        <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                    </button>
                </div>

                {/* Seletor de Modo */}
                <div className="p-6 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex space-x-3">
                        <button
                            onClick={() => handleModoChange('manual')}
                            className={`flex-1 py-3 px-4 rounded-lg font-medium flex items-center justify-center space-x-2 transition ${
                                modoEntrada === 'manual'
                                    ? 'bg-blue-500 text-white shadow-lg'
                                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600'
                            }`}
                        >
                            <Keyboard className="w-5 h-5" />
                            <span>Digitar Código</span>
                        </button>

                        <button
                            onClick={() => handleModoChange('camera')}
                            className={`flex-1 py-3 px-4 rounded-lg font-medium flex items-center justify-center space-x-2 transition ${
                                modoEntrada === 'camera'
                                    ? 'bg-blue-500 text-white shadow-lg'
                                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600'
                            }`}
                        >
                            <Camera className="w-5 h-5" />
                            <span>Usar Câmera</span>
                        </button>
                    </div>
                </div>

                {/* Conteúdo */}
                <div className="p-6">
                    {/* MODO MANUAL */}
                    {modoEntrada === 'manual' && (
                        <form onSubmit={handleEnviarManual} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    Digite o código de barras
                                </label>
                                <input
                                    type="text"
                                    value={codigoManual}
                                    onChange={(e) => setCodigoManual(e.target.value)}
                                    placeholder="Ex: 7891234567890"
                                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg font-mono bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                                    autoFocus
                                />
                                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                                    💡 Dica: Use um leitor de código de barras USB para entrada rápida
                                </p>
                            </div>

                            <button
                                type="submit"
                                disabled={!codigoManual.trim()}
                                className={`w-full py-3 rounded-lg font-semibold flex items-center justify-center space-x-2 transition ${
                                    codigoManual.trim()
                                        ? 'bg-green-500 hover:bg-green-600 text-white'
                                        : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                                }`}
                            >
                                <Scan className="w-5 h-5" />
                                <span>Buscar Produto</span>
                            </button>
                        </form>
                    )}

                    {/* MODO CÂMERA */}
                    {modoEntrada === 'camera' && (
                        <div className="space-y-4">
                            {erro ? (
                                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                                    <div className="flex items-start space-x-3">
                                        <Camera className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                                        <div>
                                            <h4 className="font-medium text-yellow-800 dark:text-yellow-300 mb-1">
                                                Funcionalidade em Desenvolvimento
                                            </h4>
                                            <p className="text-sm text-yellow-700 dark:text-yellow-400">
                                                {erro}
                                            </p>
                                            <p className="text-sm text-yellow-600 dark:text-yellow-500 mt-2">
                                                Para implementar, instale uma destas bibliotecas:
                                            </p>
                                            <ul className="mt-2 text-sm text-yellow-600 dark:text-yellow-500 list-disc list-inside">
                                                <li><code>npm install quagga</code> (Quagga2)</li>
                                                <li><code>npm install @zxing/library</code> (ZXing)</li>
                                                <li><code>npm install html5-qrcode</code></li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
                                    <video
                                        ref={videoRef}
                                        className="w-full h-full object-cover"
                                        playsInline
                                    />
                                    
                                    {cameraAtiva && (
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            {/* Guia de alinhamento */}
                                            <div className="w-64 h-32 border-4 border-green-500 rounded-lg shadow-lg">
                                                <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-green-400"></div>
                                                <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-green-400"></div>
                                                <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-green-400"></div>
                                                <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-green-400"></div>
                                            </div>
                                        </div>
                                    )}

                                    <div className="absolute bottom-4 left-0 right-0 flex justify-center">
                                        <div className="bg-black bg-opacity-75 px-4 py-2 rounded-full text-white text-sm">
                                            Alinhe o código de barras dentro da área verde
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                                <h4 className="font-medium text-blue-800 dark:text-blue-300 mb-2">
                                    📱 Compatibilidade
                                </h4>
                                <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
                                    <li>✅ Funciona em smartphones e tablets modernos</li>
                                    <li>✅ Requer HTTPS (conexão segura)</li>
                                    <li>✅ Permissão de câmera necessária</li>
                                    <li>⚠️ Use entrada manual como alternativa</li>
                                </ul>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                        <div className="flex items-center space-x-2">
                            <Scan className="w-4 h-4" />
                            <span>Suporta EAN-13, EAN-8, UPC, Code-128</span>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-blue-600 dark:text-blue-400 hover:underline"
                        >
                            Fechar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BarcodeScanner;
