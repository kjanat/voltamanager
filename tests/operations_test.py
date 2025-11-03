"""Tests for operations module."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from voltamanager.config import Config
from voltamanager.operations import (
    check_and_update,
    fast_install,
    log_update,
    save_snapshot,
)


class TestLogUpdate:
    """Test log_update function."""

    def test_log_update_creates_history_file(self, tmp_path, monkeypatch):
        """Test that log_update creates history file if it doesn't exist."""
        history_dir = tmp_path / ".voltamanager"
        history_file = history_dir / "history.log"

        monkeypatch.setattr("voltamanager.operations.HISTORY_DIR", history_dir)
        monkeypatch.setattr("voltamanager.operations.HISTORY_FILE", history_file)

        packages = ["package1@1.0.0", "package2@2.0.0"]
        log_update(packages)

        assert history_file.exists()
        content = history_file.read_text(encoding="utf-8")
        assert "Updated 2 packages" in content
        assert "package1@1.0.0" in content

    def test_log_update_appends_to_existing(self, tmp_path, monkeypatch):
        """Test that log_update appends to existing history file."""
        history_dir = tmp_path / ".voltamanager"
        history_dir.mkdir(parents=True)
        history_file = history_dir / "history.log"
        history_file.write_text("Previous entry\n", encoding="utf-8")

        monkeypatch.setattr("voltamanager.operations.HISTORY_DIR", history_dir)
        monkeypatch.setattr("voltamanager.operations.HISTORY_FILE", history_file)

        log_update(["new-package@1.0.0"])

        content = history_file.read_text(encoding="utf-8")
        assert "Previous entry" in content
        assert "Updated 1 packages" in content


class TestSaveSnapshot:
    """Test save_snapshot function."""

    def test_save_snapshot_creates_file(self, tmp_path, monkeypatch):
        """Test that save_snapshot creates snapshot file."""
        history_dir = tmp_path / ".voltamanager"
        snapshot_file = history_dir / "last_snapshot.json"

        monkeypatch.setattr("voltamanager.operations.HISTORY_DIR", history_dir)
        monkeypatch.setattr("voltamanager.operations.SNAPSHOT_FILE", snapshot_file)

        packages = {"pkg1": "1.0.0", "pkg2": "2.0.0"}
        save_snapshot(packages)

        assert snapshot_file.exists()
        data = json.loads(snapshot_file.read_text(encoding="utf-8"))
        assert data == packages

    def test_save_snapshot_overwrites_existing(self, tmp_path, monkeypatch):
        """Test that save_snapshot overwrites existing snapshot."""
        history_dir = tmp_path / ".voltamanager"
        history_dir.mkdir(parents=True)
        snapshot_file = history_dir / "last_snapshot.json"
        snapshot_file.write_text('{"old": "1.0.0"}', encoding="utf-8")

        monkeypatch.setattr("voltamanager.operations.HISTORY_DIR", history_dir)
        monkeypatch.setattr("voltamanager.operations.SNAPSHOT_FILE", snapshot_file)

        new_packages = {"new": "2.0.0"}
        save_snapshot(new_packages)

        data = json.loads(snapshot_file.read_text(encoding="utf-8"))
        assert data == new_packages
        assert "old" not in data


class TestFastInstall:
    """Test fast_install function."""

    @staticmethod
    def test_fast_install_empty_list():
        """Test fast_install with empty package list."""
        result = fast_install([], Path("/tmp"), False)
        assert result == 0

    @patch("subprocess.run")
    def test_fast_install_success(self, mock_run, tmp_path):
        """Test successful fast install."""
        mock_run.return_value = Mock(returncode=0)
        packages = ["pkg1", "pkg2"]

        result = fast_install(packages, tmp_path, False)

        assert result == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0][:2] == ["volta", "install"]
        assert "pkg1" in call_args[0][0]
        assert "pkg2" in call_args[0][0]

    @patch("subprocess.run")
    def test_fast_install_dry_run(self, mock_run, tmp_path):
        """Test fast install in dry run mode."""
        packages = ["pkg1", "pkg2"]

        result = fast_install(packages, tmp_path, True)

        assert result == 0
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_fast_install_failure(self, mock_run, tmp_path):
        """Test fast install failure handling."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "volta")
        packages = ["pkg1"]

        result = fast_install(packages, tmp_path, False)

        assert result == 1


class TestCheckAndUpdate:
    """Test check_and_update function."""

    @patch("voltamanager.operations.get_latest_versions_parallel")
    @patch("voltamanager.operations.check_local_volta_config")
    def test_check_and_update_no_packages(
        self, mock_check_config, mock_get_versions, tmp_path
    ):
        """Test check_and_update with no packages."""
        mock_check_config.return_value = False
        mock_get_versions.return_value = {}
        config = Config()

        result = check_and_update(
            [],
            tmp_path,
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
        )

        assert result == 0

    @patch("voltamanager.operations.get_latest_versions_parallel")
    @patch("voltamanager.operations.check_local_volta_config")
    @patch("voltamanager.operations.display_table")
    def test_check_and_update_up_to_date(
        self, mock_display, mock_check_config, mock_get_versions, tmp_path
    ):
        """Test check_and_update when all packages are up-to-date."""
        mock_check_config.return_value = False
        mock_get_versions.return_value = {"pkg1": "1.0.0"}
        config = Config()

        result = check_and_update(
            ["pkg1@1.0.0"],
            tmp_path,
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
        )

        assert result == 0
        mock_display.assert_called_once()

    @patch("voltamanager.operations.get_latest_versions_parallel")
    @patch("voltamanager.operations.check_local_volta_config")
    @patch("voltamanager.operations.display_json")
    def test_check_and_update_json_output(
        self, mock_display_json, mock_check_config, mock_get_versions, tmp_path
    ):
        """Test check_and_update with JSON output."""
        mock_check_config.return_value = False
        mock_get_versions.return_value = {"pkg1": "2.0.0"}
        config = Config()

        result = check_and_update(
            ["pkg1@1.0.0"],
            tmp_path,
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
        )

        assert result == 0
        mock_display_json.assert_called_once()

    @patch("voltamanager.operations.get_latest_versions_parallel")
    @patch("voltamanager.operations.check_local_volta_config")
    @patch("subprocess.run")
    def test_check_and_update_with_updates(
        self, mock_run, mock_check_config, mock_get_versions, tmp_path
    ):
        """Test check_and_update with outdated packages and update flag."""
        mock_check_config.return_value = False
        mock_get_versions.return_value = {"pkg1": "2.0.0"}
        mock_run.return_value = Mock(returncode=0)
        config = Config()

        result = check_and_update(
            ["pkg1@1.0.0"],
            tmp_path,
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
        )

        assert result == 0
        mock_run.assert_called_once()

    @patch("voltamanager.operations.get_latest_versions_parallel")
    @patch("voltamanager.operations.check_local_volta_config")
    def test_check_and_update_project_packages(
        self, mock_check_config, mock_get_versions, tmp_path
    ):
        """Test check_and_update handles project-pinned packages."""
        mock_check_config.return_value = False
        mock_get_versions.return_value = {}
        config = Config()

        result = check_and_update(
            ["pkg1@project"],
            tmp_path,
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
        )

        assert result == 0

    @patch("voltamanager.operations.get_cached_version")
    @patch("voltamanager.operations.check_local_volta_config")
    def test_check_and_update_uses_cache(
        self, mock_check_config, mock_get_cached, tmp_path
    ):
        """Test check_and_update uses cache when enabled."""
        mock_check_config.return_value = False
        mock_get_cached.return_value = "1.0.0"
        config = Config()

        result = check_and_update(
            ["pkg1@1.0.0"],
            tmp_path,
            do_check=True,
            do_update=False,
            dry_run=False,
            include_project=False,
            json_output=False,
            outdated_only=False,
            interactive=False,
            use_cache=True,
            config=config,
            verbose=False,
        )

        assert result == 0
        mock_get_cached.assert_called_once_with("pkg1", 1)  # Include TTL param

    @patch("voltamanager.operations.get_latest_versions_parallel")
    @patch("voltamanager.operations.check_local_volta_config")
    @patch("typer.confirm")
    def test_check_and_update_interactive_cancelled(
        self, mock_confirm, mock_check_config, mock_get_versions, tmp_path
    ):
        """Test check_and_update interactive mode when user cancels."""
        mock_check_config.return_value = False
        mock_get_versions.return_value = {"pkg1": "2.0.0"}
        mock_confirm.return_value = False
        config = Config()

        result = check_and_update(
            ["pkg1@1.0.0"],
            tmp_path,
            do_check=True,
            do_update=True,
            dry_run=False,
            include_project=False,
            json_output=False,
            outdated_only=False,
            interactive=True,
            use_cache=False,
            config=config,
            verbose=False,
        )

        assert result == 0
        mock_confirm.assert_called_once()

    @patch("voltamanager.operations.get_latest_versions_parallel")
    @patch("voltamanager.operations.check_local_volta_config")
    def test_check_and_update_excluded_packages(
        self, mock_check_config, mock_get_versions, tmp_path, monkeypatch
    ):
        """Test check_and_update respects excluded packages."""
        mock_check_config.return_value = False
        mock_get_versions.return_value = {"regular-pkg": "1.0.0"}
        config = Config()
        config.exclude = ["excluded-pkg"]

        result = check_and_update(
            ["excluded-pkg@1.0.0", "regular-pkg@1.0.0"],
            tmp_path,
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
        )

        assert result == 0
        # Only regular-pkg should be checked
        if mock_get_versions.called:
            call_args = mock_get_versions.call_args[0][0]
            pkg_names = [name for name, _ in call_args]
            assert "excluded-pkg" not in pkg_names

    @patch("voltamanager.operations.get_latest_versions_parallel")
    @patch("voltamanager.operations.check_local_volta_config")
    def test_check_and_update_no_cache_explicit(
        self, mock_check_config, mock_get_versions, tmp_path
    ):
        """Test check_and_update with use_cache=False (no cache path)."""
        mock_check_config.return_value = False
        mock_get_versions.return_value = {"lodash": "4.17.21", "axios": "1.5.0"}
        config = Config()

        namevers = ["lodash@4.17.20", "axios@1.5.0"]

        result = check_and_update(
            namevers,
            tmp_path,
            do_check=True,
            do_update=False,
            dry_run=False,
            include_project=False,
            json_output=False,
            outdated_only=False,
            interactive=False,
            use_cache=False,  # Explicitly test no-cache path
            config=config,
            verbose=False,
        )

        assert result == 0
        assert mock_get_versions.called

    @patch("voltamanager.operations.get_latest_versions_parallel")
    @patch("voltamanager.operations.get_cached_version")
    @patch("voltamanager.operations.cache_version")
    @patch("voltamanager.operations.check_local_volta_config")
    def test_check_and_update_partial_cache(
        self,
        mock_check_config,
        mock_cache_version,
        mock_get_cached,
        mock_get_versions,
        tmp_path,
    ):
        """Test check_and_update with partial cache hits (uncached branch)."""
        mock_check_config.return_value = False

        # lodash is cached, axios is not
        def side_effect(pkg_name, ttl_hours=1):
            if pkg_name == "lodash":
                return "4.17.21"
            return None  # axios not cached

        mock_get_cached.side_effect = side_effect
        mock_get_versions.return_value = {"axios": "1.5.0"}
        config = Config()

        namevers = ["lodash@4.17.20", "axios@1.4.0"]

        result = check_and_update(
            namevers,
            tmp_path,
            do_check=True,
            do_update=False,
            dry_run=False,
            include_project=False,
            json_output=False,
            outdated_only=False,
            interactive=False,
            use_cache=True,  # Test partial cache path
            config=config,
            verbose=False,
        )

        assert result == 0
        # axios should be cached after fetch
        mock_cache_version.assert_called_once_with("axios", "1.5.0")
