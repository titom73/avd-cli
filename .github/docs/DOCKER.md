# Docker Build Guide

This document explains how to build and use the avd-cli Docker image with proper versioning.

## 🏷️ Automatic Versioning

The Docker image is automatically versioned using:
- **VERSION**: Git tag or `git describe` output
- **REVISION**: Git commit SHA
- **BUILD_DATE**: ISO 8601 timestamp

These are embedded as OCI labels in the image.

## 🛠️ Building Locally

### Method 1: Using Make (Recommended)

```bash
# Build with auto-detected git version
make docker-build

# Build with custom tag
make docker-build TAG=v1.0.0

# Build development version
make docker-build-dev

# Run the container
make docker-run ARGS="--help"

# Check version info
make docker-version

# Show all labels
make docker-info
```

### Method 2: Using the Shell Script

```bash
# Build with auto-detected version
./.github/scripts/docker-build.sh

# Build with custom tag
./.github/scripts/docker-build.sh --tag v1.0.0

# Build and push to registry
./.github/scripts/docker-build.sh --push --registry ghcr.io/titom73

# Build dev version
./.github/scripts/docker-build.sh --dev

# Show help
./.github/scripts/docker-build.sh --help
```

### Method 3: Using Docker Directly

```bash
# Get version info from git
GIT_VERSION=$(git describe --tags --always --dirty)
GIT_SHA=$(git rev-parse HEAD)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# Build the image
docker build \
  --build-arg VERSION=$GIT_VERSION \
  --build-arg REVISION=$GIT_SHA \
  --build-arg BUILD_DATE=$BUILD_DATE \
  -t avd-cli:$GIT_VERSION \
  -t avd-cli:latest \
  .
```

## 🤖 GitHub Actions (Automated)

The Docker image is automatically built and pushed on tag push via the `release.yml` workflow:

```yaml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    build-args: |
      VERSION=${{ github.ref_name }}
      REVISION=${{ github.sha }}
      BUILD_DATE=${{ github.event.head_commit.timestamp }}
```

**Trigger:**
```bash
git tag v1.0.0
git push origin v1.0.0
```

This will:
1. ✅ Verify version matches `pyproject.toml`
2. 📦 Build and publish to PyPI
3. 🐳 Build multi-arch Docker image (amd64, arm64)
4. 🚀 Push to GitHub Container Registry (ghcr.io)
5. 🏷️ Tag as `v1.0.0` and `latest`

## 🔍 Inspecting Image Metadata

### View Version Information

```bash
docker inspect avd-cli:latest --format='{{index .Config.Labels "org.opencontainers.image.version"}}'
docker inspect avd-cli:latest --format='{{index .Config.Labels "org.opencontainers.image.revision"}}'
docker inspect avd-cli:latest --format='{{index .Config.Labels "org.opencontainers.image.created"}}'
```

### View All Labels

```bash
docker inspect avd-cli:latest --format='{{json .Config.Labels}}' | jq .
```

Example output:
```json
{
  "org.opencontainers.image.title": "avd-cli",
  "org.opencontainers.image.description": "avd-cli container",
  "org.opencontainers.image.version": "v1.0.0",
  "org.opencontainers.image.revision": "abc123def456",
  "org.opencontainers.image.created": "2025-11-15T15:30:00Z",
  "org.opencontainers.image.source": "https://github.com/titom73/avd-cli",
  "org.opencontainers.image.licenses": "Apache-2.0"
}
```

## 🎯 Use Cases

### Development Build

Quick build for testing:
```bash
make docker-build-dev
docker run --rm -it avd-cli:dev --version
```

### Release Build

Official release with version tag:
```bash
git tag v1.0.0
make docker-build
# Or let GitHub Actions handle it automatically
```

### Custom Registry Push

Push to your own registry:
```bash
./.github/scripts/docker-build.sh \
  --tag v1.0.0 \
  --push \
  --registry ghcr.io/yourname
```

## 📋 Version Detection Logic

1. **If `--dev` flag**: Use "dev" for all fields
2. **If custom `--tag`**: Use provided tag as version
3. **If in git repo**: Use `git describe --tags --always --dirty`
4. **Otherwise**: Fallback to "dev"

Examples:
- `v1.0.0` → Clean tag
- `v1.0.0-5-g1234567` → 5 commits after v1.0.0
- `v1.0.0-dirty` → Uncommitted changes
- `1234567` → No tags, just commit hash

## 🔧 Troubleshooting

### Image shows "dev" version

Check if you're on a tagged commit:
```bash
git describe --tags --always
```

If not on a tag:
```bash
git tag v1.0.0
make docker-build
```

### Build fails with version mismatch

Ensure `pyproject.toml` version matches the git tag:
```bash
grep '^version' pyproject.toml
git describe --tags
```

### Check what version will be used

```bash
git describe --tags --always --dirty
```

## 🌐 Multi-Architecture Support

GitHub Actions builds for:
- **linux/amd64** (x86_64)
- **linux/arm64** (Apple Silicon, ARM servers)

Local builds use your machine's architecture by default.

## 📚 References

- [OCI Image Spec](https://github.com/opencontainers/image-spec/blob/main/annotations.md)
- [Docker Build Args](https://docs.docker.com/engine/reference/builder/#arg)
- [Docker Metadata Action](https://github.com/docker/metadata-action)
