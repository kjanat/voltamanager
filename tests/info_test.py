"""Tests for package info command."""

import json
import subprocess
from unittest.mock import patch

from typer.testing import CliRunner

from voltamanager import app

runner = CliRunner()


class TestInfoCommand:
    """Tests for voltamanager info command."""

    @staticmethod
    def test_info_success() -> None:
        """Test successful package info retrieval."""
        mock_data = {
            "name": "typescript",
            "description": "TypeScript is a language for application scale JavaScript development",
            "version": "5.0.0",
            "license": "Apache-2.0",
            "homepage": "https://www.typescriptlang.org/",
            "repository": {
                "type": "git",
                "url": "https://github.com/Microsoft/TypeScript",
            },
            "maintainers": [{"name": "Microsoft", "email": "typescript@microsoft.com"}],
            "time": {
                "created": "2012-10-01T15:00:00.000Z",
                "modified": "2023-03-01T10:00:00.000Z",
            },
            "dependencies": {"some-dep": "^1.0.0"},
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = json.dumps(mock_data)
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ["info", "typescript"])

            assert result.exit_code == 0
            assert "typescript" in result.stdout
            assert "TypeScript is a language" in result.stdout
            assert "5.0.0" in result.stdout
            assert "Apache-2.0" in result.stdout

    @staticmethod
    def test_info_package_not_found() -> None:
        """Test info command with non-existent package."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["npm"])

            result = runner.invoke(app, ["info", "nonexistent-pkg-12345"])

            assert result.exit_code == 1
            assert "not found" in result.stdout

    @staticmethod
    def test_info_invalid_json_response() -> None:
        """Test handling of invalid JSON response."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "{invalid json}"
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ["info", "some-package"])

            assert result.exit_code == 1
            assert "Failed to parse" in result.stdout

    @staticmethod
    def test_info_timeout() -> None:
        """Test handling of npm query timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(["npm"], 10)

            result = runner.invoke(app, ["info", "some-package"])

            assert result.exit_code == 1
            assert "timed out" in result.stdout

    @staticmethod
    def test_info_scoped_package() -> None:
        """Test info command with scoped package."""
        mock_data = {
            "name": "@vue/cli",
            "description": "Command line interface for Vue.js",
            "version": "5.0.8",
            "license": "MIT",
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = json.dumps(mock_data)
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ["info", "@vue/cli"])

            assert result.exit_code == 0
            assert "@vue/cli" in result.stdout
            assert "5.0.8" in result.stdout

    @staticmethod
    def test_info_with_repository_string() -> None:
        """Test info with repository as string (not dict)."""
        mock_data = {
            "name": "lodash",
            "version": "4.17.21",
            "repository": "https://github.com/lodash/lodash",
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = json.dumps(mock_data)
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ["info", "lodash"])

            assert result.exit_code == 0
            assert "lodash" in result.stdout
            assert "github.com/lodash/lodash" in result.stdout

    @staticmethod
    def test_info_minimal_data() -> None:
        """Test info with minimal package data."""
        mock_data = {"name": "minimal-pkg", "version": "1.0.0"}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = json.dumps(mock_data)
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ["info", "minimal-pkg"])

            assert result.exit_code == 0
            assert "minimal-pkg" in result.stdout
            assert "1.0.0" in result.stdout
            # Should handle missing fields gracefully
            assert "N/A" in result.stdout or "Description" in result.stdout
