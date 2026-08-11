from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.router import router as auth_router
from app.events.router import categories_router, events_router
from app.observability.logging import configure_logging
from app.observability.metrics import EventFlowMetrics
from app.observability.middleware import RequestContextMiddleware
from app.observability.router import router as observability_router
from app.reservations.router import router as reservations_router
from app.shared.config import Settings, load_settings
from app.shared.errors import register_exception_handlers
from app.shared.security_middleware import ExactCORSMiddleware, SecurityHeadersMiddleware

SWAGGER_UI_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>EventFlow API - Swagger UI</title>
    <link rel="stylesheet" href="/docs-assets/swagger-ui.css">
    <link rel="icon" href="/docs-assets/favicon-32x32.png">
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="/docs-assets/swagger-ui-bundle.js"></script>
    <script src="/docs-initializer.js"></script>
  </body>
</html>
"""

SWAGGER_INITIALIZER = """window.ui = SwaggerUIBundle({
  url: '/api/v1/openapi.json',
  dom_id: '#swagger-ui',
  deepLinking: true,
  showExtensions: true,
  showCommonExtensions: true,
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
  layout: 'BaseLayout'
});
"""

DOCS_ASSET_DIRECTORY = Path(__file__).with_name("docs_assets")


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or load_settings()
    logger = configure_logging(
        level=active_settings.LOG_LEVEL,
        environment=active_settings.APP_ENV,
    )
    metrics = EventFlowMetrics(logger=logger)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db_engine = create_async_engine(
            active_settings.DATABASE_URL,
            pool_pre_ping=True,
        )
        redis_client = Redis.from_url(
            active_settings.REDIS_URL,
            decode_responses=True,
        )
        app.state.db_engine = db_engine
        app.state.session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        app.state.redis = redis_client
        try:
            yield
        finally:
            await redis_client.aclose()
            await db_engine.dispose()

    app = FastAPI(
        title="EventFlow API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )
    if active_settings.APP_ENV != "production":
        app.mount(
            "/docs-assets",
            StaticFiles(directory=DOCS_ASSET_DIRECTORY),
            name="docs-assets",
        )

        @app.get("/docs", include_in_schema=False)
        async def swagger_ui_html() -> HTMLResponse:
            return HTMLResponse(SWAGGER_UI_HTML)

        @app.get("/docs-initializer.js", include_in_schema=False)
        async def swagger_ui_initializer() -> Response:
            return Response(SWAGGER_INITIALIZER, media_type="application/javascript")

    app.state.settings = active_settings
    app.state.logger = logger
    app.state.metrics = metrics

    @app.get("/metrics", include_in_schema=False)
    async def prometheus_metrics() -> Response:
        return Response(generate_latest(metrics.registry), media_type=CONTENT_TYPE_LATEST)

    app.add_middleware(
        ExactCORSMiddleware,
        allowed_origins=active_settings.cors_origins,
    )
    app.add_middleware(SecurityHeadersMiddleware, settings=active_settings)
    app.add_middleware(RequestContextMiddleware, logger=logger, metrics=metrics)
    register_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(categories_router)
    app.include_router(events_router)
    app.include_router(reservations_router)
    app.include_router(observability_router)
    return app
