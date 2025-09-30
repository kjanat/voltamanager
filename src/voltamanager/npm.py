"""NPM registry interactions."""

import subprocess
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console

console = Console()


def get_latest_version(package_name: str, safe_dir: Path) -> str | None:
    """Query npm registry for the latest version of a package."""
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


def get_latest_versions_batch(
    package_names: list[str], safe_dir: Path
) -> dict[str, str | None]:
    """Query npm registry for multiple packages in a single call (experimental).

    Falls back to individual queries if batch query fails.
    """
    if not package_names:
        return {}

    try:
        # Try batch query with npm view --json
        result = subprocess.run(
            ["npm", "view", "--json"] + package_names + ["version"],
            cwd=safe_dir,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        # Parse JSON response
        data = json.loads(result.stdout)

        # Handle single package response (not a list)
        if isinstance(data, dict):
            # Single package queried
            if len(package_names) == 1:
                version = data.get("version")
                return {package_names[0]: version if isinstance(version, str) else None}
            return {}

        # Multiple packages: npm returns list or dict
        versions: dict[str, str | None] = {}
        if isinstance(data, list):
            for i, pkg_name in enumerate(package_names):
                if i < len(data) and isinstance(data[i], dict):
                    versions[pkg_name] = data[i].get("version")
                else:
                    versions[pkg_name] = None

        return versions

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
        KeyError,
    ):
        # Batch query failed, fall back to individual queries
        return {}


def get_latest_versions_parallel(
    packages: list[tuple[str, str]], safe_dir: Path, max_workers: int = 10
) -> dict[str, str | None]:
    """Query npm registry for latest versions in parallel with progress indicator.

    Uses batch queries for small package counts (<5), parallel queries otherwise.
    """
    latest_versions: dict[str, str | None] = {}
    package_names = [name for name, ver in packages if ver != "project"]

    if not package_names:
        return latest_versions

    # For small package counts, try batch query first
    if len(package_names) <= 4:
        batch_results = get_latest_versions_batch(package_names, safe_dir)
        if batch_results:
            return batch_results
        # Fall through to parallel queries if batch fails

    # Parallel queries for larger lists or if batch failed
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Checking {len(package_names)} packages...", total=len(package_names)
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_package = {
                executor.submit(get_latest_version, name, safe_dir): name
                for name in package_names
            }

            for future in as_completed(future_to_package):
                package_name = future_to_package[future]
                try:
                    latest_versions[package_name] = future.result()
                except Exception:
                    latest_versions[package_name] = None
                progress.advance(task)

    return latest_versions
