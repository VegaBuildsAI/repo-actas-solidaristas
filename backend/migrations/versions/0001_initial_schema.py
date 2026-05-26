"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums
    op.execute("CREATE TYPE rol_enum AS ENUM ('administrador', 'operario')")
    op.execute("CREATE TYPE tipo_organo_enum AS ENUM ('junta_directiva', 'comite')")
    op.execute(
        "CREATE TYPE reunion_estado_enum AS ENUM "
        "('programada', 'procesando', 'en_revision', 'aprobada')"
    )
    op.execute("CREATE TYPE doc_tipo_enum AS ENUM ('resumen', 'acta', 'minuta')")
    op.execute(
        "CREATE TYPE doc_estado_enum AS ENUM ('borrador', 'en_revision', 'aprobado')"
    )
    op.execute(
        "CREATE TYPE acuerdo_estado_enum AS ENUM ('pendiente', 'en_proceso', 'completado')"
    )

    # organizacion
    op.execute("""
        CREATE TABLE organizacion (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            sigla       TEXT NOT NULL UNIQUE,
            nombre      TEXT NOT NULL,
            afiliados   INT,
            activa      BOOLEAN NOT NULL DEFAULT TRUE,
            creada_en   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # usuario
    op.execute("""
        CREATE TABLE usuario (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            correo          TEXT NOT NULL UNIQUE,
            nombre          TEXT NOT NULL,
            hash_password   TEXT NOT NULL,
            activo          BOOLEAN NOT NULL DEFAULT TRUE,
            creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # acceso_usuario_organizacion
    op.execute("""
        CREATE TABLE acceso_usuario_organizacion (
            usuario_id        UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
            organizacion_id   UUID NOT NULL REFERENCES organizacion(id) ON DELETE CASCADE,
            rol               rol_enum NOT NULL,
            PRIMARY KEY (usuario_id, organizacion_id)
        )
    """)

    # organo
    op.execute("""
        CREATE TABLE organo (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organizacion_id   UUID NOT NULL REFERENCES organizacion(id) ON DELETE CASCADE,
            nombre            TEXT NOT NULL,
            tipo              tipo_organo_enum NOT NULL,
            UNIQUE (organizacion_id, nombre)
        )
    """)

    # miembro
    op.execute("""
        CREATE TABLE miembro (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organo_id   UUID NOT NULL REFERENCES organo(id) ON DELETE CASCADE,
            nombre      TEXT NOT NULL,
            cargo       TEXT NOT NULL,
            activo      BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)

    # reunion
    op.execute("""
        CREATE TABLE reunion (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organizacion_id   UUID NOT NULL REFERENCES organizacion(id),
            organo_id         UUID NOT NULL REFERENCES organo(id),
            tipo              TEXT NOT NULL,
            fecha             DATE NOT NULL,
            hora_inicio       TIME,
            hora_fin          TIME,
            modalidad         TEXT,
            numero_acta       INT,
            estado            reunion_estado_enum NOT NULL DEFAULT 'programada',
            creada_en         TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # grabacion
    op.execute("""
        CREATE TABLE grabacion (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            reunion_id          UUID NOT NULL REFERENCES reunion(id) ON DELETE CASCADE,
            storage_uri         TEXT NOT NULL,
            duracion_segundos   INT,
            bytes               BIGINT,
            subido_en           TIMESTAMPTZ NOT NULL DEFAULT now(),
            borrado_en          TIMESTAMPTZ
        )
    """)

    # transcripcion
    op.execute("""
        CREATE TABLE transcripcion (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            reunion_id    UUID NOT NULL REFERENCES reunion(id) ON DELETE CASCADE,
            texto_plano   TEXT NOT NULL,
            modelo        TEXT NOT NULL,
            generada_en   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # segmento_transcripcion
    op.execute("""
        CREATE TABLE segmento_transcripcion (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            transcripcion_id  UUID NOT NULL REFERENCES transcripcion(id) ON DELETE CASCADE,
            inicio_seg        NUMERIC(10,3) NOT NULL,
            fin_seg           NUMERIC(10,3) NOT NULL,
            hablante_etiqueta TEXT NOT NULL,
            miembro_id        UUID REFERENCES miembro(id),
            texto             TEXT NOT NULL,
            confianza         NUMERIC(5,4)
        )
    """)

    # documento
    op.execute("""
        CREATE TABLE documento (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            reunion_id      UUID NOT NULL REFERENCES reunion(id) ON DELETE CASCADE,
            tipo            doc_tipo_enum NOT NULL,
            estado          doc_estado_enum NOT NULL DEFAULT 'borrador',
            contenido       JSONB NOT NULL,
            version         INT NOT NULL DEFAULT 1,
            generado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),
            aprobado_por    UUID REFERENCES usuario(id),
            aprobado_en     TIMESTAMPTZ,
            UNIQUE (reunion_id, tipo)
        )
    """)

    # acuerdo
    op.execute("""
        CREATE TABLE acuerdo (
            id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            reunion_id            UUID NOT NULL REFERENCES reunion(id) ON DELETE CASCADE,
            organizacion_id       UUID NOT NULL REFERENCES organizacion(id),
            codigo                TEXT NOT NULL,
            texto                 TEXT NOT NULL,
            responsable           TEXT,
            fecha_limite          DATE,
            estado                acuerdo_estado_enum NOT NULL DEFAULT 'pendiente',
            firme                 BOOLEAN NOT NULL DEFAULT FALSE,
            objetivo_estrategico  TEXT,
            creado_en             TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # comentario_acuerdo
    op.execute("""
        CREATE TABLE comentario_acuerdo (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            acuerdo_id    UUID NOT NULL REFERENCES acuerdo(id) ON DELETE CASCADE,
            usuario_id    UUID NOT NULL REFERENCES usuario(id),
            texto         TEXT NOT NULL,
            creado_en     TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # plantilla_legal
    op.execute("""
        CREATE TABLE plantilla_legal (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organizacion_id   UUID REFERENCES organizacion(id),
            nombre            TEXT NOT NULL,
            contenido         TEXT NOT NULL,
            activa            BOOLEAN NOT NULL DEFAULT TRUE,
            creada_en         TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # rag_chunk
    op.execute("""
        CREATE TABLE rag_chunk (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organizacion_id   UUID REFERENCES organizacion(id),
            fuente            TEXT NOT NULL,
            documento_id      UUID,
            texto             TEXT NOT NULL,
            embedding         vector(1536),
            creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX rag_chunk_emb_idx ON rag_chunk "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # auditoria
    op.execute("""
        CREATE TABLE auditoria (
            id                BIGSERIAL PRIMARY KEY,
            organizacion_id   UUID,
            usuario_id        UUID,
            accion            TEXT NOT NULL,
            entidad           TEXT NOT NULL,
            entidad_id        UUID,
            metadata          JSONB,
            ocurrida_en       TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX auditoria_org_fecha_idx ON auditoria (organizacion_id, ocurrida_en DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS auditoria CASCADE")
    op.execute("DROP TABLE IF EXISTS rag_chunk CASCADE")
    op.execute("DROP TABLE IF EXISTS plantilla_legal CASCADE")
    op.execute("DROP TABLE IF EXISTS comentario_acuerdo CASCADE")
    op.execute("DROP TABLE IF EXISTS acuerdo CASCADE")
    op.execute("DROP TABLE IF EXISTS documento CASCADE")
    op.execute("DROP TABLE IF EXISTS segmento_transcripcion CASCADE")
    op.execute("DROP TABLE IF EXISTS transcripcion CASCADE")
    op.execute("DROP TABLE IF EXISTS grabacion CASCADE")
    op.execute("DROP TABLE IF EXISTS reunion CASCADE")
    op.execute("DROP TABLE IF EXISTS miembro CASCADE")
    op.execute("DROP TABLE IF EXISTS organo CASCADE")
    op.execute("DROP TABLE IF EXISTS acceso_usuario_organizacion CASCADE")
    op.execute("DROP TABLE IF EXISTS usuario CASCADE")
    op.execute("DROP TABLE IF EXISTS organizacion CASCADE")
    op.execute("DROP TYPE IF EXISTS acuerdo_estado_enum")
    op.execute("DROP TYPE IF EXISTS doc_estado_enum")
    op.execute("DROP TYPE IF EXISTS doc_tipo_enum")
    op.execute("DROP TYPE IF EXISTS reunion_estado_enum")
    op.execute("DROP TYPE IF EXISTS tipo_organo_enum")
    op.execute("DROP TYPE IF EXISTS rol_enum")
