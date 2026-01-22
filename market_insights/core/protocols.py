"""Protocol definitions for plugin interfaces.

This module defines the core interfaces that all plugins must implement.
Using Protocol allows for structural subtyping (duck typing with type checking).
"""

from __future__ import annotations

from typing import Protocol, Any, runtime_checkable
from pathlib import Path
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """Result from an analyzer execution.

    Attributes:
        analyzer_name: Unique identifier of the analyzer
        success: Whether the analysis completed successfully
        artifacts: List of generated files (images, reports, etc.)
        summary: Human-readable summary for notifications
        metadata: Additional metadata about the analysis
        error: Exception if analysis failed, None otherwise
    """

    analyzer_name: str
    success: bool
    artifacts: list[Path]
    summary: str
    metadata: dict[str, Any]
    error: Exception | None = None


@dataclass
class NotificationPayload:
    """Payload for notifications.

    Attributes:
        title: Notification title
        message: Main message content
        attachments: List of files to attach
        metadata: Additional metadata
    """

    title: str
    message: str
    attachments: list[Path]
    metadata: dict[str, Any]


@runtime_checkable
class Analyzer(Protocol):
    """Protocol for analyzer plugins.

    Each analyzer must implement this interface to be discoverable
    and executable by the orchestrator.
    """

    @property
    def name(self) -> str:
        """Unique identifier for this analyzer."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    @property
    def enabled(self) -> bool:
        """Whether this analyzer is enabled."""
        ...

    def analyze(self) -> AnalysisResult:
        """Execute the analysis and return results."""
        ...

    def validate_config(self) -> bool:
        """Validate configuration before execution."""
        ...


@runtime_checkable
class Notifier(Protocol):
    """Protocol for notification plugins."""

    @property
    def name(self) -> str:
        """Unique identifier for this notifier."""
        ...

    def send(self, payload: NotificationPayload) -> bool:
        """Send notification. Returns True on success."""
        ...

    def is_available(self) -> bool:
        """Check if notifier is properly configured."""
        ...


@runtime_checkable
class DataSource(Protocol):
    """Protocol for data source clients."""

    def fetch(self, **kwargs: Any) -> Any:
        """Fetch data from the source."""
        ...

    def is_healthy(self) -> bool:
        """Check if data source is accessible."""
        ...
