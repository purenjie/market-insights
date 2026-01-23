"""Telegram notifier for sending messages via Telegram Bot.

This notifier uses python-telegram-bot library to send notifications.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from market_insights.core.config import TelegramConfig
from market_insights.core.exceptions import NotificationError
from market_insights.core.protocols import NotificationPayload
from market_insights.notifiers.base import BaseNotifier

LOG = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    """Notifier that sends messages via Telegram Bot."""

    def __init__(self):
        """Initialize Telegram notifier."""
        self.config = TelegramConfig.from_env()

    @property
    def name(self) -> str:
        """Unique identifier for this notifier."""
        return "telegram"

    def send(self, payload: NotificationPayload) -> bool:
        """Send notification via Telegram.

        Args:
            payload: Notification payload

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            LOG.error("Telegram notifier not configured")
            return False

        try:
            # Reason: python-telegram-bot v20+ uses async API
            return asyncio.run(self._send_async(payload))
        except Exception as exc:
            LOG.exception("Failed to send Telegram notification")
            return False

    def is_available(self) -> bool:
        """Check if Telegram is properly configured.

        Returns:
            True if configured, False otherwise
        """
        return self.config is not None and self.config.enabled

    async def _send_async(self, payload: NotificationPayload) -> bool:
        """Send notification asynchronously.

        Args:
            payload: Notification payload

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid dependency if not used
            from telegram import Bot

            bot = Bot(token=self.config.bot_token)

            # Initialize bot
            async with bot:
                # Reason: 只发送图片附件，不发送总结文本消息
                # Send attachments (images)
                for attachment in payload.attachments:
                    if attachment.exists():
                        with open(attachment, "rb") as f:
                            await bot.send_photo(
                                chat_id=self.config.chat_id,
                                photo=f,
                            )

            LOG.info("Telegram notification sent successfully")
            return True

        except ImportError:
            LOG.error("python-telegram-bot library not installed")
            return False
        except Exception as exc:
            LOG.exception("Failed to send Telegram notification: %s", exc)
            return False
