import React, { useState } from 'react';
import { maskCPF, maskPhone } from './inputMasks';
import { Cliente } from '../../../types';
import {
  Dialog, DialogContent, DialogActions, Button, TextField, Typography, Box, IconButton, CircularProgress
} from '@mui/material';
// Importação compatível com todos os ambientes MUI 5+
import CloseIcon from '@mui/icons-material/Close';
import PersonAddAlt1Icon from '@mui/icons-material/PersonAddAlt1';
import SaveIcon from '@mui/icons-material/Save';
import EditIcon from '@mui/icons-material/Edit';

interface CustomerFormProps {
  open: boolean;
  onClose: () => void;
  onSave: (cliente: Partial<Cliente>) => void;
  initialData?: Partial<Cliente>;
  loading?: boolean;
}

const CustomerForm: React.FC<CustomerFormProps> = ({ open, onClose, onSave, initialData = {}, loading }) => {
  const [form, setForm] = useState<Partial<Cliente>>(initialData);

  React.useEffect(() => {
    setForm(initialData || {});
    // eslint-disable-next-line
  }, [initialData?.id, open]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value;
    if (e.target.name === 'cpf_cnpj' && value.length <= 14) {
      value = maskCPF(value);
    }
    if (e.target.name === 'telefone') {
      value = maskPhone(value);
    }
    setForm({ ...form, [e.target.name]: value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth PaperProps={{
      sx: { borderRadius: 3, boxShadow: 8, p: 0 }
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 3, pt: 2, pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {form.id ? <EditIcon color="primary" /> : <PersonAddAlt1Icon color="primary" />}
          <Typography variant="h6" fontWeight={700} color="primary.main">
            {form.id ? 'Editar Cliente' : 'Novo Cliente'}
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small" sx={{ color: 'grey.600' }}>
          <CloseIcon />
        </IconButton>
      </Box>
      <form onSubmit={handleSubmit}>
        <DialogContent sx={{ pt: 0, pb: 1 }}>
          <Box display="flex" flexWrap="wrap" gap={2}>
            <Box flex="1 1 220px" minWidth={220} maxWidth={400}>
              <TextField label="Nome" name="nome" value={form.nome || ''} onChange={handleChange} required fullWidth autoFocus
                variant="outlined" size="medium"
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 220px" minWidth={220} maxWidth={400}>
              <TextField label="CPF/CNPJ" name="cpf_cnpj" value={form.cpf_cnpj || ''} onChange={handleChange} fullWidth
                variant="outlined" size="medium"
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 220px" minWidth={220} maxWidth={400}>
              <TextField label="Telefone" name="telefone" value={form.telefone || ''} onChange={handleChange} fullWidth
                variant="outlined" size="medium"
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 220px" minWidth={220} maxWidth={400}>
              <TextField label="Email" name="email" value={form.email || ''} onChange={handleChange} type="email" fullWidth
                variant="outlined" size="medium"
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 100%" minWidth={220} maxWidth={800}>
              <TextField label="Endereço" name="endereco" value={form.endereco || ''} onChange={handleChange} fullWidth
                variant="outlined" size="medium"
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 100%" minWidth={220} maxWidth={800}>
              <TextField label="Observações" name="observacoes" value={form.observacoes || ''} onChange={handleChange} fullWidth multiline rows={2}
                variant="outlined" size="medium"
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, pt: 1, justifyContent: 'space-between' }}>
          <Button onClick={onClose} color="inherit" variant="outlined" disabled={loading} startIcon={<CloseIcon />}>
            Cancelar
          </Button>
          <Button type="submit" variant="contained" color="primary" disabled={loading}
            startIcon={form.id ? <SaveIcon /> : <PersonAddAlt1Icon />} sx={{ minWidth: 120 }}>
            {loading ? <CircularProgress size={22} color="inherit" /> : (form.id ? 'Salvar' : 'Cadastrar')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default CustomerForm;
