from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Produto(db.Model):
    """Modelo de produtos do sistema"""

    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    codigo_barras = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    preco_custo = db.Column(db.Float, nullable=False, default=0.0)
    preco_venda = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    quantidade_minima = db.Column(db.Integer, nullable=False, default=10)
    categoria = db.Column(db.String(100), nullable=False, default="Outros")
    data_validade = db.Column(db.Date)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    venda_itens = db.relationship("VendaItem", backref="produto", lazy=True)

    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            "id": self.id,
            "codigo_barras": self.codigo_barras,
            "nome": self.nome,
            "descricao": self.descricao,
            "preco_custo": self.preco_custo,
            "preco_venda": self.preco_venda,
            "quantidade": self.quantidade,
            "quantidade_minima": self.quantidade_minima,
            "categoria": self.categoria,
            "data_validade": (
                self.data_validade.isoformat() if self.data_validade else None
            ),
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Produto {self.codigo_barras}: {self.nome}>"


class Cliente(db.Model):
    """Modelo de clientes"""

    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.Text)
    data_nascimento = db.Column(db.Date)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    vendas = db.relationship("Venda", backref="cliente", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "telefone": self.telefone,
            "email": self.email,
            "endereco": self.endereco,
            "data_nascimento": (
                self.data_nascimento.isoformat() if self.data_nascimento else None
            ),
            "ativo": self.ativo,
            "data_cadastro": self.data_cadastro.isoformat(),
        }


class Venda(db.Model):
    """Modelo de vendas"""

    __tablename__ = "vendas"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=True)
    funcionario_id = db.Column(db.Integer, nullable=False)  # ID do usuário logado
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    desconto = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    forma_pagamento = db.Column(db.String(20), nullable=False, default="dinheiro")
    status = db.Column(db.String(20), nullable=False, default="finalizada")
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    itens = db.relationship(
        "VendaItem", backref="venda", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "cliente_id": self.cliente_id,
            "funcionario_id": self.funcionario_id,
            "subtotal": self.subtotal,
            "desconto": self.desconto,
            "total": self.total,
            "forma_pagamento": self.forma_pagamento,
            "status": self.status,
            "observacoes": self.observacoes,
            "created_at": self.created_at.isoformat(),
            "itens": [item.to_dict() for item in self.itens],
        }


class VendaItem(db.Model):
    """Modelo dos itens de uma venda"""

    __tablename__ = "venda_itens"

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, nullable=False, default=0.0)
    total_item = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "venda_id": self.venda_id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto.nome if self.produto else None,
            "quantidade": self.quantidade,
            "preco_unitario": self.preco_unitario,
            "desconto": self.desconto,
            "total_item": self.total_item,
        }


class Usuario(db.Model):
    """Modelo de usuários/funcionários"""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    nivel_acesso = db.Column(db.String(20), nullable=False, default="vendedor")
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "usuario": self.usuario,
            "nivel_acesso": self.nivel_acesso,
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat(),
        }
