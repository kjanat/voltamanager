"""Core logic for package management."""

import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, TypedDict

from rich.console import Console


class HealthCheckResult(TypedDict):
    """Type definition for health check results."""

    volta_installed: bool
    npm_installed: bool
    volta_version: str | None
    npm_version: str | None
    node_version: str | None
    volta_home: str | None
    packages_count: int
    issues: list[str]


console = Console()


def check_dependencies() -> bool:
    """Check if required commands are available."""
    if not shutil.which("volta"):
        console.print("[red]✗ volta not found in PATH[/red]")
        console.print("\n[yellow]To fix this:[/yellow]")
        console.print(
            "  1. Install volta: [cyan]curl https://get.volta.sh | bash[/cyan]"
        )
        console.print("  2. Or visit: [cyan]https://volta.sh[/cyan]")
        console.print("  3. Restart your terminal after installation to update PATH")
        return False
    if not shutil.which("npm"):
        console.print("[red]✗ npm not found (needed to query registry)[/red]")
        console.print("\n[yellow]To fix this:[/yellow]")
        console.print("  1. Install Node.js via volta: [cyan]volta install node[/cyan]")
        console.print("  2. Or ensure npm is in your PATH")
        console.print("  3. Verify with: [cyan]which npm[/cyan]")
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
    except subprocess.CalledProcessError as e:
        console.print("[red]✗ Failed to get installed packages[/red]")
        console.print(f"[dim]Error code: {e.returncode}[/dim]")
        if e.stderr:
            console.print(
                f"[dim]{e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}[/dim]"
            )
        console.print("\n[yellow]💡 Suggestions:[/yellow]")
        console.print("  • Verify volta is working: [cyan]volta list[/cyan]")
        console.print("  • Check volta installation: [cyan]volta --version[/cyan]")
        return []


def parse_package(name_ver: str) -> Tuple[str, str]:
    """Parse the package@version string into (name, version)."""
    if "@" not in name_ver:
        return name_ver, ""

    # Handle scoped packages like @vue/cli@5.0.8
    if name_ver.startswith("@"):
        # For scoped packages, need at least two @ symbols for a version
        at_count = name_ver.count("@")
        if at_count < 2:
            # No version, just scoped package name
            return name_ver, ""
        parts = name_ver.rsplit("@", 1)
        return parts[0], parts[1]

    parts = name_ver.split("@")
    return parts[0], parts[1] if len(parts) > 1 else ""


def check_volta_health() -> HealthCheckResult:
    """Perform comprehensive health check of volta installation.

    Returns:
        Dictionary containing health check results
    """

    results: HealthCheckResult = {
        "volta_installed": False,
        "npm_installed": False,
        "volta_version": None,
        "npm_version": None,
        "node_version": None,
        "volta_home": None,
        "packages_count": 0,
        "issues": [],
    }

    # Check volta
    volta_path = shutil.which("volta")
    if volta_path:
        results["volta_installed"] = True
        try:
            result = subprocess.run(
                ["volta", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            results["volta_version"] = result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            results["issues"].append("Cannot determine volta version")
    else:
        results["issues"].append("volta not found in PATH")

    # Check npm
    npm_path = shutil.which("npm")
    if npm_path:
        results["npm_installed"] = True
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            results["npm_version"] = result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            results["issues"].append("Cannot determine npm version")
    else:
        results["issues"].append("npm not found in PATH")

    # Check node
    node_path = shutil.which("node")
    if node_path:
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            results["node_version"] = result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            results["issues"].append("Cannot determine node version")
    else:
        results["issues"].append("node not found in PATH")

    # Check VOLTA_HOME
    import os

    volta_home = os.environ.get("VOLTA_HOME")
    if volta_home:
        results["volta_home"] = volta_home
        if not Path(volta_home).exists():
            results["issues"].append(
                f"VOLTA_HOME directory does not exist: {volta_home}"
            )
    else:
        results["issues"].append("VOLTA_HOME environment variable not set")

    # Check installed packages count
    if results["volta_installed"]:
        try:
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                packages = get_installed_packages(Path(tmpdir))
                results["packages_count"] = len(packages)
        except Exception:
            results["issues"].append("Cannot list installed packages")

    return results


def display_health_check(results: HealthCheckResult) -> None:
    """Display health check results in formatted output.

    Args:
        results: Health check results dictionary
    """
    from rich.table import Table

    console.print("\n[bold]Volta Manager Health Check[/bold]\n")

    # Status table
    status_table = Table(show_header=False)
    status_table.add_column("Component", style="cyan")
    status_table.add_column("Status")
    status_table.add_column("Version/Value", style="dim")

    # Volta
    volta_status = (
        "[green]✓ Installed[/green]"
        if results["volta_installed"]
        else "[red]✗ Missing[/red]"
    )
    status_table.add_row("Volta", volta_status, results.get("volta_version") or "")

    # npm
    npm_status = (
        "[green]✓ Installed[/green]"
        if results["npm_installed"]
        else "[red]✗ Missing[/red]"
    )
    status_table.add_row("npm", npm_status, results.get("npm_version") or "")

    # Node
    node_status = (
        "[green]✓ Installed[/green]"
        if results["node_version"]
        else "[yellow]⚠ Not found[/yellow]"
    )
    status_table.add_row("Node.js", node_status, results.get("node_version") or "")

    # VOLTA_HOME
    volta_home_status = (
        "[green]✓ Set[/green]"
        if results["volta_home"]
        else "[yellow]⚠ Not set[/yellow]"
    )
    status_table.add_row(
        "VOLTA_HOME", volta_home_status, results.get("volta_home") or ""
    )

    # Packages
    pkg_count = results.get("packages_count", 0)
    status_table.add_row("Managed Packages", f"[cyan]{pkg_count}[/cyan]", "")

    console.print(status_table)

    # Issues
    if results["issues"]:
        console.print("\n[yellow]⚠ Issues Detected:[/yellow]")
        for issue in results["issues"]:
            console.print(f"  • {issue}")
    else:
        console.print(
            "\n[green]✓ All checks passed - your volta setup looks healthy![/green]"
        )

    # Recommendations
    if not results["volta_installed"]:
        console.print("\n[yellow]Recommendation:[/yellow]")
        console.print("  Install volta: [cyan]curl https://get.volta.sh | bash[/cyan]")
    elif not results["npm_installed"]:
        console.print("\n[yellow]Recommendation:[/yellow]")
        console.print("  Install Node.js: [cyan]volta install node[/cyan]")
