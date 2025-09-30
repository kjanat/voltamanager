"""Configuration management."""

import tomllib
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "voltamanager"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = {
    "voltamanager": {
        "exclude": [],
        "include_project": False,
        "cache_ttl_hours": 1,
        "parallel_checks": 10,
    }
}


class Config:
    """Configuration for voltamanager."""

    def __init__(self) -> None:
        self.exclude: list[str] = []
        self.include_project: bool = False
        self.cache_ttl_hours: int = 1
        self.parallel_checks: int = 10
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if not CONFIG_FILE.exists():
            self._apply_defaults()
            return

        try:
            with open(CONFIG_FILE, "rb") as f:
                config_data = tomllib.load(f)
                vm_config: dict[str, object] = config_data.get("voltamanager", {})
                exclude = vm_config.get("exclude", [])
                include_project = vm_config.get("include_project", False)
                cache_ttl = vm_config.get("cache_ttl_hours", 1)
                parallel = vm_config.get("parallel_checks", 10)

                if isinstance(exclude, list):
                    self.exclude = [str(x) for x in exclude if isinstance(x, str)]
                if isinstance(include_project, bool):
                    self.include_project = include_project
                if isinstance(cache_ttl, int):
                    self.cache_ttl_hours = cache_ttl
                if isinstance(parallel, int):
                    self.parallel_checks = parallel
        except Exception:
            self._apply_defaults()

    def _apply_defaults(self) -> None:
        """Apply default configuration."""
        vm_config: dict[str, object] = DEFAULT_CONFIG["voltamanager"]
        exclude = vm_config["exclude"]
        include_project = vm_config["include_project"]
        cache_ttl = vm_config["cache_ttl_hours"]
        parallel = vm_config["parallel_checks"]

        if isinstance(exclude, list):
            self.exclude = [str(x) for x in exclude]
        if isinstance(include_project, bool):
            self.include_project = include_project
        if isinstance(cache_ttl, int):
            self.cache_ttl_hours = cache_ttl
        if isinstance(parallel, int):
            self.parallel_checks = parallel

    def should_exclude(self, package_name: str) -> bool:
        """Check if a package should be excluded from operations."""
        return package_name in self.exclude


def create_default_config() -> None:
    """Create a default configuration file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(
            """[voltamanager]
# Packages to exclude from all operations
exclude = []

# Include project-pinned packages by default
include_project = false

# Cache time-to-live in hours
cache_ttl_hours = 1

# Number of parallel npm registry checks
parallel_checks = 10
"""
        )
