"""Data models for index valuation analyzer.

This module contains the data classes used by the index valuation analyzer.
Migrated from index_analysis/index_etf_table.py
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndexSpec:
    """Static configuration for each index.

    Attributes:
        security_code: Index security code (e.g., "000300.SH")
        name: Index name (e.g., "沪深300")
        etf_code: ETF code (e.g., "510300")
        fee_rate: Annual fee rate (e.g., "0.20%")
    """

    security_code: str
    name: str
    etf_code: str
    fee_rate: str


@dataclass(frozen=True)
class IndexRow:
    """Row data for rendering the valuation table.

    Attributes:
        security_code: Index security code
        name: Index name
        pe: Price-to-Earnings ratio (TTM)
        pb: Price-to-Book ratio
        dividend_yield: Dividend yield (%)
        explicit_yield: Explicit yield (same as dividend_yield, %)
        implicit_yield: Implicit yield (1/PE * 100, %)
        roe: Return on Equity (PB/PE * 100, %)
        etf_code: ETF code
        fee_rate: Annual fee rate
    """

    security_code: str
    name: str
    pe: float | None
    pb: float | None
    dividend_yield: float | None
    explicit_yield: float | None
    implicit_yield: float | None
    roe: float | None
    etf_code: str
    fee_rate: str

    def as_cells(self) -> list[str]:
        """Convert row data to table cell strings.

        Returns:
            List of formatted cell strings
        """

        def fmt(v: float | None, ndigits: int = 1) -> str:
            if v is None:
                return "-"
            return f"{v:.{ndigits}f}"

        return [
            self.security_code,
            self.name,
            fmt(self.pe, 1),
            fmt(self.pb, 1),
            (
                f"{fmt(self.dividend_yield, 1)}%"
                if self.dividend_yield is not None
                else "-"
            ),
            (
                f"{fmt(self.explicit_yield, 1)}%"
                if self.explicit_yield is not None
                else "-"
            ),
            (
                f"{fmt(self.implicit_yield, 1)}%"
                if self.implicit_yield is not None
                else "-"
            ),
            f"{fmt(self.roe, 1)}%" if self.roe is not None else "-",
            self.etf_code,
            self.fee_rate,
        ]


def parse_float(value: object) -> float | None:
    """Parse value to float.

    Args:
        value: Value to parse

    Returns:
        Float value or None if parsing fails
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def compute_metrics(
    pe: float | None,
    pb: float | None,
    dividend_yield: float | None,
) -> tuple[float | None, float | None, float | None]:
    """Calculate explicit yield, implicit yield, and ROE.

    Args:
        pe: Price-to-Earnings ratio
        pb: Price-to-Book ratio
        dividend_yield: Dividend yield (%)

    Returns:
        Tuple of (explicit_yield, implicit_yield, roe)
    """
    explicit_yield = dividend_yield

    if pe is None or pe <= 0:
        implicit_yield = None
        roe = None
    else:
        # Reason: Implicit yield is the earnings yield (1/PE * 100)
        implicit_yield = 100.0 / pe
        # Reason: ROE = PB/PE * 100
        roe = (pb / pe * 100.0) if pb else None

    return explicit_yield, implicit_yield, roe
