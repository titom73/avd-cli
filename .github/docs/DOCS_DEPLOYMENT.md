# Documentation Deployment Guide

This guide explains how to work with the AVD CLI documentation.

## Local Development

### Serve Documentation Locally

```bash
# Install documentation dependencies
make install-doc

# Serve with live reload
make docs-serve

# Or directly with UV
uv run mkdocs serve
```

Access the documentation at: <http://127.0.0.1:8000>

### Build Documentation

```bash
# Build static site
make docs-build

# Output will be in ./site/
```

### Test Mike Deployment

```bash
# Test mike deployment locally (creates a local git commit)
make docs-test

# To undo the test commit
git reset --soft HEAD~1
```

## Deployment

### Automatic Deployment (Recommended)

Documentation is automatically deployed via GitHub Actions:

- **Push to `main` branch**: Deploys as `main` version with `development` alias
- **Push git tag `v*`**: Deploys as versioned release with `stable` alias

### Manual Deployment

#### Deploy Development Version

```bash
make docs-deploy-dev
```

#### Deploy Stable Version

```bash
make docs-deploy-stable VERSION=v0.1.0
```

#### Delete a Version

```bash
make docs-delete VERSION=v0.1.0
```

## Managing Versions

### List Deployed Versions

```bash
make docs-list
```

### Set Default Version

```bash
uv run mike set-default --push stable
```

## Documentation Structure

```
docs/
├── index.md                    # Home page
├── getting-started/            # Installation, quick start, basics
├── user-guide/                 # Commands, inventory, env vars, workflows
├── examples/                   # Real-world examples
├── api/                        # API reference (auto-generated)
├── development/                # Contributing, architecture, testing
├── stylesheets/                # Custom CSS
├── assets/                     # Images, favicon
├── faq.md                      # FAQ
└── release-notes.md            # Release notes
```

## Writing Documentation

### Markdown Extensions

AVD CLI documentation supports:

- **Admonitions**: `!!! note`, `!!! warning`, `!!! tip`
- **Code blocks** with syntax highlighting
- **Tables**
- **Mermaid diagrams**
- **Tabbed content** with `===`
- **Task lists**

### API Documentation

API documentation is auto-generated from Python docstrings using `mkdocstrings`:

```markdown
# In docs/api/cli/main.md
::: avd_cli.cli.main
```

### Cross-References

```markdown
[Installation Guide](../getting-started/installation.md)
[generate command](user-guide/commands/generate.md)
```

## CI/CD Workflow

The `.github/workflows/deploy-docs.yml` workflow:

1. **On PR**: Builds docs to validate (no deployment)
2. **On push to main**: Deploys as `main` (development)
3. **On tag push**: Deploys as versioned release (stable)
4. **Manual trigger**: Allows custom version/alias deployment

## Troubleshooting

### Documentation doesn't build

```bash
# Check for errors
uv run mkdocs build --strict --verbose
```

### Mike shows wrong versions

```bash
# List all versions
uv run mike list

# Delete unwanted version
make docs-delete VERSION=unwanted-version
```

### Git conflicts on gh-pages

```bash
# Fetch latest gh-pages
git fetch origin gh-pages:gh-pages

# Force push if needed (use with caution!)
uv run mike deploy --push --force main development
```

## Best Practices

1. **Test locally** before pushing: `make docs-serve`
2. **Build with strict mode**: `make docs-build`
3. **Commit docs changes** with descriptive messages
4. **Use semantic versioning** for tags (v0.1.0, v1.0.0)
5. **Keep stable version** as default
6. **Clean up old versions** periodically

## References

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Mike Documentation](https://github.com/jimporter/mike)
- [mkdocstrings](https://mkdocstrings.github.io/)
