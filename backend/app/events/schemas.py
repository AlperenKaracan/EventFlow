from __future__ import annotations

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.events.models import EventStatus
from app.events.repository import CategoryRecord, EventRecord


class CategoryResponse(BaseModel):
    id: UUID
    slug: str
    name: str

    @classmethod
    def from_record(cls, record: CategoryRecord) -> CategoryResponse:
        return cls(id=record.id, slug=record.slug, name=record.name)


class EventCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: UUID = Field(alias="categoryId")
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=5000)
    location: str = Field(min_length=1, max_length=255)
    starts_at: datetime = Field(alias="startsAt")
    timezone: str = Field(min_length=1, max_length=64)
    capacity: int = Field(gt=0)

    @field_validator("title", "location", "timezone", mode="after")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be blank")
        return normalized


class EventUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(alias="expectedVersion", gt=0)
    category_id: UUID | None = Field(default=None, alias="categoryId")
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    starts_at: datetime | None = Field(default=None, alias="startsAt")
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    capacity: int | None = Field(default=None, gt=0)

    @field_validator("title", "location", "timezone", mode="after")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be blank")
        return normalized

    @model_validator(mode="after")
    def require_non_null_change(self) -> Self:
        changed_fields = self.model_fields_set - {"expected_version"}
        if not changed_fields:
            raise ValueError("at least one event field must be changed")
        if any(getattr(self, field_name) is None for field_name in changed_fields):
            raise ValueError("event fields must not be null")
        changes_start = "starts_at" in changed_fields
        changes_timezone = "timezone" in changed_fields
        if changes_start != changes_timezone:
            raise ValueError("startsAt and timezone must be changed together")
        return self


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
