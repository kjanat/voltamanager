"""Tests for selective rollback functionality."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from voltamanager import app


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def snapshot_dir(monkeypatch):
    """Create a temporary snapshot directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        snapshot_dir = Path(tmpdir) / ".voltamanager"
        snapshot_dir.mkdir()
        snapshot_file = snapshot_dir / "last_snapshot.json"

        # Create a test snapshot
        snapshot_data = {
            "typescript": "5.0.0",
            "eslint": "8.0.0",
            "prettier": "3.0.0",
            "@vue/cli": "5.0.0",
        }
        snapshot_file.write_text(json.dumps(snapshot_data, indent=2), encoding="utf-8")

        # Patch SNAPSHOT_FILE path
        with patch("pathlib.Path.home", return_value=Path(tmpdir)):
            yield snapshot_dir, snapshot_file


@patch("subprocess.run")
def test_rollback_all_packages(mock_run, runner, snapshot_dir) -> None:
    """Test rolling back all packages (original behavior)."""
    snapshot_dir, _snapshot_file = snapshot_dir

    with patch("pathlib.Path.home", return_value=snapshot_dir.parent):
        result = runner.invoke(app, ["rollback", "--force"])

    assert result.exit_code == 0
    assert "Rollback complete" in result.stdout

    # Verify volta install was called with all packages
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "volta" in call_args
    assert "install" in call_args
    assert "typescript@5.0.0" in call_args
    assert "eslint@8.0.0" in call_args
    assert "prettier@3.0.0" in call_args
    assert "@vue/cli@5.0.0" in call_args


@patch("subprocess.run")
def test_rollback_single_package(mock_run, runner, snapshot_dir) -> None:
    """Test rolling back a single specified package."""
    snapshot_dir, _snapshot_file = snapshot_dir

    with patch("pathlib.Path.home", return_value=snapshot_dir.parent):
        result = runner.invoke(app, ["rollback", "typescript", "--force"])

    assert result.exit_code == 0
    assert "Rollback complete" in result.stdout
    assert "Rolled back 1 packages" in result.stdout

    # Verify only typescript was rolled back
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "typescript@5.0.0" in call_args
    assert "eslint@8.0.0" not in call_args
    assert "prettier@3.0.0" not in call_args


@patch("subprocess.run")
def test_rollback_multiple_packages(mock_run, runner, snapshot_dir) -> None:
    """Test rolling back multiple specified packages."""
    snapshot_dir, _snapshot_file = snapshot_dir

    with patch("pathlib.Path.home", return_value=snapshot_dir.parent):
        result = runner.invoke(app, ["rollback", "typescript", "eslint", "--force"])

    assert result.exit_code == 0
    assert "Rollback complete" in result.stdout
    assert "Rolled back 2 packages" in result.stdout

    # Verify only specified packages were rolled back
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "typescript@5.0.0" in call_args
    assert "eslint@8.0.0" in call_args
    assert "prettier@3.0.0" not in call_args


def test_rollback_package_not_in_snapshot(runner, snapshot_dir) -> None:
    """Test rolling back a package that's not in the snapshot."""
    snapshot_dir, _snapshot_file = snapshot_dir

    with patch("pathlib.Path.home", return_value=snapshot_dir.parent):
        result = runner.invoke(app, ["rollback", "nonexistent", "--force"])

    assert result.exit_code == 1
    assert "None of the specified packages found in snapshot" in result.stdout


def test_rollback_partial_match_warns(runner, snapshot_dir) -> None:
    """Test warning when some packages aren't in snapshot."""
    snapshot_dir, _snapshot_file = snapshot_dir

    with patch("pathlib.Path.home", return_value=snapshot_dir.parent):
        with patch("subprocess.run"):
            result = runner.invoke(
                app, ["rollback", "typescript", "nonexistent", "--force"]
            )

    assert result.exit_code == 0
    assert "Packages not in snapshot (will be skipped): nonexistent" in result.stdout


@patch("subprocess.run")
def test_rollback_scoped_package(mock_run, runner, snapshot_dir) -> None:
    """Test rolling back a scoped package."""
    snapshot_dir, _snapshot_file = snapshot_dir

    with patch("pathlib.Path.home", return_value=snapshot_dir.parent):
        result = runner.invoke(app, ["rollback", "@vue/cli", "--force"])

    assert result.exit_code == 0
    assert "Rollback complete" in result.stdout

    # Verify scoped package was rolled back
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "@vue/cli@5.0.0" in call_args


def test_rollback_no_snapshot(runner) -> None:
    """Test rollback when no snapshot exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pathlib.Path.home", return_value=Path(tmpdir)):
            result = runner.invoke(app, ["rollback", "--force"])

    assert result.exit_code == 1
    assert "No snapshot found - cannot rollback" in result.stdout
    assert "Snapshots are created before updates" in result.stdout


@patch("subprocess.run")
def test_rollback_volta_failure(mock_run, runner, snapshot_dir) -> None:
    """Test handling of volta install failure during rollback."""
    snapshot_dir, _snapshot_file = snapshot_dir

    # Simulate subprocess.CalledProcessError
    mock_run.side_effect = subprocess.CalledProcessError(1, "volta")

    with patch("pathlib.Path.home", return_value=snapshot_dir.parent):
        result = runner.invoke(app, ["rollback", "--force"])

    assert result.exit_code == 1
    assert "Rollback failed" in result.stdout


def test_rollback_requires_confirmation_without_force(runner, snapshot_dir) -> None:
    """Test that rollback requires confirmation when --force is not used."""
    snapshot_dir, _snapshot_file = snapshot_dir

    with patch("pathlib.Path.home", return_value=snapshot_dir.parent):
        # Simulate user declining confirmation
        result = runner.invoke(app, ["rollback"], input="n\n")

    assert result.exit_code == 0
    assert "Rollback cancelled" in result.stdout


@patch("subprocess.run")
def test_rollback_with_confirmation(mock_run, runner, snapshot_dir) -> None:
    """Test rollback when user confirms."""
    snapshot_dir, _snapshot_file = snapshot_dir

    with patch("pathlib.Path.home", return_value=snapshot_dir.parent):
        # Simulate user confirming
        result = runner.invoke(app, ["rollback"], input="y\n")

    assert result.exit_code == 0
    assert "Rollback complete" in result.stdout
    mock_run.assert_called_once()
