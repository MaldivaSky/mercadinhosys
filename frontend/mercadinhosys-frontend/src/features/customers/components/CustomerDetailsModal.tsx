import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Divider, Card, CardContent, CircularProgress } from '@mui/material';
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

  const labelStyle = {
    fontWeight: 600,
    color: '#1976d2',
    minWidth: 140,
    flexShrink: 0,
  };

  const valueStyle = {
    color: '#212121',
    fontWeight: 400,
  };

  const InfoRow = ({ label, value, valueColor }: { label: string; value: React.ReactNode; valueColor?: string }) => (
    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, py: 0.5 }}>
      <Typography sx={labelStyle}>{label}</Typography>
      <Typography sx={{ ...valueStyle, color: valueColor || valueStyle.color }}>{value}</Typography>
    </Box>
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Detalhes do Cliente</DialogTitle>
      <DialogContent dividers>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : cliente ? (
          <Box>
            {/* Dados Pessoais */}
            <Typography variant="subtitle2" sx={{ color: '#1976d2', fontWeight: 700, mb: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Dados Pessoais
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 0.5, mb: 2 }}>
              <InfoRow label="Nome:" value={cliente.nome || '-'} />
              <InfoRow label="CPF:" value={cliente.cpf || '-'} />
              <InfoRow label="Telefone:" value={cliente.celular || cliente.telefone || '-'} />
              <InfoRow label="Email:" value={cliente.email || '-'} />
              <InfoRow label="Data Cadastro:" value={cliente.data_cadastro ? new Date(cliente.data_cadastro).toLocaleDateString('pt-BR') : '-'} />
              <InfoRow label="Última Compra:" value={cliente.ultima_compra ? new Date(cliente.ultima_compra).toLocaleDateString('pt-BR') : '-'} />
            </Box>

            {/* Endereço (se informado) */}
            {(cliente.logradouro || cliente.cidade) && (
              <>
                <Divider sx={{ my: 1.5 }} />
                <Typography variant="subtitle2" sx={{ color: '#1976d2', fontWeight: 700, mb: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Endereço
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 0.5, mb: 2 }}>
                  <InfoRow label="Endereço:" value={cliente.endereco_completo || `${cliente.logradouro || ''} ${cliente.numero || ''}`.trim() || '-'} />
                  <InfoRow label="Bairro:" value={cliente.bairro || '-'} />
                  <InfoRow label="Cidade/UF:" value={cliente.cidade ? `${cliente.cidade}${cliente.estado ? `/${cliente.estado}` : ''}` : '-'} />
                  <InfoRow label="CEP:" value={cliente.cep || '-'} />
                </Box>
              </>
            )}

            {/* Financeiro */}
            <Divider sx={{ my: 1.5 }} />
            <Typography variant="subtitle2" sx={{ color: '#1976d2', fontWeight: 700, mb: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Financeiro
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 0.5, mb: 2 }}>
              <InfoRow label="Total Compras:" value={cliente.total_compras ?? '-'} />
              <InfoRow
                label="Valor Total Gasto:"
                value={`R$ ${cliente.valor_total_gasto ? cliente.valor_total_gasto.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : '0,00'}`}
                valueColor="#2e7d32"
              />
              <InfoRow
                label="Limite Crédito:"
                value={`R$ ${cliente.limite_credito ? cliente.limite_credito.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : '0,00'}`}
                valueColor="#2e7d32"
              />
              <InfoRow
                label="Saldo Devedor:"
                value={`R$ ${cliente.saldo_devedor?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) ?? '0,00'}`}
                valueColor={(cliente.saldo_devedor ?? 0) > 0 ? '#d32f2f' : '#2e7d32'}
              />
            </Box>

            {/* Cards de resumo */}
            <Divider sx={{ my: 1.5 }} />
            <Typography variant="h6" sx={{ mb: 2, color: '#1976d2', fontWeight: 600 }}>Resumo Estatístico</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 180px', minWidth: '160px' }}>
                <Card sx={{ bgcolor: '#e8f5e8', border: '1px solid #4caf50' }}>
                  <CardContent sx={{ textAlign: 'center', py: '12px !important' }}>
                    <Typography variant="h4" sx={{ color: '#2e7d32', fontWeight: 'bold' }}>{cliente.total_compras ?? 0}</Typography>
                    <Typography variant="body2" sx={{ color: '#424242' }}>Total de Compras</Typography>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ flex: '1 1 180px', minWidth: '160px' }}>
                <Card sx={{ bgcolor: '#fff3e0', border: '1px solid #ff9800' }}>
                  <CardContent sx={{ textAlign: 'center', py: '12px !important' }}>
                    <Typography variant="h5" sx={{ color: '#e65100', fontWeight: 'bold' }}>
                      R$ {cliente.valor_total_gasto?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) ?? '0,00'}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#424242' }}>Valor Total Gasto</Typography>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ flex: '1 1 180px', minWidth: '160px' }}>
                <Card sx={{
                  bgcolor: (cliente.saldo_devedor ?? 0) > 0 ? '#ffebee' : '#e8f5e8',
                  border: `1px solid ${(cliente.saldo_devedor ?? 0) > 0 ? '#f44336' : '#4caf50'}`
                }}>
                  <CardContent sx={{ textAlign: 'center', py: '12px !important' }}>
                    <Typography variant="h5" sx={{
                      color: (cliente.saldo_devedor ?? 0) > 0 ? '#c62828' : '#2e7d32',
                      fontWeight: 'bold'
                    }}>
                      R$ {cliente.saldo_devedor?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) ?? '0,00'}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#424242' }}>
                      {(cliente.saldo_devedor ?? 0) > 0 ? 'Saldo Devedor' : 'Sem Débitos'}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          </Box>
        ) : (
          <Typography>Cliente não encontrado.</Typography>
        )}
      </DialogContent>
      <Divider />
      <DialogActions>
        {/* Botões de ação só renderizam quando cliente está carregado — evita onEdit(null) */}
        {!loading && cliente && (
          <>
            <Button onClick={() => onEdit(cliente)} color="primary" variant="contained">Editar</Button>
            <Button onClick={() => onDelete(cliente)} color="error" variant="outlined">Excluir</Button>
          </>
        )}
        <Button onClick={onClose} color="inherit">Fechar</Button>
      </DialogActions>
    </Dialog>
  );
};

export default CustomerDetailsModal;
