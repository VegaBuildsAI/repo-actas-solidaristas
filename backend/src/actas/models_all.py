"""
Import all SQLAlchemy models to populate the shared metadata registry.

SQLAlchemy resolves FK string references (e.g. ForeignKey("miembro.id")) only if the
referenced table's model has been imported and registered with the same Base.metadata.

Workers, CLI commands, and any other code that performs ORM operations should do:
    import actas.models_all  # noqa
before opening any DB session.
"""

# Auth
from actas.auth.models import AccesoUsuarioOrganizacion, Usuario  # noqa: F401

# Organizaciones
from actas.organizaciones.models import Miembro, Organo, Organizacion  # noqa: F401

# Reuniones + pipeline tables
from actas.reuniones.models import (  # noqa: F401
    Grabacion,
    Reunion,
    SegmentoTranscripcion,
    Transcripcion,
)
