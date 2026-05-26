import asyncio
import os

import click

from actas.auth.models import AccesoUsuarioOrganizacion, RolEnum, Usuario
from actas.auth.service import hash_password
from actas.db import get_session
from actas.organizaciones.models import Miembro, Organo, Organizacion, TipoOrganoEnum


async def _seed() -> None:
    async with get_session() as db:
        async with db.begin():
            org = Organizacion(
                sigla="ASETRACO",
                nombre="Asociación Solidarista de Trabajadores de Costa Rica",
                afiliados=120,
            )
            db.add(org)
            await db.flush()

            organo = Organo(
                organizacion_id=org.id,
                nombre="Junta Directiva",
                tipo=TipoOrganoEnum.junta_directiva,
            )
            db.add(organo)
            await db.flush()

            for cargo in ["Presidencia", "Secretaría", "Tesorería"]:
                db.add(Miembro(organo_id=organo.id, nombre=f"Miembro {cargo}", cargo=cargo))

            user = Usuario(
                correo="admin@asetraco.cr",
                nombre="Administrador ASETRACO",
                hash_password=hash_password("dev1234"),
            )
            db.add(user)
            await db.flush()

            db.add(
                AccesoUsuarioOrganizacion(
                    usuario_id=user.id,
                    organizacion_id=org.id,
                    rol=RolEnum.administrador,
                )
            )

    click.echo("Seed completado: ASETRACO + Junta Directiva + 3 miembros + admin@asetraco.cr")


@click.group()
def cli():
    pass


@cli.command()
def seed():
    """Inserta datos de prueba en la base de datos."""
    asyncio.run(_seed())


# ── transcribe — F1-01 PoC ────────────────────────────────────────────────────

@cli.command()
@click.argument("audio_path")
@click.option("--model", default=None, help="Modelo Whisper (tiny/base/small/large-v3). Default: env WHISPER_MODEL o 'base'.")
@click.option("--language", default="es", show_default=True, help="Código de idioma.")
@click.option("--no-vad", is_flag=True, default=False, help="Desactiva el filtro de silencio (VAD).")
def transcribe(audio_path: str, model: str | None, language: str, no_vad: bool) -> None:
    """
    Transcribe un archivo de audio con faster-whisper (PoC F1-01).

    AUDIO_PATH: ruta al archivo de audio (wav, mp3, mp4, ogg, flac…)

    Ejemplos:

    \b
    # Transcribir con modelo 'base' (default)
    python -m actas.cli transcribe grabacion.wav

    \b
    # Usar modelo tiny para pruebas rápidas
    python -m actas.cli transcribe grabacion.mp3 --model tiny

    \b
    # En Docker:
    docker compose exec worker python -m actas.cli transcribe /tmp/audio.wav
    """
    if not os.path.exists(audio_path):
        click.echo(f"ERROR: No se encontró el archivo: {audio_path}", err=True)
        raise SystemExit(1)

    click.echo(f"Transcribiendo: {audio_path}")
    click.echo(f"  Modelo   : {model or os.getenv('WHISPER_MODEL', 'base')}")
    click.echo(f"  Idioma   : {language}")
    click.echo(f"  VAD      : {'no' if no_vad else 'sí'}")
    click.echo("")

    from actas.pipeline.transcribe import transcribe_audio

    result = transcribe_audio(
        audio_path,
        model_name=model,
        language=language,
        vad_filter=not no_vad,
    )

    click.echo(f"{'─' * 60}")
    click.echo(f"Idioma detectado : {result.idioma_detectado}")
    click.echo(f"Duración         : {result.duracion_seg:.1f}s")
    click.echo(f"Segmentos        : {len(result.segmentos)}")
    click.echo(f"Modelo           : {result.modelo}")
    click.echo(f"{'─' * 60}")
    click.echo("")

    for seg in result.segmentos:
        conf = f"  conf={float(seg.confianza):.2f}" if seg.confianza else ""
        click.echo(
            f"[{float(seg.inicio_seg):6.1f}s → {float(seg.fin_seg):6.1f}s]"
            f"  {seg.hablante_etiqueta}{conf}"
        )
        click.echo(f"  {seg.texto}")
        click.echo("")

    click.echo(f"{'─' * 60}")
    click.echo("TEXTO COMPLETO:")
    click.echo(result.texto_plano)


if __name__ == "__main__":
    cli()
