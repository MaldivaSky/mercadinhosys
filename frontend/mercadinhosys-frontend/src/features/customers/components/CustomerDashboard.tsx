import React from 'react';
import { Card, CardContent, Grid, Typography, Box, Tooltip } from '@mui/material';

interface CustomerDashboardProps {
  total: number;
  ativos: number;
  inativos: number;
  novos: number;
  vip: number;
  onFilter?: (filter: string | null) => void;
  activeFilter?: string | null;
}

const metricColors = [
  '#1976d2', // azul
  '#43a047', // verde
  '#e53935', // vermelho
  '#fbc02d', // amarelo
  '#8e24aa', // roxo
];

const CustomerDashboard: React.FC<CustomerDashboardProps> = ({ total, ativos, inativos, novos, vip, onFilter, activeFilter }) => {
  const metrics = [
    { label: 'Total de Clientes', value: total, color: metricColors[0], filter: 'total', tooltip: 'Ver todos os clientes' },
    { label: 'Ativos', value: ativos, color: metricColors[1], filter: 'ativos', tooltip: 'Clientes ativos' },
    { label: 'Inativos', value: inativos, color: metricColors[2], filter: 'inativos', tooltip: 'Clientes inativos' },
    { label: 'Novos', value: novos, color: metricColors[3], filter: 'novos', tooltip: 'Clientes cadastrados recentemente' },
    { label: 'VIP', value: vip, color: metricColors[4], filter: 'vip', tooltip: 'Clientes VIP' },
  ];

  const handleClick = (filter: string) => {
    if (onFilter) {
      if (activeFilter === filter) {
        onFilter(null); // Desativa filtro se clicar de novo
      } else {
        onFilter(filter);
      }
    }
  };

  return (
    <Box mb={4}>
      <Grid container spacing={2} columns={5}>
        {metrics.map((m) => (
          <Grid key={m.label} sx={{ flex: 1, minWidth: 180, maxWidth: 300, display: 'flex' }}>
            <Tooltip title={m.tooltip} arrow>
              <Card
                role="button"
                tabIndex={0}
                aria-pressed={activeFilter === m.filter}
                sx={{
                  background: m.color,
                  color: '#fff',
                  minHeight: 110,
                  width: '100%',
                  cursor: 'pointer',
                  border: activeFilter === m.filter ? '3px solid #fff' : '2px solid transparent',
                  opacity: activeFilter && activeFilter !== m.filter ? 0.7 : 1,
                  boxShadow: activeFilter === m.filter ? 10 : 3,
                  transition: 'all 0.18s',
                  outline: 'none',
                  position: 'relative',
                  zIndex: activeFilter === m.filter ? 2 : 1,
                  filter: activeFilter === m.filter ? 'brightness(1.08)' : 'none',
                  '&:hover': {
                    boxShadow: 12,
                    filter: 'brightness(1.12)',
                    border: '3px solid #fff',
                    transform: 'scale(1.03)',
                  },
                  '&:focus': {
                    boxShadow: 12,
                    border: '3px solid #fff',
                  },
                }}
                elevation={activeFilter === m.filter ? 10 : 3}
                onClick={() => handleClick(m.filter)}
                onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && handleClick(m.filter)}
              >
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom sx={{ letterSpacing: 0.2 }}>
                    {m.label}
                  </Typography>
                  <Typography variant="h3" fontWeight={700} sx={{ lineHeight: 1.1 }}>
                    {m.value}
                  </Typography>
                </CardContent>
              </Card>
            </Tooltip>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default CustomerDashboard;
