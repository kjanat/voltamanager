"""Tests for --all-packages flag functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from voltamanager.config import Config
from voltamanager.operations import check_and_update


def test_all_packages_flag_shows_excluded() -> None:
    """Test --all-packages flag includes excluded packages in display."""
    namevers = [
        "typescript@5.0.0",
        "eslint@8.0.0",
        "prettier@3.0.0",  # This will be excluded
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        # Create config with prettier excluded
        config = Config()
        config.exclude = ["prettier"]

        # Mock the npm calls
        with (
            patch(
                "voltamanager.operations.get_latest_versions_parallel"
            ) as mock_parallel,
            patch("voltamanager.operations.display_table") as mock_display,
            patch("voltamanager.operations.display_statistics"),
            patch("voltamanager.operations.console"),
        ):
            mock_parallel.return_value = {
                "typescript": "5.3.0",
                "eslint": "8.5.0",
            }

            # Call with all_packages=True
            check_and_update(
                namevers=namevers,
                safe_dir=safe_dir,
                do_check=True,
                do_update=False,
                dry_run=False,
                include_project=False,
                json_output=False,
                outdated_only=False,
                interactive=False,
                use_cache=False,
                config=config,
                verbose=False,
                all_packages=True,
            )

            # Verify display_table was called
            assert mock_display.called
            call_args = mock_display.call_args[0]
            names = call_args[0]
            states = call_args[3]

            # Should include prettier with EXCLUDED status
            assert "prettier" in names
            prettier_idx = names.index("prettier")
            assert states[prettier_idx] == "EXCLUDED"


def test_without_all_packages_flag_hides_excluded() -> None:
    """Test without --all-packages flag, excluded packages are hidden."""
    namevers = [
        "typescript@5.0.0",
        "eslint@8.0.0",
        "prettier@3.0.0",  # This will be excluded
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        # Create config with prettier excluded
        config = Config()
        config.exclude = ["prettier"]

        # Mock the npm calls
        with (
            patch(
                "voltamanager.operations.get_latest_versions_parallel"
            ) as mock_parallel,
            patch("voltamanager.operations.display_table") as mock_display,
            patch("voltamanager.operations.display_statistics"),
            patch("voltamanager.operations.console"),
            patch("voltamanager.operations.check_local_volta_config"),
        ):
            mock_parallel.return_value = {
                "typescript": "5.3.0",
                "eslint": "8.5.0",
            }

            # Call with all_packages=False (default)
            check_and_update(
                namevers=namevers,
                safe_dir=safe_dir,
                do_check=True,
                do_update=False,
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

            # Verify display_table was called
            assert mock_display.called
            call_args = mock_display.call_args[0]
            names = call_args[0]

            # Should NOT include prettier
            assert "prettier" not in names


def test_all_packages_with_multiple_excluded() -> None:
    """Test --all-packages with multiple excluded packages."""
    namevers = [
        "typescript@5.0.0",
        "eslint@8.0.0",
        "prettier@3.0.0",
        "webpack@5.0.0",
        "vite@4.0.0",
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        # Create config with multiple exclusions
        config = Config()
        config.exclude = ["prettier", "webpack"]

        # Mock the npm calls
        with (
            patch(
                "voltamanager.operations.get_latest_versions_parallel"
            ) as mock_parallel,
            patch("voltamanager.operations.display_table") as mock_display,
            patch("voltamanager.operations.display_statistics"),
        ):
            mock_parallel.return_value = {
                "typescript": "5.3.0",
                "eslint": "8.5.0",
                "vite": "4.5.0",
            }

            # Call with all_packages=True
            check_and_update(
                namevers=namevers,
                safe_dir=safe_dir,
                do_check=True,
                do_update=False,
                dry_run=False,
                include_project=False,
                json_output=False,
                outdated_only=False,
                interactive=False,
                use_cache=False,
                config=config,
                verbose=False,
                all_packages=True,
            )

            # Verify both excluded packages are shown
            assert mock_display.called
            call_args = mock_display.call_args[0]
            names = call_args[0]
            states = call_args[3]

            assert "prettier" in names
            assert "webpack" in names

            prettier_idx = names.index("prettier")
            webpack_idx = names.index("webpack")

            assert states[prettier_idx] == "EXCLUDED"
            assert states[webpack_idx] == "EXCLUDED"


def test_all_packages_json_output() -> None:
    """Test --all-packages works with JSON output."""
    namevers = [
        "typescript@5.0.0",
        "prettier@3.0.0",  # excluded
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        config = Config()
        config.exclude = ["prettier"]

        with (
            patch(
                "voltamanager.operations.get_latest_versions_parallel"
            ) as mock_parallel,
            patch("voltamanager.operations.display_json") as mock_json,
        ):
            mock_parallel.return_value = {"typescript": "5.3.0"}

            # Call with json_output and all_packages
            check_and_update(
                namevers=namevers,
                safe_dir=safe_dir,
                do_check=True,
                do_update=False,
                dry_run=False,
                include_project=False,
                json_output=True,
                outdated_only=False,
                interactive=False,
                use_cache=False,
                config=config,
                verbose=False,
                all_packages=True,
            )

            # Verify JSON output includes excluded package
            assert mock_json.called
            call_args = mock_json.call_args[0]
            names = call_args[0]
            states = call_args[3]

            assert "prettier" in names
            assert "EXCLUDED" in states
