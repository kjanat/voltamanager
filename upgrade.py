#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pathlib",
#     "rich",
#     "typer",
#     "typing",
# ]
# ///

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Check and upgrade Volta-managed global packages")
console = Console()


def check_dependencies() -> bool:
    """Check if required commands are available."""
    if not shutil.which("volta"):
        console.print("[red]volta not found in PATH[/red]", file=sys.stderr)
        return False
    if not shutil.which("npm"):
        console.print(
            "[red]npm not found (needed to query registry)[/red]", file=sys.stderr
        )
        return False
    return True


def get_installed_packages(safe_dir: Path) -> List[str]:
    """Get the list of Volta-managed packages."""
    try:
        result = subprocess.run(
            ["volta", "list", "--format=plain"],
            cwd=safe_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        packages = []
        for line in result.stdout.splitlines():
            if line.startswith("package "):
                packages.append(line.split()[1])
        return packages
    except subprocess.CalledProcessError:
        return []


def parse_package(name_ver: str) -> Tuple[str, str]:
    """Parse the package@version string into (name, version)."""
    if "@" not in name_ver:
        return name_ver, ""

    # Handle scoped packages like @vue/cli@5.0.8
    if name_ver.startswith("@"):
        parts = name_ver.rsplit("@", 1)
        return parts[0], parts[1] if len(parts) == 2 else ""

    parts = name_ver.split("@")
    return parts[0], parts[1] if len(parts) > 1 else ""


def get_latest_version(package_name: str, safe_dir: Path) -> Optional[str]:
    """Query npm registry for the latest versions of packages."""
    try:
        result = subprocess.run(
            ["npm", "view", package_name, "version"],
            cwd=safe_dir,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def fast_install(packages: List[str], safe_dir: Path, dry_run: bool) -> int:
    """Install packages without version checking."""
    if not packages:
        console.print(
            "[yellow]Nothing to install (only project-pinned found).[/yellow]"
        )
        return 0

    if dry_run:
        console.print(f"[cyan]Would install:[/cyan] {', '.join(packages)}")
        return 0

    try:
        subprocess.run(["volta", "install"] + packages, cwd=safe_dir, check=True)
        return 0
    except subprocess.CalledProcessError as e:
        return e.returncode


def check_and_update(
    namevers: List[str],
    safe_dir: Path,
    do_check: bool,
    do_update: bool,
    dry_run: bool,
    include_project: bool,
) -> int:
    """Check versions and optionally update packages."""

    names = []
    installed = []
    latest = []
    states = []
    to_install = []

    for name_ver in namevers:
        name, ver = parse_package(name_ver)

        if ver == "project":
            names.append(name)
            installed.append(ver)
            latest.append("-")
            states.append("PROJECT")
            if include_project:
                to_install.append(f"{name}@latest")
            continue

        lat = get_latest_version(name, safe_dir)

        if lat is None:
            lat = "?"
            st = "UNKNOWN"
        elif ver == lat:
            st = "up-to-date"
        else:
            st = "OUTDATED"
            to_install.append(f"{name}@latest")

        names.append(name)
        installed.append(ver)
        latest.append(lat)
        states.append(st)

    # Display check results
    if do_check:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Package", style="cyan", width=42)
        table.add_column("Installed", style="blue", width=12)
        table.add_column("Latest", style="blue", width=12)
        table.add_column("Status", width=12)

        for i in range(len(names)):
            status_style = ""
            if states[i] == "OUTDATED":
                status_style = "yellow"
            elif states[i] == "up-to-date":
                status_style = "green"
            elif states[i] == "PROJECT":
                status_style = "dim"

            table.add_row(
                names[i],
                installed[i],
                latest[i],
                f"[{status_style}]{states[i]}[/{status_style}]",
            )

        console.print(table)

    # Perform updates
    if do_update:
        if not to_install:
            console.print("[green]All packages are up to date.[/green]")
            return 0

        if dry_run:
            console.print(
                f"[cyan]Would update ({len(to_install)} package(s)):[/cyan] {', '.join(to_install)}"
            )
            return 0

        console.print(f"[yellow]Updating {len(to_install)} package(s)...[/yellow]")
        try:
            subprocess.run(["volta", "install"] + to_install, cwd=safe_dir, check=True)
            console.print("[green]✓ Update complete[/green]")
            return 0
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗ Update failed with code {e.returncode}[/red]")
            return e.returncode

    return 0


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
):
    """
    Check and upgrade Volta-managed global packages.

    By default, it shows the current status of all installed packages.
    Use --update to actually update outdated packages.
    """

    # Determine behavior flags
    do_check = not force
    do_update = force or update

    # Check dependencies
    if not check_dependencies():
        raise typer.Exit(code=127)

    # Create a safe temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        # Get installed packages
        namevers = get_installed_packages(safe_dir)

        if not namevers:
            console.print("[yellow]No Volta-managed packages found.[/yellow]")
            raise typer.Exit(code=0)

        # Fast path: install without version checks
        if not do_check and not do_update:
            packages = []
            for name_ver in namevers:
                name, ver = parse_package(name_ver)
                if ver == "project" and not include_project:
                    continue
                packages.append(name)

            # Remove duplicates and sort
            packages = sorted(set(packages))
            code = fast_install(packages, safe_dir, dry)
            raise typer.Exit(code=code)

        # Full check/update path
        code = check_and_update(
            namevers, safe_dir, do_check, do_update, dry, include_project
        )
        raise typer.Exit(code=code)


if __name__ == "__main__":
    app()
