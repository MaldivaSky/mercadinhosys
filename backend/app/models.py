# app/models.py – REFATORAÇÃO PROFISSIONAL COMPLETA (1/4)
# CTO: Rafael Mello - Arquitetura Limpa, Multi‑tenant, Offline‑first, Pagamentos Flexíveis

import json
import os
import re
import uuid as uuid_module
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from flask import g, has_app_context, current_app
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, case, event, func, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declared_attr, validates
from werkzeug.security import check_password_hash, generate_password_hash

# ------------------------------------------------------------------------------
# Configuração
# ------------------------------------------------------------------------------
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def normalizar_documento(doc: str) -> str:
    if not doc: return ""
    return re.sub(r"[^\d]", "", str(doc))

def validar_cpf(cpf: str) -> bool:
    if os.environ.get("FLASK_ENV") == "simulation": return True
    cpf = normalizar_documento(cpf)
    if len(cpf) != 11 or len(set(cpf)) == 1: return False
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        if ((value * 10) % 11) % 10 != int(cpf[i]): return False
    return True

def validar_cnpj(cnpj: str) -> bool:
    if os.environ.get("FLASK_ENV") == "simulation": return True
    cnpj = normalizar_documento(cnpj)
    if len(cnpj) != 14 or len(set(cnpj)) == 1: return False
    def calc_digit(num_str, weights):
        total = sum(int(d) * w for d, w in zip(num_str, weights))
        rest = total % 11
        return 0 if rest < 2 else 11 - rest
    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    pesos2 = [6,5,4,3,2,9,8,7,6,5,4,3,2]
    d1 = calc_digit(cnpj[:12], pesos1)
    d2 = calc_digit(cnpj[:12] + str(d1), pesos2)
    return d1 == int(cnpj[12]) and d2 == int(cnpj[13])

def is_offline_mode() -> bool:
    return os.environ.get("MERCADINHO_OFFLINE", "false").lower() == "true"

# ------------------------------------------------------------------------------
# Query customizada (Multi‑tenant + Soft‑delete automáticos)
# ------------------------------------------------------------------------------
class TenantQuery(db.Query):
    def __apply_filters(self):
        if not hasattr(self, "_primary_entity"): return self
        model = self._primary_entity.mapper.class_
        if hasattr(model, "estabelecimento_id") and has_app_context() and g and hasattr(g, "estabelecimento_id"):
            self = self.filter(model.estabelecimento_id == g.estabelecimento_id)
        if hasattr(model, "deleted_at"):
            self = self.filter(model.deleted_at == None)
        return self

    def get(self, ident): return super(TenantQuery, self.__apply_filters()).get(ident)
    def all(self): return super(TenantQuery, self.__apply_filters()).all()
    def paginate(self, page=1, per_page=20, error_out=True, max_per_page=None):
        return super(TenantQuery, self.__apply_filters()).paginate(page, per_page, error_out, max_per_page)

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# Mixins (Clean Code)
# ------------------------------------------------------------------------------
class SoftDeleteMixin:
    deleted_at = db.Column(db.DateTime, nullable=True)
    def soft_delete(self): self.deleted_at = utcnow()
    def restore(self): self.deleted_at = None
    @property
    def is_deleted(self): return self.deleted_at is not None

class AuditMixin:
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    sync_uuid = db.Column(db.String(36), default=lambda: str(uuid_module.uuid4()), unique=True, nullable=False)

class SerializableMixin:
    def to_dict(self, include_relationships: bool = False, depth: int = 0) -> Dict:
        result = {}
        for col in self.__table__.columns:
            value = getattr(self, col.name)
            if isinstance(value, (datetime, date, time)): value = value.isoformat() if value else None
            elif isinstance(value, Decimal): value = float(value)
            elif isinstance(value, uuid_module.UUID): value = str(value)
            result[col.name] = value
        if include_relationships and depth < 1:
            for rel in self.__mapper__.relationships:
                if not rel.uselist:
                    related = getattr(self, rel.key)
                    if related and hasattr(related, "to_dict"):
                        result[rel.key] = related.to_dict(depth=depth+1)
        return result

class EnderecoMixin:
    cep = db.Column(db.String(9), nullable=False)
    logradouro = db.Column(db.String(200), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    pais = db.Column(db.String(50), default="Brasil")
    def endereco_completo(self) -> str:
        try:
            log = getattr(self, "logradouro", "") or "Não Informado"
            num = getattr(self, "numero", "") or "S/N"
            comp = getattr(self, "complemento", "")
            bairro = getattr(self, "bairro", "") or ""
            cidade = getattr(self, "cidade", "") or ""
            estado = getattr(self, "estado", "") or ""
            cep = getattr(self, "cep", "") or ""
            end = f"{log}, {num}"
            if comp: end += f" - {comp}"
            end += f" - {bairro} - {cidade}/{estado} - {cep}"
            return end
        except: return "Endereço não disponível"

def TenantID():
    """Rafael, esta é a forma mais segura de injetar o ID sem falhas de mapeamento."""
    from sqlalchemy import Column, Integer, ForeignKey
    return Column(Integer, ForeignKey("estabelecimentos.id", ondelete="CASCADE"), nullable=False, index=True)

class MultiTenantMixin:
    """Mixin que garante o filtro automático e o relacionamento."""
    query_class = TenantQuery

    @declared_attr
    def estabelecimento(cls):
        from sqlalchemy.orm import relationship
        return relationship("Estabelecimento", foreign_keys=[cls.estabelecimento_id])

class Estabelecimento(db.Model, EnderecoMixin, SerializableMixin, AuditMixin):
    """Raiz do tenant. Não herda MultiTenantMixin."""
    __tablename__ = "estabelecimentos"
    id = db.Column(db.Integer, primary_key=True)
    nome_fantasia = db.Column(db.String(150), nullable=False)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), nullable=False)
    inscricao_estadual = db.Column(db.String(20))
    telefone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    regime_tributario = db.Column(db.String(30), default="SIMPLES NACIONAL")
    logotipo_url = db.Column(db.String(255))
    tema_principal = db.Column(db.String(50), default="blue")
    configuracoes_json = db.Column(db.Text, default="{}")
    ativo = db.Column(db.Boolean, default=True)
    data_abertura = db.Column(db.Date, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=utcnow)
    
    # Campos de Assinatura e Integração
    premium = db.Column(db.Boolean, default=False)
    plano = db.Column(db.String(50), default="bronze")
    plano_status = db.Column(db.String(20), default="experimental")
    vencimento_plano = db.Column(db.Date)
    vencimento_assinatura = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    pagarme_id = db.Column(db.String(100))
    deleted_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.Index("ix_estabelecimento_cnpj", "cnpj"),
        db.UniqueConstraint("cnpj", name="uq_estabelecimento_cnpj"),
    )

    @validates("cnpj")
    def validate_cnpj(self, key, value):
        if not validar_cnpj(value): raise ValueError(f"CNPJ inválido: {value}")
        return normalizar_documento(value)

    @property
    def configuracoes(self):
        try: return json.loads(self.configuracoes_json or "{}")
        except: return {}

    @configuracoes.setter
    def configuracoes(self, value):
        self.configuracoes_json = json.dumps(value)

    def to_dict(self, depth=0):
        data = super().to_dict(depth=depth)
        data["endereco_completo"] = self.endereco_completo()
        if self.vencimento_assinatura:
            data["vencimento_assinatura"] = self.vencimento_assinatura.isoformat()
        return data

# ------------------------------------------------------------------------------
# Sincronização Unificada (Offline‑first)
# ------------------------------------------------------------------------------
class SyncQueue(db.Model, MultiTenantMixin):
    __tablename__ = "sync_queue"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    tabela = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)
    operacao = db.Column(db.String(10), nullable=False)  # insert, update, delete
    payload_json = db.Column(db.Text)
    status = db.Column(db.String(20), default="pendente")
    tentativas = db.Column(db.Integer, default=0)
    mensagem_erro = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    synced_at = db.Column(db.DateTime)
    __table_args__ = (db.Index("ix_sync_queue_status", "status"), db.Index("ix_sync_queue_created", "created_at"))

    def to_dict(self):
        return {"id": self.id, "tabela": self.tabela, "registro_id": self.registro_id, "operacao": self.operacao,
                "status": self.status, "created_at": self.created_at.isoformat() if self.created_at else None,
                "synced_at": self.synced_at.isoformat() if self.synced_at else None}

    @classmethod
    def registrar_mutacao(cls, estabelecimento_id, tabela, registro_id, operacao, payload):
        if not estabelecimento_id: return False
        try:
            nova = cls(estabelecimento_id=estabelecimento_id, tabela=tabela, registro_id=registro_id,
                       operacao=operacao, payload_json=json.dumps(payload, default=str))
            db.session.add(nova)
            return True
        except: return False

def _should_sync(instance) -> bool:
    if not is_offline_mode(): return False
    if isinstance(instance, SyncQueue): return False
    return True

@event.listens_for(db.session, "after_flush")
def after_flush_listener(session, flush_context):
    if not is_offline_mode(): return
    for obj in session.new:
        if _should_sync(obj) and hasattr(obj, "estabelecimento_id"):
            SyncQueue.registrar_mutacao(obj.estabelecimento_id, obj.__tablename__, obj.id, "insert",
                                        obj.to_dict() if hasattr(obj, "to_dict") else {})
    for obj in session.dirty:
        if _should_sync(obj) and hasattr(obj, "estabelecimento_id"):
            SyncQueue.registrar_mutacao(obj.estabelecimento_id, obj.__tablename__, obj.id, "update",
                                        obj.to_dict() if hasattr(obj, "to_dict") else {})
    for obj in session.deleted:
        if _should_sync(obj) and hasattr(obj, "estabelecimento_id"):
            SyncQueue.registrar_mutacao(obj.estabelecimento_id, obj.__tablename__, obj.id, "delete", {"id": obj.id})

# ==============================================================================
# MODELOS DE DADOS (Parte 2/4)
# ==============================================================================

# ------------------------------------------------------------------------------
# Modelos de Negócio
# ------------------------------------------------------------------------------

class Lead(db.Model):
    __tablename__ = "leads"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(30), nullable=False)
    origem = db.Column(db.String(100), default="landing_page")
    observacao = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "email": self.email, "whatsapp": self.whatsapp,
                "origem": self.origem, "data_cadastro": self.data_cadastro.isoformat() if self.data_cadastro else None}

class Configuracao(db.Model, MultiTenantMixin, SerializableMixin):
    __tablename__ = "configuracoes"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    logo_url = db.Column(db.String(500))
    logo_base64 = db.Column(db.Text)
    cor_principal = db.Column(db.String(7), default="#2563eb")
    tema_escuro = db.Column(db.Boolean, default=False)
    emitir_nfe = db.Column(db.Boolean, default=False)
    emitir_nfce = db.Column(db.Boolean, default=True)
    impressao_automatica = db.Column(db.Boolean, default=False)
    tipo_impressora = db.Column(db.String(20), default="termica_80mm")
    exibir_preco_tela = db.Column(db.Boolean, default=True)
    permitir_venda_sem_estoque = db.Column(db.Boolean, default=False)
    desconto_maximo_percentual = db.Column(db.Numeric(5, 2), default=10.00)
    desconto_maximo_funcionario = db.Column(db.Numeric(5, 2), default=10.00)
    arredondamento_valores = db.Column(db.Boolean, default=True)
    formas_pagamento = db.Column(db.Text, default='["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX", "Voucher", "Fiado"]')
    controlar_validade = db.Column(db.Boolean, default=True)
    alerta_estoque_minimo = db.Column(db.Boolean, default=True)
    dias_alerta_validade = db.Column(db.Integer, default=30)
    estoque_minimo_padrao = db.Column(db.Integer, default=10)
    tempo_sessao_minutos = db.Column(db.Integer, default=30)
    tentativas_senha_bloqueio = db.Column(db.Integer, default=3)
    alertas_email = db.Column(db.Boolean, default=False)
    alertas_whatsapp = db.Column(db.Boolean, default=False)
    horas_extras_percentual = db.Column(db.Numeric(5, 2), default=50.00)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    __table_args__ = (db.UniqueConstraint("estabelecimento_id", name="uq_configuracao_estab"),)

    def to_dict(self, depth=0):
        data = super().to_dict(depth=depth)
        try: data["formas_pagamento"] = json.loads(self.formas_pagamento or "[]")
        except: data["formas_pagamento"] = ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX", "Voucher", "Fiado"]
        return data

class Funcionario(db.Model, MultiTenantMixin, UserMixin, SoftDeleteMixin, SerializableMixin, AuditMixin):
    __tablename__ = "funcionarios"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date, nullable=False)
    celular = db.Column(db.String(30), nullable=False)
    telefone = db.Column(db.String(30))
    email = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(50), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False)
    data_demissao = db.Column(db.Date)
    salario_base = db.Column(db.Numeric(19, 4), default=0)
    salario = db.Column(db.Numeric(10, 2))
    observacoes = db.Column(db.Text)
    permissoes_json = db.Column(db.Text)
    username = db.Column(db.String(50), nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    foto_url = db.Column(db.String(500))
    role = db.Column(db.String(30), default="FUNCIONARIO")
    status = db.Column(db.String(20), default="ativo")
    is_super_admin = db.Column(db.Boolean, default=False)
    permissoes = db.Column(db.JSON, default=lambda: {"pdv": True, "estoque": True, "compras": False, "financeiro": False, "configuracoes": False})
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=utcnow)

    __table_args__ = (
        db.Index("ix_funcionario_cpf", "cpf"),
        db.Index("ix_funcionario_estabelecimento", "estabelecimento_id"),
        db.UniqueConstraint("estabelecimento_id", "cpf", name="uq_funcionario_estab_cpf"),
        db.UniqueConstraint("estabelecimento_id", "username", name="uq_funcionario_estab_username"),
    )

    @validates("cpf")
    def validate_cpf(self, key, value):
        if not value: return value
        n = normalizar_documento(value)
        if not validar_cpf(n): raise ValueError("CPF inválido")
        return n

    @property
    def is_authenticated(self): return bool(self.ativo)
    @property
    def is_active(self): return bool(self.ativo)
    @property
    def is_anonymous(self): return False
    def get_id(self): return str(self.id)
    def get_username(self): return self.username
    def set_password(self, p): self.senha = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.senha, p)
    set_senha = set_password
    check_senha = check_password

    def to_dict(self, depth=0):
        data = super().to_dict(depth=depth)
        data["usuario"] = self.username
        data["nivel_acesso"] = self.role
        data["salario"] = float(self.salario) if self.salario else (float(self.salario_base) if self.salario_base else 0.0)
        return data

class FuncionarioPreferencias(db.Model, MultiTenantMixin):
    __tablename__ = "funcionarios_preferencias"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id", ondelete="CASCADE"), unique=True, nullable=False)
    tema_escuro = db.Column(db.Boolean, default=False)
    notificacoes_push = db.Column(db.Boolean, default=True)
    idioma = db.Column(db.String(10), default="pt-BR")
    sidebar_colapsada = db.Column(db.Boolean, default=False)
    filtros_salvos = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    funcionario = db.relationship("Funcionario", backref=db.backref("preferencias", uselist=False, cascade="all, delete-orphan"))

    def to_dict(self):
        return {"tema_escuro": bool(self.tema_escuro), "notificacoes_push": bool(self.notificacoes_push),
                "idioma": self.idioma, "sidebar_colapsada": bool(self.sidebar_colapsada), "filtros_salvos": self.filtros_salvos or {}}

class Beneficio(db.Model, MultiTenantMixin):
    __tablename__ = "beneficios"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200))
    valor_padrao = db.Column(db.Numeric(19, 4), default=0)
    ativo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "descricao": self.descricao,
                "valor_padrao": float(self.valor_padrao) if self.valor_padrao else 0.0, "ativo": self.ativo}

class FuncionarioBeneficio(db.Model, MultiTenantMixin):
    __tablename__ = "funcionario_beneficios"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False)
    beneficio_id = db.Column(db.Integer, db.ForeignKey("beneficios.id", ondelete="CASCADE"), nullable=False)
    valor = db.Column(db.Numeric(19, 4), nullable=False)
    data_inicio = db.Column(db.Date, default=date.today)
    ativo = db.Column(db.Boolean, default=True)
    funcionario = db.relationship("Funcionario", backref=db.backref("beneficios_ativos", lazy=True))
    beneficio = db.relationship("Beneficio")

class BancoHoras(db.Model, MultiTenantMixin):
    __tablename__ = "banco_horas"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False)
    mes_referencia = db.Column(db.String(7), nullable=False)
    saldo_minutos = db.Column(db.Integer, default=0)
    valor_hora_extra = db.Column(db.Numeric(19, 4), default=0)
    horas_trabalhadas_minutos = db.Column(db.Integer, default=0)
    horas_esperadas_minutos = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    funcionario = db.relationship("Funcionario", backref=db.backref("banco_horas", lazy=True))
    __table_args__ = (db.UniqueConstraint("funcionario_id", "mes_referencia", name="uq_banco_func_mes"),)

class JustificativaPonto(db.Model, MultiTenantMixin, SerializableMixin):
    __tablename__ = "justificativas_ponto"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False)
    aprovador_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=True)
    tipo = db.Column(db.String(30), nullable=False)
    data = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    observacao = db.Column(db.Text)
    documento_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default="pendente")
    data_resposta = db.Column(db.DateTime)
    motivo_rejeicao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    funcionario = db.relationship("Funcionario", foreign_keys=[funcionario_id], backref=db.backref("justificativas", lazy=True, cascade="all, delete-orphan"))
    aprovador = db.relationship("Funcionario", foreign_keys=[aprovador_id], backref=db.backref("justificativas_aprovadas", lazy=True))
    __table_args__ = (db.Index("ix_justificativa_funcionario", "funcionario_id"), db.Index("ix_justificativa_data", "data"), db.Index("ix_justificativa_status", "status"))

    def to_dict(self):
        return {"id": self.id, "funcionario_id": self.funcionario_id, "funcionario_nome": self.funcionario.nome if self.funcionario else None,
                "aprovador_id": self.aprovador_id, "aprovador_nome": self.aprovador.nome if self.aprovador else None,
                "tipo": self.tipo, "data": self.data.isoformat() if self.data else None, "motivo": self.motivo,
                "status": self.status, "created_at": self.created_at.isoformat() if self.created_at else None}

class Cliente(db.Model, MultiTenantMixin, SoftDeleteMixin, SerializableMixin, AuditMixin, EnderecoMixin):
    __tablename__ = "clientes"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    telefone = db.Column(db.String(30))
    celular = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100))
    limite_credito = db.Column(db.Numeric(19, 4), default=0)
    saldo_devedor = db.Column(db.Numeric(19, 4), default=0)
    ultima_compra = db.Column(db.DateTime)
    total_compras = db.Column(db.Integer, default=0)
    valor_total_gasto = db.Column(db.Numeric(19, 4), default=0)
    ativo = db.Column(db.Boolean, default=True)
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=utcnow)
    data_atualizacao = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    __table_args__ = (db.Index("ix_cliente_cpf", "cpf"), db.Index("ix_cliente_nome", "nome"), db.UniqueConstraint("estabelecimento_id", "cpf", name="uq_cliente_estab_cpf"))

    @staticmethod
    def segmentar_rfm(recency_score: int, frequency_score: int, monetary_score: int) -> str:
        r, f, m = int(recency_score), int(frequency_score), int(monetary_score)
        if r >= 4 and f >= 4 and m >= 4: return "Campeão"
        if r >= 4 and f >= 3: return "Fiel"
        if r <= 2 and (f >= 3 or m >= 3): return "Risco"
        if r == 1 and f <= 2: return "Perdido"
        return "Regular"

    @classmethod
    def calcular_rfm(cls, estabelecimento_id: int, days: int = 180) -> Dict[str, Any]:
        days = int(days) if days else 180
        if days <= 0: days = 180
        data_inicio = utcnow() - timedelta(days=days)
        rows = db.session.query(Venda.cliente_id, func.count(Venda.id), func.coalesce(func.sum(Venda.total), 0), func.max(Venda.data_venda))\
            .filter(Venda.estabelecimento_id == estabelecimento_id, Venda.data_venda >= data_inicio, Venda.status == "finalizada", Venda.cliente_id.isnot(None))\
            .group_by(Venda.cliente_id).all()
        now = utcnow()
        metrics = []
        for r in rows:
            ultima = r[3]
            recency_days = (now - ultima).days if ultima else days
            metrics.append({"cliente_id": int(r[0]), "recency_days": int(recency_days), "frequency": int(r[1] or 0), "monetary": float(r[2] or 0)})
        if not metrics: return {"segments": {}, "customers": [], "window_days": days}
        def _score_quintile(values_sorted, value, higher_is_better: bool) -> int:
            n = len(values_sorted)
            if n == 1: return 3
            import bisect
            idx = bisect.bisect_right(values_sorted, value) - 1
            if idx < 0: idx = 0
            p = (idx + 1) / n
            score = int(p * 5)
            if score < 1: score = 1
            if score > 5: score = 5
            return score if higher_is_better else (6 - score)
        recency_sorted = sorted(m["recency_days"] for m in metrics)
        frequency_sorted = sorted(m["frequency"] for m in metrics)
        monetary_sorted = sorted(m["monetary"] for m in metrics)
        segments_count = {"Campeão": 0, "Fiel": 0, "Risco": 0, "Perdido": 0, "Regular": 0}
        customers = []
        for m in metrics:
            rs = _score_quintile(recency_sorted, m["recency_days"], False)
            fs = _score_quintile(frequency_sorted, m["frequency"], True)
            ms = _score_quintile(monetary_sorted, m["monetary"], True)
            seg = cls.segmentar_rfm(rs, fs, ms)
            segments_count[seg] = segments_count.get(seg, 0) + 1
            customers.append({**m, "recency_score": rs, "frequency_score": fs, "monetary_score": ms, "segment": seg})
        return {"segments": segments_count, "customers": customers, "window_days": days}

class Fornecedor(db.Model, MultiTenantMixin, EnderecoMixin, SoftDeleteMixin, SerializableMixin, AuditMixin):
    __tablename__ = "fornecedores"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    nome_fantasia = db.Column(db.String(150), nullable=False)
    razao_social = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), nullable=False)
    inscricao_estadual = db.Column(db.String(20))
    telefone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    contato_nome = db.Column(db.String(100))
    contato_telefone = db.Column(db.String(30))
    prazo_entrega = db.Column(db.Integer, default=7)
    forma_pagamento = db.Column(db.String(50), default="30 DIAS")
    classificacao = db.Column(db.String(20), default="REGULAR")
    total_compras = db.Column(db.Integer, default=0)
    valor_total_comprado = db.Column(db.Numeric(19, 4), default=0)
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=utcnow)
    data_atualizacao = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    __table_args__ = (db.Index("ix_fornecedor_cnpj", "cnpj"), db.UniqueConstraint("estabelecimento_id", "cnpj", name="uq_fornecedor_estab_cnpj"))

    @validates("cnpj")
    def validate_cnpj(self, key, value):
        if not validar_cnpj(value): raise ValueError(f"CNPJ inválido: {value}")
        return normalizar_documento(value)

class CategoriaProduto(db.Model, MultiTenantMixin, SoftDeleteMixin, SerializableMixin):
    __tablename__ = "categorias_produto"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text)
    codigo = db.Column(db.String(20))
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    __table_args__ = (db.Index("ix_categoria_nome", "nome"), db.UniqueConstraint("estabelecimento_id", "nome", name="uq_categoria_estab_nome"))

    @staticmethod
    def normalizar_nome_categoria(nome: str) -> str:
        if not nome: return ""
        return " ".join(nome.strip().split()).title()

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "descricao": self.descricao, "codigo": self.codigo, "ativo": self.ativo}

class Produto(db.Model, MultiTenantMixin, SoftDeleteMixin, SerializableMixin, AuditMixin):
    __tablename__ = "produtos"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias_produto.id"), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"))
    codigo_barras = db.Column(db.String(50))
    codigo_interno = db.Column(db.String(50))
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    marca = db.Column(db.String(50))
    fabricante = db.Column(db.String(100))
    tipo = db.Column(db.String(50))
    subcategoria = db.Column(db.String(50))
    unidade_medida = db.Column(db.String(20), default="UN")
    quantidade = db.Column(db.Numeric(10, 3), default=0.0)
    quantidade_minima = db.Column(db.Numeric(10, 3), default=10.0)
    preco_custo = db.Column(db.Numeric(19, 4), nullable=False)
    preco_venda = db.Column(db.Numeric(19, 4), nullable=False)
    margem_lucro = db.Column(db.Numeric(19, 4), nullable=True)
    ncm = db.Column(db.String(8))
    origem = db.Column(db.Integer, default=0)
    total_vendido = db.Column(db.Numeric(19, 4), default=0.0)
    quantidade_vendida = db.Column(db.Numeric(10, 3), default=0.0)
    ultima_venda = db.Column(db.DateTime)
    classificacao_abc = db.Column(db.String(1))
    data_fabricacao = db.Column(db.Date)
    data_validade = db.Column(db.Date)
    lote = db.Column(db.String(50))
    imagem_url = db.Column(db.String(255))
    controlar_validade = db.Column(db.Boolean, default=True)
    ativo = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    categoria = db.relationship("CategoriaProduto", backref=db.backref("produtos", lazy=True))
    fornecedor = db.relationship("Fornecedor", backref=db.backref("produtos", lazy=True))
    __table_args__ = (db.Index("ix_produto_nome", "nome"), db.Index("ix_produto_codigo", "codigo_interno"), db.Index("ix_produto_categoria", "categoria_id"),
                      db.UniqueConstraint("estabelecimento_id", "codigo_interno", name="uq_produto_estab_codigo"),
                      db.UniqueConstraint("estabelecimento_id", "codigo_barras", name="uq_produto_estab_codbar"))

    @hybrid_property
    def estoque_status(self):
        try:
            qtd = float(self.quantidade or 0); qtd_min = float(self.quantidade_minima or 0)
            if qtd <= 0: return "esgotado"
            if qtd <= qtd_min: return "critico"
            if qtd <= (qtd_min * 1.5): return "alerta"
            return "normal"
        except: return "normal"

    @estoque_status.expression
    def estoque_status(cls):
        return case((cls.quantidade <= 0, "esgotado"), (cls.quantidade <= cls.quantidade_minima, "critico"),
                    (cls.quantidade <= (cls.quantidade_minima * 1.5), "alerta"), else_="normal")

    def movimentar_estoque(self, quantidade: int, tipo: str, motivo: str, usuario_id: int, venda_id: int = None):
        if tipo == 'saida' and quantidade <= 0: raise ValueError("Quantidade de saída deve ser positiva")
        qtd_anterior = self.quantidade
        if tipo == 'entrada': self.quantidade += quantidade
        elif tipo == 'saida':
            self.quantidade -= quantidade
            self.quantidade_vendida += quantidade
            self.total_vendido += (self.preco_venda * quantidade)
            self.ultima_venda = utcnow()
        return MovimentacaoEstoque(estabelecimento_id=self.estabelecimento_id, produto_id=self.id, venda_id=venda_id,
                                   funcionario_id=usuario_id, tipo=tipo, quantidade=quantidade, quantidade_anterior=qtd_anterior,
                                   quantidade_atual=self.quantidade, custo_unitario=self.preco_custo,
                                   valor_total=self.preco_venda * quantidade if tipo == 'saida' else self.preco_custo * quantidade, motivo=motivo)

    def recalcular_preco_custo_ponderado(self, quantidade_entrada: int, custo_unitario_entrada, estoque_atual: int = None,
                                         registrar_historico: bool = True, funcionario_id: int = None, motivo: str = "Entrada de estoque - CMP"):
        if quantidade_entrada is None or int(quantidade_entrada) <= 0 or custo_unitario_entrada is None: return
        custo_entrada = Decimal(str(custo_unitario_entrada))
        if custo_entrada < 0: raise ValueError("Custo unitário não pode ser negativo")
        qtd_atual = int(self.quantidade or 0) if estoque_atual is None else int(estoque_atual)
        if qtd_atual < 0: qtd_atual = 0
        custo_anterior = Decimal(str(self.preco_custo or 0))
        margem_anterior = Decimal(str(self.margem_lucro or 0))
        qtd_entrada = int(quantidade_entrada)
        base = qtd_atual + qtd_entrada
        if base <= 0: self.preco_custo = custo_entrada
        else:
            novo_custo = ((Decimal(qtd_atual) * custo_anterior) + (Decimal(qtd_entrada) * custo_entrada)) / Decimal(base)
            self.preco_custo = novo_custo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if self.preco_venda and self.preco_custo and self.preco_custo > 0:
            self.margem_lucro = (self.preco_venda - self.preco_custo) / self.preco_custo * 100
        else: self.margem_lucro = 0
        if registrar_historico and funcionario_id and abs(self.preco_custo - custo_anterior) > Decimal("0.01"):
            db.session.add(HistoricoPrecos(estabelecimento_id=self.estabelecimento_id, produto_id=self.id, funcionario_id=funcionario_id,
                                           preco_custo_anterior=custo_anterior, preco_venda_anterior=self.preco_venda, margem_anterior=margem_anterior,
                                           preco_custo_novo=self.preco_custo, preco_venda_novo=self.preco_venda, margem_nova=self.margem_lucro,
                                           motivo=motivo, observacoes=f"CMP recalculado: entrada de {quantidade_entrada} unidades a R$ {custo_unitario_entrada}"))

    @staticmethod
    def calcular_preco_por_markup(preco_custo, markup_percentual):
        if preco_custo is None or markup_percentual is None: return Decimal("0")
        custo = Decimal(str(preco_custo)); markup = Decimal(str(markup_percentual))
        if custo < 0 or markup < 0: return Decimal("0")
        return (custo * (1 + markup / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calcular_markup_de_preco(preco_custo, preco_venda):
        if preco_custo is None or preco_venda is None: return Decimal("0")
        custo = Decimal(str(preco_custo)); venda = Decimal(str(preco_venda))
        if custo <= 0: return Decimal("0")
        return ((venda - custo) / custo * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calcular_classificacao_abc_dinamica(estabelecimento_id: int, periodo_dias: int = 90):
        data_inicio = utcnow() - timedelta(days=periodo_dias)
        fat = db.session.query(VendaItem.produto_id, func.sum(VendaItem.total_item)).join(Venda)\
            .filter(Venda.estabelecimento_id == estabelecimento_id, Venda.status == 'finalizada', Venda.data_venda >= data_inicio)\
            .group_by(VendaItem.produto_id).order_by(func.sum(VendaItem.total_item).desc()).all()
        if not fat: return {}
        total = sum(Decimal(str(f[1] or 0)) for f in fat)
        if total == 0: return {}
        classificacoes = {}
        acum = Decimal('0')
        for pid, val in fat:
            acum += Decimal(str(val or 0))
            pct = acum / total * 100
            if pct <= 80: classificacoes[pid] = 'A'
            elif pct <= 95: classificacoes[pid] = 'B'
            else: classificacoes[pid] = 'C'
        return classificacoes

    @staticmethod
    def atualizar_classificacoes_abc(estabelecimento_id: int, periodo_dias: int = 90):
        classificacoes = Produto.calcular_classificacao_abc_dinamica(estabelecimento_id, periodo_dias)
        atualizados = 0
        for pid, cls in classificacoes.items():
            p = Produto.query.get(pid)
            if p and p.estabelecimento_id == estabelecimento_id:
                p.classificacao_abc = cls
                atualizados += 1
        sem = Produto.query.filter(Produto.estabelecimento_id == estabelecimento_id, Produto.ativo == True, ~Produto.id.in_(classificacoes.keys())).all()
        for p in sem:
            p.classificacao_abc = 'C'
            atualizados += 1
        db.session.commit()
        return {'produtos_atualizados': atualizados, 'classe_a': sum(1 for c in classificacoes.values() if c == 'A'),
                'classe_b': sum(1 for c in classificacoes.values() if c == 'B'), 'classe_c': sum(1 for c in classificacoes.values() if c == 'C'),
                'sem_vendas': len(sem)}

    def demanda_media_diaria(self, days: int = 30) -> float:
        days = int(days) if days else 30
        if days <= 0: days = 30
        data_inicio = utcnow() - timedelta(days=days)
        total = db.session.query(func.coalesce(func.sum(VendaItem.quantidade), 0)).join(Venda)\
            .filter(Venda.estabelecimento_id == self.estabelecimento_id, Venda.data_venda >= data_inicio, Venda.status == "finalizada", VendaItem.produto_id == self.id).scalar() or 0
        return float(total) / float(days)

    def ponto_ressuprimento(self, lead_time_dias: int, days: int = 30, fator_seguranca: float = 1.5) -> float:
        if lead_time_dias <= 0: return 0.0
        return float(self.demanda_media_diaria(days)) * float(lead_time_dias) * float(fator_seguranca)

    def calcular_giro(self, days: int = 30) -> float:
        try:
            vendido = float(self.quantidade_vendida or 0); estoque = float(self.quantidade or 0)
            if estoque <= 0: return 0.0
            return vendido / estoque
        except: return 0.0

    def calcular_cobertura_dias(self, days: int = 30):
        try:
            dmd = self.demanda_media_diaria(days)
            if dmd <= 0: return "Indeterminado" if float(self.quantidade or 0) > 0 else "Sem Estoque"
            return round(float(self.quantidade or 0) / dmd, 1)
        except: return "---"

    def calcular_status_giro(self, days: int = 30) -> str:
        try:
            dmd = self.demanda_media_diaria(days)
            if dmd <= 0: return "Sem Vendas"
            if dmd < 1: return "Baixo Giro"
            if dmd < 5: return "Médio Giro"
            return "Alto Giro"
        except: return "Sem Vendas"

    def get_lotes_disponiveis(self):
        return ProdutoLote.query.filter_by(produto_id=self.id, ativo=True).filter(ProdutoLote.quantidade > 0).order_by(ProdutoLote.data_validade.asc()).all()

    def consumir_estoque_fifo(self, quantidade: int) -> List[Dict]:
        consumidos = []
        restante = quantidade
        for lote in self.get_lotes_disponiveis():
            if restante <= 0: break
            qtd = min(restante, lote.quantidade)
            lote.quantidade -= qtd
            restante -= qtd
            consumidos.append({'lote_id': lote.id, 'quantidade_consumida': qtd, 'lote': lote})
        self.quantidade -= quantidade
        return consumidos

    def to_dict(self, include_metrics=False, depth=0):
        data = super().to_dict(depth=depth)
        if include_metrics: data["estoque_status"] = self.estoque_status
        return data


class ProdutoLote(db.Model, MultiTenantMixin):
    __tablename__ = "produto_lotes"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"))
    pedido_compra_id = db.Column(db.Integer, db.ForeignKey("pedidos_compra.id"))
    numero_lote = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    quantidade_inicial = db.Column(db.Numeric(10, 3), nullable=False)
    data_fabricacao = db.Column(db.Date, nullable=True)
    data_validade = db.Column(db.Date, nullable=False)
    data_entrada = db.Column(db.Date, default=date.today, nullable=False)
    preco_custo_unitario = db.Column(db.Numeric(19, 4), nullable=False)
    preco_venda = db.Column(db.Numeric(19, 4), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    motivo_inativacao = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    produto = db.relationship("Produto", backref=db.backref("lotes", lazy=True, cascade="all, delete-orphan"))
    fornecedor = db.relationship("Fornecedor", backref=db.backref("lotes_fornecidos", lazy=True))
    pedido_compra = db.relationship("PedidoCompra", backref=db.backref("lotes_recebidos", lazy=True))
    __table_args__ = (db.Index("ix_lote_produto", "produto_id"), db.Index("ix_lote_validade", "data_validade"),
                      db.Index("ix_lote_entrada", "data_entrada"), db.UniqueConstraint("estabelecimento_id", "numero_lote", name="uq_lote_estab_numero"))

    @property
    def dias_para_vencer(self) -> int:
        return (self.data_validade - date.today()).days

    @property
    def esta_vencido(self) -> bool:
        return self.dias_para_vencer < 0

    def to_dict(self):
        return {"id": self.id, "numero_lote": self.numero_lote, "produto_id": self.produto_id,
                "quantidade": float(self.quantidade) if self.quantidade else 0.0,
                "data_validade": self.data_validade.isoformat() if self.data_validade else None,
                "dias_para_vencer": self.dias_para_vencer, "esta_vencido": self.esta_vencido, "ativo": self.ativo}

# ------------------------------------------------------------------------------
# Venda e Pagamentos Flexíveis
# ------------------------------------------------------------------------------
class Venda(db.Model, MultiTenantMixin, SoftDeleteMixin, SerializableMixin, AuditMixin):
    __tablename__ = "vendas"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"))
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=False)
    caixa_id = db.Column(db.Integer, db.ForeignKey("caixas.id"), nullable=True)
    codigo = db.Column(db.String(50), nullable=False)
    subtotal = db.Column(db.Numeric(19, 4), nullable=False, default=0)
    desconto = db.Column(db.Numeric(19, 4), default=0)
    total = db.Column(db.Numeric(19, 4), nullable=False, default=0)
    valor_recebido = db.Column(db.Numeric(19, 4), default=0)
    troco = db.Column(db.Numeric(19, 4), default=0)
    status = db.Column(db.String(20), default="finalizada")
    quantidade_itens = db.Column(db.Integer, default=0)
    observacoes = db.Column(db.Text)
    tipo_venda = db.Column(db.String(20), default="balcao")
    data_venda = db.Column(db.DateTime, default=utcnow)
    data_cancelamento = db.Column(db.DateTime)
    motivo_cancelamento = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("vendas", lazy=True))
    cliente = db.relationship("Cliente", backref=db.backref("vendas", lazy=True))
    funcionario = db.relationship("Funcionario", backref=db.backref("vendas", lazy=True))
    itens = db.relationship("VendaItem", back_populates="venda", lazy=True, cascade="all, delete-orphan")
    pagamentos = db.relationship("Pagamento", back_populates="venda", lazy=True, cascade="all, delete-orphan")
    __table_args__ = (db.Index("ix_venda_codigo", "codigo"), db.Index("ix_venda_data", "data_venda"),
                      db.Index("ix_venda_tipo", "tipo_venda"), db.UniqueConstraint("estabelecimento_id", "codigo", name="uq_venda_estab_codigo"))

    def atualizar_totais(self):
        self.subtotal = sum(item.total_item for item in self.itens) if self.itens else Decimal("0")
        self.total = self.subtotal - (self.desconto or Decimal("0"))
        self.valor_recebido = sum(p.valor for p in self.pagamentos if p.status == "aprovado") if self.pagamentos else Decimal("0")
        self.troco = max(Decimal("0"), self.valor_recebido - self.total)

    def to_dict(self, depth=0):
        data = super().to_dict(depth=depth)
        data["cliente_nome"] = self.cliente.nome if self.cliente else "NÃO INFORMADO"
        data["funcionario_nome"] = self.funcionario.nome if self.funcionario else "NÃO INFORMADO"
        data["itens"] = [item.to_dict() for item in self.itens] if self.itens else []
        data["pagamentos"] = [p.to_dict() for p in self.pagamentos] if self.pagamentos else []
        return data

class VendaItem(db.Model, MultiTenantMixin, SerializableMixin, AuditMixin):
    __tablename__ = "venda_itens"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id", ondelete="CASCADE"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    produto_nome = db.Column(db.String(100), nullable=False)
    produto_codigo = db.Column(db.String(50))
    produto_unidade = db.Column(db.String(20))
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    preco_unitario = db.Column(db.Numeric(19, 4), nullable=False)
    desconto = db.Column(db.Numeric(19, 4), default=0)
    total_item = db.Column(db.Numeric(19, 4), nullable=False)
    custo_unitario = db.Column(db.Numeric(19, 4))
    margem_item = db.Column(db.Numeric(19, 4))
    margem_lucro_real = db.Column(db.Numeric(19, 4))
    venda = db.relationship("Venda", back_populates="itens")
    produto = db.relationship("Produto", backref=db.backref("itens_venda", lazy=True))
    __table_args__ = (db.Index("ix_venda_item_venda", "venda_id"), db.Index("ix_venda_item_produto", "produto_id"),
                      db.UniqueConstraint("sync_uuid", name="uq_venda_itens_sync_uuid"))

    def to_dict(self, depth=0):
        data = super().to_dict(depth=depth)
        data["produto_nome"] = self.produto_nome
        return data

class Pagamento(db.Model, MultiTenantMixin, SerializableMixin):
    __tablename__ = "pagamentos"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id", ondelete="CASCADE"), nullable=False)
    forma_pagamento = db.Column(db.String(30), nullable=False)
    valor = db.Column(db.Numeric(19, 4), nullable=False)
    bandeira = db.Column(db.String(20))
    ultimos_digitos = db.Column(db.String(4))
    parcelas = db.Column(db.Integer, default=1)
    codigo_voucher = db.Column(db.String(50))
    saldo_restante_voucher = db.Column(db.Numeric(19, 4))
    prazo_dias = db.Column(db.Integer)
    status = db.Column(db.String(20), default="aprovado")
    data_pagamento = db.Column(db.DateTime, default=utcnow)
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    venda = db.relationship("Venda", back_populates="pagamentos")
    __table_args__ = (db.Index("ix_pagamento_venda", "venda_id"), db.Index("ix_pagamento_data", "data_pagamento"),
                      db.Index("ix_pagamento_forma", "forma_pagamento"))

    def to_dict(self, depth=0):
        return super().to_dict(depth=depth)

class MovimentacaoEstoque(db.Model, MultiTenantMixin, SerializableMixin, AuditMixin):
    __tablename__ = "movimentacoes_estoque"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"))
    pedido_compra_id = db.Column(db.Integer, db.ForeignKey("pedidos_compra.id"))
    lote_id = db.Column(db.Integer, db.ForeignKey("produto_lotes.id"))
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"))
    tipo = db.Column(db.String(20), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    quantidade_anterior = db.Column(db.Numeric(10, 3), nullable=False)
    quantidade_atual = db.Column(db.Numeric(10, 3), nullable=False)
    custo_unitario = db.Column(db.Numeric(19, 4))
    valor_total = db.Column(db.Numeric(19, 4))
    motivo = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("movimentacoes_estoque", lazy=True))
    produto = db.relationship("Produto", backref=db.backref("movimentacoes", lazy=True))
    venda = db.relationship("Venda", backref=db.backref("movimentacoes_estoque_venda", lazy=True))
    funcionario = db.relationship("Funcionario", backref=db.backref("movimentacoes", lazy=True))
    lote = db.relationship("ProdutoLote", backref=db.backref("movimentacoes_lote", lazy=True))
    __table_args__ = (db.Index("ix_mov_estoque_produto", "produto_id"), db.Index("ix_mov_estoque_data", "created_at"))

class HistoricoPrecos(db.Model, MultiTenantMixin, SerializableMixin):
    __tablename__ = "historico_precos"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=False)
    preco_custo_anterior = db.Column(db.Numeric(19, 4), nullable=False)
    preco_venda_anterior = db.Column(db.Numeric(19, 4), nullable=False)
    margem_anterior = db.Column(db.Numeric(19, 4), nullable=False)
    preco_custo_novo = db.Column(db.Numeric(19, 4), nullable=False)
    preco_venda_novo = db.Column(db.Numeric(19, 4), nullable=False)
    margem_nova = db.Column(db.Numeric(19, 4), nullable=False)
    motivo = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text)
    data_alteracao = db.Column(db.DateTime, default=utcnow, nullable=False)
    produto = db.relationship("Produto", backref=db.backref("historico_precos", lazy=True))
    funcionario = db.relationship("Funcionario", backref=db.backref("alteracoes_precos", lazy=True))
    __table_args__ = (db.Index("ix_historico_produto", "produto_id"), db.Index("ix_historico_data", "data_alteracao"))

class PedidoCompra(db.Model, MultiTenantMixin, SerializableMixin, AuditMixin):
    __tablename__ = "pedidos_compra"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=False)
    numero_pedido = db.Column(db.String(50), nullable=False)
    data_pedido = db.Column(db.DateTime, default=utcnow, nullable=False)
    data_previsao_entrega = db.Column(db.Date)
    data_recebimento = db.Column(db.Date)
    status = db.Column(db.String(20), default="pendente")
    subtotal = db.Column(db.Numeric(19, 4), default=0)
    desconto = db.Column(db.Numeric(19, 4), default=0)
    frete = db.Column(db.Numeric(19, 4), default=0)
    total = db.Column(db.Numeric(19, 4), default=0)
    condicao_pagamento = db.Column(db.String(50))
    numero_nota_fiscal = db.Column(db.String(50))
    serie_nota_fiscal = db.Column(db.String(10))
    observacoes = db.Column(db.Text)
    fornecedor = db.relationship("Fornecedor", backref=db.backref("pedidos_compra", lazy="dynamic"))
    funcionario = db.relationship("Funcionario", backref=db.backref("pedidos_compra", lazy=True))
    itens = db.relationship("PedidoCompraItem", back_populates="pedido", lazy=True, cascade="all, delete-orphan")
    __table_args__ = (db.Index("ix_pedido_numero", "numero_pedido"), db.UniqueConstraint("estabelecimento_id", "numero_pedido", name="uq_pedido_estab_numero"))

class PedidoCompraItem(db.Model, MultiTenantMixin, SerializableMixin):
    __tablename__ = "pedido_compra_itens"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos_compra.id", ondelete="CASCADE"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    produto_nome = db.Column(db.String(100), nullable=False)
    produto_unidade = db.Column(db.String(20), default="UN")
    quantidade_solicitada = db.Column(db.Numeric(10, 3), nullable=False)
    quantidade_recebida = db.Column(db.Numeric(10, 3), default=0)
    preco_unitario = db.Column(db.Numeric(19, 4), nullable=False)
    desconto_percentual = db.Column(db.Numeric(5, 2), default=0)
    total_item = db.Column(db.Numeric(19, 4), nullable=False)
    status = db.Column(db.String(20), default="pendente")
    pedido = db.relationship("PedidoCompra", back_populates="itens")
    produto = db.relationship("Produto", backref=db.backref("itens_compra", lazy=True))
    __table_args__ = (db.Index("ix_pedido_item_pedido", "pedido_id"),)

class ContaPagar(db.Model, MultiTenantMixin, SerializableMixin, AuditMixin):
    __tablename__ = "contas_pagar"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"), nullable=False)
    pedido_compra_id = db.Column(db.Integer, db.ForeignKey("pedidos_compra.id"))
    numero_documento = db.Column(db.String(50), nullable=False)
    tipo_documento = db.Column(db.String(30), default="duplicata")
    valor_original = db.Column(db.Numeric(19, 4), nullable=False)
    valor_pago = db.Column(db.Numeric(19, 4), default=0)
    valor_atual = db.Column(db.Numeric(19, 4), nullable=False)
    data_emissao = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)
    status = db.Column(db.String(20), default="aberto")
    forma_pagamento = db.Column(db.String(30))
    observacoes = db.Column(db.Text)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("contas_pagar", lazy=True))
    fornecedor = db.relationship("Fornecedor", backref=db.backref("contas_pagar", lazy=True))
    pedido_compra = db.relationship("PedidoCompra", backref=db.backref("conta_pagar", uselist=False))
    __table_args__ = (db.Index("ix_conta_pagar_vencimento", "data_vencimento"), db.Index("ix_conta_pagar_status", "status"))

class ContaReceber(db.Model, MultiTenantMixin, SerializableMixin, AuditMixin):
    __tablename__ = "contas_receber"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"))
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"))
    numero_documento = db.Column(db.String(50), nullable=False)
    tipo_documento = db.Column(db.String(30), default="duplicata")
    valor_original = db.Column(db.Numeric(19, 4), nullable=False)
    valor_recebido = db.Column(db.Numeric(19, 4), default=0)
    valor_atual = db.Column(db.Numeric(19, 4), nullable=False)
    data_emissao = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_recebimento = db.Column(db.Date)
    status = db.Column(db.String(20), default="aberto")
    forma_recebimento = db.Column(db.String(30))
    observacoes = db.Column(db.Text)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("contas_receber", lazy=True))
    cliente = db.relationship("Cliente", backref=db.backref("contas_receber", lazy=True))
    venda = db.relationship("Venda", backref=db.backref("contas_receber", lazy=True))
    __table_args__ = (db.Index("ix_conta_receber_vencimento", "data_vencimento"), db.Index("ix_conta_receber_cliente", "cliente_id"))

class Despesa(db.Model, MultiTenantMixin, SerializableMixin, AuditMixin):
    __tablename__ = "despesas"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"))
    descricao = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(50), default="geral")
    tipo = db.Column(db.String(20), default="variavel")
    valor = db.Column(db.Numeric(19, 4), nullable=False)
    data_despesa = db.Column(db.Date, nullable=False, default=date.today)
    data_emissao = db.Column(db.Date, nullable=True)
    data_vencimento = db.Column(db.Date, nullable=True)
    forma_pagamento = db.Column(db.String(50))
    recorrente = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("despesas", lazy=True))
    fornecedor = db.relationship("Fornecedor", backref=db.backref("despesas", lazy=True))
    __table_args__ = (db.Index("ix_despesa_data", "data_despesa"), db.Index("ix_despesa_categoria", "categoria"))

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
    data_cadastro = db.Column(db.DateTime, default=utcnow)
    funcionario = db.relationship("Funcionario", backref=db.backref("logins", lazy=True))
    __table_args__ = (db.Index("ix_login_history_user", "username"), db.Index("ix_login_history_data", "data_cadastro"))

    def to_dict(self):
        return {"id": self.id, "funcionario_id": self.funcionario_id, "username": self.username,
                "ip_address": self.ip_address, "dispositivo": self.dispositivo, "success": self.success,
                "created_at": self.data_cadastro.isoformat() if self.data_cadastro else None}

class Caixa(db.Model, MultiTenantMixin, SerializableMixin, AuditMixin):
    __tablename__ = "caixas"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=False)
    numero_caixa = db.Column(db.String(20), nullable=False)
    saldo_inicial = db.Column(db.Numeric(19, 4), nullable=False)
    saldo_final = db.Column(db.Numeric(19, 4))
    saldo_atual = db.Column(db.Numeric(19, 4))
    data_abertura = db.Column(db.DateTime, default=utcnow, nullable=False)
    data_fechamento = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="aberto")
    observacoes = db.Column(db.Text)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("caixas", lazy=True))
    funcionario = db.relationship("Funcionario", backref=db.backref("caixas", lazy=True))
    __table_args__ = (db.Index("ix_caixa_status", "status"), db.Index("ix_caixa_data", "data_abertura"))

class MovimentacaoCaixa(db.Model, MultiTenantMixin, SerializableMixin, AuditMixin):
    __tablename__ = "movimentacoes_caixa"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    caixa_id = db.Column(db.Integer, db.ForeignKey("caixas.id", ondelete="CASCADE"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Numeric(19, 4), nullable=False)
    forma_pagamento = db.Column(db.String(50))
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"))
    descricao = db.Column(db.String(255), nullable=False)
    observacoes = db.Column(db.Text)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("movimentacoes_caixa", lazy=True))
    caixa = db.relationship("Caixa", backref=db.backref("movimentacoes", lazy=True, cascade="all, delete-orphan"))
    venda = db.relationship("Venda", backref=db.backref("movimentacoes_caixa", lazy=True))
    __table_args__ = (db.Index("ix_mov_caixa_caixa", "caixa_id"), db.Index("ix_mov_caixa_tipo", "tipo"))


class DashboardMetrica(db.Model, MultiTenantMixin):
    __tablename__ = "dashboard_metricas"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    data_referencia = db.Column(db.Date, nullable=False)
    total_vendas_dia = db.Column(db.Numeric(19, 4), default=0)
    quantidade_vendas_dia = db.Column(db.Integer, default=0)
    ticket_medio_dia = db.Column(db.Numeric(19, 4), default=0)
    clientes_atendidos_dia = db.Column(db.Integer, default=0)
    total_vendas_mes = db.Column(db.Numeric(19, 4), default=0)
    total_despesas_mes = db.Column(db.Numeric(19, 4), default=0)
    lucro_bruto_mes = db.Column(db.Numeric(19, 4), default=0)
    crescimento_vs_ontem = db.Column(db.Numeric(5, 2), default=0)
    crescimento_mensal = db.Column(db.Numeric(5, 2), default=0)
    tendencia_vendas = db.Column(db.String(20))
    top_produtos_json = db.Column(db.JSON)
    produtos_abc_json = db.Column(db.JSON)
    segmentacao_clientes_json = db.Column(db.JSON)
    top_clientes_json = db.Column(db.JSON)
    alertas_json = db.Column(db.JSON)
    insights_json = db.Column(db.JSON)
    data_calculo = db.Column(db.DateTime, default=utcnow)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("metricas", lazy=True))
    __table_args__ = (db.Index("ix_metrica_data", "data_referencia"),)

    def to_dict(self):
        return {"id": self.id, "estabelecimento_id": self.estabelecimento_id,
                "data_referencia": self.data_referencia.isoformat() if self.data_referencia else None,
                "total_vendas_dia": float(self.total_vendas_dia) if self.total_vendas_dia else 0.0,
                "quantidade_vendas_dia": self.quantidade_vendas_dia,
                "ticket_medio_dia": float(self.ticket_medio_dia) if self.ticket_medio_dia else 0.0,
                "total_vendas_mes": float(self.total_vendas_mes) if self.total_vendas_mes else 0.0,
                "lucro_bruto_mes": float(self.lucro_bruto_mes) if self.lucro_bruto_mes else 0.0,
                "crescimento_vs_ontem": float(self.crescimento_vs_ontem) if self.crescimento_vs_ontem else 0.0,
                "data_calculo": self.data_calculo.isoformat() if self.data_calculo else None}

class RelatorioAgendado(db.Model, MultiTenantMixin):
    __tablename__ = "relatorios_agendados"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
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
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("relatorios", lazy=True))

    @property
    def destinatarios_email(self):
        try: return json.loads(self.destinatarios_email_json)
        except: return []
    @destinatarios_email.setter
    def destinatarios_email(self, value):
        self.destinatarios_email_json = json.dumps(value)
    @property
    def parametros(self):
        try: return json.loads(self.parametros_json)
        except: return {}
    @parametros.setter
    def parametros(self, value):
        self.parametros_json = json.dumps(value)

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "tipo": self.tipo, "formato": self.formato,
                "frequencia": self.frequencia, "horario_envio": self.horario_envio.strftime("%H:%M") if self.horario_envio else None,
                "ativo": self.ativo, "ultima_execucao": self.ultima_execucao.isoformat() if self.ultima_execucao else None,
                "proxima_execucao": self.proxima_execucao.isoformat() if self.proxima_execucao else None}

class RegistroPonto(db.Model, MultiTenantMixin):
    __tablename__ = "registros_ponto"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)
    hora = db.Column(db.Time, nullable=False)
    tipo_registro = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    localizacao_endereco = db.Column(db.String(500))
    foto_url = db.Column(db.String(500))
    dispositivo = db.Column(db.String(200))
    ip_address = db.Column(db.String(50))
    observacao = db.Column(db.Text)
    status = db.Column(db.String(20), default='normal')
    minutos_atraso = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    funcionario = db.relationship("Funcionario", backref=db.backref("registros_ponto", lazy=True, cascade="all, delete-orphan"))
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("registros_ponto", lazy=True))
    __table_args__ = (db.Index("ix_ponto_funcionario_data", "funcionario_id", "data"),
                      db.Index("ix_ponto_estabelecimento", "estabelecimento_id"), db.Index("ix_ponto_data", "data"))

    def to_dict(self):
        return {'id': self.id, 'funcionario_id': self.funcionario_id,
                'funcionario_nome': self.funcionario.nome if self.funcionario else 'Desconhecido',
                'estabelecimento_id': self.estabelecimento_id,
                'data': self.data.isoformat() if self.data else None,
                'hora': self.hora.strftime('%H:%M:%S') if self.hora else None,
                'tipo': self.tipo_registro, 'tipo_registro': self.tipo_registro,
                'latitude': self.latitude, 'longitude': self.longitude,
                'localizacao_endereco': self.localizacao_endereco, 'foto_url': self.foto_url,
                'dispositivo': self.dispositivo, 'ip_address': self.ip_address,
                'observacao': self.observacao, 'status': self.status,
                'minutos_atraso': self.minutos_atraso, 'created_at': self.created_at.isoformat() if self.created_at else None}

class ConfiguracaoHorario(db.Model, MultiTenantMixin):
    __tablename__ = "configuracoes_horario"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    hora_entrada = db.Column(db.Time, nullable=False, default=time(8, 0))
    hora_saida_almoco = db.Column(db.Time, nullable=False, default=time(12, 0))
    hora_retorno_almoco = db.Column(db.Time, nullable=False, default=time(13, 0))
    hora_saida = db.Column(db.Time, nullable=False, default=time(18, 0))
    tolerancia_entrada = db.Column(db.Integer, default=10)
    tolerancia_saida_almoco = db.Column(db.Integer, default=5)
    tolerancia_retorno_almoco = db.Column(db.Integer, default=10)
    tolerancia_saida = db.Column(db.Integer, default=5)
    exigir_foto = db.Column(db.Boolean, default=True)
    exigir_localizacao = db.Column(db.Boolean, default=True)
    raio_permitido_metros = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("configuracao_horario", uselist=False, cascade="all, delete-orphan"))
    __table_args__ = (db.UniqueConstraint("estabelecimento_id", name="uq_config_horario_estab"),)

    def to_dict(self):
        return {'id': self.id, 'estabelecimento_id': self.estabelecimento_id,
                'hora_entrada': self.hora_entrada.strftime('%H:%M') if self.hora_entrada else None,
                'hora_saida_almoco': self.hora_saida_almoco.strftime('%H:%M') if self.hora_saida_almoco else None,
                'hora_retorno_almoco': self.hora_retorno_almoco.strftime('%H:%M') if self.hora_retorno_almoco else None,
                'hora_saida': self.hora_saida.strftime('%H:%M') if self.hora_saida else None,
                'tolerancia_entrada': self.tolerancia_entrada, 'tolerancia_saida_almoco': self.tolerancia_saida_almoco,
                'tolerancia_retorno_almoco': self.tolerancia_retorno_almoco, 'tolerancia_saida': self.tolerancia_saida,
                'exigir_foto': self.exigir_foto, 'exigir_localizacao': self.exigir_localizacao,
                'raio_permitido_metros': self.raio_permitido_metros}

class Auditoria(db.Model, MultiTenantMixin):
    __tablename__ = "auditoria"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    usuario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=True)
    tipo_evento = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(500), nullable=False)
    valor = db.Column(db.Numeric(19, 4), nullable=True)
    detalhes_json = db.Column(db.JSON, nullable=True)
    data_evento = db.Column(db.DateTime, default=utcnow)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("auditoria", lazy=True, cascade="all, delete-orphan"))
    usuario = db.relationship("Funcionario", backref=db.backref("atividades", lazy=True))

    def to_dict(self):
        return {"id": self.id, "estabelecimento_id": self.estabelecimento_id,
                "estabelecimento_nome": self.estabelecimento.nome_fantasia if self.estabelecimento else "N/A",
                "usuario_id": self.usuario_id, "usuario_nome": self.usuario.nome if self.usuario else "Sistema",
                "tipo_evento": self.tipo_evento, "descricao": self.descricao,
                "valor": float(self.valor) if self.valor else 0.0, "data_evento": self.data_evento.isoformat(),
                "detalhes": self.detalhes_json if self.detalhes_json else {}}

    @classmethod
    def registrar(cls, estabelecimento_id, tipo_evento, descricao, usuario_id=None, valor=None, detalhes=None):
        if not estabelecimento_id:
            if current_app: current_app.logger.warning(f"Auditoria rejeitada: estabelecimento_id nulo para evento {tipo_evento}")
            return False
        try:
            novo = cls(estabelecimento_id=estabelecimento_id, tipo_evento=tipo_evento, descricao=descricao,
                       usuario_id=usuario_id, valor=valor, detalhes_json=detalhes)
            db.session.add(novo)
            return True
        except Exception as e:
            if current_app: current_app.logger.error(f"Erro ao registrar auditoria: {str(e)}")
            return False

# ------------------------------------------------------------------------------
# Módulo de Entregas
# ------------------------------------------------------------------------------
class Motorista(db.Model, MultiTenantMixin):
    __tablename__ = "motoristas"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    rg = db.Column(db.String(20))
    cnh = db.Column(db.String(20), nullable=False)
    categoria_cnh = db.Column(db.String(2))
    validade_cnh = db.Column(db.Date)
    telefone = db.Column(db.String(30), nullable=False)
    celular = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100))
    foto_url = db.Column(db.String(500))
    tipo_vinculo = db.Column(db.String(20), default="terceirizado")
    percentual_comissao = db.Column(db.Numeric(5, 2), default=10.00)
    salario_fixo = db.Column(db.Numeric(10, 2), default=0)
    ativo = db.Column(db.Boolean, default=True)
    disponivel = db.Column(db.Boolean, default=True)
    total_entregas = db.Column(db.Integer, default=0)
    avaliacao_media = db.Column(db.Numeric(3, 2), default=0)
    data_cadastro = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("motoristas", lazy=True, cascade="all, delete-orphan"))
    __table_args__ = (db.Index("ix_motorista_cpf", "cpf"), db.Index("ix_motorista_disponivel", "disponivel"),
                      db.UniqueConstraint("estabelecimento_id", "cpf", name="uq_motorista_estab_cpf"))

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "cpf": self.cpf, "cnh": self.cnh, "categoria_cnh": self.categoria_cnh,
                "telefone": self.telefone, "celular": self.celular, "email": self.email, "tipo_vinculo": self.tipo_vinculo,
                "percentual_comissao": float(self.percentual_comissao) if self.percentual_comissao else 0.0,
                "ativo": self.ativo, "disponivel": self.disponivel, "total_entregas": self.total_entregas,
                "avaliacao_media": float(self.avaliacao_media) if self.avaliacao_media else 0.0}

class Veiculo(db.Model, MultiTenantMixin):
    __tablename__ = "veiculos"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    motorista_id = db.Column(db.Integer, db.ForeignKey("motoristas.id"))
    placa = db.Column(db.String(8), nullable=False)
    renavam = db.Column(db.String(20))
    tipo = db.Column(db.String(30), nullable=False)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    ano = db.Column(db.Integer)
    cor = db.Column(db.String(20))
    capacidade_kg = db.Column(db.Numeric(10, 2), default=0)
    capacidade_m3 = db.Column(db.Numeric(10, 3), default=0)
    proprietario = db.Column(db.String(20), default="motorista")
    valor_aluguel = db.Column(db.Numeric(10, 2), default=0)
    km_atual = db.Column(db.Numeric(10, 2), default=0)
    data_ultima_manutencao = db.Column(db.Date)
    data_proxima_manutencao = db.Column(db.Date)
    data_vencimento_licenciamento = db.Column(db.Date)
    data_vencimento_seguro = db.Column(db.Date)
    consumo_medio = db.Column(db.Numeric(10, 2), default=15.0)
    ativo = db.Column(db.Boolean, default=True)
    disponivel = db.Column(db.Boolean, default=True)
    total_entregas = db.Column(db.Integer, default=0)
    data_cadastro = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("veiculos", lazy=True, cascade="all, delete-orphan"))
    motorista = db.relationship("Motorista", backref=db.backref("veiculos", lazy=True))
    __table_args__ = (db.Index("ix_veiculo_placa", "placa"), db.Index("ix_veiculo_tipo", "tipo"),
                      db.UniqueConstraint("estabelecimento_id", "placa", name="uq_veiculo_estab_placa"))

    def to_dict(self):
        return {"id": self.id, "placa": self.placa, "tipo": self.tipo, "marca": self.marca, "modelo": self.modelo,
                "ano": self.ano, "cor": self.cor, "proprietario": self.proprietario,
                "motorista_id": self.motorista_id, "motorista_nome": self.motorista.nome if self.motorista else None,
                "km_atual": float(self.km_atual) if self.km_atual else 0.0,
                "consumo_medio": float(self.consumo_medio) if self.consumo_medio else 15.0,
                "ativo": self.ativo, "disponivel": self.disponivel, "total_entregas": self.total_entregas if hasattr(self, 'total_entregas') else 0}

class TaxaEntrega(db.Model, MultiTenantMixin):
    __tablename__ = "taxas_entrega"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    nome_regiao = db.Column(db.String(100), nullable=False)
    bairros = db.Column(db.Text)
    km_minimo = db.Column(db.Numeric(5, 2), default=0)
    km_maximo = db.Column(db.Numeric(5, 2), default=5)
    taxa_fixa = db.Column(db.Numeric(10, 2), default=0)
    taxa_por_km = db.Column(db.Numeric(10, 2), default=0)
    pedido_minimo = db.Column(db.Numeric(10, 2), default=0)
    taxa_gratis_acima = db.Column(db.Numeric(10, 2))
    tempo_estimado_minutos = db.Column(db.Integer, default=30)
    horario_inicio = db.Column(db.Time)
    horario_fim = db.Column(db.Time)
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("taxas_entrega", lazy=True, cascade="all, delete-orphan"))
    __table_args__ = (db.Index("ix_taxa_regiao", "nome_regiao"),)

    def to_dict(self):
        return {"id": self.id, "nome_regiao": self.nome_regiao, "bairros": json.loads(self.bairros) if self.bairros else [],
                "km_minimo": float(self.km_minimo) if self.km_minimo else 0.0, "km_maximo": float(self.km_maximo) if self.km_maximo else 0.0,
                "taxa_fixa": float(self.taxa_fixa) if self.taxa_fixa else 0.0, "taxa_por_km": float(self.taxa_por_km) if self.taxa_por_km else 0.0,
                "pedido_minimo": float(self.pedido_minimo) if self.pedido_minimo else 0.0,
                "taxa_gratis_acima": float(self.taxa_gratis_acima) if self.taxa_gratis_acima else None,
                "tempo_estimado_minutos": self.tempo_estimado_minutos, "ativo": self.ativo}

class Entrega(db.Model, MultiTenantMixin, SoftDeleteMixin):
    __tablename__ = "entregas"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"))
    motorista_id = db.Column(db.Integer, db.ForeignKey("motoristas.id"))
    veiculo_id = db.Column(db.Integer, db.ForeignKey("veiculos.id"))
    taxa_entrega_id = db.Column(db.Integer, db.ForeignKey("taxas_entrega.id"))
    codigo_rastreamento = db.Column(db.String(20), unique=True)
    endereco_cep = db.Column(db.String(9), nullable=False)
    endereco_logradouro = db.Column(db.String(200), nullable=False)
    endereco_numero = db.Column(db.String(10), nullable=False)
    endereco_complemento = db.Column(db.String(100))
    endereco_bairro = db.Column(db.String(100), nullable=False)
    endereco_cidade = db.Column(db.String(100), nullable=False)
    endereco_estado = db.Column(db.String(2), nullable=False)
    endereco_referencia = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    distancia_km = db.Column(db.Numeric(10, 2), default=0)
    km_percorridos = db.Column(db.Numeric(10, 2), default=0)
    taxa_entrega = db.Column(db.Numeric(10, 2), default=0)
    custo_entrega = db.Column(db.Numeric(10, 2), default=0)
    comissao_motorista = db.Column(db.Numeric(10, 2), default=0)
    custo_combustivel = db.Column(db.Numeric(10, 2), default=0)
    pagamento_tipo = db.Column(db.String(20), default="loja")
    pagamento_status = db.Column(db.String(20), default="pendente")
    status = db.Column(db.String(20), default="pendente")
    data_prevista = db.Column(db.DateTime, nullable=False)
    data_saida = db.Column(db.DateTime)
    data_entrega = db.Column(db.DateTime)
    data_cancelamento = db.Column(db.DateTime)
    motivo_cancelamento = db.Column(db.String(255))
    tempo_estimado_minutos = db.Column(db.Integer, default=30)
    tempo_real_minutos = db.Column(db.Integer)
    observacoes = db.Column(db.Text)
    observacoes_motorista = db.Column(db.Text)
    nota_cliente = db.Column(db.Integer)
    comentario_cliente = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    venda = db.relationship("Venda", backref=db.backref("entrega", uselist=False))
    cliente = db.relationship("Cliente", backref=db.backref("entregas", lazy=True))
    motorista = db.relationship("Motorista", backref=db.backref("entregas", lazy=True))
    veiculo = db.relationship("Veiculo", backref=db.backref("entregas", lazy=True))
    taxa_entrega_ref = db.relationship("TaxaEntrega", backref=db.backref("entregas", lazy=True))
    itens = db.relationship("EntregaItem", backref="entrega", lazy=True, cascade="all, delete-orphan")
    rastreamentos = db.relationship("RastreamentoEntrega", backref="entrega", lazy=True, cascade="all, delete-orphan")
    __table_args__ = (db.Index("ix_entrega_codigo", "codigo_rastreamento"), db.Index("ix_entrega_status", "status"),
                      db.Index("ix_entrega_data_prevista", "data_prevista"), db.Index("ix_entrega_bairro", "endereco_bairro"),
                      db.Index("ix_entrega_motorista", "motorista_id"))

    def to_dict(self):
        return {"id": self.id, "codigo_rastreamento": self.codigo_rastreamento, "venda_id": self.venda_id,
                "cliente_id": self.cliente_id, "cliente_nome": self.cliente.nome if self.cliente else None,
                "motorista_id": self.motorista_id, "motorista_nome": self.motorista.nome if self.motorista else None,
                "veiculo_id": self.veiculo_id, "veiculo_placa": self.veiculo.placa if self.veiculo else None,
                "endereco_completo": f"{self.endereco_logradouro}, {self.endereco_numero} - {self.endereco_bairro} - {self.endereco_cidade}/{self.endereco_estado}",
                "endereco_cep": self.endereco_cep, "endereco_bairro": self.endereco_bairro,
                "distancia_km": float(self.distancia_km) if self.distancia_km else 0.0,
                "km_percorridos": float(self.km_percorridos) if self.km_percorridos else 0.0,
                "taxa_entrega": float(self.taxa_entrega) if self.taxa_entrega else 0.0,
                "custo_entrega": float(self.custo_entrega) if self.custo_entrega else 0.0,
                "custo_combustivel": float(self.custo_combustivel) if self.custo_combustivel else 0.0,
                "status": self.status, "data_prevista": self.data_prevista.isoformat() if self.data_prevista else None,
                "data_saida": self.data_saida.isoformat() if self.data_saida else None,
                "data_entrega": self.data_entrega.isoformat() if self.data_entrega else None,
                "tempo_estimado_minutos": self.tempo_estimado_minutos, "tempo_real_minutos": self.tempo_real_minutos,
                "nota_cliente": self.nota_cliente, "observacoes": self.observacoes}

class EntregaItem(db.Model):
    __tablename__ = "entrega_itens"
    id = db.Column(db.Integer, primary_key=True)
    entrega_id = db.Column(db.Integer, db.ForeignKey("entregas.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    venda_item_id = db.Column(db.Integer, db.ForeignKey("venda_itens.id"))
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    quantidade_entregue = db.Column(db.Numeric(10, 3), default=0)
    status = db.Column(db.String(20), default="pendente")
    observacao = db.Column(db.Text)
    produto = db.relationship("Produto", backref=db.backref("entrega_itens", lazy=True))
    venda_item = db.relationship("VendaItem", backref=db.backref("entrega_item", uselist=False))
    __table_args__ = (db.Index("ix_entrega_item_entrega", "entrega_id"), db.Index("ix_entrega_item_produto", "produto_id"))

    def to_dict(self):
        return {"id": self.id, "entrega_id": self.entrega_id, "produto_id": self.produto_id,
                "produto_nome": self.produto.nome if self.produto else None,
                "quantidade": float(self.quantidade) if self.quantidade else 0.0,
                "quantidade_entregue": float(self.quantidade_entregue) if self.quantidade_entregue else 0.0,
                "status": self.status, "observacao": self.observacao}

class RastreamentoEntrega(db.Model):
    __tablename__ = "rastreamento_entregas"
    id = db.Column(db.Integer, primary_key=True)
    entrega_id = db.Column(db.Integer, db.ForeignKey("entregas.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    observacao = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, default=utcnow)
    foto_url = db.Column(db.String(500))
    assinatura_url = db.Column(db.String(500))
    __table_args__ = (db.Index("ix_rastreamento_entrega", "entrega_id"), db.Index("ix_rastreamento_data", "data_hora"))

    def to_dict(self):
        return {"id": self.id, "entrega_id": self.entrega_id, "status": self.status,
                "latitude": self.latitude, "longitude": self.longitude, "observacao": self.observacao,
                "data_hora": self.data_hora.isoformat() if self.data_hora else None,
                "foto_url": self.foto_url, "assinatura_url": self.assinatura_url}

class CustoEntrega(db.Model, MultiTenantMixin):
    __tablename__ = "custos_entrega"
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = TenantID()
    motorista_id = db.Column(db.Integer, db.ForeignKey("motoristas.id"))
    veiculo_id = db.Column(db.Integer, db.ForeignKey("veiculos.id"))
    tipo = db.Column(db.String(30), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    km_referencia = db.Column(db.Numeric(10, 2))
    data_custo = db.Column(db.Date, nullable=False, default=date.today)
    data_vencimento = db.Column(db.Date)
    data_pagamento = db.Column(db.Date)
    status = db.Column(db.String(20), default="pendente")
    comprovante_url = db.Column(db.String(500))
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    estabelecimento = db.relationship("Estabelecimento", backref=db.backref("custos_entrega", lazy=True))
    motorista = db.relationship("Motorista", backref=db.backref("custos_entrega", lazy=True))
    veiculo = db.relationship("Veiculo", backref=db.backref("custos_entrega", lazy=True))
    __table_args__ = (db.Index("ix_custo_entrega_tipo", "tipo"), db.Index("ix_custo_entrega_data", "data_custo"))

    def to_dict(self):
        return {"id": self.id, "tipo": self.tipo, "descricao": self.descricao,
                "valor": float(self.valor) if self.valor else 0.0,
                "km_referencia": float(self.km_referencia) if self.km_referencia else 0.0,
                "data_custo": self.data_custo.isoformat() if self.data_custo else None,
                "status": self.status, "motorista_id": self.motorista_id,
                "motorista_nome": self.motorista.nome if self.motorista else None,
                "veiculo_id": self.veiculo_id, "observacoes": self.observacoes}

# ------------------------------------------------------------------------------
# Alias e Funções de Suporte
# ------------------------------------------------------------------------------
ItemVenda = VendaItem

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    try: return Funcionario.query.get(int(user_id))
    except: return None

@login_manager.request_loader
def load_user_from_request(request):
    auth = request.headers.get("Authorization")
    if auth:
        try:
            typ, tok = auth.split(None, 1)
            if typ.lower() in ("bearer", "token"):
                user = Funcionario.query.filter_by(username=tok).first()
                if user and user.ativo: return user
        except: pass
    tok = request.args.get("token")
    if tok:
        user = Funcionario.query.filter_by(username=tok).first()
        if user and user.ativo: return user
    return None

def get_model_by_table(table_name: str):
    mapping = {
        "estabelecimentos": Estabelecimento,
        "funcionarios": Funcionario,
        "categorias_produto": CategoriaProduto,
        "fornecedores": Fornecedor,
        "produtos": Produto,
        "produto_lotes": ProdutoLote,
        "movimentacoes_estoque": MovimentacaoEstoque,
        "vendas": Venda,
        "venda_itens": VendaItem,
        "contas_receber": ContaReceber,
        "clientes": Cliente,
        "caixas": Caixa,
        "historico_precos": HistoricoPrecos,
        "configuracoes": Configuracao,
    }
    return mapping.get(table_name)
SyncLog = SyncQueue
AuditoriaSincronia = SyncQueue
