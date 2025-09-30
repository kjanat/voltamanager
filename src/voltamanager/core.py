"""Core logic for package management."""

import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

from rich.console import Console

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
