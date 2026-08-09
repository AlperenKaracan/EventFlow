from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import InvalidAccessTokenError, decode_access_token
from app.shared.database import get_session
from app.shared.errors import AppError
from app.users.models import User, UserRole, UserStatus

_bearer_scheme = HTTPBearer(auto_error=False)


def unauthenticated_error() -> AppError:
    return AppError(
        status_code=401,
        code="UNAUTHENTICATED",
        message="Oturum doğrulanamadı.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthenticated_error()

    try:
        claims = decode_access_token(credentials.credentials, request.app.state.settings)
    except InvalidAccessTokenError as exc:
        raise unauthenticated_error() from exc

    user = await session.get(User, claims.sub)
    if user is None or user.status is not UserStatus.ACTIVE or user.role is not claims.role:
        raise unauthenticated_error()
    return user


def ensure_role(user: User, required_role: UserRole) -> User:
    if user.role is not required_role:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Bu işlem için yetkiniz bulunmuyor.",
        )
    return user


def ensure_owner_or_not_found(*, owner_id: UUID, user: User) -> None:
    if owner_id != user.id:
        raise AppError(
            status_code=404,
            code="RESOURCE_NOT_FOUND",
            message="İstenen kaynak bulunamadı.",
        )


class RequireRole:
    def __init__(self, role: UserRole) -> None:
        self.role = role

    async def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        return ensure_role(current_user, self.role)


CurrentUser = Annotated[User, Depends(get_current_user)]
