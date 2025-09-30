"""Volta Manager - Check and upgrade Volta-managed global packages."""

import tempfile
from pathlib import Path

import typer

from .core import check_dependencies, get_installed_packages, parse_package
from .operations import fast_install, check_and_update
from .config import Config, create_default_config
from .cache import clear_cache

from rich.console import Console

app = typer.Typer(help="Check and upgrade Volta-managed global packages")
console = Console()


@app.command()
def main(
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip version check and force update all packages"
    ),
    update: bool = typer.Option(
        False, "--update", "-u", help="Update outdated packages"
    ),
    dry: bool = typer.Option(
        False, "--dry", help="Show what would be done without doing it"
    ),
    include_project: bool = typer.Option(
        False, "--include-project", help="Include project-pinned packages in operations"
    ),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    outdated_only: bool = typer.Option(
        False, "--outdated-only", help="Show only outdated packages"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactively select packages to update"
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass version cache and query npm directly"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output with additional details"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Minimal output (suppress tables unless updating)"
    ),
) -> None:
    """
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
    """

    # Load configuration
    config = Config()

    # Determine behavior flags
    do_check = not force
    do_update = force or update

    # Quiet mode suppresses table unless updating
    if quiet and not do_update:
        do_check = False

    # Check dependencies
    if not check_dependencies():
        raise typer.Exit(code=127)

    # Create a safe temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        # Get installed packages
        if verbose:
            console.print("[dim]Fetching installed packages...[/dim]")
        namevers = get_installed_packages(safe_dir)

        if not namevers:
            console.print("[yellow]No Volta-managed packages found.[/yellow]")
            raise typer.Exit(code=0)

        if verbose:
            console.print(f"[dim]Found {len(namevers)} packages[/dim]")

        # Fast path: install without version checks
        if not do_check and not do_update:
            packages = []
            for name_ver in namevers:
                name, ver = parse_package(name_ver)
                if ver == "project" and not include_project:
                    continue
                if config.should_exclude(name):
                    continue
                packages.append(name)

            # Remove duplicates and sort
            packages = sorted(set(packages))
            code = fast_install(packages, safe_dir, dry)
            raise typer.Exit(code=code)

        # Full check/update path
        code = check_and_update(
            namevers,
            safe_dir,
            do_check,
            do_update,
            dry,
            include_project or config.include_project,
            json,
            outdated_only,
            interactive,
            not no_cache,
            config,
            verbose,
        )
        raise typer.Exit(code=code)


@app.command(name="config")
def config_command() -> None:
    """Create default configuration file."""
    create_default_config()
    config_file = Path.home() / ".config" / "voltamanager" / "config.toml"
    console.print(f"[green]Created default config at:[/green] {config_file}")


@app.command(name="clear-cache")
def clear_cache_command() -> None:
    """Clear the npm version cache."""
    clear_cache()
    console.print("[green]✓ Cache cleared[/green]")


@app.command(name="logs")
def logs_command(
    stats: bool = typer.Option(False, "--stats", help="Show log statistics"),
) -> None:
    """View voltamanager logs and statistics."""
    from .logger import LOG_FILE, get_log_stats

    if stats:
        stats_data = get_log_stats()
        console.print("[bold]Log Statistics:[/bold]")
        console.print(f"  Total entries: {stats_data['total_lines']}")
        console.print(f"  Errors: {stats_data['errors']}")
        console.print(f"  Updates: {stats_data['updates']}")
        if stats_data["operations"]:
            console.print("  Operations:")
            for op, count in stats_data["operations"].items():
                console.print(f"    {op}: {count}")
    else:
        if not LOG_FILE.exists():
            console.print("[yellow]No log file found[/yellow]")
            return

        console.print(f"[bold]Log file:[/bold] {LOG_FILE}")
        console.print("\n[dim]Last 20 entries:[/dim]")
        with open(LOG_FILE) as f:
            lines = f.readlines()
            for line in lines[-20:]:
                console.print(line.rstrip())


@app.command(name="rollback")
def rollback() -> None:
    """Rollback to previous package versions."""
    import json
    import subprocess
    from pathlib import Path

    snapshot_file = Path.home() / ".voltamanager" / "last_snapshot.json"
    if not snapshot_file.exists():
        console.print("[red]No snapshot found - cannot rollback[/red]")
        console.print(
            "[yellow]Snapshots are created before updates with --update[/yellow]"
        )
        raise typer.Exit(1)

    snapshot = json.loads(snapshot_file.read_text())
    packages = [f"{name}@{ver}" for name, ver in snapshot.items()]

    console.print(f"[yellow]Rolling back {len(packages)} packages...[/yellow]")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["volta", "install"] + packages, cwd=Path(tmpdir), check=True
            )
        console.print("[green]✓ Rollback complete[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Rollback failed with code {e.returncode}[/red]")
        raise typer.Exit(e.returncode)


if __name__ == "__main__":
    app()
