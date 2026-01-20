"""Tests for configurable cache TTL functionality."""

import json
import tempfile
import time
from pathlib import Path

import pytest

import voltamanager.cache
from voltamanager.cache import cache_version, get_cached_version


@pytest.fixture
def temp_cache_dir(monkeypatch):
    """Create temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cache"
        cache_file = cache_dir / "versions.json"
        monkeypatch.setattr("voltamanager.cache.CACHE_DIR", cache_dir)
        monkeypatch.setattr("voltamanager.cache.CACHE_FILE", cache_file)
        # Reset in-memory cache state
        voltamanager.cache._state["cache"] = None
        voltamanager.cache._state["mtime"] = 0.0
        yield cache_dir, cache_file


def _reset_cache_state() -> None:
    """Reset in-memory cache to force re-read from disk."""
    voltamanager.cache._state["cache"] = None
    voltamanager.cache._state["mtime"] = 0.0


def test_cache_with_custom_ttl(temp_cache_dir) -> None:
    """Test cache respects custom TTL."""
    _cache_dir, cache_file = temp_cache_dir
    package = "test-package"
    version = "1.0.0"

    # Cache the version
    cache_version(package, version)

    # Should be valid with 1 hour TTL
    assert get_cached_version(package, ttl_hours=1) == version

    # Modify cache to be 2 hours old
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    data[package]["ts"] = time.time() - 7200  # 2 hours ago
    cache_file.write_text(json.dumps(data), encoding="utf-8")

    # Reset in-memory cache to force re-read
    _reset_cache_state()

    # Should be expired with 1 hour TTL
    assert get_cached_version(package, ttl_hours=1) is None

    # Should be valid with 3 hour TTL
    assert get_cached_version(package, ttl_hours=3) == version


def test_cache_with_longer_ttl(temp_cache_dir) -> None:
    """Test cache with longer TTL (24 hours)."""
    _cache_dir, cache_file = temp_cache_dir
    package = "long-lived-package"
    version = "2.0.0"

    # Cache the version
    cache_version(package, version)

    # Modify to be 12 hours old
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    data[package]["ts"] = time.time() - 43200  # 12 hours ago
    cache_file.write_text(json.dumps(data), encoding="utf-8")

    # Reset in-memory cache
    _reset_cache_state()

    # Should be expired with 1 hour TTL
    assert get_cached_version(package, ttl_hours=1) is None

    # Should be valid with 24 hour TTL
    assert get_cached_version(package, ttl_hours=24) == version


def test_cache_default_ttl(temp_cache_dir) -> None:
    """Test cache uses default 1 hour TTL when not specified."""
    _cache_dir, cache_file = temp_cache_dir
    package = "default-ttl-package"
    version = "3.0.0"

    # Cache the version
    cache_version(package, version)

    # Should be valid with default TTL
    assert get_cached_version(package) == version

    # Make it 2 hours old
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    data[package]["ts"] = time.time() - 7200  # 2 hours ago
    cache_file.write_text(json.dumps(data), encoding="utf-8")

    # Reset in-memory cache
    _reset_cache_state()

    # Should be expired with default 1 hour TTL
    assert get_cached_version(package) is None


def test_cache_scoped_package_with_ttl(temp_cache_dir) -> None:
    """Test cache handles scoped packages with custom TTL."""
    _cache_dir, cache_file = temp_cache_dir
    package = "@vue/cli"
    version = "5.0.8"

    # Cache the version
    cache_version(package, version)

    # Should be valid
    assert get_cached_version(package, ttl_hours=2) == version

    # Check data in cache file
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    assert package in data
    assert data[package]["v"] == version
