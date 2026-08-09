from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.events.models import EventStatus
from app.events.repository import CategoryRecord, EventRecord


class CategoryResponse(BaseModel):
    id: UUID
    slug: str
    name: str

    @classmethod
    def from_record(cls, record: CategoryRecord) -> CategoryResponse:
        return cls(id=record.id, slug=record.slug, name=record.name)


class PublicEventResponse(BaseModel):
    id: UUID
    category: CategoryResponse
    title: str
    description: str
    location: str
    starts_at: datetime = Field(serialization_alias="startsAt")
    timezone: str
    capacity: int
    reserved_count: int = Field(serialization_alias="reservedCount")
    available_capacity: int = Field(serialization_alias="availableCapacity")

    @classmethod
    def from_record(cls, record: EventRecord) -> PublicEventResponse:
        return cls(
            id=record.id,
            category=CategoryResponse.from_record(record.category),
            title=record.title,
            description=record.description,
            location=record.location,
            starts_at=record.starts_at,
            timezone=record.timezone,
            capacity=record.capacity,
            reserved_count=record.reserved_count,
            available_capacity=record.capacity - record.reserved_count,
        )


class OwnerEventResponse(PublicEventResponse):
    status: EventStatus
    version: int
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    cancelled_at: datetime | None = Field(serialization_alias="cancelledAt")

    @classmethod
    def from_record(cls, record: EventRecord) -> OwnerEventResponse:
        return cls(
            **PublicEventResponse.from_record(record).model_dump(),
            status=record.status,
            version=record.version,
            created_at=record.created_at,
            updated_at=record.updated_at,
            cancelled_at=record.cancelled_at,
        )


class PublicEventPage(BaseModel):
    items: list[PublicEventResponse]
    next_cursor: str | None = Field(serialization_alias="nextCursor")
    has_more: bool = Field(serialization_alias="hasMore")


class OwnerEventPage(BaseModel):
    items: list[OwnerEventResponse]
    next_cursor: str | None = Field(serialization_alias="nextCursor")
    has_more: bool = Field(serialization_alias="hasMore")
