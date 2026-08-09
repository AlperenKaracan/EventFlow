from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, exists, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

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


def invalid_refresh_token_error() -> AppError:
    return AppError(
        status_code=401,
        code="INVALID_REFRESH_TOKEN",
        message="Oturum yenileme bilgisi geçersiz.",
    )


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


async def _revoke_token_family(
    *, session: AsyncSession, family_id: object, revoked_at: datetime
) -> None:
    await session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
        .execution_options(synchronize_session=False)
    )


async def rotate_refresh_token(
    *, raw_token: str, session: AsyncSession, settings: Settings
) -> AuthenticatedSession:
    from app.auth.security import hash_refresh_token

    now = datetime.now(tz=UTC)
    current = await session.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(raw_token))
        .with_for_update()
    )
    if current is None:
        await session.rollback()
        raise invalid_refresh_token_error()

    if current.revoked_at is not None:
        await _revoke_token_family(
            session=session,
            family_id=current.family_id,
            revoked_at=now,
        )
        await session.commit()
        raise invalid_refresh_token_error()

    if current.expires_at <= now:
        current.revoked_at = now
        await session.commit()
        raise invalid_refresh_token_error()

    user = await session.get(User, current.user_id)
    if user is None or user.status is not UserStatus.ACTIVE:
        await _revoke_token_family(
            session=session,
            family_id=current.family_id,
            revoked_at=now,
        )
        await session.commit()
        raise invalid_refresh_token_error()

    replacement_material = create_refresh_token()
    replacement = RefreshToken(
        user_id=current.user_id,
        token_hash=replacement_material.token_hash,
        family_id=current.family_id,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
    )
    session.add(replacement)
    await session.flush()
    current.revoked_at = now
    current.last_used_at = now
    current.replaced_by_id = replacement.id
    access = create_access_token(user_id=user.id, role=user.role, settings=settings, now=now)
    await session.commit()
    return AuthenticatedSession(user=user, access=access, refresh=replacement_material)


async def revoke_refresh_token_family(*, raw_token: str, session: AsyncSession) -> None:
    from app.auth.security import hash_refresh_token

    token = await session.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(raw_token))
        .with_for_update()
    )
    if token is None:
        await session.rollback()
        return
    await _revoke_token_family(
        session=session,
        family_id=token.family_id,
        revoked_at=datetime.now(tz=UTC),
    )
    await session.commit()


async def cleanup_inactive_refresh_tokens(
    *, session: AsyncSession, settings: Settings, now: datetime | None = None
) -> int:
    cleanup_at = now or datetime.now(tz=UTC)
    revoked_cutoff = cleanup_at - timedelta(days=settings.REFRESH_TOKEN_REVOKED_RETENTION_DAYS)
    active_family_token = aliased(RefreshToken)
    family_has_active_token = exists(
        select(active_family_token.id).where(
            active_family_token.family_id == RefreshToken.family_id,
            active_family_token.revoked_at.is_(None),
            active_family_token.expires_at > cleanup_at,
        )
    )
    result = await session.execute(
        delete(RefreshToken).where(
            ~family_has_active_token,
            (RefreshToken.expires_at <= cleanup_at)
            | (RefreshToken.revoked_at.is_not(None) & (RefreshToken.revoked_at <= revoked_cutoff)),
        )
    )
    await session.commit()
    return int(getattr(result, "rowcount", 0))
