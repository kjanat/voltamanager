"""Tests for version flag functionality."""

import re

from typer.testing import CliRunner

from voltamanager import __version__, app

runner = CliRunner()


def test_version_flag() -> None:
    """Test --version flag shows version and exits."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"voltamanager {__version__}" in result.stdout


def test_version_flag_short() -> None:
    """Test -V flag shows version and exits."""
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert f"voltamanager {__version__}" in result.stdout


def test_version_with_other_flags() -> None:
    """Test version flag takes precedence over other flags."""
    result = runner.invoke(app, ["--version", "--update"])
    assert result.exit_code == 0
    assert f"voltamanager {__version__}" in result.stdout
    # Should not proceed to update logic
    assert "Fetching" not in result.stdout


def test_version_from_metadata() -> None:
    """Test that version is dynamically loaded from package metadata."""
    # The version should not be "unknown" in a properly installed package
    assert __version__ != "unknown"

    # Version should match semver format
    assert re.match(r"^\d+\.\d+\.\d+", __version__)
