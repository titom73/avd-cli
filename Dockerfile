ARG PYTHON_VER=3.12

FROM python:${PYTHON_VER}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

COPY . .

RUN uv sync --frozen --no-dev --no-editable

FROM python:${PYTHON_VER}-slim AS runtime

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
# Read-only filesystem friendly
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD avd-cli --version || exit 1

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