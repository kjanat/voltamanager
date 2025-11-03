# Volta Manager

[![CI](https://github.com/kjanat/voltamanager/actions/workflows/ci.yml/badge.svg)](https://github.com/kjanat/voltamanager/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kjanat/voltamanager/branch/master/graph/badge.svg?token=YOUR_TOKEN_HERE)](https://codecov.io/gh/kjanat/voltamanager)
[![Python Version](https://img.shields.io/pypi/pyversions/voltamanager)](https://pypi.org/project/voltamanager/)
[![PyPI Version](https://img.shields.io/pypi/v/voltamanager)](https://pypi.org/project/voltamanager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A package manager for a package manager of a package manager.

Volta Manager helps you check and upgrade Volta-managed global packages with ease.

## Features

- 🔍 **Check** all Volta-managed packages for updates
- ⚡ **Fast parallel** npm registry queries
- 📦 **Update** outdated packages individually or in batch
- 🎯 **Interactive selection** for selective updates
- 🔒 **Security audit** integration via npm audit
- 💾 **Smart caching** to reduce npm registry queries
- 📊 **JSON output** for scripting and automation
- 🎨 **Beautiful** terminal output with Rich formatting
- 🚀 **Breaking changes** detection for major version updates
- 📌 **Pin/Unpin** packages with configuration management
- 🔄 **Rollback** to previous versions with snapshots
- 📈 **Benchmarking** tools for performance testing

## Installation

### Prerequisites

- [Volta](https://volta.sh/) must be installed and configured
- Python 3.13 or higher
- npm (usually installed with Node.js via Volta)

### Install with pip

```bash
pip install voltamanager
```

### Install with uv

```bash
uv tool install voltamanager
```

## Quick Start

Check all packages:

```bash
voltamanager
```

Update outdated packages:

```bash
voltamanager --update
```

Interactive mode:

```bash
voltamanager --update --interactive
```

## Documentation

For full documentation, see the [auto-generated CLI docs below](#command-documentation).

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/kjanat/voltamanager.git
cd voltamanager

# Install with uv (recommended)
uv sync --dev

# Or install with pip
pip install -e .[dev]
```

### Testing

```bash
# Run tests with coverage
./scripts/test_coverage.sh

# Run specific tests
uv run pytest tests/test_core.py

# Run with markers
uv run pytest -m "not slow"
```

### Code Quality

```bash
# Linting
uv run ruff check .

# Formatting
uv run ruff format .

# Type checking
uv run pyright .

# Security scanning
uv run bandit -r src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
1. Create your feature branch (`git checkout -b feature/amazing-feature`)
1. Commit your changes (`git commit -m 'feat: add amazing feature'`)
1. Push to the branch (`git push origin feature/amazing-feature`)
1. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Volta](https://volta.sh/) for the excellent Node.js version manager
- [Typer](https://typer.tiangolo.com/) for the CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal formatting

______________________________________________________________________

<!-- Auto-generated CLI documentation below -->
