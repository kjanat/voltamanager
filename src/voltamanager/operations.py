"""Package operations and management."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .cache import cache_version, get_cached_version
from .config import Config
from .core import parse_package
from .display import (
    display_dry_run_report,
    display_json,
    display_statistics,
    display_table,
)
from .logger import log_error, log_operation, setup_logger
from .npm import get_latest_versions_parallel
from .utils import (
    check_disk_space,
    check_local_volta_config,
    estimate_update_size,
    get_changelog_url,
    get_major_updates,
    get_minor_updates,
)

console = Console()
logger = setup_logger()

HISTORY_DIR = Path.home() / ".voltamanager"
HISTORY_FILE = HISTORY_DIR / "history.log"
SNAPSHOT_FILE = HISTORY_DIR / "last_snapshot.json"


def log_update(packages: list[str]) -> None:
    """Log package updates to history file and structured logger."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    # Legacy history file
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
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
    SNAPSHOT_FILE.write_text(json.dumps(packages, indent=2), encoding="utf-8")
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
        subprocess.run(["volta", "install", *packages], cwd=safe_dir, check=True)
        log_update(packages)
        log_operation(logger, "fast_install_success", count=len(packages))
        return 0
    except subprocess.CalledProcessError as e:
        log_error(
            logger, f"Fast install failed with code {e.returncode}", count=len(packages)
        )
        return e.returncode


def check_and_update(  # noqa: C901, PLR0913, PLR0917, PLR0911, PLR0912, PLR0915, PLR0914
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
    verbose: bool = False,
    all_packages: bool = False,
) -> int:
    """Check versions and optionally update packages."""
    # Check for local volta configuration
    check_local_volta_config(verbose)

    names = []
    installed = []
    latest = []
    states = []
    to_install = []
    snapshot = {}
    excluded_packages = []

    # Parse packages and prepare for version checking
    packages_to_check = []
    for name_ver in namevers:
        name, ver = parse_package(name_ver)

        # Track excluded packages if --all-packages flag is set
        if config.should_exclude(name):
            if all_packages:
                excluded_packages.append((name, ver))
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
            cached = get_cached_version(name, config.cache_ttl_hours)
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

    # Add excluded packages to display if --all-packages flag is set
    if all_packages and excluded_packages:
        for name, ver in excluded_packages:
            names.append(name)
            installed.append(ver)
            latest.append("-")
            states.append("EXCLUDED")

    # Display check results
    if do_check:
        if json_output:
            display_json(names, installed, latest, states)
        else:
            display_table(names, installed, latest, states, outdated_only)
            display_statistics(states)

            # Show info about excluded packages if not showing them
            if excluded_packages and not all_packages:
                console.print(
                    f"\n[dim]i {len(excluded_packages)} package(s) excluded (use --all-packages to see them)[/dim]"
                )

            # Warn about major version updates
            major_updates = get_major_updates(names, installed, latest, states)
            minor_updates = get_minor_updates(names, installed, latest, states)

            if major_updates:
                console.print(
                    "\n[yellow]⚠ Major version updates detected (may have breaking changes):[/yellow]"
                )
                for pkg_name, current, lat in major_updates[:5]:  # Show first 5
                    changelog = get_changelog_url(pkg_name)
                    console.print(f"  [yellow]• {pkg_name}: {current} → {lat}[/yellow]")
                    console.print(f"    [dim]{changelog}[/dim]")

                if len(major_updates) > 5:
                    console.print(
                        f"  [dim]...and {len(major_updates) - 5} more major updates[/dim]"
                    )

            if minor_updates and do_update:
                console.print(
                    f"\n[cyan]i {len(minor_updates)} minor/patch updates available (typically safe)[/cyan]"
                )

    # Perform updates
    if do_update:
        if not to_install:
            console.print("[green]All packages are up to date.[/green]")
            return 0

        # Pre-update safety checks
        if not dry_run:
            # Check disk space
            estimated_size = estimate_update_size(len(to_install))
            sufficient_space, available_mb = check_disk_space(estimated_size)

            if not sufficient_space and available_mb >= 0:
                console.print("[red]✗ Insufficient disk space[/red]")
                console.print(
                    f"[yellow]  Estimated needed: ~{estimated_size}MB[/yellow]"
                )
                console.print(f"[yellow]  Available: {available_mb}MB[/yellow]")
                console.print("\n[yellow]💡 Suggestions:[/yellow]")
                console.print("  • Free up disk space")
                console.print("  • Update fewer packages at once")
                console.print("  • Use --interactive to select specific packages")
                return 1

            if verbose and available_mb >= 0:
                console.print(
                    f"[dim]✓ Disk space check passed ({available_mb}MB available)[/dim]"
                )

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

        # Update with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Updating {len(to_install)} package(s)...", total=None
            )
            try:
                subprocess.run(
                    ["volta", "install", *to_install], cwd=safe_dir, check=True
                )
                progress.update(task, completed=True)
                console.print("[green]✓ Update complete[/green]")
                log_update(to_install)
                return 0
            except subprocess.CalledProcessError as e:
                progress.update(task, completed=True)
                console.print(f"[red]✗ Update failed with code {e.returncode}[/red]")
                return e.returncode

    return 0
