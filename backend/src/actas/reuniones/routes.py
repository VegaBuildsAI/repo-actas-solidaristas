"""FastAPI routes for reuniones (F1-02: grabacion upload, F1-03: enqueue worker)."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from actas.auth.models import Usuario
from actas.db import get_session, set_tenant
from actas.deps import get_current_user
from actas.reuniones import repo
from actas.reuniones.models import ReunionEstadoEnum
from actas.reuniones.schemas import GrabacionOut, ReunionCreate, ReunionDetail, ReunionOut
from actas.storage.client import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reuniones", tags=["reuniones"])

# ── Helpers ───────────────────────────────────────────────────────────────────

_ALLOWED_AUDIO_TYPES = {
    "audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/webm",
    "audio/x-wav", "audio/x-m4a", "audio/aac", "audio/flac",
    "video/mp4",  # Teams exports are often mp4
    "application/octet-stream",  # generic fallback
}

_MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB


def _get_org_id(request: Request) -> str:
    org_id: str | None = getattr(request.state, "org_id", None)
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cabecera X-Organization-Id requerida",
        )
    return org_id


async def _get_db_with_tenant(request: Request) -> AsyncSession:
    """Get a DB session scoped to the request's organization (RLS)."""
    org_id = _get_org_id(request)
    async with get_session() as db:
        async with db.begin():
            await set_tenant(db, org_id)
            yield db


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ReunionOut, status_code=status.HTTP_201_CREATED)
async def create_reunion(
    request: Request,
    body: ReunionCreate,
    user: Usuario = Depends(get_current_user),
) -> ReunionOut:
    org_id = _get_org_id(request)
    async with get_session() as db:
        async with db.begin():
            await set_tenant(db, org_id)
            reunion = await repo.create_reunion(db, org_id, body)
    return ReunionOut.model_validate(reunion)


@router.get("", response_model=list[ReunionOut])
async def list_reuniones(
    request: Request,
    organo_id: str | None = None,
    estado: ReunionEstadoEnum | None = None,
    limit: int = 50,
    offset: int = 0,
    user: Usuario = Depends(get_current_user),
) -> list[ReunionOut]:
    org_id = _get_org_id(request)
    async with get_session() as db:
        async with db.begin():
            await set_tenant(db, org_id)
            items = await repo.list_reuniones(
                db, org_id, organo_id=organo_id, estado=estado,
                limit=limit, offset=offset
            )
    return [ReunionOut.model_validate(r) for r in items]


@router.get("/{reunion_id}", response_model=ReunionDetail)
async def get_reunion(
    request: Request,
    reunion_id: str,
    user: Usuario = Depends(get_current_user),
) -> ReunionDetail:
    org_id = _get_org_id(request)
    async with get_session() as db:
        async with db.begin():
            await set_tenant(db, org_id)
            reunion = await repo.get_reunion(db, reunion_id)

    if not reunion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunión no encontrada")

    # Build detail response
    grabacion = reunion.grabaciones[0] if reunion.grabaciones else None
    transcripcion = reunion.transcripciones[0] if reunion.transcripciones else None

    detail = ReunionDetail(
        **ReunionOut.model_validate(reunion).model_dump(),
        grabacion=GrabacionOut.model_validate(grabacion) if grabacion else None,
        transcripcion=None,  # TODO: add transcripcion schema when loading detail
    )
    return detail


@router.post("/{reunion_id}/grabacion", response_model=GrabacionOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_grabacion(
    request: Request,
    reunion_id: str,
    audio: UploadFile = File(...),
    user: Usuario = Depends(get_current_user),
) -> GrabacionOut:
    """
    Sube el audio de una reunión a MinIO y encola el pipeline de procesamiento.

    - Acepta: mp3, mp4, wav, ogg, webm, aac, flac (hasta 500 MB)
    - Responde 202 Accepted con la grabación creada
    - El worker procesa de forma asíncrona: transcripción → estado 'en_revision'
    """
    org_id = _get_org_id(request)

    # Validate content type
    content_type = audio.content_type or "application/octet-stream"
    if content_type not in _ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de archivo no soportado: {content_type}. "
                   "Use MP3, MP4, WAV, OGG, WebM, AAC o FLAC.",
        )

    # Validate reunion exists and belongs to org
    async with get_session() as db:
        async with db.begin():
            await set_tenant(db, org_id)
            reunion = await repo.get_reunion(db, reunion_id)

    if not reunion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunión no encontrada")

    if reunion.organizacion_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso")

    if reunion.estado not in (ReunionEstadoEnum.programada, ReunionEstadoEnum.procesando):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede subir grabación en estado '{reunion.estado}'",
        )

    # Build S3 key
    ext = (audio.filename or "audio").rsplit(".", 1)[-1].lower()
    key = f"{org_id}/audio/{reunion_id}/{uuid.uuid4()}.{ext}"

    # Upload to MinIO
    storage = get_storage()
    try:
        storage.ensure_bucket()
        file_data = await audio.read()
        file_bytes = len(file_data)

        if file_bytes > _MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande ({file_bytes // 1024 // 1024} MB). Máximo 500 MB.",
            )

        import io
        storage_uri = storage.upload_fileobj(
            io.BytesIO(file_data), key, content_type=content_type
        )
        logger.info("Audio subido: %s (%d bytes)", storage_uri, file_bytes)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error subiendo audio a MinIO")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error subiendo archivo: {exc}",
        ) from exc

    # Save grabacion record + update estado
    async with get_session() as db:
        async with db.begin():
            await set_tenant(db, org_id)
            grabacion = await repo.create_grabacion(
                db, reunion_id, storage_uri, file_bytes=file_bytes
            )
            await repo.update_reunion_estado(db, reunion_id, ReunionEstadoEnum.procesando)

    # Enqueue RQ job
    try:
        import redis
        from rq import Queue

        from actas.settings import get_settings
        settings = get_settings()

        r = redis.from_url(settings.REDIS_URL)
        q = Queue("actas", connection=r)
        job = q.enqueue(
            "actas.pipeline.worker.procesar_reunion",
            reunion_id,
            job_timeout=3600,  # 1 hour max
            result_ttl=86400,  # keep result 24h
        )
        logger.info("Job encolado: %s para reunión %s", job.id, reunion_id)

    except Exception as exc:
        # Don't fail the upload if Redis is momentarily unavailable — log and continue
        logger.warning("No se pudo encolar el job (Redis?): %s", exc)

    return GrabacionOut.model_validate(grabacion)
