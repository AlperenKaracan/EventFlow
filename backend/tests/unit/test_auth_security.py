from datetime import UTC, datetime
from uuid import uuid7

import jwt
import pytest

from app.auth.security import (
    InvalidAccessTokenError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    password_needs_rehash,
    verify_password,
)
from app.shared.config import Settings
from app.users.models import UserRole


def test_passwords_use_argon2id_and_verify_without_leaking_plaintext() -> None:
    encoded = hash_password("Strong-Password-123!")

    assert encoded.startswith("$argon2id$")
    assert "Strong-Password-123!" not in encoded
    assert verify_password("Strong-Password-123!", encoded)
    assert not verify_password("wrong-password", encoded)
    assert not password_needs_rehash(encoded)


def test_access_token_round_trip_and_tampering_rejection(settings: Settings) -> None:
    user_id = uuid7()
    material = create_access_token(
        user_id=user_id,
        role=UserRole.ORGANIZER,
        settings=settings,
    )

    claims = decode_access_token(material.raw, settings)
    assert claims.sub == user_id
    assert claims.role is UserRole.ORGANIZER
    assert claims.iss == settings.JWT_ISSUER
    assert claims.aud == settings.JWT_AUDIENCE
    assert material.expires_in_seconds == 900

    payload = jwt.decode(material.raw, options={"verify_signature": False})
    payload["role"] = UserRole.ATTENDEE.value
    tampered = jwt.encode(payload, "attacker-secret-that-is-long-enough", algorithm="HS256")
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(tampered, settings)


def test_expired_access_token_is_rejected(settings: Settings) -> None:
    material = create_access_token(
        user_id=uuid7(),
        role=UserRole.ATTENDEE,
        settings=settings,
        now=datetime(2000, 1, 1, tzinfo=UTC),
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(material.raw, settings)


def test_refresh_token_is_opaque_and_only_sha256_material_is_persistable() -> None:
    material = create_refresh_token()

    assert material.raw != material.token_hash
    assert len(material.raw) >= 64
    assert len(material.token_hash) == 64
    assert material.token_hash == hash_refresh_token(material.raw)
