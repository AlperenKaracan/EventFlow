from logging import Logger
from unittest.mock import Mock

from app.observability.metrics import EventFlowMetrics


def test_metric_update_failure_never_escapes() -> None:
    logger = Mock(spec=Logger)
    metrics = EventFlowMetrics(logger=logger)
    metrics.reservation_attempts.labels = Mock(side_effect=RuntimeError("collector failed"))

    metrics.record_reservation_attempt(outcome="created")

    logger.warning.assert_called_once()


def test_metric_and_fallback_log_failure_never_escape() -> None:
    logger = Mock(spec=Logger)
    logger.warning.side_effect = RuntimeError("logging failed")
    metrics = EventFlowMetrics(logger=logger)
    metrics.rate_limit_rejections.labels = Mock(side_effect=RuntimeError("collector failed"))

    metrics.record_rate_limit_rejection(endpoint="login")
