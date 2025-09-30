"""Integration tests for CLI commands."""

import json
from pathlib import Path
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from voltamanager import app

runner = CliRunner()


class TestMainCommandIntegration:
    """Integration tests for main command with actual CLI invocation."""

    @patch("voltamanager.check_dependencies")
    @patch("voltamanager.get_installed_packages")
    def test_main_help(self, mock_get_installed: Mock, mock_check_deps: Mock):
        """Test main command help."""
        result = runner.invoke(app, ["main", "--help"])
        assert result.exit_code == 0
        assert "Check and upgrade" in result.stdout

    @patch("voltamanager.check_dependencies")
    @patch("voltamanager.get_installed_packages")
    @patch("voltamanager.check_and_update")
    def test_main_basic_invocation(
        self, mock_check_update: Mock, mock_get_installed: Mock, mock_check_deps: Mock
    ):
        """Test basic main command invocation."""
        mock_check_deps.return_value = True
        mock_get_installed.return_value = ["typescript@5.0.0"]
        mock_check_update.return_value = None

        result = runner.invoke(app, ["main"])
        assert result.exit_code == 0

    @patch("voltamanager.check_dependencies")
    def test_main_missing_dependencies(self, mock_check_deps: Mock):
        """Test main command with missing dependencies."""
        mock_check_deps.return_value = False

        result = runner.invoke(app, ["main"])
        assert result.exit_code == 127

    @patch("voltamanager.check_dependencies")
    @patch("voltamanager.check_and_update")
    def test_main_with_flags(self, mock_check_update: Mock, mock_check_deps: Mock):
        """Test main command with various flags."""
        mock_check_deps.return_value = True
        mock_check_update.return_value = None

        # Test update flag
        result = runner.invoke(app, ["main", "--update"])
        assert result.exit_code == 0

        # Test dry run flag
        result = runner.invoke(app, ["main", "--dry"])
        assert result.exit_code == 0

        # Test json flag
        result = runner.invoke(app, ["main", "--json"])
        assert result.exit_code == 0

        # Test verbose flag
        result = runner.invoke(app, ["main", "--verbose"])
        assert result.exit_code == 0


class TestConfigCommandIntegration:
    """Integration tests for config command."""

    def test_config_help(self):
        """Test config command help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0

    @patch("voltamanager.create_default_config")
    def test_config_execution(self, mock_create: Mock):
        """Test config command creates default config."""
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        mock_create.assert_called_once()
        assert "Created default config" in result.stdout


class TestClearCacheCommandIntegration:
    """Integration tests for clear-cache command."""

    def test_clear_cache_help(self):
        """Test clear-cache command help."""
        result = runner.invoke(app, ["clear-cache", "--help"])
        assert result.exit_code == 0

    @patch("voltamanager.clear_cache")
    def test_clear_cache_execution(self, mock_clear: Mock):
        """Test clear-cache command execution."""
        result = runner.invoke(app, ["clear-cache"])
        assert result.exit_code == 0
        mock_clear.assert_called_once()


class TestLogsCommandIntegration:
    """Integration tests for logs command."""

    def test_logs_help(self):
        """Test logs command help."""
        result = runner.invoke(app, ["logs", "--help"])
        assert result.exit_code == 0

    @patch("voltamanager.logger.LOG_FILE")
    def test_logs_no_history(self, mock_log: Mock):
        """Test logs command with no history."""
        mock_log.exists.return_value = False
        result = runner.invoke(app, ["logs"])
        assert result.exit_code == 0

    @patch("voltamanager.logger.LOG_FILE")
    def test_logs_with_stats(self, mock_log: Mock):
        """Test logs command with stats option."""
        mock_log.exists.return_value = True
        result = runner.invoke(app, ["logs", "--stats"])
        assert result.exit_code == 0


class TestRollbackCommandIntegration:
    """Integration tests for rollback command."""

    def test_rollback_help(self):
        """Test rollback command help."""
        result = runner.invoke(app, ["rollback", "--help"])
        assert result.exit_code == 0
        assert "Rollback" in result.stdout

    def test_rollback_no_snapshot_real(self, tmp_path: Path):
        """Test rollback with no snapshot (real filesystem)."""
        # Temporarily change home to tmp_path
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = runner.invoke(app, ["rollback"])
            assert result.exit_code == 1
            assert "No snapshot" in result.stdout

    def test_rollback_cancelled(self, tmp_path: Path):
        """Test rollback when user cancels."""
        # Create a fake snapshot
        snapshot_dir = tmp_path / ".voltamanager"
        snapshot_dir.mkdir()
        snapshot_file = snapshot_dir / "last_snapshot.json"  # Correct filename
        snapshot_file.write_text(json.dumps({"typescript": "4.9.5"}))

        with patch("pathlib.Path.home", return_value=tmp_path):
            result = runner.invoke(app, ["rollback"], input="n\n")
            assert result.exit_code == 0
            assert "cancelled" in result.stdout.lower()

    def test_rollback_with_force(self, tmp_path: Path):
        """Test rollback with force flag."""
        # Create a fake snapshot
        snapshot_dir = tmp_path / ".voltamanager"
        snapshot_dir.mkdir()
        snapshot_file = snapshot_dir / "last_snapshot.json"  # Correct filename
        snapshot_file.write_text(json.dumps({"typescript": "4.9.5", "eslint": "8.0.0"}))

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch("subprocess.run") as mock_subprocess:
                mock_subprocess.return_value = Mock(returncode=0)
                result = runner.invoke(app, ["rollback", "--force"])
                assert result.exit_code == 0
                assert mock_subprocess.called
