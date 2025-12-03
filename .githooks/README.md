# Git Hooks

This directory contains custom git hooks for the avd-cli project.

## Available Hooks

### pre-push

**Purpose**: Enforces code quality by running `make ci` before every push.

**What it checks**:
- Linting (flake8, pylint)
- Type checking (mypy)
- All test suites
- Code coverage (≥80%)

**Installation**:
```bash
make git-hooks-install
```

**Bypass** (not recommended):
```bash
git push --no-verify
```

## Why Use These Hooks?

1. **Catch Issues Early**: Find and fix problems before CI runs on GitHub
2. **Save Time**: Avoid failed CI builds and multiple push cycles
3. **Maintain Quality**: Ensure all code meets project standards
4. **Team Consistency**: Everyone follows the same quality checks

## Manual Hook Management

If you need to manually install/uninstall hooks:

```bash
# Install
cp .githooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push

# Uninstall
rm .git/hooks/pre-push
```
