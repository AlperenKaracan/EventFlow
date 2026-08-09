from uuid import UUID

from app.idempotency.responses import SemanticResponse, semantic_error_body


def test_semantic_snapshot_excludes_request_id_and_replay_injects_current_id() -> None:
    original = UUID("01989cb0-7423-7a3a-8930-5ed69dd4b854")
    current = UUID("01989cb0-7423-7a3a-8930-5ed69dd4b855")
    stored = semantic_error_body(code="EVENT_FULL", message="Etkinlik dolu.")
    response = SemanticResponse(
        status_code=409,
        body=stored,
        original_request_id=original,
        replayed=True,
    )

    materialized = response.materialize_body(current_request_id=current)

    assert "requestId" not in stored["error"]
    assert materialized["error"]["requestId"] == str(current)
    assert response.replay_headers() == {
        "Idempotent-Replayed": "true",
        "Idempotency-Original-Request-ID": str(original),
    }


def test_owner_response_has_no_replay_headers() -> None:
    response = SemanticResponse(
        status_code=201,
        body={"id": "reservation-id"},
        original_request_id=UUID("01989cb0-7423-7a3a-8930-5ed69dd4b854"),
        replayed=False,
    )

    assert response.replay_headers() == {}
    assert response.materialize_body(
        current_request_id=UUID("01989cb0-7423-7a3a-8930-5ed69dd4b855")
    ) == {"id": "reservation-id"}
