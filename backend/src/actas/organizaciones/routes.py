from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from actas.auth.models import Usuario
from actas.db import get_session, set_tenant
from actas.deps import get_current_user
from actas.organizaciones import repo
from actas.organizaciones.schemas import OrganoCreate, OrganoOut, OrganizacionCreate, OrganizacionOut

router = APIRouter(prefix="/organizaciones", tags=["organizaciones"])


async def _db():
    async with get_session() as s:
        yield s


@router.get("", response_model=list[OrganizacionOut])
async def list_organizaciones(
    db: AsyncSession = Depends(_db),
    user: Usuario = Depends(get_current_user),
):
    return await repo.list_organizaciones(db, user.id)


@router.post("", response_model=OrganizacionOut, status_code=status.HTTP_201_CREATED)
async def create_organizacion(
    body: OrganizacionCreate,
    db: AsyncSession = Depends(_db),
    user: Usuario = Depends(get_current_user),
):
    from actas.auth.models import RolEnum, AccesoUsuarioOrganizacion

    async with db.begin():
        org = await repo.create_organizacion(db, body.sigla, body.nombre, body.afiliados)
        acceso = AccesoUsuarioOrganizacion(
            usuario_id=user.id, organizacion_id=org.id, rol=RolEnum.administrador
        )
        db.add(acceso)
    return org


@router.get("/{org_id}", response_model=OrganizacionOut)
async def get_organizacion(
    org_id: str,
    db: AsyncSession = Depends(_db),
    user: Usuario = Depends(get_current_user),
):
    org = await repo.get_organizacion(db, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organización no encontrada")
    return org


@router.get("/{org_id}/organos", response_model=list[OrganoOut])
async def list_organos(
    org_id: str,
    db: AsyncSession = Depends(_db),
    user: Usuario = Depends(get_current_user),
):
    return await repo.list_organos(db, org_id)


@router.post("/{org_id}/organos", response_model=OrganoOut, status_code=status.HTTP_201_CREATED)
async def create_organo(
    org_id: str,
    body: OrganoCreate,
    db: AsyncSession = Depends(_db),
    user: Usuario = Depends(get_current_user),
):
    async with db.begin():
        organo = await repo.create_organo(db, org_id, body.nombre, body.tipo)
    return organo
