"""
Speaker diarization using WhisperX + pyannote.audio (F1-05).

Stub — will be implemented in F1-05.
Requires: pip install whisperx  (installs torch + pyannote.audio)
Requires: HUGGINGFACE_TOKEN env var (accept pyannote terms at huggingface.co)
"""

from __future__ import annotations

import logging

from actas.pipeline.transcribe import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


def diarize(transcript: TranscriptResult, audio_path: str) -> TranscriptResult:
    """
    Assign speaker labels to each segment (F1-05, not yet implemented).

    Currently returns the transcript unchanged with 'Hablante 1' labels.
    Once F1-05 is implemented this will use pyannote.audio to identify
    'Hablante 1', 'Hablante 2', etc. and optionally map them to Miembro records.
    """
    logger.info("Diarización no implementada aún (F1-05) — retornando segmentos sin cambios.")
    return transcript
