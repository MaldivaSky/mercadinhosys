import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Grid, Divider } from '@mui/material';
import { Cliente } from '../../../types';

interface CustomerDetailsModalProps {
  open: boolean;
  cliente: Cliente | null;
  onClose: () => void;
  onEdit: (cliente: Cliente) => void;
  onDelete: (cliente: Cliente) => void;
}

const labelStyle = { fontWeight: 600, color: '#ff0000', minWidth: 120 };

const CustomerDetailsModal: React.FC<CustomerDetailsModalProps> = ({ open, cliente, onClose, onEdit, onDelete }) => {
  if (!cliente) return null;
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Detalhes do Cliente</DialogTitle>
      <DialogContent dividers>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>Nome:</Typography> <Typography>{cliente.nome}</Typography></Grid>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>CPF/CNPJ:</Typography> <Typography>{cliente.cpf_cnpj || '-'}</Typography></Grid>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>Telefone:</Typography> <Typography>{cliente.telefone || '-'}</Typography></Grid>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>Email:</Typography> <Typography>{cliente.email || '-'}</Typography></Grid>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>Endereço:</Typography> <Typography>{cliente.endereco || '-'}</Typography></Grid>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>Data Cadastro:</Typography> <Typography>{cliente.data_cadastro ? new Date(cliente.data_cadastro).toLocaleDateString() : '-'}</Typography></Grid>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>Total Compras:</Typography> <Typography>{cliente.total_compras ?? '-'}</Typography></Grid>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>Última Compra:</Typography> <Typography>{cliente.ultima_compra ? new Date(cliente.ultima_compra).toLocaleDateString() : '-'}</Typography></Grid>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>Segmento RFM:</Typography> <Typography>{cliente.segmento_rfm || '-'}</Typography></Grid>
          <Grid item xs={12} sm={6}><Typography sx={labelStyle}>Observações:</Typography> <Typography>{cliente.observacoes || '-'}</Typography></Grid>
        </Grid>
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
