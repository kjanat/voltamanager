"""Tests for cache module (single-file cache)."""

import json
import time
from pathlib import Path

import pytest

import voltamanager.cache
from voltamanager.cache import (
    cache_version,
    clear_cache,
    get_cached_version,
)


@pytest.fixture
def mock_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mock CACHE_DIR and CACHE_FILE to use tmp_path."""
    cache_dir = tmp_path / "voltamanager_cache"
    cache_file = cache_dir / "versions.json"
    monkeypatch.setattr("voltamanager.cache.CACHE_DIR", cache_dir)
    monkeypatch.setattr("voltamanager.cache.CACHE_FILE", cache_file)
    # Reset in-memory cache state
    voltamanager.cache._state["cache"] = None
    voltamanager.cache._state["mtime"] = 0.0
    return cache_dir


@pytest.fixture
def cache_file(mock_cache_dir: Path) -> Path:
    """Get the cache file path."""
    return mock_cache_dir / "versions.json"


class TestGetCachedVersion:
    """Test get_cached_version function."""

    def test_no_cache_file(self, mock_cache_dir: Path) -> None:
        """Test when no cache file exists."""
        version = get_cached_version("lodash")
        assert version is None

    def test_valid_cache_fresh(self, mock_cache_dir: Path, cache_file: Path) -> None:
        """Test with valid, fresh cache."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_data = {"lodash": {"v": "5.0.0", "ts": time.time()}}
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        version = get_cached_version("lodash")
        assert version == "5.0.0"

    def test_valid_cache_expired(self, mock_cache_dir: Path, cache_file: Path) -> None:
        """Test with expired cache (>1 hour old)."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        expired_ts = time.time() - 3700  # 1 hour + 100 seconds ago
        cache_data = {"lodash": {"v": "5.0.0", "ts": expired_ts}}
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        version = get_cached_version("lodash")
        assert version is None

    def test_scoped_package(self, mock_cache_dir: Path, cache_file: Path) -> None:
        """Test caching scoped package."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_data = {"@vue/cli": {"v": "5.0.8", "ts": time.time()}}
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        version = get_cached_version("@vue/cli")
        assert version == "5.0.8"

    def test_invalid_json(self, mock_cache_dir: Path, cache_file: Path) -> None:
        """Test handling invalid JSON in cache file."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("not valid json", encoding="utf-8")

        version = get_cached_version("lodash")
        assert version is None

    def test_missing_version_key(self, mock_cache_dir: Path, cache_file: Path) -> None:
        """Test handling cache entry without version key."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_data = {"lodash": {"ts": time.time()}}  # Missing "v"
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        version = get_cached_version("lodash")
        assert version is None

    def test_missing_timestamp_key(
        self, mock_cache_dir: Path, cache_file: Path
    ) -> None:
        """Test handling cache entry without timestamp key."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_data = {"lodash": {"v": "5.0.0"}}  # Missing "ts"
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        version = get_cached_version("lodash")
        assert version is None

    def test_version_not_string(self, mock_cache_dir: Path, cache_file: Path) -> None:
        """Test handling non-string version value."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_data = {"lodash": {"v": 5.0, "ts": time.time()}}  # Number, not string
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        version = get_cached_version("lodash")
        assert version is None

    def test_custom_ttl(self, mock_cache_dir: Path, cache_file: Path) -> None:
        """Test custom TTL parameter."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        # 30 minutes ago
        old_ts = time.time() - 1800
        cache_data = {"lodash": {"v": "5.0.0", "ts": old_ts}}
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        # Default 1 hour TTL - should be valid
        version = get_cached_version("lodash", ttl_hours=1)
        assert version == "5.0.0"

        # 15 minute TTL - should be expired
        version = get_cached_version("lodash", ttl_hours=0.25)
        assert version is None


class TestCacheVersion:
    """Test cache_version function."""

    def test_cache_regular_package(
        self, mock_cache_dir: Path, cache_file: Path
    ) -> None:
        """Test caching a regular package version."""
        cache_version("lodash", "5.0.0")

        assert cache_file.exists()

        data = json.loads(cache_file.read_text(encoding="utf-8"))
        assert data["lodash"]["v"] == "5.0.0"
        assert "ts" in data["lodash"]
        assert time.time() - data["lodash"]["ts"] < 60  # Within last minute

    def test_cache_scoped_package(self, mock_cache_dir: Path, cache_file: Path) -> None:
        """Test caching a scoped package."""
        cache_version("@vue/cli", "5.0.8")

        data = json.loads(cache_file.read_text(encoding="utf-8"))
        assert data["@vue/cli"]["v"] == "5.0.8"

    def test_cache_creates_directory(
        self, mock_cache_dir: Path, cache_file: Path
    ) -> None:
        """Test that caching creates cache directory if missing."""
        assert not mock_cache_dir.exists()

        cache_version("lodash", "5.0.0")

        assert mock_cache_dir.exists()
        assert cache_file.exists()

    def test_cache_multiple_packages(
        self, mock_cache_dir: Path, cache_file: Path
    ) -> None:
        """Test caching multiple packages in single file."""
        cache_version("lodash", "5.0.0")
        cache_version("eslint", "8.0.0")
        cache_version("@vue/cli", "5.0.8")

        data = json.loads(cache_file.read_text(encoding="utf-8"))
        assert len(data) == 3
        assert data["lodash"]["v"] == "5.0.0"
        assert data["eslint"]["v"] == "8.0.0"
        assert data["@vue/cli"]["v"] == "5.0.8"

    def test_cache_overwrites_existing(
        self, mock_cache_dir: Path, cache_file: Path
    ) -> None:
        """Test that caching overwrites existing entry."""
        cache_version("lodash", "4.17.21")
        cache_version("lodash", "5.0.0")

        data = json.loads(cache_file.read_text(encoding="utf-8"))
        assert data["lodash"]["v"] == "5.0.0"


class TestClearCache:
    """Test clear_cache function."""

    def test_clear_empty_cache(self, mock_cache_dir: Path) -> None:
        """Test clearing when cache file doesn't exist."""
        assert not mock_cache_dir.exists()
        clear_cache()  # Should not raise error

    def test_clear_cache(self, mock_cache_dir: Path, cache_file: Path) -> None:
        """Test clearing cache file."""
        cache_version("lodash", "5.0.0")
        cache_version("eslint", "8.0.0")
        assert cache_file.exists()

        clear_cache()
        assert not cache_file.exists()

    def test_clear_preserves_directory(
        self, mock_cache_dir: Path, cache_file: Path
    ) -> None:
        """Test that clear only removes cache file, not directory."""
        cache_version("lodash", "5.0.0")
        (mock_cache_dir / "other.txt").write_text("keep", encoding="utf-8")

        clear_cache()

        assert not cache_file.exists()
        assert (mock_cache_dir / "other.txt").exists()


class TestCacheIntegration:
    """Integration tests for cache functions."""

    def test_cache_and_retrieve_workflow(
        self, mock_cache_dir: Path, cache_file: Path
    ) -> None:
        """Test typical cache workflow: cache -> retrieve -> clear."""
        # Cache version
        cache_version("lodash", "5.0.0")

        # Retrieve from cache
        version = get_cached_version("lodash")
        assert version == "5.0.0"

        # Clear cache
        clear_cache()

        # Verify cache cleared
        version = get_cached_version("lodash")
        assert version is None

    def test_in_memory_cache_reuse(
        self, mock_cache_dir: Path, cache_file: Path
    ) -> None:
        """Test that in-memory cache avoids repeated file reads."""
        cache_version("lodash", "5.0.0")

        # First read loads from disk
        version1 = get_cached_version("lodash")
        assert version1 == "5.0.0"

        # Second read uses in-memory cache (same result)
        version2 = get_cached_version("lodash")
        assert version2 == "5.0.0"
