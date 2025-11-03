# Volta Manager - Project Overview

## Purpose

CLI tool for managing Volta-managed global Node.js packages. Checks versions and updates outdated packages.

## Architecture

- **Language**: Python 3.13+
- **CLI Framework**: Typer
- **UI**: Rich (tables and console formatting)
- **Build System**: uv

## Project Structure

```tree
voltaManager/
├── src/voltamanager/
│   ├── __init__.py     # Main application logic (255 lines)
│   └── __main__.py     # Entry point
├── pyproject.toml      # Project configuration
├── README.md           # Usage documentation
└── requirements.txt    # Dependencies
```

## Core Dependencies

- typer>=0.19.2 - CLI framework
- rich>=14.1.0 - Terminal formatting
- notebook>=7.4.7
- pathlib>=1.0.1
- typing>=3.10.0.0

## Dev Dependencies

- ruff>=0.13.2 - Linting

## Key Functions (in \_\_init\_\_.py)

1. `check_dependencies()` - Verifies volta and npm are available
1. `get_installed_packages(safe_dir)` - Lists volta-managed packages
1. `parse_package(name_ver)` - Parses package@version strings (handles scoped packages)
1. `get_latest_version(package_name, safe_dir)` - Queries npm registry
1. `fast_install(packages, safe_dir, dry_run)` - Installs without version checking
1. `check_and_update(...)` - Main logic for checking and updating packages
1. `main()` - Typer command entry point

## CLI Options

- `-f, --force`: Skip version check, force update all packages
- `-u, --update`: Update outdated packages
- `--dry`: Show what would be done without doing it
- `--include-project`: Include project-pinned packages in operations

## Behavior Modes

1. **Check Only** (default): Shows status table of all packages
1. **Update**: Updates outdated packages (with --update or --force)
1. **Fast Install**: When neither check nor update requested
1. **Dry Run**: Shows what would happen without executing (--dry)

## Special Handling

- **Project-pinned packages**: Marked as "PROJECT", excluded by default
- **Scoped packages**: Correctly parses @scope/package@version format
- **Safe execution**: Uses temporary directory for subprocess operations
- **Timeout**: 10s timeout on npm registry queries

## Entry Point

Script name: `voltamanager` (defined in pyproject.toml)
