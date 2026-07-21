"""ShipGate — portable, metadata-driven quality-gate orchestrator."""

from shipgate.api import install, load_catalog, load_config, run

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "install",
    "load_catalog",
    "load_config",
    "run",
]
