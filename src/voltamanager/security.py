"""Security vulnerability checking via npm audit."""

import subprocess
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class Vulnerability:
    """Represents a security vulnerability."""

    severity: str
    package: str
    via: str
    title: str
    url: str
    range: str


def run_npm_audit(safe_dir: Path, packages: list[str]) -> dict[str, Any] | None:
    """Run npm audit on specified packages.

    Args:
        safe_dir: Safe temporary directory to run npm commands
        packages: List of package names to audit

    Returns:
        Dictionary containing audit results, or None if audit fails
    """
    if not packages:
        return None

    try:
        # Create temporary package.json with packages as dependencies
        package_json = safe_dir / "package.json"
        package_data = {
            "name": "volta-manager-audit",
            "version": "1.0.0",
            "dependencies": {pkg: "latest" for pkg in packages},
        }
        package_json.write_text(json.dumps(package_data, indent=2))

        # Run npm install to populate node_modules
        subprocess.run(
            ["npm", "install", "--package-lock-only"],
            cwd=safe_dir,
            capture_output=True,
            check=True,
            timeout=30,
        )

        # Run npm audit
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=safe_dir,
            capture_output=True,
            text=True,
            timeout=20,
        )

        # npm audit returns non-zero if vulnerabilities found, but that's expected
        if result.stdout:
            return json.loads(result.stdout)

        return None

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
    ):
        return None


def parse_audit_results(audit_data: dict) -> list[Vulnerability]:
    """Parse npm audit JSON output into Vulnerability objects.

    Args:
        audit_data: Raw npm audit JSON data

    Returns:
        List of Vulnerability objects
    """
    vulnerabilities = []

    # npm audit v7+ format
    if "vulnerabilities" in audit_data:
        vulns = audit_data["vulnerabilities"]
        for pkg_name, vuln_data in vulns.items():
            if isinstance(vuln_data, dict):
                severity = vuln_data.get("severity", "unknown")
                via = vuln_data.get("via", [])
                title = ""
                url = ""
                range_info = vuln_data.get("range", "")

                # Extract details from 'via' field
                if isinstance(via, list) and via:
                    first_via = via[0]
                    if isinstance(first_via, dict):
                        title = first_via.get("title", "")
                        url = first_via.get("url", "")

                vulnerabilities.append(
                    Vulnerability(
                        severity=severity,
                        package=pkg_name,
                        via=str(via) if via else "",
                        title=title,
                        url=url,
                        range=range_info,
                    )
                )

    return vulnerabilities


def get_severity_color(severity: str) -> str:
    """Get Rich color string for severity level.

    Args:
        severity: Severity level (critical, high, moderate, low)

    Returns:
        Rich color string
    """
    severity_lower = severity.lower()
    if severity_lower == "critical":
        return "red bold"
    elif severity_lower == "high":
        return "red"
    elif severity_lower == "moderate":
        return "yellow"
    elif severity_lower == "low":
        return "blue"
    else:
        return "dim"


def display_audit_results(audit_data: dict, verbose: bool = False) -> None:
    """Display audit results in formatted tables.

    Args:
        audit_data: npm audit JSON data
        verbose: Show detailed vulnerability information
    """
    metadata = audit_data.get("metadata", {})
    vulnerabilities_count = metadata.get("vulnerabilities", {})

    # Summary statistics
    console.print("\n[bold]Security Audit Summary:[/bold]")
    total = vulnerabilities_count.get("total", 0)

    if total == 0:
        console.print("[green]✓ No vulnerabilities found[/green]")
        return

    # Show counts by severity
    table = Table(show_header=True)
    table.add_column("Severity", style="cyan")
    table.add_column("Count", justify="right")

    critical = vulnerabilities_count.get("critical", 0)
    high = vulnerabilities_count.get("high", 0)
    moderate = vulnerabilities_count.get("moderate", 0)
    low = vulnerabilities_count.get("low", 0)

    if critical > 0:
        table.add_row("[red bold]Critical[/red bold]", str(critical))
    if high > 0:
        table.add_row("[red]High[/red]", str(high))
    if moderate > 0:
        table.add_row("[yellow]Moderate[/yellow]", str(moderate))
    if low > 0:
        table.add_row("[blue]Low[/blue]", str(low))

    console.print(table)

    # Show detailed vulnerabilities if verbose
    if verbose:
        vulns = parse_audit_results(audit_data)
        if vulns:
            console.print("\n[bold]Detailed Vulnerabilities:[/bold]")
            detail_table = Table(show_header=True)
            detail_table.add_column("Package", style="cyan")
            detail_table.add_column("Severity")
            detail_table.add_column("Title", max_width=60)

            for vuln in vulns[:20]:  # Show first 20
                severity_style = get_severity_color(vuln.severity)
                detail_table.add_row(
                    vuln.package,
                    f"[{severity_style}]{vuln.severity.upper()}[/{severity_style}]",
                    vuln.title or "(No title)",
                )

            console.print(detail_table)

            if len(vulns) > 20:
                console.print(
                    f"\n[dim]...and {len(vulns) - 20} more vulnerabilities[/dim]"
                )

    # Show recommendation
    if critical > 0 or high > 0:
        console.print("\n[yellow]⚠ High-severity vulnerabilities detected![/yellow]")
        console.print(
            "[yellow]💡 Review and update affected packages as soon as possible[/yellow]"
        )


def check_package_vulnerabilities(
    packages: list[str], safe_dir: Path, verbose: bool = False
) -> tuple[bool, dict[str, Any] | None]:
    """Check packages for known security vulnerabilities.

    Args:
        packages: List of package names to check
        safe_dir: Safe temporary directory for npm operations
        verbose: Show detailed vulnerability information

    Returns:
        Tuple of (has_critical_vulns, audit_data)
    """
    console.print("[cyan]Running security audit...[/cyan]")

    audit_data = run_npm_audit(safe_dir, packages)

    if audit_data is None:
        console.print("[yellow]⚠ Unable to run security audit[/yellow]")
        return False, None

    display_audit_results(audit_data, verbose)

    # Check if there are critical vulnerabilities
    metadata = audit_data.get("metadata", {})
    vulnerabilities_count = metadata.get("vulnerabilities", {})
    critical = vulnerabilities_count.get("critical", 0)

    return critical > 0, audit_data
