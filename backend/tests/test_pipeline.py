"""Unit tests for the transcription pipeline (F1-01).

These tests mock faster-whisper so they run in CI without GPU/model download.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from actas.pipeline.transcribe import TranscriptResult, TranscriptSegment, transcribe_audio


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_segment(start: float, end: float, text: str, avg_logprob: float = -0.3):
    """Create a mock faster-whisper Segment."""
    seg = MagicMock()
    seg.start = start
    seg.end = end
    seg.text = text
    seg.avg_logprob = avg_logprob
    seg.no_speech_prob = 0.05
    seg.compression_ratio = 1.2
    return seg


def _mock_model(segments: list, language: str = "es", duration: float = 60.0):
    """Create a mock WhisperModel whose .transcribe() returns given segments."""
    info = MagicMock()
    info.language = language
    info.language_probability = 0.99
    info.duration = duration

    model = MagicMock()
    model.transcribe.return_value = (iter(segments), info)
    return model


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestTranscribeAudio:
    def test_returns_transcript_result(self, tmp_path):
        """transcribe_audio returns a TranscriptResult."""
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"\x00" * 100)  # fake audio file

        segs = [
            _make_segment(0.0, 3.5, " Buenos días a todos."),
            _make_segment(3.5, 7.0, " Iniciamos la sesión ordinaria."),
        ]
        mock_model = _mock_model(segs, language="es", duration=7.0)

        with patch("actas.pipeline.transcribe._get_model", return_value=mock_model):
            result = transcribe_audio(str(audio))

        assert isinstance(result, TranscriptResult)
        assert result.idioma_detectado == "es"
        assert result.duracion_seg == pytest.approx(7.0)
        assert len(result.segmentos) == 2

    def test_plain_text_joins_segments(self, tmp_path):
        """texto_plano is a space-joined concat of all segment texts."""
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"\x00" * 100)

        segs = [
            _make_segment(0.0, 2.0, " Hola,"),
            _make_segment(2.0, 4.0, " mundo."),
        ]
        mock_model = _mock_model(segs)

        with patch("actas.pipeline.transcribe._get_model", return_value=mock_model):
            result = transcribe_audio(str(audio))

        assert result.texto_plano == "Hola, mundo."

    def test_segment_timestamps_are_decimal(self, tmp_path):
        """Segment timestamps are stored as Decimal for DB precision."""
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"\x00" * 100)

        segs = [_make_segment(1.123, 5.678, " Test")]
        mock_model = _mock_model(segs)

        with patch("actas.pipeline.transcribe._get_model", return_value=mock_model):
            result = transcribe_audio(str(audio))

        seg = result.segmentos[0]
        assert isinstance(seg.inicio_seg, Decimal)
        assert isinstance(seg.fin_seg, Decimal)
        assert seg.inicio_seg == Decimal("1.123")
        assert seg.fin_seg == Decimal("5.678")

    def test_confidence_is_normalized(self, tmp_path):
        """Confidence is in [0, 1] regardless of log-prob value."""
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"\x00" * 100)

        # avg_logprob = 0.0 → confidence = exp(0) = 1.0
        segs = [_make_segment(0.0, 1.0, " Test", avg_logprob=0.0)]
        mock_model = _mock_model(segs)

        with patch("actas.pipeline.transcribe._get_model", return_value=mock_model):
            result = transcribe_audio(str(audio))

        conf = float(result.segmentos[0].confianza)
        assert 0.0 <= conf <= 1.0

    def test_empty_segments_are_skipped(self, tmp_path):
        """Segments with empty text after strip are not included."""
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"\x00" * 100)

        segs = [
            _make_segment(0.0, 1.0, "   "),  # whitespace only
            _make_segment(1.0, 2.0, " Hola"),
        ]
        mock_model = _mock_model(segs)

        with patch("actas.pipeline.transcribe._get_model", return_value=mock_model):
            result = transcribe_audio(str(audio))

        assert len(result.segmentos) == 1
        assert result.segmentos[0].texto == "Hola"

    def test_model_name_in_result(self, tmp_path):
        """modelo field in result includes the model name."""
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"\x00" * 100)

        mock_model = _mock_model([_make_segment(0.0, 1.0, " Test")])

        with patch("actas.pipeline.transcribe._get_model", return_value=mock_model):
            result = transcribe_audio(str(audio), model_name="small")

        assert "small" in result.modelo

    def test_default_speaker_label(self, tmp_path):
        """Default speaker label is 'Hablante 1' before diarization."""
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"\x00" * 100)

        mock_model = _mock_model([_make_segment(0.0, 1.0, " Texto")])

        with patch("actas.pipeline.transcribe._get_model", return_value=mock_model):
            result = transcribe_audio(str(audio))

        assert result.segmentos[0].hablante_etiqueta == "Hablante 1"
