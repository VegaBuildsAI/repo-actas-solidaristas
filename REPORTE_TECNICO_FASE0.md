# Reporte Técnico — Fase 0: Habilitación

> **Plataforma de Actas Inteligentes para Asociaciones Solidaristas**  
> Sociedad AXIO–Coreintelhub  ·  Cliente ancla: Bonsai Asesoría Estratégica  
> Generado: 26 de mayo de 2026  ·  Estado: ✅ Completado

---

## 1. Resumen ejecutivo

La Fase 0 entregó la base técnica completa del proyecto en menos de dos semanas de calendario, adelantándose al cronograma original. El equipo construyó desde cero un monorepo funcional con siete servicios de infraestructura en contenedores, un esquema de base de datos multi-tenant con 15 tablas y Row-Level Security activa, un backend FastAPI con autenticación JWT, y un frontend React 18 con login funcional contra el backend real. El pipeline de CI corre automáticamente en GitHub Actions. Todo el stack arranca con un solo comando (`make dev`) y cumple los criterios de aceptación definidos en el CLAUDE.md (Sección 15).

**Tareas completadas por Coreintelhub (dev):**

| ID | Tarea | Estado |
|----|-------|--------|
| F0-02 | Crear repositorios (frontend, backend, infra) | ✅ Completado |
| F0-03 | Configurar ambientes dev / staging / prod | ✅ Completado |
| F0-04 | Integración y despliegue continuos (CI/CD) | ✅ Completado |
| F0-05 | Esquema inicial de base de datos multi-tenant | ✅ Completado |
| — | Backend scaffolding (auth · tenancy · orgs · me) | ✅ Completado |
| — | Frontend scaffolding (login funcional · layout · router) | ✅ Completado |

**Tareas pendientes de partes externas:** F0-01 (kickoff formal), F0-06 a F0-13 (decisiones de negocio, material de Bonsai, DPA, revisión legal).

---

## 2. Trazabilidad con el Plan Técnico

### 2.1 F0-02 — Repositorios y monorepo (§15 · F0-02)

**Referencia CLAUDE.md:** Sección 5 (Estructura del repositorio), Sección 15 (F0-02).

**Entregables:**

```
repo-actas-solidaristas/
├─ CLAUDE.md                  ← spec técnica
├─ README.md                  ← instrucciones de arranque
├─ Makefile                   ← targets: dev, migrate, seed, test-*, lint, fmt, types
├─ .gitignore                 ← Python + Node + Docker + .env + IDEs
├─ .editorconfig              ← indent=2 TS/JSON, 4 Python, end_of_line=lf
├─ .env.example               ← todas las vars de §11, sin secretos reales
├─ .env                       ← copia local de .env.example
├─ LICENSE                    ← propietaria "All rights reserved"
├─ docker-compose.yml
├─ infra/
│  ├─ Dockerfile.backend
│  ├─ Dockerfile.frontend
│  ├─ Dockerfile.worker
│  └─ init.sql
├─ backend/
│  ├─ pyproject.toml
│  ├─ alembic.ini
│  ├─ migrations/versions/0001_initial_schema.py
│  ├─ migrations/versions/0002_rls_policies.py
│  └─ src/actas/             ← 20+ módulos Python
├─ frontend/
│  ├─ package.json
│  └─ src/                   ← 15+ archivos TypeScript/React
└─ .github/workflows/ci.yml
```

**Criterio de aceptación (CLAUDE.md):** ✅ `git clone` + README → cualquier dev entiende el repo.

---

### 2.2 F0-03 — Ambientes locales (§15 · F0-03)

**Referencia CLAUDE.md:** Sección 4 (Stack tecnológico), Sección 15 (F0-03).

**Entregable principal:** `docker-compose.yml`

| Servicio | Imagen | Puerto | Healthcheck |
|----------|--------|--------|-------------|
| `db` | `pgvector/pgvector:pg16` | 5432 | `pg_isready` |
| `redis` | `redis:7-alpine` | 6379 | `redis-cli ping` |
| `minio` | `minio/minio:latest` | 9000 / 9001 | `curl /minio/health/live` |
| `mailhog` | `mailhog/mailhog:latest` | 1025 / 8025 | — |
| `api` | `infra/Dockerfile.backend` | 8000 | `curl /healthz` |
| `worker` | `infra/Dockerfile.worker` | — | `rq info` |
| `frontend` | `infra/Dockerfile.frontend` | 5173 | `curl :5173` |

- Extensiones PostgreSQL activadas en `infra/init.sql`: `pgcrypto`, `vector`.
- Volúmenes nombrados persistentes: `pgdata`, `redis_data`, `minio_data`.
- Todos los Dockerfiles usan Python 3.12-slim / Node 20-alpine (versiones confirmadas con el cliente).

**Notas de implementación:**  
Los Dockerfiles backend/worker realizan un stub de `src/actas/__init__.py` antes de `pip install -e ".[dev]"` para que setuptools encuentre el paquete durante la imagen base. Esta solución fue necesaria porque el `COPY` inicial solo trae `pyproject.toml`.

**Criterio de aceptación:** ✅ `make dev` → 7 contenedores healthy · `curl localhost:8000/healthz` → 200 · frontend en 5173.

---

### 2.3 F0-04 — CI mínimo (§15 · F0-04)

**Referencia CLAUDE.md:** Sección 15 (F0-04), Sección 4 (lint/formato).

**Entregable:** `.github/workflows/ci.yml`

```
Triggers: push a main + PRs
Jobs (paralelos):
├─ lint-back      ruff check + black --check (Python 3.12)
├─ test-back      pytest -q  (servicios: postgres 16 + redis 7)
├─ lint-front     eslint (ESLint 9 + typescript-eslint@8)
└─ test-front     vitest run
```

- Cache de pip (`~/.cache/pip`) y npm (`~/.npm`) configurados para velocidad.
- `test-back` usa `services:` de GitHub Actions con la misma imagen `pgvector/pgvector:pg16`.
- Se resolvió un conflicto de versiones peer: `@typescript-eslint/parser@7` requiere ESLint 8; se migró a `typescript-eslint@^8.0.0` (paquete unificado para ESLint 9).

**Criterio de aceptación:** ✅ Un PR de prueba ejecuta los 4 jobs y quedan verdes.

---

### 2.4 F0-05 — Esquema inicial de BD (§15 · F0-05)

**Referencia CLAUDE.md:** Sección 6 (Modelo de datos), Sección 15 (F0-05).

#### Migración 0001 — Schema completo

`backend/migrations/versions/0001_initial_schema.py`

**Enums creados (6):**
- `rol_enum`: `administrador`, `operario`
- `tipo_organo_enum`: `junta_directiva`, `comite`
- `reunion_estado_enum`: `programada`, `procesando`, `en_revision`, `aprobada`
- `doc_tipo_enum`: `resumen`, `acta`, `minuta`
- `doc_estado_enum`: `borrador`, `en_revision`, `aprobado`
- `acuerdo_estado_enum`: `pendiente`, `en_proceso`, `completado`

**Tablas creadas (15, en orden de dependencia):**

| # | Tabla | Clave foránea relevante | Notas |
|---|-------|------------------------|-------|
| 1 | `organizacion` | — | Root tenant |
| 2 | `usuario` | — | Correo único |
| 3 | `acceso_usuario_organizacion` | usuario + organizacion | PK compuesta · rol por org |
| 4 | `organo` | organizacion | UNIQUE (org, nombre) |
| 5 | `miembro` | organo | Cargos: Presidencia, Secretaría… |
| 6 | `reunion` | organizacion + organo | Estado enum |
| 7 | `grabacion` | reunion | URI S3 · política retención |
| 8 | `transcripcion` | reunion | Texto plano + modelo STT |
| 9 | `segmento_transcripcion` | transcripcion + miembro | Timestamps + confianza |
| 10 | `documento` | reunion + usuario | JSONB · UNIQUE (reunion, tipo) |
| 11 | `acuerdo` | reunion + organizacion | Código · firme · responsable |
| 12 | `comentario_acuerdo` | acuerdo + usuario | — |
| 13 | `plantilla_legal` | organizacion (nullable) | NULL = global solidarista |
| 14 | `rag_chunk` | organizacion (nullable) | `embedding vector(1536)` |
| 15 | `auditoria` | — (IDs desvinculados) | `BIGSERIAL` |

**Índices:**
- `rag_chunk_emb_idx`: HNSW sobre `embedding vector_cosine_ops` (búsqueda coseno para RAG)
- `auditoria_org_fecha_idx`: compuesto `(organizacion_id, ocurrida_en DESC)` para consultas de auditoría por org

#### Migración 0002 — Row-Level Security

`backend/migrations/versions/0002_rls_policies.py`

**Diseño de la política:**
```sql
-- Por cada tabla con organizacion_id:
ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY;
CREATE POLICY {tabla}_tenant_isolation ON {tabla}
  USING (
    organizacion_id IS NULL
    OR organizacion_id = current_setting('app.current_organization_id', true)::UUID
  );
```

**Tablas con RLS directo (7):**  
`organo`, `reunion`, `acuerdo`, `plantilla_legal`, `rag_chunk`, `auditoria`, `acceso_usuario_organizacion`

**Decisión de arquitectura documentada:**  
La tabla `organizacion` *no* tiene RLS directa porque su PK es `id`, no `organizacion_id`. El acceso a filas de organizaciones se controla al nivel de aplicación a través del join `acceso_usuario_organizacion`. Esto evitó el error `column "organizacion_id" does not exist` que ocurre al aplicar RLS a la tabla raíz.

**Setter de tenant en la aplicación** (`backend/src/actas/db.py`):
```python
async def set_tenant(session: AsyncSession, org_id: str) -> None:
    await session.execute(
        text("SELECT set_config('app.current_organization_id', :org_id, true)"),
        {"org_id": org_id},
    )
```

#### Seed de desarrollo

`backend/src/actas/cli.py` — comando `python -m actas.cli seed`

| Entidad | Valor |
|---------|-------|
| Organización | sigla=ASETRACO, nombre="Asociación Solidarista de Trabajadores de Costa Rica" |
| Órgano | nombre="Junta Directiva", tipo=junta_directiva |
| Miembros | Presidencia · Secretaría · Tesorería |
| Usuario admin | correo=admin@asetraco.cr · password=dev1234 |

**Criterio de aceptación:** ✅ `make migrate` desde cero sin error · `make seed` puebla los datos · query con `app.current_organization_id` incorrecto devuelve 0 filas.

---

### 2.5 Backend scaffolding (§15)

**Referencia CLAUDE.md:** Sección 15 (Backend scaffolding), Sección 7 (API endpoints), Sección 9 (Seguridad).

#### Estructura del paquete `actas/`

```
src/actas/
├─ __init__.py
├─ main.py           FastAPI app + lifespan (DB pool + Redis) + /healthz + /readyz
├─ settings.py       pydantic-settings con todas las vars de §11
├─ db.py             AsyncEngine + AsyncSession + set_tenant() + get_db()
├─ deps.py           get_current_user() (JWT decode) + get_current_org()
├─ cli.py            Click: comando seed
├─ auth/
│  ├─ models.py      Usuario + AccesoUsuarioOrganizacion (SQLAlchemy mapped)
│  ├─ schemas.py     LoginRequest · RefreshRequest · TokenResponse · UserOut
│  ├─ service.py     hash_password · verify_password · create_tokens · verify_refresh_token
│  └─ routes.py      POST /auth/login · POST /auth/refresh · POST /auth/logout
├─ tenancy/
│  ├─ middleware.py  Extrae X-Organization-Id header → request.state.org_id
│  └─ deps.py        require_org dependency
├─ organizaciones/
│  ├─ models.py      Organizacion · Organo · Miembro
│  ├─ schemas.py     Pydantic in/out (snake_case en el cable)
│  ├─ repo.py        CRUD async
│  └─ routes.py      GET/POST /organizaciones · GET/POST /organizaciones/{id}/organos
└─ me/
   └─ routes.py      GET /me → perfil + lista de orgs con rol
```

#### Decisiones técnicas implementadas

| Decisión | Valor elegido | Justificación |
|----------|--------------|---------------|
| Serialización JSON | **snake_case** | Confirmado con el cliente (desvío del default camelCase del spec) |
| Hashing contraseñas | bcrypt cost=12 | CLAUDE.md §9 |
| JWT access TTL | 60 min | CLAUDE.md §9 |
| JWT refresh TTL | 7 días | CLAUDE.md §9 |
| Algoritmo JWT | HS256 | CLAUDE.md §11 |
| Middleware RLS | `set_config()` por sesión (LOCAL) | Aislamiento multi-tenant por request |
| Rutas exentas de tenancy | `/auth/*`, `/healthz`, `/readyz`, `/docs`, `/openapi.json` | Acceso público necesario |

#### Endpoints implementados y verificados

| Método | Path | Estado |
|--------|------|--------|
| `GET` | `/healthz` | ✅ |
| `GET` | `/readyz` | ✅ (db + redis + s3) |
| `POST` | `/auth/login` | ✅ |
| `POST` | `/auth/refresh` | ✅ |
| `POST` | `/auth/logout` | ✅ |
| `GET` | `/me` | ✅ |
| `GET` | `/organizaciones` | ✅ |
| `POST` | `/organizaciones` | ✅ |
| `GET` | `/organizaciones/{id}` | ✅ |
| `GET` | `/organizaciones/{id}/organos` | ✅ |
| `POST` | `/organizaciones/{id}/organos` | ✅ |

---

### 2.6 Frontend scaffolding (§15)

**Referencia CLAUDE.md:** Sección 4 (Stack frontend), Sección 15 (Frontend scaffolding).

#### Stack instalado y configurado

| Lib | Versión | Uso |
|-----|---------|-----|
| React | 18.3 | UI |
| Vite | 5.3 | Bundler + dev server |
| TypeScript | 5.4 | Tipado estático |
| Tailwind CSS | 3.4 | Estilos con paleta Coreintelhub B |
| React Router | 6.23 | SPA routing |
| TanStack Query | 5.40 | Server state |
| Axios | 1.7 | HTTP client con interceptores JWT |
| Zod | 3.23 | Validación de formularios |
| Lucide React | 0.390 | Iconos |
| Vitest | 1.6 | Unit tests |
| Playwright | 1.44 | E2E tests (preparado) |
| openapi-typescript | 7 | Generación de tipos desde OpenAPI |

#### Paleta implementada (`tailwind.config.ts`)

```typescript
colors: {
  ink:         "#15141C",   // texto principal
  indigo:      "#4B457B",   // acento primario
  blue:        "#41AAFD",   // acento secundario
  indigoDk:    "#3A3560",
  blueDk:      "#2E6FB8",
  bg:          "#FAFAFC",   // fondo app
  panel:       "#FFFFFF",   // tarjetas
  border:      "#EAEAF0",
  sidebar:     "#1C1B26",   // nav lateral
  sidebarActive:"#2C2B3A",
}
```

#### Estructura de archivos

```
src/
├─ main.tsx                 Punto de entrada + QueryClientProvider + AuthProvider
├─ App.tsx                  RouterProvider
├─ router.tsx               createBrowserRouter + RequireAuth wrapper
├─ styles/index.css         Tailwind + fuentes base
├─ api/
│  ├─ client.ts             Axios instance + JWT interceptor + 401 handler
│  └─ auth.ts               login() · refresh() · logout()
├─ auth/
│  └─ AuthContext.tsx       Context + Provider + useAuth()
├─ pages/
│  ├─ Login.tsx             Formulario con paleta brand (ink bg · indigo btn)
│  ├─ Inicio.tsx            Dashboard con métricas Fase 0 + roadmap + módulos
│  ├─ Reuniones.tsx         Placeholder Fase 1
│  ├─ Acuerdos.tsx          Placeholder Fase 2
│  └─ Reportes.tsx          Placeholder Fase 3
└─ components/
   ├─ Sidebar.tsx           Nav lateral con brand palette + NavLink activo
   ├─ Topbar.tsx            Barra superior + org + usuario + logout
   └─ Layout.tsx            Composición Sidebar + Topbar + outlet
```

---

### 2.7 Tests automatizados

**Referencia CLAUDE.md:** Sección 13 (Pirámide de pruebas), Sección 15 (Backend scaffolding).

#### Backend (`pytest`)

`backend/tests/test_auth.py` — 7 tests:
- `test_hash_and_verify` — bcrypt roundtrip
- `test_verify_wrong_password` — rechazo correcto
- `test_create_tokens_returns_two_strings` — access + refresh son strings
- `test_access_token_payload` — `sub` y `type: access`
- `test_refresh_token_payload` — `sub` y `type: refresh`
- `test_access_token_expiry` — campo `exp` presente
- `test_invalid_token_raises` — token inválido lanza excepción

`backend/tests/test_tenancy.py` — 3 tests:
- `test_org_id_extracted_from_header` — middleware extrae X-Organization-Id
- `test_no_header_yields_none` — sin header → state.org_id = None
- `test_exempt_path_skips_tenant` — /healthz no requiere header

#### Frontend (`vitest`)

`frontend/src/test/auth.test.tsx` — 3 tests:
- Render de `Login` sin crash
- AuthContext provee valor inicial `null`
- AuthContext cambia a user después de login mock

---

## 3. Problemas encontrados y soluciones

| Problema | Causa | Solución aplicada |
|----------|-------|-------------------|
| `setuptools.backends.legacy:build` no existe | Build backend incorrecto en pyproject.toml | Cambiado a `setuptools.build_meta` |
| `src does not exist` en Docker | Solo se copiaba pyproject.toml antes de pip install | `RUN mkdir -p src/actas && touch src/actas/__init__.py` antes de pip |
| ESLint peer conflict | `@typescript-eslint/parser@7` requiere ESLint 8; usábamos ESLint 9 | Migrado a `typescript-eslint@^8.0.0` (paquete unificado) |
| RLS en tabla `organizacion` falla | La tabla raíz tiene PK `id`, no `organizacion_id` | Excluida de `_DIRECT_ORG_TABLES`; acceso controlado al nivel app |
| `__import__("sqlalchemy")` en db.py | Import hackish heredado | Reemplazado con `from sqlalchemy import text` en el top |
| Endpoint `/auth/refresh` aceptaba dict crudo | Faltaba modelo Pydantic | Agregado `RefreshRequest(BaseModel)` con campo `refresh_token: str` |
| Docker no en PATH en nuevas sesiones PowerShell | PATH no persiste entre sesiones | `$env:PATH = [System.Environment]::GetEnvironmentVariable(...)` por sesión |

---

## 4. Desviaciones del spec confirmadas

| Ítem | Spec original (§7, §18) | Decisión adoptada | Fundamento |
|------|------------------------|-------------------|------------|
| Serialización JSON | camelCase en el cable | **snake_case** | Confirmado con el cliente; sin alias_generator en FastAPI; consistencia Python ↔ wire |
| Versión Python | ≥3.12 | **Python 3.12** | Confirmado con el cliente |
| Versión Node | LTS | **Node 20 LTS** | Confirmado con el cliente (se instaló Node 24.16.0 por disponibilidad de package manager) |

---

## 5. Verificaciones de aceptación realizadas

```bash
# ✅ 1. Stack completo arranca
make dev  # → 7 contenedores healthy

# ✅ 2. Liveness
curl localhost:8000/healthz  # → {"status":"ok"}

# ✅ 3. Readiness (db + redis + s3)
curl localhost:8000/readyz   # → {"status":"ok","checks":{...}}

# ✅ 4. Migraciones desde cero
make migrate  # → 0001 + 0002 sin errores

# ✅ 5. Datos de seed
make seed  # → ASETRACO · Junta Directiva · 3 miembros · admin@asetraco.cr

# ✅ 6. RLS aislamiento
# (en psql) SET app.current_organization_id = 'uuid-incorrecto';
# SELECT * FROM reunion;  → 0 rows

# ✅ 7. Login end-to-end
curl -X POST localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"correo":"admin@asetraco.cr","password":"dev1234"}'
# → {"access_token":"eyJ...","refresh_token":"eyJ...","token_type":"bearer"}

# ✅ 8. Endpoint protegido
curl localhost:8000/organizaciones \
  -H "Authorization: Bearer <access_token>"
# → [{"id":"...","sigla":"ASETRACO",...}]

# ✅ 9. Frontend
# Browser localhost:5173 → pantalla login con paleta brand
# Login con admin@asetraco.cr / dev1234 → dashboard con Sidebar + Topbar
```

---

## 6. Decisiones pendientes (no bloqueantes para Fase 1)

Estas decisiones corresponden a las Secciones 16 y 18 del CLAUDE.md y siguen en manos de partes externas o del equipo AXIO:

| # | Decisión | Responsable | Bloquea |
|---|----------|-------------|---------|
| F0-09 | Firma DPA con Anthropic (retención cero) | AXIO | Uso del LLM en staging/prod |
| F0-06 | Plantilla legal del acta solidarista | Carlos / Bonsai | Indexado RAG (F1-06) |
| F0-07 | 20+ actas históricas de muestra | Bonsai | Spike de Fase 4 |
| F0-08 | 3–5 grabaciones reales | Bonsai | PoC transcripción (F1-01) |
| F0-11 | Plan A vs. Plan B (arquitectura LLM) | AXIO + Carlos | F1-07 |
| F0-12 | Proveedor de nube y residencia de datos | AXIO + Carlos | Despliegue staging |
| F0-13 | Accuracy mínimo aceptable | Carlos + Bonsai | Criterio Fase 4 |

Para **Fase 1** (sem. 3–6) se puede arrancar inmediatamente con F1-01 (PoC WhisperX), F1-02 (servicio de carga de grabación a MinIO), y F1-03 (cola RQ + worker) usando audio de prueba propio, sin depender de Bonsai.

---

## 7. Próximos pasos — Inicio de Fase 1

Las primeras tareas de Fase 1 que no tienen dependencia externa:

1. **F1-01** — PoC transcripción WhisperX  
   Instalar `faster-whisper` + `whisperx` en `Dockerfile.worker`. Transcribir un audio de prueba de 5 min en español CR. Verificar latencia y formato de salida.

2. **F1-02** — Servicio de carga de grabación  
   Ruta `POST /reuniones/{id}/grabacion` · subir a MinIO (`s3://actas-audio/...`) · encolar job RQ.

3. **F1-03** — Cola de trabajos RQ + worker  
   Esqueleto de `pipeline/worker.py` con `procesar_reunion()`. Validar que el worker procesa jobs desde Redis correctamente.

4. **F1-04 / F1-05** — Transcripción + diarización (requiere F1-01)  
   `whisperx.transcribe()` → `whisperx.diarize()` → guardar en `transcripcion` y `segmento_transcripcion`.

---

*Documento técnico interno de la sociedad AXIO–Coreintelhub.*  
*Fase 0 construida con Claude Code (Anthropic Claude Sonnet 4.6) · Mayo 2026.*
