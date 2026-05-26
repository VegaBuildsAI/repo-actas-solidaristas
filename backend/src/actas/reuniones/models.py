"""SQLAlchemy models for reunion, grabacion, transcripcion, segmento_transcripcion."""

from __future__ import annotations

import enum
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from actas.db import Base


class ReunionEstadoEnum(str, enum.Enum):
    programada = "programada"
    procesando = "procesando"
    en_revision = "en_revision"
    aprobada = "aprobada"


class Reunion(Base):
    __tablename__ = "reunion"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    organizacion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizacion.id"), nullable=False
    )
    organo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organo.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_fin: Mapped[time | None] = mapped_column(Time, nullable=True)
    modalidad: Mapped[str | None] = mapped_column(String, nullable=True)
    numero_acta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[ReunionEstadoEnum] = mapped_column(
        Enum(ReunionEstadoEnum, name="reunion_estado_enum"),
        nullable=False,
        default=ReunionEstadoEnum.programada,
        server_default="programada",
    )
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    grabaciones: Mapped[list["Grabacion"]] = relationship(back_populates="reunion")
    transcripciones: Mapped[list["Transcripcion"]] = relationship(back_populates="reunion")


class Grabacion(Base):
    __tablename__ = "grabacion"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    reunion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("reunion.id", ondelete="CASCADE"), nullable=False
    )
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    duracion_segundos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    subido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    borrado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reunion: Mapped["Reunion"] = relationship(back_populates="grabaciones")


class Transcripcion(Base):
    __tablename__ = "transcripcion"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    reunion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("reunion.id", ondelete="CASCADE"), nullable=False
    )
    texto_plano: Mapped[str] = mapped_column(Text, nullable=False)
    modelo: Mapped[str] = mapped_column(String, nullable=False)
    generada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    reunion: Mapped["Reunion"] = relationship(back_populates="transcripciones")
    segmentos: Mapped[list["SegmentoTranscripcion"]] = relationship(
        back_populates="transcripcion"
    )


class SegmentoTranscripcion(Base):
    __tablename__ = "segmento_transcripcion"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    transcripcion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("transcripcion.id", ondelete="CASCADE"),
        nullable=False,
    )
    inicio_seg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    fin_seg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    hablante_etiqueta: Mapped[str] = mapped_column(String, nullable=False)
    miembro_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("miembro.id"), nullable=True
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    confianza: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)

    transcripcion: Mapped["Transcripcion"] = relationship(back_populates="segmentos")
