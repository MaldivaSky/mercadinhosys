# app/models.py

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Estabelecimento(db.Model):
    """Tabela de estabelecimentos (cada mercado/loja)"""

    __tablename__ = "estabelecimentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
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

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cnpj": self.cnpj,
            "telefone": self.telefone,
            "email": self.email,
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
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    senha_hash = db.Column(db.String(255))
    foto_url = db.Column(db.String(255))

    # Dados Profissionais
    cargo = db.Column(
        db.String(50), nullable=False
    )  # 'dono', 'gerente', 'caixa', 'repositor'
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
    """Clientes do estabelecimento"""

    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer, db.ForeignKey("estabelecimentos.id"), nullable=False
    )

    # Dados Pessoais
    nome = db.Column(db.String(100), nullable=False)
    cpf_cnpj = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.Text)

    # Dados de Fidelidade
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    total_compras = db.Column(db.Float, default=0.0)
    ultima_compra = db.Column(db.DateTime)

    # Observações
    observacoes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    vendas = db.relationship("Venda", backref="cliente")

    def to_dict(self):
        return {
            "id": self.id,
            "estabelecimento_id": self.estabelecimento_id,
            "nome": self.nome,
            "cpf_cnpj": self.cpf_cnpj,
            "telefone": self.telefone,
            "email": self.email,
            "endereco": self.endereco,
            "data_cadastro": (
                self.data_cadastro.isoformat() if self.data_cadastro else None
            ),
            "total_compras": self.total_compras,
            "ultima_compra": (
                self.ultima_compra.isoformat() if self.ultima_compra else None
            ),
            "observacoes": self.observacoes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


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
    contato = db.Column(db.String(100))

    # Informações de Compra
    prazo_entrega = db.Column(db.Integer)  # dias
    forma_pagamento = db.Column(db.String(50))

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
            "contato": self.contato,
            "prazo_entrega": self.prazo_entrega,
            "forma_pagamento": self.forma_pagamento,
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
    categoria = db.Column(db.String(50))
    unidade_medida = db.Column(db.String(20), default="UN")

    # Estoque
    quantidade = db.Column(db.Integer, default=0)
    quantidade_minima = db.Column(db.Integer, default=10)
    localizacao = db.Column(db.String(50))  # Prateleira, corredor

    # Preços
    preco_custo = db.Column(db.Float, nullable=False)
    preco_venda = db.Column(db.Float, nullable=False)
    margem_lucro = db.Column(db.Float)  # percentual

    # Validade
    data_validade = db.Column(db.Date)
    lote = db.Column(db.String(50))

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
            "descricao": self.descricao,
            "categoria": self.categoria,
            "unidade_medida": self.unidade_medida,
            "quantidade": self.quantidade,
            "quantidade_minima": self.quantidade_minima,
            "localizacao": self.localizacao,
            "preco_custo": self.preco_custo,
            "preco_venda": self.preco_venda,
            "margem_lucro": self.margem_lucro,
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
    produto_codigo = db.Column(db.String(50))
    produto_unidade = db.Column(db.String(20))

    # Quantidade e preços
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, default=0.0)
    total_item = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "venda_id": self.venda_id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "produto_codigo": self.produto_codigo,
            "produto_unidade": self.produto_unidade,
            "quantidade": self.quantidade,
            "preco_unitario": self.preco_unitario,
            "desconto": self.desconto,
            "total_item": self.total_item,
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
            "motivo": self.motivo,
            "observacoes": self.observacoes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


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

    # Métricas do mês
    total_vendas_mes = db.Column(db.Float, default=0.0)
    total_despesas_mes = db.Column(db.Float, default=0.0)
    lucro_bruto_mes = db.Column(db.Float, default=0.0)

    # Produtos
    top_produtos_json = db.Column(db.JSON)  # {produto_id: quantidade_vendida}
    produtos_validade_json = db.Column(
        db.JSON
    )  # Lista de produtos próximos da validade

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Índice único para garantir uma entrada por dia por estabelecimento
    __table_args__ = (
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
            "total_vendas_mes": self.total_vendas_mes,
            "total_despesas_mes": self.total_despesas_mes,
            "lucro_bruto_mes": self.lucro_bruto_mes,
            "top_produtos_json": self.top_produtos_json,
            "produtos_validade_json": self.produtos_validade_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
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
    )  # 'vendas', 'estoque', 'financeiro', 'clientes'
    formato = db.Column(db.String(10), nullable=False)  # 'pdf', 'excel', 'csv'
    frequencia = db.Column(
        db.String(20), nullable=False
    )  # 'diario', 'semanal', 'mensal'
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
