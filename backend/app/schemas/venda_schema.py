"""
Schemas Pydantic para validação de vendas
"""
from pydantic import BaseModel, validator, Field
from typing import List, Optional
from decimal import Decimal

class PagamentoSchema(BaseModel):
    """Schema para validação de pagamento"""
    forma: str = Field(..., description="Forma de pagamento")
    valor: Decimal = Field(..., gt=0, description="Valor do pagamento")
    referencia: Optional[str] = Field(None, description="Referência do pagamento (NSU, autorização, etc)")
    
    @validator('forma')
    def forma_valida(cls, v):
        """Valida forma de pagamento"""
        formas_validas = ['dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'fiado']
        if v.lower() not in formas_validas:
            raise ValueError(f"Forma inválida. Válidas: {formas_validas}")
        return v.lower()
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class VendaItemSchema(BaseModel):
    """Schema para validação de item da venda"""
    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: Decimal = Field(..., gt=0, description="Quantidade")
    preco_unitario: Optional[Decimal] = Field(None, gt=0, description="Preço unitário (opcional)")
    desconto: Optional[Decimal] = Field(0, ge=0, description="Desconto no item")
    
    # Suporte a múltiplos nomes de campos (compatibilidade)
    id: Optional[int] = None
    productId: Optional[int] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    
    @validator('produto_id', pre=True, always=True)
    def set_produto_id(cls, v, values):
        """Define produto_id a partir de múltiplos campos possíveis"""
        return v or values.get('id') or values.get('productId')
    
    @validator('quantidade', pre=True, always=True)
    def set_quantidade(cls, v, values):
        """Define quantidade a partir de múltiplos campos possíveis"""
        return v or values.get('quantity') or Decimal('1')
    
    @validator('preco_unitario', pre=True, always=True)
    def set_preco_unitario(cls, v, values):
        """Define preco_unitario a partir de múltiplos campos possíveis"""
        return v or values.get('price')
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class FinalizarVendaSchema(BaseModel):
    """Schema para validação de finalização de venda"""
    cliente_id: Optional[int] = Field(None, description="ID do cliente (opcional)")
    items: List[VendaItemSchema] = Field(..., min_items=1, description="Itens da venda")
    pagamentos: Optional[List[PagamentoSchema]] = Field(None, description="Formas de pagamento")
    subtotal: Decimal = Field(..., gt=0, description="Subtotal da venda")
    desconto: Optional[Decimal] = Field(0, ge=0, description="Desconto geral")
    total: Decimal = Field(..., gt=0, description="Total da venda")
    data_vencimento_fiado: Optional[str] = Field(None, description="Data de vencimento do fiado (YYYY-MM-DD)")
    observacoes: Optional[str] = Field(None, description="Observações da venda")
    
    # Compatibilidade com sistema antigo
    paymentMethod: Optional[str] = None
    valor_recebido: Optional[Decimal] = None
    troco: Optional[Decimal] = None
    
    @validator('items')
    def items_not_empty(cls, v):
        """Valida que há pelo menos 1 item"""
        if not v:
            raise ValueError("Mínimo 1 item na venda")
        return v
    
    @validator('pagamentos', pre=True, always=True)
    def set_pagamentos(cls, v, values):
        """
        Define pagamentos a partir de múltiplos formatos possíveis
        Compatibilidade com sistema antigo
        """
        if v:
            return v
        
        # Sistema antigo: paymentMethod + valor_recebido
        payment_method = values.get('paymentMethod')
        valor_recebido = values.get('valor_recebido')
        total = values.get('total')
        
        if payment_method:
            return [{
                "forma": payment_method,
                "valor": valor_recebido or total
            }]
        
        # Se não tem pagamentos, retorna lista vazia (será validado depois)
        return []
    
    @validator('pagamentos')
    def pagamentos_not_empty(cls, v):
        """Valida que há pelo menos 1 forma de pagamento"""
        if not v:
            raise ValueError("Mínimo 1 forma de pagamento")
        return v
    
    @validator('total')
    def validar_total(cls, v, values):
        """Valida que total = subtotal - desconto"""
        subtotal = values.get('subtotal', Decimal('0'))
        desconto = values.get('desconto', Decimal('0'))
        
        total_esperado = subtotal - desconto
        
        if abs(v - total_esperado) > Decimal('0.01'):
            raise ValueError(f"Total ({v}) não corresponde a subtotal ({subtotal}) - desconto ({desconto})")
        
        return v
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
