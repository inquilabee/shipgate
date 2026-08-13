"""ShipGate — portable, metadata-driven quality-gate orchestrator."""

from importlib.metadata import PackageNotFoundError, version

from shipgate.api import install, load_catalog, run

try:
    __version__ = version("shipgate")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "install",
    "load_catalog",
    "run",
]
