"""Tests for cache module."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest


from voltamanager.cache import (
    get_cached_version,
    cache_version,
    clear_cache,
)

# Define CACHE_TTL for tests (default 1 hour)
CACHE_TTL = timedelta(hours=1)


@pytest.fixture
def mock_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mock CACHE_DIR to use tmp_path."""
    cache_dir = tmp_path / "voltamanager_cache"
    monkeypatch.setattr("voltamanager.cache.CACHE_DIR", cache_dir)
    return cache_dir


class TestGetCachedVersion:
    """Test get_cached_version function."""

    def test_no_cache_file(self, mock_cache_dir: Path) -> None:
        """Test when no cache file exists."""
        version = get_cached_version("lodash")
        assert version is None

    def test_valid_cache_fresh(self, mock_cache_dir: Path) -> None:
        """Test with valid, fresh cache."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "lodash.json"
        cache_data = {"version": "5.0.0", "timestamp": datetime.now().isoformat()}
        cache_file.write_text(json.dumps(cache_data))

        version = get_cached_version("lodash")
        assert version == "5.0.0"

    def test_valid_cache_expired(self, mock_cache_dir: Path) -> None:
        """Test with expired cache."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "lodash.json"
        expired_time = datetime.now() - CACHE_TTL - timedelta(minutes=1)
        cache_data = {"version": "5.0.0", "timestamp": expired_time.isoformat()}
        cache_file.write_text(json.dumps(cache_data))

        version = get_cached_version("lodash")
        assert version is None

    def test_scoped_package(self, mock_cache_dir: Path) -> None:
        """Test caching scoped package (slashes replaced with underscores)."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "@vue_cli.json"  # Slash replaced
        cache_data = {"version": "5.0.8", "timestamp": datetime.now().isoformat()}
        cache_file.write_text(json.dumps(cache_data))

        version = get_cached_version("@vue/cli")
        assert version == "5.0.8"

    def test_invalid_json(self, mock_cache_dir: Path) -> None:
        """Test handling invalid JSON in cache file."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "lodash.json"
        cache_file.write_text("not valid json")

        version = get_cached_version("lodash")
        assert version is None

    def test_missing_version_key(self, mock_cache_dir: Path) -> None:
        """Test handling cache without version key."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "lodash.json"
        cache_data = {
            "timestamp": datetime.now().isoformat()
            # Missing "version"
        }
        cache_file.write_text(json.dumps(cache_data))

        version = get_cached_version("lodash")
        assert version is None

    def test_missing_timestamp_key(self, mock_cache_dir: Path) -> None:
        """Test handling cache without timestamp key."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "lodash.json"
        cache_data = {
            "version": "5.0.0"
            # Missing "timestamp"
        }
        cache_file.write_text(json.dumps(cache_data))

        version = get_cached_version("lodash")
        assert version is None

    def test_invalid_timestamp_format(self, mock_cache_dir: Path) -> None:
        """Test handling invalid timestamp format."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "lodash.json"
        cache_data = {"version": "5.0.0", "timestamp": "not a timestamp"}
        cache_file.write_text(json.dumps(cache_data))

        version = get_cached_version("lodash")
        assert version is None

    def test_version_not_string(self, mock_cache_dir: Path) -> None:
        """Test handling non-string version value."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "lodash.json"
        cache_data = {
            "version": 5.0,  # Number instead of string
            "timestamp": datetime.now().isoformat(),
        }
        cache_file.write_text(json.dumps(cache_data))

        version = get_cached_version("lodash")
        assert version is None


class TestCacheVersion:
    """Test cache_version function."""

    def test_cache_regular_package(self, mock_cache_dir: Path) -> None:
        """Test caching a regular package version."""
        cache_version("lodash", "5.0.0")

        cache_file = mock_cache_dir / "lodash.json"
        assert cache_file.exists()

        data = json.loads(cache_file.read_text())
        assert data["version"] == "5.0.0"
        assert "timestamp" in data

        # Verify timestamp is recent (within last minute)
        cached_time = datetime.fromisoformat(data["timestamp"])
        assert datetime.now() - cached_time < timedelta(minutes=1)

    def test_cache_scoped_package(self, mock_cache_dir: Path) -> None:
        """Test caching a scoped package (slashes replaced)."""
        cache_version("@vue/cli", "5.0.8")

        cache_file = mock_cache_dir / "@vue_cli.json"
        assert cache_file.exists()

        data = json.loads(cache_file.read_text())
        assert data["version"] == "5.0.8"

    def test_cache_creates_directory(self, mock_cache_dir: Path) -> None:
        """Test that caching creates cache directory if missing."""
        assert not mock_cache_dir.exists()

        cache_version("lodash", "5.0.0")

        assert mock_cache_dir.exists()
        assert (mock_cache_dir / "lodash.json").exists()

    def test_cache_overwrites_existing(self, mock_cache_dir: Path) -> None:
        """Test that caching overwrites existing cache file."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "lodash.json"

        # Write old cache
        old_data = {
            "version": "4.17.21",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        }
        cache_file.write_text(json.dumps(old_data))

        # Cache new version
        cache_version("lodash", "5.0.0")

        # Verify overwrite
        data = json.loads(cache_file.read_text())
        assert data["version"] == "5.0.0"

        cached_time = datetime.fromisoformat(data["timestamp"])
        assert datetime.now() - cached_time < timedelta(minutes=1)

    def test_cache_complex_package_name(self, mock_cache_dir: Path) -> None:
        """Test caching package with complex scope."""
        cache_version("@typescript-eslint/parser", "6.0.0")

        cache_file = mock_cache_dir / "@typescript-eslint_parser.json"
        assert cache_file.exists()

        data = json.loads(cache_file.read_text())
        assert data["version"] == "6.0.0"


class TestClearCache:
    """Test clear_cache function."""

    def test_clear_empty_cache(self, mock_cache_dir: Path) -> None:
        """Test clearing when cache directory doesn't exist."""
        assert not mock_cache_dir.exists()
        clear_cache()  # Should not raise error
        assert not mock_cache_dir.exists()

    def test_clear_single_file(self, mock_cache_dir: Path) -> None:
        """Test clearing cache with single file."""
        cache_version("lodash", "5.0.0")
        assert (mock_cache_dir / "lodash.json").exists()

        clear_cache()
        assert not (mock_cache_dir / "lodash.json").exists()

    def test_clear_multiple_files(self, mock_cache_dir: Path) -> None:
        """Test clearing cache with multiple files."""
        cache_version("lodash", "5.0.0")
        cache_version("eslint", "8.0.0")
        cache_version("@vue/cli", "5.0.8")

        assert len(list(mock_cache_dir.glob("*.json"))) == 3

        clear_cache()

        assert len(list(mock_cache_dir.glob("*.json"))) == 0

    def test_clear_ignores_non_json(self, mock_cache_dir: Path) -> None:
        """Test that clear_cache only removes .json files."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)

        # Create mix of files
        cache_version("lodash", "5.0.0")
        (mock_cache_dir / "README.txt").write_text("info")
        (mock_cache_dir / "config.ini").write_text("settings")

        clear_cache()

        assert not (mock_cache_dir / "lodash.json").exists()
        assert (mock_cache_dir / "README.txt").exists()
        assert (mock_cache_dir / "config.ini").exists()


class TestCacheIntegration:
    """Integration tests for cache functions."""

    def test_cache_and_retrieve_workflow(self, mock_cache_dir: Path) -> None:
        """Test typical cache workflow: cache → retrieve → clear."""
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

    def test_cache_expiration_boundary(self, mock_cache_dir: Path) -> None:
        """Test cache expiration at exact TTL boundary."""
        mock_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = mock_cache_dir / "lodash.json"

        # Create cache exactly at TTL boundary
        boundary_time = datetime.now() - CACHE_TTL
        cache_data = {"version": "5.0.0", "timestamp": boundary_time.isoformat()}
        cache_file.write_text(json.dumps(cache_data))

        # Should be expired (>= TTL is expired)
        version = get_cached_version("lodash")
        assert version is None
