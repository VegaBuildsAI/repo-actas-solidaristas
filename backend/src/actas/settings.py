from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    APP_BASE_URL: str = "http://localhost:5173"
    API_BASE_URL: str = "http://localhost:8000"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+asyncpg://actas:actas@db:5432/actas"

    REDIS_URL: str = "redis://redis:6379/0"

    S3_ENDPOINT: str = "http://minio:9000"
    S3_BUCKET: str = "actas-audio"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str = "minio"
    S3_SECRET_KEY: str = "minio123"

    JWT_SECRET: str = "cambiar-en-produccion-32-chars-min"
    JWT_ALG: str = "HS256"
    JWT_TTL_MIN: int = 60
    JWT_REFRESH_TTL_DAYS: int = 7

    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-3-5-sonnet-latest"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_RETRIES: int = 2

    EMBEDDING_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    WHISPER_MODEL: str = "large-v3"
    WHISPER_DEVICE: str = "cpu"
    HUGGINGFACE_TOKEN: str = ""

    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "actas@coreintelhub.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
