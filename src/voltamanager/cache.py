"""NPM registry response caching."""

import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path.home() / ".cache" / "voltamanager"
CACHE_TTL = timedelta(hours=1)


def get_cached_version(package_name: str) -> str | None:
    """Get cached version if available and not expired."""
    cache_file = CACHE_DIR / f"{package_name.replace('/', '_')}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            cached_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - cached_time < CACHE_TTL:
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
        json.dumps({"version": version, "timestamp": datetime.now().isoformat()})
    )


def clear_cache() -> None:
    """Clear all cached versions."""
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("*.json"):
            cache_file.unlink()
