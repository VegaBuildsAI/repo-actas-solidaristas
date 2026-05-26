import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from actas.db import Base


class TipoOrganoEnum(str, enum.Enum):
    junta_directiva = "junta_directiva"
    comite = "comite"


class Organizacion(Base):
    __tablename__ = "organizacion"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    sigla: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    afiliados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organos: Mapped[list["Organo"]] = relationship(back_populates="organizacion")


class Organo(Base):
    __tablename__ = "organo"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    organizacion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizacion.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[TipoOrganoEnum] = mapped_column(
        Enum(TipoOrganoEnum, name="tipo_organo_enum"), nullable=False
    )

    organizacion: Mapped["Organizacion"] = relationship(back_populates="organos")
    miembros: Mapped[list["Miembro"]] = relationship(back_populates="organo")


class Miembro(Base):
    __tablename__ = "miembro"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    organo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organo.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    cargo: Mapped[str] = mapped_column(String, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organo: Mapped["Organo"] = relationship(back_populates="miembros")
