from httpx import AsyncClient


async def test_swagger_ui_is_self_hosted_and_renderable_offline(client: AsyncClient) -> None:
    response = await client.get("/docs")

    assert response.status_code == 200
    assert 'src="/docs-assets/swagger-ui-bundle.js"' in response.text
    assert 'src="/docs-initializer.js"' in response.text
    assert 'href="/docs-assets/swagger-ui.css"' in response.text
    assert "cdn.jsdelivr.net" not in response.text

    javascript = await client.get("/docs-assets/swagger-ui-bundle.js")
    initializer = await client.get("/docs-initializer.js")
    stylesheet = await client.get("/docs-assets/swagger-ui.css")

    assert javascript.status_code == 200
    assert javascript.headers["content-type"].split(";", 1)[0] in {
        "application/javascript",
        "text/javascript",
    }
    assert "SwaggerUIBundle" in javascript.text
    assert initializer.status_code == 200
    assert "SwaggerUIBundle" in initializer.text
    assert "'/api/v1/openapi.json'" in initializer.text
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")


async def test_event_openapi_documents_operations_errors_and_cursor_contract(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["openapi"] == "3.1.0"
    paths = document["paths"]
    assert paths["/api/v1/categories"]["get"]["operationId"] == "listCategories"
    assert paths["/api/v1/events"]["get"]["operationId"] == "listPublicEvents"
    assert paths["/api/v1/events"]["post"]["operationId"] == "createEvent"
    assert paths["/api/v1/events/{event_id}"]["get"]["operationId"] == "getPublicEvent"
    assert paths["/api/v1/events/{event_id}"]["patch"]["operationId"] == "updateEvent"
    assert paths["/api/v1/events/{event_id}"]["delete"]["operationId"] == "cancelEvent"
    assert paths["/api/v1/me/events"]["get"]["operationId"] == "listOwnedEvents"
    assert paths["/api/v1/me/events/{event_id}"]["get"]["operationId"] == "getOwnedEvent"

    schemas = document["components"]["schemas"]
    for page_name in ("PublicEventPage", "OwnerEventPage"):
        properties = schemas[page_name]["properties"]
        assert "nextCursor" in properties
        assert "previousCursor" not in properties

    for method, route, statuses in (
        ("post", "/api/v1/events", ("401", "403", "422")),
        ("patch", "/api/v1/events/{event_id}", ("401", "404", "409", "422")),
        ("delete", "/api/v1/events/{event_id}", ("401", "404", "409")),
        ("get", "/api/v1/me/events/{event_id}", ("401", "404")),
    ):
        responses = paths[route][method]["responses"]
        for status_code in statuses:
            schema = responses[status_code]["content"]["application/json"]["schema"]
            assert schema["$ref"] == "#/components/schemas/ErrorEnvelope"
