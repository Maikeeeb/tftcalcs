"""Utilities for file I/O operations with retry logic."""

from __future__ import annotations

import logging
import os
import time
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_file_operation(
    max_retries: int | None = None,
    backoff_base: float | None = None,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
):
    """Decorator to retry file operations with exponential backoff.

    Parameters
    ----------
    max_retries : int | None
        Maximum number of retry attempts. Defaults to 3 or FILE_IO_MAX_RETRIES env var.
    backoff_base : float | None
        Base delay in seconds for exponential backoff. Defaults to 0.1 or FILE_IO_BACKOFF_BASE env var.
    retryable_exceptions : tuple[type[Exception], ...] | None
        Exceptions that should trigger a retry. Defaults to (IOError, OSError, PermissionError).

    Returns
    -------
    Callable
        Decorated function with retry logic.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Get configuration from environment or defaults
            retries = max_retries
            if retries is None:
                retries = int(os.getenv("FILE_IO_MAX_RETRIES", "3"))

            backoff = backoff_base
            if backoff is None:
                backoff = float(os.getenv("FILE_IO_BACKOFF_BASE", "0.1"))

            exceptions = retryable_exceptions
            if exceptions is None:
                exceptions = (IOError, OSError, PermissionError)

            last_exception: Exception | None = None

            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt < retries:
                        delay = backoff * (2**attempt)
                        logger.warning(
                            f"File I/O error on attempt {attempt + 1}/{retries + 1}: {exc}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"File I/O operation failed after {retries + 1} attempts: {exc}"
                        )
                        raise
                except Exception as exc:
                    # Don't retry non-retryable exceptions (e.g., FileNotFoundError)
                    logger.debug(f"Non-retryable exception: {type(exc).__name__}: {exc}")
                    raise

            # Should never reach here, but satisfy type checker
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected error in retry logic")

        return wrapper

    return decorator
