"""Console notifier for local testing.

This notifier prints notification content to the console.
"""

from __future__ import annotations

import logging

from market_insights.notifiers.base import BaseNotifier
from market_insights.core.protocols import NotificationPayload

LOG = logging.getLogger(__name__)


class ConsoleNotifier(BaseNotifier):
    """Notifier that prints to console (for testing)."""

    @property
    def name(self) -> str:
        """Unique identifier for this notifier."""
        return "console"

    def send(self, payload: NotificationPayload) -> bool:
        """Print notification to console.

        Args:
            payload: Notification payload

        Returns:
            Always True
        """
        print("\n" + "=" * 60)
        print(f"NOTIFICATION: {payload.title}")
        print("=" * 60)
        print(payload.message)

        if payload.attachments:
            print("\nAttachments:")
            for attachment in payload.attachments:
                print(f"  - {attachment}")

        print("=" * 60 + "\n")

        return True

    def is_available(self) -> bool:
        """Console is always available.

        Returns:
            Always True
        """
        return True
