from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class BaseItem(BaseModel):
    id: str  # portal_id:city:raw_id
    portal_id: str
    portal_name: str
    portal_url: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw: dict[str, Any] = Field(default_factory=dict)


class Pedido(BaseItem):
    titulo: str | None = None
    descricao: str | None = None
    categoria: str | None = None
    status: str | None = None
    nome: str | None = None  # nome de quem pediu
    contato: str | None = None  # telefone / whatsapp
    cidade: str | None = None
    bairro: str | None = None
    lat: float | None = None
    lng: float | None = None


class Voluntario(BaseItem):
    nome: str | None = None
    descricao: str | None = None
    categoria: str | None = None
    contato: str | None = None
    cidade: str | None = None
    bairro: str | None = None
    lat: float | None = None
    lng: float | None = None


class PontoAjuda(BaseItem):
    nome: str | None = None
    tipo: str | None = (
        None  # abrigo | coleta | doacao | entidade | abrigo_animal | ponto
    )
    descricao: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    bairro: str | None = None
    lat: float | None = None
    lng: float | None = None
    contato: str | None = None
    horario: str | None = None
    itens: list[str] = Field(default_factory=list)


class Pet(BaseItem):
    tipo: str  # perdido | encontrado | adocao
    nome: str | None = None  # nome do pet
    especie: str | None = None  # cachorro | gato | ...
    porte: str | None = None
    descricao: str | None = None
    status: str | None = None
    contato: str | None = None
    cidade: str | None = None
    bairro: str | None = None
    imagem_url: str | None = None


class FeedItem(BaseItem):
    tipo: str  # alerta | noticia | relatorio | interdicao | transacao
    titulo: str | None = None
    descricao: str | None = None
    url: str | None = None
    data: str | None = None
    urgente: bool = False


class Outro(BaseItem):
    tipo: str  # contato_emergencia | link | pix | saldo | registro
    titulo: str | None = None
    descricao: str | None = None
    url: str | None = None
    contato: str | None = None


class NormalizedResult(BaseModel):
    pedidos: list[Pedido] = Field(default_factory=list)
    voluntarios: list[Voluntario] = Field(default_factory=list)
    pontos: list[PontoAjuda] = Field(default_factory=list)
    pets: list[Pet] = Field(default_factory=list)
    feed: list[FeedItem] = Field(default_factory=list)
    outros: list[Outro] = Field(default_factory=list)
