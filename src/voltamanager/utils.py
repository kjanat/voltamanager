"""Utility functions for version comparison and configuration checks."""

import json
from pathlib import Path
from packaging import version as pkg_version

from rich.console import Console

console = Console()


def is_major_update(current: str, latest: str) -> bool:
    """Check if the version update is a major version bump.

    Args:
        current: Current installed version
        latest: Latest available version

    Returns:
        True if latest has a higher major version than current
    """
    try:
        current_ver = pkg_version.parse(current)
        latest_ver = pkg_version.parse(latest)

        # Access major version - packaging.version.Version has release tuple
        # release[0] is major, release[1] is minor, release[2] is patch
        if hasattr(current_ver, "release") and hasattr(latest_ver, "release"):
            return bool(latest_ver.release[0] > current_ver.release[0])

        return False
    except (pkg_version.InvalidVersion, AttributeError, IndexError):
        return False


def get_major_updates(
    names: list[str], installed: list[str], latest: list[str], states: list[str]
) -> list[tuple[str, str, str]]:
    """Identify packages with major version updates.

    Args:
        names: Package names
        installed: Installed versions
        latest: Latest versions
        states: Package states

    Returns:
        List of (name, current_version, latest_version) tuples for major updates
    """
    major_updates = []

    for i, state in enumerate(states):
        if state == "OUTDATED":
            current = installed[i]
            lat = latest[i]
            if lat != "?" and is_major_update(current, lat):
                major_updates.append((names[i], current, lat))

    return major_updates


def check_local_volta_config(verbose: bool = False) -> bool:
    """Check if local package.json has volta configuration.

    Warns user if local volta config is detected, as it may affect
    global package management.

    Args:
        verbose: If True, print additional details

    Returns:
        True if local volta config detected, False otherwise
    """
    package_json = Path("package.json")

    if not package_json.exists():
        return False

    try:
        with open(package_json) as f:
            data = json.load(f)

        if "volta" in data:
            console.print(
                "[yellow]⚠ Local volta config detected in package.json[/yellow]"
            )
            console.print(
                "[yellow]  This may affect global package management[/yellow]"
            )

            if verbose:
                volta_config = data["volta"]
                if "node" in volta_config:
                    console.print(f"[dim]  Node: {volta_config['node']}[/dim]")
                if "npm" in volta_config:
                    console.print(f"[dim]  npm: {volta_config['npm']}[/dim]")
                if "yarn" in volta_config:
                    console.print(f"[dim]  Yarn: {volta_config['yarn']}[/dim]")

            return True

    except (json.JSONDecodeError, KeyError):
        pass

    return False
