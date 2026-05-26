"""
Transcription service using faster-whisper (F1-01 / F1-04).

faster-whisper is a CTranslate2-based reimplementation of OpenAI Whisper.
It runs efficiently on CPU and GPU; in dev we default to CPU + int8 quantization.

Model sizes and approx. disk usage:
  tiny    (~75 MB)  — fast, lower accuracy
  base    (~145 MB) — good for development / testing
  small   (~465 MB) — reasonable quality
  large-v3 (~1.5 GB) — production quality per the spec

The model is downloaded from HuggingFace Hub on first use and cached under
$HF_HOME (set to /model-cache in the worker Dockerfile, backed by a Docker volume).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class TranscriptSegment:
    inicio_seg: Decimal
    fin_seg: Decimal
    texto: str
    hablante_etiqueta: str = "Hablante 1"
    confianza: Decimal | None = None


@dataclass
class TranscriptResult:
    texto_plano: str          # Full transcript as one string
    modelo: str               # E.g. "whisper-base"
    segmentos: list[TranscriptSegment]
    idioma_detectado: str
    duracion_seg: float


# ── Model singleton ───────────────────────────────────────────────────────────

_model = None
_model_name: str | None = None


def _get_model(model_name: str):
    global _model, _model_name

    if _model is not None and _model_name == model_name:
        return _model

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper no está instalado. Ejecuta: pip install faster-whisper"
        ) from exc

    device = os.getenv("WHISPER_DEVICE", "cpu")
    # int8 quantization works on CPU with good speed; use float16 on GPU
    compute_type = "int8" if device == "cpu" else "float16"

    logger.info(
        "Cargando modelo Whisper '%s' en %s (%s)...", model_name, device, compute_type
    )
    _model = WhisperModel(model_name, device=device, compute_type=compute_type)
    _model_name = model_name
    logger.info("Modelo Whisper listo.")
    return _model


# ── Public API ────────────────────────────────────────────────────────────────

def transcribe_audio(
    audio_path: str,
    model_name: str | None = None,
    language: str = "es",
    beam_size: int = 5,
    vad_filter: bool = True,
) -> TranscriptResult:
    """
    Transcribe an audio file with faster-whisper.

    Args:
        audio_path: Path to the audio file (WAV, MP3, MP4, OGG, FLAC, …)
        model_name: Whisper model to use. Defaults to WHISPER_MODEL env var, then 'base'.
        language: Language code. Default 'es' (Spanish).
        beam_size: Beam search width. Higher = better quality, slower.
        vad_filter: Skip silent segments (faster, slightly less accurate).

    Returns:
        TranscriptResult with segments and plain text.
    """
    if model_name is None:
        model_name = os.getenv("WHISPER_MODEL", "base")

    model = _get_model(model_name)

    logger.info("Transcribiendo %s con modelo '%s'...", audio_path, model_name)

    segments_gen, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
        word_timestamps=False,
    )

    # Materialise the generator (segments are lazy)
    raw_segments = list(segments_gen)

    logger.info(
        "Transcripción completada: idioma=%s (prob=%.2f), duración=%.1fs, %d segmentos",
        info.language,
        info.language_probability,
        info.duration,
        len(raw_segments),
    )

    transcript_segments: list[TranscriptSegment] = []
    texts: list[str] = []

    for seg in raw_segments:
        text = seg.text.strip()
        if not text:
            continue

        # avg_logprob is in log-space; convert to a 0-1 confidence approximation
        import math
        confianza = Decimal(str(round(min(1.0, math.exp(seg.avg_logprob)), 4)))

        transcript_segments.append(
            TranscriptSegment(
                inicio_seg=Decimal(str(round(seg.start, 3))),
                fin_seg=Decimal(str(round(seg.end, 3))),
                texto=text,
                hablante_etiqueta="Hablante 1",  # updated by diarize.py in F1-05
                confianza=confianza,
            )
        )
        texts.append(text)

    texto_plano = " ".join(texts)

    return TranscriptResult(
        texto_plano=texto_plano,
        modelo=f"whisper-{model_name}",
        segmentos=transcript_segments,
        idioma_detectado=info.language,
        duracion_seg=info.duration,
    )
