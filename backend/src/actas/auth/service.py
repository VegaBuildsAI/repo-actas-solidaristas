from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from actas.settings import get_settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _make_token(payload: dict[str, Any], ttl: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    data = {**payload, "iat": now, "exp": now + ttl}
    return jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    return _make_token({"sub": user_id, "type": "access"}, timedelta(minutes=settings.JWT_TTL_MIN))


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    return _make_token(
        {"sub": user_id, "type": "refresh"}, timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])


def create_tokens(user_id: str) -> tuple[str, str]:
    return create_access_token(user_id), create_refresh_token(user_id)
