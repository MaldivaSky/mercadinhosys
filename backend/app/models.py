# app/models.py

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json  # NOVO IMPORT

db = SQLAlchemy()  # Esta é a instância principal


class Estabelecimento(db.Model):
    """Tabela de estabelecimentos (cada mercado/loja)"""

    __tablename__ = "estabelecimentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cep = db.Column(db.String(10))
    endereco = db.Column(db.Text)
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    ativo = db.Column(db.Boolean, default=True)

    # Relacionamentos
    configuracao = db.relationship(
        "Configuracao", backref="estabelecimento", uselist=False
    )
    produtos = db.relationship("Produto", backref="estabelecimento")
    vendas = db.relationship("Venda", backref="estabelecimento")
    funcionarios = db.relationship("Funcionario", backref="estabelecimento")
    clientes = db.relationship("Cliente", backref="estabelecimento")
    fornecedores = db.relationship("Fornecedor", backref="estabelecimento")
    metricas = db.relationship("DashboardMetrica", backref="estabelecimento")  # NOVO

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cnpj": self.cnpj,
            "telefone": self.telefone,
            "email": self.email,
            "cep": self.cep,
            "endereco": self.endereco,
            "cidade": self.cidade,
            "estado": self.estado,
            "data_cadastro": (
                self.data_cadastro.isoformat() if self.data_cadastro else None
            ),
            "ativo": self.ativo,
        }


class Configuracao(db.Model):
    """Configurações do sistema por estabelecimento"""

    __tablename__ = "configuracoes"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), unique=True, nullable=False
    )

    # Configurações Gerais
    logo_url = db.Column(db.String(255))
    cor_principal = db.Column(db.String(7), default="#4F46E5")  # Indigo
    tema_escuro = db.Column(db.Boolean, default=False)

    # Configurações de Venda/PDV
    impressao_automatica = db.Column(db.Boolean, default=False)
    tipo_impressora = db.Column(db.String(20), default="termica")
    exibir_preco_tela = db.Column(db.Boolean, default=True)
    permitir_venda_sem_estoque = db.Column(db.Boolean, default=False)
    desconto_maximo_percentual = db.Column(db.Float, default=10.0)
    arredondamento_valores = db.Column(db.Float, default=0.05)

    # Configurações de Estoque
    dias_alerta_validade = db.Column(db.Integer, default=15)
    estoque_minimo_padrao = db.Column(db.Integer, default=10)

    # Configurações de Segurança
    tempo_sessao_minutos = db.Column(db.Integer, default=30)
    tentativas_senha_bloqueio = db.Column(db.Integer, default=3)

    # Formas de Pagamento
    formas_pagamento = db.Column(
        db.JSON,
        default=lambda: {
            "dinheiro": {"ativo": True, "taxa": 0, "exige_troco": True},
            "cartao_credito": {"ativo": True, "taxa": 2.5, "parcelas": 12},
            "cartao_debito": {"ativo": True, "taxa": 1.5},
            "pix": {"ativo": True, "taxa": 0},
        },
    )

    # NOVAS CONFIGURAÇÕES PARA DASHBOARD CIENTÍFICO
    meta_vendas_diaria = db.Column(db.Float, default=1000.0)
    meta_vendas_mensal = db.Column(db.Float, default=30000.0)
    alerta_estoque_minimo = db.Column(db.Boolean, default=True)
    alerta_validade_proxima = db.Column(db.Boolean, default=True)
    alerta_churn_clientes = db.Column(db.Boolean, default=True)
    dashboard_analytics_avancado = db.Column(db.Boolean, default=True)

    # Configurações de Notificação
    alertas_email = db.Column(db.Boolean, default=False)
    alertas_whatsapp = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "logo_url": self.logo_url,
            "cor_principal": self.cor_principal,
            "tema_escuro": self.tema_escuro,
            "impressao_automatica": self.impressao_automatica,
            "tipo_impressora": self.tipo_impressora,
            "exibir_preco_tela": self.exibir_preco_tela,
            "permitir_venda_sem_estoque": self.permitir_venda_sem_estoque,
            "desconto_maximo_percentual": self.desconto_maximo_percentual,
            "arredondamento_valores": self.arredondamento_valores,
            "dias_alerta_validade": self.dias_alerta_validade,
            "estoque_minimo_padrao": self.estoque_minimo_padrao,
            "tempo_sessao_minutos": self.tempo_sessao_minutos,
            "tentativas_senha_bloqueio": self.tentativas_senha_bloqueio,
            "formas_pagamento": self.formas_pagamento,
            "meta_vendas_diaria": self.meta_vendas_diaria,
            "meta_vendas_mensal": self.meta_vendas_mensal,
            "alerta_estoque_minimo": self.alerta_estoque_minimo,
            "alerta_validade_proxima": self.alerta_validade_proxima,
            "alerta_churn_clientes": self.alerta_churn_clientes,
            "dashboard_analytics_avancado": self.dashboard_analytics_avancado,
            "alertas_email": self.alertas_email,
            "alertas_whatsapp": self.alertas_whatsapp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Funcionario(db.Model, UserMixin):
    """Funcionários do estabelecimento"""

    __tablename__ = "funcionarios"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    # Dados Pessoais
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    senha_hash = db.Column(db.String(255))
    foto_url = db.Column(db.String(255))

    # Dados Profissionais
    cargo = db.Column(
        db.String(50), nullable=False
    )  # 'dono', 'gerente', 'caixa', 'repositor'
    role = db.Column(
        db.String(20), default="funcionario"
    )  # 'admin', 'gerente', 'funcionario'
    status = db.Column(
        db.String(20), default="ativo"
    )  # 'ativo', 'inativo', 'bloqueado'
    comissao_percentual = db.Column(db.Float, default=0.0)
    data_admissao = db.Column(db.Date, nullable=False)
    data_demissao = db.Column(db.Date)
    ativo = db.Column(db.Boolean, default=True)

    # Permissões
    permissoes = db.Column(
        db.JSON,
        default=lambda: {
            "acesso_pdv": True,
            "acesso_estoque": True,
            "acesso_relatorios": False,
            "acesso_configuracoes": False,
            "acesso_financeiro": False,
            "pode_dar_desconto": True,
            "limite_desconto": 5.0,
            "pode_cancelar_venda": False,
            "acesso_dashboard_avancado": False,  # NOVO
        },
    )

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    vendas = db.relationship("Venda", backref="funcionario")

    @property
    def is_active(self):
        """Sobrescreve o is_active padrão do UserMixin"""
        return self.ativo

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "nome": self.nome,
            "cpf": self.cpf,
            "telefone": self.telefone,
            "email": self.email,
            "foto_url": self.foto_url,
            "cargo": self.cargo,
            "username": self.username,
            "role": self.role,
            "status": self.status,
            "comissao_percentual": self.comissao_percentual,
            "data_admissao": (
                self.data_admissao.isoformat() if self.data_admissao else None
            ),
            "data_demissao": (
                self.data_demissao.isoformat() if self.data_demissao else None
            ),
            "ativo": self.ativo,
            "permissoes": self.permissoes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Cliente(db.Model):
    """Modelo de clientes"""

    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    cpf_cnpj = db.Column(db.String(20), unique=True, index=True)
    telefone = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    observacoes = db.Column(db.Text)

    # Campos de fidelidade e RFM
    total_compras = db.Column(db.Float, default=0.0)
    ultima_compra = db.Column(db.DateTime)
    frequencia_compras = db.Column(db.Integer, default=0)
    valor_medio_compra = db.Column(db.Float, default=0.0)
    dias_ultima_compra = db.Column(db.Integer, default=0)
    segmento_rfm = db.Column(db.String(20), default="novo")

    # Relacionamentos
    vendas = db.relationship("Venda", backref="cliente", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "nome": self.nome,
            "cpf_cnpj": self.cpf_cnpj,
            "telefone": self.telefone,
            "celular": self.celular,
            "email": self.email,
            "endereco": self.endereco,
            "data_cadastro": self.data_cadastro.isoformat() if self.data_cadastro else None,
            "data_atualizacao": self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            "ativo": self.ativo,
            "observacoes": self.observacoes,
            "total_compras": self.total_compras,
            "ultima_compra": self.ultima_compra.isoformat() if self.ultima_compra else None,
            "frequencia_compras": self.frequencia_compras,
            "valor_medio_compra": self.valor_medio_compra,
            "dias_ultima_compra": self.dias_ultima_compra,
            "segmento_rfm": self.segmento_rfm,
        }

    def __repr__(self):
        return f"<Cliente {self.cpf_cnpj or 'Sem CPF/CNPJ'}: {self.nome}>"

class Fornecedor(db.Model):
    """Fornecedores de produtos"""

    __tablename__ = "fornecedores"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    # Dados do Fornecedor
    nome = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.Text)
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(10))
    contato_comercial = db.Column(db.String(100))
    contato_nome = db.Column(db.String(100))
    celular_comercial = db.Column(db.String(20))

    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    data_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Informações de Compra
    prazo_entrega = db.Column(db.Integer)  # dias
    forma_pagamento = db.Column(db.String(50))

    # Métricas de performance
    avaliacao = db.Column(db.Float, default=5.0)  # NOVO: 1-5
    tempo_medio_entrega = db.Column(db.Integer)  # NOVO: dias
    taxa_atendimento = db.Column(db.Float, default=100.0)  # NOVO: percentual

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    produtos = db.relationship("Produto", backref="fornecedor")

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "nome": self.nome,
            "cnpj": self.cnpj,
            "telefone": self.telefone,
            "email": self.email,
            "endereco": self.endereco,
            "cidade": self.cidade,
            "estado": self.estado,
            "cep": self.cep,
            "contato_comercial": self.contato_comercial,
            "contato_nome": self.contato_nome,
            "celular_comercial": self.celular_comercial,
            "ativo": self.ativo,
            "data_cadastro": (
                self.data_cadastro.isoformat() if self.data_cadastro else None
            ),
            "data_atualizacao": (
                self.data_atualizacao.isoformat() if self.data_atualizacao else None
            ),
            "prazo_entrega": self.prazo_entrega,
            "forma_pagamento": self.forma_pagamento,
            "avaliacao": self.avaliacao,
            "tempo_medio_entrega": self.tempo_medio_entrega,
            "taxa_atendimento": self.taxa_atendimento,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Produto(db.Model):
    """Produtos do estoque"""

    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"))

    # Identificação
    codigo_barras = db.Column(db.String(50), unique=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    marca = db.Column(db.String(50))
    fabricante = db.Column(db.String(50))
    categoria = db.Column(db.String(50))
    subcategoria = db.Column(db.String(50))  # NOVO
    tipo = db.Column(db.String(30), default="unidade")  # Ex: Higiene, Mercearia, etc.
    unidade_medida = db.Column(db.String(20), default="UN")

    # Estoque
    quantidade = db.Column(db.Integer, default=0)
    quantidade_minima = db.Column(db.Integer, default=10)
    localizacao = db.Column(db.String(50))  # Prateleira, corredor
    dias_estoque = db.Column(db.Integer, default=0)  # NOVO: dias de estoque disponível
    giro_estoque = db.Column(db.Float, default=0.0)  # NOVO: vezes/ano

    # Preços
    preco_custo = db.Column(db.Float, nullable=False)
    preco_venda = db.Column(db.Float, nullable=False)
    margem_lucro = db.Column(db.Float)  # percentual

    # Métricas de Venda
    total_vendido = db.Column(db.Float, default=0.0)  # NOVO: valor total vendido
    quantidade_vendida = db.Column(db.Integer, default=0)  # NOVO: unidades vendidas
    frequencia_venda = db.Column(db.Integer, default=0)  # NOVO: vezes que foi vendido
    ultima_venda = db.Column(db.DateTime)  # NOVO

    # Classificação ABC
    classificação_abc = db.Column(db.String(1))  # NOVO: 'A', 'B', 'C'

    # Validade e Rastreabilidade
    data_fabricacao = db.Column(db.Date)  # NOVO: Data de fabricação
    data_validade = db.Column(db.Date)
    lote = db.Column(db.String(50))
    dias_para_vencer = db.Column(db.Integer)  # NOVO: Calculado automaticamente

    # Imagem
    imagem_url = db.Column(db.String(255))

    # Status
    ativo = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    itens_venda = db.relationship("VendaItem", backref="produto")
    movimentacoes = db.relationship("MovimentacaoEstoque", backref="produto")

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "fornecedor_id": self.fornecedor_id,
            "codigo_barras": self.codigo_barras,
            "nome": self.nome,
            "marca": self.marca,
            "fabricante": self.fabricante,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "subcategoria": self.subcategoria,
            "tipo": self.tipo,
            "unidade_medida": self.unidade_medida,
            "quantidade": self.quantidade,
            "quantidade_minima": self.quantidade_minima,
            "localizacao": self.localizacao,
            "dias_estoque": self.dias_estoque,
            "giro_estoque": self.giro_estoque,
            "preco_custo": self.preco_custo,
            "preco_venda": self.preco_venda,
            "margem_lucro": self.margem_lucro,
            "total_vendido": self.total_vendido,
            "quantidade_vendida": self.quantidade_vendida,
            "frequencia_venda": self.frequencia_venda,
            "ultima_venda": (
                self.ultima_venda.isoformat() if self.ultima_venda else None
            ),
            "classificação_abc": self.classificação_abc,
            "data_validade": (
                self.data_validade.isoformat() if self.data_validade else None
            ),
            "lote": self.lote,
            "imagem_url": self.imagem_url,
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Venda(db.Model):
    """Vendas realizadas"""

    __tablename__ = "vendas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"))
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionarios.id"), nullable=False
    )

    # Código único da venda
    codigo = db.Column(db.String(50), unique=True, nullable=False)

    # Valores
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    desconto = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)

    # Pagamento
    forma_pagamento = db.Column(db.String(50), nullable=False)
    valor_recebido = db.Column(db.Float, nullable=False)
    troco = db.Column(db.Float, default=0.0)

    # Status
    status = db.Column(
        db.String(20), default="finalizada"
    )  # 'finalizada', 'cancelada', 'pendente'

    # Métricas adicionais
    quantidade_itens = db.Column(db.Integer, default=0)  # NOVO
    tipo_venda = db.Column(
        db.String(20), default="normal"
    )  # NOVO: 'normal', 'atacado', 'promocional'

    # Observações
    observacoes = db.Column(db.Text)

    # Datas
    data_venda = db.Column(db.DateTime, default=datetime.now)
    data_cancelamento = db.Column(db.DateTime)
    motivo_cancelamento = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    itens = db.relationship("VendaItem", backref="venda", cascade="all, delete-orphan")
    movimentacoes = db.relationship("MovimentacaoEstoque", backref="venda")

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "cliente_id": self.cliente_id,
            "funcionario_id": self.funcionario_id,
            "codigo": self.codigo,
            "subtotal": self.subtotal,
            "desconto": self.desconto,
            "total": self.total,
            "forma_pagamento": self.forma_pagamento,
            "valor_recebido": self.valor_recebido,
            "troco": self.troco,
            "status": self.status,
            "quantidade_itens": self.quantidade_itens,
            "tipo_venda": self.tipo_venda,
            "observacoes": self.observacoes,
            "data_venda": self.data_venda.isoformat() if self.data_venda else None,
            "data_cancelamento": (
                self.data_cancelamento.isoformat() if self.data_cancelamento else None
            ),
            "motivo_cancelamento": self.motivo_cancelamento,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "itens": [item.to_dict() for item in self.itens],
        }


class VendaItem(db.Model):
    """Itens de uma venda"""

    __tablename__ = "venda_itens"

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)

    # Dados do produto no momento da venda
    produto_nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    produto_codigo = db.Column(db.String(50))
    produto_unidade = db.Column(db.String(20))

    # Quantidade e preços
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, default=0.0)
    total_item = db.Column(db.Float, nullable=False)

    # Métricas adicionais
    custo_unitario = db.Column(db.Float)  # NOVO
    margem_item = db.Column(db.Float)  # NOVO: percentual

    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "venda_id": self.venda_id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "descricao": self.descricao,
            "produto_codigo": self.produto_codigo,
            "produto_unidade": self.produto_unidade,
            "quantidade": self.quantidade,
            "preco_unitario": self.preco_unitario,
            "desconto": self.desconto,
            "total_item": self.total_item,
            "custo_unitario": self.custo_unitario,
            "margem_item": self.margem_item,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MovimentacaoEstoque(db.Model):
    """Movimentações de estoque (entrada/saída)"""

    __tablename__ = "movimentacoes_estoque"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"))
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"))

    # Tipo de movimentação
    tipo = db.Column(db.String(20), nullable=False)  # 'entrada', 'saida', 'ajuste'

    # Quantidades
    quantidade = db.Column(db.Integer, nullable=False)
    quantidade_anterior = db.Column(db.Integer, nullable=False)
    quantidade_atual = db.Column(db.Integer, nullable=False)

    # Valores
    custo_unitario = db.Column(db.Float)  # NOVO
    valor_total = db.Column(db.Float)  # NOVO

    # Motivo
    motivo = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "produto_id": self.produto_id,
            "venda_id": self.venda_id,
            "funcionario_id": self.funcionario_id,
            "tipo": self.tipo,
            "quantidade": self.quantidade,
            "quantidade_anterior": self.quantidade_anterior,
            "quantidade_atual": self.quantidade_atual,
            "custo_unitario": self.custo_unitario,
            "valor_total": self.valor_total,
            "motivo": self.motivo,
            "observacoes": self.observacoes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Despesa(db.Model):
    """Despesas do estabelecimento (fixas/variáveis)"""

    __tablename__ = "despesas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False, index=True
    )

    descricao = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(50), default="geral")
    tipo = db.Column(db.String(20), default="variavel")  # 'fixa' | 'variavel'
    valor = db.Column(db.Float, nullable=False)
    data_despesa = db.Column(db.Date, nullable=False, default=date.today)
    forma_pagamento = db.Column(db.String(50))
    recorrente = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "tipo": self.tipo,
            "valor": self.valor,
            "data_despesa": self.data_despesa.isoformat() if self.data_despesa else None,
            "forma_pagamento": self.forma_pagamento,
            "recorrente": self.recorrente,
            "observacoes": self.observacoes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LoginHistory(db.Model):
    """Histórico de tentativas de login (auditoria)."""

    __tablename__ = "login_history"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=True)
    username = db.Column(db.String(100), nullable=False)
    estabelecimento_id = db.Column(db.Integer, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6: até 45 chars
    dispositivo = db.Column(db.String(200))
    success = db.Column(db.Boolean, default=False)
    token_hash = db.Column(db.Integer)
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    funcionario = db.relationship("Funcionario", backref="login_history")

    def __repr__(self):
        return f"<LoginHistory {self.username} {self.created_at}>"


class DashboardMetrica(db.Model):
    """Métricas pré-calculadas para dashboard"""

    __tablename__ = "dashboard_metricas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )
    data_referencia = db.Column(db.Date, nullable=False)  # Dia de referência

    # Métricas do dia
    total_vendas_dia = db.Column(db.Float, default=0.0)
    quantidade_vendas_dia = db.Column(db.Integer, default=0)
    ticket_medio_dia = db.Column(db.Float, default=0.0)
    clientes_atendidos_dia = db.Column(db.Integer, default=0)
    meta_atingida_dia = db.Column(db.Boolean, default=False)
    meta_diaria = db.Column(db.Float, default=0.0)

    # Métricas do mês
    total_vendas_mes = db.Column(db.Float, default=0.0)
    total_despesas_mes = db.Column(db.Float, default=0.0)
    lucro_bruto_mes = db.Column(db.Float, default=0.0)
    margem_lucro_mes = db.Column(db.Float, default=0.0)

    # Crescimento e tendências
    crescimento_vs_ontem = db.Column(db.Float, default=0.0)
    crescimento_mensal = db.Column(db.Float, default=0.0)
    tendencia_vendas = db.Column(db.String(20))  # 'alta', 'estavel', 'baixa'

    # Análises temporais
    vendas_por_hora_json = db.Column(db.Text)  # JSON com vendas por hora
    padrao_semanal_json = db.Column(db.Text)  # JSON com padrão semanal
    sazonalidade_json = db.Column(db.Text)  # JSON com análise de sazonalidade

    # Análise de produtos
    top_produtos_json = db.Column(db.Text)  # JSON com top produtos
    produtos_abc_json = db.Column(db.Text)  # NOVO: Classificação ABC
    cross_selling_json = db.Column(db.Text)  # NOVO: Análise de cross-selling

    # Análise de clientes
    segmentacao_clientes_json = db.Column(db.Text)  # NOVO: Segmentação RFM
    top_clientes_json = db.Column(db.Text)  # NOVO: Top clientes
    taxa_churn = db.Column(db.Float, default=0.0)  # NOVO
    clv_medio = db.Column(db.Float, default=0.0)  # NOVO: Customer Lifetime Value

    # Alertas e insights
    alertas_json = db.Column(db.Text)  # JSON com alertas
    insights_json = db.Column(db.Text)  # JSON com insights automáticos
    anomalias_json = db.Column(db.Text)  # JSON com anomalias detectadas

    # Previsões
    previsoes_json = db.Column(db.Text)  # JSON com previsões
    confianca_previsao = db.Column(db.Float, default=0.0)

    # Métricas comparativas
    comparativo_ontem_json = db.Column(db.Text)
    comparativo_semana_json = db.Column(db.Text)
    comparativo_mes_json = db.Column(db.Text)

    # Performance
    tempo_resposta_medio = db.Column(db.Float, default=0.0)  # segundos
    precisao_previsoes = db.Column(db.Float, default=0.0)

    data_calculo = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Índices para performance
    __table_args__ = (
        db.Index("idx_metricas_estab_data", "estabelecimento_id", "data_referencia"),
        db.Index("idx_metricas_data", "data_referencia"),
        db.UniqueConstraint(
            "estabelecimento_id", "data_referencia", name="uix_estab_data"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "data_referencia": (
                self.data_referencia.isoformat() if self.data_referencia else None
            ),
            "total_vendas_dia": self.total_vendas_dia,
            "quantidade_vendas_dia": self.quantidade_vendas_dia,
            "ticket_medio_dia": self.ticket_medio_dia,
            "clientes_atendidos_dia": self.clientes_atendidos_dia,
            "meta_atingida_dia": self.meta_atingida_dia,
            "meta_diaria": self.meta_diaria,
            "total_vendas_mes": self.total_vendas_mes,
            "total_despesas_mes": self.total_despesas_mes,
            "lucro_bruto_mes": self.lucro_bruto_mes,
            "margem_lucro_mes": self.margem_lucro_mes,
            "crescimento_vs_ontem": self.crescimento_vs_ontem,
            "crescimento_mensal": self.crescimento_mensal,
            "tendencia_vendas": self.tendencia_vendas,
            "taxa_churn": self.taxa_churn,
            "clv_medio": self.clv_medio,
            "confianca_previsao": self.confianca_previsao,
            "tempo_resposta_medio": self.tempo_resposta_medio,
            "precisao_previsoes": self.precisao_previsoes,
            "data_calculo": (
                self.data_calculo.isoformat() if self.data_calculo else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # Campos JSON (serão parseados no dashboard)
            "vendas_por_hora_json": self.vendas_por_hora_json,
            "padrao_semanal_json": self.padrao_semanal_json,
            "sazonalidade_json": self.sazonalidade_json,
            "top_produtos_json": self.top_produtos_json,
            "produtos_abc_json": self.produtos_abc_json,
            "cross_selling_json": self.cross_selling_json,
            "segmentacao_clientes_json": self.segmentacao_clientes_json,
            "top_clientes_json": self.top_clientes_json,
            "alertas_json": self.alertas_json,
            "insights_json": self.insights_json,
            "anomalias_json": self.anomalias_json,
            "previsoes_json": self.previsoes_json,
            "comparativo_ontem_json": self.comparativo_ontem_json,
            "comparativo_semana_json": self.comparativo_semana_json,
            "comparativo_mes_json": self.comparativo_mes_json,
        }


class RelatorioAgendado(db.Model):
    """Relatórios agendados para geração automática"""

    __tablename__ = "relatorios_agendados"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    # Configuração do relatório
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(
        db.String(50), nullable=False
    )  # 'vendas', 'estoque', 'financeiro', 'clientes', 'analytics'
    formato = db.Column(db.String(10), nullable=False)  # 'pdf', 'excel', 'csv', 'json'
    frequencia = db.Column(
        db.String(20), nullable=False
    )  # 'diario', 'semanal', 'mensal', 'trimestral'

    # Análises específicas para relatórios científicos
    analises_incluidas = db.Column(
        db.JSON,
        default=lambda: {
            "tendencia": True,
            "sazonalidade": True,
            "previsao": True,
            "segmentacao": True,
            "anomalias": True,
            "benchmarking": True,
        },
    )

    horario_envio = db.Column(db.Time, nullable=False)

    # Destinatários
    destinatarios_email = db.Column(db.JSON)  # Lista de emails
    enviar_para_proprietario = db.Column(db.Boolean, default=True)

    # Parâmetros do relatório
    parametros = db.Column(db.JSON)  # Filtros específicos

    # Status
    ativo = db.Column(db.Boolean, default=True)
    ultima_execucao = db.Column(db.DateTime)
    proxima_execucao = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "nome": self.nome,
            "tipo": self.tipo,
            "formato": self.formato,
            "frequencia": self.frequencia,
            "analises_incluidas": self.analises_incluidas,
            "horario_envio": (
                self.horario_envio.strftime("%H:%M") if self.horario_envio else None
            ),
            "destinatarios_email": self.destinatarios_email,
            "enviar_para_proprietario": self.enviar_para_proprietario,
            "parametros": self.parametros,
            "ativo": self.ativo,
            "ultima_execucao": (
                self.ultima_execucao.isoformat() if self.ultima_execucao else None
            ),
            "proxima_execucao": (
                self.proxima_execucao.isoformat() if self.proxima_execucao else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# NOVA CLASSE: Análise Preditiva
class AnalisePreditiva(db.Model):
    """Modelos preditivos treinados"""

    __tablename__ = "analises_preditivas"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    # Tipo de análise
    tipo = db.Column(
        db.String(50), nullable=False
    )  # 'demanda', 'churn', 'clv', 'preco'
    modelo = db.Column(
        db.String(50), nullable=False
    )  # 'regressao', 'arima', 'prophet', 'mlp'

    # Parâmetros do modelo
    parametros = db.Column(db.JSON)
    metricas = db.Column(db.JSON)  # RMSE, MAE, R², etc.

    # Dados de treinamento
    dados_treinamento_inicio = db.Column(db.Date)
    dados_treinamento_fim = db.Column(db.Date)
    tamanho_treinamento = db.Column(db.Integer)

    # Status
    status = db.Column(
        db.String(20), default="treinado"
    )  # 'treinando', 'treinado', 'falha'
    ultimo_treinamento = db.Column(db.DateTime)
    proximo_treinamento = db.Column(db.DateTime)

    # Performance
    precisao = db.Column(db.Float, default=0.0)
    recall = db.Column(db.Float, default=0.0)
    f1_score = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "tipo": self.tipo,
            "modelo": self.modelo,
            "parametros": self.parametros,
            "metricas": self.metricas,
            "dados_treinamento_inicio": (
                self.dados_treinamento_inicio.isoformat()
                if self.dados_treinamento_inicio
                else None
            ),
            "dados_treinamento_fim": (
                self.dados_treinamento_fim.isoformat()
                if self.dados_treinamento_fim
                else None
            ),
            "tamanho_treinamento": self.tamanho_treinamento,
            "status": self.status,
            "ultimo_treinamento": (
                self.ultimo_treinamento.isoformat() if self.ultimo_treinamento else None
            ),
            "proximo_treinamento": (
                self.proximo_treinamento.isoformat()
                if self.proximo_treinamento
                else None
            ),
            "precisao": self.precisao,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
