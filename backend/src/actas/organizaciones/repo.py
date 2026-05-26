from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from actas.organizaciones.models import Organo, Organizacion


async def list_organizaciones(db: AsyncSession, user_id: str) -> list[Organizacion]:
    from actas.auth.models import AccesoUsuarioOrganizacion

    result = await db.execute(
        select(Organizacion)
        .join(AccesoUsuarioOrganizacion, AccesoUsuarioOrganizacion.organizacion_id == Organizacion.id)
        .where(AccesoUsuarioOrganizacion.usuario_id == user_id)
        .where(Organizacion.activa.is_(True))
        .order_by(Organizacion.sigla)
    )
    return list(result.scalars().all())


async def get_organizacion(db: AsyncSession, org_id: str) -> Organizacion | None:
    result = await db.execute(select(Organizacion).where(Organizacion.id == org_id))
    return result.scalar_one_or_none()


async def create_organizacion(db: AsyncSession, sigla: str, nombre: str, afiliados: int | None) -> Organizacion:
    org = Organizacion(sigla=sigla, nombre=nombre, afiliados=afiliados)
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org


async def list_organos(db: AsyncSession, org_id: str) -> list[Organo]:
    result = await db.execute(
        select(Organo).where(Organo.organizacion_id == org_id).order_by(Organo.nombre)
    )
    return list(result.scalars().all())


async def create_organo(db: AsyncSession, org_id: str, nombre: str, tipo: str) -> Organo:
    organo = Organo(organizacion_id=org_id, nombre=nombre, tipo=tipo)
    db.add(organo)
    await db.flush()
    await db.refresh(organo)
    return organo
