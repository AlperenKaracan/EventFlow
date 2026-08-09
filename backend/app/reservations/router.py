from __future__ import annotations

from logging import Logger
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, RequireRole
from app.idempotency.keys import reservation_create_request_hash, validate_idempotency_key
from app.reservations.rate_limit import enforce_reservation_rate_limit
from app.reservations.schemas import (
    EventAttendeePage,
    ReservationHistoryPage,
    ReservationMutationResponse,
)
from app.reservations.service import (
    cancel_reservation,
    create_reservation,
    get_event_attendee_page,
    get_reservation_history_page,
)
from app.shared.config import Settings
from app.shared.database import get_session
from app.shared.errors import ErrorEnvelope
from app.shared.request_context import get_request_id
from app.users.models import User, UserRole

router = APIRouter(tags=["reservations"])
AttendeeCapability = Annotated[User, Depends(RequireRole(UserRole.ATTENDEE))]


@router.post(
    "/api/v1/events/{event_id}/reservations",
    response_model=ReservationMutationResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    operation_id="createReservation",
    responses={
        401: {"model": ErrorEnvelope, "description": "Bearer token is invalid"},
        403: {"model": ErrorEnvelope, "description": "Attendee capability is required"},
        404: {"model": ErrorEnvelope, "description": "Event is missing"},
        409: {"model": ErrorEnvelope, "description": "Reservation or idempotency conflict"},
        422: {"model": ErrorEnvelope, "description": "Idempotency key is invalid"},
        429: {"model": ErrorEnvelope, "description": "Reservation rate limit exceeded"},
        503: {"model": ErrorEnvelope, "description": "Rate limit dependency unavailable"},
    },
)
async def create_attendee_reservation(
    request: Request,
    event_id: UUID,
    attendee: AttendeeCapability,
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key_header: Annotated[str, Header(alias="Idempotency-Key")],
) -> JSONResponse:
    settings = cast(Settings, request.app.state.settings)
    await enforce_reservation_rate_limit(
        redis=cast(Redis, request.app.state.redis),
        user_id=attendee.id,
        settings=settings,
    )
    idempotency_key = validate_idempotency_key(idempotency_key_header)
    semantic_response = await create_reservation(
        session=session,
        event_id=event_id,
        attendee_id=attendee.id,
        idempotency_key=idempotency_key,
        request_hash=reservation_create_request_hash(event_id=event_id, body={}),
        logger=cast(Logger, request.app.state.logger),
    )
    return JSONResponse(
        status_code=semantic_response.status_code,
        content=semantic_response.materialize_body(current_request_id=UUID(get_request_id())),
        headers=semantic_response.replay_headers(),
    )


@router.get(
    "/api/v1/me/reservations",
    response_model=ReservationHistoryPage,
    response_model_by_alias=True,
    operation_id="listMyReservations",
    responses={
        400: {"model": ErrorEnvelope, "description": "Cursor is invalid"},
        401: {"model": ErrorEnvelope, "description": "Bearer token is invalid"},
        403: {"model": ErrorEnvelope, "description": "Attendee capability is required"},
    },
)
async def my_reservations(
    request: Request,
    attendee: AttendeeCapability,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> ReservationHistoryPage:
    return await get_reservation_history_page(
        session=session,
        attendee_id=attendee.id,
        limit=limit,
        raw_cursor=cursor,
        settings=cast(Settings, request.app.state.settings),
    )


@router.get(
    "/api/v1/events/{event_id}/attendees",
    response_model=EventAttendeePage,
    response_model_by_alias=True,
    operation_id="listEventAttendees",
    responses={
        400: {"model": ErrorEnvelope, "description": "Cursor is invalid"},
        401: {"model": ErrorEnvelope, "description": "Bearer token is invalid"},
        404: {"model": ErrorEnvelope, "description": "Event is missing or inaccessible"},
    },
)
async def event_attendees(
    request: Request,
    event_id: UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> EventAttendeePage:
    return await get_event_attendee_page(
        session=session,
        event_id=event_id,
        organizer_id=current_user.id,
        limit=limit,
        raw_cursor=cursor,
        settings=cast(Settings, request.app.state.settings),
    )


@router.delete(
    "/api/v1/reservations/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="cancelReservation",
    responses={
        401: {"model": ErrorEnvelope, "description": "Bearer token is invalid"},
        404: {"model": ErrorEnvelope, "description": "Reservation is missing or inaccessible"},
        409: {"model": ErrorEnvelope, "description": "Event lifecycle conflict"},
    },
)
async def cancel_attendee_reservation(
    reservation_id: UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    await cancel_reservation(
        session=session,
        reservation_id=reservation_id,
        attendee_id=current_user.id,
    )
