"""Version handling for voltamanager."""

from importlib.metadata import version

try:
    __version__ = version("voltamanager")
except Exception:
    __version__ = "unknown"
