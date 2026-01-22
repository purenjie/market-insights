"""Data source client for Red Rocket API.

This module handles fetching index data from the Red Rocket (hongsehuojian.com) API.
Migrated from index_analysis/index_etf_table.py
"""

from __future__ import annotations

import logging
import time
from typing import Any, Final

import requests

from market_insights.core.exceptions import DataSourceError
from market_insights.utils.retry import retry
from market_insights.analyzers.index_valuation.models import parse_float

LOG = logging.getLogger(__name__)

BASE_URL: Final[str] = "https://www.hongsehuojian.com"
LIST_ENDPOINT: Final[str] = "/fundex-quote/allPage/findListBySecurity"
VALUATION_ENDPOINT: Final[str] = "/fundex-quote/index/valuation"

DEFAULT_HEADERS: Final[dict[str, str]] = {
    "User-Agent": "Mozilla/5.0 (compatible; MarketInsights/1.0)",
    "Accept": "application/json, text/plain, */*",
}


class RedRocketDataSource:
    """Client for fetching data from Red Rocket API."""

    def __init__(self, timeout: float = 10.0, max_retries: int = 3):
        """Initialize data source.

        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(requests.RequestException,))
    def fetch_basic_info(self, security_code: str) -> dict[str, Any]:
        """Fetch basic index information (PE/PB).

        Args:
            security_code: Index security code

        Returns:
            Dictionary with PE and PB values

        Raises:
            DataSourceError: If request fails
        """
        url = f"{BASE_URL}{LIST_ENDPOINT}"
        # Reason: Use complete parameters as in original code
        params = {
            "classA": "",
            "classB": "",
            "classC": "",
            "orderBy": "scale",
            "order": "desc",
            "searchValue": security_code,
            "isSelected": "",
            "pageNo": "1",
            "pageSize": "1",
            "position": "",
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Parse response
            if not isinstance(data, dict):
                raise DataSourceError(f"Unexpected response type for {security_code}")

            # Check response code
            if data.get("code") != "200":
                LOG.warning(
                    "API returned non-200 code for %s: %s %s",
                    security_code,
                    data.get("code"),
                    data.get("msg"),
                )
                return {"pe": None, "pb": None}

            # Extract data
            payload_data = data.get("data")
            if not isinstance(payload_data, dict):
                return {"pe": None, "pb": None}

            items = payload_data.get("data")
            if not isinstance(items, list) or not items:
                LOG.warning("No data found for %s", security_code)
                return {"pe": None, "pb": None}

            row = items[0]
            return {
                "pe": parse_float(row.get("pe")),
                "pb": parse_float(row.get("pb")),
            }

        except requests.RequestException as exc:
            LOG.error("Failed to fetch basic info for %s: %s", security_code, exc)
            raise DataSourceError(f"Failed to fetch basic info: {exc}") from exc

    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(requests.RequestException,))
    def fetch_dividend_yield(self, security_code: str) -> float | None:
        """Fetch dividend yield (DID).

        Args:
            security_code: Index security code

        Returns:
            Dividend yield (%) or None if not available

        Raises:
            DataSourceError: If request fails
        """
        url = f"{BASE_URL}{VALUATION_ENDPOINT}"

        # Reason: Use current timestamp for the request
        current_time_ms = int(time.time() * 1000)

        params = {
            "securityCode": security_code,
            "time": current_time_ms,
            "timeInterval": "last_5_years",
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                raise DataSourceError(f"Unexpected response type for {security_code}")

            # Extract DID from response
            did_value = data.get("did")
            return parse_float(did_value)

        except requests.RequestException as exc:
            LOG.error("Failed to fetch dividend yield for %s: %s", security_code, exc)
            raise DataSourceError(f"Failed to fetch dividend yield: {exc}") from exc

    def is_healthy(self) -> bool:
        """Check if data source is accessible.

        Returns:
            True if accessible, False otherwise
        """
        try:
            response = self.session.get(BASE_URL, timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
