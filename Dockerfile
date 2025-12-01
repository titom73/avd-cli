# ==========================================
# Stage 1: Builder
# ==========================================
ARG PYTHON_VER=3.12
FROM python:${PYTHON_VER}-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# 1. Copy only dependency files first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# 2. Install dependencies only (creates .venv)
# This layer will be cached unless pyproject.toml or uv.lock changes
RUN uv sync --frozen --no-install-project --no-dev

# 3. Copy the rest of the application
COPY . .

# 4. Install the project itself into the existing environment
RUN uv sync --frozen --no-dev --no-editable

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:${PYTHON_VER}-slim AS runtime

WORKDIR /app

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy the virtual environment from the builder stage
# We only need the .venv folder where everything is installed
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"
# Prevent Python from writing pyc files to disc (read-only filesystem friendly)
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure output is flushed directly to terminal
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Build arguments for versioning
ARG VERSION=dev
ARG REVISION=unknown
ARG BUILD_DATE=unknown

LABEL maintainer="Thomas Grimonet <tom@inetsix.net>"
LABEL   "org.opencontainers.image.title"="avd-cli" \
        "org.opencontainers.image.description"="avd-cli container" \
        "org.opencontainers.artifact.description"="A CLI to manage Arista EOS version download" \
        "org.opencontainers.image.source"="https://github.com/titom73/avd-cli" \
        "org.opencontainers.image.url"="https://github.com/titom73/avd-cli" \
        "org.opencontainers.image.documentation"="https://github.com/titom73/avd-cli" \
        "org.opencontainers.image.licenses"="Apache-2.0" \
        "org.opencontainers.image.vendor"="N/A" \
        "org.opencontainers.image.authors"="Thomas Grimonet <tom@inetsix.net>" \
        "org.opencontainers.image.base.name"="python" \
        "org.opencontainers.image.revision"="${REVISION}" \
        "org.opencontainers.image.version"="${VERSION}" \
        "org.opencontainers.image.created"="${BUILD_DATE}"

ENTRYPOINT [ "avd-cli" ]