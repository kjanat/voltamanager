"""Volta Manager - Check and upgrade Volta-managed global packages."""

from .cli import app as app
from .cli import main as main
from .core import HealthCheckResult as HealthCheckResult
from .core import check_dependencies as check_dependencies
from .core import check_volta_health as check_volta_health
from .core import display_health_check as display_health_check
from .core import get_installed_packages as get_installed_packages
from .core import parse_package as parse_package
from .operations import check_and_update as check_and_update
from .operations import fast_install as fast_install
from .version import __version__ as __version__
