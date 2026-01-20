"""Tests for npm module."""

import urllib.error
from unittest.mock import MagicMock, patch

from voltamanager.npm import (
    get_latest_version,
    get_latest_versions_batch,
    get_latest_versions_parallel,
)


class TestGetLatestVersion:
    """Test get_latest_version function (HTTP-based)."""

    def test_get_version_success(self) -> None:
        """Test successful version retrieval via HTTP."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"version": "5.0.0"}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            version = get_latest_version("lodash")

            assert version == "5.0.0"

    def test_get_version_scoped_package(self) -> None:
        """Test version retrieval for scoped package (URL encoding)."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"version": "5.0.8"}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "urllib.request.urlopen", return_value=mock_response
        ) as mock_urlopen:
            version = get_latest_version("@vue/cli")

            assert version == "5.0.8"
            # Check URL encoding of scoped package
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            assert "@vue%2Fcli" in request.full_url

    def test_get_version_timeout(self) -> None:
        """Test handling timeout error after all retries exhausted."""
        with (
            patch("urllib.request.urlopen") as mock_urlopen,
            patch("time.sleep") as mock_sleep,
        ):
            mock_urlopen.side_effect = TimeoutError("Connection timed out")
            version = get_latest_version("lodash")

            assert version is None
            # Should retry 2 times (3 total attempts)
            assert mock_urlopen.call_count == 3
            # Should sleep with exponential backoff (0.5s, 1.0s)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(0.5)
            mock_sleep.assert_any_call(1.0)

    def test_get_version_not_found(self) -> None:
        """Test handling HTTP 404 error after all retries exhausted."""
        with (
            patch("urllib.request.urlopen") as mock_urlopen,
            patch("time.sleep") as mock_sleep,
        ):
            mock_urlopen.side_effect = urllib.error.HTTPError(
                "url", 404, "Not Found", {}, None
            )
            version = get_latest_version("nonexistent-package")

            assert version is None
            # Should retry 2 times (3 total attempts)
            assert mock_urlopen.call_count == 3
            assert mock_sleep.call_count == 2

    def test_get_version_retry_success_second_attempt(self) -> None:
        """Test successful retry on second attempt."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"version": "5.0.0"}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("urllib.request.urlopen") as mock_urlopen,
            patch("time.sleep") as mock_sleep,
        ):
            # First call fails, second succeeds
            mock_urlopen.side_effect = [
                TimeoutError("Connection timed out"),
                mock_response,
            ]
            version = get_latest_version("lodash")

            assert version == "5.0.0"
            assert mock_urlopen.call_count == 2
            # Should only sleep once (after first failure)
            assert mock_sleep.call_count == 1
            mock_sleep.assert_called_once_with(0.5)

    def test_get_version_retry_success_third_attempt(self) -> None:
        """Test successful retry on third attempt."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"version": "5.0.0"}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("urllib.request.urlopen") as mock_urlopen,
            patch("time.sleep") as mock_sleep,
        ):
            # First two calls fail, third succeeds
            mock_urlopen.side_effect = [
                urllib.error.URLError("Network error"),
                TimeoutError("Connection timed out"),
                mock_response,
            ]
            version = get_latest_version("lodash")

            assert version == "5.0.0"
            assert mock_urlopen.call_count == 3
            assert mock_sleep.call_count == 2

    def test_get_version_invalid_json(self) -> None:
        """Test handling invalid JSON response."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("urllib.request.urlopen", return_value=mock_response),
            patch("time.sleep"),
        ):
            version = get_latest_version("lodash")
            assert version is None


class TestGetLatestVersionsBatch:
    """Test get_latest_versions_batch function (HTTP bulk endpoint)."""

    def test_batch_empty_list(self) -> None:
        """Test batch query with empty package list."""
        versions = get_latest_versions_batch([])
        assert versions == {}

    def test_batch_http_error(self) -> None:
        """Test handling HTTP error."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                "url", 500, "Server Error", {}, None
            )
            versions = get_latest_versions_batch(["lodash"])
            assert versions == {}

    def test_batch_timeout(self) -> None:
        """Test handling timeout."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = TimeoutError("Connection timed out")
            versions = get_latest_versions_batch(["lodash"])
            assert versions == {}

    def test_batch_invalid_json(self) -> None:
        """Test handling invalid JSON response."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            versions = get_latest_versions_batch(["lodash"])
            assert versions == {}


class TestGetLatestVersionsParallel:
    """Test get_latest_versions_parallel function."""

    def test_parallel_small_batch_success(self) -> None:
        """Test parallel queries with small package count (uses batch)."""
        packages = [("lodash", "4.17.21"), ("eslint", "7.0.0")]

        with patch("voltamanager.npm.get_latest_versions_batch") as mock_batch:
            mock_batch.return_value = {"lodash": "5.0.0", "eslint": "8.0.0"}

            versions = get_latest_versions_parallel(packages)

            assert versions == {"lodash": "5.0.0", "eslint": "8.0.0"}
            mock_batch.assert_called_once()

    def test_parallel_small_batch_fallback(self) -> None:
        """Test fallback to parallel when batch fails."""
        packages = [("lodash", "4.17.21"), ("eslint", "7.0.0")]

        with (
            patch("voltamanager.npm.get_latest_versions_batch") as mock_batch,
            patch("voltamanager.npm.get_latest_version") as mock_get,
        ):
            mock_batch.return_value = {}  # Batch fails
            mock_get.side_effect = ["5.0.0", "8.0.0"]

            versions = get_latest_versions_parallel(packages)

            assert versions == {"lodash": "5.0.0", "eslint": "8.0.0"}
            assert mock_get.call_count == 2

    def test_parallel_large_batch(self) -> None:
        """Test parallel queries with many packages (>10, skips batch)."""
        packages = [(f"pkg{i}", "1.0.0") for i in range(15)]

        with patch("voltamanager.npm.get_latest_version") as mock_get:
            mock_get.return_value = "2.0.0"

            versions = get_latest_versions_parallel(packages)

            assert len(versions) == 15
            assert all(v == "2.0.0" for v in versions.values())
            assert mock_get.call_count == 15

    def test_parallel_project_packages_excluded(self) -> None:
        """Test that project-pinned packages are excluded."""
        packages = [
            ("lodash", "4.17.21"),
            ("eslint", "project"),
            ("typescript", "5.0.0"),
        ]

        with patch("voltamanager.npm.get_latest_versions_batch") as mock_batch:
            mock_batch.return_value = {"lodash": "2.0.0", "typescript": "2.0.0"}

            versions = get_latest_versions_parallel(packages)

            assert "eslint" not in versions
            assert "lodash" in versions
            assert "typescript" in versions

    def test_parallel_empty_packages(self) -> None:
        """Test with empty package list."""
        versions = get_latest_versions_parallel([])
        assert versions == {}

    def test_parallel_all_project_packages(self) -> None:
        """Test with all project-pinned packages."""
        packages = [("pkg1", "project"), ("pkg2", "project")]

        versions = get_latest_versions_parallel(packages)
        assert versions == {}

    def test_parallel_exception_handling(self) -> None:
        """Test handling exceptions in parallel execution."""
        packages = [(f"pkg{i}", "1.0.0") for i in range(15)]  # >10 to skip batch

        def mock_version(name: str) -> str | None:
            if name == "pkg5":
                raise Exception("Network error")  # noqa: TRY002, TRY003
            return "2.0.0"

        with patch("voltamanager.npm.get_latest_version", side_effect=mock_version):
            versions = get_latest_versions_parallel(packages)

            assert versions["pkg0"] == "2.0.0"
            assert versions["pkg5"] is None
            assert len(versions) == 15

    def test_parallel_custom_max_workers(self) -> None:
        """Test with custom max_workers parameter."""
        packages = [(f"pkg{i}", "1.0.0") for i in range(15)]  # >10 to skip batch

        with patch("voltamanager.npm.get_latest_version") as mock_get:
            mock_get.return_value = "2.0.0"

            # Just verify it runs without error - max_workers is internal implementation
            versions = get_latest_versions_parallel(packages, max_workers=3)

            assert len(versions) == 15
            assert all(v == "2.0.0" for v in versions.values())
