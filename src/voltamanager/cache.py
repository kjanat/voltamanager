"""NPM registry response caching."""

import json
from datetime import datetime, timedelta
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "voltamanager"


def get_cached_version(package_name: str, ttl_hours: int = 1) -> str | None:
    """Get cached version if available and not expired.

    Args:
        package_name: Name of the package
        ttl_hours: Time-to-live in hours (default: 1)

    Returns:
        Cached version string if valid, None otherwise

    """
    cache_ttl = timedelta(hours=ttl_hours)
    cache_file = CACHE_DIR / f"{package_name.replace('/', '_')}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - cached_time < cache_ttl:
                version = data.get("version")
                if isinstance(version, str):
                    return version
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache file, ignore
            pass
    return None


def cache_version(package_name: str, version: str) -> None:
    """Cache a package version."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{package_name.replace('/', '_')}.json"
    cache_file.write_text(
        json.dumps({"version": version, "timestamp": datetime.now().isoformat()}),
        encoding="utf-8",
    )


def clear_cache() -> None:
    """Clear all cached versions."""
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("*.json"):
            cache_file.unlink()
