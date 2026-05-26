from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from actas.auth.models import AccesoUsuarioOrganizacion, RolEnum, Usuario
from actas.auth.schemas import UserOut
from actas.db import get_session
from actas.deps import get_current_user

router = APIRouter(tags=["me"])


class OrgAcceso(BaseModel):
    organizacion_id: str
    rol: RolEnum


class MeOut(BaseModel):
    id: str
    correo: str
    nombre: str
    activo: bool
    organizaciones: list[OrgAcceso]


@router.get("/me", response_model=MeOut)
async def get_me(user: Usuario = Depends(get_current_user)):
    async with get_session() as db:
        result = await db.execute(
            select(AccesoUsuarioOrganizacion).where(AccesoUsuarioOrganizacion.usuario_id == user.id)
        )
        accesos = result.scalars().all()

    return MeOut(
        id=user.id,
        correo=user.correo,
        nombre=user.nombre,
        activo=user.activo,
        organizaciones=[OrgAcceso(organizacion_id=a.organizacion_id, rol=a.rol) for a in accesos],
    )
