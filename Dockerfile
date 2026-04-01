# Stage 1: Build React dashboard
FROM node:20-alpine AS dashboard-builder
WORKDIR /dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY pyproject.toml ./
RUN pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir \
      fastapi uvicorn sqlmodel pydantic "typer[all]" httpx sympy \
      sentence-transformers vaderSentiment scipy rich numpy

# Copy source
COPY probe/ ./probe/
COPY canary_sdk/ ./canary_sdk/
COPY scripts/ ./scripts/

# Copy pre-built dashboard
COPY --from=dashboard-builder /dashboard/dist ./dashboard/dist

# DB lives outside the image in a mounted volume
ENV DB_PATH=/data/probe.db
VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "probe.api:app", "--host", "0.0.0.0", "--port", "8000"]
