from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from app.factory import create_app
from app.shared.config import Settings


async def test_expected_http_error_is_logged_with_bounded_structured_fields(
    settings: Settings,
) -> None:
    app = create_app(settings)
    request_id = "01989cb0-7423-7a3a-8930-5ed69dd4b854"

    with patch.object(app.state.logger, "info") as info:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get(
                f"/missing/{request_id}",
                headers={"X-Request-ID": request_id},
            )

    rejected = [
        call.kwargs["extra"]
        for call in info.call_args_list
        if call.kwargs.get("extra", {}).get("event") == "http.request.rejected"
    ]
    assert rejected == [
        {
            "event": "http.request.rejected",
            "method": "GET",
            "route": "unmatched",
            "status": 404,
            "errorCode": "RESOURCE_NOT_FOUND",
        }
    ]
    assert request_id not in rejected[0].values()
    assert response.status_code == 404
