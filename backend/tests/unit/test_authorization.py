from uuid import uuid7

import pytest

from app.auth.dependencies import ensure_owner_or_not_found, ensure_role
from app.shared.errors import AppError
from app.users.models import User, UserRole, UserStatus


def make_user(role: UserRole) -> User:
    return User(
        id=uuid7(),
        email=f"{uuid7()}@example.test",
        full_name="Authorization Test",
        password_hash="test-only",
        role=role,
        status=UserStatus.ACTIVE,
    )


def test_general_capability_denial_returns_403() -> None:
    attendee = make_user(UserRole.ATTENDEE)

    with pytest.raises(AppError) as captured:
        ensure_role(attendee, UserRole.ORGANIZER)

    assert captured.value.status_code == 403
    assert captured.value.code == "FORBIDDEN"


def test_id_based_ownership_denial_hides_resource_with_404() -> None:
    organizer = make_user(UserRole.ORGANIZER)

    with pytest.raises(AppError) as captured:
        ensure_owner_or_not_found(owner_id=uuid7(), user=organizer)

    assert captured.value.status_code == 404
    assert captured.value.code == "RESOURCE_NOT_FOUND"


def test_matching_role_and_owner_are_accepted() -> None:
    organizer = make_user(UserRole.ORGANIZER)

    assert ensure_role(organizer, UserRole.ORGANIZER) is organizer
    ensure_owner_or_not_found(owner_id=organizer.id, user=organizer)
