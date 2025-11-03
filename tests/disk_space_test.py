"""Tests for disk space checking functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from voltamanager.config import Config
from voltamanager.operations import check_and_update
from voltamanager.utils import check_disk_space, estimate_update_size


def test_check_disk_space_sufficient():
    """Test disk space check with sufficient space."""
    # Mock shutil.disk_usage to return plenty of space (10GB)
    with patch("voltamanager.utils.shutil.disk_usage") as mock_disk:
        mock_disk.return_value = type(
            "obj", (object,), {"free": 10 * 1024 * 1024 * 1024}
        )()

        sufficient, available = check_disk_space(min_mb=500)
        assert sufficient is True
        assert available >= 500


def test_check_disk_space_insufficient():
    """Test disk space check with insufficient space."""
    # Mock shutil.disk_usage to return low space (100MB)
    with patch("voltamanager.utils.shutil.disk_usage") as mock_disk:
        mock_disk.return_value = type("obj", (object,), {"free": 100 * 1024 * 1024})()

        sufficient, available = check_disk_space(min_mb=500)
        assert sufficient is False
        assert available < 500


def test_check_disk_space_error_handling():
    """Test disk space check handles OS errors gracefully."""
    with patch("voltamanager.utils.shutil.disk_usage") as mock_disk:
        mock_disk.side_effect = OSError("Cannot access disk")

        sufficient, available = check_disk_space(min_mb=500)
        # Should assume okay if can't check
        assert sufficient is True
        assert available == -1


def test_estimate_update_size():
    """Test update size estimation."""
    # 1 package = 50MB
    assert estimate_update_size(1) == 50

    # 5 packages = 250MB
    assert estimate_update_size(5) == 250

    # 10 packages = 500MB
    assert estimate_update_size(10) == 500


def test_update_blocks_on_insufficient_space():
    """Test that updates are blocked when disk space is insufficient."""
    namevers = ["typescript@5.0.0", "eslint@8.0.0", "prettier@3.0.0"]

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)
        config = Config()

        # Mock insufficient disk space (100MB available, need ~150MB)
        with (
            patch("voltamanager.utils.shutil.disk_usage") as mock_disk,
            patch(
                "voltamanager.operations.get_latest_versions_parallel"
            ) as mock_parallel,
            patch("voltamanager.operations.console") as mock_console,
        ):
            mock_disk.return_value = type(
                "obj", (object,), {"free": 100 * 1024 * 1024}
            )()
            mock_parallel.return_value = {
                "typescript": "5.3.0",
                "eslint": "8.5.0",
                "prettier": "3.1.0",
            }

            # Attempt update with insufficient space
            result = check_and_update(
                namevers=namevers,
                safe_dir=safe_dir,
                do_check=True,
                do_update=True,  # Try to update
                dry_run=False,
                include_project=False,
                json_output=False,
                outdated_only=False,
                interactive=False,
                use_cache=False,
                config=config,
                verbose=False,
                all_packages=False,
            )

            # Should return error code
            assert result == 1

            # Should print error message
            calls = [str(call) for call in mock_console.print.call_args_list]
            error_printed = any(
                "Insufficient disk space" in str(call) for call in calls
            )
            assert error_printed


def test_update_proceeds_with_sufficient_space():
    """Test that updates proceed when disk space is sufficient."""
    namevers = ["typescript@5.0.0"]

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)
        config = Config()

        # Mock sufficient disk space (10GB available)
        with (
            patch("voltamanager.utils.shutil.disk_usage") as mock_disk,
            patch(
                "voltamanager.operations.get_latest_versions_parallel"
            ) as mock_parallel,
            patch("voltamanager.operations.subprocess.run") as mock_run,
            patch("voltamanager.operations.save_snapshot"),
            patch("voltamanager.operations.log_update"),
        ):
            mock_disk.return_value = type(
                "obj", (object,), {"free": 10 * 1024 * 1024 * 1024}
            )()
            mock_parallel.return_value = {"typescript": "5.3.0"}
            mock_run.return_value = type("obj", (object,), {"returncode": 0})()

            # Attempt update with sufficient space
            result = check_and_update(
                namevers=namevers,
                safe_dir=safe_dir,
                do_check=True,
                do_update=True,
                dry_run=False,
                include_project=False,
                json_output=False,
                outdated_only=False,
                interactive=False,
                use_cache=False,
                config=config,
                verbose=False,
                all_packages=False,
            )

            # Should succeed
            assert result == 0

            # Should have called volta install
            assert mock_run.called


def test_dry_run_skips_disk_check():
    """Test that dry run skips disk space check."""
    namevers = ["typescript@5.0.0"]

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)
        config = Config()

        # Mock insufficient space, but dry run should proceed anyway
        with (
            patch("voltamanager.utils.shutil.disk_usage") as mock_disk,
            patch(
                "voltamanager.operations.get_latest_versions_parallel"
            ) as mock_parallel,
            patch("voltamanager.operations.display_dry_run_report") as mock_report,
        ):
            mock_disk.return_value = type(
                "obj", (object,), {"free": 10 * 1024 * 1024}
            )()  # Very low space
            mock_parallel.return_value = {"typescript": "5.3.0"}

            # Dry run with insufficient space should still show report
            result = check_and_update(
                namevers=namevers,
                safe_dir=safe_dir,
                do_check=True,
                do_update=True,
                dry_run=True,  # Dry run
                include_project=False,
                json_output=False,
                outdated_only=False,
                interactive=False,
                use_cache=False,
                config=config,
                verbose=False,
                all_packages=False,
            )

            # Should succeed and show report
            assert result == 0
            assert mock_report.called


def test_verbose_shows_disk_check_pass():
    """Test that verbose mode shows disk space check passed."""
    namevers = ["typescript@5.0.0"]

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)
        config = Config()

        with (
            patch("voltamanager.utils.shutil.disk_usage") as mock_disk,
            patch(
                "voltamanager.operations.get_latest_versions_parallel"
            ) as mock_parallel,
            patch("voltamanager.operations.subprocess.run") as mock_run,
            patch("voltamanager.operations.save_snapshot"),
            patch("voltamanager.operations.log_update"),
            patch("voltamanager.operations.console") as mock_console,
        ):
            mock_disk.return_value = type(
                "obj", (object,), {"free": 10 * 1024 * 1024 * 1024}
            )()
            mock_parallel.return_value = {"typescript": "5.3.0"}
            mock_run.return_value = type("obj", (object,), {"returncode": 0})()

            # Update with verbose mode
            check_and_update(
                namevers=namevers,
                safe_dir=safe_dir,
                do_check=True,
                do_update=True,
                dry_run=False,
                include_project=False,
                json_output=False,
                outdated_only=False,
                interactive=False,
                use_cache=False,
                config=config,
                verbose=True,  # Verbose mode
                all_packages=False,
            )

            # Should print disk check passed message
            calls = [str(call) for call in mock_console.print.call_args_list]
            disk_check_shown = any(
                "Disk space check passed" in str(call) for call in calls
            )
            assert disk_check_shown
