// @ts-nocheck
import React, { useState, useEffect, useRef } from 'react';
import {
  Clock, Camera, MapPin, CheckCircle, AlertCircle, Calendar,
  TrendingUp, Users, BarChart3, Map, RefreshCw, Settings
} from 'lucide-react';
import { pontoService, RegistroPonto, ConfiguracaoHorario, EstatisticasPonto } from './pontoService';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

const PontoPage: React.FC = () => {
  const [registrosHoje, setRegistrosHoje] = useState<RegistroPonto[]>([]);
  const [configuracao, setConfiguracao] = useState<ConfiguracaoHorario | null>(null);
  const [estatisticas, setEstatisticas] = useState<EstatisticasPonto | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [foto, setFoto] = useState<string | null>(null);
  const [localizacao, setLocalizacao] = useState<{ latitude: number; longitude: number } | null>(null);
  const [tipoRegistroSelecionado, setTipoRegistroSelecionado] = useState<string | null>(null);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    carregarDados();
  }, []);

  const carregarDados = async () => {
    try {
      setLoading(true);
      const [pontosResponse, estatisticasResponse] = await Promise.all([
        pontoService.obterPontosHoje(),
        pontoService.obterEstatisticas()
      ]);
      
      if (pontosResponse.success) {
        setRegistrosHoje(pontosResponse.data.registros);
        setConfiguracao(pontosResponse.data.configuracao);
      }
      
      if (estatisticasResponse.success) {
        setEstatisticas(estatisticasResponse.data);
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const obterLocalizacao = (): Promise<{ latitude: number; longitude: number }> => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocalização não suportada'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          });
        },
        (error) => reject(error),
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    });
  };

  const iniciarCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'user', width: 640, height: 480 } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
      }
      
      setShowCamera(true);
    } catch (error) {
      console.error('Erro ao acessar câmera:', error);
      alert('Não foi possível acessar a câmera. Verifique as permissões.');
    }
  };

  const pararCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setShowCamera(false);
  };

  const tirarFoto = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      if (context) {
        canvasRef.current.width = videoRef.current.videoWidth;
        canvasRef.current.height = videoRef.current.videoHeight;
        context.drawImage(videoRef.current, 0, 0);
        const fotoBase64 = canvasRef.current.toDataURL('image/jpeg', 0.8);
        setFoto(fotoBase64);
        pararCamera();
      }
    }
  };

  const registrarPonto = async (tipoRegistro: string) => {
    try {
      setLoading(true);
      setTipoRegistroSelecionado(tipoRegistro);

      // Obter localização
      let loc = null;
      try {
        loc = await obterLocalizacao();
        setLocalizacao(loc);
      } catch (error) {
        console.error('Erro ao obter localização:', error);
        if (configuracao?.exigir_localizacao) {
          alert('É necessário permitir acesso à localização para registrar o ponto.');
          setLoading(false);
          return;
        }
      }

      // Tirar foto se necessário
      if (configuracao?.exigir_foto && !foto) {
        await iniciarCamera();
        setLoading(false);
        return; // Aguarda usuário tirar foto
      }

      // Registrar ponto
      const dados = {
        tipo_registro: tipoRegistro,
        latitude: loc?.latitude,
        longitude: loc?.longitude,
        foto: foto || undefined,
        dispositivo: navigator.userAgent
      };

      const response = await pontoService.registrarPonto(dados);
      
      if (response.success) {
        alert(response.message);
        setFoto(null);
        setLocalizacao(null);
        setTipoRegistroSelecionado(null);
        await carregarDados();
      }
    } catch (error: any) {
      console.error('Erro ao registrar ponto:', error);
      alert(error.response?.data?.message || 'Erro ao registrar ponto');
    } finally {
      setLoading(false);
    }
  };

  const confirmarRegistroComFoto = async () => {
    if (tipoRegistroSelecionado && foto) {
      await registrarPonto(tipoRegistroSelecionado);
    }
  };

  const jaRegistrou = (tipo: string) => {
    return registrosHoje.some(r => r.tipo_registro === tipo);
  };

  const getTipoLabel = (tipo: string) => {
    const labels = {
      'entrada': 'Entrada',
      'saida_almoco': 'Saída Almoço',
      'retorno_almoco': 'Retorno Almoço',
      'saida': 'Saída'
    };
    return labels[tipo] || tipo;
  };

  const getHorarioEsperado = (tipo: string) => {
    if (!configuracao) return '';
    const horarios = {
      'entrada': configuracao.hora_entrada,
      'saida_almoco': configuracao.hora_saida_almoco,
      'retorno_almoco': configuracao.hora_retorno_almoco,
      'saida': configuracao.hora_saida
    };
    return horarios[tipo] || '';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4 md:p-6">
      {/* HEADER */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 flex items-center gap-3">
              <Clock className="w-10 h-10 text-blue-600" />
              Controle de Ponto
            </h1>
            <p className="text-gray-600 mt-2">
              Registre sua entrada, saídas e retornos com foto e localização
            </p>
          </div>
          <button
            onClick={carregarDados}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Atualizar
          </button>
        </div>
      </div>

      {/* MODAL DE CÂMERA */}
      {showCamera && (
        <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Tire sua foto</h3>
            <div className="relative">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full rounded-lg"
              />
              <canvas ref={canvasRef} className="hidden" />
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={tirarFoto}
                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
              >
                <Camera className="w-5 h-5" />
                Capturar Foto
              </button>
              <button
                onClick={pararCamera}
                className="px-6 py-3 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PREVIEW DA FOTO */}
      {foto && !showCamera && (
        <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Confirmar foto</h3>
            <img src={foto} alt="Preview" className="w-full rounded-lg mb-4" />
            <div className="flex gap-3">
              <button
                onClick={confirmarRegistroComFoto}
                disabled={loading}
                className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <CheckCircle className="w-5 h-5" />
                {loading ? 'Registrando...' : 'Confirmar e Registrar'}
              </button>
              <button
                onClick={() => setFoto(null)}
                className="px-6 py-3 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                Tirar Novamente
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BOTÕES DE REGISTRO */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { tipo: 'entrada', label: 'Entrada', icon: '🌅', color: 'from-green-500 to-emerald-600' },
          { tipo: 'saida_almoco', label: 'Saída Almoço', icon: '🍽️', color: 'from-orange-500 to-red-600' },
          { tipo: 'retorno_almoco', label: 'Retorno Almoço', icon: '🔙', color: 'from-blue-500 to-cyan-600' },
          { tipo: 'saida', label: 'Saída', icon: '🌙', color: 'from-purple-500 to-pink-600' }
        ].map((item) => {
          const registrado = jaRegistrou(item.tipo);
          const registro = registrosHoje.find(r => r.tipo_registro === item.tipo);
          
          return (
            <button
              key={item.tipo}
              onClick={() => !registrado && registrarPonto(item.tipo)}
              disabled={registrado || loading}
              className={`relative p-6 rounded-2xl shadow-xl transform transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
                registrado ? 'bg-gray-200' : `bg-gradient-to-r ${item.color}`
              }`}
            >
              {registrado && (
                <div className="absolute top-2 right-2">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
              )}
              
              <div className="text-center">
                <div className="text-4xl mb-2">{item.icon}</div>
                <h3 className={`text-xl font-bold mb-2 ${registrado ? 'text-gray-700' : 'text-white'}`}>
                  {item.label}
                </h3>
                
                {configuracao && (
                  <p className={`text-sm mb-2 ${registrado ? 'text-gray-600' : 'text-white/90'}`}>
                    Horário: {getHorarioEsperado(item.tipo)}
                  </p>
                )}
                
                {registrado && registro && (
                  <div className="mt-3 p-2 bg-white rounded-lg">
                    <p className="text-sm font-semibold text-gray-900">
                      Registrado às {registro.hora}
                    </p>
                    {registro.status === 'atrasado' && (
                      <p className="text-xs text-red-600 mt-1">
                        ⚠️ Atraso de {registro.minutos_atraso} min
                      </p>
                    )}
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* ESTATÍSTICAS */}
      {estatisticas && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* GRÁFICO DE FREQUÊNCIA */}
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-6 h-6 text-blue-600" />
              Frequência (Últimos 30 dias)
            </h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={estatisticas.grafico_frequencia}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="data" 
                    tick={{ fontSize: 10 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis />
                  <Tooltip 
                    content={({ payload }) => {
                      if (payload && payload.length > 0) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white p-3 shadow-xl rounded-lg border">
                            <p className="font-bold">{data.data}</p>
                            <p className="text-sm">Registros: {data.total_registros}</p>
                            {data.teve_atraso && (
                              <p className="text-sm text-red-600">
                                ⚠️ Atraso: {data.minutos_atraso} min
                              </p>
                            )}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar 
                    dataKey="total_registros" 
                    fill="#3B82F6"
                    radius={[8, 8, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* RESUMO ESTATÍSTICAS */}
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm opacity-90">Taxa de Presença</p>
                  <p className="text-4xl font-bold">{estatisticas.taxa_presenca}%</p>
                  <p className="text-sm mt-2">{estatisticas.dias_trabalhados} dias trabalhados</p>
                </div>
                <TrendingUp className="w-16 h-16 opacity-50" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-red-500 to-orange-600 rounded-2xl shadow-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm opacity-90">Total de Atrasos</p>
                  <p className="text-4xl font-bold">{estatisticas.total_atrasos}</p>
                  <p className="text-sm mt-2">{estatisticas.minutos_atraso_total} minutos no total</p>
                </div>
                <AlertCircle className="w-16 h-16 opacity-50" />
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h4 className="font-bold text-gray-900 mb-3">Registros por Tipo</h4>
              <div className="space-y-2">
                {Object.entries(estatisticas.frequencia_tipo).map(([tipo, count]) => (
                  <div key={tipo} className="flex justify-between items-center">
                    <span className="text-gray-700">{getTipoLabel(tipo)}</span>
                    <span className="font-bold text-blue-600">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* REGISTROS DE HOJE */}
      <div className="bg-white rounded-2xl shadow-xl p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Calendar className="w-6 h-6 text-blue-600" />
          Registros de Hoje
        </h3>
        
        {registrosHoje.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Nenhum registro hoje. Registre seu primeiro ponto!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {registrosHoje.map((registro) => (
              <div
                key={registro.id}
                className={`p-4 rounded-lg border-2 ${
                  registro.status === 'atrasado' 
                    ? 'border-red-300 bg-red-50' 
                    : 'border-green-300 bg-green-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                      registro.status === 'atrasado' ? 'bg-red-500' : 'bg-green-500'
                    }`}>
                      <Clock className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="font-bold text-gray-900">{getTipoLabel(registro.tipo_registro)}</p>
                      <p className="text-sm text-gray-600">Horário: {registro.hora}</p>
                      {registro.status === 'atrasado' && (
                        <p className="text-sm text-red-600 font-semibold">
                          ⚠️ Atraso de {registro.minutos_atraso} minutos
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {registro.foto_url && (
                      <div className="w-16 h-16 rounded-lg overflow-hidden border-2 border-gray-300">
                        <img 
                          src={registro.foto_url} 
                          alt="Foto do registro" 
                          className="w-full h-full object-cover"
                        />
                      </div>
                    )}
                    {registro.latitude && registro.longitude && (
                      <div className="text-green-600">
                        <MapPin className="w-6 h-6" />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PontoPage;
