# Resumen Ejecutivo — Plataforma de Actas Solidaristas
**AXIO–Coreintelhub × Bonsai Asesoría Estratégica**
Fecha: 26 de mayo de 2026 · Semana 1 del proyecto

---

## Estado general

| Fase | Semanas | Estado | Progreso |
|------|---------|--------|----------|
| Fase 0 — Habilitación | Sem. 1–2 | **Completada** | 4/13 tareas críticas ✅ |
| Fase 1 — Canal núcleo de IA | Sem. 3–6 | **En progreso** | 4/10 tareas (40%) |
| Fase 2 — Aplicación web | Sem. 7–9 | No iniciada | 0/8 tareas |
| Fase 3 — Reportería | Sem. 10–11 | No iniciada | 0/5 tareas |

**Tests automatizados:** 19 (17 backend · 2 frontend) · todos en verde.
**Stack operativo:** 7 contenedores Docker levantados con `make dev` · pipeline STT verificado end-to-end.

---

## Lo que está funcionando hoy

### Infraestructura completa (Fase 0)
- **Stack Docker**: `db` (PostgreSQL 16 + pgvector) · `redis` · `minio` · `mailhog` · `api` · `worker` · `frontend` — todos con healthchecks.
- **Base de datos**: 15 tablas · 6 enums · índice HNSW para RAG · Row-Level Security multi-tenant activado en 7 tablas (aislamiento por `organizacion_id`).
- **Auth JWT**: login · refresh · logout · `bcrypt` cost 12 · multi-tenant por organización.
- **CI/CD**: GitHub Actions con 4 jobs paralelos (lint-back · test-back · lint-front · test-front) con caché pip/npm.
- **Seed de desarrollo**: organización ASETRACO · Junta Directiva · 3 miembros · usuario `admin@asetraco.cr`.

### Canal de transcripción (Fase 1 parcial)
- **STT auto-hospedado**: `faster-whisper large-v3` corriendo en el contenedor worker. Modelo cacheado en volumen Docker `/model-cache` (no se re-descarga entre reinicios).
- **Almacenamiento S3**: `StorageClient` sobre MinIO. Upload, download, presigned URLs. Bucket `actas-audio` se auto-crea al inicio.
- **Pipeline async**: `POST /reuniones/{id}/grabacion` → guarda en MinIO → encola job RQ → worker descarga audio → transcribe → guarda `Transcripcion` + `SegmentoTranscripcion` en BD → actualiza estado a `en_revision`.
- **Verificación end-to-end**: audio MP3 en español subido, procesado en 18.7 segundos con `large-v3`, 4 segmentos guardados con timestamps `NUMERIC(10,3)`, confianza por segmento, y `quórum` transcrito correctamente.
- **API reuniones**: `GET/POST /reuniones` · `GET /reuniones/{id}` (detalle con transcripción y segmentos) · `PATCH /reuniones/{id}` · `POST /reuniones/{id}/grabacion`.

---

## Tareas completadas (F1-01 a F1-04)

| ID | Tarea | Completado |
|----|-------|-----------|
| F1-01 | PoC transcripción Whisper en español | 26/05/2026 |
| F1-02 | Servicio de carga de grabación + S3 | 26/05/2026 |
| F1-03 | Cola de trabajos y worker asíncrono | 26/05/2026 |
| F1-04 | Servicio de transcripción auto-hospedado | 26/05/2026 |

---

## Tareas bloqueadas — esperando a Carlos y Bonsai

Las siguientes 6 tareas de Fase 1 no pueden iniciarse sin material externo:

| ID | Tarea | Bloqueante | Responsable |
|----|-------|-----------|-------------|
| F1-05 | Diarización de hablantes (pyannote) | Token HuggingFace + GPU en staging | Carlos / AXIO |
| F1-06 | Indexar plantilla legal en pgvector (RAG) | Plantilla legal del acta solidarista | **Bonsai** |
| F1-07 | Servicio de generación con LLM | DPA firmado con Anthropic + F1-06 | AXIO |
| F1-08 | Generación de los 3 documentos | F1-07 | Coreintelhub |
| F1-09 | Extracción estructurada de acuerdos | F1-08 | Coreintelhub |
| F1-10 | Pruebas E2E con grabaciones de muestra | Grabaciones reales de Bonsai + F1-09 | **Bonsai** |

**Entregables pendientes de Bonsai:**
1. Plantilla legal del acta solidarista (documento Word o PDF) — bloqueante para RAG.
2. 20+ actas históricas aprobadas — bloqueante para spike de precisión (Fase 4).
3. 3–5 grabaciones de reuniones reales — bloqueante para pruebas E2E y validación STT.
4. Confirmación del accuracy mínimo aceptable (definir umbral antes del spike).

**Decisiones pendientes de AXIO + Carlos:**
1. Plan A vs. Plan B — ¿el texto puede salir a la API de Anthropic con DPA, o se necesita LLM auto-hospedado? Decisión define el stack de generación.
2. Proveedor de nube y residencia de datos (AWS / GCP / DigitalOcean Costa Rica).
3. Token de HuggingFace para modelo de diarización `pyannote.audio`.

---

## Riesgos activos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| Bonsai demora en entregar material | Media | Alto — bloquea F1-05..F1-10 y Fase 4 | Carlos hace seguimiento activo; acordar fecha límite |
| Plan B (LLM local) consume semanas extra | Baja-Media | Alto — retrasa Fase 1 y Fase 2 | Resolver DPA pronto; Plan B tiene stub listo |
| GPU no disponible para `large-v3` en staging | Media | Medio — STT lento en CPU | En CPU tarda ~5× más; aceptable para PoC |
| HuggingFace token denegado o modelo requiere licencia | Baja | Medio — bloquea F1-05 | pyannote requiere aceptar términos en HF; gestionar con Carlos |

---

## Próximos pasos (cuando lleguen noticias de Carlos)

**Desbloqueable inmediatamente con token HuggingFace:**
- [ ] F1-05 — Diarización: integrar `WhisperX` + `pyannote.audio`; atribuir segmentos a hablantes; pantalla de corrección manual.

**Desbloqueable con plantilla legal de Bonsai:**
- [ ] F1-06 — RAG: chunkear plantilla en pasajes de ~500 tokens con overlap; generar embeddings `text-embedding-3-small`; indexar en `pgvector` con HNSW.

**Desbloqueable con DPA firmado:**
- [ ] F1-07/F1-08 — Generación con Claude API: prompts en `backend/src/actas/pipeline/prompts/*.md`; salida estructurada JSON (esquema en CLAUDE.md §8); 3 documentos en paralelo.
- [ ] F1-09 — Extracción de acuerdos del JSON estructurado del acta.

**Con todo F1 completo:**
- [ ] F1-10 — Pruebas E2E con grabaciones reales de Bonsai.
- [ ] Iniciar Fase 2 — UI de revisión, tablero de acuerdos, dashboard.

---

## Métricas de calidad del código

| Métrica | Valor |
|---------|-------|
| Tests backend | 17 (auth · tenancy · pipeline) |
| Tests frontend | 2 |
| Cobertura de módulos con tests | auth · tenancy · transcribe pipeline |
| Lint (ruff + black) | Pasando |
| CI/CD | Activo (GitHub Actions) |

---

## Resumen para comunicación con Bonsai

El stack técnico está listo. La plataforma puede hoy mismo:
- Recibir la grabación de una reunión (audio MP3/WAV/M4A).
- Transcribirla automáticamente en español con alta precisión (`large-v3`).
- Guardar la transcripción segmentada con timestamps y confianza.
- Manejar múltiples organizaciones con aislamiento completo de datos.

Lo que falta para generar el primer borrador de acta es el material de Bonsai (plantilla legal + actas históricas + grabaciones) y la firma del DPA con Anthropic. Con eso en mano, el tiempo estimado para tener el primer acta generada automáticamente es de **2–3 semanas de desarrollo**.

---

*Documento interno AXIO–Coreintelhub · Confidencial · v1.0 · 26 de mayo de 2026*
