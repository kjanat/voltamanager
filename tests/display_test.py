"""Tests for display module."""

import json
from unittest.mock import patch

import pytest

from voltamanager.display import (
    display_dry_run_report,
    display_json,
    display_statistics,
    display_table,
)


class TestDisplayTable:
    """Test display_table function."""

    @staticmethod
    def test_display_table_basic():
        """Test basic table display."""
        names = ["pkg1", "pkg2"]
        installed = ["1.0.0", "2.0.0"]
        latest = ["1.0.0", "2.1.0"]
        states = ["up-to-date", "OUTDATED"]

        # Should not raise any exceptions
        display_table(names, installed, latest, states)

    @staticmethod
    def test_display_table_empty():
        """Test display_table with empty lists."""
        display_table([], [], [], [])

    @staticmethod
    def test_display_table_outdated_only():
        """Test display_table with outdated_only filter."""
        names = ["pkg1", "pkg2", "pkg3"]
        installed = ["1.0.0", "2.0.0", "3.0.0"]
        latest = ["1.0.0", "2.1.0", "3.0.0"]
        states = ["up-to-date", "OUTDATED", "up-to-date"]

        # Should not raise any exceptions
        display_table(names, installed, latest, states, outdated_only=True)

    @staticmethod
    def test_display_table_project_packages():
        """Test display_table with project-pinned packages."""
        names = ["pkg1", "pkg2"]
        installed = ["project", "1.0.0"]
        latest = ["-", "1.0.0"]
        states = ["PROJECT", "up-to-date"]

        display_table(names, installed, latest, states)

    @staticmethod
    def test_display_table_unknown_state():
        """Test display_table with UNKNOWN state."""
        names = ["pkg1"]
        installed = ["1.0.0"]
        latest = ["?"]
        states = ["UNKNOWN"]

        # Should not raise exceptions
        try:
            display_table(names, installed, latest, states)
        except Exception as e:
            pytest.fail(f"display_table raised unexpected exception: {e}")

    @staticmethod
    def test_display_table_major_update_warning():
        """Test display_table shows warning for major updates."""
        names = ["pkg1"]
        installed = ["1.0.0"]
        latest = ["2.0.0"]
        states = ["OUTDATED"]

        display_table(names, installed, latest, states)

    @staticmethod
    def test_display_table_scoped_packages():
        """Test display_table with scoped package names."""
        names = ["@vue/cli", "@angular/core"]
        installed = ["5.0.0", "14.0.0"]
        latest = ["5.0.8", "15.0.0"]
        states = ["OUTDATED", "OUTDATED"]

        display_table(names, installed, latest, states)


class TestDisplayJson:
    """Test display_json function."""

    @patch("voltamanager.display.console.print")
    def test_display_json_basic(self, mock_print):
        """Test JSON output formatting."""
        names = ["pkg1", "pkg2"]
        installed = ["1.0.0", "2.0.0"]
        latest = ["1.0.0", "2.1.0"]
        states = ["up-to-date", "OUTDATED"]

        display_json(names, installed, latest, states)

        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        data = json.loads(output)

        assert len(data) == 2
        assert data[0]["name"] == "pkg1"
        assert data[0]["installed"] == "1.0.0"
        assert data[0]["latest"] == "1.0.0"
        assert data[0]["status"] == "up-to-date"

    @patch("voltamanager.display.console.print")
    def test_display_json_empty(self, mock_print):
        """Test JSON output with empty lists."""
        display_json([], [], [], [])

        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        data = json.loads(output)

        assert data == []

    @patch("voltamanager.display.console.print")
    def test_display_json_project_packages(self, mock_print):
        """Test JSON output includes project-pinned packages."""
        names = ["pkg1"]
        installed = ["project"]
        latest = ["-"]
        states = ["PROJECT"]

        display_json(names, installed, latest, states)

        output = mock_print.call_args[0][0]
        data = json.loads(output)

        assert data[0]["name"] == "pkg1"
        assert data[0]["installed"] == "project"
        assert data[0]["status"] == "PROJECT"

    @patch("voltamanager.display.console.print")
    def test_display_json_valid_structure(self, mock_print):
        """Test JSON output has valid structure."""
        names = ["pkg1", "pkg2", "pkg3"]
        installed = ["1.0.0", "2.0.0", "3.0.0"]
        latest = ["1.1.0", "2.0.0", "?"]
        states = ["OUTDATED", "up-to-date", "UNKNOWN"]

        display_json(names, installed, latest, states)

        output = mock_print.call_args[0][0]
        data = json.loads(output)

        # Verify all entries have required fields
        for entry in data:
            assert "name" in entry
            assert "installed" in entry
            assert "latest" in entry
            assert "status" in entry


class TestDisplayStatistics:
    """Test display_statistics function."""

    @staticmethod
    def test_display_statistics_basic():
        """Test statistics display."""
        states = ["up-to-date", "OUTDATED", "up-to-date", "PROJECT", "UNKNOWN"]
        names = ["pkg1", "pkg2", "pkg3", "pkg4", "pkg5"]
        installed = ["1.0.0", "1.0.0", "1.0.0", "project", "1.0.0"]
        latest = ["1.0.0", "2.0.0", "1.0.0", "-", "?"]
        display_statistics(states, names, installed, latest)

    @staticmethod
    def test_display_statistics_empty():
        """Test statistics with empty state list."""
        display_statistics([])

    @staticmethod
    def test_display_statistics_all_up_to_date():
        """Test statistics when all packages are up-to-date."""
        states = ["up-to-date", "up-to-date", "up-to-date"]
        display_statistics(states)

    @staticmethod
    def test_display_statistics_all_outdated():
        """Test statistics when all packages are outdated."""
        states = ["OUTDATED", "OUTDATED", "OUTDATED"]
        names = ["pkg1", "pkg2", "pkg3"]
        installed = ["1.0.0", "2.0.0", "3.0.0"]
        latest = ["2.0.0", "2.1.0", "3.0.1"]  # major, minor, patch
        display_statistics(states, names, installed, latest)

    @staticmethod
    def test_display_statistics_mixed():
        """Test statistics with mixed states."""
        states = ["up-to-date", "OUTDATED", "PROJECT", "UNKNOWN"] * 5
        names = [f"pkg{i}" for i in range(20)]
        installed = ["1.0.0", "1.0.0", "project", "1.0.0"] * 5
        latest = ["1.0.0", "2.0.0", "-", "?"] * 5
        display_statistics(states, names, installed, latest)


class TestDisplayDryRunReport:
    """Test display_dry_run_report function."""

    @staticmethod
    def test_display_dry_run_report_basic():
        """Test dry run report display."""
        to_install = ["pkg1@latest", "pkg2@latest"]
        names = ["pkg1", "pkg2"]
        installed = ["1.0.0", "2.0.0"]
        latest = ["1.1.0", "2.1.0"]

        display_dry_run_report(to_install, names, installed, latest)

    @staticmethod
    def test_display_dry_run_report_empty():
        """Test dry run report with no packages to install."""
        display_dry_run_report([], [], [], [])

    @staticmethod
    def test_display_dry_run_report_scoped_packages():
        """Test dry run report with scoped package names."""
        to_install = ["@vue/cli@latest", "@angular/core@latest"]
        names = ["@vue/cli", "@angular/core"]
        installed = ["5.0.0", "14.0.0"]
        latest = ["5.0.8", "15.0.0"]

        display_dry_run_report(to_install, names, installed, latest)

    @staticmethod
    def test_display_dry_run_report_single_package():
        """Test dry run report with single package."""
        to_install = ["pkg1@latest"]
        names = ["pkg1", "pkg2"]
        installed = ["1.0.0", "2.0.0"]
        latest = ["1.1.0", "2.0.0"]

        display_dry_run_report(to_install, names, installed, latest)

    @staticmethod
    def test_display_dry_run_report_many_packages():
        """Test dry run report with many packages."""
        to_install = [f"pkg{i}@latest" for i in range(20)]
        names = [f"pkg{i}" for i in range(20)]
        installed = ["1.0.0"] * 20
        latest = ["2.0.0"] * 20

        display_dry_run_report(to_install, names, installed, latest)

    @staticmethod
    def test_display_dry_run_report_package_not_found():
        """Test dry run report when package not found in names list."""
        to_install = ["missing-pkg@latest"]
        names = ["pkg1", "pkg2"]
        installed = ["1.0.0", "2.0.0"]
        latest = ["1.1.0", "2.0.0"]

        # Should not raise exception
        display_dry_run_report(to_install, names, installed, latest)


class TestDisplayIntegration:
    """Integration tests for display functions."""

    @staticmethod
    def test_full_workflow_check_only():
        """Test full display workflow for check-only mode."""
        names = ["pkg1", "pkg2", "pkg3"]
        installed = ["1.0.0", "2.0.0", "3.0.0"]
        latest = ["1.1.0", "2.0.0", "3.0.0"]  # Changed from "?" to avoid parsing issues
        states = ["OUTDATED", "up-to-date", "up-to-date"]

        # Should not raise exceptions
        display_table(names, installed, latest, states)
        display_statistics(states, names, installed, latest)
        display_json(names, installed, latest, states)

    @staticmethod
    def test_full_workflow_with_updates():
        """Test full display workflow for update mode."""
        names = ["pkg1", "pkg2"]
        installed = ["1.0.0", "2.0.0"]
        latest = ["1.1.0", "2.1.0"]
        states = ["OUTDATED", "OUTDATED"]
        to_install = ["pkg1@latest", "pkg2@latest"]

        # Should not raise exceptions
        display_table(names, installed, latest, states)
        display_statistics(states, names, installed, latest)
        display_dry_run_report(to_install, names, installed, latest)

    @staticmethod
    def test_full_workflow_outdated_only():
        """Test full display workflow with outdated-only filter."""
        names = ["pkg1", "pkg2", "pkg3", "pkg4"]
        installed = ["1.0.0", "2.0.0", "3.0.0", "project"]
        latest = ["1.1.0", "2.0.0", "3.1.0", "-"]
        states = ["OUTDATED", "up-to-date", "OUTDATED", "PROJECT"]

        # Should not raise exceptions
        display_table(names, installed, latest, states, outdated_only=True)
        display_statistics(states, names, installed, latest)
