import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from actas.auth.routes import router as auth_router
from actas.db import get_engine
from actas.me.routes import router as me_router
from actas.organizaciones.routes import router as org_router
from actas.reuniones.routes import router as reuniones_router
from actas.settings import get_settings
from actas.tenancy.middleware import TenantMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Warm up DB connection pool
    engine = get_engine()
    async with engine.connect():
        pass
    logger.info("Database connection pool ready")

    # Check Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        logger.info("Redis ready")
    except Exception as e:
        logger.warning("Redis not reachable at startup: %s", e)

    yield

    await engine.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Plataforma de Actas Solidaristas",
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.APP_BASE_URL, "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TenantMiddleware)

    app.include_router(auth_router)
    app.include_router(me_router)
    app.include_router(org_router)
    app.include_router(reuniones_router)

    @app.get("/healthz", tags=["health"])
    async def healthz():
        return {"status": "ok"}

    @app.get("/readyz", tags=["health"])
    async def readyz():
        checks: dict = {}
        ok = True

        # DB check
        try:
            from sqlalchemy import text

            engine = get_engine()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["db"] = "ok"
        except Exception as e:
            checks["db"] = str(e)
            ok = False

        # Redis check
        try:
            r = aioredis.from_url(settings.REDIS_URL)
            await r.ping()
            await r.aclose()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = str(e)
            ok = False

        # S3 check
        try:
            import boto3
            from botocore.config import Config

            s3 = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                config=Config(connect_timeout=2, read_timeout=2),
            )
            s3.head_bucket(Bucket=settings.S3_BUCKET)
            checks["s3"] = "ok"
        except Exception as e:
            checks["s3"] = str(e)
            # S3 bucket may not exist yet in dev — don't fail readyz for it
            ok = ok

        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=200 if ok else 503,
            content={"status": "ok" if ok else "degraded", "checks": checks},
        )

    return app


app = create_app()
