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
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [cpfChecking, setCpfChecking] = useState(false);

  React.useEffect(() => {
    if (initialData && Object.keys(initialData).length > 0) {
      setForm({...initialData});
    } else {
      setForm({});
    }
    setErrors({});
  }, [initialData?.id, open]); // Dependências mais específicas

  // Validação de CPF
  const validateCPF = (cpf: string): boolean => {
    cpf = cpf.replace(/\D/g, '');
    if (cpf.length !== 11) return false;
    if (/^(\d)\1+$/.test(cpf)) return false;

    let sum = 0;
    for (let i = 0; i < 9; i++) {
      sum += parseInt(cpf.charAt(i)) * (10 - i);
    }
    let remainder = (sum * 10) % 11;
    if (remainder === 10 || remainder === 11) remainder = 0;
    if (remainder !== parseInt(cpf.charAt(9))) return false;

    sum = 0;
    for (let i = 0; i < 10; i++) {
      sum += parseInt(cpf.charAt(i)) * (11 - i);
    }
    remainder = (sum * 10) % 11;
    if (remainder === 10 || remainder === 11) remainder = 0;
    return remainder === parseInt(cpf.charAt(10));
  };

  // Verificar se CPF já existe
  const checkCPFDuplicate = async (cpf: string): Promise<boolean> => {
    if (!cpf || cpf.length < 14) return false;
    try {
      const cleanCPF = cpf.replace(/\D/g, '');
      const response = await fetch(`/api/clientes?busca=${cleanCPF}`);
      const data = await response.json();
      const existing = data.clientes?.find((c: Cliente) => c.cpf === cleanCPF && c.id !== initialData?.id);
      return !!existing;
    } catch {
      return false;
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    let value: string | number = e.target.value;
    const name = e.target.name;

    if (name === 'cpf' && value.length <= 14) {
      value = maskCPF(value);
    }
    if (name === 'celular') {
      value = maskPhone(value);
    }
    if (name === 'limite_credito') {
      const numValue = parseFloat(value);
      value = isNaN(numValue) ? '' : numValue.toString();
    }

    setForm({ ...form, [name]: value });

    // Limpar erro do campo
    if (errors[name]) {
      setErrors({ ...errors, [name]: '' });
    }

    // Validação em tempo real para CPF
    if (name === 'cpf' && typeof value === 'string' && value.length === 14) {
      if (!validateCPF(value)) {
        setErrors({ ...errors, cpf: 'CPF inválido' });
      } else {
        setCpfChecking(true);
        const isDuplicate = await checkCPFDuplicate(value);
        setCpfChecking(false);
        if (isDuplicate) {
          setErrors({ ...errors, cpf: 'CPF já cadastrado para outro cliente' });
        }
      }
    }

    // Validação de email
    if (name === 'email' && value && typeof value === 'string') {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) {
        setErrors({ ...errors, email: 'Email inválido' });
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors: Record<string, string> = {};

    // Validações obrigatórias
    if (!form.nome?.trim()) newErrors.nome = 'Nome é obrigatório';
    if (!form.cpf?.trim()) newErrors.cpf = 'CPF é obrigatório';
    if (!form.celular?.trim()) newErrors.celular = 'Telefone é obrigatório';

    // Validação de CPF
    if (form.cpf && !validateCPF(form.cpf)) {
      newErrors.cpf = 'CPF inválido';
    }

    // Validação de email
    if (form.email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(form.email)) {
        newErrors.email = 'Email inválido';
      }
    }

    // Verificar CPF duplicado se não há erro de validação
    if (form.cpf && !newErrors.cpf) {
      const isDuplicate = await checkCPFDuplicate(form.cpf);
      if (isDuplicate) {
        newErrors.cpf = 'CPF já cadastrado para outro cliente';
      }
    }

    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      // Para edição, garantir que campos obrigatórios sejam enviados
      const dataToSave = { ...form };
      if (initialData?.id) {
        // Na edição, garantir campos obrigatórios
        const requiredFields = ['nome', 'cpf', 'celular'] as const;
        for (const field of requiredFields) {
          if (!dataToSave[field] && initialData[field]) {
            dataToSave[field] = initialData[field];
          }
        }
      }
      
      // Filtrar campos que não devem ser enviados na atualização
      const camposNaoEnviar = ['id', 'saldo_devedor', 'total_compras', 'data_cadastro', 'ultima_compra', 'valor_total_gasto'];
      const cleanData = Object.fromEntries(
        Object.entries(dataToSave).filter(([key, value]) => 
          value !== undefined && 
          value !== null && 
          value !== "" &&
          !camposNaoEnviar.includes(key)
        )
      );
      
      onSave(cleanData);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth PaperProps={{
      sx: { borderRadius: 3, boxShadow: 8, p: 0 }
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 3, pt: 2, pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {initialData.id ? <EditIcon color="primary" /> : <PersonAddAlt1Icon color="primary" />}
          <Typography variant="h6" fontWeight={700} color="primary.main">
            {initialData.id ? 'Editar Cliente' : 'Novo Cliente'}
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
              <TextField
                label="Nome"
                name="nome"
                value={form.nome || ''}
                onChange={handleChange}
                required
                fullWidth
                autoFocus
                variant="outlined"
                size="medium"
                error={!!errors.nome}
                helperText={errors.nome}
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 220px" minWidth={220} maxWidth={400}>
              <TextField
                label="CPF"
                name="cpf"
                value={form.cpf || ''}
                onChange={handleChange}
                required
                fullWidth
                variant="outlined"
                size="medium"
                error={!!errors.cpf}
                helperText={errors.cpf || (cpfChecking ? 'Verificando CPF...' : '')}
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
                InputProps={{
                  endAdornment: cpfChecking ? <CircularProgress size={16} /> : null,
                }}
              />
            </Box>
            <Box flex="1 1 220px" minWidth={220} maxWidth={400}>
              <TextField
                label="Telefone"
                name="celular"
                value={form.celular || ''}
                onChange={handleChange}
                required
                fullWidth
                variant="outlined"
                size="medium"
                error={!!errors.celular}
                helperText={errors.celular}
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 220px" minWidth={220} maxWidth={400}>
              <TextField
                label="Email"
                name="email"
                value={form.email || ''}
                onChange={handleChange}
                type="email"
                fullWidth
                variant="outlined"
                size="medium"
                error={!!errors.email}
                helperText={errors.email}
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 100%" minWidth={220} maxWidth={800}>
              <TextField
                label="Endereço"
                name="endereco_completo"
                value={form.endereco_completo || ''}
                onChange={handleChange}
                fullWidth
                variant="outlined"
                size="medium"
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 220px" minWidth={220} maxWidth={400}>
              <TextField
                label="Limite de Crédito"
                name="limite_credito"
                value={form.limite_credito || ''}
                onChange={handleChange}
                type="number"
                fullWidth
                variant="outlined"
                size="medium"
                InputProps={{
                  startAdornment: <span style={{ color: '#bdbdbd', marginRight: 8 }}>R$</span>,
                }}
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
            <Box flex="1 1 100%" minWidth={220} maxWidth={800}>
              <TextField
                label="Observações"
                name="observacoes"
                value={form.observacoes || ''}
                onChange={handleChange}
                fullWidth
                multiline
                rows={2}
                variant="outlined"
                size="medium"
                InputLabelProps={{ style: { color: '#bdbdbd' } }}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, pt: 1, justifyContent: 'space-between' }}>
          <Button 
            onClick={onClose} 
            variant="outlined" 
            disabled={loading} 
            startIcon={<CloseIcon />}
            sx={{ 
              color: '#757575', 
              borderColor: '#e0e0e0',
              '&:hover': { 
                borderColor: '#bdbdbd',
                bgcolor: '#f5f5f5'
              }
            }}
          >
            Cancelar
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            disabled={loading}
            startIcon={form.id ? <SaveIcon /> : <PersonAddAlt1Icon />} 
            sx={{ 
              minWidth: 120,
              bgcolor: '#1976d2',
              '&:hover': { 
                bgcolor: '#1565c0'
              }
            }}
          >
            {loading ? <CircularProgress size={22} color="inherit" /> : (form.id ? 'Salvar' : 'Cadastrar')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default CustomerForm;
