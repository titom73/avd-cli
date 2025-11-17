# Automated Release Process

This guide describes how to use the **automated release workflow** for avd-cli.

---

## Overview

The automated release process simplifies version management by:

- ✅ Automatically bumping versions in all required files
- ✅ Creating a release branch and Pull Request
- ✅ Generating a release notes template
- ✅ Running all quality checks before release
- ✅ **Automatically creating and pushing the release tag when PR is merged**
- ✅ Triggering the full release pipeline automatically
- ✅ Providing clear next steps

---

## Quick Start

### 1. Trigger the Workflow

**Option A: GitHub Web Interface**

1. Go to [Actions → Release: Prepare Version](https://github.com/titom73/avd-cli/actions/workflows/prepare-release.yml)
2. Click **"Run workflow"** button
3. Select the version bump type:
   - `patch` → Bug fixes (0.1.0 → 0.1.1)
   - `minor` → New features (0.1.0 → 0.2.0)
   - `major` → Breaking changes (0.1.0 → 1.0.0)
4. Click **"Run workflow"**

**Option B: GitHub CLI**

```bash
# Patch release (bug fixes)
gh workflow run prepare-release.yml -f version_bump=patch

# Minor release (new features)
gh workflow run prepare-release.yml -f version_bump=minor

# Major release (breaking changes)
gh workflow run prepare-release.yml -f version_bump=major
```

### 2. Monitor the Workflow

Watch the workflow execution:

```bash
gh run watch
```

Or visit: https://github.com/titom73/avd-cli/actions

### 3. Review the Pull Request

The workflow creates a PR automatically with:

- ✅ Version bumped in `pyproject.toml`
- ✅ Version bumped in `avd_cli/__init__.py`
- ✅ Release branch created (`release/vX.Y.Z`)
- ✅ Checklist of tasks to complete
- ✅ Next steps clearly documented

**Review the PR and:**

1. Update the description with actual changes
2. Ensure all CI checks pass
3. Request review if needed

### 4. Merge the Pull Request

Once approved and all checks pass:

```bash
gh pr merge --squash
```

Or merge via GitHub web interface.

### 5. Sit Back and Relax ☕ - Everything is Automated!

**✨ Fully Automated Release Pipeline**

When you merge the PR, the following happens **automatically without any manual intervention**:

#### Step 1: Auto-Tag (within seconds)

The [`auto-tag-release.yml`](https://github.com/titom73/avd-cli/actions/workflows/auto-tag-release.yml) workflow:

1. ✅ Detects that a `release/v*` branch was merged to `main`
2. ✅ Extracts the version from the branch name
3. ✅ Verifies it matches the version in `pyproject.toml`
4. ✅ Creates the git tag (e.g., `v0.1.1`)
5. ✅ **Pushes the tag to GitHub using PAT token** (this is critical!)

**Why use PAT?** GitHub's `GITHUB_TOKEN` doesn't trigger other workflows (security feature). By using a Personal Access Token (PAT), we ensure the tag push triggers the release workflow.

#### Step 2: Automatic Release Publication (1-5 minutes)

Once the tag is created, the [release workflow](https://github.com/titom73/avd-cli/actions/workflows/release.yml) automatically:

1. ✅ Verifies tag matches `pyproject.toml` version
2. 📦 Builds the package with `uv build`
3. 🚀 Publishes to PyPI
4. 🐳 Builds and pushes Docker images to Docker Hub and GHCR
5. 📚 Deploys documentation

**Monitor both workflows:**

```bash
# Watch the auto-tag workflow
gh run watch

# Then watch the release workflow
gh run watch
```

**That's it! No manual commands needed. Just merge and monitor.** 🎉

---

## Workflow Details

### What the Workflow Does

1. **Version Bump**
   - Uses `bumpver` to update version in:
     - `pyproject.toml` (package version and bumpver config)
     - `avd_cli/__init__.py` (`__version__` variable)
   - Creates a commit with message: `bump: version X.Y.Z → A.B.C`

2. **Branch Creation**
   - Creates branch: `release/vX.Y.Z`
   - Pushes to remote repository

3. **Pull Request**
   - Creates PR with:
     - Title: `release: avd-cli vX.Y.Z`
     - Detailed description with checklist
     - Labels: `release`, `automated`
     - Assigned to workflow initiator

4. **Summary**
   - Provides workflow summary with:
     - Version information
     - PR link
     - Next steps

---

## Version Bump Types

### Patch Release (X.Y.Z → X.Y.Z+1)

**When to use:**
- Bug fixes
- Security patches
- Documentation updates
- Minor improvements

**Example:** `0.1.0` → `0.1.1`

```bash
gh workflow run prepare-release.yml -f version_bump=patch
```

### Minor Release (X.Y.Z → X.Y+1.0)

**When to use:**
- New features (backward compatible)
- Enhancements
- New commands or options
- Deprecations (with backward compatibility)

**Example:** `0.1.0` → `0.2.0`

```bash
gh workflow run prepare-release.yml -f version_bump=minor
```

### Major Release (X.Y.Z → X+1.0.0)

**When to use:**
- Breaking changes
- Major redesigns
- API changes
- Removed deprecated features

**Example:** `0.1.0` → `1.0.0`

```bash
gh workflow run prepare-release.yml -f version_bump=major
```

---

## Troubleshooting

### Workflow Fails: "No patterns matched for file 'pyproject.toml'"

**Cause:** `bumpver` configuration issue in `pyproject.toml`

**Solution:**

1. Check `[tool.bumpver.file_patterns]` section in `pyproject.toml`
2. Ensure patterns use proper escaping
3. Test locally:
   ```bash
   uv run bumpver update --patch --dry
   ```

### Workflow Fails: "Permission denied"

**Cause:** Insufficient GitHub token permissions

**Solution:**

1. Check workflow permissions in `.github/workflows/prepare-release.yml`
2. Ensure `contents: write` and `pull-requests: write` are set
3. Verify branch protection rules don't block bot commits

### PR Creation Fails

**Cause:** Branch already exists or PR already open

**Solution:**

1. Delete the existing release branch:
   ```bash
   git push origin --delete release/vX.Y.Z
   ```
2. Close existing PR if any
3. Re-run the workflow

### Tag Creation Not Triggered

**Error:** Tag was not created automatically after merging PR

**Possible Causes:**
1. PR doesn't have the `kind:release` label
2. Branch name doesn't match `release/v*` pattern
3. PAT token is not configured or expired

**Solution:**

1. Check if the auto-tag workflow ran:
   ```bash
   gh run list --workflow=auto-tag-release.yml
   ```

2. If it didn't run, check the PR labels:
   ```bash
   gh pr view 123 --json labels
   ```

3. Verify PAT token is configured:
   ```bash
   gh secret list | grep PAT
   ```

4. Manual fallback (if needed):
   ```bash
   git checkout main
   git pull origin main
   VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
   git tag "v$VERSION"
   git push origin "v$VERSION"
   ```

### Release Workflow Not Triggered

**Error:** Tag was created but release workflow didn't start

**Cause:** Tag was created with `GITHUB_TOKEN` instead of `PAT`

**Solution:**

1. Delete and recreate the tag manually with PAT authentication:
   ```bash
   git tag -d v0.1.1
   git push --delete origin v0.1.1
   # Then create it with a local git authenticated with PAT
   git tag v0.1.1
   git push origin v0.1.1
   ```

2. Or ensure the `PAT` secret is properly configured in repository settings

---

## Best Practices

### ✅ Do

- **Always use the workflow** for consistency
- **Review the PR carefully** before merging
- **Update release notes** with actual changes
- **Wait for CI checks** to pass before merging
- **Test locally** before pushing the tag
- **Follow semantic versioning** guidelines

### ❌ Don't

- **Don't bump versions manually** - use the workflow
- **Don't skip the PR** - always review changes
- **Don't push tags without merging PR** - versions won't match
- **Don't reuse version numbers** - PyPI won't accept duplicates
- **Don't force push** on release branches

---

## Example Workflow

Here's a complete example of releasing version 0.1.1 (patch):

```bash
# 1. Trigger the workflow
gh workflow run prepare-release.yml -f version_bump=patch

# 2. Wait for workflow completion (~1-2 minutes)
gh run watch

# 3. Check the created PR
gh pr list --label kind:release

# 4. Review and merge the PR
gh pr view 123  # Replace with actual PR number
gh pr merge 123 --squash

# 5. 🎉 That's it! Everything else is automatic!
#    - Tag is created automatically (within seconds)
#    - Release workflow is triggered automatically
#    - Package is built and published to PyPI
#    - Docker images are built and pushed
#    - Documentation is deployed

# 6. Monitor the automated workflows
gh run watch  # Watch auto-tag workflow
gh run watch  # Watch release workflow

# 7. Verify the release (after ~5-10 minutes)
gh release list
gh release view v0.1.1
```

**Timeline:** 
- PR creation: ~1 minute
- Your review and merge: ~5-10 minutes
- **Automated tag creation: ~10 seconds** ⚡
- **Automated release: ~5-10 minutes** 🚀
- **Total: ~10-20 minutes with zero manual commands!**

---

## Manual Override

If you need to perform a release manually (not recommended), see [release.md](release.md) for the manual process.

---

## Additional Resources

- [GitHub Actions: Release Workflows](workflows/README.md)
- [Manual Release Process](release.md)
- [Semantic Versioning](https://semver.org/)
- [bumpver Documentation](https://github.com/mbarkhau/bumpver)
- [Workflow Source](.github/workflows/prepare-release.yml)

---

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Review [workflow logs](https://github.com/titom73/avd-cli/actions/workflows/prepare-release.yml)
3. Open an issue on GitHub

---

**Last updated:** November 2025
