"""Tests for security audit functionality."""

import json
import subprocess
from unittest.mock import MagicMock, patch

from voltamanager.security import (
    Vulnerability,
    check_package_vulnerabilities,
    display_audit_results,
    get_severity_color,
    parse_audit_results,
    run_npm_audit,
)


def test_run_npm_audit_success(tmp_path):
    """Test successful npm audit execution."""
    audit_data = {
        "metadata": {
            "vulnerabilities": {
                "critical": 1,
                "high": 2,
                "moderate": 3,
                "low": 0,
                "total": 6,
            }
        },
        "vulnerabilities": {},
    }

    with patch("voltamanager.security.subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(audit_data)
        mock_run.return_value = mock_result

        result = run_npm_audit(tmp_path, ["typescript", "eslint"])

        assert result is not None
        assert result["metadata"]["vulnerabilities"]["total"] == 6


def test_run_npm_audit_no_packages(tmp_path):
    """Test npm audit with empty package list."""
    result = run_npm_audit(tmp_path, [])
    assert result is None


def test_run_npm_audit_timeout(tmp_path):
    """Test npm audit when command times out."""
    with patch("voltamanager.security.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("npm audit", 20)

        result = run_npm_audit(tmp_path, ["typescript"])

        assert result is None


def test_run_npm_audit_command_fails(tmp_path):
    """Test npm audit when command fails."""
    with patch("voltamanager.security.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "npm audit")

        result = run_npm_audit(tmp_path, ["typescript"])

        assert result is None


def test_parse_audit_results_with_vulnerabilities():
    """Test parsing audit results with vulnerabilities."""
    audit_data = {
        "vulnerabilities": {
            "lodash": {
                "severity": "high",
                "via": [
                    {
                        "title": "Prototype Pollution",
                        "url": "https://npmjs.com/advisories/1234",
                    }
                ],
                "range": ">=4.0.0 <4.17.21",
            },
            "axios": {
                "severity": "critical",
                "via": [
                    {
                        "title": "Server-Side Request Forgery",
                        "url": "https://npmjs.com/advisories/5678",
                    }
                ],
                "range": ">=0.8.0 <0.21.2",
            },
        }
    }

    vulnerabilities = parse_audit_results(audit_data)

    assert len(vulnerabilities) == 2
    assert any(v.package == "lodash" for v in vulnerabilities)
    assert any(v.package == "axios" for v in vulnerabilities)

    lodash_vuln = next(v for v in vulnerabilities if v.package == "lodash")
    assert lodash_vuln.severity == "high"
    assert lodash_vuln.title == "Prototype Pollution"
    assert lodash_vuln.url == "https://npmjs.com/advisories/1234"


def test_parse_audit_results_empty():
    """Test parsing empty audit results."""
    audit_data = {"vulnerabilities": {}}

    vulnerabilities = parse_audit_results(audit_data)

    assert len(vulnerabilities) == 0


def test_parse_audit_results_no_via_details():
    """Test parsing audit results without via details."""
    audit_data = {
        "vulnerabilities": {
            "test-pkg": {
                "severity": "moderate",
                "via": [],
                "range": "*",
            }
        }
    }

    vulnerabilities = parse_audit_results(audit_data)

    assert len(vulnerabilities) == 1
    assert vulnerabilities[0].package == "test-pkg"
    assert vulnerabilities[0].title
    assert vulnerabilities[0].url


def test_get_severity_color():
    """Test severity color mapping."""
    assert get_severity_color("critical") == "red bold"
    assert get_severity_color("high") == "red"
    assert get_severity_color("moderate") == "yellow"
    assert get_severity_color("low") == "blue"
    assert get_severity_color("unknown") == "dim"
    assert get_severity_color("CRITICAL") == "red bold"  # case insensitive


def test_display_audit_results_no_vulnerabilities(capsys):
    """Test displaying audit results with no vulnerabilities."""
    audit_data = {"metadata": {"vulnerabilities": {"total": 0}}}

    display_audit_results(audit_data, verbose=False)
    captured = capsys.readouterr()

    assert "No vulnerabilities found" in captured.out


def test_display_audit_results_with_vulnerabilities(capsys):
    """Test displaying audit results with vulnerabilities."""
    audit_data = {
        "metadata": {
            "vulnerabilities": {
                "critical": 2,
                "high": 3,
                "moderate": 5,
                "low": 1,
                "total": 11,
            }
        }
    }

    display_audit_results(audit_data, verbose=False)
    captured = capsys.readouterr()

    assert "Security Audit Summary" in captured.out
    assert "Critical" in captured.out
    assert "High" in captured.out
    assert "Moderate" in captured.out
    assert "Low" in captured.out


def test_display_audit_results_verbose(capsys):
    """Test displaying detailed audit results in verbose mode."""
    audit_data = {
        "metadata": {
            "vulnerabilities": {
                "critical": 1,
                "high": 0,
                "moderate": 0,
                "low": 0,
                "total": 1,
            }
        },
        "vulnerabilities": {
            "test-package": {
                "severity": "critical",
                "via": [
                    {"title": "Remote Code Execution", "url": "https://example.com"}
                ],
                "range": "*",
            }
        },
    }

    display_audit_results(audit_data, verbose=True)
    captured = capsys.readouterr()

    assert "Detailed Vulnerabilities" in captured.out
    assert "test-package" in captured.out
    assert "CRITICAL" in captured.out


def test_display_audit_results_high_severity_warning(capsys):
    """Test warning message for high-severity vulnerabilities."""
    audit_data = {
        "metadata": {
            "vulnerabilities": {
                "critical": 1,
                "high": 0,
                "moderate": 0,
                "low": 0,
                "total": 1,
            }
        }
    }

    display_audit_results(audit_data, verbose=False)
    captured = capsys.readouterr()

    assert "High-severity vulnerabilities detected" in captured.out


def test_check_package_vulnerabilities_success(tmp_path, capsys):
    """Test checking packages for vulnerabilities."""
    audit_data = {
        "metadata": {
            "vulnerabilities": {
                "critical": 0,
                "high": 1,
                "moderate": 0,
                "low": 0,
                "total": 1,
            }
        }
    }

    with patch("voltamanager.security.run_npm_audit") as mock_audit:
        mock_audit.return_value = audit_data

        has_critical, result = check_package_vulnerabilities(
            ["typescript"], tmp_path, verbose=False
        )

        assert has_critical is False
        assert result is not None
        captured = capsys.readouterr()
        assert "Running security audit" in captured.out


def test_check_package_vulnerabilities_critical(tmp_path, capsys):
    """Test checking packages with critical vulnerabilities."""
    audit_data = {
        "metadata": {
            "vulnerabilities": {
                "critical": 2,
                "high": 0,
                "moderate": 0,
                "low": 0,
                "total": 2,
            }
        }
    }

    with patch("voltamanager.security.run_npm_audit") as mock_audit:
        mock_audit.return_value = audit_data

        has_critical, result = check_package_vulnerabilities(
            ["vulnerable-package"], tmp_path, verbose=False
        )

        assert has_critical is True
        assert result is not None


def test_check_package_vulnerabilities_audit_fails(tmp_path, capsys):
    """Test checking packages when audit fails."""
    with patch("voltamanager.security.run_npm_audit") as mock_audit:
        mock_audit.return_value = None

        has_critical, result = check_package_vulnerabilities(
            ["typescript"], tmp_path, verbose=False
        )

        assert has_critical is False
        assert result is None
        captured = capsys.readouterr()
        assert "Unable to run security audit" in captured.out


def test_vulnerability_dataclass():
    """Test Vulnerability dataclass creation."""
    vuln = Vulnerability(
        severity="high",
        package="test-pkg",
        via="dependency",
        title="Test Vulnerability",
        url="https://example.com",
        range=">=1.0.0",
    )

    assert vuln.severity == "high"
    assert vuln.package == "test-pkg"
    assert vuln.title == "Test Vulnerability"
    assert vuln.url == "https://example.com"
