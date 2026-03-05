import React from 'react';
import { Card, CardContent, Grid, Typography, Box } from '@mui/material';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import MoneyOffIcon from '@mui/icons-material/MoneyOff';
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
}

const metricColors = [
  '#0288d1', // azul (Total Clientes)
  '#2e7d32', // verde (Total Gasto)
  '#c62828', // vermelho (Total Devido)
  '#f57f17', // dourado (Melhor Cliente)
  '#d84315', // laranja escuro (Maior Devedor)
];

const CustomerDashboard: React.FC<CustomerDashboardProps> = ({
  total,
  total_gasto,
  total_devido,
  melhor_cliente_nome,
  melhor_cliente_valor,
  maior_devedor_nome,
  maior_devedor_valor
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
      label: 'Valor Total Gasto',
      value: formatCurrency(total_gasto),
      subtext: 'Soma de todas as compras',
      color: metricColors[1],
      icon: <AttachMoneyIcon fontSize="large" sx={{ opacity: 0.8 }} />
    },
    {
      label: 'Valor Total Devido',
      value: formatCurrency(total_devido),
      subtext: 'Total pendente em fiado',
      color: metricColors[2],
      icon: <MoneyOffIcon fontSize="large" sx={{ opacity: 0.8 }} />
    },
    {
      label: 'Melhor Cliente',
      value: melhor_cliente_nome,
      subtext: `Gasto: ${formatCurrency(melhor_cliente_valor)}`,
      color: metricColors[3],
      icon: <StarIcon fontSize="large" sx={{ opacity: 0.8 }} />
    },
    {
      label: 'Maior Devedor',
      value: maior_devedor_nome,
      subtext: `Dívida: ${formatCurrency(maior_devedor_valor)}`,
      color: metricColors[4],
      icon: <WarningAmberIcon fontSize="large" sx={{ opacity: 0.8 }} />
    },
  ];

  return (
    <Box mb={4}>
      <Grid container spacing={2}>
        {metrics.map((m, index) => (
          <Grid key={index} sx={{ flex: 1, minWidth: 180, maxWidth: 300, display: 'flex' }}>
            <Card
              sx={{
                background: `linear-gradient(135deg, ${m.color} 0%, ${m.color}dd 100%)`,
                color: '#fff',
                minHeight: 120,
                width: '100%',
                boxShadow: 3,
                transition: 'all 0.2s',
                position: 'relative',
                overflow: 'hidden',
                '&:hover': {
                  boxShadow: 8,
                  transform: 'translateY(-4px)',
                },
              }}
              elevation={3}
            >
              <Box sx={{ position: 'absolute', right: -15, top: -15, opacity: 0.2, transform: 'scale(2.5)' }}>
                {m.icon}
              </Box>
              <CardContent sx={{ position: 'relative', zIndex: 1, p: 2, pb: '16px !important' }}>
                <Typography variant="caption" fontWeight={600} sx={{ textTransform: 'uppercase', letterSpacing: 1, opacity: 0.9 }}>
                  {m.label}
                </Typography>
                <Typography variant="h5" fontWeight={800} sx={{ mt: 1, mb: 0.5, lineHeight: 1.1, whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
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
    </Box>
  );
};

export default CustomerDashboard;
