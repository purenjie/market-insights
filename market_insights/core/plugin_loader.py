"""Plugin discovery and loading mechanism.

This module provides automatic discovery of analyzer and notifier plugins
using Python's import system and Protocol-based type checking.
"""

from __future__ import annotations

import importlib
import inspect
import logging
from pathlib import Path
from typing import TypeVar

from market_insights.core.protocols import Analyzer, Notifier

LOG = logging.getLogger(__name__)

T = TypeVar("T")


class PluginLoader:
    """Discovers and loads plugins dynamically.

    This class scans the analyzers/ and notifiers/ directories for plugins
    that implement the required protocols.
    """

    def __init__(self, package_root: Path):
        """Initialize plugin loader.

        Args:
            package_root: Root directory of the market_insights package
        """
        self.package_root = package_root
        self._analyzer_cache: dict[str, Analyzer] = {}
        self._notifier_cache: dict[str, Notifier] = {}

    def discover_analyzers(self) -> dict[str, Analyzer]:
        """Discover all analyzer plugins.

        Searches for analyzer.py files in analyzers/ subdirectories
        and loads classes implementing the Analyzer protocol.

        Returns:
            Dictionary mapping analyzer names to instances
        """
        if self._analyzer_cache:
            return self._analyzer_cache

        analyzers_dir = self.package_root / "analyzers"
        if not analyzers_dir.exists():
            LOG.warning("Analyzers directory not found: %s", analyzers_dir)
            return {}

        for plugin_dir in analyzers_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith("_"):
                continue

            analyzer_file = plugin_dir / "analyzer.py"
            if not analyzer_file.exists():
                continue

            try:
                # Import the module
                module_name = f"market_insights.analyzers.{plugin_dir.name}.analyzer"
                module = importlib.import_module(module_name)

                # Find classes implementing Analyzer protocol
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Reason: Check if class is defined in this module and implements Analyzer
                    if (
                        obj.__module__ == module_name
                        and hasattr(obj, "name")
                        and hasattr(obj, "analyze")
                    ):
                        # Try to instantiate
                        try:
                            instance = obj()
                            if isinstance(instance, Analyzer):
                                self._analyzer_cache[instance.name] = instance
                                LOG.info("Discovered analyzer: %s", instance.name)
                        except TypeError:
                            # Class requires arguments, skip
                            pass

            except Exception:
                LOG.exception("Failed to load analyzer from %s", plugin_dir)

        return self._analyzer_cache

    def discover_notifiers(self) -> dict[str, Notifier]:
        """Discover all notifier plugins.

        Searches for Python files in notifiers/ directory and loads
        classes implementing the Notifier protocol.

        Returns:
            Dictionary mapping notifier names to instances
        """
        if self._notifier_cache:
            return self._notifier_cache

        notifiers_dir = self.package_root / "notifiers"
        if not notifiers_dir.exists():
            return {}

        for notifier_file in notifiers_dir.glob("*.py"):
            if notifier_file.name.startswith("_") or notifier_file.name == "base.py":
                continue

            try:
                module_name = f"market_insights.notifiers.{notifier_file.stem}"
                module = importlib.import_module(module_name)

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        obj.__module__ == module_name
                        and hasattr(obj, "name")
                        and hasattr(obj, "send")
                    ):
                        try:
                            instance = obj()
                            if isinstance(instance, Notifier):
                                self._notifier_cache[instance.name] = instance
                                LOG.info("Discovered notifier: %s", instance.name)
                        except TypeError:
                            pass

            except Exception:
                LOG.exception("Failed to load notifier from %s", notifier_file)

        return self._notifier_cache

    def get_analyzer(self, name: str) -> Analyzer | None:
        """Get analyzer by name.

        Args:
            name: Analyzer name

        Returns:
            Analyzer instance or None if not found
        """
        analyzers = self.discover_analyzers()
        return analyzers.get(name)

    def get_notifier(self, name: str) -> Notifier | None:
        """Get notifier by name.

        Args:
            name: Notifier name

        Returns:
            Notifier instance or None if not found
        """
        notifiers = self.discover_notifiers()
        return notifiers.get(name)
