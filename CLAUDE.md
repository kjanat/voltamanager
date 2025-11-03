# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Volta Manager** is a Python CLI tool for managing Volta-managed global Node.js packages. It checks versions against the npm registry and updates outdated packages.

## Development Commands

### Environment Setup

```bash
# Create virtual environment and install dependencies
uv sync

# Install with dev dependencies
uv sync --dev
```

### Running the Application

```bash
# Run directly with uv (recommended)
uv run voltamanager [OPTIONS]

# Examples
uv run voltamanager              # Check status of all packages
uv run voltamanager --update     # Update outdated packages
uv run voltamanager --dry        # Dry run to see what would be updated
uv run voltamanager --help       # Show help
```

### Linting

```bash
# Run ruff linter (check only)
uv run ruff check .

# Run ruff linter with auto-fix
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff-check --all-files
```

### README Generation

The README.md is auto-generated from Typer docstrings using:

```bash
uv run typer voltamanager utils docs --name voltamanager --title "Volta Manager" --output README.md
```

This runs automatically via pre-commit hook. **Do not manually edit README.md**.

## Architecture

### Multi-Module Design

The application has been refactored into separate modules for better organization:

- `__init__.py` - Main CLI commands and Typer app definition
- `__main__.py` - Entry point for `python -m voltamanager`
- `cache.py` - npm version caching logic
- `config.py` - Configuration file handling
- `core.py` - Core functionality (dependency checks, package parsing, health checks)
- `display.py` - Rich console output formatting and statistics
- `logger.py` - Structured logging setup
- `npm.py` - npm registry queries (single, batch, parallel)
- `operations.py` - Package update operations
- `security.py` - npm audit integration
- `utils.py` - Version comparison and utility functions
- `constants.py` - Shared constants

### Core Flow

1. **Dependency Check** → Verify `volta` and `npm` are in PATH
1. **Package Discovery** → Run `volta list --format=plain` to get installed packages
1. **Version Checking** → Query npm registry for each package's latest version
1. **Update Execution** → Install updates via `volta install package@latest`

### Safe Subprocess Execution

All subprocess operations use a temporary directory (`tempfile.TemporaryDirectory()`) as the working directory to avoid interference with any local package.json in the current directory.

### Package Name Parsing

Handles scoped packages correctly:

- `package@1.0.0` → `(package, 1.0.0)`
- `@vue/cli@5.0.8` → `(@vue/cli, 5.0.8)`
- Uses `rsplit("@", 1)` for scoped packages to avoid splitting the scope

### Project-Pinned Packages

Volta can pin packages to specific projects. These appear with version "project" and are:

- Displayed in status table with "PROJECT" status
- Excluded from updates by default
- Included only with `--include-project` flag

## Build System Notes

- **Package Manager**: uv (modern Python package manager)
- **Build Backend**: uv_build (specified in pyproject.toml)
- **Python Version**: Requires >=3.13
- **Lock File**: uv.lock is automatically maintained by pre-commit hooks
- **Core Dependencies**: `rich`, `typer`, `packaging` for version parsing

## Important Pre-commit Behaviors

1. **uv-lock hook**: Automatically updates `uv.lock` when `pyproject.toml` changes
1. **uv-export hook**: Keeps `requirements.txt` in sync with `uv.lock`
1. **readme-gen hook**: Auto-generates README.md from Typer docstrings
1. **cleanup hook**: Removes cache directories (`__pycache__`, `.pytest_cache`, etc.)

Pre-commit CI skips `cleanup` and `readme-gen` hooks (configured in `.pre-commit-config.yaml`).

## Testing

Comprehensive test suite exists covering all modules:

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/core_test.py

# Run with verbose output
uv run pytest -v

# Show coverage report
uv run pytest --cov=voltamanager --cov-report=html
```

Test Organization:

- Place tests in `tests/` directory
- Use naming convention `test_*.py` or `*_test.py` (enforced by pre-commit)
- Test coverage configured for src/voltamanager with branch coverage enabled

## Volta Integration

The tool wraps these Volta commands:

- `volta list --format=plain` - Lists installed packages
- `volta install <package>[@version]` - Installs/updates packages

It queries npm registry via:

- `npm view <package> version` - Gets latest version (10s timeout)
