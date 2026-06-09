// @ts-nocheck
import React from 'react';
import { Card, CardContent, Grid, Typography, Box, Divider } from '@mui/material';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import StarIcon from '@mui/icons-material/Star';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

interface CustomerDashboardProps {
  total: number;
  total_gasto: number;
  total_devido: number;
  melhor_cliente_nome: string;
  melhor_cliente_valor: number;
  maior_devedor_nome: string;
  maior_devedor_valor: number;
  rfmData?: any;
}

const metricColors = [
  '#1976d2', // azul
  '#2e7d32', // verde
  '#f57f17', // dourado
];

const segmentColors: Record<string, string> = {
  'Campeão': '#2e7d32',
  'Fiel': '#1976d2',
  'Regular': '#7b1fa2',
  'Risco': '#ed6c02',
  'Perdido': '#d32f2f'
};

const CustomerDashboard: React.FC<CustomerDashboardProps> = ({
  total,
  total_gasto,
  melhor_cliente_nome,
  melhor_cliente_valor,
  rfmData
}) => {
  const formatCurrency = (val: number) => {
    return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const metrics = [
    {
      label: 'Total de Clientes',
      value: total,
      subtext: 'Cadastrados na loja',
      color: metricColors[0],
      icon: <PeopleAltIcon fontSize="large" sx={{ opacity: 0.8 }} />
    },
    {
      label: 'Faturamento Total',
      value: formatCurrency(total_gasto),
      subtext: 'Soma de todas as compras',
      color: metricColors[1],
      icon: <AttachMoneyIcon fontSize="large" sx={{ opacity: 0.8 }} />
    },
    {
      label: 'Melhor Cliente',
      value: melhor_cliente_nome,
      subtext: `Gasto: ${formatCurrency(melhor_cliente_valor)}`,
      color: metricColors[2],
      icon: <StarIcon fontSize="large" sx={{ opacity: 0.8 }} />
    }
  ];

  const renderSegmentCards = () => {
    if (!rfmData || !rfmData.segments) return null;
    const segments = rfmData.segments;
    return (
      <Box mt={3} p={3} sx={{ bgcolor: '#f8fafc', borderRadius: 2, border: '1px solid #e2e8f0' }}>
        <Typography variant="h6" fontWeight={700} sx={{ color: '#334155', mb: 2 }}>
          Segmentação de Clientes (RFM)
        </Typography>
        <Grid container spacing={2}>
          {Object.entries(segments).map(([segment, count]) => {
             const color = segmentColors[segment] || '#94a3b8';
             return (
              <Grid item xs={12} sm={6} md={2.4} key={segment}>
                <Card sx={{ borderLeft: `4px solid ${color}`, boxShadow: 1, '&:hover': { boxShadow: 3 } }}>
                  <CardContent sx={{ p: '12px !important' }}>
                    <Typography variant="subtitle2" sx={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: 0.5 }}>{segment}</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, color: '#0f172a' }}>{count as number}</Typography>
                  </CardContent>
                </Card>
              </Grid>
             );
          })}
        </Grid>
        <Typography variant="caption" sx={{ mt: 2, display: 'block', color: '#94a3b8' }}>
          * Baseado no histórico dos últimos {rfmData.window_days} dias. (Recência, Frequência, Monetário).
        </Typography>
      </Box>
    );
  };

  return (
    <Box mb={4}>
      <Grid container spacing={2}>
        {metrics.map((m, index) => (
          <Grid item key={index} xs={12} md={4}>
            <Card
              sx={{
                background: `linear-gradient(135deg, ${m.color} 0%, ${m.color}dd 100%)`,
                color: '#fff',
                minHeight: 110,
                boxShadow: 2,
                position: 'relative',
                overflow: 'hidden',
                '&:hover': { transform: 'translateY(-2px)' },
                transition: 'transform 0.2s'
              }}
            >
              <Box sx={{ position: 'absolute', right: -15, top: -15, opacity: 0.2, transform: 'scale(2.5)' }}>
                {m.icon}
              </Box>
              <CardContent sx={{ position: 'relative', zIndex: 1, p: 2, pb: '16px !important' }}>
                <Typography variant="caption" fontWeight={600} sx={{ textTransform: 'uppercase', letterSpacing: 1, opacity: 0.9 }}>
                  {m.label}
                </Typography>
                <Typography fontWeight={800} sx={{ mt: 1, mb: 0.5, lineHeight: 1.1, fontSize: { xs: '1.2rem', sm: '1.4rem', md: '1.6rem' }, wordBreak: 'break-word', whiteSpace: 'normal' }}>
                  {m.value}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8, fontSize: '0.75rem', fontWeight: 500 }}>
                  {m.subtext}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      {renderSegmentCards()}
    </Box>
  );
};

export default CustomerDashboard;
