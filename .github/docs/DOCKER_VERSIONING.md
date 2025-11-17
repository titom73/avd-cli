# 🏷️ Docker Image Versioning Strategy

## 📋 Overview

This document explains the unified versioning approach for Docker images in the avd-cli project, ensuring consistency between GitHub Actions workflows and manual local builds.

## 🎯 Goals

1. ✅ **Consistency**: Same version information whether built via CI/CD or locally
2. ✅ **Traceability**: Every image can be traced back to exact source code (git SHA)
3. ✅ **Automation**: Minimal manual intervention required
4. ✅ **Standards**: Follows OCI Image Specification for labels
5. ✅ **Flexibility**: Support for development, release, and custom builds

## 🏗️ Architecture

### Version Information Sources

The Docker image captures three key metadata fields:

| Field | Source | Example | Description |
|-------|--------|---------|-------------|
| **VERSION** | Git tag or `git describe` | `v1.0.0` | Semantic version from git |
| **REVISION** | `git rev-parse HEAD` | `abc123def` | Exact commit SHA |
| **BUILD_DATE** | ISO 8601 timestamp | `2025-11-15T15:30:00Z` | When image was built |

### Dockerfile Build Arguments

```dockerfile
# Build arguments for versioning
ARG VERSION=dev
ARG REVISION=unknown
ARG BUILD_DATE=unknown

# OCI labels
LABEL "org.opencontainers.image.version"="${VERSION}"
LABEL "org.opencontainers.image.revision"="${REVISION}"
LABEL "org.opencontainers.image.created"="${BUILD_DATE}"
```

**Key points:**
- Build args have sensible defaults (`dev`, `unknown`)
- Labels use standard OCI annotation names
- All three fields are mandatory for complete traceability

## 🤖 GitHub Actions Workflow

### Release Workflow (`.github/workflows/release.yml`)

Triggered on tag push (`v*.*.*`):

```yaml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    build-args: |
      VERSION=${{ github.ref_name }}
      REVISION=${{ github.sha }}
      BUILD_DATE=${{ github.event.head_commit.timestamp }}
```

**Flow:**
```
git tag v1.0.0
     ↓
git push origin v1.0.0
     ↓
GitHub Actions trigger
     ↓
Build with VERSION=v1.0.0, REVISION=abc123, BUILD_DATE=2025-11-15T...
     ↓
Push to ghcr.io/titom73/avd-cli:v1.0.0
     ↓
Also tag as ghcr.io/titom73/avd-cli:latest
```

### Advantages

- ✅ Fully automated on tag push
- ✅ Multi-architecture builds (amd64, arm64)
- ✅ Consistent versioning across all builds
- ✅ Published to GitHub Container Registry
- ✅ Version verified against `pyproject.toml`

## 🛠️ Local Build Methods

### Method 1: Makefile (Simplest)

```bash
# Auto-detect version from git
make docker-build

# Custom tag
make docker-build TAG=v1.0.0

# Development build
make docker-build-dev

# Run container
make docker-run ARGS="--help"

# Check version
make docker-version
```

**Implementation:**
```makefile
docker-build:
	@GIT_VERSION=$$(git describe --tags --always --dirty 2>/dev/null || echo "dev"); \
	GIT_SHA=$$(git rev-parse HEAD 2>/dev/null || echo "unknown"); \
	BUILD_DATE=$$(date -u +'%Y-%m-%dT%H:%M:%SZ'); \
	docker build \
		--build-arg VERSION=$$GIT_VERSION \
		--build-arg REVISION=$$GIT_SHA \
		--build-arg BUILD_DATE=$$BUILD_DATE \
		-t avd-cli:$$GIT_VERSION \
		-t avd-cli:latest \
		.
```

### Method 2: Shell Script (Most Flexible)

```bash
# Auto-detect version
./.github/scripts/docker-build.sh

# Custom tag
./.github/scripts/docker-build.sh --tag v1.0.0

# Build and push
./.github/scripts/docker-build.sh --push --registry ghcr.io/titom73

# Development build
./.github/scripts/docker-build.sh --dev
```

**Features:**
- ✅ Colored output
- ✅ Comprehensive help (`--help`)
- ✅ Push to any registry
- ✅ Automatic version detection
- ✅ Error handling

### Method 3: Direct Docker Command

```bash
# Manual build with explicit versions
GIT_VERSION=$(git describe --tags --always --dirty)
GIT_SHA=$(git rev-parse HEAD)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

docker build \
  --build-arg VERSION=$GIT_VERSION \
  --build-arg REVISION=$GIT_SHA \
  --build-arg BUILD_DATE=$BUILD_DATE \
  -t avd-cli:$GIT_VERSION \
  -t avd-cli:latest \
  .
```

## 🔍 Version Detection Logic

### Git Describe Output

`git describe --tags --always --dirty` produces:

| Git State | Output | Description |
|-----------|--------|-------------|
| On exact tag | `v1.0.0` | Clean release |
| After tag | `v1.0.0-5-g1234567` | 5 commits after v1.0.0 |
| Uncommitted changes | `v1.0.0-dirty` | Local modifications |
| No tags | `1234567` | Just commit hash |

### Decision Tree

```
Is --dev flag set?
├─ Yes → VERSION=dev, REVISION=dev
└─ No → Is custom --tag provided?
    ├─ Yes → VERSION=custom_tag
    └─ No → Is git repository?
        ├─ Yes → VERSION=$(git describe)
        └─ No → VERSION=dev (fallback)
```

## 📊 Comparison Matrix

| Feature | GitHub Actions | Makefile | Shell Script | Docker Direct |
|---------|---------------|----------|--------------|---------------|
| **Ease of use** | N/A (automated) | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Flexibility** | Limited | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Version detection** | Git ref name | Auto | Auto | Manual |
| **Multi-arch** | ✅ Yes | ❌ No | ❌ No | ✅ Possible |
| **Registry push** | ✅ Auto | ❌ No | ✅ Yes | ✅ Manual |
| **Error handling** | ✅ Yes | ⭐⭐ | ⭐⭐⭐ | ❌ No |
| **Help/Docs** | N/A | `make help` | `--help` | Manual |

**Recommendation:**
- 🚀 **CI/CD**: Let GitHub Actions handle releases
- 💻 **Local dev**: Use `make docker-build` or `make docker-build-dev`
- 🔧 **Advanced**: Use `.github/scripts/docker-build.sh` for registry push

## 🔬 Inspecting Image Metadata

### Quick Version Check

```bash
# Using make
make docker-version

# Using docker inspect
docker inspect avd-cli:latest \
  --format='Version: {{index .Config.Labels "org.opencontainers.image.version"}}'
```

### Complete Label Inspection

```bash
# Using make
make docker-info

# Using docker inspect + jq
docker inspect avd-cli:latest \
  --format='{{json .Config.Labels}}' | jq .
```

**Example output:**
```json
{
  "maintainer": "Thomas Grimonet <tom@inetsix.net>",
  "org.opencontainers.image.title": "avd-cli",
  "org.opencontainers.image.description": "avd-cli container",
  "org.opencontainers.image.version": "v1.0.0",
  "org.opencontainers.image.revision": "abc123def456789",
  "org.opencontainers.image.created": "2025-11-15T15:30:00Z",
  "org.opencontainers.image.source": "https://github.com/titom73/avd-cli",
  "org.opencontainers.image.licenses": "Apache-2.0"
}
```

## 🎭 Usage Scenarios

### Scenario 1: Development Testing

**Goal**: Quick local build for testing

```bash
# Fast dev build
make docker-build-dev

# Run tests
docker run --rm -it avd-cli:dev --version
```

### Scenario 2: Release Preparation

**Goal**: Build and test before pushing tag

```bash
# Build with release version
make docker-build TAG=v1.0.0

# Test the image
make docker-run ARGS="--help"

# If OK, create and push tag
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will rebuild and publish
```

### Scenario 3: Custom Registry

**Goal**: Push to private registry

```bash
# Login to registry
docker login ghcr.io

# Build and push
./.github/scripts/docker-build.sh \
  --tag v1.0.0 \
  --push \
  --registry ghcr.io/myorg
```

### Scenario 4: CI/CD Release

**Goal**: Automated release

```bash
# Developer creates and pushes tag
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions automatically:
# 1. Verifies version matches pyproject.toml
# 2. Creates GitHub Release
# 3. Publishes to PyPI
# 4. Builds multi-arch Docker image
# 5. Pushes to ghcr.io/titom73/avd-cli:v1.0.0
# 6. Updates ghcr.io/titom73/avd-cli:latest
```

## 🔧 Troubleshooting

### Problem: Image shows "dev" version

**Cause**: Not on a git tag

**Solution:**
```bash
# Check current version
git describe --tags --always

# Create tag if needed
git tag v1.0.0
make docker-build
```

### Problem: Build fails in GitHub Actions

**Cause**: Version mismatch with pyproject.toml

**Solution:**
```bash
# Check versions
grep '^version' pyproject.toml
git describe --tags

# Update pyproject.toml to match tag
# Or create matching tag
```

### Problem: Missing git information

**Cause**: Shallow clone or not in git repo

**Solution:**
```bash
# For shallow clone
git fetch --unshallow

# For non-git directory
./.github/scripts/docker-build.sh --dev
```

## 📚 References

- **Dockerfile**: `Dockerfile`
- **Workflow**: `.github/workflows/release.yml`
- **Makefile**: `Makefile` (Docker targets)
- **Script**: `.github/scripts/docker-build.sh`
- **Documentation**: `.github/DOCKER.md`

### External Standards

- [OCI Image Specification](https://github.com/opencontainers/image-spec/blob/main/annotations.md)
- [Semantic Versioning](https://semver.org/)
- [Docker Build Args](https://docs.docker.com/engine/reference/builder/#arg)
- [Git Describe](https://git-scm.com/docs/git-describe)

## ✅ Best Practices

1. **Always tag releases**: Use semantic versioning (v1.0.0)
2. **Keep pyproject.toml in sync**: Version should match git tag
3. **Use descriptive commits**: Helps with `git describe` output
4. **Test before tagging**: Use `make docker-build TAG=vX.Y.Z` first
5. **Document breaking changes**: In release notes and CHANGELOG
6. **Let CI/CD handle production**: Don't manually push to ghcr.io
7. **Use dev builds locally**: `make docker-build-dev` for quick iteration

## 🚀 Quick Start

```bash
# Development
make docker-build-dev

# Pre-release testing
make docker-build TAG=v1.0.0-beta

# Official release (automated via GitHub Actions)
git tag v1.0.0
git push origin v1.0.0
```

---

**Last Updated**: 2025-11-15  
**Version**: 1.0  
**Maintainer**: Thomas Grimonet <tom@inetsix.net>
