"""
Módulo centralizado de validações
Elimina redundância de código em múltiplos arquivos
"""
import re
import os
from decimal import Decimal
from typing import Optional, Union

def normalizar_documento(doc: str) -> str:
    """Remove caracteres não numéricos de documentos"""
    if not doc:
        return ""
    return re.sub(r"[^\d]", "", str(doc))

def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF brasileiro
    
    Args:
        cpf: CPF com ou sem formatação
        
    Returns:
        bool: True se válido
    """
    # Modo simulação sempre válido
    if os.environ.get("FLASK_ENV") == "simulation":
        return True
    
    cpf = normalizar_documento(cpf)
    
    # Validações básicas
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    
    # Validação dos dígitos verificadores
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False
    
    return True

def validar_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ brasileiro
    
    Args:
        cnpj: CNPJ com ou sem formatação
        
    Returns:
        bool: True se válido
    """
    # Modo simulação sempre válido
    if os.environ.get("FLASK_ENV") == "simulation":
        return True
    
    cnpj = normalizar_documento(cnpj)
    
    # Validações básicas
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False
    
    def calc_digit(num_str, weights):
        total = sum(int(d) * w for d, w in zip(num_str, weights))
        rest = total % 11
        return 0 if rest < 2 else 11 - rest
    
    # Pesos para cálculo dos dígitos
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Validar dígitos verificadores
    d1 = calc_digit(cnpj[:12], pesos1)
    d2 = calc_digit(cnpj[:12] + str(d1), pesos2)
    
    return d1 == int(cnpj[12]) and d2 == int(cnpj[13])

def validar_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: Email a validar
        
    Returns:
        bool: True se válido
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validar_telefone(telefone: str) -> bool:
    """
    Valida telefone brasileiro
    
    Args:
        telefone: Telefone com ou sem formatação
        
    Returns:
        bool: True se válido
    """
    if not telefone:
        return False
    
    # Remove formatação
    numeros = normalizar_documento(telefone)
    
    # Valida tamanho (10 ou 11 dígitos)
    if len(numeros) not in [10, 11]:
        return False
    
    # Valida DDD (11-99)
    ddd = int(numeros[:2])
    if ddd < 11 or ddd > 99:
        return False
    
    return True

def validar_cep(cep: str) -> bool:
    """
    Valida CEP brasileiro
    
    Args:
        cep: CEP com ou sem formatação
        
    Returns:
        bool: True se válido
    """
    if not cep:
        return False
    
    # Remove formatação
    numeros = normalizar_documento(cep)
    
    # Valida tamanho
    return len(numeros) == 8

def validar_valor_monetario(valor: Union[str, float, Decimal], min_valor: float = 0.0, max_valor: Optional[float] = None) -> bool:
    """
    Valida valor monetário
    
    Args:
        valor: Valor a validar
        min_valor: Valor mínimo permitido
        max_valor: Valor máximo permitido (opcional)
        
    Returns:
        bool: True se válido
    """
    try:
        valor_decimal = Decimal(str(valor))
        
        if valor_decimal < Decimal(str(min_valor)):
            return False
        
        if max_valor is not None and valor_decimal > Decimal(str(max_valor)):
            return False
        
        return True
    except:
        return False

def validar_quantidade(quantidade: Union[str, float, Decimal], min_qtd: float = 0.001) -> bool:
    """
    Valida quantidade de produto
    
    Args:
        quantidade: Quantidade a validar
        min_qtd: Quantidade mínima permitida
        
    Returns:
        bool: True se válido
    """
    try:
        qtd_decimal = Decimal(str(quantidade))
        return qtd_decimal >= Decimal(str(min_qtd))
    except:
        return False

def validar_codigo_barras(codigo: str) -> bool:
    """
    Valida código de barras (EAN-13, EAN-8, UPC)
    
    Args:
        codigo: Código de barras
        
    Returns:
        bool: True se válido
    """
    if not codigo:
        return False
    
    # Remove espaços
    codigo = codigo.strip()
    
    # Valida tamanho (8, 12, 13 ou 14 dígitos)
    if len(codigo) not in [8, 12, 13, 14]:
        return False
    
    # Valida se são apenas números
    if not codigo.isdigit():
        return False
    
    return True

def sanitizar_string(texto: str, max_length: int = 255) -> str:
    """
    Sanitiza string removendo caracteres perigosos
    
    Args:
        texto: Texto a sanitizar
        max_length: Tamanho máximo
        
    Returns:
        str: Texto sanitizado
    """
    if not texto:
        return ""
    
    # Remove caracteres de controle
    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)
    
    # Remove múltiplos espaços
    texto = re.sub(r'\s+', ' ', texto)
    
    # Limita tamanho
    texto = texto[:max_length]
    
    return texto.strip()

def validar_range_inteiro(valor: int, min_val: int, max_val: int) -> bool:
    """
    Valida se inteiro está dentro do range
    
    Args:
        valor: Valor a validar
        min_val: Valor mínimo
        max_val: Valor máximo
        
    Returns:
        bool: True se válido
    """
    try:
        valor_int = int(valor)
        return min_val <= valor_int <= max_val
    except:
        return False
