"""Pydantic schemas for reuniones (snake_case on the wire)."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from actas.reuniones.models import ReunionEstadoEnum


# ── Reunion ───────────────────────────────────────────────────────────────────

class ReunionCreate(BaseModel):
    organo_id: str
    tipo: str
    fecha: date
    hora_inicio: time | None = None
    hora_fin: time | None = None
    modalidad: str | None = None
    numero_acta: int | None = None


class ReunionUpdate(BaseModel):
    tipo: str | None = None
    fecha: date | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    modalidad: str | None = None
    numero_acta: int | None = None


class ReunionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organizacion_id: str
    organo_id: str
    tipo: str
    fecha: date
    hora_inicio: time | None
    hora_fin: time | None
    modalidad: str | None
    numero_acta: int | None
    estado: ReunionEstadoEnum
    creada_en: datetime


# ── Grabacion ─────────────────────────────────────────────────────────────────

class GrabacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reunion_id: str
    storage_uri: str
    duracion_segundos: int | None
    bytes: int | None
    subido_en: datetime


# ── Transcripcion ─────────────────────────────────────────────────────────────

class SegmentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    inicio_seg: Decimal
    fin_seg: Decimal
    hablante_etiqueta: str
    miembro_id: str | None
    texto: str
    confianza: Decimal | None


class TranscripcionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reunion_id: str
    texto_plano: str
    modelo: str
    generada_en: datetime
    segmentos: list[SegmentoOut] = []


# ── Detail (with related data) ────────────────────────────────────────────────

class ReunionDetail(ReunionOut):
    grabacion: GrabacionOut | None = None
    transcripcion: TranscripcionOut | None = None
