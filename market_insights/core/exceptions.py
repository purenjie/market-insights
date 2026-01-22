"""Custom exceptions for the Market Insights application."""


class MarketInsightsError(Exception):
    """Base exception for all Market Insights errors."""

    pass


class ConfigurationError(MarketInsightsError):
    """Raised when configuration is invalid or missing."""

    pass


class PluginError(MarketInsightsError):
    """Raised when plugin loading or execution fails."""

    pass


class OrchestratorError(MarketInsightsError):
    """Raised when orchestrator encounters an error."""

    pass


class DataSourceError(MarketInsightsError):
    """Raised when data source operations fail."""

    pass


class NotificationError(MarketInsightsError):
    """Raised when notification sending fails."""

    pass
