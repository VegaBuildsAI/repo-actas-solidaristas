import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from actas.db import Base


class RolEnum(str, enum.Enum):
    administrador = "administrador"
    operario = "operario"


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    correo: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    hash_password: Mapped[str] = mapped_column(String, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    accesos: Mapped[list["AccesoUsuarioOrganizacion"]] = relationship(back_populates="usuario")


class AccesoUsuarioOrganizacion(Base):
    __tablename__ = "acceso_usuario_organizacion"

    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True
    )
    organizacion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizacion.id", ondelete="CASCADE"), primary_key=True
    )
    rol: Mapped[RolEnum] = mapped_column(Enum(RolEnum, name="rol_enum"), nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="accesos")
