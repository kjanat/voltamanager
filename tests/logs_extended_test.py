"""Extended tests for logs command new features."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from voltamanager import app


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_log_file(tmp_path):
    """Create a sample log file for testing."""
    log_file = tmp_path / "test.log"
    log_content = """2024-01-01 10:00:00 - INFO - Application started
2024-01-01 10:01:00 - INFO - Checking 5 packages
2024-01-01 10:02:00 - WARNING - Package typescript is outdated
2024-01-01 10:03:00 - ERROR - Failed to update package react
2024-01-01 10:04:00 - INFO - Updated 3 packages successfully
2024-01-01 10:05:00 - INFO - Operation completed
2024-01-01 10:06:00 - INFO - Cache cleared
2024-01-01 10:07:00 - WARNING - High memory usage detected
2024-01-01 10:08:00 - INFO - Benchmark completed
2024-01-01 10:09:00 - ERROR - Network timeout occurred
2024-01-01 10:10:00 - INFO - Rollback initiated
2024-01-01 10:11:00 - INFO - Rollback completed
2024-01-01 10:12:00 - INFO - Configuration updated
2024-01-01 10:13:00 - WARNING - Deprecated feature used
2024-01-01 10:14:00 - INFO - Snapshot saved
2024-01-01 10:15:00 - INFO - Version check completed
2024-01-01 10:16:00 - ERROR - Permission denied
2024-01-01 10:17:00 - INFO - Cache miss for package vue
2024-01-01 10:18:00 - WARNING - Slow network detected
2024-01-01 10:19:00 - INFO - Application shutdown"""
    log_file.write_text(log_content, encoding="utf-8")
    return log_file


class TestLogsTailOption:
    """Test logs --tail option."""

    def test_tail_default(self, runner, sample_log_file):
        """Test default tail shows last 20 lines."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs"])
            assert result.exit_code == 0
            # Default is 20 lines, file has 20 lines, so all should show
            assert "Application started" in result.stdout
            assert "Application shutdown" in result.stdout

    def test_tail_custom_small(self, runner, sample_log_file):
        """Test custom tail with small count."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs", "--tail", "3"])
            assert result.exit_code == 0
            # Should only show last 3 lines
            assert "Application shutdown" in result.stdout
            assert "Slow network detected" in result.stdout
            assert "Cache miss" in result.stdout
            # Should not show early lines
            assert "Application started" not in result.stdout

    def test_tail_custom_large(self, runner, sample_log_file):
        """Test custom tail with large count."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs", "--tail", "100"])
            assert result.exit_code == 0
            # Should show all lines (file has 20 lines)
            assert "Application started" in result.stdout
            assert "Application shutdown" in result.stdout

    def test_tail_zero(self, runner, sample_log_file):
        """Test tail with zero shows all lines."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs", "--tail", "0"])
            assert result.exit_code == 0
            # tail=0 should show everything
            assert "Application started" in result.stdout
            assert "Application shutdown" in result.stdout

    def test_tail_shorthand(self, runner, sample_log_file):
        """Test tail shorthand -n option."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs", "-n", "5"])
            assert result.exit_code == 0
            assert "Application shutdown" in result.stdout


class TestLogsSearchOption:
    """Test logs --search option."""

    def test_search_error_only(self, runner, sample_log_file):
        """Test search for ERROR messages."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs", "--search", "ERROR"])
            assert result.exit_code == 0
            assert "Failed to update package react" in result.stdout
            assert "Network timeout occurred" in result.stdout
            assert "Permission denied" in result.stdout
            # Should not show INFO or WARNING
            assert "Application started" not in result.stdout

    def test_search_warning_only(self, runner, sample_log_file):
        """Test search for WARNING messages."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs", "--search", "WARNING"])
            assert result.exit_code == 0
            assert "typescript is outdated" in result.stdout
            assert "High memory usage" in result.stdout
            assert "Slow network detected" in result.stdout

    def test_search_case_insensitive(self, runner, sample_log_file):
        """Test search is case insensitive."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result1 = runner.invoke(app, ["logs", "--search", "error"])
            result2 = runner.invoke(app, ["logs", "--search", "ERROR"])
            # Both should find the same ERROR entries
            assert "Failed to update package react" in result1.stdout
            assert "Failed to update package react" in result2.stdout
            assert "Network timeout occurred" in result1.stdout
            assert "Network timeout occurred" in result2.stdout

    def test_search_specific_text(self, runner, sample_log_file):
        """Test search for specific text."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs", "--search", "package"])
            assert result.exit_code == 0
            assert "Checking 5 packages" in result.stdout
            assert "typescript is outdated" in result.stdout
            assert "Failed to update package react" in result.stdout

    def test_search_no_matches(self, runner, sample_log_file):
        """Test search with no matches."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs", "--search", "nonexistent"])
            assert result.exit_code == 0
            assert "No matching log entries found" in result.stdout

    def test_search_shorthand(self, runner, sample_log_file):
        """Test search shorthand -s option."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            result = runner.invoke(app, ["logs", "-s", "ERROR"])
            assert result.exit_code == 0
            assert "ERROR" in result.stdout


class TestLogsClearOption:
    """Test logs --clear option."""

    def test_clear_with_confirmation(self, runner, tmp_path):
        """Test clear with user confirmation."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Some log content", encoding="utf-8")

        with patch("voltamanager.logger.LOG_FILE", log_file):
            result = runner.invoke(app, ["logs", "--clear"], input="y\n")
            assert result.exit_code == 0
            assert "Logs cleared" in result.stdout
            assert not log_file.exists()

    def test_clear_cancelled(self, runner, tmp_path):
        """Test clear cancelled by user."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Some log content", encoding="utf-8")

        with patch("voltamanager.logger.LOG_FILE", log_file):
            result = runner.invoke(app, ["logs", "--clear"], input="n\n")
            assert result.exit_code == 0
            assert "Clear cancelled" in result.stdout
            assert log_file.exists()  # File still exists

    def test_clear_no_log_file(self, runner, tmp_path):
        """Test clear when no log file exists."""
        log_file = tmp_path / "nonexistent.log"

        with patch("voltamanager.logger.LOG_FILE", log_file):
            result = runner.invoke(app, ["logs", "--clear"], input="y\n")
            assert result.exit_code == 0
            assert "No log file to clear" in result.stdout

    def test_clear_confirmation_prompt(self, runner, tmp_path):
        """Test that clear shows confirmation prompt."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Some log content", encoding="utf-8")

        with patch("voltamanager.logger.LOG_FILE", log_file):
            result = runner.invoke(app, ["logs", "--clear"], input="n\n")
            assert "Are you sure" in result.stdout


class TestLogsColorCoding:
    """Test log color coding."""

    def test_color_coding_levels(self, runner, tmp_path):
        """Test that different log levels are color coded."""
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2024-01-01 - INFO - Info message\n"
            "2024-01-01 - ERROR - Error message\n"
            "2024-01-01 - WARNING - Warning message\n"
            "2024-01-01 - DEBUG - Debug message\n",
            encoding="utf-8",
        )

        with patch("voltamanager.logger.LOG_FILE", log_file):
            result = runner.invoke(app, ["logs"])
            assert result.exit_code == 0
            # Verify all message types are present
            assert "Info message" in result.stdout
            assert "Error message" in result.stdout
            assert "Warning message" in result.stdout
            assert "Debug message" in result.stdout

    def test_color_coding_error_distinct(self, runner, tmp_path):
        """Test ERROR messages have distinct formatting."""
        log_file = tmp_path / "test.log"
        log_file.write_text("2024-01-01 - ERROR - Critical failure\n", encoding="utf-8")

        with patch("voltamanager.logger.LOG_FILE", log_file):
            result = runner.invoke(app, ["logs"])
            assert result.exit_code == 0
            assert "Critical failure" in result.stdout


class TestLogsCombinedOptions:
    """Test combining multiple logs options."""

    def test_tail_and_search_combined(self, runner, sample_log_file):
        """Test using --tail and --search together."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            # Search for ERROR, then tail to 2 results
            result = runner.invoke(app, ["logs", "--search", "ERROR", "--tail", "2"])
            assert result.exit_code == 0
            # Should show last 2 ERROR matches
            assert "ERROR" in result.stdout

    def test_stats_overrides_tail(self, runner, sample_log_file):
        """Test that --stats mode doesn't show log lines."""
        with patch("voltamanager.logger.LOG_FILE", sample_log_file):
            with patch("voltamanager.logger.get_log_stats") as mock_stats:
                mock_stats.return_value = {
                    "total_lines": 20,
                    "operations": {"update": 3},
                    "errors": 3,
                    "updates": 3,
                }
                result = runner.invoke(app, ["logs", "--stats", "--tail", "5"])
                assert result.exit_code == 0
                assert "Log Statistics" in result.stdout


class TestLogsEdgeCases:
    """Test edge cases for logs command."""

    def test_empty_log_file(self, runner, tmp_path):
        """Test with empty log file."""
        log_file = tmp_path / "empty.log"
        log_file.write_text("", encoding="utf-8")

        with patch("voltamanager.logger.LOG_FILE", log_file):
            result = runner.invoke(app, ["logs"])
            assert result.exit_code == 0

    def test_single_line_log(self, runner, tmp_path):
        """Test with single line log file."""
        log_file = tmp_path / "single.log"
        log_file.write_text("2024-01-01 - INFO - Single entry", encoding="utf-8")

        with patch("voltamanager.logger.LOG_FILE", log_file):
            result = runner.invoke(app, ["logs", "--tail", "10"])
            assert result.exit_code == 0
            assert "Single entry" in result.stdout

    def test_very_long_lines(self, runner, tmp_path):
        """Test with very long log lines."""
        log_file = tmp_path / "long.log"
        long_line = "2024-01-01 - INFO - " + "x" * 1000
        log_file.write_text(long_line, encoding="utf-8")

        with patch("voltamanager.logger.LOG_FILE", log_file):
            result = runner.invoke(app, ["logs"])
            assert result.exit_code == 0
