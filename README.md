# Plataforma de Actas Solidaristas

SaaS multi-tenant para gestión de actas de asociaciones solidaristas costarricenses.

## Requisitos previos

- Docker Desktop (con Compose V2)
- Make

## Arranque local

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Levantar toda la pila
make dev

# 3. Aplicar migraciones
make migrate

# 4. Cargar datos de prueba
make seed
```

La API queda en `http://localhost:8000`, el frontend en `http://localhost:5173`.

## Verificación rápida

```bash
curl localhost:8000/healthz   # → {"status":"ok"}
curl localhost:8000/readyz    # → {"status":"ok","checks":{...}}
```

## Comandos disponibles

```bash
make dev              # Levanta todos los servicios con docker compose
make migrate          # Aplica migraciones de Alembic
make migrate-create m="descripcion"  # Genera nueva migración
make seed             # Inserta datos de prueba (ASETRACO + usuario admin)
make test-back        # Pytest en el backend
make test-front       # Vitest en el frontend
make test-e2e         # Playwright end-to-end
make lint             # Ruff + Black (back) / ESLint (front)
make fmt              # Auto-formato
make types            # Genera tipos TypeScript desde OpenAPI
```

## Usuario de prueba

Después de `make seed`:

- **Correo:** `admin@asetraco.cr`
- **Contraseña:** `dev1234`

## Estructura del repositorio

```
backend/   — FastAPI + SQLAlchemy + pipeline de IA
frontend/  — React 18 + Vite + TypeScript + Tailwind
infra/     — Dockerfiles + init.sql
.github/   — CI (GitHub Actions)
```

Ver `CLAUDE.md` para la especificación técnica completa.
