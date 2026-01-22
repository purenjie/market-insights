"""Retry decorator with exponential backoff.

This module provides a decorator for retrying failed operations with
configurable backoff strategies.
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, TypeVar, Any

LOG = logging.getLogger(__name__)

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function with retry logic

    Example:
        @retry(max_attempts=3, delay=1.0, backoff=2.0)
        def fetch_data():
            return requests.get("https://api.example.com/data")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        LOG.error(
                            "Function %s failed after %d attempts",
                            func.__name__,
                            max_attempts,
                        )
                        raise

                    LOG.warning(
                        "Function %s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                        func.__name__,
                        attempt,
                        max_attempts,
                        exc,
                        current_delay,
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            # Should never reach here, but for type safety
            raise last_exception or RuntimeError("Retry logic error")

        return wrapper

    return decorator
