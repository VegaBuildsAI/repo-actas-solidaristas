"""Row-Level Security policies for tenant isolation

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-26
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# Tables that are scoped by organizacion_id
_TENANT_TABLES = [
    "organizacion",
    "acceso_usuario_organizacion",
    "organo",
    "miembro",
    "reunion",
    "grabacion",
    "transcripcion",
    "segmento_transcripcion",
    "documento",
    "acuerdo",
    "comentario_acuerdo",
    "plantilla_legal",
    "rag_chunk",
    "auditoria",
]

# Tables that have an organizacion_id column (subset used for direct RLS policy).
# Note: the `organizacion` table itself is NOT included — its PK is `id`,
# not `organizacion_id`. Access to org rows is enforced at the app layer
# via the acceso_usuario_organizacion join.
_DIRECT_ORG_TABLES = [
    "organo",
    "reunion",
    "acuerdo",
    "plantilla_legal",
    "rag_chunk",
    "auditoria",
]


def upgrade() -> None:
    for table in _DIRECT_ORG_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            USING (
                organizacion_id IS NULL
                OR organizacion_id = current_setting('app.current_organization_id', true)::UUID
            )
        """)

    # acceso_usuario_organizacion uses organizacion_id too
    op.execute("ALTER TABLE acceso_usuario_organizacion ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE acceso_usuario_organizacion FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY acceso_usuario_organizacion_tenant_isolation
        ON acceso_usuario_organizacion
        USING (
            organizacion_id = current_setting('app.current_organization_id', true)::UUID
        )
    """)


def downgrade() -> None:
    for table in _DIRECT_ORG_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")

    op.execute(
        "DROP POLICY IF EXISTS acceso_usuario_organizacion_tenant_isolation "
        "ON acceso_usuario_organizacion"
    )
    op.execute("ALTER TABLE acceso_usuario_organizacion DISABLE ROW LEVEL SECURITY")
