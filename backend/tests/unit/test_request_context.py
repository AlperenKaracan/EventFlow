from uuid import UUID

from app.shared.request_context import normalize_request_id


def test_normalize_request_id_preserves_valid_uuid() -> None:
    request_id = "01989cb0-7423-7a3a-8930-5ed69dd4b854"

    assert normalize_request_id(request_id) == request_id


def test_normalize_request_id_replaces_invalid_value() -> None:
    generated = normalize_request_id("not-a-request-id")

    assert UUID(generated).version == 7
