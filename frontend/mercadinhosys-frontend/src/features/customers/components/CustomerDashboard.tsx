// @ts-nocheck
import React from 'react';
import { Card, CardContent, Typography, Box, Grid } from '@mui/material';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import StarIcon from '@mui/icons-material/Star';

interface CustomerDashboardProps {
  total: number;
  total_gasto: number;
  total_gasto_mes: number;
  total_devido: number;
  melhor_cliente_nome: string;
  melhor_cliente_valor: number;
  maior_devedor_nome: string;
  maior_devedor_valor: number;
  rfmData?: any;
  onSegmentClick?: (segment: string) => void;
}

const segmentColors: Record<string, string> = {
  'Campeão': '#22c55e',
  'Fiel': '#3b82f6',
  'Regular': '#8b5cf6',
  'Risco': '#f97316',
  'Perdido': '#ef4444'
};

const CustomerDashboard: React.FC<CustomerDashboardProps> = ({
  total,
  total_gasto,
  total_gasto_mes,
  melhor_cliente_nome,
  melhor_cliente_valor,
  rfmData,
  onSegmentClick
}) => {
  const formatCurrency = (val: number) => {
    return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const metrics = [
    {
      label: 'TOTAL DE CLIENTES',
      value: total,
      subtext: 'Cadastrados na loja',
      color: '#2563eb', // blue-600
      icon: <PeopleAltIcon sx={{ fontSize: 80, opacity: 0.15 }} />
    },
    {
      // "LTV" é jargão de marketing que o lojista não usa no dia a dia —
      // aqui é simplesmente tudo que a base de clientes já deixou na loja.
      label: 'TOTAL GASTO PELOS CLIENTES (DESDE SEMPRE)',
      value: formatCurrency(total_gasto),
      subtext: 'Soma de tudo que seus clientes já compraram, na história da loja',
      color: '#0f766e', // teal-700
      icon: <AttachMoneyIcon sx={{ fontSize: 80, opacity: 0.15 }} />
    },
    {
      // Antes era "mês calendário desde o dia 1" — no início de cada mês o
      // card parecia "quebrado" (dia 3 só somava 3 dias de venda). Últimos
      // 30 dias corridos dá uma leitura sempre justa, todo dia do mês.
      label: 'RECEITA DOS ÚLTIMOS 30 DIAS',
      value: formatCurrency(total_gasto_mes),
      subtext: 'Compras de clientes identificados nos últimos 30 dias',
      color: '#16a34a', // green-600
      icon: <AttachMoneyIcon sx={{ fontSize: 80, opacity: 0.15 }} />
    },
    {
      label: 'MELHOR CLIENTE (DESDE SEMPRE)',
      value: melhor_cliente_nome,
      subtext: `Já gastou ${formatCurrency(melhor_cliente_valor)} na loja, no total`,
      color: '#ea580c', // orange-600
      icon: <StarIcon sx={{ fontSize: 80, opacity: 0.15 }} />
    }
  ];

  const renderSegmentCards = () => {
    if (!rfmData || !rfmData.segments) return null;
    const segments = rfmData.segments;
    return (
      <Box sx={{ mt: 3, p: 3, bgcolor: 'background.paper', borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ fontWeight: 800, mb: 2, color: 'text.primary' }}>
          Segmentação de Clientes (RFM)
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)', lg: 'repeat(5, 1fr)' }, gap: 2 }}>
          {Object.entries(segments).map(([segment, count]) => {
             const color = segmentColors[segment] || '#94a3b8';
             return (
               <Card 
                 key={segment}
                 onClick={() => onSegmentClick && onSegmentClick(segment)}
                 sx={{ 
                   cursor: onSegmentClick ? 'pointer' : 'default',
                   border: '1px solid',
                   borderColor: 'divider',
                   borderBottom: `4px solid ${color}`, 
                   bgcolor: 'background.default',
                   transition: 'all 0.2s',
                   '&:hover': onSegmentClick ? { 
                     transform: 'translateY(-2px)',
                     boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                   } : {}
                 }}
               >
                 <CardContent sx={{ p: '16px !important' }}>
                   <Typography variant="overline" sx={{ color: 'text.secondary', fontWeight: 700, letterSpacing: 1, display: 'block', mb: 1 }}>
                     {segment}
                   </Typography>
                   <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary' }}>
                     {count as number}
                   </Typography>
                 </CardContent>
               </Card>
             );
          })}
        </Box>
        <Typography variant="caption" sx={{ mt: 3, display: 'block', color: 'text.secondary' }}>
          * Baseado no histórico dos últimos {rfmData.window_days} dias. (Recência, Frequência, Monetário).
        </Typography>
      </Box>
    );
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2 }}>
        {metrics.map((m, index) => (
          <Card
            key={index}
            sx={{
              bgcolor: m.color,
              color: '#fff',
              minHeight: 120,
              position: 'relative',
              overflow: 'hidden',
              borderRadius: 3,
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
            }}
          >
            <Box sx={{ position: 'absolute', right: -10, top: '50%', transform: 'translateY(-50%)' }}>
              {m.icon}
            </Box>
            <CardContent sx={{ position: 'relative', zIndex: 1, p: 3, pb: '24px !important' }}>
              <Typography variant="overline" sx={{ fontWeight: 800, letterSpacing: 1, opacity: 0.9 }}>
                {m.label}
              </Typography>
              <Typography variant="h4" sx={{ mt: 1, mb: 0.5, fontWeight: 900, wordBreak: 'break-word' }}>
                {m.value}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8, fontWeight: 500 }}>
                {m.subtext}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Box>
      
      {renderSegmentCards()}
    </Box>
  );
};

export default CustomerDashboard;
