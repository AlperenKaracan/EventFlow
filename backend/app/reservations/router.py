from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, RequireRole
from app.reservations.schemas import EventAttendeePage, ReservationHistoryPage
from app.reservations.service import get_event_attendee_page, get_reservation_history_page
from app.shared.config import Settings
from app.shared.database import get_session
from app.shared.errors import ErrorEnvelope
from app.users.models import User, UserRole

router = APIRouter(tags=["reservations"])
AttendeeCapability = Annotated[User, Depends(RequireRole(UserRole.ATTENDEE))]


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
