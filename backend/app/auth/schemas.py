from __future__ import annotations

from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.users.models import User, UserRole


class RegistrationRole(StrEnum):
    ORGANIZER = "organizer"
    ATTENDEE = "attendee"

    def to_model(self) -> UserRole:
        return UserRole(self.value.upper())


NormalizedPassword = Annotated[str, StringConstraints(min_length=12, max_length=128)]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(alias="fullName", min_length=1, max_length=120)
    password: NormalizedPassword
    role: RegistrationRole

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("full_name", mode="after")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("fullName must not be blank")
        return normalized


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: Annotated[str, StringConstraints(min_length=1, max_length=128)]

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        local_part, separator, domain = normalized.partition("@")
        if (
            separator != "@"
            or not local_part
            or not domain
            or any(character.isspace() for character in normalized)
        ):
            raise ValueError("email must have a valid lookup format")
        return normalized


class UserResponse(BaseModel):
    id: UUID
    email: str = Field(min_length=3, max_length=320)
    full_name: str = Field(serialization_alias="fullName")
    role: RegistrationRole

    @classmethod
    def from_user(cls, user: User) -> UserResponse:
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=RegistrationRole(user.role.value.lower()),
        )


class LoginResponse(BaseModel):
    access_token: str = Field(serialization_alias="accessToken")
    token_type: str = Field(default="Bearer", serialization_alias="tokenType")
    expires_in: int = Field(serialization_alias="expiresIn")
    user: UserResponse
