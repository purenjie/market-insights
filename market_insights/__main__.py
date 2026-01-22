"""Main entry point for Market Insights application.

Usage:
    python -m market_insights
"""

from __future__ import annotations

import sys
import logging
from pathlib import Path

from market_insights.core.config import AppConfig
from market_insights.core.plugin_loader import PluginLoader
from market_insights.core.orchestrator import Orchestrator
from market_insights.utils.logging import setup_logging

LOG = logging.getLogger(__name__)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Load configuration
    config = AppConfig.from_env()

    # Setup logging
    setup_logging(
        log_level=config.log_level,
        log_format=config.log_format,
    )

    LOG.info("Starting Market Insights")
    LOG.info("Project root: %s", config.project_root)

    try:
        # Initialize plugin loader
        plugin_loader = PluginLoader(config.project_root / "market_insights")

        # Initialize orchestrator
        orchestrator = Orchestrator(config, plugin_loader)

        # Run analysis
        success = orchestrator.run()

        if success:
            LOG.info("Market Insights completed successfully")
            return 0
        else:
            LOG.error("Market Insights completed with errors")
            return 1

    except Exception as exc:
        LOG.exception("Market Insights failed with exception")
        return 1


if __name__ == "__main__":
    sys.exit(main())
