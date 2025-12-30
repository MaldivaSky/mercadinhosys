from datetime import datetime, date
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


# ==================== TABELAS BASE ====================


class Fornecedor(db.Model):
    """Modelo de fornecedores - ESSENCIAL para gestão de compras"""

    __tablename__ = "fornecedores"

    id = db.Column(db.Integer, primary_key=True)

    # Identificação
    nome = db.Column(db.String(200), nullable=False, index=True)
    razao_social = db.Column(db.String(200))
    cnpj = db.Column(db.String(18), unique=True, index=True)
    inscricao_estadual = db.Column(db.String(20))

    # Contato
    telefone = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    email = db.Column(db.String(100))
    site = db.Column(db.String(200))

    # Endereço
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(50))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(9))

    # Contato comercial
    contato_nome = db.Column(db.String(100))
    contato_telefone = db.Column(db.String(20))
    contato_email = db.Column(db.String(100))

    # Dados financeiros
    prazo_entrega = db.Column(db.Integer, default=7)  # dias
    condicao_pagamento = db.Column(db.String(100))
    limite_credito = db.Column(db.Float, default=0.0)

    # Status
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    produtos = db.relationship("Produto", backref="fornecedor_rel", lazy=True)
    compras = db.relationship("Compra", backref="fornecedor", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "razao_social": self.razao_social,
            "cnpj": self.cnpj,
            "telefone": self.telefone,
            "email": self.email,
            "cidade": self.cidade,
            "estado": self.estado,
            "contato_nome": self.contato_nome,
            "ativo": self.ativo,
            "quantidade_produtos": len(self.produtos),
        }

    def __repr__(self):
        return f"<Fornecedor {self.cnpj or 'Sem CNPJ'}: {self.nome}>"


class Produto(db.Model):
    """Modelo de produtos - ATUALIZADO com fornecedor"""

    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)

    # Identificação (ÍNDICES para busca rápida)
    codigo_barras = db.Column(db.String(50), unique=True, nullable=True, index=True)
    codigo_interno = db.Column(db.String(50), unique=True, nullable=True, index=True)
    nome = db.Column(db.String(200), nullable=False, index=True)
    descricao = db.Column(db.Text)

    # Fornecedor (NOVO CAMPO ESSENCIAL)
    fornecedor_id = db.Column(
        db.Integer, db.ForeignKey("fornecedores.id"), nullable=True
    )

    # Preços
    preco_custo = db.Column(db.Float, nullable=False, default=0.0)
    preco_venda = db.Column(db.Float, nullable=False, default=0.0)
    margem_lucro = db.Column(db.Float, nullable=False, default=30.0)

    # Estoque
    quantidade = db.Column(db.Float, nullable=False, default=0.0)  # Float para granel
    quantidade_minima = db.Column(db.Float, nullable=False, default=10.0)
    localizacao = db.Column(db.String(50))  # Corredor, prateleira, etc

    # Categorização SIMPLIFICADA
    categoria = db.Column(db.String(100), nullable=False, default="Geral")  # Bebidas, Alimentos, Limpeza, etc
    marca = db.Column(db.String(100), nullable=False, default="Sem Marca")
    fabricante = db.Column(db.String(100), nullable=False, default="Desconhecido")

    # Controle de validade
    data_validade = db.Column(db.Date)
    lote = db.Column(db.String(50))

    # Tipo de produto
    tipo = db.Column(db.String(20), nullable=False, default="unidade")
    unidade_medida = db.Column(db.String(20), nullable=False, default="un")
    peso_unidade = db.Column(db.Float)  # Para conversões

    # Impostos
    imposto_estadual = db.Column(db.Float, default=0.0)
    imposto_federal = db.Column(db.Float, default=0.0)

    # Status
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    controla_estoque = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos EXPLÍCITOS
    venda_itens = db.relationship("VendaItem", backref="produto_rel", lazy=True)
    movimentacoes = db.relationship(
        "MovimentacaoEstoque", backref="produto_mov", lazy=True
    )
    compra_itens = db.relationship("CompraItem", backref="produto_compra", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "codigo_barras": self.codigo_barras,
            "codigo_interno": self.codigo_interno,
            "nome": self.nome,
            "descricao": self.descricao,
            "fornecedor_id": self.fornecedor_id,
            "fornecedor_nome": (
                self.fornecedor_rel.nome if self.fornecedor_rel else None
            ),
            "preco_custo": self.preco_custo,
            "preco_venda": self.preco_venda,
            "margem_lucro": self.margem_lucro,
            "quantidade": self.quantidade,
            "quantidade_minima": self.quantidade_minima,
            "localizacao": self.localizacao,
            "categoria": self.categoria,
            "marca": self.marca,
            "fabricante": self.fabricante,
            "data_validade": (
                self.data_validade.isoformat() if self.data_validade else None
            ),
            "imposto_estadual": self.imposto_estadual,
            "imposto_federal": self.imposto_federal,
            "lote": self.lote,
            "tipo": self.tipo,
            "unidade_medida": self.unidade_medida,
            "ativo": self.ativo,
            "controla_estoque": self.controla_estoque,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Produto {self.codigo_barras or 'Sem código'}: {self.nome}>"


class Funcionario(db.Model):
    """Modelo de funcionários """

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
    """Modelo de clientes - MANTIDO (já está bom)"""

    # ... (mantenha como está) ...


# ==================== VENDAS E FINANCEIRO ====================


class Venda(db.Model):
    """Modelo de vendas - MELHORADO com mais detalhes"""

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
    acrescimo = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)

    # Pagamento
    forma_pagamento = db.Column(db.String(20), nullable=False, default="dinheiro")
    parcelas = db.Column(db.Integer, default=1)
    valor_recebido = db.Column(db.Float, default=0.0)
    troco = db.Column(db.Float, default=0.0)

    # Status
    status = db.Column(db.String(20), nullable=False, default="finalizada")
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    itens = db.relationship(
        "VendaItem", backref="venda_rel", lazy=True, cascade="all, delete-orphan"
    )
    pagamentos = db.relationship("Pagamento", backref="venda_pag", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "cliente_id": self.cliente_id,
            "cliente_nome": self.cliente.nome if self.cliente else None,
            "funcionario_id": self.funcionario_id,
            "funcionario_nome": self.funcionario.nome if self.funcionario else None,
            "subtotal": self.subtotal,
            "desconto": self.desconto,
            "acrescimo": self.acrescimo,
            "total": self.total,
            "forma_pagamento": self.forma_pagamento,
            "parcelas": self.parcelas,
            "valor_recebido": self.valor_recebido,
            "troco": self.troco,
            "status": self.status,
            "observacoes": self.observacoes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "itens": [item.to_dict() for item in self.itens],
            "pagamentos": [p.to_dict() for p in self.pagamentos],
        }

    def __repr__(self):
        return f"<Venda {self.codigo}: R$ {self.total:.2f}>"


class VendaItem(db.Model):
    """Modelo dos itens de uma venda - MANTIDO"""

    # ... (mantenha como está) ...


class Pagamento(db.Model):
    """Modelo de pagamentos - NOVO para controle financeiro"""

    __tablename__ = "pagamentos"

    id = db.Column(db.Integer, primary_key=True)

    # Identificação
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=True)
    descricao = db.Column(db.String(200))

    # Valores
    valor = db.Column(db.Float, nullable=False)
    valor_pago = db.Column(db.Float, default=0.0)
    desconto = db.Column(db.Float, default=0.0)
    acrescimo = db.Column(db.Float, default=0.0)

    # Datas
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)

    # Forma de pagamento
    forma_pagamento = db.Column(db.String(20), nullable=False, default="dinheiro")
    banco = db.Column(db.String(50))
    agencia = db.Column(db.String(10))
    conta = db.Column(db.String(20))
    cheque_numero = db.Column(db.String(50))

    # Status
    status = db.Column(db.String(20), nullable=False, default="pendente")
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "venda_id": self.venda_id,
            "descricao": self.descricao,
            "valor": self.valor,
            "valor_pago": self.valor_pago,
            "desconto": self.desconto,
            "acrescimo": self.acrescimo,
            "data_vencimento": self.data_vencimento.isoformat(),
            "data_pagamento": (
                self.data_pagamento.isoformat() if self.data_pagamento else None
            ),
            "forma_pagamento": self.forma_pagamento,
            "status": self.status,
            "observacoes": self.observacoes,
        }

    def __repr__(self):
        return f"<Pagamento {self.descricao}: R$ {self.valor:.2f}>"


# ==================== COMPRAS ====================


class Compra(db.Model):
    """Modelo de compras - NOVO para gestão de entradas"""

    __tablename__ = "compras"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Fornecedor
    fornecedor_id = db.Column(
        db.Integer, db.ForeignKey("fornecedores.id"), nullable=False
    )

    # Valores
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    frete = db.Column(db.Float, default=0.0)
    outras_despesas = db.Column(db.Float, default=0.0)
    desconto = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)

    # Status
    status = db.Column(db.String(20), nullable=False, default="pendente")
    data_compra = db.Column(db.Date, default=date.today)
    data_entrega = db.Column(db.Date)
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    itens = db.relationship(
        "CompraItem", backref="compra_rel", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "fornecedor_id": self.fornecedor_id,
            "fornecedor_nome": self.fornecedor.nome if self.fornecedor else None,
            "subtotal": self.subtotal,
            "frete": self.frete,
            "outras_despesas": self.outras_despesas,
            "desconto": self.desconto,
            "total": self.total,
            "status": self.status,
            "data_compra": self.data_compra.isoformat(),
            "data_entrega": (
                self.data_entrega.isoformat() if self.data_entrega else None
            ),
            "observacoes": self.observacoes,
            "itens": [item.to_dict() for item in self.itens],
        }

    def __repr__(self):
        return f"<Compra {self.codigo}: R$ {self.total:.2f}>"


class CompraItem(db.Model):
    """Modelo de itens de compra"""

    __tablename__ = "compra_itens"

    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey("compras.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)

    # Quantidade e preço
    quantidade = db.Column(db.Float, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, default=0.0)
    total_item = db.Column(db.Float, nullable=False)

    # Informações do produto
    produto_nome = db.Column(db.String(200))
    produto_codigo = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "compra_id": self.compra_id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "produto_codigo": self.produto_codigo,
            "quantidade": self.quantidade,
            "preco_unitario": self.preco_unitario,
            "desconto": self.desconto,
            "total_item": self.total_item,
        }

    def __repr__(self):
        return f"<CompraItem {self.produto_nome}: {self.quantidade} x R$ {self.preco_unitario}>"


# ==================== CONTROLES ====================


class MovimentacaoEstoque(db.Model):
    """Modelo de movimentações de estoque - MANTIDO"""

    # ... (mantenha como está) ...


class Auditoria(db.Model):
    """Modelo de auditoria - NOVO para logs do sistema"""

    __tablename__ = "auditoria"

    id = db.Column(db.Integer, primary_key=True)

    # Identificação
    usuario_id = db.Column(db.Integer, nullable=True)
    usuario_nome = db.Column(db.String(100))

    # Ação
    acao = db.Column(
        db.String(50), nullable=False
    )  # CREATE, UPDATE, DELETE, LOGIN, etc
    modulo = db.Column(db.String(50), nullable=False)  # produto, cliente, venda, etc
    registro_id = db.Column(db.Integer, nullable=True)

    # Detalhes
    dados_anteriores = db.Column(db.Text)
    dados_novos = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

    # Data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "usuario_nome": self.usuario_nome,
            "acao": self.acao,
            "modulo": self.modulo,
            "registro_id": self.registro_id,
            "dados_anteriores": self.dados_anteriores,
            "dados_novos": self.dados_novos,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Auditoria {self.modulo}.{self.acao} por {self.usuario_nome}>"


class Configuracao(db.Model):
    """Modelo de configurações do sistema - NOVO"""

    __tablename__ = "configuracoes"

    id = db.Column(db.Integer, primary_key=True)

    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text)
    tipo = db.Column(db.String(20), default="texto")  # texto, numero, booleano, json
    descricao = db.Column(db.Text)
    categoria = db.Column(db.String(50), default="geral")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def get_valor(self):
        """Retorna valor convertido conforme tipo"""
        if self.tipo == "numero":
            return float(self.valor) if self.valor else 0
        elif self.tipo == "booleano":
            return self.valor.lower() == "true"
        elif self.tipo == "json":
            import json

            return json.loads(self.valor) if self.valor else {}
        return self.valor

    def __repr__(self):
        return f"<Configuracao {self.chave}>"


# ==================== EVENTOS/TABELAS AUXILIARES ====================


def gerar_codigo_venda(mapper, connection, target):
    """Gera código único para a venda"""
    if not target.codigo:
        data_atual = datetime.utcnow().strftime("%Y%m%d")
        contador = (
            db.session.query(func.count(Venda.id))
            .filter(db.cast(Venda.created_at, db.Date) == date.today())
            .scalar()
            or 0
        )
        target.codigo = f"V-{data_atual}-{contador + 1:04d}"


def gerar_codigo_compra(mapper, connection, target):
    """Gera código único para compra"""
    if not target.codigo:
        data_atual = datetime.utcnow().strftime("%Y%m%d")
        contador = (
            db.session.query(func.count(Compra.id))
            .filter(db.cast(Compra.created_at, db.Date) == date.today())
            .scalar()
            or 0
        )
        target.codigo = f"C-{data_atual}-{contador + 1:04d}"


# Registrar eventos
from sqlalchemy import event, func

event.listen(Venda, "before_insert", gerar_codigo_venda)
event.listen(Compra, "before_insert", gerar_codigo_compra)
