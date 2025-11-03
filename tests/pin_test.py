"""Tests for pin/unpin commands."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from voltamanager import app


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "voltamanager"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"

        # Patch CONFIG_DIR and CONFIG_FILE
        import voltamanager.config as config_module  # noqa: PLC0415

        monkeypatch.setattr(config_module, "CONFIG_DIR", config_dir)
        monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)

        # Create initial empty config
        config_file.write_text(
            """[voltamanager]
exclude = []
include_project = false
cache_ttl_hours = 1
parallel_checks = 10
""",
            encoding="utf-8",
        )

        yield config_dir, config_file


def test_pin_single_package(runner, temp_config_dir):
    """Test pinning a single package."""
    _config_dir, config_file = temp_config_dir

    result = runner.invoke(app, ["pin", "typescript"])

    assert result.exit_code == 0
    assert "✓ Pinned 1 package(s): typescript" in result.stdout
    assert "These packages will be excluded from future updates" in result.stdout
    assert "Currently pinned packages:" in result.stdout
    assert "• typescript" in result.stdout

    # Verify config file was updated
    config_content = config_file.read_text(encoding="utf-8")
    assert '"typescript"' in config_content


def test_pin_multiple_packages(runner, temp_config_dir):
    """Test pinning multiple packages at once."""
    _config_dir, config_file = temp_config_dir

    result = runner.invoke(app, ["pin", "typescript", "eslint", "prettier"])

    assert result.exit_code == 0
    assert "✓ Pinned 3 package(s): typescript, eslint, prettier" in result.stdout

    # Verify all packages are in config
    config_content = config_file.read_text(encoding="utf-8")
    assert '"typescript"' in config_content
    assert '"eslint"' in config_content
    assert '"prettier"' in config_content


def test_pin_already_pinned(runner, temp_config_dir):
    """Test pinning a package that's already pinned."""
    _config_dir, _config_file = temp_config_dir

    # Pin once
    runner.invoke(app, ["pin", "typescript"])

    # Try to pin again
    result = runner.invoke(app, ["pin", "typescript"])

    assert result.exit_code == 0
    assert "All specified packages were already pinned" in result.stdout
    assert "Currently pinned packages:" in result.stdout


def test_unpin_package(runner, temp_config_dir):
    """Test unpinning a package."""
    _config_dir, config_file = temp_config_dir

    # First pin a package
    runner.invoke(app, ["pin", "typescript"])

    # Then unpin it
    result = runner.invoke(app, ["pin", "--unpin", "typescript"])

    assert result.exit_code == 0
    assert "✓ Unpinned 1 package(s): typescript" in result.stdout

    # Verify config was updated
    config_content = config_file.read_text(encoding="utf-8")
    assert "exclude = []" in config_content


def test_unpin_not_pinned(runner, temp_config_dir):
    """Test unpinning a package that wasn't pinned."""
    _config_dir, _config_file = temp_config_dir

    result = runner.invoke(app, ["pin", "--unpin", "typescript"])

    assert result.exit_code == 0
    assert "None of the specified packages were pinned" in result.stdout


def test_unpin_multiple_packages(runner, temp_config_dir):
    """Test unpinning multiple packages."""
    _config_dir, config_file = temp_config_dir

    # Pin multiple packages
    runner.invoke(app, ["pin", "typescript", "eslint", "prettier"])

    # Unpin two of them
    result = runner.invoke(app, ["pin", "--unpin", "typescript", "eslint"])

    assert result.exit_code == 0
    assert "✓ Unpinned 2 package(s): typescript, eslint" in result.stdout

    # Verify only prettier remains
    config_content = config_file.read_text(encoding="utf-8")
    assert '"typescript"' not in config_content
    assert '"eslint"' not in config_content
    assert '"prettier"' in config_content


def test_pin_preserves_other_config(runner, temp_config_dir):
    """Test that pinning doesn't break other config values."""
    _config_dir, config_file = temp_config_dir

    # Set custom config values
    config_file.write_text(
        """[voltamanager]
exclude = []
include_project = true
cache_ttl_hours = 24
parallel_checks = 20
"""
    )

    # Pin a package
    runner.invoke(app, ["pin", "typescript"])

    # Verify other config values are preserved
    config_content = config_file.read_text(encoding="utf-8")
    assert "include_project = true" in config_content
    assert "cache_ttl_hours = 24" in config_content
    assert "parallel_checks = 20" in config_content
