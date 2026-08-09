from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, RequireRole
from app.events.repository import list_active_categories
from app.events.schemas import (
    CategoryResponse,
    EventCreateRequest,
    EventUpdateRequest,
    OwnerEventPage,
    OwnerEventResponse,
    PublicEventPage,
    PublicEventResponse,
)
from app.events.service import (
    cancel_event,
    create_event,
    get_owner_event_detail,
    get_owner_event_page,
    get_public_event_detail,
    get_public_event_page,
    update_event,
)
from app.shared.config import Settings
from app.shared.database import get_session
from app.shared.errors import ErrorEnvelope
from app.users.models import User, UserRole

categories_router = APIRouter(prefix="/api/v1/categories", tags=["categories"])
events_router = APIRouter(tags=["events"])
OrganizerCapability = Annotated[User, Depends(RequireRole(UserRole.ORGANIZER))]


@categories_router.get(
    "",
    response_model=list[CategoryResponse],
    operation_id="listCategories",
)
async def categories(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CategoryResponse]:
    records = await list_active_categories(session)
    return [CategoryResponse.from_record(record) for record in records]


@events_router.get(
    "/api/v1/events",
    response_model=PublicEventPage,
    response_model_by_alias=True,
    operation_id="listPublicEvents",
    responses={400: {"model": ErrorEnvelope, "description": "Cursor is invalid"}},
)
async def public_events(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> PublicEventPage:
    return await get_public_event_page(
        session=session,
        limit=limit,
        raw_cursor=cursor,
        settings=cast(Settings, request.app.state.settings),
    )


@events_router.get(
    "/api/v1/events/{event_id}",
    response_model=PublicEventResponse,
    response_model_by_alias=True,
    operation_id="getPublicEvent",
    responses={404: {"model": ErrorEnvelope, "description": "Event is unavailable"}},
)
async def public_event(
    event_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PublicEventResponse:
    return await get_public_event_detail(session=session, event_id=event_id)


@events_router.post(
    "/api/v1/events",
    response_model=OwnerEventResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    operation_id="createEvent",
    responses={
        401: {"model": ErrorEnvelope, "description": "Bearer token is invalid"},
        403: {"model": ErrorEnvelope, "description": "Organizer capability is required"},
        422: {"model": ErrorEnvelope, "description": "Event validation failed"},
    },
)
async def create_organizer_event(
    payload: EventCreateRequest,
    organizer: OrganizerCapability,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OwnerEventResponse:
    return await create_event(
        payload=payload,
        organizer_id=organizer.id,
        session=session,
    )


@events_router.patch(
    "/api/v1/events/{event_id}",
    response_model=OwnerEventResponse,
    response_model_by_alias=True,
    operation_id="updateEvent",
    responses={
        401: {"model": ErrorEnvelope, "description": "Bearer token is invalid"},
        404: {"model": ErrorEnvelope, "description": "Event is missing or inaccessible"},
        409: {"model": ErrorEnvelope, "description": "Version or lifecycle conflict"},
        422: {"model": ErrorEnvelope, "description": "Event validation failed"},
    },
)
async def update_organizer_event(
    event_id: UUID,
    payload: EventUpdateRequest,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OwnerEventResponse:
    return await update_event(
        event_id=event_id,
        payload=payload,
        organizer_id=current_user.id,
        session=session,
    )


@events_router.delete(
    "/api/v1/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="cancelEvent",
    responses={
        401: {"model": ErrorEnvelope, "description": "Bearer token is invalid"},
        404: {"model": ErrorEnvelope, "description": "Event is missing or inaccessible"},
        409: {"model": ErrorEnvelope, "description": "Version or lifecycle conflict"},
    },
)
async def cancel_organizer_event(
    event_id: UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    expected_version: Annotated[int, Query(alias="expectedVersion", gt=0)],
) -> None:
    await cancel_event(
        event_id=event_id,
        expected_version=expected_version,
        organizer_id=current_user.id,
        session=session,
    )


@events_router.get(
    "/api/v1/me/events",
    response_model=OwnerEventPage,
    response_model_by_alias=True,
    operation_id="listOwnedEvents",
    responses={
        401: {"model": ErrorEnvelope, "description": "Bearer token is invalid"},
        403: {"model": ErrorEnvelope, "description": "Organizer capability is required"},
        400: {"model": ErrorEnvelope, "description": "Cursor is invalid"},
    },
)
async def owner_events(
    request: Request,
    organizer: OrganizerCapability,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> OwnerEventPage:
    return await get_owner_event_page(
        session=session,
        organizer_id=organizer.id,
        limit=limit,
        raw_cursor=cursor,
        settings=cast(Settings, request.app.state.settings),
    )


@events_router.get(
    "/api/v1/me/events/{event_id}",
    response_model=OwnerEventResponse,
    response_model_by_alias=True,
    operation_id="getOwnedEvent",
    responses={
        401: {"model": ErrorEnvelope, "description": "Bearer token is invalid"},
        404: {"model": ErrorEnvelope, "description": "Event is missing or inaccessible"},
    },
)
async def owner_event(
    event_id: UUID,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OwnerEventResponse:
    return await get_owner_event_detail(
        session=session,
        event_id=event_id,
        organizer_id=current_user.id,
    )
