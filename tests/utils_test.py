"""Tests for utility functions."""

import json


from voltamanager.utils import (
    is_major_update,
    get_major_updates,
    check_local_volta_config,
)


class TestVersionComparison:
    """Tests for version comparison utilities."""

    def test_is_major_update_true(self) -> None:
        """Test detection of major version updates."""
        assert is_major_update("1.0.0", "2.0.0") is True
        assert is_major_update("2.5.3", "3.0.0") is True
        assert is_major_update("0.9.9", "1.0.0") is True

    def test_is_major_update_false(self) -> None:
        """Test non-major version updates."""
        assert is_major_update("1.0.0", "1.1.0") is False
        assert is_major_update("1.0.0", "1.0.1") is False
        assert is_major_update("2.5.3", "2.6.0") is False

    def test_is_major_update_same_version(self) -> None:
        """Test same version comparison."""
        assert is_major_update("1.0.0", "1.0.0") is False
        assert is_major_update("2.5.3", "2.5.3") is False

    def test_is_major_update_downgrade(self) -> None:
        """Test downgrade detection (higher to lower major version)."""
        assert is_major_update("2.0.0", "1.0.0") is False

    def test_is_major_update_invalid_versions(self) -> None:
        """Test handling of invalid version strings."""
        assert is_major_update("invalid", "1.0.0") is False
        assert is_major_update("1.0.0", "invalid") is False
        assert is_major_update("not.a.version", "also.not.valid") is False

    def test_is_major_update_prerelease(self) -> None:
        """Test handling of prerelease versions."""
        assert is_major_update("1.0.0", "2.0.0-beta.1") is True
        assert is_major_update("1.0.0-alpha", "1.0.0") is False

    def test_get_major_updates_empty(self) -> None:
        """Test with no packages."""
        result = get_major_updates([], [], [], [])
        assert result == []

    def test_get_major_updates_none_outdated(self) -> None:
        """Test with all packages up-to-date."""
        names = ["lodash", "axios"]
        installed = ["4.17.21", "1.4.0"]
        latest = ["4.17.21", "1.4.0"]
        states = ["up-to-date", "up-to-date"]

        result = get_major_updates(names, installed, latest, states)
        assert result == []

    def test_get_major_updates_minor_only(self) -> None:
        """Test with only minor/patch updates."""
        names = ["lodash", "axios"]
        installed = ["4.17.20", "1.3.0"]
        latest = ["4.17.21", "1.4.0"]
        states = ["OUTDATED", "OUTDATED"]

        result = get_major_updates(names, installed, latest, states)
        assert result == []

    def test_get_major_updates_with_major(self) -> None:
        """Test detection of major version updates."""
        names = ["react", "vue", "lodash"]
        installed = ["17.0.2", "2.6.14", "4.17.20"]
        latest = ["18.0.0", "3.0.0", "4.17.21"]
        states = ["OUTDATED", "OUTDATED", "OUTDATED"]

        result = get_major_updates(names, installed, latest, states)

        assert len(result) == 2
        assert ("react", "17.0.2", "18.0.0") in result
        assert ("vue", "2.6.14", "3.0.0") in result
        assert ("lodash", "4.17.20", "4.17.21") not in result

    def test_get_major_updates_with_unknown(self) -> None:
        """Test handling of unknown versions."""
        names = ["react", "unknown-pkg"]
        installed = ["17.0.2", "1.0.0"]
        latest = ["18.0.0", "?"]
        states = ["OUTDATED", "UNKNOWN"]

        result = get_major_updates(names, installed, latest, states)

        assert len(result) == 1
        assert ("react", "17.0.2", "18.0.0") in result

    def test_get_major_updates_with_project(self) -> None:
        """Test handling of project-pinned packages."""
        names = ["react", "local-package"]
        installed = ["17.0.2", "project"]
        latest = ["18.0.0", "-"]
        states = ["OUTDATED", "PROJECT"]

        result = get_major_updates(names, installed, latest, states)

        assert len(result) == 1
        assert ("react", "17.0.2", "18.0.0") in result


class TestVoltaConfigCheck:
    """Tests for local volta configuration checking."""

    def test_no_package_json(self, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Test when no package.json exists."""
        monkeypatch.chdir(tmp_path)
        result = check_local_volta_config()
        assert result is False

    def test_package_json_without_volta(self, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Test package.json without volta configuration."""
        monkeypatch.chdir(tmp_path)
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({"name": "test-app", "version": "1.0.0"}))

        result = check_local_volta_config()
        assert result is False

    def test_package_json_with_volta(self, tmp_path, monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
        """Test package.json with volta configuration."""
        monkeypatch.chdir(tmp_path)
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps({
                "name": "test-app",
                "version": "1.0.0",
                "volta": {"node": "18.0.0", "npm": "9.0.0"},
            })
        )

        result = check_local_volta_config()
        assert result is True

        captured = capsys.readouterr()
        assert "Local volta config detected" in captured.out

    def test_package_json_with_volta_verbose(  # type: ignore[no-untyped-def]
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        """Test verbose output with volta configuration."""
        monkeypatch.chdir(tmp_path)
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps({
                "name": "test-app",
                "volta": {
                    "node": "18.0.0",
                    "npm": "9.0.0",
                    "yarn": "1.22.0",
                },
            })
        )

        result = check_local_volta_config(verbose=True)
        assert result is True

        captured = capsys.readouterr()
        assert "Node: 18.0.0" in captured.out
        assert "npm: 9.0.0" in captured.out
        assert "Yarn: 1.22.0" in captured.out

    def test_invalid_package_json(self, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Test handling of invalid JSON in package.json."""
        monkeypatch.chdir(tmp_path)
        package_json = tmp_path / "package.json"
        package_json.write_text("{invalid json}")

        result = check_local_volta_config()
        assert result is False
