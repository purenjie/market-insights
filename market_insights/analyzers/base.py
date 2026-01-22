"""Base class for analyzers with common functionality.

This module provides an abstract base class that all analyzers should inherit from.
It provides common functionality like configuration loading and output directory management.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from market_insights.core.protocols import AnalysisResult
from market_insights.core.config import AppConfig, load_yaml_config

LOG = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """Abstract base class for analyzers.

    Provides common functionality like configuration loading,
    output directory management, and error handling patterns.
    """

    def __init__(self, config: AppConfig):
        """Initialize base analyzer.

        Args:
            config: Application configuration
        """
        self.config = config
        self.output_dir = config.output_dir / self.name
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this analyzer."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        ...

    @property
    def enabled(self) -> bool:
        """Whether this analyzer is enabled.

        Override this to add custom enable/disable logic.
        """
        return True

    @abstractmethod
    def analyze(self) -> AnalysisResult:
        """Execute the analysis and return results."""
        ...

    def validate_config(self) -> bool:
        """Validate configuration before execution.

        Override this to add custom validation logic.
        """
        return True

    def load_plugin_config(self) -> dict[str, Any]:
        """Load plugin-specific configuration from config.yaml.

        Returns:
            Dictionary with plugin configuration
        """
        # Reason: Find config.yaml in the same directory as the analyzer module
        config_path = Path(self.__class__.__module__.replace(".", "/")).parent / "config.yaml"
        full_path = self.config.project_root / config_path
        return load_yaml_config(full_path)
