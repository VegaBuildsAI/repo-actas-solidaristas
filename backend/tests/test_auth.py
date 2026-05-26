import time

import pytest

from actas.auth.service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    hashed = hash_password("mi-contrasena-123")
    assert verify_password("mi-contrasena-123", hashed)
    assert not verify_password("wrong", hashed)


def test_password_different_hashes():
    h1 = hash_password("abc")
    h2 = hash_password("abc")
    assert h1 != h2  # bcrypt salt randomness


def test_access_token_roundtrip():
    token = create_access_token("user-uuid-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-uuid-123"
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    token = create_refresh_token("user-uuid-456")
    payload = decode_token(token)
    assert payload["sub"] == "user-uuid-456"
    assert payload["type"] == "refresh"


def test_token_expiry_fields():
    token = create_access_token("u1")
    payload = decode_token(token)
    assert "exp" in payload
    assert "iat" in payload
    assert payload["exp"] > payload["iat"]


def test_invalid_token_raises():
    import jwt

    with pytest.raises(Exception):
        decode_token("not.a.valid.token")


def test_tampered_token_raises():
    import jwt

    token = create_access_token("u1")
    # Tamper by replacing last char
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(Exception):
        decode_token(tampered)
