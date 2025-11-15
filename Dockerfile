ARG PYTHON_VER=3

FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:${PYTHON_VER}-slim

# Copy UV from official image
COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /local

# Copy all necessary files for installation
COPY . ./

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

# Install dependencies and application using UV with frozen lockfile for reproducibility
RUN uv sync --frozen --no-dev --no-editable

ENTRYPOINT [ "avd-cli" ]