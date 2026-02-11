# app/models.py - VERSÃO COMPLETA CORRIGIDA
# SISTEMA ERP COMERCIAL COMPLETO - PADRÃO INDUSTRIAL BRASILEIRO
# Versão completa com todas as tabelas necessárias

from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any
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

    # RH
    horas_extras_percentual = db.Column(db.Numeric(5, 2), default=50.00)

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
            "alertas_whatsapp": self.alertas_whatsapp,
            "horas_extras_percentual": float(self.horas_extras_percentual) if self.horas_extras_percentual else 50.0
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
    data_demissao = db.Column(db.Date)
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
# 3.1. BENEFÍCIOS E BANCO DE HORAS
# ============================================

class Beneficio(db.Model):
    __tablename__ = "beneficios"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False
    )
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200))
    valor_padrao = db.Column(db.Numeric(10, 2), default=0)
    ativo = db.Column(db.Boolean, default=True)

    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("beneficios", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "valor_padrao": float(self.valor_padrao) if self.valor_padrao else 0.0,
            "ativo": self.ativo
        }

class FuncionarioBeneficio(db.Model):
    __tablename__ = "funcionario_beneficios"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(
        db.Integer,
        db.ForeignKey("funcionarios.id", ondelete="CASCADE"),
        nullable=False
    )
    beneficio_id = db.Column(
        db.Integer,
        db.ForeignKey("beneficios.id", ondelete="CASCADE"),
        nullable=False
    )
    valor = db.Column(db.Numeric(10, 2), nullable=False) # Valor específico para o funcionário
    data_inicio = db.Column(db.Date, default=date.today)
    ativo = db.Column(db.Boolean, default=True)

    funcionario = db.relationship("Funcionario", backref=db.backref("beneficios_ativos", lazy=True))
    beneficio = db.relationship("Beneficio")

class BancoHoras(db.Model):
    __tablename__ = "banco_horas"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(
        db.Integer,
        db.ForeignKey("funcionarios.id", ondelete="CASCADE"),
        nullable=False
    )
    mes_referencia = db.Column(db.String(7), nullable=False) # Formato YYYY-MM
    saldo_minutos = db.Column(db.Integer, default=0) # Saldo acumulado do mês em minutos
    valor_hora_extra = db.Column(db.Numeric(10, 2), default=0) # Valor monetário acumulado
    
    # Detalhes
    horas_trabalhadas_minutos = db.Column(db.Integer, default=0)
    horas_esperadas_minutos = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    funcionario = db.relationship("Funcionario", backref=db.backref("banco_horas", lazy=True))

    __table_args__ = (
        db.UniqueConstraint("funcionario_id", "mes_referencia", name="uq_banco_func_mes"),
    )


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

    @staticmethod
    def segmentar_rfm(recency_score: int, frequency_score: int, monetary_score: int) -> str:
        r = int(recency_score)
        f = int(frequency_score)
        m = int(monetary_score)

        if r >= 4 and f >= 4 and m >= 4:
            return "Campeão"
        if r >= 4 and f >= 3:
            return "Fiel"
        if r <= 2 and (f >= 3 or m >= 3):
            return "Risco"
        if r == 1 and f <= 2:
            return "Perdido"
        return "Regular"

    @classmethod
    def calcular_rfm(
        cls, estabelecimento_id: int, days: int = 180
    ) -> Dict[str, Any]:
        from datetime import datetime, timedelta
        from sqlalchemy import func

        days = int(days) if days else 180
        if days <= 0:
            days = 180

        data_inicio = datetime.utcnow() - timedelta(days=days)

        rows = (
            db.session.query(
                Venda.cliente_id.label("cliente_id"),
                func.count(Venda.id).label("frequencia"),
                func.coalesce(func.sum(Venda.total), 0).label("monetario"),
                func.max(Venda.data_venda).label("ultima_compra"),
            )
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == "finalizada",
                Venda.cliente_id.isnot(None),
            )
            .group_by(Venda.cliente_id)
            .all()
        )

        now = datetime.utcnow()
        metrics = []
        for r in rows:
            ultima = r.ultima_compra
            recency_days = (now - ultima).days if ultima else days
            metrics.append(
                {
                    "cliente_id": int(r.cliente_id),
                    "recency_days": int(recency_days),
                    "frequency": int(r.frequencia or 0),
                    "monetary": float(r.monetario or 0),
                }
            )

        if not metrics:
            return {"segments": {}, "customers": [], "window_days": days}

        def _score_quintile(values_sorted, value, higher_is_better: bool) -> int:
            n = len(values_sorted)
            if n == 1:
                return 3
            import bisect

            idx = bisect.bisect_right(values_sorted, value) - 1
            if idx < 0:
                idx = 0
            p = (idx + 1) / n
            score = int(p * 5)
            if score < 1:
                score = 1
            if score > 5:
                score = 5
            return score if higher_is_better else (6 - score)

        recency_sorted = sorted(m["recency_days"] for m in metrics)
        frequency_sorted = sorted(m["frequency"] for m in metrics)
        monetary_sorted = sorted(m["monetary"] for m in metrics)

        segments_count = {"Campeão": 0, "Fiel": 0, "Risco": 0, "Perdido": 0, "Regular": 0}
        customers = []

        for m in metrics:
            recency_score = _score_quintile(recency_sorted, m["recency_days"], higher_is_better=False)
            frequency_score = _score_quintile(frequency_sorted, m["frequency"], higher_is_better=True)
            monetary_score = _score_quintile(monetary_sorted, m["monetary"], higher_is_better=True)

            segment = cls.segmentar_rfm(recency_score, frequency_score, monetary_score)
            segments_count[segment] = segments_count.get(segment, 0) + 1

            customers.append(
                {
                    **m,
                    "recency_score": recency_score,
                    "frequency_score": frequency_score,
                    "monetary_score": monetary_score,
                    "segment": segment,
                }
            )

        return {"segments": segments_count, "customers": customers, "window_days": days}


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

    @staticmethod
    def normalizar_nome_categoria(nome: str) -> str:
        """
        Normaliza o nome da categoria para evitar duplicatas por erros de digitação.
        
        Regras de normalização:
        - Remove espaços extras no início e fim
        - Converte para Title Case (primeira letra maiúscula)
        - Remove espaços duplicados internos
        - Remove caracteres especiais desnecessários
        
        Exemplos:
        - "  bebidas  " -> "Bebidas"
        - "ALIMENTOS" -> "Alimentos"
        - "limpeza   doméstica" -> "Limpeza Doméstica"
        
        Args:
            nome: Nome da categoria a ser normalizado
            
        Returns:
            str: Nome normalizado
        """
        if not nome:
            return ""
        
        # Remove espaços extras e converte para title case
        nome_normalizado = " ".join(nome.strip().split()).title()
        
        return nome_normalizado

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
    tipo = db.Column(db.String(50))  # Tipo do produto: Higiene, Limpeza, Alimentos, etc.

    unidade_medida = db.Column(db.String(20), default="UN")

    quantidade = db.Column(db.Integer, default=0)
    quantidade_minima = db.Column(db.Integer, default=10)

    preco_custo = db.Column(db.Numeric(10, 2), nullable=False)
    preco_venda = db.Column(db.Numeric(10, 2), nullable=False)
    margem_lucro = db.Column(db.Numeric(10, 2), nullable=True)

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

    def movimentar_estoque(self, quantidade: int, tipo: str, motivo: str, 
                          usuario_id: int, venda_id: int = None):
        """
        Realiza a movimentação de estoque de forma segura e auditável.
        Encapsula a regra de negócio e garante a criação do log.
        """
        # 1. Validação de Invariantes (Regra de Negócio)
        if tipo == 'saida':
            if quantidade <= 0:
                raise ValueError("Quantidade de saída deve ser positiva")
            
            # Validação básica de estoque
            if self.quantidade < quantidade:
                 # Aqui poderia ser lançada uma exceção se a configuração não permitir estoque negativo
                 pass

        quantidade_anterior = self.quantidade
        
        # 2. Atualização de Estado
        if tipo == 'entrada':
            self.quantidade += quantidade
        elif tipo == 'saida':
            self.quantidade -= quantidade
            self.quantidade_vendida += quantidade
            self.total_vendido += float(self.preco_venda * quantidade)
            self.ultima_venda = datetime.utcnow()
            
        # 3. Geração de Auditoria (Garante Integridade)
        # MovimentacaoEstoque é resolvida em tempo de execução
        movimentacao = MovimentacaoEstoque(
            estabelecimento_id=self.estabelecimento_id,
            produto_id=self.id,
            venda_id=venda_id,
            funcionario_id=usuario_id,
            tipo=tipo,
            quantidade=quantidade,
            quantidade_anterior=quantidade_anterior,
            quantidade_atual=self.quantidade,
            custo_unitario=self.preco_custo,
            valor_total=self.preco_venda * quantidade if tipo == 'saida' else self.preco_custo * quantidade,
            motivo=motivo
        )
        
        return movimentacao

    def recalcular_preco_custo_ponderado(
        self,
        quantidade_entrada: int,
        custo_unitario_entrada,
        estoque_atual: int = None,
        registrar_historico: bool = True,
        funcionario_id: int = None,
        motivo: str = "Entrada de estoque - CMP"
    ):
        """
        Calcula o Custo Médio Ponderado (CMP) do produto.
        
        Fórmula: CMP = (Estoque_Atual × Custo_Atual + Qtd_Entrada × Custo_Entrada) / (Estoque_Atual + Qtd_Entrada)
        
        Esta é a metodologia contábil correta para valoração de estoques, conforme NBC TG 16.
        Garante que o custo reflita a média ponderada de todas as aquisições.
        
        Args:
            quantidade_entrada: Quantidade sendo adicionada ao estoque
            custo_unitario_entrada: Custo unitário da nova entrada
            estoque_atual: Estoque atual (se None, usa self.quantidade)
            registrar_historico: Se deve criar registro de auditoria
            funcionario_id: ID do funcionário responsável pela alteração
            motivo: Motivo da alteração de custo
        
        Raises:
            ValueError: Se quantidade ou custo forem inválidos
        """
        from decimal import Decimal, ROUND_HALF_UP

        if quantidade_entrada is None or int(quantidade_entrada) <= 0:
            return

        if custo_unitario_entrada is None:
            return

        custo_entrada = Decimal(str(custo_unitario_entrada))
        if custo_entrada < 0:
            raise ValueError("Custo unitário não pode ser negativo")

        qtd_atual = int(self.quantidade or 0) if estoque_atual is None else int(estoque_atual)
        if qtd_atual < 0:
            qtd_atual = 0

        # Guardar valores anteriores para auditoria
        custo_anterior = Decimal(str(self.preco_custo or 0))
        margem_anterior = Decimal(str(self.margem_lucro or 0))
        
        custo_atual = custo_anterior
        qtd_entrada = int(quantidade_entrada)

        base = qtd_atual + qtd_entrada
        if base <= 0:
            self.preco_custo = custo_entrada
        else:
            novo_custo = ((Decimal(qtd_atual) * custo_atual) + (Decimal(qtd_entrada) * custo_entrada)) / Decimal(base)
            self.preco_custo = novo_custo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if self.preco_venda and self.preco_custo and self.preco_custo > 0:
            self.margem_lucro = (self.preco_venda - self.preco_custo) / self.preco_custo * 100
        else:
            self.margem_lucro = 0

        # Registrar histórico se houve mudança significativa e funcionario_id foi fornecido
        if registrar_historico and funcionario_id and abs(self.preco_custo - custo_anterior) > Decimal("0.01"):
            from app.models import HistoricoPrecos
            historico = HistoricoPrecos(
                estabelecimento_id=self.estabelecimento_id,
                produto_id=self.id,
                funcionario_id=funcionario_id,
                preco_custo_anterior=custo_anterior,
                preco_venda_anterior=self.preco_venda,
                margem_anterior=margem_anterior,
                preco_custo_novo=self.preco_custo,
                preco_venda_novo=self.preco_venda,
                margem_nova=self.margem_lucro,
                motivo=motivo,
                observacoes=f"CMP recalculado: entrada de {quantidade_entrada} unidades a R$ {custo_unitario_entrada}"
            )
            db.session.add(historico)

    @staticmethod
    def calcular_preco_por_markup(preco_custo, markup_percentual):
        """
        Calcula preço de venda baseado em markup sobre o custo.
        
        Fórmula: Preço_Venda = Custo × (1 + Markup/100)
        
        Exemplo: Custo R$ 10,00 com markup de 50% = R$ 15,00
        
        Args:
            preco_custo: Custo do produto
            markup_percentual: Percentual de markup desejado (ex: 50 para 50%)
            
        Returns:
            Decimal: Preço de venda calculado
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        if preco_custo is None or markup_percentual is None:
            return Decimal("0")
        
        custo = Decimal(str(preco_custo))
        markup = Decimal(str(markup_percentual))
        
        if custo < 0 or markup < 0:
            return Decimal("0")
        
        preco_venda = custo * (1 + markup / 100)
        return preco_venda.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calcular_markup_de_preco(preco_custo, preco_venda):
        """
        Calcula o markup percentual a partir dos preços.
        
        Fórmula: Markup = ((Preço_Venda - Custo) / Custo) × 100
        
        Args:
            preco_custo: Custo do produto
            preco_venda: Preço de venda do produto
            
        Returns:
            Decimal: Markup percentual
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        if preco_custo is None or preco_venda is None:
            return Decimal("0")
        
        custo = Decimal(str(preco_custo))
        venda = Decimal(str(preco_venda))
        
        if custo <= 0:
            return Decimal("0")
        
        markup = ((venda - custo) / custo * 100)
        return markup.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calcular_status_giro(self, dias_analise: int = 30) -> str:
        """
        Calcula o status de giro do produto baseado na última venda.
        
        Classificação de giro para otimização de estoque:
        - Rápido: Vendido nos últimos 7 dias (alta rotatividade)
        - Normal: Vendido entre 8 e 30 dias (rotatividade média)
        - Lento: Vendido há mais de 30 dias ou nunca vendido (baixa rotatividade)
        
        Args:
            dias_analise: Período de análise (padrão: 30 dias)
            
        Returns:
            str: "rapido", "normal" ou "lento"
        """
        if not self.ultima_venda:
            return "lento"

        dias_desde_ultima_venda = (datetime.utcnow() - self.ultima_venda).days

        if dias_desde_ultima_venda <= 7:
            return "rapido"
        elif dias_desde_ultima_venda <= dias_analise:
            return "normal"
        else:
            return "lento"

    @staticmethod
    def calcular_classificacao_abc_dinamica(estabelecimento_id: int, periodo_dias: int = 90):
        """
        Calcula classificação ABC dinâmica baseada no Princípio de Pareto (80/20).
        
        Metodologia:
        - Classe A: Produtos que representam 80% do faturamento (alta prioridade)
        - Classe B: Produtos que representam os próximos 15% do faturamento (média prioridade)
        - Classe C: Produtos que representam os últimos 5% do faturamento (baixa prioridade)
        
        Esta é a abordagem correta para gestão de estoque, substituindo valores fixos arbitrários.
        
        Args:
            estabelecimento_id: ID do estabelecimento
            periodo_dias: Período de análise em dias (padrão: 90 dias)
            
        Returns:
            dict: Mapeamento {produto_id: classificacao}
        """
        from datetime import datetime, timedelta
        from sqlalchemy import func
        from decimal import Decimal

        data_inicio = datetime.utcnow() - timedelta(days=periodo_dias)

        # Calcular faturamento por produto no período
        faturamento_query = (
            db.session.query(
                VendaItem.produto_id,
                func.sum(VendaItem.total_item).label('faturamento_total')
            )
            .join(Venda, Venda.id == VendaItem.venda_id)
            .filter(
                Venda.estabelecimento_id == estabelecimento_id,
                Venda.status == 'finalizada',
                Venda.data_venda >= data_inicio
            )
            .group_by(VendaItem.produto_id)
            .order_by(func.sum(VendaItem.total_item).desc())
            .all()
        )

        if not faturamento_query:
            return {}

        # Calcular faturamento total
        faturamento_total = sum(Decimal(str(item.faturamento_total or 0)) for item in faturamento_query)

        if faturamento_total == 0:
            return {}

        # Aplicar Princípio de Pareto
        classificacoes = {}
        acumulado = Decimal('0')
        
        for item in faturamento_query:
            produto_id = item.produto_id
            faturamento = Decimal(str(item.faturamento_total or 0))
            percentual_acumulado = (acumulado + faturamento) / faturamento_total * 100

            if percentual_acumulado <= 80:
                classificacoes[produto_id] = 'A'
            elif percentual_acumulado <= 95:
                classificacoes[produto_id] = 'B'
            else:
                classificacoes[produto_id] = 'C'

            acumulado += faturamento

        return classificacoes

    @staticmethod
    def atualizar_classificacoes_abc(estabelecimento_id: int, periodo_dias: int = 90):
        """
        Atualiza as classificações ABC de todos os produtos do estabelecimento.
        
        Deve ser executado periodicamente (ex: semanalmente) para manter
        a classificação atualizada conforme o comportamento de vendas muda.
        
        Args:
            estabelecimento_id: ID do estabelecimento
            periodo_dias: Período de análise em dias (padrão: 90 dias)
            
        Returns:
            dict: Estatísticas da atualização
        """
        classificacoes = Produto.calcular_classificacao_abc_dinamica(
            estabelecimento_id, periodo_dias
        )

        # Atualizar produtos com classificação
        produtos_atualizados = 0
        for produto_id, classificacao in classificacoes.items():
            produto = Produto.query.get(produto_id)
            if produto and produto.estabelecimento_id == estabelecimento_id:
                produto.classificacao_abc = classificacao
                produtos_atualizados += 1

        # Produtos sem vendas no período ficam como C
        produtos_sem_classificacao = Produto.query.filter(
            Produto.estabelecimento_id == estabelecimento_id,
            Produto.ativo == True,
            ~Produto.id.in_(classificacoes.keys())
        ).all()

        for produto in produtos_sem_classificacao:
            produto.classificacao_abc = 'C'
            produtos_atualizados += 1

        db.session.commit()

        return {
            'produtos_atualizados': produtos_atualizados,
            'classe_a': len([c for c in classificacoes.values() if c == 'A']),
            'classe_b': len([c for c in classificacoes.values() if c == 'B']),
            'classe_c': len([c for c in classificacoes.values() if c == 'C']),
            'sem_vendas': len(produtos_sem_classificacao)
        }

    def demanda_media_diaria(self, days: int = 30) -> float:
        from datetime import datetime, timedelta
        from sqlalchemy import func

        days = int(days) if days else 30
        if days <= 0:
            days = 30

        data_inicio = datetime.utcnow() - timedelta(days=days)

        total_quantidade = (
            db.session.query(func.coalesce(func.sum(VendaItem.quantidade), 0))
            .join(Venda, Venda.id == VendaItem.venda_id)
            .filter(
                Venda.estabelecimento_id == self.estabelecimento_id,
                Venda.data_venda >= data_inicio,
                Venda.status == "finalizada",
                VendaItem.produto_id == self.id,
            )
            .scalar()
            or 0
        )

        return float(total_quantidade) / float(days)

    def ponto_ressuprimento(
        self, lead_time_dias: int, days: int = 30, fator_seguranca: float = 1.5
    ) -> float:
        lead_time_dias = int(lead_time_dias) if lead_time_dias else 0
        if lead_time_dias <= 0:
            return 0.0
        demanda = self.demanda_media_diaria(days=days)
        return float(demanda) * float(lead_time_dias) * float(fator_seguranca)

    def to_dict(self):
        return {
            "id": self.id,
            "codigo_barras": self.codigo_barras,
            "codigo_interno": self.codigo_interno,
            "nome": self.nome,
            "descricao": self.descricao,
            "marca": self.marca,
            "fabricante": self.fabricante,
            "tipo": self.tipo,
            "unidade_medida": self.unidade_medida,
            "categoria": self.categoria.nome if self.categoria else None,
            "categoria_id": self.categoria_id,
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
            "total_vendido": float(self.total_vendido) if self.total_vendido else 0.0,
            "quantidade_vendida": int(self.quantidade_vendida) if self.quantidade_vendida else 0,
            "ultima_venda": self.ultima_venda.isoformat() if self.ultima_venda else None,
            "classificação_abc": self.classificacao_abc,
        }

    def get_lotes_disponiveis(self):
        """Retorna lotes disponíveis ordenados por FIFO (data de validade)"""
        from app.models import ProdutoLote
        return ProdutoLote.query.filter_by(
            produto_id=self.id,
            ativo=True
        ).filter(
            ProdutoLote.quantidade > 0
        ).order_by(
            ProdutoLote.data_validade.asc()
        ).all()

    def consumir_estoque_fifo(self, quantidade: int) -> List[Dict]:
        """
        Consome estoque usando FIFO (First In, First Out) por data de validade.
        Retorna lista de lotes consumidos com quantidades.
        
        Args:
            quantidade: Quantidade total a consumir
            
        Returns:
            List[Dict]: Lista com {lote_id, quantidade_consumida, lote}
        """
        lotes_consumidos = []
        quantidade_restante = quantidade
        
        lotes = self.get_lotes_disponiveis()
        
        for lote in lotes:
            if quantidade_restante <= 0:
                break
            
            quantidade_consumida = min(quantidade_restante, lote.quantidade)
            lote.quantidade -= quantidade_consumida
            quantidade_restante -= quantidade_consumida
            
            lotes_consumidos.append({
                'lote_id': lote.id,
                'quantidade_consumida': quantidade_consumida,
                'lote': lote
            })
        
        # Atualizar quantidade total do produto
        self.quantidade -= quantidade
        
        return lotes_consumidos


# ============================================
# 7.1. LOTE/BATCH DE PRODUTO (VALIDADE)
# ============================================


class ProdutoLote(db.Model):
    """
    Modelo para rastreamento de lotes/batches de produtos com datas de validade diferentes.
    
    Permite que o mesmo produto tenha múltiplos lotes com diferentes datas de validade,
    essencial para:
    - Controle de validade por lote
    - Seleção FIFO (First In, First Out) na venda
    - Rastreabilidade de origem (fornecedor, data de entrada)
    - Gestão de recalls por lote
    
    Exemplo:
    - Produto: Leite Integral 1L
    - Lote 1: 50 unidades, validade 2025-02-15, entrada 2025-01-15
    - Lote 2: 30 unidades, validade 2025-03-20, entrada 2025-02-01
    
    Ao vender, o sistema seleciona primeiro o Lote 1 (FIFO por validade).
    """
    __tablename__ = "produto_lotes"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )
    produto_id = db.Column(
        db.Integer,
        db.ForeignKey("produtos.id", ondelete="CASCADE"),
        nullable=False,
    )
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"))
    pedido_compra_id = db.Column(db.Integer, db.ForeignKey("pedidos_compra.id"))

    # Identificação do lote
    numero_lote = db.Column(db.String(50), nullable=False)  # Ex: "LOTE-2025-001"
    
    # Quantidade e validade
    quantidade = db.Column(db.Integer, nullable=False)  # Quantidade atual no lote
    quantidade_inicial = db.Column(db.Integer, nullable=False)  # Quantidade quando recebido
    
    data_validade = db.Column(db.Date, nullable=False)
    data_entrada = db.Column(db.Date, default=date.today, nullable=False)
    
    # Preço de custo (pode variar por lote)
    preco_custo_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Status
    ativo = db.Column(db.Boolean, default=True)  # False se lote foi descartado/devolvido
    motivo_inativacao = db.Column(db.String(100))  # Ex: "Validade expirada", "Devolução"
    
    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    estabelecimento = db.relationship(
        "Estabelecimento",
        backref=db.backref("produto_lotes", lazy=True, cascade="all, delete-orphan"),
    )
    produto = db.relationship(
        "Produto",
        backref=db.backref("lotes", lazy=True, cascade="all, delete-orphan"),
    )
    fornecedor = db.relationship(
        "Fornecedor",
        backref=db.backref("lotes_fornecidos", lazy=True),
    )
    pedido_compra = db.relationship(
        "PedidoCompra",
        backref=db.backref("lotes_recebidos", lazy=True),
    )

    __table_args__ = (
        db.Index("idx_lote_produto", "produto_id"),
        db.Index("idx_lote_validade", "data_validade"),
        db.Index("idx_lote_entrada", "data_entrada"),
        db.UniqueConstraint(
            "estabelecimento_id", "numero_lote", name="uq_lote_estab_numero"
        ),
    )

    @property
    def dias_para_vencer(self) -> int:
        """Retorna dias até a validade (negativo se vencido)"""
        return (self.data_validade - date.today()).days

    @property
    def esta_vencido(self) -> bool:
        """Retorna True se o lote está vencido"""
        return self.dias_para_vencer < 0

    @property
    def esta_proximo_vencer(self, dias_alerta: int = 30) -> bool:
        """Retorna True se o lote vence em breve"""
        return 0 <= self.dias_para_vencer <= dias_alerta

    def to_dict(self):
        return {
            "id": self.id,
            "numero_lote": self.numero_lote,
            "produto_id": self.produto_id,
            "produto_nome": self.produto.nome if self.produto else None,
            "quantidade": self.quantidade,
            "quantidade_inicial": self.quantidade_inicial,
            "data_validade": self.data_validade.isoformat() if self.data_validade else None,
            "data_entrada": self.data_entrada.isoformat() if self.data_entrada else None,
            "dias_para_vencer": self.dias_para_vencer,
            "esta_vencido": self.esta_vencido,
            "preco_custo_unitario": float(self.preco_custo_unitario) if self.preco_custo_unitario else 0.0,
            "fornecedor_nome": self.fornecedor.nome_fantasia if self.fornecedor else None,
            "ativo": self.ativo,
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
    margem_lucro_real = db.Column(db.Numeric(10, 2))  # Lucro real: (preco_venda - custo_atual) * quantidade

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
            "margem_lucro_real": float(self.margem_lucro_real) if self.margem_lucro_real else 0.0,
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
# 11. HISTÓRICO DE PREÇOS (AUDITORIA)
# ============================================


class HistoricoPrecos(db.Model):
    """
    Tabela de auditoria para rastreamento de alterações de preços.
    
    Permite análise temporal de:
    - Evolução de margem de lucro
    - Impacto de reajustes no faturamento
    - Elasticidade-preço da demanda
    - Compliance e auditoria fiscal
    """
    __tablename__ = "historico_precos"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )
    produto_id = db.Column(
        db.Integer, 
        db.ForeignKey("produtos.id", ondelete="CASCADE"), 
        nullable=False
    )
    funcionario_id = db.Column(
        db.Integer, 
        db.ForeignKey("funcionarios.id"), 
        nullable=False
    )

    # Valores anteriores
    preco_custo_anterior = db.Column(db.Numeric(10, 2), nullable=False)
    preco_venda_anterior = db.Column(db.Numeric(10, 2), nullable=False)
    margem_anterior = db.Column(db.Numeric(5, 2), nullable=False)

    # Valores novos
    preco_custo_novo = db.Column(db.Numeric(10, 2), nullable=False)
    preco_venda_novo = db.Column(db.Numeric(10, 2), nullable=False)
    margem_nova = db.Column(db.Numeric(5, 2), nullable=False)

    # Metadados
    motivo = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text)
    data_alteracao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    produto = db.relationship("Produto", backref=db.backref("historico_precos", lazy=True))
    funcionario = db.relationship("Funcionario", backref=db.backref("alteracoes_precos", lazy=True))

    __table_args__ = (
        db.Index("idx_historico_produto", "produto_id"),
        db.Index("idx_historico_data", "data_alteracao"),
        db.Index("idx_historico_estabelecimento", "estabelecimento_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto.nome if self.produto else None,
            "funcionario": self.funcionario.nome if self.funcionario else None,
            "preco_custo_anterior": float(self.preco_custo_anterior),
            "preco_venda_anterior": float(self.preco_venda_anterior),
            "margem_anterior": float(self.margem_anterior),
            "preco_custo_novo": float(self.preco_custo_novo),
            "preco_venda_novo": float(self.preco_venda_novo),
            "margem_nova": float(self.margem_nova),
            "variacao_custo_pct": float(
                ((self.preco_custo_novo - self.preco_custo_anterior) / self.preco_custo_anterior * 100)
                if self.preco_custo_anterior > 0 else 0
            ),
            "variacao_venda_pct": float(
                ((self.preco_venda_novo - self.preco_venda_anterior) / self.preco_venda_anterior * 100)
                if self.preco_venda_anterior > 0 else 0
            ),
            "motivo": self.motivo,
            "observacoes": self.observacoes,
            "data_alteracao": self.data_alteracao.isoformat() if self.data_alteracao else None,
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
            'funcionario_nome': self.funcionario.nome if self.funcionario else 'Desconhecido',
            'funcionario_cargo': self.funcionario.cargo if self.funcionario else 'N/A',
            'estabelecimento_id': self.estabelecimento_id,
            'data': self.data.isoformat() if self.data else None,
            'hora': self.hora.strftime('%H:%M:%S') if self.hora else None,
            'tipo': self.tipo_registro,  # Alias para compatibilidade com frontend
            'tipo_registro': self.tipo_registro,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'localizacao_endereco': self.localizacao_endereco,
            'foto_url': self.foto_url,
            'foto_path': self.foto_url,  # Alias para compatibilidade
            'dispositivo': self.dispositivo,
            'ip_address': self.ip_address,
            'observacao': self.observacao,
            'status': self.status,
            'minutos_atraso': self.minutos_atraso,
            'minutos_extras': 0,  # Placeholder - calcular se necessário
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


# ============================================
# 24. FILA DE SINCRONIZAÇÃO (OFFLINE-FIRST)
# ============================================


class SyncQueue(db.Model):
    """
    Fila de sincronização para garantir que operações realizadas offline
    sejam replicadas para a nuvem quando a conexão retornar.
    """
    __tablename__ = "sync_queue"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Identificação do recurso
    tabela = db.Column(db.String(50), nullable=False) # ex: 'vendas'
    registro_id = db.Column(db.Integer, nullable=False) # ID do registro local
    operacao = db.Column(db.String(10), nullable=False) # 'INSERT', 'UPDATE', 'DELETE'
    
    # Payload para reconstrução (opcional, mas útil se o registro for deletado)
    payload_json = db.Column(db.Text) 
    
    # Controle de Sincronização
    status = db.Column(db.String(20), default="pendente") # pendente, erro, sincronizado
    tentativas = db.Column(db.Integer, default=0)
    mensagem_erro = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_at = db.Column(db.DateTime)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("sync_queue", lazy=True)
    )

    __table_args__ = (
        db.Index("idx_sync_status", "status"),
        db.Index("idx_sync_created", "created_at"),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "tabela": self.tabela,
            "registro_id": self.registro_id,
            "operacao": self.operacao,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None
        }


class SyncLog(db.Model):
    __tablename__ = "sync_logs"

    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id", ondelete="CASCADE"),
        nullable=False,
    )
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"))

    operacao = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="running")
    since = db.Column(db.String(50))

    payload_json = db.Column(db.Text)
    resultado_json = db.Column(db.Text)
    mensagem_erro = db.Column(db.Text)

    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)

    estabelecimento = db.relationship(
        "Estabelecimento", backref=db.backref("sync_logs", lazy=True)
    )
    funcionario = db.relationship(
        "Funcionario", backref=db.backref("sync_logs", lazy=True)
    )


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
