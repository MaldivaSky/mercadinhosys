from datetime import datetime, date
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Produto(db.Model):
    """Modelo de produtos do sistema - ATUALIZADO"""

    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)

    # Identificação
    codigo_barras = db.Column(db.String(50), unique=True, nullable=True, index=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)

    # Preços
    preco_custo = db.Column(db.Float, nullable=False, default=0.0)
    preco_venda = db.Column(db.Float, nullable=False, default=0.0)
    margem_lucro = db.Column(
        db.Float, nullable=False, default=30.0
    )  # Percentual de margem

    # Estoque
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    quantidade_minima = db.Column(db.Integer, nullable=False, default=10)

    # Categorização
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=True)
    marca = db.Column(db.String(100), nullable=False, default="Sem Marca")
    fabricante = db.Column(db.String(100))

    # Controle de validade
    data_validade = db.Column(db.Date)
    data_fabricacao = db.Column(db.Date)

    # Tipo de produto
    tipo = db.Column(
        db.String(20), nullable=False, default="unidade"
    )  # unidade, granel, fracionado
    unidade_medida = db.Column(
        db.String(20), nullable=False, default="un"
    )  # un, kg, g, L, ml

    # Status
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    venda_itens = db.relationship("VendaItem", backref="produto", lazy=True)
    categoria_rel = db.relationship("Categoria", backref="produtos_list", lazy=True)

    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            "id": self.id,
            "codigo_barras": self.codigo_barras,
            "nome": self.nome,
            "descricao": self.descricao,
            # Preços
            "preco_custo": self.preco_custo,
            "preco_venda": self.preco_venda,
            "margem_lucro": self.margem_lucro,
            # Estoque
            "quantidade": self.quantidade,
            "quantidade_minima": self.quantidade_minima,
            # Categorização
            "categoria_id": self.categoria_id,
            "categoria_nome": self.categoria_rel.nome if self.categoria_rel else None,
            "marca": self.marca,
            "fabricante": self.fabricante,
            # Datas
            "data_validade": (
                self.data_validade.isoformat() if self.data_validade else None
            ),
            "data_fabricacao": (
                self.data_fabricacao.isoformat() if self.data_fabricacao else None
            ),
            # Tipo
            "tipo": self.tipo,
            "unidade_medida": self.unidade_medida,
            # Status
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def calcular_preco_venda_por_margem(self, margem_percentual):
        """Calcula preço de venda baseado no custo e margem"""
        if self.preco_custo > 0:
            self.margem_lucro = margem_percentual
            self.preco_venda = self.preco_custo * (1 + (margem_percentual / 100))
            return self.preco_venda
        return 0.0

    def calcular_margem_por_preco_venda(self, preco_venda):
        """Calcula margem baseada no preço de venda informado"""
        if self.preco_custo > 0:
            self.preco_venda = preco_venda
            self.margem_lucro = (
                (preco_venda - self.preco_custo) / self.preco_custo
            ) * 100
            return self.margem_lucro
        return 0.0

    def __repr__(self):
        return f"<Produto {self.codigo_barras or 'Sem código'}: {self.nome}>"


class Funcionario(db.Model):
    """Modelo de funcionários/atendentes - NOVO"""

    __tablename__ = "funcionarios"

    id = db.Column(db.Integer, primary_key=True)

    # Dados pessoais
    nome = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)

    # Contato
    telefone = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.Text)

    # Dados profissionais
    cargo = db.Column(db.String(50), nullable=False, default="Atendente")
    salario = db.Column(db.Float, default=0.0)
    data_admissao = db.Column(db.Date, nullable=False, default=date.today)
    data_demissao = db.Column(db.Date)

    # Acesso ao sistema
    usuario = db.Column(db.String(50), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    nivel_acesso = db.Column(
        db.String(20), nullable=False, default="atendente"
    )  # atendente, gerente, admin
    pin_pdv = db.Column(db.String(255))  # Hash do PIN para PDV (4-6 dígitos)

    # Status
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    vendas = db.relationship("Venda", backref="funcionario", lazy=True)

    def set_senha(self, senha):
        """Define a senha do funcionário"""
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        """Verifica a senha do funcionário"""
        return check_password_hash(self.senha_hash, senha)

    def set_pin(self, pin):
        """Define o PIN para PDV"""
        self.pin_pdv = generate_password_hash(str(pin))

    def check_pin(self, pin):
        """Verifica o PIN para PDV"""
        if self.pin_pdv:
            return check_password_hash(self.pin_pdv, str(pin))
        return False

    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "rg": self.rg,
            "data_nascimento": (
                self.data_nascimento.isoformat() if self.data_nascimento else None
            ),
            "telefone": self.telefone,
            "celular": self.celular,
            "email": self.email,
            "endereco": self.endereco,
            "cargo": self.cargo,
            "salario": self.salario,
            "data_admissao": (
                self.data_admissao.isoformat() if self.data_admissao else None
            ),
            "data_demissao": (
                self.data_demissao.isoformat() if self.data_demissao else None
            ),
            "usuario": self.usuario,
            "nivel_acesso": self.nivel_acesso,
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Funcionario {self.usuario}: {self.nome}>"


class Cliente(db.Model):
    """Modelo de clientes - ATUALIZADO"""

    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)

    # Dados pessoais
    nome = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)

    # Contato
    telefone = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.Text)

    # Dados comerciais
    limite_credito = db.Column(db.Float, default=0.0)
    dia_vencimento = db.Column(db.Integer, default=10)  # Dia do vencimento da fatura
    observacoes = db.Column(db.Text)

    # Status
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    vendas = db.relationship("Venda", backref="cliente", lazy=True)

    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "rg": self.rg,
            "data_nascimento": (
                self.data_nascimento.isoformat() if self.data_nascimento else None
            ),
            "telefone": self.telefone,
            "celular": self.celular,
            "email": self.email,
            "endereco": self.endereco,
            "limite_credito": self.limite_credito,
            "dia_vencimento": self.dia_vencimento,
            "observacoes": self.observacoes,
            "ativo": self.ativo,
            "data_cadastro": self.data_cadastro.isoformat(),
            "data_atualizacao": self.data_atualizacao.isoformat(),
        }

    def __repr__(self):
        return f"<Cliente {self.cpf or 'Sem CPF'}: {self.nome}>"


class Venda(db.Model):
    """Modelo de vendas - ATUALIZADO"""

    __tablename__ = "vendas"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Relacionamentos
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=True)
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    # Valores
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    desconto = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)

    # Pagamento
    forma_pagamento = db.Column(db.String(20), nullable=False, default="dinheiro")
    valor_recebido = db.Column(db.Float, default=0.0)  # Para calcular troco
    troco = db.Column(db.Float, default=0.0)

    # Status
    status = db.Column(
        db.String(20), nullable=False, default="finalizada"
    )  # finalizada, cancelada, pendente
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    itens = db.relationship(
        "VendaItem", backref="venda", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            "id": self.id,
            "codigo": self.codigo,
            "cliente_id": self.cliente_id,
            "cliente_nome": self.cliente.nome if self.cliente else None,
            "funcionario_id": self.funcionario_id,
            "funcionario_nome": self.funcionario.nome if self.funcionario else None,
            "subtotal": self.subtotal,
            "desconto": self.desconto,
            "total": self.total,
            "forma_pagamento": self.forma_pagamento,
            "valor_recebido": self.valor_recebido,
            "troco": self.troco,
            "status": self.status,
            "observacoes": self.observacoes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "itens": [item.to_dict() for item in self.itens],
        }

    def calcular_totais(self):
        """Recalcula subtotal, desconto e total da venda"""
        self.subtotal = sum(item.total_item for item in self.itens)
        self.total = self.subtotal - self.desconto
        if self.valor_recebido > 0:
            self.troco = max(0, self.valor_recebido - self.total)

    def __repr__(self):
        return f"<Venda {self.codigo}: R$ {self.total:.2f}>"


class VendaItem(db.Model):
    """Modelo dos itens de uma venda - ATUALIZADO"""

    __tablename__ = "venda_itens"

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)

    # Quantidade e preço
    quantidade = db.Column(
        db.Float, nullable=False, default=1
    )  # Float para produtos a granel
    preco_unitario = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, nullable=False, default=0.0)
    total_item = db.Column(db.Float, nullable=False)

    # Informações do produto no momento da venda (para histórico)
    produto_nome = db.Column(db.String(200))
    produto_codigo = db.Column(db.String(50))
    produto_unidade = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            "id": self.id,
            "venda_id": self.venda_id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome
            or (self.produto.nome if self.produto else None),
            "produto_codigo": self.produto_codigo
            or (self.produto.codigo_barras if self.produto else None),
            "produto_unidade": self.produto_unidade
            or (self.produto.unidade_medida if self.produto else None),
            "quantidade": self.quantidade,
            "preco_unitario": self.preco_unitario,
            "desconto": self.desconto,
            "total_item": self.total_item,
            "created_at": self.created_at.isoformat(),
        }

    def calcular_total(self):
        """Calcula total do item"""
        self.total_item = (self.preco_unitario * self.quantidade) - self.desconto
        return self.total_item

    def __repr__(self):
        return f"<VendaItem {self.produto_nome}: {self.quantidade} x R$ {self.preco_unitario}>"


class Categoria(db.Model):
    """Modelo de categorias de produtos - NOVO"""

    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)

    # Dados da categoria
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    cor = db.Column(db.String(7), default="#3498db")  # Cor em hex para UI

    # Hierarquia
    categoria_pai_id = db.Column(
        db.Integer, db.ForeignKey("categorias.id"), nullable=True
    )

    # Status
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    produtos = db.relationship(
        "Produto",
        primaryjoin="Categoria.id == Produto.categoria_id",
        foreign_keys="Produto.categoria_id",
        lazy=True,
        overlaps="categoria_rel,produtos_list"
    )
    subcategorias = db.relationship(
        "Categoria", backref=db.backref("categoria_pai", remote_side=[id]), lazy=True
    )

    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "cor": self.cor,
            "categoria_pai_id": self.categoria_pai_id,
            "categoria_pai_nome": (
                self.categoria_pai.nome if self.categoria_pai else None
            ),
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "quantidade_produtos": len(self.produtos),
        }

    def __repr__(self):
        return f"<Categoria {self.nome}>"


class MovimentacaoEstoque(db.Model):
    """Modelo de movimentações de estoque - NOVO"""

    __tablename__ = "movimentacoes_estoque"

    id = db.Column(db.Integer, primary_key=True)

    # Identificação
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # entrada, saida, ajuste, perda
    quantidade = db.Column(db.Float, nullable=False)
    quantidade_anterior = db.Column(db.Float, nullable=False)
    quantidade_atual = db.Column(db.Float, nullable=False)

    # Motivo
    motivo = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text)

    # Relacionamentos
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=True)
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    # Data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    produto = db.relationship("Produto", backref="movimentacoes", lazy=True)
    venda = db.relationship("Venda", backref="movimentacoes_estoque", lazy=True)
    funcionario = db.relationship(
        "Funcionario", backref="movimentacoes_estoque", lazy=True
    )

    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto.nome if self.produto else None,
            "tipo": self.tipo,
            "quantidade": self.quantidade,
            "quantidade_anterior": self.quantidade_anterior,
            "quantidade_atual": self.quantidade_atual,
            "motivo": self.motivo,
            "observacoes": self.observacoes,
            "venda_id": self.venda_id,
            "funcionario_id": self.funcionario_id,
            "funcionario_nome": self.funcionario.nome if self.funcionario else None,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<MovimentacaoEstoque {self.tipo}: {self.quantidade} unidades>"


# Criar trigger/evento para gerar código da venda automaticamente
def gerar_codigo_venda(mapper, connection, target):
    """Gera código único para a venda"""
    if not target.codigo:
        # Formato: V-YYYYMMDD-XXXX
        data_atual = datetime.utcnow().strftime("%Y%m%d")

        # Contar vendas do dia
        from sqlalchemy import func

        contador = (
            db.session.query(func.count(Venda.id))
            .filter(db.cast(Venda.created_at, db.Date) == date.today())
            .scalar()
            or 0
        )

        target.codigo = f"V-{data_atual}-{contador + 1:04d}"


# Conectar o evento ao modelo Venda
from sqlalchemy import event

event.listen(Venda, "before_insert", gerar_codigo_venda)
# Note: The above models have been updated to reflect recent changes in the routes.