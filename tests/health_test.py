"""Tests for health check functionality."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from voltamanager.core import (
    HealthCheckResult,
    check_volta_health,
    display_health_check,
)


def test_check_volta_health_all_good() -> None:
    """Test health check when everything is properly installed."""
    with (
        patch("voltamanager.core.shutil.which") as mock_which,
        patch("voltamanager.core.subprocess.run") as mock_run,
        patch("voltamanager.core.Path.exists") as mock_exists,
        patch("os.environ.get") as mock_env,
        patch("voltamanager.core.get_installed_packages") as mock_packages,
    ):
        # Setup mocks
        mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"
        mock_exists.return_value = True
        mock_env.return_value = "/home/user/.volta"
        mock_packages.return_value = ["pkg1@1.0.0", "pkg2@2.0.0"]

        # Mock version commands
        def run_side_effect(*args, **kwargs):
            result = MagicMock()
            if "volta" in args[0]:
                result.stdout = "1.1.0"
            elif "npm" in args[0]:
                result.stdout = "9.0.0"
            elif "node" in args[0]:
                result.stdout = "v18.0.0"
            return result

        mock_run.side_effect = run_side_effect

        results = check_volta_health()

        assert results["volta_installed"] is True
        assert results["npm_installed"] is True
        assert results["volta_version"] == "1.1.0"
        assert results["npm_version"] == "9.0.0"
        assert results["node_version"] == "v18.0.0"
        assert results["volta_home"] == "/home/user/.volta"
        assert results["packages_count"] == 2
        assert len(results["issues"]) == 0


def test_check_volta_health_volta_missing() -> None:
    """Test health check when volta is not installed."""
    with patch("voltamanager.core.shutil.which") as mock_which:
        mock_which.return_value = None

        results = check_volta_health()

        assert results["volta_installed"] is False
        assert "volta not found in PATH" in results["issues"]


def test_check_volta_health_npm_missing() -> None:
    """Test health check when npm is not installed."""
    with (
        patch("voltamanager.core.shutil.which") as mock_which,
        patch("voltamanager.core.subprocess.run") as mock_run,
    ):
        # volta exists, npm doesn't
        mock_which.side_effect = (
            lambda cmd: "/usr/bin/volta" if cmd == "volta" else None
        )

        def run_side_effect(*args, **kwargs):
            result = MagicMock()
            result.stdout = "1.1.0"
            return result

        mock_run.side_effect = run_side_effect

        results = check_volta_health()

        assert results["volta_installed"] is True
        assert results["npm_installed"] is False
        assert "npm not found in PATH" in results["issues"]


def test_check_volta_health_no_volta_home() -> None:
    """Test health check when VOLTA_HOME is not set."""
    with (
        patch("voltamanager.core.shutil.which") as mock_which,
        patch("voltamanager.core.subprocess.run") as mock_run,
        patch("os.environ.get") as mock_env,
    ):
        mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"
        mock_env.return_value = None  # VOLTA_HOME not set

        def run_side_effect(*args, **kwargs):
            result = MagicMock()
            result.stdout = "1.1.0"
            return result

        mock_run.side_effect = run_side_effect

        results = check_volta_health()

        assert "VOLTA_HOME environment variable not set" in results["issues"]


def test_check_volta_health_volta_home_missing_dir() -> None:
    """Test health check when VOLTA_HOME directory doesn't exist."""
    with (
        patch("voltamanager.core.shutil.which") as mock_which,
        patch("voltamanager.core.subprocess.run") as mock_run,
        patch("voltamanager.core.Path.exists") as mock_exists,
        patch("os.environ.get") as mock_env,
    ):
        mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"
        mock_exists.return_value = False
        mock_env.return_value = "/home/user/.volta"

        def run_side_effect(*args, **kwargs):
            result = MagicMock()
            result.stdout = "1.1.0"
            return result

        mock_run.side_effect = run_side_effect

        results = check_volta_health()

        assert any("does not exist" in issue for issue in results["issues"])


def test_check_volta_health_version_command_fails() -> None:
    """Test health check when version commands timeout."""
    with (
        patch("voltamanager.core.shutil.which") as mock_which,
        patch("voltamanager.core.subprocess.run") as mock_run,
    ):
        mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)

        results = check_volta_health()

        assert results["volta_installed"] is True
        assert "Cannot determine volta version" in results["issues"]


def test_display_health_check_with_issues(capsys: pytest.CaptureFixture[str]) -> None:
    """Test displaying health check results with issues."""
    results: HealthCheckResult = {
        "volta_installed": True,
        "npm_installed": False,
        "volta_version": "1.1.0",
        "npm_version": None,
        "node_version": None,
        "volta_home": None,
        "packages_count": 0,
        "issues": ["npm not found in PATH", "VOLTA_HOME environment variable not set"],
    }

    display_health_check(results)
    captured = capsys.readouterr()

    assert "Health Check" in captured.out
    assert "Issues Detected" in captured.out
    assert "npm not found in PATH" in captured.out


def test_display_health_check_no_issues(capsys: pytest.CaptureFixture[str]) -> None:
    """Test displaying health check results without issues."""
    results: HealthCheckResult = {
        "volta_installed": True,
        "npm_installed": True,
        "volta_version": "1.1.0",
        "npm_version": "9.0.0",
        "node_version": "v18.0.0",
        "volta_home": "/home/user/.volta",
        "packages_count": 5,
        "issues": [],
    }

    display_health_check(results)
    captured = capsys.readouterr()

    assert "Health Check" in captured.out
    assert "All checks passed" in captured.out
