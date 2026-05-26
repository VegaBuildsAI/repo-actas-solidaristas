"""
LLM document generation using Anthropic Claude (F1-07 / F1-08).

Stub — will be implemented in F1-07 once DPA is signed and the legal
template from Bonsai is available for RAG indexing (F1-06).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def generate_documentos(
    transcripcion_texto: str,
    contexto_rag: list[str],
    organo: dict,
    miembros: list[dict],
) -> dict:
    """
    Generate resumen, acta (structured JSON), and minuta using the Claude API.
    (F1-07/F1-08 — not yet implemented)
    """
    logger.info("Generación LLM no implementada aún (F1-07/F1-08)")
    return {
        "resumen": {},
        "acta": {"acuerdos": []},
        "minuta": {},
    }
