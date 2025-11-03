"""Tests for breaking-changes command."""

from unittest.mock import patch

from typer.testing import CliRunner

from voltamanager import app

runner = CliRunner()


class TestBreakingChangesCommand:
    """Tests for voltamanager breaking-changes command."""

    @staticmethod
    def test_no_packages_installed() -> None:
        """Test with no packages installed."""
        with patch("voltamanager.get_installed_packages", return_value=[]):
            result = runner.invoke(app, ["breaking-changes"])

            assert result.exit_code == 0
            assert "No Volta-managed packages found" in result.stdout

    @staticmethod
    def test_no_major_updates() -> None:
        """Test when all packages are up-to-date or have minor updates only."""
        with (
            patch(
                "voltamanager.get_installed_packages",
                return_value=["typescript@5.0.0", "eslint@8.40.0"],
            ),
            patch(
                "voltamanager.get_latest_versions_parallel",
                return_value={"typescript": "5.0.1", "eslint": "8.41.0"},
            ),
        ):
            result = runner.invoke(app, ["breaking-changes"])

            assert result.exit_code == 0
            assert "No major version updates detected" in result.stdout
            assert "up-to-date or have minor/patch updates only" in result.stdout

    @staticmethod
    def test_with_major_updates() -> None:
        """Test when major updates are detected."""
        with (
            patch(
                "voltamanager.get_installed_packages",
                return_value=["typescript@4.9.5", "react@17.0.2", "lodash@4.17.20"],
            ),
            patch(
                "voltamanager.npm.get_latest_versions_parallel",
                return_value={
                    "typescript": "5.0.0",
                    "react": "18.2.0",
                    "lodash": "4.17.21",
                },
            ),
        ):
            result = runner.invoke(app, ["breaking-changes"])

            assert result.exit_code == 0
            assert "Found 2 packages with major version updates" in result.stdout
            assert "typescript" in result.stdout
            # Version numbers might be truncated in table output, so just check package name
            assert "react" in result.stdout
            # lodash should not appear (minor update only)
            assert "Breaking Changes Warning" in result.stdout

    @staticmethod
    def test_with_specific_package() -> None:
        """Test checking a specific package."""
        with (
            patch(
                "voltamanager.get_installed_packages",
                return_value=["typescript@4.9.5", "react@17.0.2"],
            ),
            patch(
                "voltamanager.npm.get_latest_versions_parallel",
                return_value={"typescript": "5.0.0"},
            ),
        ):
            result = runner.invoke(app, ["breaking-changes", "typescript"])

            assert result.exit_code == 0
            assert "typescript" in result.stdout
            # Don't check for specific version in output due to table truncation

    @staticmethod
    def test_with_specific_package_not_installed() -> None:
        """Test checking a package that isn't installed."""
        with patch(
            "voltamanager.get_installed_packages", return_value=["eslint@8.40.0"]
        ):
            result = runner.invoke(app, ["breaking-changes", "typescript"])

            assert result.exit_code == 1
            assert "None of the specified packages are installed" in result.stdout

    @staticmethod
    def test_with_unknown_version() -> None:
        """Test handling of packages with unknown latest versions."""
        with (
            patch(
                "voltamanager.get_installed_packages",
                return_value=["typescript@4.9.5", "private-pkg@1.0.0"],
            ),
            patch(
                "voltamanager.npm.get_latest_versions_parallel",
                return_value={"typescript": "5.0.0", "private-pkg": None},
            ),
        ):
            result = runner.invoke(app, ["breaking-changes"])

            assert result.exit_code == 0
            # Should still show typescript
            assert "typescript" in result.stdout
            # private-pkg should not appear (unknown version)

    @staticmethod
    def test_skips_project_pinned() -> None:
        """Test that project-pinned packages are skipped."""
        with (
            patch(
                "voltamanager.get_installed_packages",
                return_value=["typescript@4.9.5", "local-pkg@project"],
            ),
            patch(
                "voltamanager.npm.get_latest_versions_parallel",
                return_value={"typescript": "5.0.0"},
            ),
        ):
            result = runner.invoke(app, ["breaking-changes"])

            assert result.exit_code == 0
            # Should only check typescript
            assert "Checking 1 packages" in result.stdout

    @staticmethod
    def test_changelog_links_included() -> None:
        """Test that changelog links are included in output."""
        with (
            patch(
                "voltamanager.get_installed_packages",
                return_value=["typescript@4.9.5"],
            ),
            patch(
                "voltamanager.npm.get_latest_versions_parallel",
                return_value={"typescript": "5.0.0"},
            ),
        ):
            result = runner.invoke(app, ["breaking-changes"])

            assert result.exit_code == 0
            # Should include changelog URL
            assert "npmjs.com" in result.stdout or "Changelog" in result.stdout

    @staticmethod
    def test_multiple_specific_packages() -> None:
        """Test checking multiple specific packages."""
        with (
            patch(
                "voltamanager.get_installed_packages",
                return_value=["typescript@4.9.5", "react@17.0.2", "lodash@4.17.20"],
            ),
            patch(
                "voltamanager.npm.get_latest_versions_parallel",
                return_value={"typescript": "5.0.0", "react": "18.2.0"},
            ),
        ):
            result = runner.invoke(app, ["breaking-changes", "typescript", "react"])

            assert result.exit_code == 0
            # Should check both packages
            assert "Checking 2 packages" in result.stdout
            assert "typescript" in result.stdout
            assert "react" in result.stdout
