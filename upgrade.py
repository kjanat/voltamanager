#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "argparse",
#     "pathlib",
#     "typing",
# ]
# ///

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional


def check_dependencies() -> bool:
    """Check if required commands are available."""
    if not shutil.which("volta"):
        print("volta not found in PATH", file=sys.stderr)
        return False
    if not shutil.which("npm"):
        print("npm not found (needed to query registry)", file=sys.stderr)
        return False
    return True


def get_installed_packages(safe_dir: Path) -> List[str]:
    """Get list of Volta-managed packages."""
    try:
        result = subprocess.run(
            ["volta", "list", "--format=plain"],
            cwd=safe_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        packages = []
        for line in result.stdout.splitlines():
            if line.startswith("package "):
                packages.append(line.split()[1])
        return packages
    except subprocess.CalledProcessError:
        return []


def parse_package(name_ver: str) -> Tuple[str, str]:
    """Parse package@version string into (name, version)."""
    if "@" not in name_ver:
        return name_ver, ""

    # Handle scoped packages like @vue/cli@5.0.8
    if name_ver.startswith("@"):
        parts = name_ver.rsplit("@", 1)
        return parts[0], parts[1] if len(parts) == 2 else ""

    parts = name_ver.split("@")
    return parts[0], parts[1] if len(parts) > 1 else ""


def get_latest_version(package_name: str, safe_dir: Path) -> Optional[str]:
    """Query npm registry for latest version of a package."""
    try:
        result = subprocess.run(
            ["npm", "view", package_name, "version"],
            cwd=safe_dir,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def fast_install(packages: List[str], safe_dir: Path, dry_run: bool) -> int:
    """Install packages without version checking."""
    if not packages:
        print("Nothing to install (only project-pinned found).")
        return 0

    if dry_run:
        print(f"Would install: {', '.join(packages)}")
        return 0

    try:
        subprocess.run(["volta", "install"] + packages, cwd=safe_dir, check=True)
        return 0
    except subprocess.CalledProcessError as e:
        return e.returncode


def check_and_update(
    namevers: List[str],
    safe_dir: Path,
    do_check: bool,
    do_update: bool,
    dry_run: bool,
    include_project: bool,
) -> int:
    """Check versions and optionally update packages."""

    names = []
    installed = []
    latest = []
    states = []
    to_install = []

    for name_ver in namevers:
        name, ver = parse_package(name_ver)

        if ver == "project":
            names.append(name)
            installed.append(ver)
            latest.append("-")
            states.append("PROJECT")
            if include_project:
                to_install.append(f"{name}@latest")
            continue

        lat = get_latest_version(name, safe_dir)

        if lat is None:
            lat = "?"
            st = "UNKNOWN"
        elif ver == lat:
            st = "up-to-date"
        else:
            st = "OUTDATED"
            to_install.append(f"{name}@latest")

        names.append(name)
        installed.append(ver)
        latest.append(lat)
        states.append(st)

    # Display check results
    if do_check:
        print(f"{'Package':<42}  {'Installed':<12}  {'Latest':<12}  Status")
        print(f"{'-' * 42}  {'-' * 12}  {'-' * 12}  ------")
        for i in range(len(names)):
            print(f"{names[i]:<42}  {installed[i]:<12}  {latest[i]:<12}  {states[i]}")

    # Perform updates
    if do_update:
        if not to_install:
            print("All packages are up to date.")
            return 0

        if dry_run:
            print(
                f"Would update ({len(to_install)} package(s)): {', '.join(to_install)}"
            )
            return 0

        print(f"Updating {len(to_install)} package(s)...")
        try:
            subprocess.run(["volta", "install"] + to_install, cwd=safe_dir, check=True)
            return 0
        except subprocess.CalledProcessError as e:
            return e.returncode

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Check and upgrade Volta-managed global packages"
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help="Skip version check and force update"
    )
    parser.add_argument(
        "-u", "--update", action="store_true", help="Update outdated packages"
    )
    parser.add_argument(
        "--dry", action="store_true", help="Show what would be done without doing it"
    )
    parser.add_argument(
        "--include-project", action="store_true", help="Include project-pinned packages"
    )

    args = parser.parse_args()

    # Determine behavior flags
    do_check = not args.force
    do_update = args.force or args.update

    # Check dependencies
    if not check_dependencies():
        return 127

    # Create safe temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        safe_dir = Path(tmpdir)

        # Get installed packages
        namevers = get_installed_packages(safe_dir)

        if not namevers:
            print("No Volta-managed packages found.")
            return 0

        # Fast path: install without version checks
        if not do_check and not do_update:
            packages = []
            for name_ver in namevers:
                name, ver = parse_package(name_ver)
                if ver == "project" and not args.include_project:
                    continue
                packages.append(name)

            # Remove duplicates and sort
            packages = sorted(set(packages))
            return fast_install(packages, safe_dir, args.dry)

        # Full check/update path
        return check_and_update(
            namevers, safe_dir, do_check, do_update, args.dry, args.include_project
        )


if __name__ == "__main__":
    sys.exit(main())
