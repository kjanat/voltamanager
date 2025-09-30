# Volta Manager

Check and upgrade Volta-managed global packages

**Usage**:

```console
$ voltamanager [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `main`: Check and upgrade Volta-managed global...
* `config`: Create default configuration file.
* `clear-cache`: Clear the npm version cache.
* `logs`: View voltamanager logs and statistics.
* `rollback`: Rollback to previous package versions.
* `bench`: Benchmark npm registry query performance.
* `health`: Check the health of your volta installation.
* `audit`: Run security audit on installed packages.
* `pin`: Pin packages to prevent updates (adds to...
* `info`: Show detailed information about a package.
* `breaking-changes`: Analyze packages with major version...

## `voltamanager main`

Check and upgrade Volta-managed global packages.

By default, shows the current status of all installed packages.
Use --update to actually update outdated packages.

Examples:
    voltamanager                    # Check all packages
    voltamanager --update           # Update outdated packages
    voltamanager --outdated-only    # Show only outdated packages
    voltamanager --json             # Output as JSON
    voltamanager -u -i              # Interactively select updates
    voltamanager --no-cache         # Force fresh npm queries

**Usage**:

```console
$ voltamanager main [OPTIONS]
```

**Options**:

* `-f, --force`: Skip version check and force update all packages
* `-u, --update`: Update outdated packages
* `--dry`: Show what would be done without doing it
* `--include-project`: Include project-pinned packages in operations
* `--json`: Output in JSON format
* `--outdated-only`: Show only outdated packages
* `-i, --interactive`: Interactively select packages to update
* `--no-cache`: Bypass version cache and query npm directly
* `-v, --verbose`: Verbose output with additional details
* `-q, --quiet`: Minimal output (suppress tables unless updating)
* `-a, --all-packages`: Show all packages including excluded ones
* `--help`: Show this message and exit.

## `voltamanager config`

Create default configuration file.

**Usage**:

```console
$ voltamanager config [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `voltamanager clear-cache`

Clear the npm version cache.

**Usage**:

```console
$ voltamanager clear-cache [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `voltamanager logs`

View voltamanager logs and statistics.

**Usage**:

```console
$ voltamanager logs [OPTIONS]
```

**Options**:

* `--stats`: Show log statistics
* `-n, --tail INTEGER`: Number of log lines to show (default: 20)  [default: 20]
* `--clear`: Clear all log files
* `-s, --search TEXT`: Search logs for specific text
* `--help`: Show this message and exit.

## `voltamanager rollback`

Rollback to previous package versions.

Examples:
    voltamanager rollback              # Rollback all packages
    voltamanager rollback typescript   # Rollback only typescript
    voltamanager rollback eslint prettier --force  # Rollback multiple without confirmation

**Usage**:

```console
$ voltamanager rollback [OPTIONS] [PACKAGES]...
```

**Arguments**:

* `[PACKAGES]...`: Specific packages to rollback (empty for all)

**Options**:

* `-f, --force`: Skip confirmation prompt
* `--help`: Show this message and exit.

## `voltamanager bench`

Benchmark npm registry query performance.

**Usage**:

```console
$ voltamanager bench [OPTIONS]
```

**Options**:

* `-p, --packages INTEGER`: Number of test packages to check  [default: 10]
* `--help`: Show this message and exit.

## `voltamanager health`

Check the health of your volta installation.

Verifies that volta, npm, and node are properly installed and configured.
Useful for troubleshooting installation issues.

Examples:
    voltamanager health    # Run health check

**Usage**:

```console
$ voltamanager health [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `voltamanager audit`

Run security audit on installed packages.

Checks all volta-managed packages for known security vulnerabilities
using npm audit.

Examples:
    voltamanager audit              # Basic audit
    voltamanager audit -v           # Detailed vulnerability info
    voltamanager audit --critical-only  # Only fail on critical vulns

**Usage**:

```console
$ voltamanager audit [OPTIONS]
```

**Options**:

* `-v, --verbose`: Show detailed vulnerability information
* `--critical-only`: Exit with error only if critical vulnerabilities found
* `--help`: Show this message and exit.

## `voltamanager pin`

Pin packages to prevent updates (adds to config exclude list).

Examples:
    voltamanager pin typescript eslint    # Pin typescript and eslint
    voltamanager pin --unpin typescript   # Unpin typescript

**Usage**:

```console
$ voltamanager pin [OPTIONS] PACKAGES...
```

**Arguments**:

* `PACKAGES...`: Package names to pin  [required]

**Options**:

* `--unpin`: Remove packages from pin list
* `--help`: Show this message and exit.

## `voltamanager info`

Show detailed information about a package.

Examples:
    voltamanager info typescript
    voltamanager info @vue/cli

**Usage**:

```console
$ voltamanager info [OPTIONS] PACKAGE
```

**Arguments**:

* `PACKAGE`: Package name to get information about  [required]

**Options**:

* `--help`: Show this message and exit.

## `voltamanager breaking-changes`

Analyze packages with major version updates (breaking changes).

Shows detailed information about packages that have major version bumps,
which may contain breaking changes requiring code updates.

Examples:
    voltamanager breaking-changes              # Check all packages
    voltamanager breaking-changes typescript   # Check specific package

**Usage**:

```console
$ voltamanager breaking-changes [OPTIONS] [PACKAGES]...
```

**Arguments**:

* `[PACKAGES]...`: Specific packages to check (empty for all)

**Options**:

* `--help`: Show this message and exit.
