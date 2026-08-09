from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.auth.rate_limit import enforce_login_rate_limit
from app.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.auth.service import authenticate_user, register_user
from app.shared.config import Settings
from app.shared.database import get_session

REFRESH_COOKIE_NAME = "eventflow_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth"

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, *, raw_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=settings.REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    user = await register_user(request=payload, session=session)
    return UserResponse.from_user(user)


@router.post("/login", response_model=LoginResponse, response_model_by_alias=True)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LoginResponse:
    settings = cast(Settings, request.app.state.settings)
    redis = cast(Redis, request.app.state.redis)
    client_ip = request.client.host if request.client is not None else "unknown"
    await enforce_login_rate_limit(
        redis=redis,
        client_ip=client_ip,
        normalized_email=str(payload.email),
        settings=settings,
    )
    authenticated = await authenticate_user(
        request=payload,
        session=session,
        settings=settings,
    )
    _set_refresh_cookie(response, raw_token=authenticated.refresh.raw, settings=settings)
    return LoginResponse(
        access_token=authenticated.access.raw,
        expires_in=authenticated.access.expires_in_seconds,
        user=UserResponse.from_user(authenticated.user),
    )


@router.get("/me", response_model=UserResponse, response_model_by_alias=True)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.from_user(current_user)
