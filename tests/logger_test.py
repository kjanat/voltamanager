"""Tests for logger module."""

import logging


from voltamanager.logger import (
    StructuredFormatter,
    setup_logger,
    log_operation,
    log_package_update,
    log_error,
    get_log_stats,
)


class TestStructuredFormatter:
    """Test StructuredFormatter."""

    def test_format_basic_message(self):
        """Format a basic log message without extras."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "INFO" in result
        assert "Test message" in result
        assert "[" not in result  # No extras

    def test_format_with_package(self):
        """Format message with package attribute."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.package = "test-package"
        result = formatter.format(record)
        assert "package=test-package" in result

    def test_format_with_version(self):
        """Format message with version attribute."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.version = "1.0.0"
        result = formatter.format(record)
        assert "version=1.0.0" in result

    def test_format_with_operation(self):
        """Format message with operation attribute."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.operation = "check"
        result = formatter.format(record)
        assert "operation=check" in result

    def test_format_with_count(self):
        """Format message with count attribute."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.count = 42
        result = formatter.format(record)
        assert "count=42" in result

    def test_format_with_all_extras(self):
        """Format message with all extra attributes."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.package = "test-pkg"
        record.version = "2.0.0"
        record.operation = "update"
        record.count = 5
        result = formatter.format(record)
        assert "package=test-pkg" in result
        assert "version=2.0.0" in result
        assert "operation=update" in result
        assert "count=5" in result


class TestSetupLogger:
    """Test setup_logger function."""

    def test_setup_logger_basic(self, tmp_path, monkeypatch):
        """Test basic logger setup."""
        log_dir = tmp_path / ".voltamanager"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr(
            "voltamanager.logger.LOG_FILE", log_dir / "voltamanager.log"
        )

        logger = setup_logger(verbose=False)

        assert logger.name == "voltamanager"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1  # File handler only
        assert log_dir.exists()

    def test_setup_logger_verbose(self, tmp_path, monkeypatch):
        """Test logger setup with verbose mode."""
        log_dir = tmp_path / ".voltamanager"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr(
            "voltamanager.logger.LOG_FILE", log_dir / "voltamanager.log"
        )

        logger = setup_logger(verbose=True)

        assert logger.name == "voltamanager"
        assert len(logger.handlers) == 2  # File + console handler
        assert log_dir.exists()

    def test_setup_logger_creates_directory(self, tmp_path, monkeypatch):
        """Test that setup_logger creates log directory if it doesn't exist."""
        log_dir = tmp_path / "nonexistent" / ".voltamanager"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr(
            "voltamanager.logger.LOG_FILE", log_dir / "voltamanager.log"
        )

        assert not log_dir.exists()
        setup_logger()
        assert log_dir.exists()

    def test_setup_logger_clears_existing_handlers(self, tmp_path, monkeypatch):
        """Test that setup_logger clears existing handlers."""
        log_dir = tmp_path / ".voltamanager"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr(
            "voltamanager.logger.LOG_FILE", log_dir / "voltamanager.log"
        )

        # Setup logger twice
        logger1 = setup_logger()
        logger2 = setup_logger()

        # Should have exactly 1 handler after second setup
        assert len(logger2.handlers) == 1
        assert logger1 is logger2  # Same logger instance


class TestLogOperation:
    """Test log_operation function."""

    def test_log_operation_basic(self, tmp_path, monkeypatch):
        """Test basic operation logging."""
        log_dir = tmp_path / ".voltamanager"
        log_file = log_dir / "voltamanager.log"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        logger = setup_logger()
        log_operation(logger, "test_operation")

        log_content = log_file.read_text()
        assert "test_operation" in log_content
        assert "operation=test_operation" in log_content

    def test_log_operation_with_kwargs(self, tmp_path, monkeypatch):
        """Test operation logging with additional kwargs."""
        log_dir = tmp_path / ".voltamanager"
        log_file = log_dir / "voltamanager.log"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        logger = setup_logger()
        log_operation(logger, "check", count=5, package="test-pkg")

        log_content = log_file.read_text()
        assert "check" in log_content
        assert "count=5" in log_content
        assert "package=test-pkg" in log_content


class TestLogPackageUpdate:
    """Test log_package_update function."""

    def test_log_package_update(self, tmp_path, monkeypatch):
        """Test package update logging."""
        log_dir = tmp_path / ".voltamanager"
        log_file = log_dir / "voltamanager.log"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        logger = setup_logger()
        log_package_update(logger, "lodash", "4.17.20", "4.17.21")

        log_content = log_file.read_text()
        assert "lodash" in log_content
        assert "4.17.20" in log_content
        assert "4.17.21" in log_content
        assert "→" in log_content

    def test_log_package_update_with_scoped_package(self, tmp_path, monkeypatch):
        """Test package update logging with scoped package."""
        log_dir = tmp_path / ".voltamanager"
        log_file = log_dir / "voltamanager.log"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        logger = setup_logger()
        log_package_update(logger, "@vue/cli", "5.0.0", "5.0.8")

        log_content = log_file.read_text()
        assert "@vue/cli" in log_content
        assert "5.0.0" in log_content
        assert "5.0.8" in log_content


class TestLogError:
    """Test log_error function."""

    def test_log_error_basic(self, tmp_path, monkeypatch):
        """Test basic error logging."""
        log_dir = tmp_path / ".voltamanager"
        log_file = log_dir / "voltamanager.log"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        logger = setup_logger()
        log_error(logger, "Test error message")

        log_content = log_file.read_text()
        assert "ERROR" in log_content
        assert "Test error message" in log_content

    def test_log_error_with_kwargs(self, tmp_path, monkeypatch):
        """Test error logging with context kwargs."""
        log_dir = tmp_path / ".voltamanager"
        log_file = log_dir / "voltamanager.log"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        logger = setup_logger()
        log_error(logger, "Failed operation", package="test-pkg", count=3)

        log_content = log_file.read_text()
        assert "ERROR" in log_content
        assert "Failed operation" in log_content
        assert "package=test-pkg" in log_content
        assert "count=3" in log_content


class TestGetLogStats:
    """Test get_log_stats function."""

    def test_get_log_stats_no_file(self, tmp_path, monkeypatch):
        """Test get_log_stats when log file doesn't exist."""
        log_file = tmp_path / "nonexistent.log"
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        stats = get_log_stats()

        assert stats["total_lines"] == 0
        assert stats["operations"] == {}
        assert stats["errors"] == 0

    def test_get_log_stats_empty_file(self, tmp_path, monkeypatch):
        """Test get_log_stats with empty log file."""
        log_file = tmp_path / "empty.log"
        log_file.touch()
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        stats = get_log_stats()

        assert stats["total_lines"] == 0
        assert stats["operations"] == {}
        assert stats["errors"] == 0

    def test_get_log_stats_with_operations(self, tmp_path, monkeypatch):
        """Test get_log_stats with various operations."""
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2025-09-30T10:00:00 INFO     Operation: check\n"
            "2025-09-30T10:01:00 INFO     Operation: update\n"
            "2025-09-30T10:02:00 INFO     Operation: update\n"
            "2025-09-30T10:03:00 ERROR    Failed to install\n"
        )
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        stats = get_log_stats()

        assert stats["total_lines"] == 4
        assert stats["operations"]["check"] == 1
        assert stats["operations"]["update"] == 2
        assert stats["errors"] == 1
        assert stats["updates"] == 2

    def test_get_log_stats_malformed_lines(self, tmp_path, monkeypatch):
        """Test get_log_stats with malformed log lines."""
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "2025-09-30T10:00:00 INFO     Operation:\n"  # Malformed
            "Random text without structure\n"
            "2025-09-30T10:01:00 INFO     Operation: check\n"
        )
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        stats = get_log_stats()

        assert stats["total_lines"] == 3
        assert stats["operations"]["check"] == 1
        assert stats["errors"] == 0


class TestLoggerIntegration:
    """Integration tests for logger module."""

    def test_full_logging_workflow(self, tmp_path, monkeypatch):
        """Test complete logging workflow."""
        log_dir = tmp_path / ".voltamanager"
        log_file = log_dir / "voltamanager.log"
        monkeypatch.setattr("voltamanager.logger.LOG_DIR", log_dir)
        monkeypatch.setattr("voltamanager.logger.LOG_FILE", log_file)

        # Setup logger and perform operations
        logger = setup_logger()
        log_operation(logger, "check", count=5)
        log_package_update(logger, "lodash", "4.17.20", "4.17.21")
        log_error(logger, "Test error")

        # Verify log file
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Operation: check" in log_content
        assert "lodash" in log_content
        assert "ERROR" in log_content

        # Get stats
        stats = get_log_stats()
        assert stats["total_lines"] == 3
        assert stats["operations"]["check"] == 1
        assert stats["errors"] == 1
