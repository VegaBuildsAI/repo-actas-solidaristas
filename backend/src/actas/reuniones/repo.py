"""Async CRUD operations for Reunion and Grabacion."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from actas.reuniones.models import (
    Grabacion,
    Reunion,
    ReunionEstadoEnum,
    SegmentoTranscripcion,
    Transcripcion,
)
from actas.reuniones.schemas import ReunionCreate


async def create_reunion(
    db: AsyncSession, org_id: str, data: ReunionCreate
) -> Reunion:
    reunion = Reunion(
        organizacion_id=org_id,
        organo_id=data.organo_id,
        tipo=data.tipo,
        fecha=data.fecha,
        hora_inicio=data.hora_inicio,
        hora_fin=data.hora_fin,
        modalidad=data.modalidad,
        numero_acta=data.numero_acta,
    )
    db.add(reunion)
    await db.flush()
    await db.refresh(reunion)
    return reunion


async def get_reunion(db: AsyncSession, reunion_id: str) -> Reunion | None:
    result = await db.execute(
        select(Reunion)
        .where(Reunion.id == reunion_id)
        .options(
            selectinload(Reunion.grabaciones),
            selectinload(Reunion.transcripciones).selectinload(Transcripcion.segmentos),
        )
    )
    return result.scalar_one_or_none()


async def list_reuniones(
    db: AsyncSession,
    org_id: str,
    organo_id: str | None = None,
    estado: ReunionEstadoEnum | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Reunion]:
    q = select(Reunion).where(Reunion.organizacion_id == org_id)
    if organo_id:
        q = q.where(Reunion.organo_id == organo_id)
    if estado:
        q = q.where(Reunion.estado == estado)
    q = q.order_by(Reunion.fecha.desc(), Reunion.creada_en.desc())
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_reunion_estado(
    db: AsyncSession, reunion_id: str, estado: ReunionEstadoEnum
) -> Reunion | None:
    reunion = await db.get(Reunion, reunion_id)
    if reunion:
        reunion.estado = estado
        await db.flush()
    return reunion


async def create_grabacion(
    db: AsyncSession,
    reunion_id: str,
    storage_uri: str,
    file_bytes: int | None = None,
) -> Grabacion:
    grabacion = Grabacion(
        reunion_id=reunion_id,
        storage_uri=storage_uri,
        bytes=file_bytes,
    )
    db.add(grabacion)
    await db.flush()
    await db.refresh(grabacion)
    return grabacion


async def create_transcripcion(
    db: AsyncSession,
    reunion_id: str,
    texto_plano: str,
    modelo: str,
    segmentos: list[dict],
) -> Transcripcion:
    transcripcion = Transcripcion(
        reunion_id=reunion_id,
        texto_plano=texto_plano,
        modelo=modelo,
    )
    db.add(transcripcion)
    await db.flush()

    for seg in segmentos:
        db.add(
            SegmentoTranscripcion(
                transcripcion_id=transcripcion.id,
                inicio_seg=seg["inicio_seg"],
                fin_seg=seg["fin_seg"],
                hablante_etiqueta=seg.get("hablante_etiqueta", "Hablante 1"),
                texto=seg["texto"],
                confianza=seg.get("confianza"),
            )
        )

    await db.flush()
    await db.refresh(transcripcion)
    return transcripcion
