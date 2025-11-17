# 🐳 Docker Quick Start Guide

## 🎯 TL;DR

```bash
# Local development
make docker-build-dev

# Pre-release testing
make docker-build TAG=v1.0.0

# Official release (automated)
git tag v1.0.0
git push origin v1.0.0
# → GitHub Actions builds and publishes automatically
```

## 📦 What Changed?

### Before
- No version information in Docker images
- Manual build with `docker build .`
- Labels always showed "dev"

### After
- ✅ **Automatic versioning** from git tags
- ✅ **Consistent builds** (CI/CD and local)
- ✅ **Full traceability** (version, commit SHA, build date)
- ✅ **OCI-compliant labels**
- ✅ **Multiple build methods** (Make, script, Docker)

## 🚀 Usage

### For Developers

**Daily development:**
```bash
make docker-build-dev
docker run --rm -it avd-cli:dev --help
```

**Test a specific version:**
```bash
make docker-build TAG=v1.0.0
make docker-run ARGS="--version"
```

**Check image version:**
```bash
make docker-version
```

### For Release Managers

**Create a release:**
```bash
# 1. Update version in pyproject.toml
# 2. Commit changes
git commit -am "chore: bump version to 1.0.0"

# 3. Create and push tag
git tag v1.0.0
git push origin v1.0.0

# 4. GitHub Actions will automatically:
#    - Build multi-arch image (amd64, arm64)
#    - Push to ghcr.io/titom73/avd-cli:v1.0.0
#    - Update ghcr.io/titom73/avd-cli:latest
#    - Publish to PyPI
#    - Create GitHub Release
```

### For Advanced Users

**Push to custom registry:**
```bash
./.github/scripts/docker-build.sh \
  --tag v1.0.0 \
  --push \
  --registry ghcr.io/myorg
```

**Build specific version without tag:**
```bash
./.github/scripts/docker-build.sh --tag v1.0.0-beta1
```

## 🔍 Verification

### Check version in running container

```bash
# Run container and check version
docker run --rm avd-cli:latest --version

# Inspect image labels
make docker-version

# Or manually
docker inspect avd-cli:latest \
  --format='{{index .Config.Labels "org.opencontainers.image.version"}}'
```

### View all metadata

```bash
make docker-info

# Or manually with jq
docker inspect avd-cli:latest --format='{{json .Config.Labels}}' | jq .
```

**Expected output:**
```json
{
  "org.opencontainers.image.version": "v1.0.0",
  "org.opencontainers.image.revision": "abc123def456",
  "org.opencontainers.image.created": "2025-11-15T15:30:00Z",
  "org.opencontainers.image.source": "https://github.com/titom73/avd-cli",
  ...
}
```

## 📚 Available Commands

### Makefile Targets

```bash
make docker-build          # Build with git version
make docker-build TAG=v1.0.0  # Build with custom tag
make docker-build-dev      # Build dev version
make docker-run ARGS="--help"  # Run container
make docker-version        # Show version info
make docker-info           # Show all labels
```

### Script Commands

```bash
./.github/scripts/docker-build.sh              # Auto-detect version
./.github/scripts/docker-build.sh --dev        # Dev build
./.github/scripts/docker-build.sh --tag v1.0.0 # Custom version
./.github/scripts/docker-build.sh --push       # Build and push
./.github/scripts/docker-build.sh --help       # Show help
```

## 🔧 How It Works

### Version Detection

```
1. Check if --dev flag → Use "dev"
2. Check if --tag provided → Use provided tag
3. Check git describe → Use git version
4. Fallback → Use "dev"
```

### Git Describe Examples

| Git State | Output | Description |
|-----------|--------|-------------|
| On tag `v1.0.0` | `v1.0.0` | Clean release |
| 5 commits after tag | `v1.0.0-5-g1234567` | Development version |
| Uncommitted changes | `v1.0.0-dirty` | Local modifications |
| No tags | `1234567` | Commit hash only |

### Build Process

```
Local Build                    GitHub Actions
    ↓                               ↓
Get git version               Get tag from push
    ↓                               ↓
docker build                  docker/build-push-action
 --build-arg VERSION=...       build-args:
 --build-arg REVISION=...        VERSION=${{ github.ref_name }}
 --build-arg BUILD_DATE=...      REVISION=${{ github.sha }}
    ↓                               ↓
Tag: avd-cli:version          ghcr.io/titom73/avd-cli:version
Tag: avd-cli:latest           ghcr.io/titom73/avd-cli:latest
```

## 🐛 Troubleshooting

### Problem: Image shows "dev" version

```bash
# Check current git state
git describe --tags --always

# Not on a tag? Create one
git tag v1.0.0
make docker-build
```

### Problem: "fatal: no tags found"

```bash
# Create initial tag
git tag v0.1.0
git push origin v0.1.0

# Or use dev build
make docker-build-dev
```

### Problem: GitHub Actions build fails

```bash
# Check version in pyproject.toml matches tag
grep '^version' pyproject.toml
# Should output: version = "1.0.0"

# Tag should be: v1.0.0
```

### Problem: Can't push to registry

```bash
# Login first
docker login ghcr.io

# Then build and push
./.github/scripts/docker-build.sh --push --registry ghcr.io/myorg
```

## 📖 Documentation

- **Complete guide**: `.github/DOCKER_VERSIONING.md`
- **Docker basics**: `.github/DOCKER.md`
- **Scripts README**: `.github/scripts/README.md`
- **Release workflow**: `.github/workflows/release.yml`

## 💡 Tips

1. **Use `make` for most tasks** - Simplest and most intuitive
2. **Test before tagging** - Build with `TAG=vX.Y.Z` first
3. **Let CI/CD handle releases** - Don't manually push to ghcr.io
4. **Keep pyproject.toml in sync** - Version should match git tag
5. **Use semantic versioning** - Follow `vMAJOR.MINOR.PATCH` format

## 🎓 Examples

### Example 1: Feature Development

```bash
# During development
make docker-build-dev
docker run --rm avd-cli:dev --help

# Test changes
make docker-run ARGS="get eos --help"
```

### Example 2: Release Candidate

```bash
# Build RC
make docker-build TAG=v1.0.0-rc1

# Test extensively
docker run --rm avd-cli:v1.0.0-rc1 --version

# If OK, create final release
git tag v1.0.0
git push origin v1.0.0
```

### Example 3: Hotfix

```bash
# Create hotfix tag
git tag v1.0.1
git push origin v1.0.1

# GitHub Actions automatically:
# - Builds v1.0.1
# - Publishes to PyPI
# - Updates Docker image
```

### Example 4: Multi-Registry Push

```bash
# Build once
make docker-build TAG=v1.0.0

# Push to multiple registries
docker tag avd-cli:v1.0.0 ghcr.io/titom73/avd-cli:v1.0.0
docker tag avd-cli:v1.0.0 docker.io/titom73/avd-cli:v1.0.0

docker push ghcr.io/titom73/avd-cli:v1.0.0
docker push docker.io/titom73/avd-cli:v1.0.0
```

## 🤝 Contributing

When contributing Docker-related changes:

1. **Test locally first**: `make docker-build-dev`
2. **Update documentation**: If changing build process
3. **Maintain backward compatibility**: Don't break existing scripts
4. **Follow OCI standards**: Use standard label names

---

**Quick Links:**
- [Dockerfile](../Dockerfile)
- [Release Workflow](workflows/release.yml)
- [Scripts](scripts/README.md)

**Need Help?** Check `.github/DOCKER_VERSIONING.md` for comprehensive documentation.
