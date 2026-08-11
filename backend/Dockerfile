FROM ghcr.io/astral-sh/uv:0.10.6 AS uv

FROM python:3.14.3-slim-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini backend/README.md ./
RUN uv sync --frozen --no-dev

FROM python:3.14.3-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN groupadd --gid 10001 eventflow \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin eventflow

COPY --from=builder --chown=10001:10001 /app /app

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["python", "-m", "app.server"]
