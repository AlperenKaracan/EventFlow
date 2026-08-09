from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid7

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from pydantic import BaseModel, ConfigDict

from app.shared.config import Settings
from app.users.models import UserRole

JWT_ALGORITHM = "HS256"
REFRESH_TOKEN_BYTES = 48

_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65_536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


class InvalidAccessTokenError(Exception):
    """Raised without token details so credentials never leak into logs or responses."""


class AccessTokenClaims(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sub: UUID
    role: UserRole
    jti: UUID
    iss: str
    aud: str
    iat: int
    exp: int


@dataclass(frozen=True, slots=True)
class AccessTokenMaterial:
    raw: str
    expires_in_seconds: int


@dataclass(frozen=True, slots=True)
class RefreshTokenMaterial:
    raw: str
    token_hash: str


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        return _password_hasher.verify(encoded_hash, password)
    except InvalidHashError, VerificationError, VerifyMismatchError:
        return False


def password_needs_rehash(encoded_hash: str) -> bool:
    try:
        return _password_hasher.check_needs_rehash(encoded_hash)
    except InvalidHashError:
        return True


DUMMY_PASSWORD_HASH = hash_password("EventFlow-Dummy-Password-For-Timing-Only")


def create_access_token(
    *,
    user_id: UUID,
    role: UserRole,
    settings: Settings,
    now: datetime | None = None,
) -> AccessTokenMaterial:
    issued_at = (now or datetime.now(tz=UTC)).astimezone(UTC)
    expires_at = issued_at + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES)
    expires_in_seconds = settings.ACCESS_TOKEN_TTL_MINUTES * 60
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "jti": str(uuid7()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return AccessTokenMaterial(
        raw=jwt.encode(
            payload,
            settings.JWT_SECRET.get_secret_value(),
            algorithm=JWT_ALGORITHM,
        ),
        expires_in_seconds=expires_in_seconds,
    )


def decode_access_token(raw_token: str, settings: Settings) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            raw_token,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={"require": ["sub", "role", "jti", "iss", "aud", "iat", "exp"]},
        )
        return AccessTokenClaims.model_validate(payload)
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise InvalidAccessTokenError from exc


def create_refresh_token() -> RefreshTokenMaterial:
    raw_token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    return RefreshTokenMaterial(raw=raw_token, token_hash=hash_refresh_token(raw_token))


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_token_family_id() -> UUID:
    return uuid7()
