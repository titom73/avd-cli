# Release Process for avd-cli

This document describes the release process for the `avd-cli` package.

## Prerequisites

### Required Tools

- **[uv](https://docs.astral.sh/uv/)** - Modern Python package manager (replaces pip, build, twine)
- **[bumpver](https://github.com/mbarkhau/bumpver)** - Version bumping tool
- **[GitHub CLI](https://cli.github.com/)** - Recommended for easier GitHub operations

### Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install bumpver (in project venv)
uv pip install bumpver
```

## Release Workflow Overview

The release process is **fully automated** via GitHub Actions. When you push a tag matching `v*.*.*`, the workflow:

1. ✅ **Verifies** that the Git tag matches the version in `pyproject.toml`
2. 📦 **Builds** the package using `uv build`
3. 🚀 **Publishes** to PyPI automatically
4. 🐳 **Builds** and pushes Docker images
5. 📚 **Deploys** documentation to the versioned site

## Step-by-Step Release Process

### 1. Prepare the Release Branch

Create a dedicated branch for the version bump:

```bash
git switch main
git pull origin main
git switch -c release/vX.Y.Z
```

### 2. Bump the Version

Use `bumpver` to update the version in `pyproject.toml`:

**For a patch release (X.Y.Z → X.Y.Z+1):**
```bash
bumpver update --patch
```

**For a minor release (X.Y.Z → X.Y+1.0):**
```bash
bumpver update --minor
```

**For a major release (X.Y.Z → X+1.0.0):**
```bash
bumpver update --major
```

**Preview changes without applying (dry-run):**
```bash
bumpver update --minor --dry
```

> [!TIP]
> `bumpver` automatically updates the version in `pyproject.toml` and creates a Git commit with the version bump.

### 3. Create a Pull Request

Push the release branch and create a PR:

```bash
git push origin release/vX.Y.Z
gh pr create --title "release: avd-cli vX.Y.Z" --body "Release version X.Y.Z"
```

### 4. Review and Merge

After PR review and approval:

```bash
gh pr merge --squash
```

### 5. Create and Push the Git Tag

**The tag MUST match the version in `pyproject.toml` (with `v` prefix):**

```bash
git switch main
git pull origin main

# Create the tag (e.g., v0.1.0 for version 0.1.0)
git tag vX.Y.Z

# Push the tag to trigger the release workflow
git push origin vX.Y.Z
```

> [!IMPORTANT]
> The GitHub Actions workflow will **automatically verify** that the tag matches the version in `pyproject.toml`. If they don't match, the release will be aborted.

### 6. Monitor the Release Workflow

The [release workflow](https://github.com/titom73/avd-cli/actions/workflows/release.yml) will automatically:

1. Verify tag matches `pyproject.toml` version
2. Build the package with `uv build`
3. Publish to PyPI
4. Build and push Docker images
5. Trigger documentation deployment

**Monitor the workflow:**
```bash
gh run watch
```

Or visit: https://github.com/titom73/avd-cli/actions/workflows/release.yml

### 7. Verify the Release

After the workflow completes successfully:

**Check PyPI:**
```bash
# In a fresh virtual environment
uv venv test-release
source test-release/bin/activate
uv pip install avd-cli

# Verify version
avd-cli --version
```

**Check Docker Hub:**
```bash
docker pull titom73/avd-cli:vX.Y.Z
docker run --rm titom73/avd-cli:vX.Y.Z --version
```

**Check Documentation:**
Visit: https://avd-cli.readthedocs.io/ and verify the new version is listed.

---

## Manual Testing (Optional)

If you want to test the package build locally before creating the tag:

### Build Locally

```bash
# Clean previous builds
rm -rf dist/

# Build with uv
uv build

# Check the built packages
ls -lh dist/
```

### Test Package Locally

```bash
# Create a test environment
uv venv test-env
source test-env/bin/activate

# Install the local wheel
uv pip install dist/avd_cli-X.Y.Z-py3-none-any.whl

# Run tests
avd-cli --version
avd-cli --help
```

---

## Troubleshooting

### Tag/Version Mismatch Error

**Error:**
```
❌ Error: Git tag (vX.Y.Z) does not match version in pyproject.toml (vA.B.C)
```

**Solution:**
1. Delete the incorrect tag:
   ```bash
   git tag -d vX.Y.Z
   git push origin :refs/tags/vX.Y.Z
   ```

2. Update `pyproject.toml` to the correct version (or use `bumpver`)

3. Create the correct tag:
   ```bash
   git tag vA.B.C
   git push origin vA.B.C
   ```

### Workflow Failed

**Check workflow logs:**
```bash
gh run list --workflow=release.yml
gh run view <run-id> --log
```

**Common issues:**
- Missing PyPI token (`PYPI_API_TOKEN` secret)
- Docker Hub credentials not configured
- Version already exists on PyPI (can't re-upload)

### PyPI Upload Failed

If PyPI upload fails but you need to retry:

1. The workflow cannot re-upload the same version
2. You must bump to a new version (e.g., from 0.1.0 to 0.1.1)
3. Follow the release process again with the new version

---

## Configuration for bumpver

The `bumpver` tool is configured in `pyproject.toml` to automatically update version in:

- `pyproject.toml` - Package version and bumpver current_version
- `avd_cli/__init__.py` - `__version__` variable

```toml
[tool.bumpver]
current_version = "0.1.0"
version_pattern = "MAJOR.MINOR.PATCH"
commit_message = "bump: version {old_version} → {new_version}"
commit = true
tag = false  # We create tags manually
push = false  # We push manually after PR merge

[tool.bumpver.file_patterns]
"pyproject.toml" = [
    'version = "{version}"',
    'current_version = "{version}"',
]
"avd_cli/__init__.py" = [
    '__version__ = "{version}"',
]
```

---

## Release Checklist

- [ ] All tests passing on `main` branch
- [ ] CHANGELOG/release notes updated (if applicable)
- [ ] Version bumped with `bumpver`
- [ ] PR created and reviewed
- [ ] PR merged to `main`
- [ ] Tag created matching version in `pyproject.toml`
- [ ] Tag pushed to trigger release workflow
- [ ] Release workflow completed successfully
- [ ] PyPI package verified
- [ ] Docker images verified
- [ ] Documentation updated and deployed

---

## Additional Resources

- [GitHub Actions Release Workflow](.github/workflows/release.yml)
- [uv Documentation](https://docs.astral.sh/uv/)
- [bumpver Documentation](https://github.com/mbarkhau/bumpver)
- [PyPI Package](https://pypi.org/project/avd-cli/)
- [Docker Hub](https://hub.docker.com/r/titom73/avd-cli)

