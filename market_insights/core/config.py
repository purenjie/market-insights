"""Configuration management with environment variable support.

This module handles loading configuration from multiple sources:
1. Environment variables (highest priority)
2. YAML configuration files
3. Default values (lowest priority)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

import yaml


@dataclass
class AppConfig:
    """Application-wide configuration.

    Attributes:
        project_root: Root directory of the project
        config_dir: Directory containing configuration files
        output_dir: Directory for output artifacts
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Format string for log messages
        enabled_analyzers: List of analyzer names to enable
        enabled_notifiers: List of notifier names to enable
        max_retries: Maximum number of retry attempts for failed operations
        retry_delay: Initial delay between retries (seconds)
        http_timeout: HTTP request timeout (seconds)
        http_user_agent: User agent string for HTTP requests
    """

    # Paths
    project_root: Path
    config_dir: Path
    output_dir: Path

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

    # Execution
    enabled_analyzers: list[str] = field(default_factory=list)
    enabled_notifiers: list[str] = field(default_factory=list)

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0

    # HTTP settings
    http_timeout: float = 10.0
    http_user_agent: str = "MarketInsights/1.0"

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> AppConfig:
        """Load configuration from environment and config files.

        Args:
            project_root: Project root directory. If None, auto-detect.

        Returns:
            AppConfig instance with loaded configuration
        """
        # Reason: Auto-detect project root if not provided
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        # Load .env file if exists (using python-dotenv if available)
        env_file = project_root / ".env"
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                pass  # python-dotenv not installed, skip

        config_dir = project_root / "config"
        output_dir = project_root / "output"
        output_dir.mkdir(exist_ok=True)

        # Load main config from YAML
        main_config_path = config_dir / "analyzers.yaml"
        if main_config_path.exists():
            config_data = load_yaml_config(main_config_path)
        else:
            config_data =

        return cls(
            project_root=project_root,
            config_dir=config_dir,
            output_dir=output_dir,
            log_level=os.getenv("LOG_LEVEL", config_data.get("log_level", "INFO")),
            enabled_analyzers=_parse_list(
                os.getenv("ENABLED_ANALYZERS"),
                config_data.get("enabled_analyzers", []),
            ),
            enabled_notifiers=_parse_list(
                os.getenv("ENABLED_NOTIFIERS"),
                config_data.get("enabled_notifiers", ["console"]),
            ),
            max_retries=int(
                os.getenv("MAX_RETRIES", config_data.get("max_retries", 3))
            ),
            retry_delay=float(
                os.getenv("RETRY_DELAY", config_data.get("retry_delay", 1.0))
            ),
            http_timeout=float(
                os.getenv("HTTP_TIMEOUT", config_data.get("http_timeout", 10.0))
            ),
        )


@dataclass
class TelegramConfig:
    """Telegram bot configuration.

    Attributes:
        bot_token: Telegram bot token
        chat_id: Target chat ID for notifications
        enabled: Whether Telegram notifications are enabled
    """

    bot_token: str
    chat_id: str
    enabled: bool = True

    @classmethod
    def from_env(cls) -> TelegramConfig | None:
        """Load from environment variables.

        Returns:
            TelegramConfig if credentials are available, None otherwise
        """
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            return None

        return cls(
            bot_token=bot_token,
            chat_id=chat_id,
            enabled=os.getenv("TELEGRAM_ENABLED", "true").lower() == "true",
        )


def _parse_list(env_value: str | None, default: list[str]) -> list[str]:
    """Parse comma-separated environment variable.

    Args:
        env_value: Environment variable value (comma-separated)
        default: Default list if env_value is None

    Returns:
        List of strings
    """
    if env_value:
        return [s.strip() for s in env_value.split(",") if s.strip()]
    return default


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load YAML configuration file.

    Args:
        path: Path to YAML file

    Returns:
        Dictionary with configuration data, empty dict if file doesn't exist
    """
    if not path.exists():
        return {}

    with open(path) as f:
        return yaml.safe_load(f) or {}
