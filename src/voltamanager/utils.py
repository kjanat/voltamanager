"""Utility functions for version comparison and configuration checks."""

import json
import shutil
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


def get_changelog_url(package_name: str) -> str:
    """Get the changelog URL for a package.

    Args:
        package_name: Name of the npm package

    Returns:
        URL to the package's changelog or npm page
    """
    # Most packages have changelogs at these common locations
    return f"https://www.npmjs.com/package/{package_name}?activeTab=versions"


def get_minor_updates(
    names: list[str], installed: list[str], latest: list[str], states: list[str]
) -> list[tuple[str, str, str]]:
    """Identify packages with minor version updates.

    Args:
        names: Package names
        installed: Installed versions
        latest: Latest versions
        states: Package states

    Returns:
        List of (name, current_version, latest_version) tuples for minor updates
    """
    minor_updates = []

    for i, state in enumerate(states):
        if state == "OUTDATED":
            current = installed[i]
            lat = latest[i]
            if lat != "?" and not is_major_update(current, lat):
                try:
                    current_ver = pkg_version.parse(current)
                    latest_ver = pkg_version.parse(lat)

                    if (
                        hasattr(current_ver, "release")
                        and hasattr(latest_ver, "release")
                        and len(current_ver.release) >= 2
                        and len(latest_ver.release) >= 2
                    ):
                        # Minor update: major same, minor different
                        if (
                            current_ver.release[0] == latest_ver.release[0]
                            and current_ver.release[1] < latest_ver.release[1]
                        ):
                            minor_updates.append((names[i], current, lat))
                except (pkg_version.InvalidVersion, AttributeError, IndexError):
                    pass

    return minor_updates


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


def check_disk_space(min_mb: int = 500) -> tuple[bool, int]:
    """Check if sufficient disk space is available.

    Args:
        min_mb: Minimum required space in MB (default: 500)

    Returns:
        Tuple of (sufficient_space, available_mb)
    """
    try:
        stat = shutil.disk_usage(Path.home())
        available_mb = stat.free // (1024 * 1024)
        return available_mb >= min_mb, available_mb
    except OSError:
        # If we can't check, assume it's okay
        return True, -1


def estimate_update_size(package_count: int) -> int:
    """Estimate disk space needed for updates in MB.

    Args:
        package_count: Number of packages to update

    Returns:
        Estimated size in MB (conservative estimate)
    """
    # Conservative estimate: 50MB per package on average
    # Some packages like typescript, webpack are larger
    return package_count * 50
