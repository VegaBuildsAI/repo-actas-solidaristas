# Plataforma de Actas Inteligentes para Asociaciones Solidaristas

> **Especificación técnica para arranque del proyecto** — Sociedad AXIO–Coreintelhub
> Documento de contexto para Claude Code en modo plan. Es auto-contenido: contiene todo lo necesario para empezar a construir sin depender de los documentos Word de referencia.

---

## Cómo usar este documento

1. Abrí Claude Code en el directorio del repositorio (vacío al inicio).
2. Subí este archivo o renómbralo a `CLAUDE.md` para que Claude lo lea automáticamente como contexto del proyecto.
3. Activá modo plan y pedile a Claude que proponga el plan de la **Fase 0** (Sección 15). Iterá hasta acordar el plan; luego salí de modo plan y empezá la ejecución.
4. Cualquier ambigüedad o decisión faltante: ver Sección 18 (preguntas que Claude debe hacer antes de codificar) y Sección 16 (decisiones pendientes del cliente).

**Documentos complementarios en la misma carpeta** (no son requeridos para arrancar, son referencia):

- `Plan de Accion - Plataforma Actas Solidaristas (AXIO-Coreintelhub).docx` — estrategia comercial y de negocio.
- `Plan Tecnico - Plataforma Actas Solidaristas (AXIO-Coreintelhub).docx` — el plan técnico extendido del que se deriva este spec.
- `Pipeline Seguimiento - Plataforma Actas Solidaristas.xlsx` — 47 tareas con responsable, fechas y dependencias (este spec se sincroniza con esos IDs `F0-XX`, `F1-XX`, etc.).
- `Demo Bonsai - Plataforma de Actas Solidaristas.jsx` — demo React navegable; la implementación real toma como referencia su UI/UX.

---

## 1. Resumen y contexto

**Quiénes lo construyen.** Sociedad AXIO–Coreintelhub (Costa Rica). Equipo: dos desarrolladores de Coreintelhub + coordinación de producto desde AXIO + Carlos León (relación con cliente y validación legal).

**Para quién.** Bonsai Asesoría Estratégica (cliente ancla); su gerente general, Gabriel Meléndez, es el champion. Bonsai administra varias asociaciones solidaristas.

**Qué se construye.** Una plataforma SaaS multi-tenant que:

1. Captura el audio de reuniones de junta directiva y comités (carga de grabación o asistente que entra en vivo).
2. Lo transcribe e identifica a los hablantes.
3. Genera tres documentos: resumen ejecutivo, **acta** con estructura legal solidarista y minuta operativa.
4. Extrae los acuerdos a un tablero de seguimiento con estados.
5. Da a Bonsai y a sus asociaciones un dashboard con indicadores y reportería.

**Por qué.** Hoy una asociación solidarista típica produce 12+ actas al mes con personal no remunerado, con errores, sin trazabilidad y exponiéndose legalmente. El producto convierte ese pasivo no gestionado en un servicio predecible.

**Estado actual.** Propuesta enviada a Bonsai y en negociación; demo navegable entregado; este es el documento técnico de arranque.

---

## 2. Objetivo, alcance y restricciones

### Objetivo del MVP

Procesar la primera reunión real de Bonsai de extremo a extremo —del audio al acta aprobada— con la calidad y la trazabilidad exigibles ante una junta directiva, dentro de 16 semanas.

### En alcance

- Captura por carga de grabación (Fase 1) y por bot Teams/Meet (Fase 5).
- Transcripción en español de Costa Rica con identificación de hablantes.
- Generación con IA de los tres documentos (resumen, acta, minuta).
- Extracción estructurada de acuerdos.
- Flujo de revisión y aprobación humana.
- Multi-organización (Bonsai administra varias asociaciones).
- Reportería: tiempo, asistencia, participación, estado de acuerdos.

### Fuera de alcance (MVP)

- Migración de actas históricas.
- Integraciones con sistemas contables / de gestión de las asociaciones.
- Edición colaborativa en tiempo real.
- Aplicación móvil nativa.

### Restricciones

- **Regulatorias.** Ley 6970 de Asociaciones Solidaristas (estructura del acta y libro de actas) y Ley 8968 de Protección de Datos (PRODHAB es el regulador en Costa Rica). El audio es dato sensible.
- **De equipo.** Dos desarrolladores. El stack y la arquitectura se eligen para ser sostenibles por un equipo pequeño.
- **De presupuesto.** Ver Plan de Acción Estratégico. Decisiones técnicas favorecen la previsibilidad sobre la sofisticación.

---

## 3. Arquitectura

Canal de procesamiento en cuatro etapas que alimentan una aplicación web multi-organización, con la seguridad y el cumplimiento como capa transversal.

```
┌──────────┐   ┌───────────────┐   ┌────────────────┐   ┌───────────┐
│ Captura  │ → │ Transcripción │ → │ Generación IA  │ → │ Revisión  │
│ (audio)  │   │ + diarización │   │ (LLM + RAG)    │   │ humana    │
└──────────┘   └───────────────┘   └────────────────┘   └─────┬─────┘
                                                              │
                                                              ▼
                                              ┌───────────────────────┐
                                              │ Aplicación web React  │
                                              │ + API + worker + BD   │
                                              └───────────────────────┘
       Capa transversal: cifrado · DPA · control de acceso · auditoría
```

**Decisión de arquitectura por defecto: Plan A** — el modelo de lenguaje corre vía API empresarial con DPA y retención cero. La transcripción se auto-hospeda; el audio nunca sale de infraestructura controlada. Solo cruza el texto.

**Plan B (contingencia).** Si la consulta legal prohíbe la transferencia del texto incluso con DPA, se sustituye el LLM por uno auto-hospedado. La frontera del servicio de generación está aislada justamente para permitir este cambio sin rehacer el sistema.

---

## 4. Stack tecnológico

| Capa | Tecnología (versión objetivo) | Notas |
|---|---|---|
| Frontend | React 18 + Vite 5 + TypeScript 5 | SPA; el demo navegable ya está en React. |
| Estilos | Tailwind CSS 3 + Headless UI | Identidad B de Coreintelhub (paleta abajo). |
| Frontend libs | React Router 6, TanStack Query 5, Zod 3, Recharts 2, Lucide React | Lo necesario, nada más. |
| API / backend | Python 3.12 + FastAPI 0.110+ + Uvicorn | Async nativo; mismo lenguaje que el pipeline. |
| ORM y migraciones | SQLAlchemy 2 (async) + Alembic | Migraciones versionadas desde el día 1. |
| Validación | Pydantic v2 | Esquemas compartidos con FastAPI. |
| Cola de trabajos | Redis 7 + RQ (`rq` 1.16+) | Simple y robusto para el tamaño del equipo. |
| Base de datos | PostgreSQL 16 + extensión `pgvector` 0.7+ | RAG en la misma BD; sin servicio aparte de vectores. |
| Almacenamiento de objetos | S3-compatible (en dev: MinIO) | Grabaciones cifradas en reposo. |
| Transcripción (STT) | `faster-whisper` (modelo `large-v3`) auto-hospedado | Funciona en CPU para dev; GPU recomendada para producción. |
| Diarización | `WhisperX` (incluye STT + diarización con `pyannote.audio`) | Modelo de diarización requiere token HuggingFace. |
| LLM | Anthropic Claude (default) — SDK `anthropic` Python | Plan A. DPA con retención cero. |
| Embeddings | `text-embedding-3-small` (1536 dim) vía API | Para indexar la plantilla legal y actas en `pgvector`. |
| Autenticación | JWT (`pyjwt`) + refresh tokens; `bcrypt` para contraseñas | Multi-tenant con scope por organización. |
| Email transaccional | SMTP estándar (envío al secretario para revisión) | En dev: MailHog. |
| Contenedores | Docker + docker-compose | Local idéntico a staging. |
| Integración continua | GitHub Actions | Lint + tests + build. |
| Testing | `pytest` + `pytest-asyncio` (back) · Vitest + Playwright (front) | Unit + integration + e2e. |
| Lint / formato | `ruff` + `black` (Python) · ESLint + Prettier (TS) | Pre-commit hooks. |

### Paleta (identidad de Coreintelhub — dirección B)

```
ink:     #15141C       indigo:   #4B457B       blue:     #41AAFD
indigoDk:#3A3560       blueDk:   #2E6FB8       bg:       #FAFAFC
panel:   #FFFFFF       border:   #EAEAF0       sidebar:  #1C1B26
sidebarActive: #2C2B3A
```

---

## 5. Estructura del repositorio

Monorepo con frontend y backend en el mismo árbol. Un solo `docker-compose.yml` levanta todo el entorno local.

```
repo-actas-solidaristas/
├─ README.md
├─ CLAUDE.md                        # este documento
├─ Makefile                         # ver Sección 12
├─ docker-compose.yml
├─ .editorconfig
├─ .gitignore
├─ .env.example
├─ backend/
│  ├─ pyproject.toml
│  ├─ alembic.ini
│  ├─ src/
│  │  └─ actas/
│  │     ├─ __init__.py
│  │     ├─ main.py                 # FastAPI app + lifespan
│  │     ├─ settings.py             # pydantic-settings
│  │     ├─ db.py                   # engine, session, RLS helpers
│  │     ├─ deps.py                 # dependencies de FastAPI
│  │     ├─ auth/                   # login, JWT, password hashing
│  │     ├─ tenancy/                # current_user, current_org, RLS
│  │     ├─ organizaciones/         # modelos + repos + routes
│  │     ├─ organos/
│  │     ├─ reuniones/
│  │     ├─ grabaciones/            # upload S3, presigned URLs
│  │     ├─ transcripciones/
│  │     ├─ documentos/
│  │     ├─ acuerdos/
│  │     ├─ reportes/
│  │     ├─ pipeline/               # workers
│  │     │  ├─ transcribe.py
│  │     │  ├─ diarize.py
│  │     │  ├─ rag.py
│  │     │  ├─ generate.py
│  │     │  └─ extract_acuerdos.py
│  │     ├─ storage/                # cliente S3
│  │     ├─ email/                  # envío al secretario
│  │     └─ audit/                  # bitácora
│  ├─ migrations/                   # Alembic
│  └─ tests/
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ tsconfig.json
│  ├─ index.html
│  └─ src/
│     ├─ main.tsx
│     ├─ App.tsx
│     ├─ router.tsx
│     ├─ api/                        # cliente HTTP + react-query hooks
│     ├─ auth/
│     ├─ pages/
│     │  ├─ Login.tsx
│     │  ├─ Inicio.tsx
│     │  ├─ Reuniones.tsx
│     │  ├─ ReunionDetalle.tsx
│     │  ├─ Acuerdos.tsx
│     │  ├─ Reportes.tsx
│     │  └─ Organizaciones.tsx
│     ├─ components/                 # Card, Pill, Btn, Sidebar, Topbar, ...
│     └─ styles/
├─ infra/
│  ├─ Dockerfile.backend
│  ├─ Dockerfile.frontend
│  └─ Dockerfile.worker
└─ .github/workflows/
   └─ ci.yml
```

---

## 6. Modelo de datos

PostgreSQL 16. Multi-tenant por `organizacion_id` en toda tabla con datos de cliente. **Row-Level Security activada** y políticas por sesión que filtran por `current_org`.

```sql
-- ---------- Extensiones ----------
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- ---------- Organización (tenant) ----------
CREATE TABLE organizacion (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sigla         TEXT NOT NULL UNIQUE,
  nombre        TEXT NOT NULL,
  afiliados     INT,
  activa        BOOLEAN NOT NULL DEFAULT TRUE,
  creada_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Usuario y acceso ----------
CREATE TYPE rol_enum AS ENUM ('administrador', 'operario');

CREATE TABLE usuario (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  correo          TEXT NOT NULL UNIQUE,
  nombre          TEXT NOT NULL,
  hash_password   TEXT NOT NULL,
  activo          BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE acceso_usuario_organizacion (
  usuario_id        UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  organizacion_id   UUID NOT NULL REFERENCES organizacion(id) ON DELETE CASCADE,
  rol               rol_enum NOT NULL,
  PRIMARY KEY (usuario_id, organizacion_id)
);

-- ---------- Estructura organizacional ----------
CREATE TYPE tipo_organo_enum AS ENUM ('junta_directiva', 'comite');

CREATE TABLE organo (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organizacion_id   UUID NOT NULL REFERENCES organizacion(id) ON DELETE CASCADE,
  nombre            TEXT NOT NULL,                -- "Junta Directiva", "Comité de Crédito"
  tipo              tipo_organo_enum NOT NULL,
  UNIQUE (organizacion_id, nombre)
);

CREATE TABLE miembro (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organo_id   UUID NOT NULL REFERENCES organo(id) ON DELETE CASCADE,
  nombre      TEXT NOT NULL,
  cargo       TEXT NOT NULL,                       -- Presidencia, Secretaría, Tesorería, ...
  activo      BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------- Reunión y materiales ----------
CREATE TYPE reunion_estado_enum AS ENUM ('programada', 'procesando', 'en_revision', 'aprobada');

CREATE TABLE reunion (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organizacion_id   UUID NOT NULL REFERENCES organizacion(id),
  organo_id         UUID NOT NULL REFERENCES organo(id),
  tipo              TEXT NOT NULL,                -- "Sesión Ordinaria" / "Extraordinaria"
  fecha             DATE NOT NULL,
  hora_inicio       TIME,
  hora_fin          TIME,
  modalidad         TEXT,                          -- "Virtual · Teams" / "Presencial"
  numero_acta       INT,
  estado            reunion_estado_enum NOT NULL DEFAULT 'programada',
  creada_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE grabacion (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reunion_id          UUID NOT NULL REFERENCES reunion(id) ON DELETE CASCADE,
  storage_uri         TEXT NOT NULL,               -- s3://bucket/key
  duracion_segundos   INT,
  bytes               BIGINT,
  subido_en           TIMESTAMPTZ NOT NULL DEFAULT now(),
  borrado_en          TIMESTAMPTZ                  -- política de retención
);

CREATE TABLE transcripcion (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reunion_id    UUID NOT NULL REFERENCES reunion(id) ON DELETE CASCADE,
  texto_plano   TEXT NOT NULL,
  modelo        TEXT NOT NULL,                     -- "whisper-large-v3"
  generada_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE segmento_transcripcion (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transcripcion_id  UUID NOT NULL REFERENCES transcripcion(id) ON DELETE CASCADE,
  inicio_seg        NUMERIC(10,3) NOT NULL,
  fin_seg           NUMERIC(10,3) NOT NULL,
  hablante_etiqueta TEXT NOT NULL,                 -- "Hablante 1" o id
  miembro_id        UUID REFERENCES miembro(id),   -- nullable: atribución sugerida
  texto             TEXT NOT NULL,
  confianza         NUMERIC(5,4)
);

-- ---------- Documentos generados ----------
CREATE TYPE doc_tipo_enum AS ENUM ('resumen', 'acta', 'minuta');
CREATE TYPE doc_estado_enum AS ENUM ('borrador', 'en_revision', 'aprobado');

CREATE TABLE documento (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reunion_id      UUID NOT NULL REFERENCES reunion(id) ON DELETE CASCADE,
  tipo            doc_tipo_enum NOT NULL,
  estado          doc_estado_enum NOT NULL DEFAULT 'borrador',
  contenido       JSONB NOT NULL,                  -- ver Sección 8 para esquema del acta
  version         INT NOT NULL DEFAULT 1,
  generado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),
  aprobado_por    UUID REFERENCES usuario(id),
  aprobado_en     TIMESTAMPTZ,
  UNIQUE (reunion_id, tipo)
);

-- ---------- Acuerdos ----------
CREATE TYPE acuerdo_estado_enum AS ENUM ('pendiente', 'en_proceso', 'completado');

CREATE TABLE acuerdo (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reunion_id            UUID NOT NULL REFERENCES reunion(id) ON DELETE CASCADE,
  organizacion_id       UUID NOT NULL REFERENCES organizacion(id),
  codigo                TEXT NOT NULL,             -- "ASETRACO·142-01"
  texto                 TEXT NOT NULL,
  responsable           TEXT,
  fecha_limite          DATE,
  estado                acuerdo_estado_enum NOT NULL DEFAULT 'pendiente',
  firme                 BOOLEAN NOT NULL DEFAULT FALSE,
  objetivo_estrategico  TEXT,
  creado_en             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE comentario_acuerdo (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  acuerdo_id    UUID NOT NULL REFERENCES acuerdo(id) ON DELETE CASCADE,
  usuario_id    UUID NOT NULL REFERENCES usuario(id),
  texto         TEXT NOT NULL,
  creado_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- RAG ----------
CREATE TABLE plantilla_legal (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organizacion_id   UUID REFERENCES organizacion(id),     -- NULL = global solidarista
  nombre            TEXT NOT NULL,
  contenido         TEXT NOT NULL,
  activa            BOOLEAN NOT NULL DEFAULT TRUE,
  creada_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE rag_chunk (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organizacion_id   UUID REFERENCES organizacion(id),     -- NULL = recursos globales
  fuente            TEXT NOT NULL,                         -- 'plantilla' | 'acta_historica'
  documento_id      UUID,                                  -- referencia opcional
  texto             TEXT NOT NULL,
  embedding         vector(1536),
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX rag_chunk_emb_idx ON rag_chunk USING hnsw (embedding vector_cosine_ops);

-- ---------- Auditoría ----------
CREATE TABLE auditoria (
  id                BIGSERIAL PRIMARY KEY,
  organizacion_id   UUID,
  usuario_id        UUID,
  accion            TEXT NOT NULL,                         -- "documento.aprobar", "reunion.crear", ...
  entidad           TEXT NOT NULL,
  entidad_id        UUID,
  metadata          JSONB,
  ocurrida_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX auditoria_org_fecha_idx ON auditoria (organizacion_id, ocurrida_en DESC);
```

### Row-Level Security (RLS)

Cada tabla con `organizacion_id` activa RLS y aplica una política que compara con la variable de sesión `app.current_organization_id`. La aplicación setea esa variable al inicio de cada request:

```sql
ALTER TABLE reunion ENABLE ROW LEVEL SECURITY;
CREATE POLICY reunion_tenant_isolation ON reunion
  USING (organizacion_id = current_setting('app.current_organization_id')::UUID);
```

El backend ejecuta `SET LOCAL app.current_organization_id = '<uuid>'` al iniciar la transacción de cada request autenticado.

---

## 7. API — endpoints principales

Todos los endpoints requieren `Authorization: Bearer <jwt>` salvo `auth/*`. Las respuestas usan JSON con `camelCase` o `snake_case` consistente — **elegir uno y mantenerlo**. Recomendación: `camelCase` en el cable, `snake_case` en Python.

| Método | Path | Descripción |
|---|---|---|
| POST | `/auth/login` | `{ correo, password }` → `{ accessToken, refreshToken, user }` |
| POST | `/auth/refresh` | `{ refreshToken }` → `{ accessToken }` |
| POST | `/auth/logout` | Invalida el refresh token |
| GET | `/me` | Perfil del usuario + accesos por organización |
| GET | `/organizaciones` | Lista (filtrado por accesos del usuario) |
| POST | `/organizaciones` | Crear (solo administrador) |
| GET | `/organizaciones/{id}` | Detalle |
| GET | `/organizaciones/{id}/organos` | Junta y comités |
| POST | `/organizaciones/{id}/organos` | Crear órgano |
| GET | `/reuniones` | Filtros: `?organizacionId=…&organoId=…&desde=…&estado=…` |
| POST | `/reuniones` | Programar reunión |
| GET | `/reuniones/{id}` | Detalle (incluye documentos, transcripción si existe) |
| PATCH | `/reuniones/{id}` | Actualizar metadatos |
| POST | `/reuniones/{id}/grabacion` | Subir audio (multipart) — encola el pipeline |
| GET | `/reuniones/{id}/documentos` | Los tres documentos |
| GET | `/reuniones/{id}/transcripcion` | Transcripción + segmentos por hablante |
| GET | `/documentos/{id}` | Contenido |
| PATCH | `/documentos/{id}` | Editar (solo si estado `borrador` o `en_revision`) |
| POST | `/documentos/{id}/enviar-a-revision` | Envía al secretario por correo |
| POST | `/documentos/{id}/aprobar` | Cambia a `aprobado`; bloquea ediciones |
| GET | `/acuerdos` | Filtros: `?organizacionId=…&estado=…&responsable=…` |
| GET | `/acuerdos/{id}` | Detalle |
| PATCH | `/acuerdos/{id}` | Actualizar estado, responsable, etc. |
| POST | `/acuerdos/{id}/comentarios` | Agregar comentario |
| GET | `/reportes/asistencia` | Stats agregadas |
| GET | `/reportes/participacion` | Stats por hablante |
| GET | `/reportes/tiempo` | Duración promedio por organización / órgano |
| GET | `/healthz` | Liveness |
| GET | `/readyz` | Readiness (db + redis + s3) |

### Códigos de error

- `400` validación; `401` no autenticado; `403` sin acceso a la organización; `404` no existe; `409` conflicto de estado (p. ej. aprobar un documento ya aprobado); `422` cuerpo malformado; `500` error inesperado.

---

## 8. Pipeline de inteligencia artificial

### Flujo del worker

Cuando se sube una grabación, la API guarda el archivo en S3 y encola un job `procesar_reunion(reunion_id)`. El worker ejecuta secuencialmente:

```python
def procesar_reunion(reunion_id: UUID) -> None:
    # 1. Descargar audio de S3 a tmpfile
    audio_path = storage.download(reunion.grabacion.storage_uri)

    # 2. Transcripción + diarización (auto-hospedado)
    transcript = whisperx.transcribe(audio_path, language="es")
    diarized   = whisperx.diarize(transcript, audio_path)
    save_transcripcion(reunion_id, diarized)

    # 3. RAG: recuperar plantilla legal + actas históricas relevantes
    contexto = rag.retrieve(
        organizacion_id=reunion.organizacion_id,
        organo=reunion.organo,
        k=8,
    )

    # 4. Generación con LLM (salida estructurada)
    documentos = llm.generate_documentos(
        transcripcion=diarized,
        contexto_rag=contexto,
        organo=reunion.organo,
        miembros=reunion.organo.miembros,
    )
    save_documentos(reunion_id, documentos)

    # 5. Extracción de acuerdos del acta estructurada
    save_acuerdos(reunion_id, documentos["acta"]["acuerdos"])

    # 6. Cambio de estado y notificación
    set_estado(reunion_id, "en_revision")
    email.enviar_a_secretario(reunion_id)
```

### Esquema de salida del acta (JSON)

El LLM produce el acta en formato estructurado para que pueda guardarse en el modelo de datos y renderizarse en la UI sin reescritura:

```json
{
  "encabezado": {
    "organizacion": "ASETRACO",
    "organo": "Junta Directiva",
    "tipo": "Sesión Ordinaria",
    "numero": 142,
    "fecha": "2026-05-19",
    "hora_inicio": "17:05",
    "hora_fin": "18:48",
    "modalidad": "Virtual · Microsoft Teams"
  },
  "asistencia": {
    "presentes": [{"miembro_id": "...", "cargo": "Presidencia", "nombre": "..."}],
    "ausentes":  [{"miembro_id": "...", "cargo": "Vocal III",   "nombre": "...", "justificacion": "..."}],
    "quorum_verificado": true
  },
  "articulos": [
    {"numero": "I", "titulo": "Comprobación del quórum", "contenido": "..."},
    {"numero": "II", "titulo": "Aprobación del acta anterior", "contenido": "..."}
  ],
  "acuerdos": [
    {
      "codigo_interno": "142-01",
      "texto": "Aprobar el otorgamiento del crédito ...",
      "responsable": "Luis Fernando Acuña",
      "fecha_limite": "2026-05-30",
      "firme": true
    }
  ],
  "cierre": {"hora": "18:48", "nota": "Sin más asuntos que tratar..."},
  "firmantes": {"presidencia": "...", "secretaria": "..."}
}
```

El modelo se obliga a producir este esquema usando JSON mode / structured outputs del SDK del LLM. Toda salida inválida se reintenta una vez; si vuelve a fallar, la reunión queda en estado `procesando` con un error visible para revisión manual.

### Prompts (estructura)

Tres prompts separados, uno por documento, ejecutados en paralelo. Cada prompt recibe: (a) la transcripción con hablantes; (b) los chunks recuperados del RAG; (c) los miembros del órgano; (d) instrucciones específicas del tipo de documento. Los prompts viven versionados en `backend/src/actas/pipeline/prompts/` como archivos `.md` para que se puedan revisar e iterar sin tocar código.

### RAG

- **Qué se indexa:** la plantilla legal del acta solidarista (Bonsai la entrega en Fase 0) y las 20+ actas históricas aprobadas (también de Bonsai). Cada documento se chunkea en pasajes de ~500 tokens con overlap.
- **Cómo se indexa:** `text-embedding-3-small` (1536 dim) → `pgvector` con índice HNSW sobre `cosine`.
- **Cómo se recupera:** búsqueda híbrida: vector + filtro por `organizacion_id` (cuando aplique) y por `organo`. Top k = 8.
- **Por qué `pgvector` y no un servicio aparte:** menor superficie operativa para un equipo pequeño; el volumen no justifica un Pinecone/Weaviate.

### Control de calidad

- Cada generación registra: tokens consumidos, latencia, modelo, versión del prompt. Va a `auditoria`.
- Métrica viva: distancia de edición entre el documento generado y el documento aprobado por el secretario. Se reporta en la sección de Reportería.
- Spike de validación de Fase 4 (Sección 14): se procesan las 20+ actas históricas y se mide accuracy contra las actas reales.

---

## 9. Seguridad y cumplimiento

- **Cifrado en tránsito:** TLS obligatorio en todos los ambientes. HSTS en producción.
- **Cifrado en reposo:** la base de datos cifrada por la nube; el almacenamiento de objetos con SSE.
- **Contraseñas:** `bcrypt` (cost 12) con sal por usuario; nunca en logs ni en respuestas.
- **JWT:** acceso 60 min; refresh 7 días; rotación del refresh en cada uso (token reuse detection).
- **Acceso:** dos roles (administrador / operario), alcance por organización. Sin acceso compartido entre organizaciones salvo para usuarios con `acceso_usuario_organizacion` explícito.
- **DPA:** contrato firmado con el proveedor del LLM con retención cero, antes de procesar datos reales.
- **Datos sensibles:** el audio no sale de infraestructura controlada (Plan A). Solo el texto va al LLM.
- **Retención:** audio cifrado, eliminable una vez aprobada el acta (política configurable por organización). Transcripción se conserva.
- **Auditoría:** toda acción que cambia estado (crear reunión, generar documento, aprobar, mover acuerdo) queda en `auditoria` con `usuario_id`, `metadata`.
- **Aislamiento multi-tenant:** Row-Level Security en PostgreSQL como segunda barrera frente a errores de aplicación.
- **PRODHAB:** cumplimiento con la Ley 8968. Política de privacidad y registro de base de datos antes de pasar a producción.

---

## 10. Convenciones de código y flujo de trabajo

### Python (backend)

- `ruff` + `black`, ambos vía pre-commit.
- Anotaciones de tipo obligatorias en funciones públicas (`mypy --strict` como objetivo, pragmático en el día 1).
- `snake_case` para variables, funciones y módulos; `PascalCase` para clases.
- Funciones cortas, una responsabilidad. Excepciones de dominio en `errors.py` por módulo.
- Repos en `repos/` (acceso a BD); routes en `routes/` (FastAPI); servicios en `services/` (lógica de dominio).

### TypeScript (frontend)

- ESLint + Prettier (`@typescript-eslint/strict`).
- `camelCase`; componentes en `PascalCase`.
- Tipos compartidos con el backend generados desde la spec de OpenAPI de FastAPI (`openapi-typescript`).
- Estado del servidor con TanStack Query; estado local con `useState` / `useReducer` (sin Redux salvo necesidad real).
- Componentes pequeños, sin lógica de fetch dentro — todo el fetch va por hooks `useX()` en `api/`.

### Git

- **Trunk-based con ramas cortas.** Rama: `feature/F0-02-crear-repos`, `fix/F1-04-stt-latencia`. Los IDs vienen del tracker (Sección 14).
- Commits convencionales: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`.
- PRs revisados por al menos una persona; CI verde antes de merge.
- `main` siempre desplegable.

### Definición de "hecho"

Una tarea está hecha cuando:

1. Tiene pruebas que pasan.
2. Pasó revisión de código.
3. Está desplegada en el ambiente de pruebas.
4. La documentación (en código o en el repo) se actualizó.

---

## 11. Variables de entorno

`.env.example` en el repo. Nada de secretos en Git.

```bash
# ---------- App ----------
APP_ENV=development                     # development | staging | production
APP_BASE_URL=http://localhost:5173
API_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO

# ---------- Base de datos ----------
DATABASE_URL=postgresql+asyncpg://actas:actas@db:5432/actas

# ---------- Redis (cola) ----------
REDIS_URL=redis://redis:6379/0

# ---------- Almacenamiento de objetos ----------
S3_ENDPOINT=http://minio:9000
S3_BUCKET=actas-audio
S3_REGION=us-east-1
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123

# ---------- JWT ----------
JWT_SECRET=cambiar-en-produccion-32-chars-min
JWT_ALG=HS256
JWT_TTL_MIN=60
JWT_REFRESH_TTL_DAYS=7

# ---------- LLM (Plan A) ----------
ANTHROPIC_API_KEY=                       # requerido en staging/prod
LLM_MODEL=claude-3-5-sonnet-latest
LLM_TEMPERATURE=0.2
LLM_MAX_RETRIES=2

# ---------- Embeddings ----------
EMBEDDING_PROVIDER=openai                # openai | local
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536

# ---------- Whisper / WhisperX ----------
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cpu                       # cpu en dev; cuda en prod
HUGGINGFACE_TOKEN=                       # para el modelo de diarización de pyannote

# ---------- SMTP (envío al secretario) ----------
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USER=
SMTP_PASS=
SMTP_FROM=actas@coreintelhub.com

# ---------- Frontend ----------
VITE_API_BASE_URL=http://localhost:8000
```

---

## 12. Comandos clave (Makefile sugerido)

```makefile
# Levanta toda la pila en local
dev:
	docker compose up --build

# Migraciones
migrate:
	docker compose exec api alembic upgrade head
migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(m)"

# Seeds de desarrollo (datos de ejemplo del demo)
seed:
	docker compose exec api python -m actas.cli seed

# Tests
test-back:
	docker compose exec api pytest -q
test-front:
	cd frontend && npm run test
test-e2e:
	cd frontend && npm run test:e2e

# Lint y formato
lint:
	docker compose exec api ruff check . && docker compose exec api black --check .
	cd frontend && npm run lint
fmt:
	docker compose exec api ruff check --fix . && docker compose exec api black .
	cd frontend && npm run fmt

# Generar tipos de TypeScript desde OpenAPI del backend
types:
	cd frontend && npm run gen:types
```

---

## 13. Pruebas y validación de precisión

### Pirámide

- **Unit** (pytest, Vitest): lógica pura — validación de prompts, parseo de salida estructurada, formatters, hooks.
- **Integration** (pytest con BD efímera): repos contra Postgres real (testcontainers), endpoints con cliente HTTP.
- **End-to-end** (Playwright): flujos críticos — login, subir grabación de muestra, ver documentos generados, aprobar acta, mover acuerdo.

### Spike de validación de precisión (Fase 4)

Ver Sección 13 del Plan Técnico extendido. Resumen operativo:

1. Conjunto de validación: ≥20 actas históricas reales de Bonsai + sus grabaciones.
2. El sistema procesa las grabaciones; se comparan los documentos generados con los aprobados.
3. Métricas: % de actas listas con ediciones menores; tasa de error en datos críticos (nombres, montos, fechas, acuerdos).
4. Umbral mínimo aceptable acordado por escrito con Bonsai antes del spike.
5. El conjunto queda como prueba de regresión.

---

## 14. Plan de fases y sprints (resumen)

16 semanas, 6 fases. El detalle por tarea con responsables y fechas está en `Pipeline Seguimiento - Plataforma Actas Solidaristas.xlsx` (47 tareas, IDs `F0-XX` … `F5-XX`).

| Fase | Semanas | Foco |
|---|---|---|
| Fase 0 | 1–2 | Habilitación: repos, ambientes, CI, esquema de BD, recibir muestras, DPA |
| Fase 1 | 3–6 | Canal núcleo de IA: STT + diarización + RAG + generación |
| Fase 2 | 7–9 | Aplicación web: auth, listado, detalle, revisión, tablero de acuerdos |
| Fase 3 | 10–11 | Reportería y refinamiento de calidad |
| Fase 4 | 12–13 | Spike de validación de precisión |
| Fase 5 | 14–16 | Piloto en producción + captura en vivo |

---

## 15. Fase 0 — qué construir AHORA (lista accionable)

Tareas en orden, todas sin dependencia de Bonsai. Cada una con criterio de aceptación.

### F0-02 — Repositorios y monorepo
- [ ] Estructura de carpetas según Sección 5.
- [ ] `README.md` con instrucciones de arranque local.
- [ ] `.gitignore`, `.editorconfig`, `.env.example`.
- [ ] Licencia (propietaria; "All rights reserved" por ahora).
- **Aceptación:** `git clone` + leer README → cualquier dev nuevo entiende el repo.

### F0-03 — Ambientes locales (docker-compose)
- [ ] Servicios: `db` (postgres 16 con `pgvector`), `redis`, `minio`, `mailhog`, `api`, `worker`, `frontend`.
- [ ] Volúmenes nombrados para persistencia local.
- [ ] Healthchecks en cada servicio.
- **Aceptación:** `make dev` levanta todo; `curl localhost:8000/healthz` → `200`; el frontend abre en `5173`.

### F0-04 — CI mínimo
- [ ] GitHub Actions: `lint` + `test-back` + `test-front` en PRs y `main`.
- [ ] Cache de pip y npm para velocidad.
- **Aceptación:** un PR de prueba ejecuta el workflow y queda verde.

### F0-05 — Esquema inicial de la base de datos
- [ ] Migración Alembic con todas las tablas de la Sección 6.
- [ ] Políticas RLS sobre las tablas con `organizacion_id`.
- [ ] Seed mínimo: una organización de prueba ("ASETRACO"), un órgano (Junta Directiva), tres miembros, un usuario administrador.
- **Aceptación:** `make migrate` aplica todo desde cero sin error; `make seed` puebla los datos; un query con `app.current_organization_id` mal seteado devuelve 0 filas.

### F0-09 — Iniciar DPA con proveedor de IA
- [ ] Solicitar el contrato a Anthropic (Claude for Work / Enterprise) o equivalente.
- [ ] Marcar la cláusula de retención cero.
- **Aceptación:** contrato recibido; lo revisa el abogado de Bonsai.

### Backend scaffolding (puede empezar en paralelo a F0-03)
- [ ] FastAPI app con lifespan, settings (pydantic-settings), logging estructurado.
- [ ] Stack de dependencias en `pyproject.toml`.
- [ ] Endpoints: `GET /healthz`, `GET /readyz` (chequea DB, Redis, S3).
- [ ] Módulo `auth/`: `POST /auth/login` y `POST /auth/refresh` con bcrypt + JWT.
- [ ] Módulo `tenancy/`: dependencia `current_user`, `current_org`; middleware que setea `app.current_organization_id` en cada request.
- [ ] Módulo `organizaciones/`: modelo + repo + endpoints CRUD básicos.
- [ ] Tests unitarios de auth y tenancy.

### Frontend scaffolding (en paralelo)
- [ ] Vite + React 18 + TS + Tailwind configurados.
- [ ] Router con dos rutas iniciales: `/login` y `/`.
- [ ] Pantalla de login funcional contra el backend.
- [ ] Layout principal (Sidebar + Topbar) inspirado en el demo.
- [ ] Cliente HTTP (axios o fetch) + react-query.
- [ ] Generación automática de tipos desde OpenAPI.

### Cosas que NO empezar todavía (Fase 1+, requieren muestras o el DPA)
- El servicio de generación con LLM.
- El indexado del RAG (requiere la plantilla legal de Bonsai).
- El spike de validación (requiere las actas históricas).

---

## 16. Decisiones pendientes y prerrequisitos del cliente

Mientras Claude Code avanza con la Sección 15, estos puntos viven en paralelo (no son blockers de F0-02 … F0-05):

| # | Decisión / entrega | Responsable | Bloquea |
|---|---|---|---|
| 1 | Plantilla legal del acta solidarista | Bonsai | Indexado del RAG (F1-06) |
| 2 | 20+ actas históricas de muestra | Bonsai | Spike de Fase 4 (F4-01) |
| 3 | 3–5 grabaciones reales | Bonsai | PoC de transcripción (F1-01) |
| 4 | Accuracy mínimo aceptable | Carlos + Bonsai | Criterio de aceptación |
| 5 | Plan A vs. Plan B (transferencia de datos) | AXIO + Carlos + abogado | Decisión de stack del LLM |
| 6 | Proveedor de nube y residencia de datos | AXIO + Carlos | Despliegue de staging |
| 7 | Estructura legal de la sociedad AXIO–Coreintelhub | Socios | Contrato con Bonsai |
| 8 | Confirmar número de asociaciones administradas (¿2 o 12?) | Carlos | Dimensionamiento |

---

## 17. Glosario solidarista

- **Asociación solidarista.** Persona jurídica regulada por la Ley 6970 (Costa Rica); reúne a personas trabajadoras de una empresa con aportes propios y patronales, dedicada a fines de bienestar.
- **Junta directiva.** Órgano de dirección de la asociación; típicamente: Presidencia, Secretaría, Tesorería, Fiscalía, Vocales.
- **Comité.** Órgano específico (Crédito, Becas, Vivienda, Vigilancia, Electoral) con funciones delegadas.
- **Acta.** Documento legal que registra una sesión; debe asentarse en el libro de actas; firmada por Presidencia y Secretaría.
- **Acuerdo firme.** Acuerdo que produce efectos legales inmediatos, sin esperar la aprobación de la siguiente acta.
- **Quórum.** Asistencia mínima requerida para sesionar válidamente (estructural) y para aprobar (funcional).
- **Afiliado.** Persona trabajadora asociada.
- **MTSS.** Ministerio de Trabajo y Seguridad Social; lleva el registro de las asociaciones solidaristas.
- **PRODHAB.** Agencia de Protección de Datos de los Habitantes; aplica la Ley 8968.

---

## 18. Cosas que Claude Code debe preguntar antes de codificar

Si algo de lo siguiente no está claro al iniciar una sesión, **preguntar al usuario antes de implementar**:

1. ¿Confirmamos camelCase en JSON del cable (con conversión automática en FastAPI vía `alias_generator`)?
2. ¿Qué nube se usará? (Hasta que se decida, asumir AWS para nombres y SDK; abstraer detrás de interfaces.)
3. ¿Qué proveedor de LLM final? (Por defecto Anthropic Claude; abstraer detrás de `LLMClient` para no atarse.)
4. ¿Se requiere soporte mobile-first? (Por defecto, escritorio primero; el demo ya está pensado así.)
5. Para la diarización, ¿se hará registro previo de voces (enrollment) o se acepta atribución manual de "Hablante 1/2/3"? (Por defecto: etiquetas + corrección manual en la pantalla de transcripción.)
6. ¿La política de retención de audio es por organización (configurable) o global? (Por defecto: por organización, con default razonable.)
7. ¿Bilingüe o solo español? (Por defecto: solo español; UI y prompts.)
8. ¿Versiones específicas de Python/Node a fijar? (Sugerido: Python 3.12, Node 20 LTS.)

---

## 19. Referencias y trazabilidad

- IDs de tareas (`F0-XX`, `F1-XX`, …) referencian filas del Excel `Pipeline Seguimiento - Plataforma Actas Solidaristas.xlsx`. Las ramas de Git usan ese ID.
- Decisiones de arquitectura derivan del Plan Técnico (`.docx`); estrategia comercial del Plan de Acción Estratégico (`.docx`).
- La UI/UX objetivo es la del demo (`Demo Bonsai - Plataforma de Actas Solidaristas.jsx`). La implementación de producción reproduce esos componentes con su versión persistida.

---

*Documento técnico interno de la sociedad AXIO–Coreintelhub. Versión 1.0 · 25 de mayo de 2026. Preparado como contexto inicial para Claude Code en modo plan.*
