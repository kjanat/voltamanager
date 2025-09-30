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
* `--help`: Show this message and exit.

## `voltamanager rollback`

Rollback to previous package versions.

**Usage**:

```console
$ voltamanager rollback [OPTIONS]
```

**Options**:

* `-f, --force`: Skip confirmation prompt
* `--help`: Show this message and exit.
