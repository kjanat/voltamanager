"""NPM registry interactions."""

import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

console = Console()

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAYS = (0.5, 1.0)  # Exponential backoff delays in seconds
HTTP_TIMEOUT = 10

# npm registry base URL
NPM_REGISTRY = "https://registry.npmjs.org"


def get_latest_version(package_name: str) -> str | None:
    """Query npm registry for the latest version of a package via HTTP.

    Direct HTTP is ~10-50x faster than spawning npm subprocess.
    Retries up to MAX_RETRIES times on timeout/network errors with
    exponential backoff.
    """
    # URL encode scoped packages: @scope/pkg -> @scope%2Fpkg
    encoded_name = package_name.replace("/", "%2F")
    url = f"{NPM_REGISTRY}/{encoded_name}/latest"

    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "voltamanager"},
            )
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                version = data.get("version")
                return version if isinstance(version, str) else None
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAYS[attempt])
        except TimeoutError:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAYS[attempt])

    # All retries exhausted
    return None


def get_latest_versions_batch(package_names: list[str]) -> dict[str, str | None]:
    """Query npm registry for multiple packages using bulk endpoint.

    Uses npm registry's bulk endpoint for efficiency.
    Falls back to empty dict if batch query fails.
    """
    if not package_names:
        return {}

    # npm registry bulk endpoint
    url = f"{NPM_REGISTRY}/-/package-metadata"

    try:
        # POST with package names
        payload = json.dumps({"packages": package_names}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "voltamanager",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # Parse response
        versions: dict[str, str | None] = {}
        for pkg_name in package_names:
            pkg_data = data.get(pkg_name, {})
            if isinstance(pkg_data, dict):
                versions[pkg_name] = pkg_data.get("version")
            else:
                versions[pkg_name] = None

        return versions

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        json.JSONDecodeError,
        TimeoutError,
    ):
        # Batch query failed, caller should fall back to individual queries
        return {}


def get_latest_versions_parallel(
    packages: list[tuple[str, str]], max_workers: int = 10
) -> dict[str, str | None]:
    """Query npm registry for latest versions in parallel with progress indicator.

    Uses direct HTTP requests (~10-50x faster than npm subprocess).
    """
    latest_versions: dict[str, str | None] = {}
    package_names = [name for name, ver in packages if ver != "project"]

    if not package_names:
        return latest_versions

    # For small package counts, try batch query first
    if len(package_names) <= 10:
        batch_results = get_latest_versions_batch(package_names)
        if batch_results:
            return batch_results
        # Fall through to parallel queries if batch fails

    # Parallel HTTP queries for larger lists or if batch failed
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
                executor.submit(get_latest_version, name): name
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
