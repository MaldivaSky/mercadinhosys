import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Divider, Card, CardContent, Grid, useTheme } from '@mui/material';
import Box from '@mui/material/Box';


interface CustomerDetailsModalProps {
  open: boolean;
  cliente: any | null;
  loading?: boolean;
  onClose: () => void;
  onEdit: (cliente: any) => void;
  onDelete: (cliente: any) => void;
}

const CustomerDetailsModal: React.FC<CustomerDetailsModalProps> = ({ open, cliente, loading, onClose, onEdit, onDelete }) => {
  const theme = useTheme();

  const labelStyle = { 
    fontWeight: 600, 
    color: theme.palette.primary.main,
    minWidth: 120 
  };

  const valueStyle = { 
    color: theme.palette.text.primary,
    fontWeight: 400 
  };
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Detalhes do Cliente</DialogTitle>
      <DialogContent dividers>
        {loading ? (
          <Typography>Carregando detalhes...</Typography>
        ) : cliente ? (
          <Grid container spacing={2}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Nome:</Typography> 
              <Typography sx={valueStyle}>{cliente.nome}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>CPF:</Typography> 
              <Typography sx={valueStyle}>{cliente.cpf || '-'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Telefone:</Typography> 
              <Typography sx={valueStyle}>{cliente.celular || cliente.telefone || '-'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Email:</Typography> 
              <Typography sx={valueStyle}>{cliente.email || '-'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Endereço:</Typography> 
              <Typography sx={valueStyle}>{cliente.endereco_completo || '-'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Data Cadastro:</Typography> 
              <Typography sx={valueStyle}>{cliente.data_cadastro ? new Date(cliente.data_cadastro).toLocaleDateString('pt-BR') : '-'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Total Compras:</Typography> 
              <Typography sx={valueStyle}>{cliente.total_compras ?? '-'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Limite Crédito:</Typography> 
              <Typography sx={{...valueStyle, color: '#2e7d32'}}>R$ {cliente.limite_credito?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) ?? '-'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Saldo Devedor:</Typography> 
              <Typography sx={{...valueStyle, color: cliente.saldo_devedor > 0 ? '#d32f2f' : '#2e7d32'}}>
                R$ {cliente.saldo_devedor?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) ?? '0,00'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Última Compra:</Typography> 
              <Typography sx={valueStyle}>{cliente.ultima_compra ? new Date(cliente.ultima_compra).toLocaleDateString('pt-BR') : '-'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}>
              <Typography sx={labelStyle}>Valor Total Gasto:</Typography> 
              <Typography sx={{...valueStyle, color: '#2e7d32', fontWeight: 500}}>
                R$ {cliente.valor_total_gasto?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) ?? '0,00'}
              </Typography>
            </Box>
          </Grid>
        ) : (
          <Typography>Cliente não encontrado.</Typography>
        )}
      </DialogContent>
      <Divider />
      {!loading && cliente && (
        <Box sx={{ p: 2, bgcolor: '#fafafa' }}>
          <Typography variant="h6" sx={{ mb: 2, color: '#1976d2', fontWeight: 600 }}>Resumo Estatístico</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ flex: '1 1 250px', minWidth: '200px' }}>
              <Card sx={{ bgcolor: '#e8f5e8', border: '1px solid #4caf50' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ color: '#2e7d32', fontWeight: 'bold' }}>{cliente.total_compras ?? 0}</Typography>
                  <Typography variant="body2" sx={{ color: '#424242' }}>Total de Compras</Typography>
                </CardContent>
              </Card>
            </Box>
            <Box sx={{ flex: '1 1 250px', minWidth: '200px' }}>
              <Card sx={{ bgcolor: '#fff3e0', border: '1px solid #ff9800' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ color: '#e65100', fontWeight: 'bold' }}>
                    R$ {cliente.valor_total_gasto?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) ?? '0,00'}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#424242' }}>Valor Total Gasto</Typography>
                </CardContent>
              </Card>
            </Box>
            <Box sx={{ flex: '1 1 250px', minWidth: '200px' }}>
              <Card sx={{ 
                bgcolor: cliente.saldo_devedor > 0 ? '#ffebee' : '#e8f5e8', 
                border: `1px solid ${cliente.saldo_devedor > 0 ? '#f44336' : '#4caf50'}` 
              }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ 
                    color: cliente.saldo_devedor > 0 ? '#c62828' : '#2e7d32', 
                    fontWeight: 'bold' 
                  }}>
                    R$ {cliente.saldo_devedor?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) ?? '0,00'}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#424242' }}>
                    {cliente.saldo_devedor > 0 ? 'Saldo Devedor' : 'Saldo Positivo'}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          </Box>
        </Box>
      )}
      <DialogActions>
        <Button onClick={() => onEdit(cliente)} color="primary" variant="contained">Editar</Button>
        <Button onClick={() => onDelete(cliente)} color="error" variant="outlined">Excluir</Button>
        <Button onClick={onClose} color="inherit">Fechar</Button>
      </DialogActions>
    </Dialog>
  );
};

export default CustomerDetailsModal;
