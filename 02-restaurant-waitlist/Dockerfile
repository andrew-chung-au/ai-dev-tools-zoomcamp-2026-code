# syntax=docker/dockerfile:1

# ---- Frontend build (Node) ----
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./

# Same-origin API calls once the backend serves this build (see below), so a
# relative base URL works regardless of host/port.
ENV VITE_API_BASE_URL=/api

RUN npm run build \
    && mv .output/public/_shell.html .output/public/index.html

# ---- Backend (Python), serving the frontend build as static files ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS backend
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY backend ./backend
RUN uv sync --frozen --no-dev

COPY --from=frontend-build /app/frontend/.output/public ./frontend_dist

ENV FRONTEND_DIST_DIR=/app/frontend_dist
EXPOSE 8091

CMD ["uv", "run", "--no-sync", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8091"]
