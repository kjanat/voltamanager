"""Tests for configurable cache TTL functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from voltamanager.cache import cache_version, get_cached_version


@pytest.fixture
def temp_cache_dir(monkeypatch):
    """Create temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("voltamanager.cache.CACHE_DIR", cache_dir)
        yield cache_dir


def test_cache_with_custom_ttl(temp_cache_dir):
    """Test cache respects custom TTL."""
    package = "test-package"
    version = "1.0.0"

    # Cache the version
    cache_version(package, version)

    # Should be valid with 1 hour TTL
    assert get_cached_version(package, ttl_hours=1) == version

    # Modify cache to be 2 hours old
    cache_file = temp_cache_dir / f"{package}.json"
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    old_time = datetime.now() - timedelta(hours=2)
    data["timestamp"] = old_time.isoformat()
    cache_file.write_text(json.dumps(data), encoding="utf-8")

    # Should be expired with 1 hour TTL
    assert get_cached_version(package, ttl_hours=1) is None

    # Should be valid with 3 hour TTL
    assert get_cached_version(package, ttl_hours=3) == version


def test_cache_with_longer_ttl(temp_cache_dir):
    """Test cache with longer TTL (24 hours)."""
    package = "long-lived-package"
    version = "2.0.0"

    # Cache the version
    cache_version(package, version)

    # Modify to be 12 hours old
    cache_file = temp_cache_dir / f"{package}.json"
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    old_time = datetime.now() - timedelta(hours=12)
    data["timestamp"] = old_time.isoformat()
    cache_file.write_text(json.dumps(data), encoding="utf-8")

    # Should be expired with 1 hour TTL
    assert get_cached_version(package, ttl_hours=1) is None

    # Should be valid with 24 hour TTL
    assert get_cached_version(package, ttl_hours=24) == version


def test_cache_default_ttl(temp_cache_dir):
    """Test cache uses default 1 hour TTL when not specified."""
    package = "default-ttl-package"
    version = "3.0.0"

    # Cache the version
    cache_version(package, version)

    # Should be valid with default TTL
    assert get_cached_version(package) == version

    # Make it 2 hours old
    cache_file = temp_cache_dir / f"{package}.json"
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    old_time = datetime.now() - timedelta(hours=2)
    data["timestamp"] = old_time.isoformat()
    cache_file.write_text(json.dumps(data), encoding="utf-8")

    # Should be expired with default 1 hour TTL
    assert get_cached_version(package) is None


def test_cache_scoped_package_with_ttl(temp_cache_dir):
    """Test cache handles scoped packages with custom TTL."""
    package = "@vue/cli"
    version = "5.0.8"

    # Cache the version
    cache_version(package, version)

    # Should be valid
    assert get_cached_version(package, ttl_hours=2) == version

    # Check file was created with correct name (/ replaced with _)
    cache_file = temp_cache_dir / "@vue_cli.json"
    assert cache_file.exists()
