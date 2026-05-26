.PHONY: dev down migrate migrate-create seed \
        test-back test-front test-e2e lint fmt types \
        transcribe worker-logs worker-restart

# ── Stack ──────────────────────────────────────────────────────────────────────

dev:
	docker compose up --build

down:
	docker compose down

# ── DB ─────────────────────────────────────────────────────────────────────────

migrate:
	docker compose exec api alembic upgrade head

migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(m)"

seed:
	docker compose exec api python -m actas.cli seed

# ── Pipeline / F1 ──────────────────────────────────────────────────────────────

# Transcribe a local audio file through the worker container.
# Usage:  make transcribe AUDIO=/path/to/file.wav
# Usage:  make transcribe AUDIO=/path/to/file.mp3 MODEL=tiny
transcribe:
	docker compose exec worker python -m actas.cli transcribe \
		$(AUDIO) \
		$(if $(MODEL),--model $(MODEL),) \
		$(if $(LANG),--language $(LANG),)

worker-logs:
	docker compose logs -f worker

worker-restart:
	docker compose restart worker

# ── Tests ──────────────────────────────────────────────────────────────────────

test-back:
	docker compose exec api pytest -q

test-front:
	cd frontend && npm run test

test-e2e:
	cd frontend && npm run test:e2e

# ── Lint / Format ──────────────────────────────────────────────────────────────

lint:
	docker compose exec api ruff check . && docker compose exec api black --check .
	cd frontend && npm run lint

fmt:
	docker compose exec api ruff check --fix . && docker compose exec api black .
	cd frontend && npm run fmt

# ── OpenAPI types ──────────────────────────────────────────────────────────────

types:
	cd frontend && npm run gen:types
