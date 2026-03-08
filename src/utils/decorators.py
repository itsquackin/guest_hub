"""Utility decorators for the Guest Hub pipeline."""
from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import TypeVar

F = TypeVar("F", bound=Callable)


def log_stage(logger: logging.Logger | None = None) -> Callable[[F], F]:
    """Decorator that logs entry, exit, and elapsed time for a pipeline function.

    Usage::

        @log_stage()
        def my_stage() -> None:
            ...

        @log_stage(logger=logging.getLogger("pipeline"))
        def another_stage() -> None:
            ...
    """
    def decorator(fn: F) -> F:
        _logger = logger or logging.getLogger(fn.__module__)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            _logger.info("→ Starting stage: %s", fn.__name__)
            start = time.monotonic()
            try:
                result = fn(*args, **kwargs)
                elapsed = time.monotonic() - start
                _logger.info("✓ Completed stage: %s (%.2fs)", fn.__name__, elapsed)
                return result
            except Exception as exc:
                elapsed = time.monotonic() - start
                _logger.error(
                    "✗ Stage failed: %s after %.2fs — %s: %s",
                    fn.__name__,
                    elapsed,
                    type(exc).__name__,
                    exc,
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def catch_and_log(
    logger: logging.Logger | None = None,
    *,
    default=None,
    reraise: bool = False,
) -> Callable[[F], F]:
    """Decorator that catches exceptions, logs them, and returns *default*.

    Useful for optional enrichment steps where failures should not abort
    the pipeline.

    Args:
        logger: Logger to use; falls back to module-level logger.
        default: Value to return on exception.
        reraise: If True, re-raise the exception after logging.
    """
    def decorator(fn: F) -> F:
        _logger = logger or logging.getLogger(fn.__module__)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                _logger.warning(
                    "Non-fatal error in %s: %s: %s",
                    fn.__name__,
                    type(exc).__name__,
                    exc,
                )
                if reraise:
                    raise
                return default

        return wrapper  # type: ignore[return-value]

    return decorator
