"""HTTP utilities for making requests with retry logic.

This module provides helper functions for HTTP operations with
built-in retry and error handling.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from market_insights.utils.retry import retry
from market_insights.core.exceptions import DataSourceError

LOG = logging.getLogger(__name__)


@retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(requests.RequestException,))
def fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Fetch JSON data from URL with retry logic.

    Args:
        url: URL to fetch
        headers: Optional HTTP headers
        params: Optional query parameters
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response as dictionary

    Raises:
        DataSourceError: If request fails after retries
    """
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        LOG.error("HTTP request failed: %s", exc)
        raise DataSourceError(f"Failed to fetch {url}: {exc}") from exc
