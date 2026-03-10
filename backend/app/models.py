import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import EmailStr
from sqlalchemy import ARRAY, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

# para usar no sistema de cron e kpis, para marcar quando os dados foram atualizados pela última vez


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# ---------------------------------------------------------------------------
# Generic
# ---------------------------------------------------------------------------


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


# ---------------------------------------------------------------------------
# Scraped data — base comum (não é tabela)
# ---------------------------------------------------------------------------


class ScrapedItemBase(SQLModel):
    portal_id: str = Field(index=True)
    portal_name: str
    portal_url: str
    scraped_at: datetime = Field(sa_type=DateTime(timezone=True))  # type: ignore
    raw: dict[str, Any] = Field(default_factory=dict, sa_type=JSONB)  # type: ignore
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


# ---------------------------------------------------------------------------
# Pedido
# ---------------------------------------------------------------------------


class Pedido(ScrapedItemBase, table=True):
    id: str = Field(primary_key=True)
    titulo: str | None = None
    descricao: str | None = None
    categoria: str | None = Field(default=None, index=True)
    status: str | None = Field(default=None, index=True)
    nome: str | None = None
    contato: str | None = None
    cidade: str | None = Field(default=None, index=True)
    bairro: str | None = None
    lat: float | None = None
    lng: float | None = None
    data_criacao: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    origem: str | None = None
    categoria_item: str | None = None
    quantidade: int | None = None
    unidade: str | None = None
    urgencia: str | None = None
    ponto_destino: str | None = None


# ---------------------------------------------------------------------------
# Voluntario
# ---------------------------------------------------------------------------


class Voluntario(ScrapedItemBase, table=True):
    id: str = Field(primary_key=True)
    nome: str | None = None
    descricao: str | None = None
    categoria: str | None = Field(default=None, index=True)
    contato: str | None = None
    cidade: str | None = Field(default=None, index=True)
    bairro: str | None = None
    lat: float | None = None
    lng: float | None = None


# ---------------------------------------------------------------------------
# PontoAjuda
# ---------------------------------------------------------------------------


class PontoAjuda(ScrapedItemBase, table=True):
    __tablename__ = "ponto_ajuda"

    id: str = Field(primary_key=True)
    tipo: str | None = Field(default=None, index=True)
    nome: str | None = None
    descricao: str | None = None
    endereco: str | None = None
    cidade: str | None = Field(default=None, index=True)
    bairro: str | None = None
    lat: float | None = None
    lng: float | None = None
    contato: str | None = None
    horario: str | None = None
    itens: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(Text), nullable=False)
    )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------


class Pet(ScrapedItemBase, table=True):
    id: str = Field(primary_key=True)
    tipo: str = Field(index=True)  # perdido | encontrado | adocao
    nome: str | None = None
    especie: str | None = Field(default=None, index=True)
    porte: str | None = None
    descricao: str | None = None
    status: str | None = None
    contato: str | None = None
    cidade: str | None = Field(default=None, index=True)
    bairro: str | None = None
    imagem_url: str | None = None


# ---------------------------------------------------------------------------
# FeedItem
# ---------------------------------------------------------------------------


class FeedItem(ScrapedItemBase, table=True):
    __tablename__ = "feed_item"

    id: str = Field(primary_key=True)
    tipo: str = Field(
        index=True
    )  # alerta | noticia | relatorio | interdicao | vistoria | transacao
    titulo: str | None = None
    descricao: str | None = None
    url: str | None = None
    data: str | None = None
    urgente: bool = Field(default=False, index=True)


# ---------------------------------------------------------------------------
# Outro
# ---------------------------------------------------------------------------


class Outro(ScrapedItemBase, table=True):
    id: str = Field(primary_key=True)
    tipo: str = Field(
        index=True
    )  # contato_emergencia | link | pix | saldo | registro | formulario | vaquinha
    titulo: str | None = None
    descricao: str | None = None
    url: str | None = None
    contato: str | None = None


# ---------------------------------------------------------------------------
# User-submitted data — schemas de input (sem metadados de scraping)
# ---------------------------------------------------------------------------


class PedidoCreate(SQLModel):
    portal_name: str | None = None
    titulo: str | None = None
    descricao: str | None = None
    categoria: str | None = None
    nome: str | None = None
    contato: str | None = None
    cidade: str | None = None
    bairro: str | None = None
    lat: float | None = None
    lng: float | None = None
    data_criacao: datetime | None = Field(default=None)
    origem: str | None = None
    categoria_item: str | None = None
    quantidade: int | None = None
    unidade: str | None = None
    urgencia: str | None = None
    ponto_destino: str | None = None


class PedidoUpdate(PedidoCreate):
    status: str | None = None


class VoluntarioCreate(SQLModel):
    portal_name: str | None = None
    nome: str | None = None
    descricao: str | None = None
    categoria: str | None = None
    contato: str | None = None
    cidade: str | None = None
    bairro: str | None = None
    lat: float | None = None
    lng: float | None = None


class VoluntarioUpdate(VoluntarioCreate):
    pass


class PontoAjudaCreate(SQLModel):
    portal_name: str | None = None
    tipo: str | None = None  # abrigo | coleta | doacao | entidade | abrigo_animal
    nome: str | None = None
    descricao: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    bairro: str | None = None
    lat: float | None = None
    lng: float | None = None
    contato: str | None = None
    horario: str | None = None
    itens: list[str] = Field(default_factory=list)


class PontoAjudaUpdate(PontoAjudaCreate):
    pass


class PetCreate(SQLModel):
    portal_name: str | None = None
    tipo: str  # perdido | encontrado | adocao
    nome: str | None = None
    especie: str | None = None
    porte: str | None = None
    descricao: str | None = None
    contato: str | None = None
    cidade: str | None = None
    bairro: str | None = None
    imagem_url: str | None = None


class PetUpdate(PetCreate):
    tipo: str | None = None  # type: ignore[assignment]


class FeedItemCreate(SQLModel):
    portal_name: str | None = None
    tipo: str  # alerta | noticia | relatorio
    titulo: str | None = None
    descricao: str | None = None
    url: str | None = None
    data: str | None = None
    urgente: bool = False


class FeedItemUpdate(FeedItemCreate):
    tipo: str | None = None  # type: ignore[assignment]
    urgente: bool | None = None  # type: ignore[assignment]


class OutroCreate(SQLModel):
    portal_name: str | None = None
    tipo: str  # contato_emergencia | link | pix | saldo | registro | formulario | vaquinha
    titulo: str | None = None
    descricao: str | None = None
    url: str | None = None
    contato: str | None = None


class OutroUpdate(OutroCreate):
    tipo: str | None = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Evento
# ---------------------------------------------------------------------------


class Evento(ScrapedItemBase, table=True):
    id: str = Field(primary_key=True)
    tipo: str = Field(index=True)  # indicacao_recurso | ...
    destinatario: str = Field(index=True)  # portal que receberá o evento
    status: str = Field(
        default="aberto", index=True
    )  # aberto | em_atendimento | atendido
    metadados: dict[str, Any] = Field(default_factory=dict, sa_type=JSONB)  # type: ignore


class EventoCreate(SQLModel):
    portal_name: str | None = None
    tipo: str
    destinatario: str
    metadados: dict[str, Any] = Field(default_factory=dict)


class EventoUpdate(SQLModel):
    tipo: str | None = None
    destinatario: str | None = None
    status: str | None = None
    metadados: dict[str, Any] | None = None


class EventoList(SQLModel):
    data: list[Evento]
    count: int


# ---------------------------------------------------------------------------
# API Key
# ---------------------------------------------------------------------------


def _slugify(value: str) -> str:
    return value.strip().lower().replace(" ", "-")


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_key"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    slug: str = Field(max_length=255, unique=True, index=True)
    description: str | None = None
    prefix: str = Field(max_length=8, index=True)
    key_hash: str = Field(unique=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    is_active: bool = Field(default=True, index=True)


# ---------------------------------------------------------------------------
# Respostas de listagem tipadas
# ---------------------------------------------------------------------------


class PedidoList(SQLModel):
    data: list[Pedido]
    count: int


class VoluntarioList(SQLModel):
    data: list[Voluntario]
    count: int


class PontoAjudaList(SQLModel):
    data: list[PontoAjuda]
    count: int


class PetList(SQLModel):
    data: list[Pet]
    count: int


class FeedItemList(SQLModel):
    data: list[FeedItem]
    count: int


class OutroList(SQLModel):
    data: list[Outro]
    count: int


# ---------------------------------------------------------------------------
# API Key
# ---------------------------------------------------------------------------


class ApiKeyCreate(SQLModel):
    name: str = Field(max_length=255)
    description: str | None = None


class ApiKeyPublic(SQLModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    prefix: str
    created_at: datetime
    is_active: bool


class ApiKeyCreated(ApiKeyPublic):
    key: str  # plain-text key, shown only once


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------


class KPIHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome_kpi: str
    valor: int
    data_registro: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KPIHistoryPublic(SQLModel):
    nome_kpi: str
    valor: int
    data_registro: datetime


class KPIHistoryList(SQLModel):
    data: list[KPIHistoryPublic]
    count: int


# ---------------------------------------------------------------------------
# Solicitação (robô WhatsApp)
# ---------------------------------------------------------------------------

IncidentPriority = Literal["CRITICA", "ALTA", "MEDIA", "BAIXA"]

EmergencyService = Literal[
    "Defesa Civil",
    "Direitos Humanos",
    "Desenvolvimento Social",
    "Assistência Social",
    "EMCASA",
    "Defesa Animal",
    "Canil Municipal",
    "Procon",
    "Secretaria de Comunicação",
]


class Solicitacao(SQLModel, table=True):
    __tablename__ = "solicitacao"

    uid: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    portal_id: str = Field(index=True)
    portal_name: str
    categoria: str
    prioridade: str = Field(index=True)  # CRITICA | ALTA | MEDIA | BAIXA
    bairro: str
    orgao_responsavel: str = Field(index=True)
    descricao_resumida: str
    pessoas_afetadas: int = Field(default=0)
    animais_afetados: int = Field(default=0)
    risco_imediato: bool = Field(default=False, index=True)
    protocolo_atendimento: str
    media_hash: str | None = None
    endereco_completo: str
    metadados: dict[str, Any] = Field(default_factory=dict, sa_type=JSONB)  # type: ignore
    criado_em: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class SolicitacaoCreate(SQLModel):
    categoria: str
    prioridade: IncidentPriority
    bairro: str
    orgao_responsavel: EmergencyService
    descricao_resumida: str
    pessoas_afetadas: int = 0
    animais_afetados: int = 0
    risco_imediato: bool = False
    protocolo_atendimento: str
    media_hash: str | None = None
    endereco_completo: str
    metadados: dict[str, Any] = Field(default_factory=dict)


class SolicitacaoList(SQLModel):
    data: list[Solicitacao]
    count: int
