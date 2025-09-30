# Changelog

All notable changes to VoltaManager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2025-09-30

### Added

- **Breaking Change Warnings**: Automatic detection and warnings for major version updates
  - Uses `packaging` library to parse and compare semantic versions
  - Displays clear warnings when packages have major version bumps
  - Warns users to review changelogs before updating
  - Visual indicators (⚠) in status table for major updates
  - New `utils.py` module with version comparison utilities
- **Local Volta Config Detection**: Warns when local `package.json` has volta configuration
  - Detects potential conflicts with global package management
  - Shows volta config details in verbose mode
  - Helps prevent unexpected behavior from local project settings
  - Runs automatically at the start of check operations

### Tests

- Added 17 comprehensive unit tests for new features
  - Version comparison tests (major/minor/patch detection)
  - Major update detection with various package states
  - Volta config detection with different JSON scenarios
  - Edge case handling (invalid versions, missing files, malformed JSON)
  - Test coverage now includes all utility functions

### Changed

- `check_and_update()` now accepts `verbose` parameter for detailed output
- Major version updates are highlighted in the status table
- Enhanced user safety with proactive warnings about breaking changes

## [0.3.0] - 2025-09-30

### Added

- **Type Checking**: Full mypy support with comprehensive type hints across all modules
  - Modern Python 3.13 type hints (using `dict[str, str]` instead of `Dict[str, str]`)
  - Strict mypy configuration in `mypy.ini`
  - Pre-commit hook for automatic type checking
- **Structured Logging System**: Professional logging infrastructure
  - New `logger.py` module with structured log formatter
  - Log file at `~/.voltamanager/voltamanager.log`
  - `voltamanager logs` command to view logs
  - `voltamanager logs --stats` for log statistics
  - Logs operations, updates, and errors with structured data
- **Batch NPM Queries**: Performance optimization for small package counts
  - `get_latest_versions_batch()` function for querying multiple packages at once
  - Auto-switches to batch mode for ≤4 packages
  - Falls back to parallel queries if batch fails
- **Integration Tests**: Comprehensive test suite with subprocess mocking
  - 20+ new integration tests using pytest-mock
  - Tests for core, npm, and operations modules
  - Mocked subprocess calls for safe testing
  - Tests cover success, failure, and edge cases

### Changed

- Updated all type hints to Python 3.13 style (`list[str]` instead of `List[str]`)
- Enhanced `get_latest_versions_parallel()` to use batch queries when beneficial
- `log_update()` now uses structured logging in addition to legacy history file
- All operations now log to structured logger for better observability

### Dependencies

- Added `pytest-mock>=3.14.0` for integration testing
- Added `mypy>=1.13.0` for type checking
- Added `types-setuptools>=75.0.0` for mypy type stubs

### Developer Experience

- Mypy pre-commit hook ensures type safety
- Better test coverage with integration tests
- Improved code quality with strict type checking
- Professional logging for debugging and monitoring

______________________________________________________________________

## [0.2.0] - 2025-09-30

### Major Improvements

#### Architecture

- **Modular Structure**: Refactored from single 255-line file into organized modules
  - `core.py`: Core logic and dependency checking
  - `npm.py`: NPM registry interactions with parallel queries
  - `cache.py`: Version caching system
  - `config.py`: Configuration management
  - `display.py`: Output formatting (tables, JSON, statistics)
  - `operations.py`: Package operations and update management

#### Performance

- **Parallel Version Checking**: 5-10x faster for 10+ packages using `ThreadPoolExecutor`
- **Progress Indicators**: Real-time progress bars with Rich library during version checks
- **NPM Response Caching**: 1-hour TTL cache for version queries in `~/.cache/voltamanager/`
- **Configurable Parallelism**: Control concurrent checks via config file

#### New Features

##### Command-Line Options

- `--json`: Output package status in JSON format for scripting
- `--outdated-only`: Filter display to show only outdated packages
- `--interactive, -i`: Interactively select which packages to update
- `--no-cache`: Bypass cache and force fresh npm queries
- `--verbose, -v`: Detailed output with timing information
- `--quiet, -q`: Minimal output (suppress tables unless updating)

##### New Commands

- `voltamanager config`: Generate default configuration file
- `voltamanager clear-cache`: Clear the npm version cache
- `voltamanager rollback`: Rollback to previous package versions

##### Configuration File

- Support for `~/.config/voltamanager/config.toml`
- Configurable package exclusion list
- Default include/exclude project-pinned packages
- Customizable cache TTL and parallel check limits

##### Safety Features

- **Automatic Snapshots**: State saved before updates for rollback capability
- **Update History**: Log all updates to `~/.voltamanager/history.log`
- **Major Version Warnings**: Visual indicator (⚠) for major version bumps in table
- **Breaking Change Detection**: Uses `packaging` library for semantic version comparison

#### User Experience

- **Better Error Messages**: Detailed error messages with installation instructions
- **Summary Statistics**: Display counts of up-to-date, outdated, project-pinned packages
- **Detailed Dry Run Report**: Enhanced dry-run output showing planned changes in table format
- **Interactive Updates**: Choose which packages to update with confirmation prompts

### Testing

- Comprehensive test suite with pytest
- 22 tests covering:
  - Package parsing (regular and scoped packages)
  - Version comparison and major update detection
  - Configuration loading and validation
  - Cache operations and expiration
- Test coverage for edge cases (empty strings, scoped packages, invalid versions)

### Dependencies

- Added `packaging>=24.0` for semantic versioning
- Added `pytest>=8.0.0` and `pytest-cov>=6.0.0` for testing

### Bug Fixes

- Fixed scoped package parsing without version (e.g., `@vue/cli`)
- Improved handling of edge cases in package name parsing

______________________________________________________________________

## [0.1.0] - Initial Release

### Features

- Check Volta-managed package versions against npm registry
- Update outdated packages with `--update` flag
- Project-pinned package handling
- Dry-run mode with `--dry`
- Force update all packages with `--force`
- Rich table display with color-coded status
