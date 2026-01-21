# app/models.py
# SISTEMA ERP COMERCIAL COMPLETO - PADRÃO INDUSTRIAL BRASILEIRO
# Modelos completos com todas as tabelas necessárias para um ERP

from datetime import datetime, date
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# ============================================
# MIXINS REUTILIZÁVEIS
# ============================================


class EnderecoMixin:
    """Mixin para padronização de endereços"""

    cep = db.Column(db.String(9), nullable=False)
    logradouro = db.Column(db.String(200), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    pais = db.Column(db.String(50), default="Brasil")

    def endereco_completo(self):
        end = f"{self.logradouro}, {self.numero}"
        if self.complemento:
            end += f" - {self.complemento}"
        end += f" - {self.bairro} - {self.cidade}/{self.estado}"
        return end


# ============================================
# 1. ESTABELECIMENTO
# ============================================


class Estabelecimento(db.Model, EnderecoMixin):
    __tablename__ = "estabelecimentos"

    id = db.Column(db.Integer, primary_key=True)
    nome_fantasia = db.Column(db.String(150), nullable=False)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    inscricao_estadual = db.Column(db.String(20))
    telefone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    regime_tributario = db.Column(db.String(30), default="SIMPLES NACIONAL")
    ativo = db.Column(db.Boolean, default=True)
    data_abertura = db.Column(db.Date, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos serão definidos após as classes

    def to_dict(self):
        return {
            "id": self.id,
            "nome_fantasia": self.nome_fantasia,
            "cnpj": self.cnpj,
            "telefone": self.telefone,
            "email": self.email,
            "endereco_completo": self.endereco_completo(),
            "ativo": self.ativo,
        }


# ============================================
# 2. CONFIGURAÇÃO
# ============================================


class Configuracao(db.Model):
    __tablename__ = "configuracoes"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), unique=True
    )

    logo_url = db.Column(db.String(500))
    cor_principal = db.Column(db.String(7), default="#2563eb")

    emitir_nfe = db.Column(db.Boolean, default=False)
    emitir_nfce = db.Column(db.Boolean, default=True)

    desconto_maximo_funcionario = db.Column(db.Numeric(5, 2), default=10.00)
    controlar_validade = db.Column(db.Boolean, default=True)
    alerta_estoque_minimo = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("configuracao", uselist=False)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "logo_url": self.logo_url,
            "emitir_nfce": self.emitir_nfce,
            "desconto_maximo_funcionario": float(self.desconto_maximo_funcionario),
        }


# ============================================
# 3. FUNCIONÁRIO
# ============================================


class Funcionario(db.Model, UserMixin, EnderecoMixin):
    __tablename__ = "funcionarios"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date, nullable=False)

    telefone = db.Column(db.String(15), nullable=False)
    celular = db.Column(db.String(15))
    email = db.Column(db.String(100), nullable=False)

    cargo = db.Column(db.String(50), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False)
    salario_base = db.Column(db.Numeric(10, 2), default=0)

    username = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    foto_url = db.Column(db.String(500))
    role = db.Column(db.String(30), default="FUNCIONARIO")

    permissoes = db.Column(
        db.JSON,
        default=lambda: {
            "pdv": True,
            "estoque": True,
            "compras": False,
            "financeiro": False,
            "configuracoes": False,
        },
    )

    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("funcionarios", lazy="dynamic")
    )

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_active(self):
        return self.ativo

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "cargo": self.cargo,
            "telefone": self.telefone,
            "username": self.username,
            "role": self.role,
            "ativo": self.ativo,
        }


# ============================================
# 4. CLIENTE (APENAS CPF)
# ============================================


class Cliente(db.Model, EnderecoMixin):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)

    telefone = db.Column(db.String(15))
    celular = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100))

    limite_credito = db.Column(db.Numeric(10, 2), default=0)
    saldo_devedor = db.Column(db.Numeric(10, 2), default=0)

    ultima_compra = db.Column(db.DateTime)
    total_compras = db.Column(db.Integer, default=0)
    valor_total_gasto = db.Column(db.Numeric(12, 2), default=0)

    ativo = db.Column(db.Boolean, default=True)
    observacoes = db.Column(db.Text)

    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("clientes", lazy="dynamic")
    )
    vendas = db.relationship("Venda", backref="cliente", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "celular": self.celular,
            "email": self.email,
            "endereco_completo": self.endereco_completo(),
            "limite_credito": float(self.limite_credito),
            "saldo_devedor": float(self.saldo_devedor),
            "total_compras": self.total_compras,
            "ativo": self.ativo,
        }


# ============================================
# 5. FORNECEDOR
# ============================================


class Fornecedor(db.Model, EnderecoMixin):
    __tablename__ = "fornecedores"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    nome_fantasia = db.Column(db.String(150), nullable=False)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), nullable=False)
    inscricao_estadual = db.Column(db.String(20))

    telefone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    contato_nome = db.Column(db.String(100))
    contato_telefone = db.Column(db.String(15))

    prazo_entrega = db.Column(db.Integer, default=7)
    forma_pagamento = db.Column(db.String(50), default="30 DIAS")

    classificacao = db.Column(db.String(20), default="REGULAR")
    total_compras = db.Column(db.Integer, default=0)
    valor_total_comprado = db.Column(db.Numeric(12, 2), default=0)

    ativo = db.Column(db.Boolean, default=True)

    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("fornecedores", lazy="dynamic")
    )
    produtos = db.relationship("Produto", backref="fornecedor", lazy="dynamic")
    pedidos_compra = db.relationship(
        "PedidoCompra", backref="fornecedor", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome_fantasia": self.nome_fantasia,
            "cnpj": self.cnj,
            "telefone": self.telefone,
            "email": self.email,
            "endereco_completo": self.endereco_completo(),
            "contato_nome": self.contato_nome,
            "ativo": self.ativo,
        }


# ============================================
# 6. PRODUTO
# ============================================


class Produto(db.Model):
    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"))

    codigo_barras = db.Column(db.String(50), unique=True)
    codigo_interno = db.Column(db.String(50), unique=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    marca = db.Column(db.String(50))

    categoria = db.Column(db.String(50), nullable=False)
    subcategoria = db.Column(db.String(50))
    unidade_medida = db.Column(db.String(20), default="UN")

    quantidade = db.Column(db.Integer, default=0)
    quantidade_minima = db.Column(db.Integer, default=10)

    preco_custo = db.Column(db.Numeric(10, 2), nullable=False)
    preco_venda = db.Column(db.Numeric(10, 2), nullable=False)
    margem_lucro = db.Column(db.Numeric(5, 2))

    ncm = db.Column(db.String(8))
    origem = db.Column(db.Integer, default=0)

    total_vendido = db.Column(db.Float, default=0.0)
    quantidade_vendida = db.Column(db.Integer, default=0)
    ultima_venda = db.Column(db.DateTime)

    classificacao_abc = db.Column(db.String(1))

    controlar_validade = db.Column(db.Boolean, default=False)
    data_validade = db.Column(db.Date)
    lote = db.Column(db.String(50))

    imagem_url = db.Column(db.String(255))

    ativo = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("produtos", lazy="dynamic")
    )
    fornecedor = db.relationship(
        "Fornecedor", backref=db.backref("produtos_fornecedor", lazy="dynamic")
    )
    itens_venda = db.relationship("VendaItem", backref="produto", lazy="dynamic")
    itens_compra = db.relationship(
        "PedidoCompraItem", backref="produto", lazy="dynamic"
    )
    movimentacoes = db.relationship(
        "MovimentacaoEstoque", backref="produto", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigo_barras": self.codigo_barras,
            "nome": self.nome,
            "categoria": self.categoria,
            "quantidade": self.quantidade,
            "preco_custo": float(self.preco_custo),
            "preco_venda": float(self.preco_venda),
            "ativo": self.ativo,
            "fornecedor": self.fornecedor.to_dict() if self.fornecedor else None,
        }


# ============================================
# 7. CATEGORIA DE PRODUTO
# ============================================


class CategoriaProduto(db.Model):
    __tablename__ = "categorias_produto"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text)
    codigo = db.Column(db.String(20), unique=True)

    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("categorias", lazy="dynamic")
    )
    produtos = db.relationship(
        "Produto",
        backref="categoria_obj",
        lazy="dynamic",
        foreign_keys="Produto.categoria",
        primaryjoin="and_(CategoriaProduto.nome==Produto.categoria, "
        "CategoriaProduto.estabelecimento_id==Produto.estabelecimento_id)",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "codigo": self.codigo,
            "ativo": self.ativo,
        }


# ============================================
# 8. VENDA
# ============================================


class Venda(db.Model):
    __tablename__ = "vendas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"))
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    codigo = db.Column(db.String(50), unique=True, nullable=False)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    desconto = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    forma_pagamento = db.Column(db.String(50), nullable=False)
    valor_recebido = db.Column(db.Numeric(10, 2), nullable=False)
    troco = db.Column(db.Numeric(10, 2), default=0)

    status = db.Column(db.String(20), default="finalizada")

    quantidade_itens = db.Column(db.Integer, default=0)
    observacoes = db.Column(db.Text)

    data_venda = db.Column(db.DateTime, default=datetime.utcnow)
    data_cancelamento = db.Column(db.DateTime)
    motivo_cancelamento = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("vendas", lazy="dynamic")
    )
    cliente = db.relationship(
        "Cliente", backref=db.backref("vendas_cliente", lazy="dynamic")
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("vendas_funcionario", lazy="dynamic")
    )
    itens = db.relationship(
        "VendaItem", backref="venda", lazy="dynamic", cascade="all, delete-orphan"
    )
    movimentacoes = db.relationship(
        "MovimentacaoEstoque", backref="venda", lazy="dynamic"
    )
    pagamentos = db.relationship(
        "Pagamento", backref="venda", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "cliente": self.cliente.to_dict() if self.cliente else None,
            "funcionario": self.funcionario.to_dict() if self.funcionario else None,
            "subtotal": float(self.subtotal),
            "desconto": float(self.desconto),
            "total": float(self.total),
            "forma_pagamento": self.forma_pagamento,
            "data_venda": self.data_venda.isoformat() if self.data_venda else None,
            "status": self.status,
            "itens": [item.to_dict() for item in self.itens],
            "pagamentos": [pagamento.to_dict() for pagamento in self.pagamentos],
        }


# ============================================
# 9. ITEM DE VENDA
# ============================================


class VendaItem(db.Model):
    __tablename__ = "venda_itens"

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)

    produto_nome = db.Column(db.String(100), nullable=False)
    produto_codigo = db.Column(db.String(50))
    produto_unidade = db.Column(db.String(20))

    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    desconto = db.Column(db.Numeric(10, 2), default=0)
    total_item = db.Column(db.Numeric(10, 2), nullable=False)

    custo_unitario = db.Column(db.Numeric(10, 2))
    margem_item = db.Column(db.Numeric(5, 2))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "quantidade": self.quantidade,
            "preco_unitario": float(self.preco_unitario),
            "total_item": float(self.total_item),
        }


# ============================================
# 10. PAGAMENTO
# ============================================


class Pagamento(db.Model):
    __tablename__ = "pagamentos"

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=False)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    forma_pagamento = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    troco = db.Column(db.Numeric(10, 2), default=0)

    status = db.Column(db.String(20), default="aprovado")
    data_pagamento = db.Column(db.DateTime, default=datetime.utcnow)

    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("pagamentos", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "forma_pagamento": self.forma_pagamento,
            "valor": float(self.valor),
            "troco": float(self.troco),
            "status": self.status,
            "data_pagamento": (
                self.data_pagamento.isoformat() if self.data_pagamento else None
            ),
        }


# ============================================
# 11. MOVIMENTAÇÃO DE ESTOQUE
# ============================================


class MovimentacaoEstoque(db.Model):
    __tablename__ = "movimentacoes_estoque"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)

    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"))
    pedido_compra_id = db.Column(db.Integer, db.ForeignKey("pedidos_compra.id"))
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"))

    tipo = db.Column(db.String(20), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    quantidade_anterior = db.Column(db.Integer, nullable=False)
    quantidade_atual = db.Column(db.Integer, nullable=False)

    custo_unitario = db.Column(db.Numeric(10, 2))
    valor_total = db.Column(db.Numeric(10, 2))

    motivo = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("movimentacoes_estoque", lazy="dynamic")
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("movimentacoes_funcionario", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "tipo": self.tipo,
            "quantidade": self.quantidade,
            "quantidade_atual": self.quantidade_atual,
            "motivo": self.motivo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================
# 12. PEDIDO DE COMPRA
# ============================================


class PedidoCompra(db.Model):
    __tablename__ = "pedidos_compra"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    fornecedor_id = db.Column(
        db.Integer, db.ForeignKey("fornecedores.id"), nullable=False
    )
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    numero_pedido = db.Column(db.String(50), unique=True, nullable=False)

    data_pedido = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_previsao_entrega = db.Column(db.Date)
    data_recebimento = db.Column(db.Date)

    status = db.Column(db.String(20), default="pendente")

    subtotal = db.Column(db.Numeric(10, 2), default=0)
    desconto = db.Column(db.Numeric(10, 2), default=0)
    frete = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), default=0)

    condicao_pagamento = db.Column(db.String(50))

    numero_nota_fiscal = db.Column(db.String(50))
    serie_nota_fiscal = db.Column(db.String(10))

    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("pedidos_compra", lazy="dynamic")
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("pedidos_funcionario", lazy="dynamic")
    )
    itens = db.relationship(
        "PedidoCompraItem",
        backref="pedido",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    conta_pagar = db.relationship(
        "ContaPagar",
        backref="pedido_compra",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "numero_pedido": self.numero_pedido,
            "fornecedor": self.fornecedor.to_dict() if self.fornecedor else None,
            "status": self.status,
            "data_pedido": self.data_pedido.isoformat() if self.data_pedido else None,
            "total": float(self.total),
            "itens": [item.to_dict() for item in self.itens],
        }


# ============================================
# 13. ITEM DE PEDIDO DE COMPRA
# ============================================


class PedidoCompraItem(db.Model):
    __tablename__ = "pedido_compra_itens"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(
        db.Integer, db.ForeignKey("pedidos_compra.id"), nullable=False
    )
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)

    produto_nome = db.Column(db.String(100), nullable=False)
    produto_unidade = db.Column(db.String(20), default="UN")

    quantidade_solicitada = db.Column(db.Integer, nullable=False)
    quantidade_recebida = db.Column(db.Integer, default=0)

    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    desconto_percentual = db.Column(db.Numeric(5, 2), default=0)
    total_item = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(db.String(20), default="pendente")

    def to_dict(self):
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "quantidade_solicitada": self.quantidade_solicitada,
            "quantidade_recebida": self.quantidade_recebida,
            "preco_unitario": float(self.preco_unitario),
            "total_item": float(self.total_item),
            "status": self.status,
        }


# ============================================
# 14. CONTA A PAGAR
# ============================================


class ContaPagar(db.Model):
    __tablename__ = "contas_pagar"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    fornecedor_id = db.Column(
        db.Integer, db.ForeignKey("fornecedores.id"), nullable=False
    )
    pedido_compra_id = db.Column(db.Integer, db.ForeignKey("pedidos_compra.id"))

    numero_documento = db.Column(db.String(50), nullable=False)
    tipo_documento = db.Column(db.String(30), default="duplicata")

    valor_original = db.Column(db.Numeric(10, 2), nullable=False)
    valor_pago = db.Column(db.Numeric(10, 2), default=0)
    valor_atual = db.Column(db.Numeric(10, 2), nullable=False)

    data_emissao = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)

    status = db.Column(db.String(20), default="aberto")
    forma_pagamento = db.Column(db.String(30))

    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("contas_pagar", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "fornecedor_id": self.fornecedor_id,
            "numero_documento": self.numero_documento,
            "valor_original": float(self.valor_original),
            "valor_atual": float(self.valor_atual),
            "data_vencimento": (
                self.data_vencimento.isoformat() if self.data_vencimento else None
            ),
            "data_pagamento": (
                self.data_pagamento.isoformat() if self.data_pagamento else None
            ),
            "status": self.status,
        }


# ============================================
# 15. CONTA A RECEBER
# ============================================


class ContaReceber(db.Model):
    __tablename__ = "contas_receber"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"))
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"))

    numero_documento = db.Column(db.String(50), nullable=False)
    tipo_documento = db.Column(db.String(30), default="duplicata")

    valor_original = db.Column(db.Numeric(10, 2), nullable=False)
    valor_recebido = db.Column(db.Numeric(10, 2), default=0)
    valor_atual = db.Column(db.Numeric(10, 2), nullable=False)

    data_emissao = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_recebimento = db.Column(db.Date)

    status = db.Column(db.String(20), default="aberto")
    forma_recebimento = db.Column(db.String(30))

    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("contas_receber", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "numero_documento": self.numero_documento,
            "valor_original": float(self.valor_original),
            "valor_atual": float(self.valor_atual),
            "data_vencimento": (
                self.data_vencimento.isoformat() if self.data_vencimento else None
            ),
            "data_recebimento": (
                self.data_recebimento.isoformat() if self.data_recebimento else None
            ),
            "status": self.status,
        }


# ============================================
# 16. DESPESA
# ============================================


class Despesa(db.Model):
    __tablename__ = "despesas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"))

    descricao = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(50), default="geral")
    tipo = db.Column(db.String(20), default="variavel")

    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data_despesa = db.Column(db.Date, nullable=False, default=date.today)

    forma_pagamento = db.Column(db.String(50))
    recorrente = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("despesas", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "valor": float(self.valor),
            "data_despesa": (
                self.data_despesa.isoformat() if self.data_despesa else None
            ),
            "forma_pagamento": self.forma_pagamento,
            "recorrente": self.recorrente,
        }


# ============================================
# 17. HISTÓRICO DE LOGIN
# ============================================


class LoginHistory(db.Model):
    __tablename__ = "login_history"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=True
    )
    username = db.Column(db.String(100), nullable=False)
    estabelecimento_id = db.Column(db.Integer, nullable=False)

    ip_address = db.Column(db.String(45), nullable=False)
    dispositivo = db.Column(db.String(200))
    user_agent = db.Column(db.Text)

    success = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    funcionario = db.relationship(
        "Funcionario", backref=db.backref("logins", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "funcionario_id": self.funcionario_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "dispositivo": self.dispositivo,
            "success": self.success,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================
# 18. DASHBOARD MÉTRICAS
# ============================================


class DashboardMetrica(db.Model):
    __tablename__ = "dashboard_metricas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    data_referencia = db.Column(db.Date, nullable=False)

    total_vendas_dia = db.Column(db.Numeric(10, 2), default=0)
    quantidade_vendas_dia = db.Column(db.Integer, default=0)
    ticket_medio_dia = db.Column(db.Numeric(10, 2), default=0)
    clientes_atendidos_dia = db.Column(db.Integer, default=0)

    total_vendas_mes = db.Column(db.Numeric(12, 2), default=0)
    total_despesas_mes = db.Column(db.Numeric(12, 2), default=0)
    lucro_bruto_mes = db.Column(db.Numeric(12, 2), default=0)

    crescimento_vs_ontem = db.Column(db.Numeric(5, 2), default=0)
    crescimento_mensal = db.Column(db.Numeric(5, 2), default=0)
    tendencia_vendas = db.Column(db.String(20))

    top_produtos_json = db.Column(db.Text)
    produtos_abc_json = db.Column(db.Text)

    segmentacao_clientes_json = db.Column(db.Text)
    top_clientes_json = db.Column(db.Text)

    alertas_json = db.Column(db.Text)
    insights_json = db.Column(db.Text)

    data_calculo = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("metricas", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "data_referencia": (
                self.data_referencia.isoformat() if self.data_referencia else None
            ),
            "total_vendas_dia": float(self.total_vendas_dia),
            "quantidade_vendas_dia": self.quantidade_vendas_dia,
            "ticket_medio_dia": float(self.ticket_medio_dia),
            "total_vendas_mes": float(self.total_vendas_mes),
            "lucro_bruto_mes": float(self.lucro_bruto_mes),
            "crescimento_vs_ontem": float(self.crescimento_vs_ontem),
            "data_calculo": (
                self.data_calculo.isoformat() if self.data_calculo else None
            ),
        }


# ============================================
# 19. RELATÓRIO AGENDADO
# ============================================


class RelatorioAgendado(db.Model):
    __tablename__ = "relatorios_agendados"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    formato = db.Column(db.String(10), nullable=False)
    frequencia = db.Column(db.String(20), nullable=False)

    horario_envio = db.Column(db.Time, nullable=False)

    destinatarios_email = db.Column(db.JSON)
    enviar_para_proprietario = db.Column(db.Boolean, default=True)

    parametros = db.Column(db.JSON)

    ativo = db.Column(db.Boolean, default=True)
    ultima_execucao = db.Column(db.DateTime)
    proxima_execucao = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("relatorios", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "formato": self.formato,
            "frequencia": self.frequencia,
            "horario_envio": (
                self.horario_envio.strftime("%H:%M") if self.horario_envio else None
            ),
            "ativo": self.ativo,
            "ultima_execucao": (
                self.ultima_execucao.isoformat() if self.ultima_execucao else None
            ),
            "proxima_execucao": (
                self.proxima_execucao.isoformat() if self.proxima_execucao else None
            ),
        }


# ============================================
# 20. ANÁLISE PREDITIVA
# ============================================


class AnalisePreditiva(db.Model):
    __tablename__ = "analises_preditivas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    tipo = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)

    parametros = db.Column(db.JSON)
    metricas = db.Column(db.JSON)

    dados_treinamento_inicio = db.Column(db.Date)
    dados_treinamento_fim = db.Column(db.Date)
    tamanho_treinamento = db.Column(db.Integer)

    status = db.Column(db.String(20), default="treinado")
    ultimo_treinamento = db.Column(db.DateTime)
    proximo_treinamento = db.Column(db.DateTime)

    precisao = db.Column(db.Numeric(5, 2), default=0)
    recall = db.Column(db.Numeric(5, 2), default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("analises", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "modelo": self.modelo,
            "status": self.status,
            "precisao": float(self.precisao),
            "ultimo_treinamento": (
                self.ultimo_treinamento.isoformat() if self.ultimo_treinamento else None
            ),
            "proximo_treinamento": (
                self.proximo_treinamento.isoformat()
                if self.proximo_treinamento
                else None
            ),
        }


# ============================================
# 21. SERVIÇO (opcional, para estabelecimentos que oferecem serviços)
# ============================================


class Servico(db.Model):
    __tablename__ = "servicos"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    codigo = db.Column(db.String(50), unique=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)

    valor = db.Column(db.Numeric(10, 2), nullable=False)
    duracao = db.Column(db.Integer)  # minutos

    categoria = db.Column(db.String(50))
    ativo = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("servicos", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nome": self.nome,
            "descricao": self.descricao,
            "valor": float(self.valor),
            "duracao": self.duracao,
            "categoria": self.categoria,
            "ativo": self.ativo,
        }


# ============================================
# 22. CAIXA (controle de abertura/fechamento de caixa)
# ============================================


class Caixa(db.Model):
    __tablename__ = "caixas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    numero_caixa = db.Column(db.String(20), nullable=False)

    saldo_inicial = db.Column(db.Numeric(10, 2), nullable=False)
    saldo_final = db.Column(db.Numeric(10, 2))
    saldo_atual = db.Column(db.Numeric(10, 2))

    data_abertura = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_fechamento = db.Column(db.DateTime)

    status = db.Column(db.String(20), default="aberto")
    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("caixas", lazy="dynamic")
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("caixas_funcionario", lazy="dynamic")
    )
    movimentacoes = db.relationship(
        "MovimentacaoCaixa",
        backref="caixa",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "numero_caixa": self.numero_caixa,
            "funcionario": self.funcionario.to_dict() if self.funcionario else None,
            "saldo_inicial": float(self.saldo_inicial),
            "saldo_atual": float(self.saldo_atual),
            "data_abertura": (
                self.data_abertura.isoformat() if self.data_abertura else None
            ),
            "data_fechamento": (
                self.data_fechamento.isoformat() if self.data_fechamento else None
            ),
            "status": self.status,
        }


# ============================================
# 23. MOVIMENTAÇÃO DE CAIXA
# ============================================


class MovimentacaoCaixa(db.Model):
    __tablename__ = "movimentacoes_caixa"

    id = db.Column(db.Integer, primary_key=True)
    caixa_id = db.Column(db.Integer, db.ForeignKey("caixas.id"), nullable=False)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    tipo = db.Column(db.String(20), nullable=False)  # entrada, saida
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50))

    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"))
    descricao = db.Column(db.String(255), nullable=False)

    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("movimentacoes_caixa", lazy="dynamic")
    )
    venda = db.relationship(
        "Venda", backref=db.backref("movimentacoes_caixa_venda", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "caixa_id": self.caixa_id,
            "tipo": self.tipo,
            "valor": float(self.valor),
            "forma_pagamento": self.forma_pagamento,
            "descricao": self.descricao,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================
# 24. TRANSPORTADORA (para controle de entregas)
# ============================================


class Transportadora(db.Model, EnderecoMixin):
    __tablename__ = "transportadoras"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    nome_fantasia = db.Column(db.String(150), nullable=False)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), nullable=False)

    telefone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    contato = db.Column(db.String(100))
    telefone_contato = db.Column(db.String(15))

    taxa_frete = db.Column(db.Numeric(10, 2), default=0)
    prazo_entrega = db.Column(db.Integer, default=5)  # dias

    ativo = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("transportadoras", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome_fantasia": self.nome_fantasia,
            "cnpj": self.cnpj,
            "telefone": self.telefone,
            "email": self.email,
            "endereco_completo": self.endereco_completo(),
            "taxa_frete": float(self.taxa_frete),
            "prazo_entrega": self.prazo_entrega,
            "ativo": self.ativo,
        }


# ============================================
# 25. ORDEM DE SERVIÇO
# ============================================


class OrdemServico(db.Model):
    __tablename__ = "ordens_servico"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    numero_os = db.Column(db.String(50), unique=True, nullable=False)

    equipamento = db.Column(db.String(200), nullable=False)
    problema = db.Column(db.Text, nullable=False)
    diagnostico = db.Column(db.Text)
    solucao = db.Column(db.Text)

    valor_servico = db.Column(db.Numeric(10, 2), default=0)
    valor_pecas = db.Column(db.Numeric(10, 2), default=0)
    valor_total = db.Column(db.Numeric(10, 2), default=0)

    data_abertura = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_previsao = db.Column(db.Date)
    data_conclusao = db.Column(db.DateTime)

    status = db.Column(db.String(20), default="aberta")

    garantia = db.Column(db.Integer)  # dias de garantia
    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("ordens_servico", lazy="dynamic")
    )
    cliente = db.relationship(
        "Cliente", backref=db.backref("ordens_cliente", lazy="dynamic")
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("ordens_funcionario", lazy="dynamic")
    )
    itens = db.relationship(
        "OrdemServicoItem",
        backref="ordem_servico",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "numero_os": self.numero_os,
            "cliente": self.cliente.to_dict() if self.cliente else None,
            "equipamento": self.equipamento,
            "problema": self.problema,
            "status": self.status,
            "valor_total": float(self.valor_total),
            "data_abertura": (
                self.data_abertura.isoformat() if self.data_abertura else None
            ),
            "data_conclusao": (
                self.data_conclusao.isoformat() if self.data_conclusao else None
            ),
        }


# ============================================
# 26. ITEM DE ORDEM DE SERVIÇO
# ============================================


class OrdemServicoItem(db.Model):
    __tablename__ = "ordem_servico_itens"

    id = db.Column(db.Integer, primary_key=True)
    ordem_servico_id = db.Column(
        db.Integer, db.ForeignKey("ordens_servico.id"), nullable=False
    )
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"))

    tipo = db.Column(db.String(20), nullable=False)  # produto, servico
    descricao = db.Column(db.String(200), nullable=False)

    quantidade = db.Column(db.Integer, default=1)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    produto = db.relationship("Produto", backref=db.backref("itens_os", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "quantidade": self.quantidade,
            "valor_unitario": float(self.valor_unitario),
            "valor_total": float(self.valor_total),
        }


# ============================================
# 27. BLOCO DE NOTAS
# ============================================


class BlocoNota(db.Model):
    __tablename__ = "bloco_notas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)

    cor = db.Column(db.String(10), default="#ffffff")
    fixado = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("bloco_notas", lazy="dynamic")
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("bloco_notas_funcionario", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "cor": self.cor,
            "fixado": self.fixado,
            "funcionario": self.funcionario.to_dict() if self.funcionario else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================
# 28. HISTÓRICO DE ALTERAÇÕES
# ============================================


class HistoricoAlteracao(db.Model):
    __tablename__ = "historico_alteracoes"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    tabela = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)

    acao = db.Column(db.String(20), nullable=False)  # CREATE, UPDATE, DELETE
    dados_anteriores = db.Column(db.JSON)
    dados_novos = db.Column(db.JSON)

    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("historico_alteracoes", lazy="dynamic")
    )
    funcionario = db.relationship(
        "Funcionario",
        backref=db.backref("historico_alteracoes_funcionario", lazy="dynamic"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "tabela": self.tabela,
            "registro_id": self.registro_id,
            "acao": self.acao,
            "funcionario": self.funcionario.to_dict() if self.funcionario else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================
# 29. PARÂMETRO DO SISTEMA
# ============================================


class ParametroSistema(db.Model):
    __tablename__ = "parametros_sistema"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    chave = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Text)
    tipo = db.Column(db.String(20), default="string")  # string, number, boolean, json

    descricao = db.Column(db.Text)
    grupo = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("parametros", lazy="dynamic")
    )

    __table_args__ = (
        db.UniqueConstraint(
            "estabelecimento_id", "chave", name="uq_parametro_estab_chave"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "chave": self.chave,
            "valor": self.valor,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "grupo": self.grupo,
        }


# ============================================
# 30. BACKUP (controle de backups)
# ============================================


class Backup(db.Model):
    __tablename__ = "backups"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=True
    )

    nome_arquivo = db.Column(db.String(200), nullable=False)
    tamanho = db.Column(db.BigInteger)  # bytes
    tipo = db.Column(db.String(20), default="automatico")  # automatico, manual

    caminho = db.Column(db.String(500))
    hash_arquivo = db.Column(db.String(64))  # SHA256

    status = db.Column(db.String(20), default="sucesso")  # sucesso, falha, pendente
    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("backups", lazy="dynamic")
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("backups_funcionario", lazy="dynamic")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome_arquivo": self.nome_arquivo,
            "tamanho": self.tamanho,
            "tipo": self.tipo,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

ItemVenda = VendaItem
