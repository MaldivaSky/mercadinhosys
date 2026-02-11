import React, { useState, useEffect } from 'react';
import { Gift, Plus, Trash2, Edit2, DollarSign, Calendar, AlertCircle } from 'lucide-react';
import { apiClient } from '../../../api/apiClient';

interface Beneficio {
  id: number;
  funcionario_id: number;
  nome_beneficio: string;
  tipo: 'vale_refeicao' | 'vale_transporte' | 'vale_alimentacao' | 'seguro_saude' | 'outro';
  valor_mensal: number;
  data_inicio: string;
  data_fim?: string;
  ativo: boolean;
  observacao?: string;
}

interface Funcionario {
  id: number;
  nome: string;
  cargo: string;
}

export default function BeneficiosFuncionario() {
  const [beneficios, setBeneficios] = useState<Beneficio[]>([]);
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [filtroFuncionario, setFiltroFuncionario] = useState<string>('');
  const [filtroAtivos, setFiltroAtivos] = useState<string>('true');
  
  const [modalAberto, setModalAberto] = useState(false);
  const [novoBeneficio, setNovoBeneficio] = useState({
    funcionario_id: '',
    nome_beneficio: '',
    tipo: 'vale_refeicao' as any,
    valor_mensal: '',
    data_inicio: new Date().toISOString().split('T')[0],
    data_fim: '',
    observacao: ''
  });

  useEffect(() => {
    loadFuncionarios();
    loadBeneficios();
  }, [filtroFuncionario, filtroAtivos]);

  const loadFuncionarios = async () => {
    try {
      const response = await apiClient.get('/funcionarios');
      const items = response?.data?.data || response?.data?.funcionarios || [];
      setFuncionarios(Array.isArray(items) ? items : []);
    } catch (err) {
      console.error('Erro ao carregar funcionários:', err);
    }
  };

  const loadBeneficios = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filtroFuncionario) params.funcionario_id = filtroFuncionario;
      if (filtroAtivos) params.ativo = filtroAtivos === 'true';
      
      const response = await apiClient.get('/rh/beneficios', { params });
      setBeneficios(response.data?.data || []);
    } catch (err: any) {
      console.error('Erro ao carregar benefícios:', err);
      setError(err.message);
