from contextvars import ContextVar, Token
from uuid import UUID, uuid7

REQUEST_ID_HEADER = "X-Request-ID"
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def normalize_request_id(candidate: str | None) -> str:
    if candidate is not None and len(candidate) <= 64:
        try:
            return str(UUID(candidate))
        except ValueError:
            pass
    return str(uuid7())


def set_request_id(request_id: str) -> Token[str | None]:
    return _request_id.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)


def get_request_id() -> str:
    request_id = _request_id.get()
    return request_id if request_id is not None else str(uuid7())
