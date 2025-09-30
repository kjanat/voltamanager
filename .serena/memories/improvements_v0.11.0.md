# VoltaManager v0.11.0 Improvements Summary

## Version

- **Old**: 0.10.0
- **New**: 0.11.0
- **Release Date**: 2025-09-30

## Major Achievement: Enhanced Configuration and Safety Features

### New Features

**1. Configurable Cache TTL**:

- Cache respects `cache_ttl_hours` from config file
- `get_cached_version()` accepts `ttl_hours` parameter
- Operations use configured TTL via `config.cache_ttl_hours`
- Enables longer cache (e.g., 24 hours) for stability
- Default remains 1 hour for backward compatibility

**2. --all-packages Flag (-a)**:

- Shows excluded packages in status table
- Excluded packages displayed with `EXCLUDED` status (dim red)
- Info message shown when packages excluded (without flag)
- Works with table and JSON output
- Helps users understand what's being filtered

**3. Shell Completion**:

- Built-in tab completion via Typer
- Works with bash, zsh, fish
- Install: `voltamanager --install-completion`
- Improves CLI usability and command discovery

**4. Pre-Update Safety Checks**:

- Disk space validation before updates
- Conservative estimation (~50MB per package)
- Blocks updates when insufficient space
- Actionable error messages with specific MB counts
- Verbose mode shows disk check results
- Dry run skips check (plan only)

**5. Enhanced Error Messages**:

- Disk errors show: needed space, available space, suggestions
- Professional formatting with Rich
- Clear action items for resolution

### Code Changes

**src/voltamanager/cache.py** (+18 lines):

- `get_cached_version()`: Added `ttl_hours` parameter with default=1
- Updated function signature and docstring
- Dynamic TTL calculation using `timedelta(hours=ttl_hours)`

**src/voltamanager/__init__.py** (+3 lines):

- Added `--all-packages` / `-a` flag option
- Enabled shell completion: `add_completion=True`
- Passed `all_packages` to `check_and_update()`

**src/voltamanager/operations.py** (+42 lines):

- Added `all_packages` parameter to `check_and_update()`
- Track excluded packages when `all_packages=True`
- Pass config TTL to `get_cached_version()`
- Pre-update disk space check with actionable errors
- Display excluded packages or info message appropriately
- Import `check_disk_space` and `estimate_update_size`

**src/voltamanager/display.py** (+7 lines):

- Handle `EXCLUDED` status with "dim red" style
- Show excluded count in statistics when present

**src/voltamanager/utils.py** (+31 lines):

- Added `check_disk_space(min_mb: int) -> tuple[bool, int]`
- Added `estimate_update_size(package_count: int) -> int`
- Conservative 50MB per package estimate

### Testing

**New Test Files**:

- **tests/cache_ttl_test.py** (96 lines, 4 tests):

  - Custom TTL validation
  - Longer TTL (24 hours)
  - Default TTL behavior
  - Scoped packages with TTL

- **tests/all_packages_test.py** (191 lines, 4 tests):

  - Shows excluded when flag enabled
  - Hides excluded when flag disabled
  - Multiple excluded packages
  - JSON output with excluded

- **tests/disk_space_test.py** (215 lines, 8 tests):

  - Sufficient/insufficient space checks
  - Error handling
  - Update size estimation
  - Blocking on low space
  - Proceeding with sufficient space
  - Dry run behavior
  - Verbose disk check output

**Test Updates**:

- Fixed `test_check_and_update_uses_cache` for new signature
- Fixed `test_check_and_update_partial_cache` for TTL param
- Fixed `cache_test.py` to define CACHE_TTL locally

### Quality Metrics

**Test Execution**:

- ✅ 246/246 tests passing (100% success rate)
- ✅ +16 tests from v0.10.0
- ✅ Execution time: ~22 seconds
- ✅ Zero failures, zero warnings

**Code Quality**:

- ✅ ruff: 0 linting issues
- ✅ mypy: Type checking passing
- ✅ All pre-commit hooks passing

**Test Coverage**: 88.31% overall (+0.52% from v0.10.0)

| Module | Coverage |
|--------|----------|
| cache.py | 100.00% |
| logger.py | 100.00% |
| npm.py | 97.30% |
| core.py | 96.97% |
| display.py | 95.24% |
| config.py | 94.94% |
| utils.py | 94.17% |
| operations.py | 90.38% |
| __init__.py | 74.79% |

### Project Status: Production Ready with Enhanced Safety

**Classification**: **Production Ready - Safety & Configuration Release**

- ✅ Four practical enhancements solving real pain points
- ✅ 100% backward compatibility with v0.10.0
- ✅ Comprehensive test coverage (246 tests, 88.31%)
- ✅ 100% test success rate
- ✅ Fast test suite (~22 seconds)
- ✅ Zero breaking changes
- ✅ Enhanced user safety with disk checks

**Key Benefits**:

- **Configurable cache**: Flexibility for different update policies
- **--all-packages**: Transparency about what's excluded
- **Shell completion**: Improved CLI usability
- **Disk checks**: Prevent update failures due to space
- **Better errors**: Clearer guidance when things go wrong

## Files Changed

### Modified

- `pyproject.toml`: Version bump 0.10.0 → 0.11.0
- `CHANGELOG.md`: v0.11.0 release notes
- `src/voltamanager/__init__.py`: +3 lines (--all-packages, completion)
- `src/voltamanager/cache.py`: +18 lines (configurable TTL)
- `src/voltamanager/operations.py`: +42 lines (all_packages, disk checks)
- `src/voltamanager/display.py`: +7 lines (EXCLUDED status)
- `src/voltamanager/utils.py`: +31 lines (disk space functions)
- `tests/cache_test.py`: Fixed CACHE_TTL import
- `tests/operations_test.py`: Fixed 2 tests for new signature
- `uv.lock`: Updated for version bump
- `requirements.txt`: Updated via pre-commit hook

### Added

- `tests/cache_ttl_test.py`: 96 lines, 4 comprehensive tests
- `tests/all_packages_test.py`: 191 lines, 4 comprehensive tests
- `tests/disk_space_test.py`: 215 lines, 8 comprehensive tests

## Summary

Version 0.11.0 is a safety and configuration-focused release that adds intelligent pre-flight checks, better transparency about package filtering, and improved user experience through shell completion and better error messages. All enhancements maintain perfect backward compatibility while solving real user pain points.

**Key Achievement**: +4 major features, +16 tests, 88.31% coverage, 100% backward compatible, zero test failures
