"""Package operations and management."""

import subprocess
import json
from pathlib import Path
from datetime import datetime

from rich.console import Console
import typer

from .core import parse_package
from .npm import get_latest_versions_parallel
from .cache import get_cached_version, cache_version
from .display import (
    display_table,
    display_json,
    display_statistics,
    display_dry_run_report,
)
from .config import Config
from .logger import setup_logger, log_operation, log_error

console = Console()
logger = setup_logger()

HISTORY_DIR = Path.home() / ".voltamanager"
HISTORY_FILE = HISTORY_DIR / "history.log"
SNAPSHOT_FILE = HISTORY_DIR / "last_snapshot.json"


def log_update(packages: list[str]) -> None:
    """Log package updates to history file and structured logger."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    # Legacy history file
    with open(HISTORY_FILE, "a") as f:
        timestamp = datetime.now().isoformat()
        f.write(
            f"{timestamp} - Updated {len(packages)} packages: {', '.join(packages)}\n"
        )

    # Structured logging
    log_operation(
        logger, "batch_update", count=len(packages), packages=", ".join(packages)
    )


def save_snapshot(packages: dict[str, str]) -> None:
    """Save current package state for rollback."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_FILE.write_text(json.dumps(packages, indent=2))
    log_operation(logger, "snapshot", count=len(packages))


def fast_install(packages: list[str], safe_dir: Path, dry_run: bool) -> int:
    """Install packages without version checking."""
    if not packages:
        console.print(
            "[yellow]Nothing to install (only project-pinned found).[/yellow]"
        )
        return 0

    if dry_run:
        console.print(f"[cyan]Would install:[/cyan] {', '.join(packages)}")
        log_operation(logger, "fast_install_dry_run", count=len(packages))
        return 0

    try:
        log_operation(logger, "fast_install_start", count=len(packages))
        subprocess.run(["volta", "install"] + packages, cwd=safe_dir, check=True)
        log_update(packages)
        log_operation(logger, "fast_install_success", count=len(packages))
        return 0
    except subprocess.CalledProcessError as e:
        log_error(
            logger, f"Fast install failed with code {e.returncode}", count=len(packages)
        )
        return e.returncode


def check_and_update(
    namevers: list[str],
    safe_dir: Path,
    do_check: bool,
    do_update: bool,
    dry_run: bool,
    include_project: bool,
    json_output: bool,
    outdated_only: bool,
    interactive: bool,
    use_cache: bool,
    config: Config,
) -> int:
    """Check versions and optionally update packages."""

    names = []
    installed = []
    latest = []
    states = []
    to_install = []
    snapshot = {}

    # Parse packages and prepare for version checking
    packages_to_check = []
    for name_ver in namevers:
        name, ver = parse_package(name_ver)

        # Skip excluded packages
        if config.should_exclude(name):
            continue

        if ver == "project":
            names.append(name)
            installed.append(ver)
            latest.append("-")
            states.append("PROJECT")
            if include_project:
                to_install.append(f"{name}@latest")
            continue

        snapshot[name] = ver
        packages_to_check.append((name, ver))

    # Check versions (parallel with caching)
    if use_cache:
        # Try cache first
        for name, ver in packages_to_check:
            cached = get_cached_version(name)
            if cached:
                lat = cached
            else:
                # Will be checked in parallel batch
                lat = None

            if lat:
                names.append(name)
                installed.append(ver)
                latest.append(lat)
                if ver == lat:
                    states.append("up-to-date")
                else:
                    states.append("OUTDATED")
                    to_install.append(f"{name}@latest")

        # Get uncached packages
        uncached = [(n, v) for n, v in packages_to_check if n not in names]
        if uncached:
            latest_versions = get_latest_versions_parallel(
                uncached, safe_dir, config.parallel_checks
            )
            for name, ver in uncached:
                lat = latest_versions.get(name)
                if lat:
                    cache_version(name, lat)

                names.append(name)
                installed.append(ver)
                if lat is None:
                    latest.append("?")
                    states.append("UNKNOWN")
                else:
                    latest.append(lat)
                    if ver == lat:
                        states.append("up-to-date")
                    else:
                        states.append("OUTDATED")
                        to_install.append(f"{name}@latest")
    else:
        # No cache, check all in parallel
        latest_versions = get_latest_versions_parallel(
            packages_to_check, safe_dir, config.parallel_checks
        )
        for name, ver in packages_to_check:
            lat = latest_versions.get(name)
            names.append(name)
            installed.append(ver)
            if lat is None:
                latest.append("?")
                states.append("UNKNOWN")
            else:
                latest.append(lat)
                if ver == lat:
                    states.append("up-to-date")
                else:
                    states.append("OUTDATED")
                    to_install.append(f"{name}@latest")

    # Display check results
    if do_check:
        if json_output:
            display_json(names, installed, latest, states)
        else:
            display_table(names, installed, latest, states, outdated_only)
            display_statistics(states)

    # Perform updates
    if do_update:
        if not to_install:
            console.print("[green]All packages are up to date.[/green]")
            return 0

        # Interactive mode
        if interactive and to_install:
            selected = []
            for pkg in to_install:
                pkg_name = pkg.rsplit("@", 1)[0]
                if typer.confirm(f"Update {pkg_name}?", default=True):
                    selected.append(pkg)
            to_install = selected

            if not to_install:
                console.print("[yellow]No packages selected for update.[/yellow]")
                return 0

        if dry_run:
            display_dry_run_report(to_install, names, installed, latest)
            return 0

        # Save snapshot before updating
        save_snapshot(snapshot)

        console.print(f"[yellow]Updating {len(to_install)} package(s)...[/yellow]")
        try:
            subprocess.run(["volta", "install"] + to_install, cwd=safe_dir, check=True)
            console.print("[green]✓ Update complete[/green]")
            log_update(to_install)
            return 0
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗ Update failed with code {e.returncode}[/red]")
            return e.returncode

    return 0
