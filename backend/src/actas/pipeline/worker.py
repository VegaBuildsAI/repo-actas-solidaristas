"""
RQ worker job: procesar_reunion (F1-03).

This is the entry point for the async AI pipeline.
Each step is isolated and failures update reunion.estado accordingly.

Current implementation (Fase 1):
  1. Download audio from MinIO
  2. Transcribe with faster-whisper
  3. Save Transcripcion + SegmentoTranscripcion to DB
  4. Update reunion.estado → en_revision

Future steps (plugged in as they're built):
  F1-05  diarize.py  — speaker diarization (WhisperX + pyannote)
  F1-06  rag.py      — retrieve context chunks from pgvector
  F1-07  generate.py — LLM document generation (Claude API)
  F1-09  extract_acuerdos.py — structured acuerdo extraction
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

# Ensure all models are registered in SQLAlchemy metadata before any DB access.
# This resolves FK string references (e.g. ForeignKey("miembro.id")).
import actas.models_all  # noqa: F401, E402


# ── Public RQ entry point ─────────────────────────────────────────────────────

def procesar_reunion(reunion_id: str) -> dict:
    """
    RQ job: process a reunión from stored audio to transcribed text.
    Called as: q.enqueue('actas.pipeline.worker.procesar_reunion', reunion_id)
    """
    logger.info("[worker] Iniciando procesamiento de reunión %s", reunion_id)
    result = asyncio.run(_run(reunion_id))
    logger.info("[worker] Procesamiento completado: %s", result)
    return result


# ── Async pipeline ────────────────────────────────────────────────────────────

async def _run(reunion_id: str) -> dict:
    from actas.db import get_session, set_tenant
    from actas.reuniones import repo
    from actas.reuniones.models import ReunionEstadoEnum
    from actas.storage.client import get_storage

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from actas.reuniones.models import Grabacion, Reunion

    # ── Step 0: Load reunion + grabacion ──────────────────────────────────────

    async with get_session() as db:
        async with db.begin():
            result = await db.execute(
                select(Reunion)
                .where(Reunion.id == reunion_id)
                .options(selectinload(Reunion.grabaciones))
            )
            reunion = result.scalar_one_or_none()

    if reunion is None:
        raise ValueError(f"Reunión {reunion_id} no encontrada")

    if not reunion.grabaciones:
        raise ValueError(f"Reunión {reunion_id} no tiene grabación")

    grabacion = reunion.grabaciones[0]
    org_id = reunion.organizacion_id

    # ── Step 1: Download audio ────────────────────────────────────────────────
    storage = get_storage()
    key = storage.uri_to_key(grabacion.storage_uri)
    ext = key.rsplit(".", 1)[-1] if "." in key else "audio"

    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        logger.info("[worker] Descargando audio: %s → %s", grabacion.storage_uri, tmp_path)
        storage.download_file(key, tmp_path)
        file_size = os.path.getsize(tmp_path)
        logger.info("[worker] Audio descargado: %.1f MB", file_size / 1024 / 1024)

        # ── Step 2: Transcribe ────────────────────────────────────────────────
        from actas.pipeline.transcribe import transcribe_audio

        transcript = transcribe_audio(tmp_path)
        logger.info(
            "[worker] Transcripción lista: %d segmentos, idioma=%s, duración=%.1fs",
            len(transcript.segmentos),
            transcript.idioma_detectado,
            transcript.duracion_seg,
        )

        # ── Step 3: Save to DB ────────────────────────────────────────────────
        segmentos_data = [
            {
                "inicio_seg": seg.inicio_seg,
                "fin_seg": seg.fin_seg,
                "hablante_etiqueta": seg.hablante_etiqueta,
                "texto": seg.texto,
                "confianza": seg.confianza,
            }
            for seg in transcript.segmentos
        ]

        async with get_session() as db:
            async with db.begin():
                await set_tenant(db, org_id)
                saved = await repo.create_transcripcion(
                    db,
                    reunion_id=reunion_id,
                    texto_plano=transcript.texto_plano,
                    modelo=transcript.modelo,
                    segmentos=segmentos_data,
                )
                # Update grabacion duration if available
                if transcript.duracion_seg:
                    from sqlalchemy import update as sql_update
                    from actas.reuniones.models import Grabacion
                    await db.execute(
                        sql_update(Grabacion)
                        .where(Grabacion.id == grabacion.id)
                        .values(duracion_segundos=int(transcript.duracion_seg))
                    )
                await repo.update_reunion_estado(
                    db, reunion_id, ReunionEstadoEnum.en_revision
                )

        logger.info(
            "[worker] Transcripción guardada (id=%s). Estado → en_revision.", saved.id
        )

        return {
            "reunion_id": reunion_id,
            "transcripcion_id": saved.id,
            "segmentos": len(transcript.segmentos),
            "idioma": transcript.idioma_detectado,
            "duracion_seg": transcript.duracion_seg,
            "estado": "en_revision",
        }

    except Exception as exc:
        logger.exception("[worker] Error procesando reunión %s", reunion_id)
        # Try to mark the reunion with an error-readable state
        try:
            async with get_session() as db:
                async with db.begin():
                    await set_tenant(db, org_id)
                    await repo.update_reunion_estado(
                        db, reunion_id, ReunionEstadoEnum.procesando
                    )
        except Exception:
            pass  # Don't shadow the original exception
        raise

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
