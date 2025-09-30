# VoltaManager v0.10.0 - Command Enhancement Release

## Release Date

2025-09-30

## Version Change

- **Previous**: 0.9.0
- **Current**: 0.10.0
- **Type**: Minor version bump (new features added)

## Overview

Version 0.10.0 introduces three new practical commands that enhance package management flexibility and provide better control over volta-managed packages. This release focuses on real-world user pain points: selective package rollback, persistent package exclusion management, and quick package information lookup.

## New Features

### 1. Selective Rollback

**Problem Solved**: Previously, rollback was all-or-nothing. If you wanted to undo an update to just one package, you had to rollback everything and re-update the rest.

**Solution**: Enhanced `rollback` command to accept optional package names.

```bash
# Rollback all packages (original behavior)
voltamanager rollback

# Rollback just one package
voltamanager rollback typescript

# Rollback multiple specific packages
voltamanager rollback typescript eslint prettier --force

# Rollback a scoped package
voltamanager rollback @vue/cli
```

**Features**:

- Accepts zero or more package names as arguments
- Falls back to full rollback when no packages specified (backward compatible)
- Warns when requested packages aren't found in snapshot
- Shows available packages when none match
- Displays preview table before execution
- Requires confirmation unless --force flag provided

**Use Cases**:

- Undo a problematic update to a single package
- Rollback build tools while keeping linters updated
- Selective recovery after bulk updates cause issues

### 2. Pin/Unpin Commands

**Problem Solved**: Users needed to manually edit config files to add packages to the exclude list. There was no easy way to manage pinned packages.

**Solution**: New `pin` command for package exclusion management.

```bash
# Pin packages to prevent updates
voltamanager pin typescript eslint

# Unpin packages to allow updates again
voltamanager pin --unpin typescript

# Pin with automatic config display
voltamanager pin prettier  # Shows all currently pinned packages after operation
```

**Features**:

- Add one or more packages to config exclude list
- Remove packages from exclude list with --unpin flag
- Automatically creates/updates config file
- Displays currently pinned packages after operation
- Preserves other configuration values
- Provides feedback on which packages were added/removed

**Use Cases**:

- Pin packages with known breaking changes in newer versions
- Temporarily exclude packages from updates during testing
- Maintain stable versions of critical dependencies
- Quick package exclusion management without editing config files

### 3. Info Command

**Problem Solved**: No quick way to get detailed package information without opening browser or querying npm manually.

**Solution**: New `info` command for package metadata lookup.

```bash
# Get detailed information about a package
voltamanager info typescript

# Works with scoped packages
voltamanager info @vue/cli

# Example output:
# Package: typescript
# Description: TypeScript is a language for application scale JavaScript development
# Latest Version: 5.7.2
# License: Apache-2.0
# Homepage: https://www.typescriptlang.org/
# Repository: git+https://github.com/Microsoft/TypeScript.git
# Maintainers:
#   • typescript-bot
#   • weswigham
#   • sandersn
# Created: 2012-10-01
# Last Modified: 2024-11-08
# Dependencies: 0 packages
```

**Features**:

- Displays name, description, latest version
- Shows license information
- Links to homepage and repository
- Lists maintainers (first 3)
- Shows creation and last modified dates
- Counts dependencies
- Provides link to npm page for download stats
- Handles timeouts and errors gracefully
- Works with scoped packages

**Use Cases**:

- Quick package information lookup before updating
- Verify package authenticity and maintainers
- Check when package was last updated
- Research packages before installation
- Validate package metadata for security reviews

## Technical Implementation

### Architecture Changes

1. **Enhanced Rollback Logic** (src/voltamanager/__init__.py):

   - Modified `rollback()` to accept optional `packages: list[str]` argument
   - Added filtering logic to extract only requested packages from snapshot
   - Improved error messaging for missing packages
   - Maintains backward compatibility (no args = rollback all)

1. **Config Save Method** (src/voltamanager/config.py):

   - Added `Config.save()` method to persist configuration changes
   - Properly formats TOML with comments
   - Preserves all configuration values during write
   - Creates config directory if needed

1. **New Commands** (src/voltamanager/__init__.py):

   - `pin_package()`: Pin/unpin package management
   - `package_info()`: NPM package information lookup

### Testing

**New Test Files**:

- `tests/pin_test.py`: 7 comprehensive tests for pin/unpin functionality

  - Single and multiple package pinning
  - Unpin functionality
  - Already-pinned detection
  - Config preservation
  - Empty/missing cases

- `tests/rollback_selective_test.py`: 10 comprehensive tests for selective rollback

  - All packages rollback (backward compatibility)
  - Single and multiple package rollback
  - Missing package error handling
  - Partial match warnings
  - Scoped package support
  - Confirmation flow
  - Failure handling

**Test Coverage**:

| Metric | Value |
|--------|-------|
| **Total Tests** | **230** (+17 from v0.9.0) |
| **Overall Coverage** | **87.79%** |
| **Test Success** | **230/230 (100%)** |
| **Execution Time** | **~22 seconds** |

**Module Coverage**:

| Module | Coverage |
|--------|----------|
| cache.py | 100.00% |
| display.py | 100.00% |
| logger.py | 100.00% |
| config.py | 94.94% |
| npm.py | 97.30% |
| core.py | 96.97% |
| utils.py | 93.55% |
| operations.py | 87.33% |
| __init__.py | 74.79% |

### Code Quality

- ✅ All 230 tests passing
- ✅ Zero linting errors (ruff)
- ✅ Zero type errors (mypy)
- ✅ All pre-commit hooks passing
- ✅ Backward compatible with v0.9.0
- ✅ Well-documented with examples in docstrings

## Files Changed

### Modified

1. **src/voltamanager/__init__.py**:

   - Enhanced `rollback()` command (+30 lines)
   - Added `pin_package()` command (+56 lines)
   - Added `package_info()` command (+88 lines)

1. **src/voltamanager/config.py**:

   - Added `save()` method (+21 lines)

1. **pyproject.toml**:

   - Version: 0.9.0 → 0.10.0

1. **CHANGELOG.md**:

   - Added v0.10.0 release notes with detailed feature descriptions

### Added

5. **tests/pin_test.py**: 7 new tests (125 lines)
1. **tests/rollback_selective_test.py**: 10 new tests (195 lines)
1. **IMPLEMENTATION_SUMMARY_v0.10.0.md**: This document

## Usage Examples

### Selective Rollback Workflow

```bash
# Update all packages
voltamanager --update

# Oops, typescript update broke something
# Check what versions we had before
cat ~/.voltamanager/last_snapshot.json

# Rollback just typescript
voltamanager rollback typescript --force

# Everything else stays updated!
```

### Package Management Workflow

```bash
# Pin packages with known issues
voltamanager pin webpack eslint

# See what's pinned
voltamanager config

# Update everything except pinned packages
voltamanager --update

# Later, unpin when issues are resolved
voltamanager pin --unpin webpack eslint

# Update previously pinned packages
voltamanager --update
```

### Research Workflow

```bash
# Research a package before installing
voltamanager info typescript

# Check license and maintainers
# Verify it's actively maintained
# See when last updated

# Install if everything looks good
volta install typescript
```

## Performance Impact

- **Rollback**: No performance change (filtered in-memory before volta install)
- **Pin/Unpin**: Negligible (single config file write, \<1ms)
- **Info**: ~500ms-2s depending on npm registry response time

## Breaking Changes

**None** - This release is fully backward compatible with v0.9.0.

- `rollback` without arguments works exactly as before
- Config file format unchanged (just adds save() method)
- All existing commands and flags remain unchanged

## Future Enhancements

Potential additions for future versions:

1. **Multiple Rollback Snapshots**: Keep history of multiple snapshots, not just last one
1. **Package Groups**: Tag and manage related packages together
1. **Update Policies**: Set different update strategies per package (semver rules)
1. **Automated Recommendations**: ML-based suggestions on when to update
1. **Changelog Preview**: Fetch and display changelogs between versions

## Conclusion

Version 0.10.0 enhances VoltaManager with practical commands that solve real user pain points:

- **Selective rollback** provides surgical precision when updates go wrong
- **Pin/unpin** makes persistent exclusion management effortless
- **Info command** enables quick package research without leaving terminal

With 230 passing tests and 87.79% coverage, this release maintains the high quality standards established in v0.9.0 while adding valuable new capabilities.

**Recommended Action**: Safe to upgrade - no breaking changes, comprehensive test coverage, all features thoroughly validated.
