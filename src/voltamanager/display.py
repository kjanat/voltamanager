"""Display formatting and output."""

import json
from typing import List

from rich.console import Console
from rich.table import Table

from .utils import is_major_update

console = Console()


def display_table(
    names: List[str],
    installed: List[str],
    latest: List[str],
    states: List[str],
    outdated_only: bool = False,
) -> None:
    """Display package status as a rich table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Package", style="cyan", width=42)
    table.add_column("Installed", style="blue", width=12)
    table.add_column("Latest", style="blue", width=12)
    table.add_column("Status", width=12)

    for i in range(len(names)):
        if outdated_only and states[i] not in ["OUTDATED", "UNKNOWN"]:
            continue

        status_style = ""
        if states[i] == "OUTDATED":
            status_style = "yellow"
        elif states[i] == "up-to-date":
            status_style = "green"
        elif states[i] == "PROJECT":
            status_style = "dim"

        status_text = states[i]
        if states[i] == "OUTDATED" and is_major_update(installed[i], latest[i]):
            status_text = f"{states[i]} ⚠"

        table.add_row(
            names[i],
            installed[i],
            latest[i],
            f"[{status_style}]{status_text}[/{status_style}]",
        )

    console.print(table)


def display_json(
    names: List[str], installed: List[str], latest: List[str], states: List[str]
) -> None:
    """Display package status as JSON."""
    result = [
        {
            "name": names[i],
            "installed": installed[i],
            "latest": latest[i],
            "status": states[i],
        }
        for i in range(len(names))
    ]
    console.print(json.dumps(result, indent=2))


def display_statistics(states: List[str]) -> None:
    """Display summary statistics."""
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Total packages: {len(states)}")
    console.print(f"  Up-to-date: {states.count('up-to-date')}")
    console.print(f"  Outdated: {states.count('OUTDATED')}")
    console.print(f"  Project-pinned: {states.count('PROJECT')}")
    console.print(f"  Unknown: {states.count('UNKNOWN')}")


def display_dry_run_report(
    to_install: List[str],
    names: List[str],
    installed: List[str],
    latest: List[str],
) -> None:
    """Display detailed dry-run report."""
    console.print("[cyan]Dry Run Report:[/cyan]")
    console.print(f"  Packages to update: {len(to_install)}")

    if to_install:
        table = Table(title="Planned Updates", show_header=True)
        table.add_column("Package", style="cyan")
        table.add_column("Current", style="yellow")
        table.add_column("Target", style="green")

        for pkg_spec in to_install:
            pkg_name = pkg_spec.rsplit("@", 1)[0]
            idx = names.index(pkg_name) if pkg_name in names else -1
            if idx >= 0:
                table.add_row(pkg_name, installed[idx], latest[idx])

        console.print(table)
