"""Tests for npm module."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch


from voltamanager.npm import (
    get_latest_version,
    get_latest_versions_batch,
    get_latest_versions_parallel,
)


class TestGetLatestVersion:
    """Test get_latest_version function."""

    def test_get_version_success(self, tmp_path: Path) -> None:
        """Test successful version retrieval."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="5.0.0\n", returncode=0)
            version = get_latest_version("lodash", tmp_path)

            assert version == "5.0.0"
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == ["npm", "view", "lodash", "version"]
            assert call_args[1]["cwd"] == tmp_path
            assert call_args[1]["timeout"] == 10

    def test_get_version_scoped_package(self, tmp_path: Path) -> None:
        """Test version retrieval for scoped package."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="5.0.8\n", returncode=0)
            version = get_latest_version("@vue/cli", tmp_path)

            assert version == "5.0.8"
            call_args = mock_run.call_args
            assert call_args[0][0] == ["npm", "view", "@vue/cli", "version"]

    def test_get_version_timeout(self, tmp_path: Path) -> None:
        """Test handling timeout error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(["npm"], 10)
            version = get_latest_version("lodash", tmp_path)
            assert version is None

    def test_get_version_not_found(self, tmp_path: Path) -> None:
        """Test handling package not found error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["npm"])
            version = get_latest_version("nonexistent-package", tmp_path)
            assert version is None

    def test_get_version_empty_output(self, tmp_path: Path) -> None:
        """Test handling empty output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", returncode=0)
            version = get_latest_version("lodash", tmp_path)
            assert version == ""


class TestGetLatestVersionsBatch:
    """Test get_latest_versions_batch function."""

    def test_batch_single_package(self, tmp_path: Path) -> None:
        """Test batch query with single package."""
        mock_response = json.dumps({"version": "5.0.0"})

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=mock_response, returncode=0)
            versions = get_latest_versions_batch(["lodash"], tmp_path)

            assert versions == {"lodash": "5.0.0"}

    def test_batch_multiple_packages(self, tmp_path: Path) -> None:
        """Test batch query with multiple packages."""
        mock_response = json.dumps([
            {"version": "5.0.0"},
            {"version": "8.0.0"},
            {"version": "5.0.8"},
        ])

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=mock_response, returncode=0)
            versions = get_latest_versions_batch(
                ["lodash", "eslint", "@vue/cli"], tmp_path
            )

            assert versions == {
                "lodash": "5.0.0",
                "eslint": "8.0.0",
                "@vue/cli": "5.0.8",
            }

    def test_batch_empty_list(self, tmp_path: Path) -> None:
        """Test batch query with empty package list."""
        versions = get_latest_versions_batch([], tmp_path)
        assert versions == {}

    def test_batch_subprocess_error(self, tmp_path: Path) -> None:
        """Test handling subprocess error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["npm"])
            versions = get_latest_versions_batch(["lodash"], tmp_path)
            assert versions == {}

    def test_batch_timeout(self, tmp_path: Path) -> None:
        """Test handling timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(["npm"], 30)
            versions = get_latest_versions_batch(["lodash"], tmp_path)
            assert versions == {}

    def test_batch_invalid_json(self, tmp_path: Path) -> None:
        """Test handling invalid JSON response."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="not valid json", returncode=0)
            versions = get_latest_versions_batch(["lodash"], tmp_path)
            assert versions == {}

    def test_batch_incomplete_response(self, tmp_path: Path) -> None:
        """Test handling incomplete response (fewer results than packages)."""
        mock_response = json.dumps([
            {"version": "5.0.0"}
            # Missing entries for other packages
        ])

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=mock_response, returncode=0)
            versions = get_latest_versions_batch(
                ["lodash", "eslint", "@vue/cli"], tmp_path
            )

            assert versions.get("lodash") == "5.0.0"
            assert versions.get("eslint") is None
            assert versions.get("@vue/cli") is None


class TestGetLatestVersionsParallel:
    """Test get_latest_versions_parallel function."""

    def test_parallel_small_batch_success(self, tmp_path: Path) -> None:
        """Test parallel queries with small package count (uses batch)."""
        packages = [("lodash", "4.17.21"), ("eslint", "7.0.0")]

        with patch("voltamanager.npm.get_latest_versions_batch") as mock_batch:
            mock_batch.return_value = {"lodash": "5.0.0", "eslint": "8.0.0"}

            versions = get_latest_versions_parallel(packages, tmp_path)

            assert versions == {"lodash": "5.0.0", "eslint": "8.0.0"}
            mock_batch.assert_called_once()

    def test_parallel_small_batch_fallback(self, tmp_path: Path) -> None:
        """Test fallback to parallel when batch fails."""
        packages = [("lodash", "4.17.21"), ("eslint", "7.0.0")]

        with (
            patch("voltamanager.npm.get_latest_versions_batch") as mock_batch,
            patch("voltamanager.npm.get_latest_version") as mock_get,
        ):
            mock_batch.return_value = {}  # Batch fails
            mock_get.side_effect = ["5.0.0", "8.0.0"]

            versions = get_latest_versions_parallel(packages, tmp_path)

            assert versions == {"lodash": "5.0.0", "eslint": "8.0.0"}
            assert mock_get.call_count == 2

    def test_parallel_large_batch(self, tmp_path: Path) -> None:
        """Test parallel queries with many packages (skips batch)."""
        packages = [(f"pkg{i}", "1.0.0") for i in range(10)]

        with patch("voltamanager.npm.get_latest_version") as mock_get:
            mock_get.return_value = "2.0.0"

            versions = get_latest_versions_parallel(packages, tmp_path)

            assert len(versions) == 10
            assert all(v == "2.0.0" for v in versions.values())
            assert mock_get.call_count == 10

    def test_parallel_project_packages_excluded(self, tmp_path: Path) -> None:
        """Test that project-pinned packages are excluded."""
        packages = [
            ("lodash", "4.17.21"),
            ("eslint", "project"),
            ("typescript", "5.0.0"),
        ]

        with patch("voltamanager.npm.get_latest_version") as mock_get:
            mock_get.return_value = "2.0.0"

            versions = get_latest_versions_parallel(packages, tmp_path)

            assert "eslint" not in versions
            assert "lodash" in versions
            assert "typescript" in versions
            assert mock_get.call_count == 2

    def test_parallel_empty_packages(self, tmp_path: Path) -> None:
        """Test with empty package list."""
        versions = get_latest_versions_parallel([], tmp_path)
        assert versions == {}

    def test_parallel_all_project_packages(self, tmp_path: Path) -> None:
        """Test with all project-pinned packages."""
        packages = [("pkg1", "project"), ("pkg2", "project")]

        versions = get_latest_versions_parallel(packages, tmp_path)
        assert versions == {}

    def test_parallel_exception_handling(self, tmp_path: Path) -> None:
        """Test handling exceptions in parallel execution."""
        packages = [("lodash", "4.17.21"), ("error-pkg", "1.0.0")]

        def mock_version(name: str, _: Path) -> str | None:
            if name == "error-pkg":
                raise Exception("Network error")
            return "2.0.0"

        with patch("voltamanager.npm.get_latest_version", side_effect=mock_version):
            versions = get_latest_versions_parallel(packages, tmp_path)

            assert versions["lodash"] == "2.0.0"
            assert versions["error-pkg"] is None

    def test_parallel_custom_max_workers(self, tmp_path: Path) -> None:
        """Test with custom max_workers parameter."""
        packages = [(f"pkg{i}", "1.0.0") for i in range(5)]

        with patch("voltamanager.npm.get_latest_version") as mock_get:
            mock_get.return_value = "2.0.0"

            # Just verify it runs without error - max_workers is internal implementation
            versions = get_latest_versions_parallel(packages, tmp_path, max_workers=3)

            assert len(versions) == 5
            assert all(v == "2.0.0" for v in versions.values())
