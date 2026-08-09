FROM node:22.17.1-alpine AS builder

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
WORKDIR /workspace

RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontend/package.json ./frontend/package.json
COPY e2e/package.json ./e2e/package.json
RUN pnpm install --frozen-lockfile --filter @eventflow/frontend...

COPY frontend ./frontend
RUN pnpm --filter @eventflow/frontend build

FROM nginxinc/nginx-unprivileged:1.29.5-alpine AS runtime

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder --chown=101:101 /workspace/frontend/dist /usr/share/nginx/html

USER 101:101
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD ["wget", "--quiet", "--tries=1", "--spider", "http://127.0.0.1:8080/health"]
