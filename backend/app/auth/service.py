from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken
from app.auth.schemas import LoginRequest, RegisterRequest
from app.auth.security import (
    DUMMY_PASSWORD_HASH,
    AccessTokenMaterial,
    RefreshTokenMaterial,
    create_access_token,
    create_refresh_token,
    create_token_family_id,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.shared.config import Settings
from app.shared.errors import AppError
from app.users.models import User, UserStatus


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    user: User
    access: AccessTokenMaterial
    refresh: RefreshTokenMaterial


async def register_user(*, request: RegisterRequest, session: AsyncSession) -> User:
    user = User(
        email=str(request.email),
        full_name=request.full_name,
        password_hash=hash_password(request.password),
        role=request.role.to_model(),
        status=UserStatus.ACTIVE,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            status_code=409,
            code="EMAIL_ALREADY_REGISTERED",
            message="Bu e-posta adresi zaten kayıtlı.",
        ) from exc
    await session.refresh(user)
    return user


async def authenticate_user(
    *, request: LoginRequest, session: AsyncSession, settings: Settings
) -> AuthenticatedSession:
    user = await session.scalar(select(User).where(User.email == str(request.email)))
    encoded_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_valid = verify_password(request.password, encoded_hash)

    if user is None or user.status is not UserStatus.ACTIVE or not password_valid:
        raise AppError(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="E-posta veya parola hatalı.",
        )

    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(request.password)

    now = datetime.now(tz=UTC)
    access = create_access_token(user_id=user.id, role=user.role, settings=settings, now=now)
    refresh = create_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh.token_hash,
            family_id=create_token_family_id(),
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
        )
    )
    await session.commit()
    return AuthenticatedSession(user=user, access=access, refresh=refresh)
