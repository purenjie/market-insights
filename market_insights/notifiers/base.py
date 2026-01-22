"""Base class for notifiers.

This module provides an abstract base class that all notifiers should inherit from.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from market_insights.core.protocols import NotificationPayload

LOG = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """Abstract base class for notifiers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this notifier."""
        ...

    @abstractmethod
    def send(self, payload: NotificationPayload) -> bool:
        """Send notification. Returns True on success."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if notifier is properly configured."""
        ...
