"""Logging configuration utilities."""
from __future__ import annotations

import logging
import logging.config
from pathlib import Path

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    _YAML_AVAILABLE = False

_DEFAULT_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    config_path: str | Path | None = None,
    level: str = "INFO",
) -> None:
    """Configure the root logger.

    When *config_path* points to a valid YAML ``dictConfig`` file, that
    configuration is applied.  Otherwise a sensible default is used.

    Args:
        config_path: Path to a YAML logging config file (optional).
        level: Fallback log level string (e.g. ``"INFO"``, ``"DEBUG"``).
    """
    if config_path and _YAML_AVAILABLE:
        cfg_path = Path(config_path)
        if cfg_path.exists():
            with open(cfg_path) as fh:
                cfg = yaml.safe_load(fh)
            if cfg and isinstance(cfg, dict) and "version" in cfg:
                logging.config.dictConfig(cfg)
                return

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=_DEFAULT_FORMAT,
        datefmt=_DEFAULT_DATE_FORMAT,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for use in pipeline modules."""
    return logging.getLogger(name)
