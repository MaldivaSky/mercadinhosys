# 🧹 RECOMENDAÇÕES DE CÓDIGO LIMPO
## Padrões e Melhores Práticas para o MercadinhoSys

---

## 1. ESTRUTURA DE PASTAS RECOMENDADA

### Antes (Atual)
```
backend/app/
├── routes/          # Tudo junto
├── models.py        # 1603 linhas
├── services/
└── utils/
```

### Depois (Recomendado)
```
backend/app/
├── models/
│   ├── __init__.py
│   ├── base.py              # Mixins e classes base
│   ├── vendas.py            # Venda, VendaItem, Pagamento
│   ├── clientes.py          # Cliente, ContaReceber
│   ├── produtos.py          # Produto, MovimentacaoEstoque
│   ├── funcionarios.py      # Funcionario, RegistroPonto
│   ├── delivery.py          # Entrega, Motorista, Veiculo
│   └── configuracao.py      # Configuracao, Estabelecimento
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── vendas.py
│   ├── pdv.py
│   ├── clientes.py
│   ├── produtos.py
│   ├── delivery.py
│   ├── dashboard.py
│   └── ...
├── services/
│   ├── __init__.py
│   ├── venda_service.py     # Lógica de vendas
│   ├── cliente_service.py   # Lógica de clientes
│   ├── email_service.py
│   ├── pagamento_service.py # Novo: Lógica de pagamentos
│   └── ...
├── decorators/
├── middleware/
├── schemas/                 # Validação com Pydantic
│   ├── __init__.py
│   ├── venda_schema.py
│   ├── cliente_schema.py
│   └── ...
├── utils/
│   ├── __init__.py
│   ├── validators.py        # Validações reutilizáveis
│   ├── formatters.py        # Formatação de dados
│   ├── errors.py            # Exceções customizadas
│   └── ...
└── tests/
    ├── __init__.py
    ├── test_vendas.py
    ├── test_clientes.py
    └── ...
```

---

## 2. PADRÃO DE RESPOSTA PADRONIZADO

### Criar arquivo: `backend/app/utils/response.py`

```python
from flask import jsonify
from typing import Any, Dict, Optional

class APIResponse:
    """Padroniza respostas da API"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Sucesso", status_code: int = 200):
        """Resposta de sucesso"""
        return jsonify({
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), status_code
    
    @staticmethod
    def error(error_code: str, message: str, details: Optional[Dict] = None, status_code: int = 400):
        """Resposta de erro"""
        return jsonify({
            "success": False,
            "error": error_code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), status_code
    
    @staticmethod
    def paginated(items: list, page: int, per_page: int, total: int, status_code: int = 200):
        """Resposta paginada"""
        return jsonify({
            "success": True,
            "data": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), status_code

# Uso em rotas:
# return APIResponse.success(data=venda.to_dict(), message="Venda criada", status_code=201)
# return APIResponse.error("ESTOQUE_INSUFICIENTE", "Estoque insuficiente", status_code=400)
```

---

## 3. EXCEÇÕES CUSTOMIZADAS

### Criar arquivo: `backend/app/utils/errors.py`

```python
class APIError(Exception):
    """Exceção base para erros da API"""
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class EstoqueInsuficienteError(APIError):
    def __init__(self, produto_nome: str, disponivel: int, solicitado: int):
        super().__init__(
            code="ESTOQUE_INSUFICIENTE",
            message=f"Estoque insuficiente para {produto_nome}",
            status_code=400,
            details={"disponivel": disponivel, "solicitado": solicitado}
        )

class ClienteNaoEncontradoError(APIError):
    def __init__(self, cliente_id: int):
        super().__init__(
            code="CLIENTE_NAO_ENCONTRADO",
            message=f"Cliente {cliente_id} não encontrado",
            status_code=404
        )

class CaixaFechadoError(APIError):
    def __init__(self):
        super().__init__(
            code="CAIXA_FECHADO",
            message="Caixa está fechado. Abra o caixa antes de registrar vendas.",
            status_code=403
        )

# Uso em rotas:
# if not cliente:
#     raise ClienteNaoEncontradoError(cliente_id)
```

---

## 4. VALIDAÇÃO COM PYDANTIC

### Criar arquivo: `backend/app/schemas/venda_schema.py`

```python
from pydantic import BaseModel, validator, Field
from typing import List, Optional
from decimal import Decimal

class PagamentoSchema(BaseModel):
    forma: str = Field(..., description="Forma de pagamento")
    valor: Decimal = Field(..., gt=0, description="Valor do pagamento")
    referencia: Optional[str] = None
    
    @validator('forma')
    def forma_valida(cls, v):
        formas_validas = ['dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'fiado']
        if v not in formas_validas:
            raise ValueError(f"Forma inválida. Válidas: {formas_validas}")
        return v

class VendaItemSchema(BaseModel):
    produto_id: int = Field(..., gt=0)
    quantidade: Decimal = Field(..., gt=0)
    desconto: Optional[Decimal] = 0

class FinalizarVendaSchema(BaseModel):
    cliente_id: Optional[int] = None
    items: List[VendaItemSchema] = Field(..., min_items=1)
    pagamentos: List[PagamentoSchema] = Field(..., min_items=1)
    desconto_geral: Optional[Decimal] = 0
    data_vencimento_fiado: Optional[str] = None
    observacoes: Optional[str] = None
    
    @validator('items')
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("Mínimo 1 item na venda")
        return v
    
    @validator('pagamentos')
    def pagamentos_not_empty(cls, v):
        if not v:
            raise ValueError("Mínimo 1 forma de pagamento")
        return v

# Uso em rotas:
# from pydantic import ValidationError
# try:
#     schema = FinalizarVendaSchema(**request.get_json())
# except ValidationError as e:
#     return APIResponse.error("VALIDACAO_ERRO", str(e), status_code=422)
```

---

## 5. SERVIÇO DE VENDAS

### Criar arquivo: `backend/app/services/venda_service.py`

```python
from app.models import db, Venda, VendaItem, Pagamento, ContaReceber, Produto, MovimentacaoEstoque
from app.utils.errors import EstoqueInsuficienteError, CaixaFechadoError
from decimal import Decimal
from datetime import datetime, timedelta, timezone

class VendaService:
    """Serviço de lógica de vendas"""
    
    @staticmethod
    def validar_estoque(produto_id: int, quantidade: Decimal) -> Produto:
        """Valida se há estoque suficiente"""
        produto = Produto.query.with_for_update().get(produto_id)
        if not produto:
            raise ValueError(f"Produto {produto_id} não encontrado")
        
        if produto.quantidade < quantidade:
            raise EstoqueInsuficienteError(
                produto_nome=produto.nome,
                disponivel=int(produto.quantidade),
                solicitado=int(quantidade)
            )
        
        return produto
    
    @staticmethod
    def criar_pagamentos(venda_id: int, pagamentos_data: list, estabelecimento_id: int):
        """Cria registros de pagamento"""
        for pagamento_data in pagamentos_data:
            pagamento = Pagamento(
                venda_id=venda_id,
                forma_pagamento=pagamento_data['forma'],
                valor=pagamento_data['valor'],
                referencia=pagamento_data.get('referencia'),
                estabelecimento_id=estabelecimento_id
            )
            db.session.add(pagamento)
    
    @staticmethod
    def criar_conta_receber(cliente_id: int, venda_id: int, valor: Decimal, 
                           data_vencimento: datetime, estabelecimento_id: int):
        """Cria conta a receber (fiado)"""
        conta = ContaReceber(
            cliente_id=cliente_id,
            venda_id=venda_id,
            valor=valor,
            data_vencimento=data_vencimento,
            status="aberta",
            estabelecimento_id=estabelecimento_id
        )
        db.session.add(conta)
    
    @staticmethod
    def atualizar_estoque(produto_id: int, quantidade: Decimal, venda_id: int, 
                         estabelecimento_id: int):
        """Atualiza estoque e registra movimentação"""
        produto = VendaService.validar_estoque(produto_id, quantidade)
        produto.quantidade -= quantidade
        
        movimentacao = MovimentacaoEstoque(
            produto_id=produto_id,
            tipo="saida",
            quantidade=quantidade,
            venda_id=venda_id,
            estabelecimento_id=estabelecimento_id,
            motivo="venda_pdv"
        )
        db.session.add(movimentacao)

# Uso em rotas:
# try:
#     VendaService.validar_estoque(produto_id, quantidade)
#     VendaService.criar_pagamentos(venda_id, pagamentos_data, estab_id)
# except EstoqueInsuficienteError as e:
#     return APIResponse.error(e.code, e.message, e.details, e.status_code)
```

---

## 6. LOGGING ESTRUTURADO

### Criar arquivo: `backend/app/utils/logger.py`

```python
import logging
import json
from datetime import datetime, timezone

class StructuredLogger:
    """Logger estruturado para melhor rastreamento"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log de informação com contexto"""
        self.logger.info(json.dumps({
            "level": "INFO",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }))
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """Log de erro com contexto"""
        self.logger.error(json.dumps({
            "level": "ERROR",
            "message": message,
            "exception": str(exception) if exception else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }))
    
    def warning(self, message: str, **kwargs):
        """Log de aviso com contexto"""
        self.logger.warning(json.dumps({
            "level": "WARNING",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }))

# Uso em rotas:
# logger = StructuredLogger(__name__)
# logger.info("Venda finalizada", venda_id=venda.id, total=venda.total, funcionario_id=funcionario_id)
# logger.error("Erro ao finalizar venda", exception=e, venda_id=venda_id)
```

---

## 7. TESTES UNITÁRIOS

### Criar arquivo: `backend/tests/test_venda_service.py`

```python
import pytest
from app import create_app
from app.models import db, Produto, Cliente, Venda
from app.services.venda_service import VendaService
from app.utils.errors import EstoqueInsuficienteError
from decimal import Decimal

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def cliente(app):
    with app.app_context():
        cliente = Cliente(
            nome="João Silva",
            cpf="123.456.789-00",
            email="joao@email.com",
            estabelecimento_id=1
        )
        db.session.add(cliente)
        db.session.commit()
        return cliente

@pytest.fixture
def produto(app):
    with app.app_context():
        produto = Produto(
            nome="Arroz 5kg",
            codigo_barras="1234567890123",
            preco_venda=Decimal("25.00"),
            preco_custo=Decimal("15.00"),
            quantidade=100,
            estabelecimento_id=1
        )
        db.session.add(produto)
        db.session.commit()
        return produto

def test_validar_estoque_suficiente(app, produto):
    """Testa validação de estoque suficiente"""
    with app.app_context():
        resultado = VendaService.validar_estoque(produto.id, Decimal("10"))
        assert resultado.id == produto.id

def test_validar_estoque_insuficiente(app, produto):
    """Testa validação de estoque insuficiente"""
    with app.app_context():
        with pytest.raises(EstoqueInsuficienteError):
            VendaService.validar_estoque(produto.id, Decimal("200"))

def test_criar_pagamentos(app):
    """Testa criação de pagamentos"""
    with app.app_context():
        venda = Venda(
            codigo="V-20260426-0001",
            cliente_id=1,
            funcionario_id=1,
            total=Decimal("50.00"),
            estabelecimento_id=1
        )
        db.session.add(venda)
        db.session.commit()
        
        pagamentos_data = [
            {"forma": "dinheiro", "valor": Decimal("30.00")},
            {"forma": "cartao_credito", "valor": Decimal("20.00")}
        ]
        
        VendaService.criar_pagamentos(venda.id, pagamentos_data, 1)
        db.session.commit()
        
        assert len(venda.pagamentos) == 2
```

---

## 8. DECORADORES REUTILIZÁVEIS

### Criar arquivo: `backend/app/decorators/validators.py`

```python
from functools import wraps
from flask import request, jsonify
from app.utils.response import APIResponse

def require_json(f):
    """Valida se request tem JSON"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return APIResponse.error(
                "INVALID_CONTENT_TYPE",
                "Content-Type deve ser application/json",
                status_code=400
            )
        return f(*args, **kwargs)
    return decorated_function

def validate_schema(schema_class):
    """Valida request contra schema Pydantic"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = schema_class(**request.get_json())
                kwargs['validated_data'] = data
                return f(*args, **kwargs)
            except Exception as e:
                return APIResponse.error(
                    "VALIDATION_ERROR",
                    str(e),
                    status_code=422
                )
        return decorated_function
    return decorator

# Uso em rotas:
# @pdv_bp.route("/finalizar", methods=["POST"])
# @require_json
# @validate_schema(FinalizarVendaSchema)
# def finalizar_venda(validated_data):
#     ...
```

---

## 9. CHECKLIST DE CÓDIGO LIMPO

- [ ] Nomes de variáveis descritivos
- [ ] Funções com responsabilidade única
- [ ] Máximo 20 linhas por função
- [ ] Sem código duplicado
- [ ] Tratamento de erros explícito
- [ ] Logging estruturado
- [ ] Testes para lógica crítica
- [ ] Documentação com docstrings
- [ ] Type hints em Python
- [ ] Validação de entrada
- [ ] Respostas padronizadas
- [ ] Sem magic numbers
- [ ] Sem comentários óbvios
- [ ] Sem código comentado
- [ ] Sem imports não utilizados

---

## 10. EXEMPLO COMPLETO: Rota Refatorada

### Antes (Atual)
```python
@pdv_bp.route("/finalizar", methods=["POST"])
@funcionario_required
def finalizar_venda():
    try:
        current_user_id = get_jwt_identity()
        # ... 100+ linhas de código ...
        return jsonify({"success": True, "venda": venda.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### Depois (Refatorado)
```python
@pdv_bp.route("/finalizar", methods=["POST"])
@funcionario_required
@require_json
@validate_schema(FinalizarVendaSchema)
def finalizar_venda(validated_data):
    """Finaliza uma venda com múltiplos pagamentos"""
    logger = StructuredLogger(__name__)
    
    try:
        # 1. Validar contexto
        funcionario_id = get_jwt_identity()
        funcionario = Funcionario.query.get(funcionario_id)
        if not funcionario:
            raise ClienteNaoEncontradoError(funcionario_id)
        
        # 2. Validar caixa
        caixa = Caixa.query.filter_by(
            funcionario_id=funcionario_id,
            status="aberto"
        ).first()
        if not caixa:
            raise CaixaFechadoError()
        
        # 3. Validar estoque
        for item in validated_data.items:
            VendaService.validar_estoque(item.produto_id, item.quantidade)
        
        # 4. Criar venda
        venda = Venda(
            codigo=gerar_codigo_venda(),
            cliente_id=validated_data.cliente_id,
            funcionario_id=funcionario_id,
            caixa_id=caixa.id,
            total=calcular_total(validated_data),
            estabelecimento_id=funcionario.estabelecimento_id
        )
        db.session.add(venda)
        db.session.flush()
        
        # 5. Criar pagamentos
        VendaService.criar_pagamentos(
            venda.id,
            validated_data.pagamentos,
            funcionario.estabelecimento_id
        )
        
        # 6. Atualizar estoque
        for item in validated_data.items:
            VendaService.atualizar_estoque(
                item.produto_id,
                item.quantidade,
                venda.id,
                funcionario.estabelecimento_id
            )
        
        # 7. Commit
        db.session.commit()
        
        logger.info(
            "Venda finalizada",
            venda_id=venda.id,
            total=venda.total,
            funcionario_id=funcionario_id
        )
        
        return APIResponse.success(
            data=venda.to_dict(),
            message="Venda finalizada com sucesso",
            status_code=201
        )
        
    except APIError as e:
        db.session.rollback()
        logger.error("Erro na venda", exception=e, funcionario_id=funcionario_id)
        return APIResponse.error(e.code, e.message, e.details, e.status_code)
    
    except Exception as e:
        db.session.rollback()
        logger.error("Erro inesperado", exception=e, funcionario_id=funcionario_id)
        return APIResponse.error(
            "INTERNAL_ERROR",
            "Erro ao finalizar venda",
            status_code=500
        )
```

---

## CONCLUSÃO

Aplicando estes padrões:
- ✅ Código mais limpo e legível
- ✅ Mais fácil de manter
- ✅ Menos bugs
- ✅ Melhor performance
- ✅ Mais testável
- ✅ Melhor documentação

**Próximo Passo:** Refatorar `backend/app/routes/pdv.py` seguindo este padrão.
