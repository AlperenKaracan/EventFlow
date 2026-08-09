import json
import logging

from app.observability.logging import JsonFormatter
from app.shared.request_context import reset_request_id, set_request_id


def test_json_formatter_emits_required_schema_without_secret_fields() -> None:
    request_id = "01989cb0-7423-7a3a-8930-5ed69dd4b854"
    token = set_request_id(request_id)
    try:
        record = logging.LogRecord(
            name="eventflow",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Request completed",
            args=(),
            exc_info=None,
        )
        record.event = "http.request.completed"
        record.route = "/health"
        record.status = 200

        payload = json.loads(JsonFormatter(service="backend", environment="test").format(record))
    finally:
        reset_request_id(token)

    assert payload["level"] == "INFO"
    assert payload["service"] == "backend"
    assert payload["environment"] == "test"
    assert payload["requestId"] == request_id
    assert payload["event"] == "http.request.completed"
    assert payload["route"] == "/health"
    assert "authorization" not in payload
    assert "password" not in payload
