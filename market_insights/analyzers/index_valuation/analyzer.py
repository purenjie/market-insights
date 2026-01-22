"""Index valuation analyzer implementation.

This module implements the index valuation analyzer that fetches data from
Red Rocket API and generates valuation table visualizations.
Migrated from index_analysis/index_etf_table.py
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from market_insights.analyzers.base import BaseAnalyzer
from market_insights.core.protocols import AnalysisResult
from market_insights.core.config import AppConfig, load_yaml_config
from market_insights.analyzers.index_valuation.data_source import RedRocketDataSource
from market_insights.analyzers.index_valuation.renderer import ValuationTableRenderer
from market_insights.analyzers.index_valuation.models import (
    IndexSpec,
    IndexRow,
    compute_metrics,
)

LOG = logging.getLogger(__name__)


class IndexValuationAnalyzer(BaseAnalyzer):
    """Analyzes index valuations and generates visual reports.

    This analyzer:
    - Fetches PE/PB/dividend yield from Red Rocket API
    - Calculates derived metrics (implicit yield, ROE)
    - Generates color-coded valuation table
    """

    def __init__(self, config: AppConfig | None = None):
        """Initialize analyzer.

        Args:
            config: Application configuration (auto-loaded if None)
        """
        if config is None:
            config = AppConfig.from_env()

        super().__init__(config)

        # Load plugin-specific configuration
        plugin_config = self._load_plugin_config()

        # Initialize data source
        self.data_source = RedRocketDataSource(
            timeout=self.config.http_timeout,
            max_retries=self.config.max_retries,
        )

        # Initialize renderer
        self.renderer = ValuationTableRenderer(
            dpi=plugin_config.get("dpi", 200),
            output_dir=self.output_dir,
        )

        # Load index specifications
        self.index_specs = self._load_index_specs()

    @property
    def name(self) -> str:
        """Unique identifier for this analyzer."""
        return "index_valuation"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Index ETF valuation analysis with PE/PB/dividend metrics"

    def validate_config(self) -> bool:
        """Validate that we have index specifications."""
        if not self.index_specs:
            LOG.error("No index specifications loaded")
            return False
        return True

    def analyze(self) -> AnalysisResult:
        """Execute valuation analysis."""
        LOG.info(
            "Starting index valuation analysis for %d indices",
            len(self.index_specs),
        )

        try:
            # Fetch data for all indices
            rows = self._fetch_all_data()

            # Generate visualization
            output_path = (
                self.output_dir / f"valuation_table_{datetime.now():%Y%m%d}.png"
            )
            self.renderer.render(rows, output_path)

            # Build summary
            valid_count = sum(1 for r in rows if r.pe is not None)
            summary = f"Generated valuation table for {valid_count}/{len(rows)} indices"

            return AnalysisResult(
                analyzer_name=self.name,
                success=True,
                artifacts=[output_path],
                summary=summary,
                metadata={
                    "total_indices": len(rows),
                    "valid_data_count": valid_count,
                    "output_path": str(output_path),
                },
            )

        except Exception as exc:
            LOG.exception("Index valuation analysis failed")
            return AnalysisResult(
                analyzer_name=self.name,
                success=False,
                artifacts=[],
                summary=f"Analysis failed: {exc}",
                metadata={},
                error=exc,
            )

    def _load_plugin_config(self) -> dict:
        """Load plugin-specific configuration."""
        config_path = Path(__file__).parent / "config.yaml"
        return load_yaml_config(config_path)

    def _load_index_specs(self) -> list[IndexSpec]:
        """Load index specifications from config file.

        Returns:
            List of IndexSpec objects
        """
        indices_config_path = self.config.config_dir / "indices.yaml"
        config_data = load_yaml_config(indices_config_path)

        specs = []
        for item in config_data.get("indices", []):
            specs.append(
                IndexSpec(
                    security_code=item["security_code"],
                    name=item["name"],
                    etf_code=item["etf_code"],
                    fee_rate=item["fee_rate"],
                )
            )

        LOG.info("Loaded %d index specifications", len(specs))
        return specs

    def _fetch_all_data(self) -> list[IndexRow]:
        """Fetch data for all indices.

        Returns:
            List of IndexRow objects with fetched data
        """
        rows = []

        for spec in self.index_specs:
            try:
                # Fetch basic info (PE/PB)
                basic_info = self.data_source.fetch_basic_info(spec.security_code)
                pe = basic_info.get("pe")
                pb = basic_info.get("pb")

                # Fetch dividend yield
                dividend_yield = self.data_source.fetch_dividend_yield(
                    spec.security_code
                )

                # Compute derived metrics
                explicit_yield, implicit_yield, roe = compute_metrics(
                    pe, pb, dividend_yield
                )

                # Create row
                row = IndexRow(
                    security_code=spec.security_code,
                    name=spec.name,
                    pe=pe,
                    pb=pb,
                    dividend_yield=dividend_yield,
                    explicit_yield=explicit_yield,
                    implicit_yield=implicit_yield,
                    roe=roe,
                    etf_code=spec.etf_code,
                    fee_rate=spec.fee_rate,
                )
                rows.append(row)

            except Exception as exc:
                # Reason: Degradation strategy - continue with partial data
                LOG.warning(
                    "Failed to fetch data for %s: %s", spec.security_code, exc
                )
                # Add row with None values
                row = IndexRow(
                    security_code=spec.security_code,
                    name=spec.name,
                    pe=None,
                    pb=None,
                    dividend_yield=None,
                    explicit_yield=None,
                    implicit_yield=None,
                    roe=None,
                    etf_code=spec.etf_code,
                    fee_rate=spec.fee_rate,
                )
                rows.append(row)

        return rows
