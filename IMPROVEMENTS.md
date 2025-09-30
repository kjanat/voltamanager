# VoltaManager CLI Improvements

Proposed enhancements to improve functionality, performance, and user experience.

______________________________________________________________________

## 🚀 High Priority Improvements

### 1. Parallel Version Checking

**Problem**: Checking versions sequentially is slow with many packages
**Solution**: Use `asyncio` or `concurrent.futures` to query npm registry in parallel

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_and_update(...):
    # Parallel version checking
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_package = {
            executor.submit(get_latest_version, name, safe_dir): name
            for name, ver in packages if ver != "project"
        }
        for future in as_completed(future_to_package):
            name = future_to_package[future]
            latest[name] = future.result()
```

**Impact**: 5-10x faster for 10+ packages

______________________________________________________________________

### 2. Progress Indicators

**Problem**: No feedback during long operations
**Solution**: Use Rich's `Progress` for version checks and updates

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console,
) as progress:
    task = progress.add_task(
        f"Checking {len(packages)} packages...", total=len(packages)
    )
    for pkg in packages:
        # check version
        progress.advance(task)
```

**Impact**: Better UX, especially for 10+ packages

______________________________________________________________________

### 3. Output Filtering Options

**Problem**: Can't filter status table to show only outdated packages
**Solution**: Add `--outdated-only` flag

```python
@app.command()
def main(
    outdated_only: bool = typer.Option(
        False, "--outdated-only", help="Show only outdated packages"
    ),
    ...
):
    # In display logic
    if outdated_only and states[i] not in ["OUTDATED", "UNKNOWN"]:
        continue
```

**Impact**: Cleaner output for large package lists

______________________________________________________________________

### 4. JSON Output Mode

**Problem**: Not scriptable - output is human-readable only
**Solution**: Add `--json` flag for machine-readable output

```python
import json

json_mode: bool = typer.Option(False, "--json", help="Output in JSON format")

if json_mode:
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
```

**Impact**: Enables automation and integration with other tools

______________________________________________________________________

## ⚡ Performance Improvements

### 5. Cache NPM Registry Responses

**Problem**: Repeated runs re-query npm for same packages
**Solution**: Cache results in `~/.cache/voltamanager/` with TTL

```python
from pathlib import Path
import json
from datetime import datetime, timedelta

CACHE_DIR = Path.home() / ".cache" / "voltamanager"
CACHE_TTL = timedelta(hours=1)


def get_cached_version(package_name: str) -> Optional[str]:
    cache_file = CACHE_DIR / f"{package_name.replace('/', '_')}.json"
    if cache_file.exists():
        data = json.loads(cache_file.read_text())
        cached_time = datetime.fromisoformat(data["timestamp"])
        if datetime.now() - cached_time < CACHE_TTL:
            return data["version"]
    return None


def cache_version(package_name: str, version: str):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{package_name.replace('/', '_')}.json"
    cache_file.write_text(
        json.dumps({"version": version, "timestamp": datetime.now().isoformat()})
    )
```

**Impact**: Much faster repeated checks within cache window

______________________________________________________________________

### 6. Batch NPM Queries

**Problem**: Individual `npm view` calls have overhead
**Solution**: Use `npm view` with multiple packages at once (if supported)

**Research needed**: Check if `npm view` supports batch queries efficiently

______________________________________________________________________

## 🎯 User Experience Improvements

### 7. Verbose and Quiet Modes

**Problem**: No control over output verbosity
**Solution**: Add `-v/--verbose` and `-q/--quiet` flags

```python
verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output")

# In verbose mode, show npm query results, timing info
if verbose:
    console.print(f"[dim]Querying npm for {package_name}...[/dim]")

# In quiet mode, suppress table output unless --update used
if quiet and not do_update:
    return 0
```

______________________________________________________________________

### 8. Interactive Update Selection

**Problem**: All-or-nothing updates - can't choose which to update
**Solution**: Add `--interactive` mode using `typer.confirm()`

```python
interactive: bool = typer.Option(
    False, "--interactive", "-i", help="Interactively choose packages to update"
)

if interactive and to_install:
    selected = []
    for pkg in to_install:
        if typer.confirm(f"Update {pkg}?"):
            selected.append(pkg)
    to_install = selected
```

______________________________________________________________________

### 9. Configuration File Support

**Problem**: Can't persistently exclude packages or set preferences
**Solution**: Load config from `~/.config/voltamanager/config.toml`

```toml
# ~/.config/voltamanager/config.toml
[voltamanager]
exclude = ["@vue/cli", "npm"]  # Never update these
include_project = false
cache_ttl_hours = 24
parallel_checks = 10
```

______________________________________________________________________

### 10. Better Error Messages

**Problem**: Generic errors don't help troubleshooting
**Solution**: Specific error messages with suggestions

```python
if not shutil.which("volta"):
    console.print("[red]✗ volta not found in PATH[/red]", file=sys.stderr)
    console.print("[yellow]→ Install volta: https://volta.sh[/yellow]", file=sys.stderr)
    console.print("[yellow]→ Or add volta to PATH[/yellow]", file=sys.stderr)
    return False
```

______________________________________________________________________

## 🧪 Testing & Quality

### 11. Unit Tests

**Priority**: Add comprehensive test suite

```python
# tests/test_parse_package.py
def test_parse_regular_package():
    assert parse_package("lodash@4.17.21") == ("lodash", "4.17.21")


def test_parse_scoped_package():
    assert parse_package("@vue/cli@5.0.8") == ("@vue/cli", "5.0.8")


def test_parse_no_version():
    assert parse_package("lodash") == ("lodash", "")


# tests/test_integration.py - requires mocking subprocess
```

**Tools**: pytest, pytest-mock, pytest-cov

______________________________________________________________________

### 12. Type Checking

**Current**: Type hints exist but not enforced
**Solution**: Add mypy or pyright to pre-commit

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.11.1
  hooks:
    - id: mypy
      additional_dependencies: [types-all]
```

______________________________________________________________________

## 🔒 Safety & Reliability

### 13. Rollback Capability

**Problem**: No way to undo updates if something breaks
**Solution**: Save state before updates, provide rollback command

```python
@app.command()
def rollback():
    """Rollback to previous package versions"""
    snapshot_file = Path.home() / ".voltamanager" / "last_snapshot.json"
    if not snapshot_file.exists():
        console.print("[red]No snapshot found[/red]")
        raise typer.Exit(1)

    snapshot = json.loads(snapshot_file.read_text())
    packages = [f"{name}@{ver}" for name, ver in snapshot.items()]
    subprocess.run(["volta", "install"] + packages, check=True)
```

______________________________________________________________________

### 14. Dry Run Improvements

**Current**: Dry run shows what would install but not side effects
**Solution**: Show complete dry-run report

```python
if dry_run:
    console.print("[cyan]Dry Run Report:[/cyan]")
    console.print(f"  Packages to update: {len(to_install)}")
    table = Table(title="Planned Updates")
    table.add_column("Package", style="cyan")
    table.add_column("Current", style="yellow")
    table.add_column("Target", style="green")
    # ... populate table
    console.print(table)
```

______________________________________________________________________

### 15. Check for Volta Hooks

**Problem**: Some packages may have Volta pin conflicts
**Solution**: Detect and warn about local volta config conflicts

```python
def check_local_volta_config():
    """Warn if local package.json has volta config"""
    if Path("package.json").exists():
        with open("package.json") as f:
            data = json.load(f)
            if "volta" in data:
                console.print(
                    "[yellow]⚠ Local volta config detected in package.json[/yellow]"
                )
                console.print(
                    "[yellow]  This may affect global package management[/yellow]"
                )
```

______________________________________________________________________

## 📊 Additional Features

### 16. Statistics and Reporting

Show summary statistics after operations

```python
# After check
console.print("\n[bold]Summary:[/bold]")
console.print(f"  Total packages: {len(names)}")
console.print(f"  Up-to-date: {states.count('up-to-date')}")
console.print(f"  Outdated: {states.count('OUTDATED')}")
console.print(f"  Project-pinned: {states.count('PROJECT')}")
```

______________________________________________________________________

### 17. Update History Log

**Problem**: No record of what was updated when
**Solution**: Log updates to `~/.voltamanager/history.log`

```python
import logging

log_file = Path.home() / ".voltamanager" / "history.log"
logging.basicConfig(filename=log_file, level=logging.INFO)

# After successful update
logging.info(f"Updated {len(to_install)} packages: {', '.join(to_install)}")
```

______________________________________________________________________

### 18. Check for Breaking Changes

**Problem**: Major version updates may have breaking changes
**Solution**: Warn on major version bumps

```python
from packaging import version


def is_major_update(current: str, latest: str) -> bool:
    try:
        return version.parse(latest).major > version.parse(current).major
    except:
        return False


# In check logic
if is_major_update(ver, lat):
    console.print(f"[yellow]⚠ {name}: Major version update detected[/yellow]")
```

______________________________________________________________________

## 🎨 Code Quality Improvements

### 19. Refactor into Multiple Modules

**Current**: Everything in `__init__.py` (255 lines)
**Suggested Structure**:

```
src/voltamanager/
├── __init__.py          # CLI definition only
├── __main__.py          # Entry point
├── core.py              # Core logic (get_installed, check_and_update)
├── npm.py               # NPM registry interactions
├── cache.py             # Caching logic
├── config.py            # Configuration management
└── display.py           # Rich table formatting
```

**Impact**: Better maintainability, easier testing

______________________________________________________________________

### 20. Add Logging

**Current**: No logging infrastructure
**Solution**: Add structured logging

```python
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("voltamanager")

# Usage
logger.info(f"Checking {len(packages)} packages")
logger.error(f"Failed to query npm for {package_name}: {e}")
```

______________________________________________________________________

## 📋 Implementation Priority

### Phase 1 (Quick Wins)

1. ✅ Fix uv run command (DONE)
1. Progress indicators (#2)
1. Better error messages (#10)
1. Output filtering (#3)

### Phase 2 (Performance)

5. Parallel version checking (#1)
1. NPM response caching (#5)
1. Statistics and reporting (#16)

### Phase 3 (Features)

8. JSON output mode (#4)
1. Interactive updates (#8)
1. Configuration file (#9)

### Phase 4 (Quality)

11. Unit tests (#11)
01. Type checking (#12)
01. Code refactoring (#19)

### Phase 5 (Advanced)

14. Rollback capability (#13)
01. Update history log (#17)
01. Breaking change warnings (#18)

______________________________________________________________________

## 🎯 Recommended First Steps

1. **Add tests** (#11) - Critical foundation for future changes
1. **Parallel checking** (#1) - Biggest performance win
1. **Progress indicators** (#2) - Best UX improvement for minimal effort
1. **JSON output** (#4) - Enables automation use cases

Would you like me to implement any of these improvements?
