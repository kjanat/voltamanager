"""NPM registry response caching - single file for all packages."""

import json
import time
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "voltamanager"
CACHE_FILE = CACHE_DIR / "versions.json"

# Type alias for cache structure
CacheData = dict[str, dict[str, str | float]]

# Module state dict to avoid global statements
_state: dict[str, CacheData | float | None] = {"cache": None, "mtime": 0.0}


def _load_cache() -> CacheData:
    """Load cache from disk, using in-memory cache if file unchanged."""
    if not CACHE_FILE.exists():
        empty: CacheData = {}
        _state["cache"] = empty
        _state["mtime"] = 0.0
        return empty

    try:
        mtime = CACHE_FILE.stat().st_mtime
        cached = _state["cache"]
        if cached is not None and mtime == _state["mtime"]:
            return cached  # type: ignore[return-value]

        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        result: CacheData = data if isinstance(data, dict) else {}
        _state["cache"] = result
        _state["mtime"] = mtime
        return result
    except (json.JSONDecodeError, OSError):
        empty_fallback: CacheData = {}
        _state["cache"] = empty_fallback
        _state["mtime"] = 0.0
        return empty_fallback


def _save_cache(cache: dict[str, dict]) -> None:
    """Save cache to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
    _state["cache"] = cache
    _state["mtime"] = CACHE_FILE.stat().st_mtime


def get_cached_version(package_name: str, ttl_hours: float = 1) -> str | None:
    """Get cached version if available and not expired.

    Args:
        package_name: Name of the package
        ttl_hours: Time-to-live in hours (default: 1)

    Returns:
        Cached version string if valid, None otherwise

    """
    cache = _load_cache()
    entry = cache.get(package_name)

    if entry is None:
        return None

    # Check expiry using Unix timestamp (fast, no parsing)
    ts_value = entry.get("ts", 0)
    timestamp = float(ts_value) if isinstance(ts_value, (int, float)) else 0.0
    ttl_seconds = ttl_hours * 3600
    if time.time() - timestamp > ttl_seconds:
        return None

    version = entry.get("v")
    return version if isinstance(version, str) else None


def cache_version(package_name: str, version: str) -> None:
    """Cache a package version."""
    cache = _load_cache()
    cache[package_name] = {"v": version, "ts": time.time()}
    _save_cache(cache)


def clear_cache() -> None:
    """Clear all cached versions."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    _state["cache"] = None
    _state["mtime"] = 0.0
