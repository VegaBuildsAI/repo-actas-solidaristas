from datetime import datetime

from pydantic import BaseModel

from actas.organizaciones.models import TipoOrganoEnum


class OrganizacionOut(BaseModel):
    id: str
    sigla: str
    nombre: str
    afiliados: int | None
    activa: bool
    creada_en: datetime

    model_config = {"from_attributes": True}


class OrganizacionCreate(BaseModel):
    sigla: str
    nombre: str
    afiliados: int | None = None


class OrganoOut(BaseModel):
    id: str
    organizacion_id: str
    nombre: str
    tipo: TipoOrganoEnum

    model_config = {"from_attributes": True}


class OrganoCreate(BaseModel):
    nombre: str
    tipo: TipoOrganoEnum
