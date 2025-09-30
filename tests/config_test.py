"""Tests for config module."""

from pathlib import Path

import pytest

from voltamanager.config import (
    Config,
    create_default_config,
)


@pytest.fixture
def mock_config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mock CONFIG_FILE and CONFIG_DIR to use tmp_path."""
    config_dir = tmp_path / "voltamanager_config"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr("voltamanager.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("voltamanager.config.CONFIG_FILE", config_file)
    return config_file


class TestConfig:
    """Test Config class."""

    def test_default_config(self, mock_config_file: Path) -> None:
        """Test config with defaults when no file exists."""
        config = Config()

        assert config.exclude == []
        assert config.include_project is False
        assert config.cache_ttl_hours == 1
        assert config.parallel_checks == 10

    def test_load_valid_config(self, mock_config_file: Path) -> None:
        """Test loading valid configuration file."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
[voltamanager]
exclude = ["npm", "@vue/cli"]
include_project = true
cache_ttl_hours = 24
parallel_checks = 5
""")

        config = Config()

        assert config.exclude == ["npm", "@vue/cli"]
        assert config.include_project is True
        assert config.cache_ttl_hours == 24
        assert config.parallel_checks == 5

    def test_load_partial_config(self, mock_config_file: Path) -> None:
        """Test loading config with only some values set."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
[voltamanager]
exclude = ["npm"]
cache_ttl_hours = 12
""")

        config = Config()

        assert config.exclude == ["npm"]
        assert config.include_project is False  # Default
        assert config.cache_ttl_hours == 12
        assert config.parallel_checks == 10  # Default

    def test_load_empty_voltamanager_section(self, mock_config_file: Path) -> None:
        """Test loading config with empty voltamanager section."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("[voltamanager]\n")

        config = Config()

        assert config.exclude == []
        assert config.include_project is False
        assert config.cache_ttl_hours == 1
        assert config.parallel_checks == 10

    def test_load_missing_voltamanager_section(self, mock_config_file: Path) -> None:
        """Test loading config without voltamanager section."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("[other_section]\nvalue = 1\n")

        config = Config()

        # Should use defaults
        assert config.exclude == []
        assert config.include_project is False

    def test_load_invalid_toml(self, mock_config_file: Path) -> None:
        """Test handling invalid TOML syntax."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("not valid toml [[[")

        config = Config()

        # Should fall back to defaults
        assert config.exclude == []
        assert config.include_project is False

    def test_load_invalid_type_exclude(self, mock_config_file: Path) -> None:
        """Test handling invalid type for exclude (not a list)."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
[voltamanager]
exclude = "npm"
""")

        config = Config()

        # Should ignore invalid value and use default
        assert config.exclude == []

    def test_load_invalid_type_include_project(self, mock_config_file: Path) -> None:
        """Test handling invalid type for include_project (not a bool)."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
[voltamanager]
include_project = "yes"
""")

        config = Config()

        # Should ignore invalid value and use default
        assert config.include_project is False

    def test_load_invalid_type_cache_ttl(self, mock_config_file: Path) -> None:
        """Test handling invalid type for cache_ttl_hours (not an int)."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
[voltamanager]
cache_ttl_hours = "24"
""")

        config = Config()

        # Should ignore invalid value and use default
        assert config.cache_ttl_hours == 1

    def test_load_invalid_type_parallel(self, mock_config_file: Path) -> None:
        """Test handling invalid type for parallel_checks (not an int)."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
[voltamanager]
parallel_checks = 5.5
""")

        config = Config()

        # Should ignore invalid value and use default
        assert config.parallel_checks == 10

    def test_exclude_list_with_non_strings(self, mock_config_file: Path) -> None:
        """Test handling exclude list with non-string values."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
[voltamanager]
exclude = ["npm", 123, "@vue/cli", true]
""")

        config = Config()

        # Should filter out non-string values
        assert config.exclude == ["npm", "@vue/cli"]

    def test_should_exclude_included_package(self, mock_config_file: Path) -> None:
        """Test should_exclude with package in exclude list."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
[voltamanager]
exclude = ["npm", "@vue/cli"]
""")

        config = Config()

        assert config.should_exclude("npm") is True
        assert config.should_exclude("@vue/cli") is True

    def test_should_exclude_not_included_package(self, mock_config_file: Path) -> None:
        """Test should_exclude with package not in exclude list."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
[voltamanager]
exclude = ["npm"]
""")

        config = Config()

        assert config.should_exclude("lodash") is False
        assert config.should_exclude("eslint") is False

    def test_should_exclude_empty_exclude_list(self, mock_config_file: Path) -> None:
        """Test should_exclude with empty exclude list."""
        config = Config()

        assert config.should_exclude("npm") is False
        assert config.should_exclude("lodash") is False


class TestCreateDefaultConfig:
    """Test create_default_config function."""

    def test_create_default_config_new_file(self, mock_config_file: Path) -> None:
        """Test creating default config when file doesn't exist."""
        assert not mock_config_file.exists()

        create_default_config()

        assert mock_config_file.exists()
        content = mock_config_file.read_text()

        # Verify content includes all expected sections
        assert "[voltamanager]" in content
        assert "exclude = []" in content
        assert "include_project = false" in content
        assert "cache_ttl_hours = 1" in content
        assert "parallel_checks = 10" in content

    def test_create_default_config_existing_file(self, mock_config_file: Path) -> None:
        """Test that create_default_config doesn't overwrite existing file."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        original_content = """
[voltamanager]
exclude = ["custom"]
cache_ttl_hours = 999
"""
        mock_config_file.write_text(original_content)

        create_default_config()

        # Should not overwrite
        assert mock_config_file.read_text() == original_content

    def test_create_default_config_creates_directory(
        self, mock_config_file: Path
    ) -> None:
        """Test that create_default_config creates config directory if needed."""
        assert not mock_config_file.parent.exists()

        create_default_config()

        assert mock_config_file.parent.exists()
        assert mock_config_file.exists()

    def test_default_config_is_valid_toml(self, mock_config_file: Path) -> None:
        """Test that created default config is valid TOML."""
        import tomllib

        create_default_config()

        # Should be parseable as TOML
        with open(mock_config_file, "rb") as f:
            data = tomllib.load(f)

        assert "voltamanager" in data
        assert isinstance(data["voltamanager"]["exclude"], list)
        assert isinstance(data["voltamanager"]["include_project"], bool)
        assert isinstance(data["voltamanager"]["cache_ttl_hours"], int)
        assert isinstance(data["voltamanager"]["parallel_checks"], int)


class TestConfigIntegration:
    """Integration tests for Config class."""

    def test_config_reload_with_changes(self, mock_config_file: Path) -> None:
        """Test that reloading config picks up changes."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)

        # Initial config
        mock_config_file.write_text("""
[voltamanager]
exclude = ["npm"]
cache_ttl_hours = 12
""")

        config1 = Config()
        assert config1.exclude == ["npm"]
        assert config1.cache_ttl_hours == 12

        # Update config file
        mock_config_file.write_text("""
[voltamanager]
exclude = ["npm", "yarn"]
cache_ttl_hours = 24
""")

        config2 = Config()
        assert config2.exclude == ["npm", "yarn"]
        assert config2.cache_ttl_hours == 24

    def test_config_with_comments(self, mock_config_file: Path) -> None:
        """Test that config handles comments correctly."""
        mock_config_file.parent.mkdir(parents=True, exist_ok=True)
        mock_config_file.write_text("""
# VoltaManager Configuration
[voltamanager]

# Packages to never update
exclude = ["npm", "@vue/cli"]  # Critical packages

# Project settings
include_project = true  # Include project-pinned packages

# Cache duration in hours
cache_ttl_hours = 24

# Parallel execution limit
parallel_checks = 15
""")

        config = Config()

        assert config.exclude == ["npm", "@vue/cli"]
        assert config.include_project is True
        assert config.cache_ttl_hours == 24
        assert config.parallel_checks == 15
