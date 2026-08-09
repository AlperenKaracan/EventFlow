import pytest
from pydantic import ValidationError

from app.auth.schemas import RegisterRequest, RegistrationRole
from app.users.models import UserRole


def test_register_request_normalizes_identity_fields() -> None:
    payload = RegisterRequest.model_validate(
        {
            "email": "  USER@Example.COM ",
            "fullName": "  Example User  ",
            "password": "a-secure-password",
            "role": "organizer",
        }
    )

    assert payload.email == "user@example.com"
    assert payload.full_name == "Example User"
    assert payload.role is RegistrationRole.ORGANIZER
    assert payload.role.to_model() is UserRole.ORGANIZER


def test_register_request_rejects_blank_name_after_trimming() -> None:
    with pytest.raises(ValidationError, match="fullName must not be blank"):
        RegisterRequest.model_validate(
            {
                "email": "user@example.com",
                "fullName": "   ",
                "password": "a-secure-password",
                "role": "attendee",
            }
        )
