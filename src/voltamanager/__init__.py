"""Volta Manager - Check and upgrade Volta-managed global packages."""

import tempfile
from pathlib import Path

import typer

from .core import check_dependencies, get_installed_packages, parse_package
from .operations import fast_install, check_and_update
from .config import Config, create_default_config
from .cache import clear_cache

from rich.console import Console

app = typer.Typer(
    help="Check and upgrade Volta-managed global packages",
    add_completion=True,
)
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
    all_packages: bool = typer.Option(
        False, "--all-packages", "-a", help="Show all packages including excluded ones"
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
            all_packages,
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
    tail: int = typer.Option(
        20, "--tail", "-n", help="Number of log lines to show (default: 20)"
    ),
    clear: bool = typer.Option(False, "--clear", help="Clear all log files"),
    search: str = typer.Option(
        "", "--search", "-s", help="Search logs for specific text"
    ),
) -> None:
    """View voltamanager logs and statistics."""
    from .logger import LOG_FILE, get_log_stats

    if clear:
        confirm = typer.confirm(
            "Are you sure you want to clear all log files?", default=False
        )
        if not confirm:
            console.print("[yellow]Clear cancelled[/yellow]")
            return

        if LOG_FILE.exists():
            LOG_FILE.unlink()
            console.print("[green]✓ Logs cleared[/green]")
        else:
            console.print("[yellow]No log file to clear[/yellow]")
        return

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

        with open(LOG_FILE) as f:
            lines = f.readlines()

        # Apply search filter if provided
        if search:
            lines = [line for line in lines if search.lower() in line.lower()]
            console.print(f"\n[dim]Showing entries matching '{search}':[/dim]")
        else:
            console.print(f"\n[dim]Last {min(tail, len(lines))} entries:[/dim]")

        # Show last N lines
        display_lines = lines[-tail:] if tail > 0 else lines

        if not display_lines:
            console.print("[yellow]No matching log entries found[/yellow]")
        else:
            for line in display_lines:
                # Color code by log level
                if " ERROR " in line:
                    console.print(f"[red]{line.rstrip()}[/red]")
                elif " WARNING " in line:
                    console.print(f"[yellow]{line.rstrip()}[/yellow]")
                elif " INFO " in line:
                    console.print(f"[dim]{line.rstrip()}[/dim]")
                else:
                    console.print(line.rstrip())


@app.command(name="rollback")
def rollback(
    packages: list[str] = typer.Argument(
        None, help="Specific packages to rollback (empty for all)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
) -> None:
    """Rollback to previous package versions.

    Examples:
        voltamanager rollback              # Rollback all packages
        voltamanager rollback typescript   # Rollback only typescript
        voltamanager rollback eslint prettier --force  # Rollback multiple without confirmation
    """
    import json
    import subprocess
    from pathlib import Path
    from rich.table import Table

    snapshot_file = Path.home() / ".voltamanager" / "last_snapshot.json"
    if not snapshot_file.exists():
        console.print("[red]✗ No snapshot found - cannot rollback[/red]")
        console.print(
            "[yellow]💡 Snapshots are created before updates with --update[/yellow]"
        )
        raise typer.Exit(1)

    snapshot = json.loads(snapshot_file.read_text())

    # Filter packages if specific ones requested
    if packages:
        filtered_snapshot = {
            name: ver for name, ver in snapshot.items() if name in packages
        }
        if not filtered_snapshot:
            console.print(
                "[red]✗ None of the specified packages found in snapshot[/red]"
            )
            console.print(
                f"[dim]Available: {', '.join(sorted(snapshot.keys())[:5])}...[/dim]"
            )
            raise typer.Exit(1)

        missing = set(packages) - set(filtered_snapshot.keys())
        if missing:
            console.print(
                f"[yellow]⚠ Packages not in snapshot (will be skipped): {', '.join(missing)}[/yellow]"
            )

        snapshot = filtered_snapshot

    packages_to_install = [f"{name}@{ver}" for name, ver in snapshot.items()]

    # Show what will be rolled back
    console.print("\n[bold]Rollback Preview:[/bold]")
    table = Table(show_header=True)
    table.add_column("Package", style="cyan")
    table.add_column("Version to Restore", style="yellow")

    for name, ver in sorted(snapshot.items())[:10]:  # Show first 10
        table.add_row(name, ver)

    if len(snapshot) > 10:
        table.add_row("...", f"...and {len(snapshot) - 10} more packages")

    console.print(table)
    console.print(
        f"\n[yellow]Total packages to rollback: {len(packages_to_install)}[/yellow]"
    )

    # Confirmation
    if not force:
        confirm = typer.confirm(
            "\nAre you sure you want to rollback to these versions?", default=False
        )
        if not confirm:
            console.print("[yellow]Rollback cancelled[/yellow]")
            raise typer.Exit(0)

    console.print("\n[yellow]Rolling back packages...[/yellow]")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["volta", "install"] + packages_to_install, cwd=Path(tmpdir), check=True
            )
        console.print("[green]✓ Rollback complete[/green]")
        console.print(
            f"[dim]Rolled back {len(packages_to_install)} packages to previous versions[/dim]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Rollback failed with code {e.returncode}[/red]")
        console.print(
            "[yellow]💡 Some packages may have been partially rolled back[/yellow]"
        )
        raise typer.Exit(e.returncode)


@app.command(name="bench")
def benchmark(
    packages: int = typer.Option(
        10, "--packages", "-p", help="Number of test packages to check"
    ),
) -> None:
    """Benchmark npm registry query performance."""
    import time
    from rich.table import Table
    from .npm import get_latest_version, get_latest_versions_parallel

    console.print("[bold]Running performance benchmark...[/bold]\n")

    # Test packages (common popular packages)
    test_packages = [
        "typescript",
        "eslint",
        "prettier",
        "webpack",
        "vite",
        "react",
        "vue",
        "express",
        "lodash",
        "axios",
        "jest",
        "mocha",
        "babel",
        "rollup",
        "esbuild",
        "@types/node",
        "@vue/cli",
        "@angular/core",
        "@babel/core",
        "@webpack-cli/serve",
    ][:packages]

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        # Sequential benchmark
        console.print("[cyan]Sequential queries...[/cyan]")
        sequential_start = time.time()
        for pkg in test_packages:
            get_latest_version(pkg, safe_dir)
        sequential_time = time.time() - sequential_start

        # Parallel benchmark (default workers)
        console.print("[cyan]Parallel queries (10 workers)...[/cyan]")
        parallel_start = time.time()
        get_latest_versions_parallel(
            [(pkg, "1.0.0") for pkg in test_packages], safe_dir, max_workers=10
        )
        parallel_time = time.time() - parallel_start

        # Parallel benchmark (high concurrency)
        console.print("[cyan]Parallel queries (20 workers)...[/cyan]")
        parallel_high_start = time.time()
        get_latest_versions_parallel(
            [(pkg, "1.0.0") for pkg in test_packages], safe_dir, max_workers=20
        )
        parallel_high_time = time.time() - parallel_high_start

    # Display results
    console.print("\n[bold]Results:[/bold]")
    table = Table(show_header=True)
    table.add_column("Method", style="cyan")
    table.add_column("Time (s)", justify="right", style="yellow")
    table.add_column("Speedup", justify="right", style="green")
    table.add_column("Pkgs/sec", justify="right", style="blue")

    baseline = sequential_time
    table.add_row(
        "Sequential",
        f"{sequential_time:.2f}",
        "1.00×",
        f"{packages / sequential_time:.1f}",
    )
    table.add_row(
        "Parallel (10 workers)",
        f"{parallel_time:.2f}",
        f"{baseline / parallel_time:.2f}×",
        f"{packages / parallel_time:.1f}",
    )
    table.add_row(
        "Parallel (20 workers)",
        f"{parallel_high_time:.2f}",
        f"{baseline / parallel_high_time:.2f}×",
        f"{packages / parallel_high_time:.1f}",
    )

    console.print(table)

    console.print(f"\n[dim]Tested with {packages} packages[/dim]")
    console.print(
        "[green]💡 Recommendation:[/green] Use parallel mode (default) for best performance"
    )


@app.command(name="health")
def health_check() -> None:
    """Check the health of your volta installation.

    Verifies that volta, npm, and node are properly installed and configured.
    Useful for troubleshooting installation issues.

    Examples:
        voltamanager health    # Run health check
    """
    from .core import check_volta_health, display_health_check

    results = check_volta_health()
    display_health_check(results)

    # Exit with error code if critical issues found
    critical_issues = ["volta not found in PATH", "npm not found in PATH"]
    has_critical = any(issue in results["issues"] for issue in critical_issues)

    if has_critical:
        raise typer.Exit(1)


@app.command(name="audit")
def security_audit(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed vulnerability information"
    ),
    critical_only: bool = typer.Option(
        False,
        "--critical-only",
        help="Exit with error only if critical vulnerabilities found",
    ),
) -> None:
    """Run security audit on installed packages.

    Checks all volta-managed packages for known security vulnerabilities
    using npm audit.

    Examples:
        voltamanager audit              # Basic audit
        voltamanager audit -v           # Detailed vulnerability info
        voltamanager audit --critical-only  # Only fail on critical vulns
    """
    from .security import check_package_vulnerabilities
    from .core import get_installed_packages, parse_package, check_dependencies

    # Check dependencies first
    if not check_dependencies():
        raise typer.Exit(127)

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        # Get installed packages
        namevers = get_installed_packages(safe_dir)
        if not namevers:
            console.print("[yellow]No packages to audit[/yellow]")
            raise typer.Exit(0)

        # Extract package names
        packages = []
        for name_ver in namevers:
            name, ver = parse_package(name_ver)
            if ver != "project":  # Skip project-pinned packages
                packages.append(name)

        if not packages:
            console.print(
                "[yellow]No packages to audit (only project-pinned found)[/yellow]"
            )
            raise typer.Exit(0)

        console.print(f"[dim]Auditing {len(packages)} packages...[/dim]\n")

        # Run security audit
        has_critical, audit_data = check_package_vulnerabilities(
            packages, safe_dir, verbose
        )

        # Exit with error if critical vulnerabilities found and flag set
        if critical_only and has_critical:
            console.print("\n[red]✗ Critical vulnerabilities detected[/red]")
            raise typer.Exit(1)
        elif (
            audit_data
            and audit_data.get("metadata", {})
            .get("vulnerabilities", {})
            .get("total", 0)
            > 0
        ):
            raise typer.Exit(1)


@app.command(name="pin")
def pin_package(
    packages: list[str] = typer.Argument(..., help="Package names to pin"),
    unpin: bool = typer.Option(False, "--unpin", help="Remove packages from pin list"),
) -> None:
    """Pin packages to prevent updates (adds to config exclude list).

    Examples:
        voltamanager pin typescript eslint    # Pin typescript and eslint
        voltamanager pin --unpin typescript   # Unpin typescript
    """
    from .config import Config

    config = Config()

    if unpin:
        # Remove from exclude list
        removed = []
        for pkg in packages:
            if pkg in config.exclude:
                config.exclude.remove(pkg)
                removed.append(pkg)

        if removed:
            config.save()
            console.print(
                f"[green]✓ Unpinned {len(removed)} package(s): {', '.join(removed)}[/green]"
            )
        else:
            console.print("[yellow]None of the specified packages were pinned[/yellow]")
    else:
        # Add to exclude list
        added = []
        for pkg in packages:
            if pkg not in config.exclude:
                config.exclude.append(pkg)
                added.append(pkg)

        if added:
            config.save()
            console.print(
                f"[green]✓ Pinned {len(added)} package(s): {', '.join(added)}[/green]"
            )
            console.print(
                "[dim]These packages will be excluded from future updates[/dim]"
            )
        else:
            console.print("[yellow]All specified packages were already pinned[/yellow]")

    # Show current pinned packages
    if config.exclude:
        console.print("\n[bold]Currently pinned packages:[/bold]")
        for pkg in sorted(config.exclude):
            console.print(f"  [cyan]• {pkg}[/cyan]")


@app.command(name="info")
def package_info(
    package: str = typer.Argument(..., help="Package name to get information about"),
) -> None:
    """Show detailed information about a package.

    Examples:
        voltamanager info typescript
        voltamanager info @vue/cli
    """
    import subprocess
    import json
    from pathlib import Path

    console.print(f"[cyan]Fetching information for {package}...[/cyan]\n")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_dir = Path(tmpdir)

            # Get full package info from npm
            result = subprocess.run(
                ["npm", "view", package, "--json"],
                cwd=safe_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            data = json.loads(result.stdout)

            # Display basic info
            console.print(
                f"[bold]Package:[/bold] [cyan]{data.get('name', package)}[/cyan]"
            )
            console.print(f"[bold]Description:[/bold] {data.get('description', 'N/A')}")
            console.print(
                f"[bold]Latest Version:[/bold] [green]{data.get('version', 'N/A')}[/green]"
            )

            # License
            license_info = data.get("license", "N/A")
            console.print(f"[bold]License:[/bold] {license_info}")

            # Links
            if homepage := data.get("homepage"):
                console.print(f"[bold]Homepage:[/bold] {homepage}")

            if repo := data.get("repository"):
                if isinstance(repo, dict):
                    repo_url = repo.get("url", "")
                else:
                    repo_url = repo
                console.print(f"[bold]Repository:[/bold] {repo_url}")

            # Maintainers
            if maintainers := data.get("maintainers"):
                console.print("\n[bold]Maintainers:[/bold]")
                for m in maintainers[:3]:  # Show first 3
                    name = m.get("name", "Unknown")
                    email = m.get("email", "")
                    console.print(f"  • {name} {f'<{email}>' if email else ''}")

            # Time info
            if time_data := data.get("time"):
                modified = time_data.get("modified", "")
                created = time_data.get("created", "")
                if created:
                    console.print(f"\n[bold]Created:[/bold] {created.split('T')[0]}")
                if modified:
                    console.print(
                        f"[bold]Last Modified:[/bold] {modified.split('T')[0]}"
                    )

            # Dependencies
            if deps := data.get("dependencies"):
                console.print(f"\n[bold]Dependencies:[/bold] {len(deps)} packages")

            # Note: npm doesn't provide download stats directly via CLI
            # Would need to query npm registry API separately
            console.print(
                f"\n[dim]💡 For download stats, visit: https://www.npmjs.com/package/{package}[/dim]"
            )

    except subprocess.CalledProcessError:
        console.print(f"[red]✗ Package '{package}' not found or npm query failed[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError:
        console.print("[red]✗ Failed to parse npm response[/red]")
        raise typer.Exit(1)
    except subprocess.TimeoutExpired:
        console.print("[red]✗ npm query timed out[/red]")
        raise typer.Exit(1)


@app.command(name="breaking-changes")
def breaking_changes(
    packages: list[str] = typer.Argument(
        None, help="Specific packages to check (empty for all)"
    ),
) -> None:
    """Analyze packages with major version updates (breaking changes).

    Shows detailed information about packages that have major version bumps,
    which may contain breaking changes requiring code updates.

    Examples:
        voltamanager breaking-changes              # Check all packages
        voltamanager breaking-changes typescript   # Check specific package
    """
    from rich.table import Table
    from .utils import get_major_updates, get_changelog_url

    # Check dependencies
    if not check_dependencies():
        raise typer.Exit(code=127)

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        # Get installed packages
        console.print("[dim]Fetching installed packages...[/dim]")
        namevers = get_installed_packages(safe_dir)

        if not namevers:
            console.print("[yellow]No Volta-managed packages found.[/yellow]")
            raise typer.Exit(code=0)

        # Parse packages
        pkg_list = []
        names_list = []
        for name_ver in namevers:
            name, ver = parse_package(name_ver)
            if ver != "project":  # Skip project-pinned
                pkg_list.append((name, ver))
                names_list.append(name)

        # Filter by specified packages if provided
        if packages:
            pkg_list = [(n, v) for n, v in pkg_list if n in packages]
            names_list = [n for n in names_list if n in packages]

            if not pkg_list:
                console.print(
                    "[yellow]None of the specified packages are installed[/yellow]"
                )
                raise typer.Exit(code=1)

        console.print(f"[dim]Checking {len(pkg_list)} packages for updates...[/dim]\n")

        # Get latest versions
        from .npm import get_latest_versions_parallel

        latest_dict = get_latest_versions_parallel(pkg_list, safe_dir)

        # Build lists for analysis
        names = []
        installed = []
        latest = []
        states = []

        for name, ver in pkg_list:
            names.append(name)
            installed.append(ver)
            lat = latest_dict.get(name) or "?"
            latest.append(lat)

            if lat == "?" or lat is None:
                states.append("UNKNOWN")
            elif ver == lat:
                states.append("up-to-date")
            else:
                states.append("OUTDATED")

        # Get major updates
        major_updates = get_major_updates(names, installed, latest, states)

        if not major_updates:
            console.print("[green]✓ No major version updates detected![/green]")
            console.print(
                "[dim]All packages are either up-to-date or have minor/patch updates only.[/dim]"
            )
            raise typer.Exit(code=0)

        # Display results
        console.print(
            f"[yellow]⚠ Found {len(major_updates)} packages with major version updates:[/yellow]\n"
        )

        table = Table(show_header=True, header_style="bold red")
        table.add_column("Package", style="cyan", width=35)
        table.add_column("Current", style="yellow", width=12)
        table.add_column("Latest", style="green", width=12)
        table.add_column("Changelog", style="blue", width=50)

        for pkg_name, current, lat in major_updates:
            changelog = get_changelog_url(pkg_name)
            table.add_row(pkg_name, current, lat, changelog)

        console.print(table)

        console.print("\n[bold]⚠ Breaking Changes Warning:[/bold]")
        console.print(
            "  Major version updates often contain breaking changes that may require"
        )
        console.print("  code changes or configuration updates in your projects.")
        console.print(
            "\n[dim]💡 Review changelogs before updating to understand the impact.[/dim]"
        )


if __name__ == "__main__":
    app()
