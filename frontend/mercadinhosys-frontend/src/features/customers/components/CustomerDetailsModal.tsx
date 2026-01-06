import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Divider } from '@mui/material';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';


interface CustomerDetailsModalProps {
  open: boolean;
  cliente: any | null;
  loading?: boolean;
  onClose: () => void;
  onEdit: (cliente: any) => void;
  onDelete: (cliente: any) => void;
}

const labelStyle = { fontWeight: 600, color: '#ff0000', minWidth: 120 };

const CustomerDetailsModal: React.FC<CustomerDetailsModalProps> = ({ open, cliente, loading, onClose, onEdit, onDelete }) => {
  if (!cliente) return null;
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Detalhes do Cliente</DialogTitle>
      <DialogContent dividers>
        {loading ? (
          <Typography>Carregando detalhes...</Typography>
        ) : (
          <Grid container spacing={2}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Nome:</Typography> <Typography>{cliente.nome}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>CPF/CNPJ:</Typography> <Typography>{cliente.cpf_cnpj || '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Telefone:</Typography> <Typography>{cliente.telefone || '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Email:</Typography> <Typography>{cliente.email || '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Endereço:</Typography> <Typography>{cliente.endereco || '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Data Cadastro:</Typography> <Typography>{cliente.data_cadastro ? new Date(cliente.data_cadastro).toLocaleDateString() : '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Total Compras:</Typography> <Typography>{cliente.estatisticas?.total_compras ?? '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Total Gasto:</Typography> <Typography>R$ {cliente.estatisticas?.total_gasto?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) ?? '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Ticket Médio:</Typography> <Typography>R$ {cliente.estatisticas?.ticket_medio?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) ?? '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Última Compra:</Typography> <Typography>{cliente.estatisticas?.ultima_compra_data ? new Date(cliente.estatisticas.ultima_compra_data).toLocaleDateString() : '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Dias desde última compra:</Typography> <Typography>{cliente.estatisticas?.dias_ultima_compra ?? '-'}</Typography></Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Classificação:</Typography> <Typography>{cliente.classificacao || '-'}</Typography></Box>
            {/* Produtos preferidos */}
            {cliente.estatisticas?.produtos_preferidos && cliente.estatisticas.produtos_preferidos.length > 0 && (
              <Box sx={{ gridColumn: 'span 12', mt: 2 }}>
                <Typography sx={{ fontWeight: 600, color: '#1976d2', mb: 1 }}>Produtos Preferidos:</Typography>
                <ul style={{ margin: 0, paddingLeft: 16 }}>
                  {cliente.estatisticas.produtos_preferidos.map((p: any) => (
                    <li key={p.nome}>
                      {p.nome} — {p.quantidade}x (R$ {p.valor_total.toLocaleString('pt-BR', {minimumFractionDigits: 2})})
                    </li>
                  ))}
                </ul>
              </Box>
            )}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} gridColumn={{ xs: 'span 12', sm: 'span 6' }}><Typography sx={labelStyle}>Observações:</Typography> <Typography>{cliente.observacoes || '-'}</Typography></Box>
          </Grid>
        )}
      </DialogContent>
      <Divider />
      <DialogActions>
        <Button onClick={() => onEdit(cliente)} color="primary" variant="contained">Editar</Button>
        <Button onClick={() => onDelete(cliente)} color="error" variant="outlined">Excluir</Button>
        <Button onClick={onClose} color="inherit">Fechar</Button>
      </DialogActions>
    </Dialog>
  );
};

export default CustomerDetailsModal;
