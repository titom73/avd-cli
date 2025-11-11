# Docker Usage

This guide explains how to build and use the AVD CLI Docker image for containerized deployments.

## Overview

The AVD CLI Docker image provides a containerized environment for running AVD CLI commands without installing Python or dependencies on your host system. The image is based on Python slim and uses UV for fast dependency management.

## Available Images

AVD CLI images are available from two registries:

```bash
docker pull ghcr.io/titom73/avd-cli:latest
docker pull ghcr.io/titom73/avd-cli:v0.1.0  # Specific version
```

## Building the Image

### Prerequisites

- Docker 20.10 or later
- Docker Buildx (for multi-platform builds)

### Basic Build

Build the image locally for your current platform:

```bash
docker build -t avd-cli:local .
```

### Multi-Platform Build

Build for multiple architectures (AMD64 and ARM64):

```bash
# Set up buildx builder (first time only)
docker buildx create --name avd-builder --use
docker buildx inspect --bootstrap

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t titom73/avd-cli:latest \
  --push \
  .
```

### Build with Specific Python Version

The Dockerfile accepts a build argument for the Python version:

```bash
docker build \
  --build-arg PYTHON_VER=3.11 \
  -t avd-cli:python3.11 \
  .
```

## Using the Docker Image

### Basic Usage

Run AVD CLI commands by mounting your inventory directory:

```bash
docker run --rm \
  -v $(pwd)/inventory:/inventory \
  titom73/avd-cli:latest \
  info /inventory/inventory.yml
```

### Interactive Mode

Start an interactive shell in the container:

```bash
docker run --rm -it \
  -v $(pwd)/inventory:/inventory \
  --entrypoint /bin/bash \
  titom73/avd-cli:latest
```

### Common Commands

=== "Info Command"

    ```bash
    docker run --rm \
      -v $(pwd):/workspace \
      -w /workspace \
      titom73/avd-cli:latest \
      info inventory/inventory.yml
    ```

=== "Validate Command"

    ```bash
    docker run --rm \
      -v $(pwd):/workspace \
      -w /workspace \
      titom73/avd-cli:latest \
      validate inventory/inventory.yml
    ```

=== "Generate Command"

    ```bash
    docker run --rm \
      -v $(pwd):/workspace \
      -w /workspace \
      titom73/avd-cli:latest \
      generate inventory/inventory.yml
    ```

=== "Deploy Command"

    ```bash
    docker run --rm \
      -v $(pwd):/workspace \
      -w /workspace \
      -e AVD_CLI_DRY_RUN=true \
      titom73/avd-cli:latest \
      deploy inventory/inventory.yml
    ```

### Environment Variables

Pass environment variables using the `-e` flag:

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  -e AVD_CLI_DRY_RUN=true \
  -e AVD_CLI_SHOW_DIFF=true \
  titom73/avd-cli:latest \
  deploy inventory/inventory.yml
```

See [Environment Variables](../user-guide/environment-variables.md) for a complete list.

## Docker Compose

Create a `docker-compose.yml` file for easier management:

```yaml
version: '3.8'

services:
  avd-cli:
    image: titom73/avd-cli:latest
    volumes:
      - ./inventory:/workspace/inventory
      - ./configs:/workspace/configs
    working_dir: /workspace
    environment:
      - AVD_CLI_DRY_RUN=${AVD_CLI_DRY_RUN:-false}
      - AVD_CLI_SHOW_DIFF=${AVD_CLI_SHOW_DIFF:-true}
    command: ["--help"]
```

Usage:

```bash
# Run info command
docker compose run --rm avd-cli info inventory/inventory.yml

# Generate configurations
docker compose run --rm avd-cli generate inventory/inventory.yml

# Deploy with dry-run
docker compose run --rm -e AVD_CLI_DRY_RUN=true avd-cli deploy inventory/inventory.yml
```

## Advanced Usage

### Running with SSH Keys

Mount your SSH keys for device authentication:

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -v ~/.ssh:/root/.ssh:ro \
  -w /workspace \
  titom73/avd-cli:latest \
  deploy inventory/inventory.yml
```

!!! warning "Security Note"
    Be cautious when mounting SSH keys. Consider using SSH agent forwarding or Docker secrets for production environments.

### Custom Configuration

Mount a custom configuration file:

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/custom-config.yml:/config/avd-cli.yml:ro \
  -w /workspace \
  titom73/avd-cli:latest \
  generate inventory/inventory.yml
```

### Network Access

For deployment operations, ensure the container can reach your devices:

```bash
# Use host network
docker run --rm \
  --network host \
  -v $(pwd):/workspace \
  -w /workspace \
  titom73/avd-cli:latest \
  deploy inventory/inventory.yml
```

### Continuous Integration

Example GitHub Actions workflow using Docker:

```yaml
name: Generate Configs
on: [push]

jobs:
  generate:
    runs-on: ubuntu-latest
    container:
      image: titom73/avd-cli:latest
    steps:
      - uses: actions/checkout@v5

      - name: Validate inventory
        run: avd-cli validate inventory/inventory.yml

      - name: Generate configurations
        run: avd-cli generate inventory/inventory.yml

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: configs
          path: intended/configs/
```

## Image Details

### Image Layers

The image is built using a multi-stage approach:

1. **UV Stage**: Copies the UV binary from the official image
2. **Final Stage**: Installs dependencies and application

### Installed Components

- Python 3 (slim variant)
- UV package manager
- AVD CLI and all runtime dependencies
- No development dependencies

### Image Size

Typical image size: ~330 MB

- Base Python image: ~130 MB
- AVD CLI + dependencies: ~200 MB

### Security

- Based on official Python slim images
- Regular updates through automated builds
- Scanned for vulnerabilities in CI/CD pipeline

## Additional Resources

- [Dockerfile source](https://github.com/titom73/avd-cli/blob/main/Dockerfile)
- [Docker Hub repository](https://hub.docker.com/r/titom73/avd-cli)
- [GitHub Container Registry](https://github.com/titom73/avd-cli/pkgs/container/avd-cli)
- [Docker documentation](https://docs.docker.com/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
