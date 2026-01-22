"""Main orchestrator that coordinates analyzers and notifiers.

The orchestrator is responsible for:
1. Loading and validating plugins
2. Executing analyzers in sequence
3. Aggregating results
4. Sending notifications
5. Handling errors with retry logic
"""

from __future__ import annotations

import logging
from pathlib import Path

from market_insights.core.config import AppConfig
from market_insights.core.plugin_loader import PluginLoader
from market_insights.core.protocols import (
    Analyzer,
    AnalysisResult,
    Notifier,
    NotificationPayload,
)
from market_insights.core.exceptions import OrchestratorError

LOG = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates execution of analyzers and notifiers."""

    def __init__(self, config: AppConfig, plugin_loader: PluginLoader):
        """Initialize orchestrator.

        Args:
            config: Application configuration
            plugin_loader: Plugin loader instance
        """
        self.config = config
        self.plugin_loader = plugin_loader
        self.results: list[AnalysisResult] = []

    def run(self) -> bool:
        """Execute all enabled analyzers and send notifications.

        Returns:
            True if at least one analyzer succeeded, False otherwise
        """
        LOG.info("Starting Market Insights orchestration")

        # Discover plugins
        analyzers = self._load_analyzers()
        notifiers = self._load_notifiers()

        if not analyzers:
            LOG.error("No analyzers enabled or discovered")
            return False

        # Execute analyzers
        self.results = []
        for analyzer in analyzers:
            result = self._execute_analyzer(analyzer)
            self.results.append(result)

        # Send notifications
        if notifiers:
            self._send_notifications(notifiers)

        # Summary
        success_count = sum(1 for r in self.results if r.success)
        LOG.info(
            "Orchestration complete: %d/%d analyzers succeeded",
            success_count,
            len(self.results),
        )

        return success_count > 0

    def _load_analyzers(self) -> list[Analyzer]:
        """Load enabled analyzers.

        Returns:
            List of enabled analyzer instances
        """
        all_analyzers = self.plugin_loader.discover_analyzers()

        if not self.config.enabled_analyzers:
            # If no specific analyzers enabled, use all discovered
            enabled = list(all_analyzers.values())
        else:
            enabled = []
            for name in self.config.enabled_analyzers:
                analyzer = all_analyzers.get(name)
                if analyzer:
                    enabled.append(analyzer)
                else:
                    LOG.warning("Analyzer not found: %s", name)

        # Filter by enabled flag
        enabled = [a for a in enabled if a.enabled]

        LOG.info("Loaded %d analyzers: %s", len(enabled), [a.name for a in enabled])
        return enabled

    def _load_notifiers(self) -> list[Notifier]:
        """Load enabled notifiers.

        Returns:
            List of enabled notifier instances
        """
        all_notifiers = self.plugin_loader.discover_notifiers()

        enabled = []
        for name in self.config.enabled_notifiers:
            notifier = all_notifiers.get(name)
            if notifier and notifier.is_available():
                enabled.append(notifier)
            else:
                LOG.warning("Notifier not available: %s", name)

        LOG.info("Loaded %d notifiers: %s", len(enabled), [n.name for n in enabled])
        return enabled

    def _execute_analyzer(self, analyzer: Analyzer) -> AnalysisResult:
        """Execute a single analyzer with error handling.

        Args:
            analyzer: Analyzer instance to execute

        Returns:
            AnalysisResult with execution outcome
        """
        LOG.info("Executing analyzer: %s", analyzer.name)

        try:
            # Validate configuration
            if not analyzer.validate_config():
                raise OrchestratorError(
                    f"Configuration validation failed for {analyzer.name}"
                )

            # Execute analysis
            result = analyzer.analyze()

            if result.success:
                LOG.info(
                    "Analyzer %s succeeded: %d artifacts generated",
                    analyzer.name,
                    len(result.artifacts),
                )
            else:
                LOG.error("Analyzer %s failed: %s", analyzer.name, result.error)

            return result

        except Exception as exc:
            LOG.exception("Analyzer %s raised exception", analyzer.name)
            return AnalysisResult(
                analyzer_name=analyzer.name,
                success=False,
                artifacts=[],
                summary=f"Failed with error: {exc}",
                metadata={},
                error=exc,
            )

    def _send_notifications(self, notifiers: list[Notifier]) -> None:
        """Send notifications via all enabled notifiers.

        Args:
            notifiers: List of notifier instances
        """
        payload = self._build_notification_payload()

        for notifier in notifiers:
            try:
                success = notifier.send(payload)
                if success:
                    LOG.info("Notification sent via %s", notifier.name)
                else:
                    LOG.warning("Notification failed via %s", notifier.name)
            except Exception:
                LOG.exception("Notifier %s raised exception", notifier.name)

    def _build_notification_payload(self) -> NotificationPayload:
        """Build notification payload from analysis results.

        Returns:
            NotificationPayload with aggregated results
        """
        success_count = sum(1 for r in self.results if r.success)
        total_count = len(self.results)

        # Build message
        lines = [
            "Market Insights Analysis Complete",
            "",
            f"Success: {success_count}/{total_count} analyzers",
            "",
        ]

        for result in self.results:
            status = "✓" if result.success else "✗"
            lines.append(f"{status} {result.analyzer_name}")
            if result.summary:
                lines.append(f"  {result.summary}")

        # Collect all artifacts
        all_artifacts = []
        for result in self.results:
            if result.success:
                all_artifacts.extend(result.artifacts)

        return NotificationPayload(
            title="Market Insights Report",
            message="\n".join(lines),
            attachments=all_artifacts,
            metadata={
                "success_count": success_count,
                "total_count": total_count,
                "results": [
                    {
                        "name": r.analyzer_name,
                        "success": r.success,
                        "artifacts": [str(a) for a in r.artifacts],
                    }
                    for r in self.results
                ],
            },
        )
