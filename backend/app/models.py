# app/models.py - VERSÃO COMPLETA CORRIGIDA
# SISTEMA ERP COMERCIAL COMPLETO - PADRÃO INDUSTRIAL BRASILEIRO
# Versão completa com todas as tabelas necessárias

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
        end += f" - {self.bairro} - {self.cidade}/{self.estado} - {self.cep}"
        return end


# ============================================
# 1. ESTABELECIMENTO
# ============================================


class Estabelecimento(db.Model, EnderecoMixin):
    __tablename__ = "estabelecimentos"

    id = db.Column(db.Integer, primary_key=True)
    nome_fantasia = db.Column(db.String(150), nullable=False)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), nullable=False)
    inscricao_estadual = db.Column(db.String(20))
    telefone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    regime_tributario = db.Column(db.String(30), default="SIMPLES NACIONAL")
    ativo = db.Column(db.Boolean, default=True)
    data_abertura = db.Column(db.Date, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("idx_estabelecimento_cnpj", "cnpj"),
        db.UniqueConstraint("cnpj", name="uq_estabelecimento_cnpj"),
    )

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
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        unique=True,
    )

    logo_url = db.Column(db.String(500))
    logo_base64 = db.Column(db.Text)  # Para persistência em deploy serverless/online
    cor_principal = db.Column(db.String(7), default="#2563eb")
    tema_escuro = db.Column(db.Boolean, default=False)

    # Vendas / PDV
    emitir_nfe = db.Column(db.Boolean, default=False)
    emitir_nfce = db.Column(db.Boolean, default=True)
    impressao_automatica = db.Column(db.Boolean, default=False)
    tipo_impressora = db.Column(db.String(20), default="termica_80mm") # termica_80mm, termica_58mm, a4
    exibir_preco_tela = db.Column(db.Boolean, default=True)
    permitir_venda_sem_estoque = db.Column(db.Boolean, default=False)
    desconto_maximo_percentual = db.Column(db.Numeric(5, 2), default=10.00)
    desconto_maximo_funcionario = db.Column(db.Numeric(5, 2), default=10.00)
    arredondamento_valores = db.Column(db.Boolean, default=True)
    formas_pagamento = db.Column(db.Text, default='["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"]')

    # Estoque
    controlar_validade = db.Column(db.Boolean, default=True)
    alerta_estoque_minimo = db.Column(db.Boolean, default=True)
    dias_alerta_validade = db.Column(db.Integer, default=30)
    estoque_minimo_padrao = db.Column(db.Integer, default=10)

    # Segurança / Sistema
    tempo_sessao_minutos = db.Column(db.Integer, default=30)
    tentativas_senha_bloqueio = db.Column(db.Integer, default=3)
    
    # Notificações
    alertas_email = db.Column(db.Boolean, default=False)
    alertas_whatsapp = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento",
        backref=db.backref("configuracao", uselist=False, cascade="all, delete-orphan"),
    )

    def to_dict(self):
        try:
            formas_pagamento_list = json.loads(self.formas_pagamento) if self.formas_pagamento else []
        except:
            formas_pagamento_list = ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"]

        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "logo_url": self.logo_base64 if self.logo_base64 else self.logo_url,
            "cor_principal": self.cor_principal,
            "tema_escuro": self.tema_escuro,
            "emitir_nfe": self.emitir_nfe,
            "emitir_nfce": self.emitir_nfce,
            "impressao_automatica": self.impressao_automatica,
            "tipo_impressora": self.tipo_impressora,
            "exibir_preco_tela": self.exibir_preco_tela,
            "permitir_venda_sem_estoque": self.permitir_venda_sem_estoque,
            "desconto_maximo_percentual": float(self.desconto_maximo_percentual) if self.desconto_maximo_percentual else 0.0,
            "desconto_maximo_funcionario": float(self.desconto_maximo_funcionario) if self.desconto_maximo_funcionario else 0.0,
            "arredondamento_valores": self.arredondamento_valores,
            "formas_pagamento": formas_pagamento_list,
            "controlar_validade": self.controlar_validade,
            "alerta_estoque_minimo": self.alerta_estoque_minimo,
            "dias_alerta_validade": self.dias_alerta_validade,
            "estoque_minimo_padrao": self.estoque_minimo_padrao,
            "tempo_sessao_minutos": self.tempo_sessao_minutos,
            "tentativas_senha_bloqueio": self.tentativas_senha_bloqueio,
            "alertas_email": self.alertas_email,
            "alertas_whatsapp": self.alertas_whatsapp
        }


# ============================================
# 3. FUNCIONÁRIO
# ============================================


class Funcionario(db.Model, UserMixin, EnderecoMixin):
    __tablename__ = "funcionarios"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )

    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date, nullable=False)

    celular = db.Column(db.String(15), nullable=False)
    telefone = db.Column(db.String(15))
    email = db.Column(db.String(100), nullable=False)

    cargo = db.Column(db.String(50), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False)
    salario_base = db.Column(db.Numeric(10, 2), default=0)

    username = db.Column(db.String(50), nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    foto_url = db.Column(db.String(500))
    role = db.Column(db.String(30), default="FUNCIONARIO")
    status = db.Column(db.String(20), default="ativo")

    # PROPRIEDADES NECESSÁRIAS PARA FLASK-LOGIN
    @property
    def is_authenticated(self):
        """Retorna True se o usuário está autenticado"""
        return True if self.ativo else False

    @property
    def is_active(self):
        """Retorna True se a conta está ativa"""
        return self.ativo

    @property
    def is_anonymous(self):
        """Retorna False para usuários reais"""
        return False

    def get_id(self):
        """Retorna o ID do usuário como string (requerido pelo Flask-Login)"""
        return str(self.id)

    def get_username(self):
        """Retorna o username"""
        return self.username

    # Para compatibilidade com SQLite, usamos Text e fazemos parse manual
    permissoes_json = db.Column(
        db.Text,
        default='{"pdv": true, "estoque": true, "compras": false, "financeiro": false, "configuracoes": false}',
    )

    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento",
        backref=db.backref("funcionarios", lazy=True, cascade="all, delete-orphan"),
    )

    __table_args__ = (
        db.Index("idx_funcionario_cpf", "cpf"),
        db.Index("idx_funcionario_estabelecimento", "estabelecimento_id"),
        db.UniqueConstraint(
            "estabelecimento_id", "cpf", name="uq_funcionario_estab_cpf"
        ),
        db.UniqueConstraint(
            "estabelecimento_id", "username", name="uq_funcionario_estab_username"
        ),
    )

    @property
    def permissoes(self):
        try:
            return json.loads(self.permissoes_json)
        except:
            return {
                "pdv": True,
                "estoque": True,
                "compras": False,
                "financeiro": False,
                "configuracoes": False,
            }

    @permissoes.setter
    def permissoes(self, value):
        self.permissoes_json = json.dumps(value)

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
            "rg": self.rg,
            "data_nascimento": self.data_nascimento.isoformat() if self.data_nascimento else None,
            "telefone": self.telefone,
            "celular": self.celular,
            "email": self.email,
            "cep": self.cep,
            "logradouro": self.logradouro,
            "numero": self.numero,
            "complemento": self.complemento,
            "bairro": self.bairro,
            "cidade": self.cidade,
            "estado": self.estado,
            "pais": self.pais,
            "cargo": self.cargo,
            "data_admissao": self.data_admissao.isoformat() if self.data_admissao else None,
            "salario_base": float(self.salario_base) if self.salario_base else 0.0,
            "username": self.username,
            "role": self.role,
            "ativo": self.ativo,
            "permissoes": self.permissoes,
            # Campos de compatibilidade para frontend
            "usuario": self.username,
            "nivel_acesso": self.role,
            "salario": float(self.salario_base) if self.salario_base else 0.0,
        }


# ============================================
# 4. CLIENTE
# ============================================


class Cliente(db.Model, EnderecoMixin):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
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
        "Estabelecimento",
        backref=db.backref("clientes", lazy=True, cascade="all, delete-orphan"),
    )

    __table_args__ = (
        db.Index("idx_cliente_cpf", "cpf"),
        db.Index("idx_cliente_nome", "nome"),
        db.UniqueConstraint("estabelecimento_id", "cpf", name="uq_cliente_estab_cpf"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "celular": self.celular,
            "email": self.email,
            "endereco_completo": self.endereco_completo(),
            "limite_credito": (
                float(self.limite_credito) if self.limite_credito else 0.0
            ),
            "saldo_devedor": float(self.saldo_devedor) if self.saldo_devedor else 0.0,
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
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
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
        "Estabelecimento",
        backref=db.backref("fornecedores", lazy=True, cascade="all, delete-orphan"),
    )

    __table_args__ = (
        db.Index("idx_fornecedor_cnpj", "cnpj"),
        db.UniqueConstraint(
            "estabelecimento_id", "cnpj", name="uq_fornecedor_estab_cnpj"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome_fantasia": self.nome_fantasia,
            "cnpj": self.cnpj,
            "telefone": self.telefone,
            "email": self.email,
            "endereco_completo": self.endereco_completo(),
            "contato_nome": self.contato_nome,
            "ativo": self.ativo,
        }


# ============================================
# 6. CATEGORIA DE PRODUTO
# ============================================


class CategoriaProduto(db.Model):
    __tablename__ = "categorias_produto"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )

    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text)
    codigo = db.Column(db.String(20))

    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento",
        backref=db.backref(
            "categorias_produto", lazy=True, cascade="all, delete-orphan"
        ),
    )

    __table_args__ = (
        db.Index("idx_categoria_nome", "nome"),
        db.UniqueConstraint(
            "estabelecimento_id", "nome", name="uq_categoria_estab_nome"
        ),
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
# 7. PRODUTO
# ============================================


class Produto(db.Model):
    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )
    categoria_id = db.Column(
        db.Integer, db.ForeignKey("categorias_produto.id"), nullable=False
    )
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"))

    codigo_barras = db.Column(db.String(50))
    codigo_interno = db.Column(db.String(50))
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    marca = db.Column(db.String(50))
    fabricante = db.Column(db.String(100))  # Adicionado campo fabricante

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
        "Estabelecimento", backref=db.backref("produtos", lazy=True)
    )
    categoria = db.relationship(
        "CategoriaProduto", backref=db.backref("produtos", lazy=True)
    )
    fornecedor = db.relationship(
        "Fornecedor", backref=db.backref("produtos", lazy=True)
    )

    __table_args__ = (
        db.Index("idx_produto_nome", "nome"),
        db.Index("idx_produto_codigo", "codigo_interno"),
        db.Index("idx_produto_categoria", "categoria_id"),
        db.UniqueConstraint(
            "estabelecimento_id", "codigo_interno", name="uq_produto_estab_codigo"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigo_barras": self.codigo_barras,
            "codigo_interno": self.codigo_interno,
            "nome": self.nome,
            "descricao": self.descricao,
            "marca": self.marca,
            "fabricante": self.fabricante,
            "unidade_medida": self.unidade_medida,
            "categoria": self.categoria.nome if self.categoria else None,
            "quantidade": self.quantidade,
            "quantidade_minima": self.quantidade_minima,
            "preco_custo": float(self.preco_custo) if self.preco_custo else 0.0,
            "preco_venda": float(self.preco_venda) if self.preco_venda else 0.0,
            "margem_lucro": float(self.margem_lucro) if self.margem_lucro else 0.0,
            "ativo": self.ativo,
            "fornecedor": self.fornecedor.to_dict() if self.fornecedor else None,
            "fornecedor_nome": self.fornecedor.nome_fantasia if self.fornecedor else None,
            "fornecedor_id": self.fornecedor_id,
            "data_validade": self.data_validade.isoformat() if self.data_validade else None,
            "lote": self.lote,
            "imagem_url": self.imagem_url,
            "controlar_validade": self.controlar_validade,
        }


# ============================================
# 8. VENDA
# ============================================


class Venda(db.Model):
    __tablename__ = "vendas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"))
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    codigo = db.Column(db.String(50), nullable=False)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    desconto = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    forma_pagamento = db.Column(db.String(50), nullable=False)
    valor_recebido = db.Column(db.Numeric(10, 2), default=0)
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
        "Estabelecimento", backref=db.backref("vendas", lazy=True)
    )
    cliente = db.relationship("Cliente", backref=db.backref("vendas", lazy=True))
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("vendas", lazy=True)
    )

    __table_args__ = (
        db.Index("idx_venda_codigo", "codigo"),
        db.Index("idx_venda_data", "data_venda"),
        db.UniqueConstraint(
            "estabelecimento_id", "codigo", name="uq_venda_estab_codigo"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "cliente": self.cliente.to_dict() if self.cliente else None,
            "funcionario": self.funcionario.to_dict() if self.funcionario else None,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
            "desconto": float(self.desconto) if self.desconto else 0.0,
            "total": float(self.total) if self.total else 0.0,
            "forma_pagamento": self.forma_pagamento,
            "data_venda": self.data_venda.isoformat() if self.data_venda else None,
            "status": self.status,
        }


# ============================================
# 9. ITEM DE VENDA
# ============================================


class VendaItem(db.Model):
    __tablename__ = "venda_itens"

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(
        db.Integer, db.ForeignKey("vendas.id", ondelete="CASCADE"), nullable=False
    )
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

    venda = db.relationship(
        "Venda", backref=db.backref("itens", lazy=True, cascade="all, delete-orphan")
    )
    produto = db.relationship("Produto", backref=db.backref("itens_venda", lazy=True))

    __table_args__ = (
        db.Index("idx_venda_item_venda", "venda_id"),
        db.Index("idx_venda_item_produto", "produto_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "quantidade": self.quantidade,
            "preco_unitario": (
                float(self.preco_unitario) if self.preco_unitario else 0.0
            ),
            "total_item": float(self.total_item) if self.total_item else 0.0,
        }


# ============================================
# 10. PAGAMENTO
# ============================================


class Pagamento(db.Model):
    __tablename__ = "pagamentos"

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(
        db.Integer, db.ForeignKey("vendas.id", ondelete="CASCADE"), nullable=False
    )
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )

    forma_pagamento = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    troco = db.Column(db.Numeric(10, 2), default=0)

    status = db.Column(db.String(20), default="aprovado")
    data_pagamento = db.Column(db.DateTime, default=datetime.utcnow)

    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("pagamentos", lazy=True)
    )
    venda = db.relationship(
        "Venda",
        backref=db.backref("pagamentos", lazy=True, cascade="all, delete-orphan"),
    )

    __table_args__ = (
        db.Index("idx_pagamento_venda", "venda_id"),
        db.Index("idx_pagamento_data", "data_pagamento"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "forma_pagamento": self.forma_pagamento,
            "valor": float(self.valor) if self.valor else 0.0,
            "troco": float(self.troco) if self.troco else 0.0,
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
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
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
        "Estabelecimento", backref=db.backref("movimentacoes_estoque", lazy=True)
    )
    produto = db.relationship("Produto", backref=db.backref("movimentacoes", lazy=True))
    venda = db.relationship(
        "Venda", backref=db.backref("movimentacoes_estoque_venda", lazy=True)
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("movimentacoes", lazy=True)
    )

    __table_args__ = (
        db.Index("idx_mov_estoque_produto", "produto_id"),
        db.Index("idx_mov_estoque_data", "created_at"),
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
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )
    fornecedor_id = db.Column(
        db.Integer, db.ForeignKey("fornecedores.id"), nullable=False
    )
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    numero_pedido = db.Column(db.String(50), nullable=False)

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
        "Estabelecimento", backref=db.backref("pedidos_compra", lazy=True)
    )
    fornecedor = db.relationship(
        "Fornecedor", backref=db.backref("pedidos_compra", lazy=True)
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("pedidos_compra", lazy=True)
    )

    __table_args__ = (
        db.Index("idx_pedido_numero", "numero_pedido"),
        db.UniqueConstraint(
            "estabelecimento_id", "numero_pedido", name="uq_pedido_estab_numero"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "numero_pedido": self.numero_pedido,
            "fornecedor": self.fornecedor.to_dict() if self.fornecedor else None,
            "status": self.status,
            "data_pedido": self.data_pedido.isoformat() if self.data_pedido else None,
            "total": float(self.total) if self.total else 0.0,
        }


# ============================================
# 13. ITEM DE PEDIDO DE COMPRA
# ============================================


class PedidoCompraItem(db.Model):
    __tablename__ = "pedido_compra_itens"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos_compra.id", ondelete="CASCADE"),
        nullable=False,
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

    pedido = db.relationship(
        "PedidoCompra",
        backref=db.backref("itens", lazy=True, cascade="all, delete-orphan"),
    )
    produto = db.relationship("Produto", backref=db.backref("itens_compra", lazy=True))

    __table_args__ = (db.Index("idx_pedido_item_pedido", "pedido_id"),)

    def to_dict(self):
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "quantidade_solicitada": self.quantidade_solicitada,
            "quantidade_recebida": self.quantidade_recebida,
            "preco_unitario": (
                float(self.preco_unitario) if self.preco_unitario else 0.0
            ),
            "total_item": float(self.total_item) if self.total_item else 0.0,
            "status": self.status,
        }


# ============================================
# 14. CONTA A PAGAR
# ============================================


class ContaPagar(db.Model):
    __tablename__ = "contas_pagar"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
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
        "Estabelecimento", backref=db.backref("contas_pagar", lazy=True)
    )
    fornecedor = db.relationship(
        "Fornecedor", backref=db.backref("contas_pagar", lazy=True)
    )
    pedido_compra = db.relationship(
        "PedidoCompra", backref=db.backref("conta_pagar", uselist=False)
    )

    __table_args__ = (
        db.Index("idx_conta_pagar_vencimento", "data_vencimento"),
        db.Index("idx_conta_pagar_status", "status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "fornecedor_id": self.fornecedor_id,
            "numero_documento": self.numero_documento,
            "valor_original": (
                float(self.valor_original) if self.valor_original else 0.0
            ),
            "valor_atual": float(self.valor_atual) if self.valor_atual else 0.0,
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
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
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
        "Estabelecimento", backref=db.backref("contas_receber", lazy=True)
    )
    cliente = db.relationship(
        "Cliente", backref=db.backref("contas_receber", lazy=True)
    )
    venda = db.relationship("Venda", backref=db.backref("contas_receber", lazy=True))

    __table_args__ = (
        db.Index("idx_conta_receber_vencimento", "data_vencimento"),
        db.Index("idx_conta_receber_cliente", "cliente_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "numero_documento": self.numero_documento,
            "valor_original": (
                float(self.valor_original) if self.valor_original else 0.0
            ),
            "valor_atual": float(self.valor_atual) if self.valor_atual else 0.0,
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
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
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
        "Estabelecimento", backref=db.backref("despesas", lazy=True)
    )
    fornecedor = db.relationship(
        "Fornecedor", backref=db.backref("despesas", lazy=True)
    )

    __table_args__ = (
        db.Index("idx_despesa_data", "data_despesa"),
        db.Index("idx_despesa_categoria", "categoria"),
    )

    def to_dict(self):
        result = {
            "id": self.id,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "tipo": self.tipo,
            "valor": float(self.valor) if self.valor else 0.0,
            "data_despesa": (
                self.data_despesa.isoformat() if self.data_despesa else None
            ),
            "forma_pagamento": self.forma_pagamento,
            "recorrente": self.recorrente,
            "observacoes": self.observacoes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if self.fornecedor:
            result["fornecedor"] = {
                "id": self.fornecedor.id,
                "nome": self.fornecedor.nome_fantasia
            }
        
        return result


# ============================================
# 17. HISTÓRICO DE LOGIN
# ============================================


class LoginHistory(db.Model):
    __tablename__ = "login_history"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"))
    username = db.Column(db.String(100), nullable=False)
    estabelecimento_id = db.Column(db.Integer, nullable=True)

    ip_address = db.Column(db.String(45), nullable=False)
    dispositivo = db.Column(db.String(200))
    user_agent = db.Column(db.Text)

    success = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)
    token_hash = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    funcionario = db.relationship(
        "Funcionario", backref=db.backref("logins", lazy=True)
    )

    __table_args__ = (
        db.Index("idx_login_history_user", "username"),
        db.Index("idx_login_history_data", "created_at"),
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
# 18. CAIXA
# ============================================


class Caixa(db.Model):
    __tablename__ = "caixas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
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
        "Estabelecimento", backref=db.backref("caixas", lazy=True)
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("caixas", lazy=True)
    )

    __table_args__ = (
        db.Index("idx_caixa_status", "status"),
        db.Index("idx_caixa_data", "data_abertura"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "numero_caixa": self.numero_caixa,
            "funcionario": self.funcionario.to_dict() if self.funcionario else None,
            "saldo_inicial": float(self.saldo_inicial) if self.saldo_inicial else 0.0,
            "saldo_atual": float(self.saldo_atual) if self.saldo_atual else 0.0,
            "data_abertura": (
                self.data_abertura.isoformat() if self.data_abertura else None
            ),
            "data_fechamento": (
                self.data_fechamento.isoformat() if self.data_fechamento else None
            ),
            "status": self.status,
        }


# ============================================
# 19. MOVIMENTAÇÃO DE CAIXA
# ============================================


class MovimentacaoCaixa(db.Model):
    __tablename__ = "movimentacoes_caixa"

    id = db.Column(db.Integer, primary_key=True)
    caixa_id = db.Column(
        db.Integer, db.ForeignKey("caixas.id", ondelete="CASCADE"), nullable=False
    )
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )

    tipo = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50))

    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"))
    descricao = db.Column(db.String(255), nullable=False)

    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("movimentacoes_caixa", lazy=True)
    )
    caixa = db.relationship(
        "Caixa",
        backref=db.backref("movimentacoes", lazy=True, cascade="all, delete-orphan"),
    )
    venda = db.relationship(
        "Venda", backref=db.backref("movimentacoes_caixa", lazy=True)
    )

    __table_args__ = (
        db.Index("idx_mov_caixa_caixa", "caixa_id"),
        db.Index("idx_mov_caixa_tipo", "tipo"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "caixa_id": self.caixa_id,
            "tipo": self.tipo,
            "valor": float(self.valor) if self.valor else 0.0,
            "forma_pagamento": self.forma_pagamento,
            "descricao": self.descricao,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================
# 20. DASHBOARD MÉTRICAS
# ============================================


class DashboardMetrica(db.Model):
    __tablename__ = "dashboard_metricas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
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

    # Armazenando JSON como Text para compatibilidade com SQLite
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
        "Estabelecimento", backref=db.backref("metricas", lazy=True)
    )

    __table_args__ = (db.Index("idx_metrica_data", "data_referencia"),)

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "data_referencia": (
                self.data_referencia.isoformat() if self.data_referencia else None
            ),
            "total_vendas_dia": (
                float(self.total_vendas_dia) if self.total_vendas_dia else 0.0
            ),
            "quantidade_vendas_dia": self.quantidade_vendas_dia,
            "ticket_medio_dia": (
                float(self.ticket_medio_dia) if self.ticket_medio_dia else 0.0
            ),
            "total_vendas_mes": (
                float(self.total_vendas_mes) if self.total_vendas_mes else 0.0
            ),
            "lucro_bruto_mes": (
                float(self.lucro_bruto_mes) if self.lucro_bruto_mes else 0.0
            ),
            "crescimento_vs_ontem": (
                float(self.crescimento_vs_ontem) if self.crescimento_vs_ontem else 0.0
            ),
            "data_calculo": (
                self.data_calculo.isoformat() if self.data_calculo else None
            ),
        }


# ============================================
# 21. RELATÓRIO AGENDADO
# ============================================


class RelatorioAgendado(db.Model):
    __tablename__ = "relatorios_agendados"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )

    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    formato = db.Column(db.String(10), nullable=False)
    frequencia = db.Column(db.String(20), nullable=False)

    horario_envio = db.Column(db.Time, nullable=False)

    destinatarios_email_json = db.Column(db.Text, default="[]")
    enviar_para_proprietario = db.Column(db.Boolean, default=True)

    parametros_json = db.Column(db.Text, default="{}")

    ativo = db.Column(db.Boolean, default=True)
    ultima_execucao = db.Column(db.DateTime)
    proxima_execucao = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("relatorios", lazy=True)
    )

    @property
    def destinatarios_email(self):
        try:
            return json.loads(self.destinatarios_email_json)
        except:
            return []

    @destinatarios_email.setter
    def destinatarios_email(self, value):
        self.destinatarios_email_json = json.dumps(value)

    @property
    def parametros(self):
        try:
            return json.loads(self.parametros_json)
        except:
            return {}

    @parametros.setter
    def parametros(self, value):
        self.parametros_json = json.dumps(value)

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
# ALIAS PARA COMPATIBILIDADE
# ============================================

ItemVenda = VendaItem


# ============================================
# SISTEMA DE CONTROLE DE PONTO
# ============================================

class RegistroPonto(db.Model):
    """Modelo para registro de ponto dos funcionários"""
    __tablename__ = "registros_ponto"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(
        db.Integer,
        db.ForeignKey("funcionarios.id", ondelete="CASCADE"),
        nullable=False
    )
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Dados do registro
    data = db.Column(db.Date, nullable=False, default=date.today)
    hora = db.Column(db.Time, nullable=False)
    tipo_registro = db.Column(
        db.String(20), 
        nullable=False
    )  # 'entrada', 'saida_almoco', 'retorno_almoco', 'saida'
    
    # Geolocalização
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    localizacao_endereco = db.Column(db.String(500))
    
    # Foto
    foto_url = db.Column(db.String(500))
    
    # Metadados
    dispositivo = db.Column(db.String(200))  # Informações do dispositivo/navegador
    ip_address = db.Column(db.String(50))
    observacao = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='normal')  # 'normal', 'atrasado', 'justificado'
    minutos_atraso = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    funcionario = db.relationship(
        "Funcionario",
        backref=db.backref("registros_ponto", lazy=True, cascade="all, delete-orphan")
    )
    estabelecimento = db.relationship(
        "Estabelecimento",
        backref=db.backref("registros_ponto", lazy=True)
    )
    
    __table_args__ = (
        db.Index("idx_ponto_funcionario_data", "funcionario_id", "data"),
        db.Index("idx_ponto_estabelecimento", "estabelecimento_id"),
        db.Index("idx_ponto_data", "data"),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'funcionario_id': self.funcionario_id,
            'funcionario_nome': self.funcionario.nome if self.funcionario else None,
            'estabelecimento_id': self.estabelecimento_id,
            'data': self.data.isoformat() if self.data else None,
            'hora': self.hora.strftime('%H:%M:%S') if self.hora else None,
            'tipo_registro': self.tipo_registro,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'localizacao_endereco': self.localizacao_endereco,
            'foto_url': self.foto_url,
            'dispositivo': self.dispositivo,
            'ip_address': self.ip_address,
            'observacao': self.observacao,
            'status': self.status,
            'minutos_atraso': self.minutos_atraso,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ConfiguracaoHorario(db.Model):
    """Configuração de horários de trabalho por estabelecimento"""
    __tablename__ = "configuracoes_horario"
    
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    
    # Horários padrão
    hora_entrada = db.Column(db.Time, nullable=False, default=datetime.strptime('08:00', '%H:%M').time())
    hora_saida_almoco = db.Column(db.Time, nullable=False, default=datetime.strptime('12:00', '%H:%M').time())
    hora_retorno_almoco = db.Column(db.Time, nullable=False, default=datetime.strptime('13:00', '%H:%M').time())
    hora_saida = db.Column(db.Time, nullable=False, default=datetime.strptime('18:00', '%H:%M').time())
    
    # Tolerâncias (em minutos)
    tolerancia_entrada = db.Column(db.Integer, default=10)
    tolerancia_saida_almoco = db.Column(db.Integer, default=5)
    tolerancia_retorno_almoco = db.Column(db.Integer, default=10)
    tolerancia_saida = db.Column(db.Integer, default=5)
    
    # Configurações
    exigir_foto = db.Column(db.Boolean, default=True)
    exigir_localizacao = db.Column(db.Boolean, default=True)
    raio_permitido_metros = db.Column(db.Integer, default=100)  # Raio em metros do estabelecimento
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    estabelecimento = db.relationship(
        "Estabelecimento",
        backref=db.backref("configuracao_horario", uselist=False, cascade="all, delete-orphan")
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'estabelecimento_id': self.estabelecimento_id,
            'hora_entrada': self.hora_entrada.strftime('%H:%M') if self.hora_entrada else None,
            'hora_saida_almoco': self.hora_saida_almoco.strftime('%H:%M') if self.hora_saida_almoco else None,
            'hora_retorno_almoco': self.hora_retorno_almoco.strftime('%H:%M') if self.hora_retorno_almoco else None,
            'hora_saida': self.hora_saida.strftime('%H:%M') if self.hora_saida else None,
            'tolerancia_entrada': self.tolerancia_entrada,
            'tolerancia_saida_almoco': self.tolerancia_saida_almoco,
            'tolerancia_retorno_almoco': self.tolerancia_retorno_almoco,
            'tolerancia_saida': self.tolerancia_saida,
            'exigir_foto': self.exigir_foto,
            'exigir_localizacao': self.exigir_localizacao,
            'raio_permitido_metros': self.raio_permitido_metros
        }


print("Models.py carregado com todas as classes necessarias!")


# ============================================
# FUNÇÕES DE SUPORTE PARA FLASK-LOGIN
# ============================================

from flask_login import LoginManager

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """
    Função necessária para o Flask-Login carregar o usuário da sessão.
    """
    # O user_id pode ser string ou inteiro, converta para inteiro
    try:
        return Funcionario.query.get(int(user_id))
    except (ValueError, TypeError):
        return None


@login_manager.request_loader
def load_user_from_request(request):
    """
    Carrega usuário a partir do token na requisição (para API).
    """
    # Primeiro tenta carregar do token da API
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            # Formato: Bearer <token> ou Token <token>
            auth_type, token = auth_header.split(None, 1)
            if auth_type.lower() == "bearer" or auth_type.lower() == "token":
                # Implementar lógica de validação de token JWT aqui
                # Por enquanto, vamos usar uma lógica simples
                from app.models import Funcionario

                user = Funcionario.query.filter_by(username=token).first()
                if user and user.ativo:
                    return user
        except (ValueError, AttributeError):
            pass

    # Se não encontrou no header, tenta na query string
    token = request.args.get("token")
    if token:
        from app.models import Funcionario

        user = Funcionario.query.filter_by(username=token).first()
        if user and user.ativo:
            return user

    return None
