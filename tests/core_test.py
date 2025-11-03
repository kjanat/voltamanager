"""Tests for core module."""

from pathlib import Path
from unittest.mock import Mock, patch

from voltamanager.core import (
    check_dependencies,
    get_installed_packages,
    parse_package,
)


class TestCheckDependencies:
    """Test check_dependencies function."""

    @staticmethod
    def test_both_dependencies_available() -> None:
        """Test when both volta and npm are available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/volta"
            assert check_dependencies() is True
            assert mock_which.call_count == 2

    @staticmethod
    def test_volta_missing() -> None:
        """Test when volta is not in PATH."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = (
                lambda cmd: None if cmd == "volta" else "/usr/bin/npm"
            )
            assert check_dependencies() is False

    @staticmethod
    def test_npm_missing() -> None:
        """Test when npm is not in PATH."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = (
                lambda cmd: "/usr/bin/volta" if cmd == "volta" else None
            )
            assert check_dependencies() is False

    @staticmethod
    def test_both_dependencies_missing() -> None:
        """Test when neither volta nor npm are available."""
        with patch("shutil.which", return_value=None):
            assert check_dependencies() is False


class TestGetInstalledPackages:
    """Test get_installed_packages function."""

    def test_get_packages_success(self, tmp_path: Path) -> None:
        """Test successful package retrieval."""
        mock_output = """package typescript@5.0.0
package eslint@8.0.0
package @vue/cli@5.0.8
tool node@18.0.0"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=mock_output, returncode=0)
            packages = get_installed_packages(tmp_path)

            assert len(packages) == 3
            assert "typescript@5.0.0" in packages
            assert "eslint@8.0.0" in packages
            assert "@vue/cli@5.0.8" in packages

            # Verify subprocess was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == ["volta", "list", "--format=plain"]
            assert call_args[1]["cwd"] == tmp_path

    def test_get_packages_empty_output(self, tmp_path: Path) -> None:
        """Test with no packages installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", returncode=0)
            packages = get_installed_packages(tmp_path)
            assert packages == []

    def test_get_packages_subprocess_error(self, tmp_path: Path) -> None:
        """Test handling subprocess CalledProcessError."""
        import subprocess  # noqa: PLC0415

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["volta", "list"])
            packages = get_installed_packages(tmp_path)
            assert packages == []

    def test_get_packages_only_tools(self, tmp_path: Path) -> None:
        """Test output with only tools (no packages)."""
        mock_output = """tool node@18.0.0
tool yarn@1.22.0"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=mock_output, returncode=0)
            packages = get_installed_packages(tmp_path)
            assert packages == []


class TestParsePackage:
    """Test parse_package function."""

    @staticmethod
    def test_parse_regular_package() -> None:
        """Test parsing regular package with version."""
        name, version = parse_package("lodash@4.17.21")
        assert name == "lodash"
        assert version == "4.17.21"

    @staticmethod
    def test_parse_scoped_package() -> None:
        """Test parsing scoped package with version."""
        name, version = parse_package("@vue/cli@5.0.8")
        assert name == "@vue/cli"
        assert version == "5.0.8"

    @staticmethod
    def test_parse_scoped_package_complex() -> None:
        """Test parsing scoped package with complex scope."""
        name, version = parse_package("@typescript-eslint/parser@6.0.0")
        assert name == "@typescript-eslint/parser"
        assert version == "6.0.0"

    @staticmethod
    def test_parse_no_version() -> None:
        """Test parsing package without version."""
        name, version = parse_package("lodash")
        assert name == "lodash"
        assert not version

    @staticmethod
    def test_parse_scoped_no_version() -> None:
        """Test parsing scoped package without version."""
        name, version = parse_package("@vue/cli")
        assert name == "@vue/cli"
        assert not version

    @staticmethod
    def test_parse_empty_string() -> None:
        """Test parsing empty string."""
        name, version = parse_package("")
        assert not name
        assert not version

    @staticmethod
    def test_parse_prerelease_version() -> None:
        """Test parsing package with prerelease version."""
        name, version = parse_package("react@18.0.0-rc.0")
        assert name == "react"
        assert version == "18.0.0-rc.0"

    @staticmethod
    def test_parse_scoped_prerelease() -> None:
        """Test parsing scoped package with prerelease version."""
        name, version = parse_package("@babel/core@7.22.0-beta.1")
        assert name == "@babel/core"
        assert version == "7.22.0-beta.1"

    @staticmethod
    def test_parse_multiple_at_signs() -> None:
        """Test parsing package name with multiple @ - uses first @ for split."""
        # Note: parse_package uses split() not rsplit() for non-scoped packages
        name, version = parse_package("package@1.0.0@special")
        assert name == "package"
        assert version == "1.0.0"
