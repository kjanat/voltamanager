"""Structured logging system for voltamanager."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict


class LogStats(TypedDict):
    """Type definition for log statistics."""

    total_lines: int
    operations: dict[str, int]
    errors: int
    updates: int


# Configure logging directory
LOG_DIR = Path.home() / ".voltamanager"
LOG_FILE = LOG_DIR / "voltamanager.log"


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        # Base format
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        level = record.levelname
        message = record.getMessage()

        # Add structured fields if present
        extras = []
        if hasattr(record, "package"):
            extras.append(f"package={record.package}")
        if hasattr(record, "version"):
            extras.append(f"version={record.version}")
        if hasattr(record, "operation"):
            extras.append(f"operation={record.operation}")
        if hasattr(record, "count"):
            extras.append(f"count={record.count}")

        extra_str = f" [{', '.join(extras)}]" if extras else ""
        return f"{timestamp} {level:8} {message}{extra_str}"


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Set up the logger with file and optional console output.

    Args:
        verbose: If True, also log to console

    Returns:
        Configured logger instance

    """
    # Create logger
    logger = logging.getLogger("voltamanager")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers.clear()

    # Create log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)

    # Console handler (only if verbose)
    if verbose:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(console_handler)

    return logger


def log_operation(logger: logging.Logger, operation: str, **kwargs: Any) -> None:
    """Log an operation with structured data.

    Args:
        logger: Logger instance
        operation: Operation name (e.g., 'check', 'update', 'install')
        **kwargs: Additional structured data (package, version, count, etc.)

    """
    logger.info(f"Operation: {operation}", extra={"operation": operation, **kwargs})


def log_package_update(
    logger: logging.Logger, package: str, old_version: str, new_version: str
) -> None:
    """Log a package update.

    Args:
        logger: Logger instance
        package: Package name
        old_version: Previous version
        new_version: New version

    """
    logger.info(
        f"Updated {package}: {old_version} → {new_version}",
        extra={
            "operation": "update",
            "package": package,
            "old_version": old_version,
            "new_version": new_version,
        },
    )


def log_error(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log an error with structured data.

    Args:
        logger: Logger instance
        message: Error message
        **kwargs: Additional context

    """
    logger.error(message, extra=kwargs)


def get_log_stats() -> LogStats:
    """Get statistics from the log file.

    Returns:
        Dictionary with log statistics

    """
    if not LOG_FILE.exists():
        return {"total_lines": 0, "operations": {}, "errors": 0, "updates": 0}

    stats: LogStats = {
        "total_lines": 0,
        "operations": {},
        "errors": 0,
        "updates": 0,
    }

    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            stats["total_lines"] += 1
            if " ERROR " in line:
                stats["errors"] += 1
            if "Operation: update" in line:
                stats["updates"] += 1
            if "Operation:" in line:
                # Extract operation type
                try:
                    op = line.split("Operation: ")[1].split()[0]
                    stats["operations"][op] = stats["operations"].get(op, 0) + 1
                except IndexError:
                    pass

    return stats
