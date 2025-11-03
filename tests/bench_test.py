"""Tests for the bench command."""

import pytest
from typer.testing import CliRunner

from voltamanager import app


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


class TestBenchCommand:
    """Test bench command functionality."""

    def test_bench_help(self, runner):
        """Test bench command help."""
        result = runner.invoke(app, ["bench", "--help"])
        assert result.exit_code == 0
        assert "Benchmark npm registry query performance" in result.stdout
        assert "--packages" in result.stdout

    def test_bench_basic_execution(self, runner):
        """Test bench command runs successfully."""
        # Use very small package count for faster test
        result = runner.invoke(app, ["bench", "--packages", "2"])
        assert result.exit_code == 0
        assert "Running performance benchmark" in result.stdout
        assert "Results:" in result.stdout

    def test_bench_shows_table_structure(self, runner):
        """Test bench shows proper table structure."""
        result = runner.invoke(app, ["bench", "--packages", "2"])
        assert result.exit_code == 0
        # Check table columns
        assert "Method" in result.stdout
        assert "Time" in result.stdout
        assert "Speedup" in result.stdout
        # Check methods listed
        assert "Sequential" in result.stdout
        assert "workers" in result.stdout

    def test_bench_shows_recommendation(self, runner):
        """Test that bench shows recommendation."""
        result = runner.invoke(app, ["bench", "--packages", "2"])
        assert result.exit_code == 0
        assert "Recommendation" in result.stdout or "parallel" in result.stdout.lower()

    def test_bench_custom_package_count(self, runner):
        """Test bench with custom package count."""
        result = runner.invoke(app, ["bench", "--packages", "3"])
        assert result.exit_code == 0
        assert "Tested with 3 packages" in result.stdout

    def test_bench_shorthand_flag(self, runner):
        """Test bench with shorthand -p flag."""
        result = runner.invoke(app, ["bench", "-p", "2"])
        assert result.exit_code == 0
        assert "Tested with 2 packages" in result.stdout


class TestBenchIntegration:
    """Integration tests for bench command."""

    def test_bench_full_workflow(self, runner):
        """Test complete bench workflow."""
        result = runner.invoke(app, ["bench", "-p", "2"])
        assert result.exit_code == 0

        # Verify all phases executed
        assert "Sequential queries" in result.stdout
        assert "Parallel queries (10 workers)" in result.stdout
        assert "Parallel queries (20 workers)" in result.stdout
        assert "Results:" in result.stdout

    def test_bench_shows_phases(self, runner):
        """Test that bench shows all benchmark phases."""
        result = runner.invoke(app, ["bench", "--packages", "2"])
        assert result.exit_code == 0
        # Check that all phases are mentioned
        assert "Sequential" in result.stdout
        assert "Parallel" in result.stdout

    def test_bench_shows_speedup_calculation(self, runner):
        """Test that bench shows speedup calculations."""
        result = runner.invoke(app, ["bench", "--packages", "2"])
        assert result.exit_code == 0
        # Baseline should be 1.00x
        assert "1.00x" in result.stdout or "1.0x" in result.stdout
        # Should have speedup multipliers
        assert "x" in result.stdout
