ARG PYTHON_VER=3

FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:${PYTHON_VER}-slim

# Copy UV from official image
COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /local

# Copy all necessary files for installation
COPY . ./

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
        "org.opencontainers.image.revision"="dev" \
        "org.opencontainers.image.version"="dev"

# Install dependencies and application using UV with frozen lockfile for reproducibility
RUN uv sync --frozen --no-dev --no-editable

ENTRYPOINT [ "avd-cli" ]