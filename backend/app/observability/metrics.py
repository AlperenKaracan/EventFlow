from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from contextvars import ContextVar, Token
from logging import Logger
from time import perf_counter

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

_current_metrics: ContextVar[EventFlowMetrics | None] = ContextVar(
    "eventflow_metrics",
    default=None,
)


class EventFlowMetrics:
    def __init__(self, *, logger: Logger) -> None:
        self.logger = logger
        self.registry = CollectorRegistry()
        self.http_requests = Counter(
            "eventflow_http_requests_total",
            "Completed EventFlow HTTP requests.",
            ("method", "route", "status"),
            registry=self.registry,
        )
        self.http_request_duration = Histogram(
            "eventflow_http_request_duration_seconds",
            "EventFlow HTTP request duration in seconds.",
            ("method", "route"),
            registry=self.registry,
        )
        self.http_requests_in_progress = Gauge(
            "eventflow_http_requests_in_progress",
            "EventFlow HTTP requests currently in progress.",
            registry=self.registry,
        )
        self.http_errors = Counter(
            "eventflow_http_errors_total",
            "Completed EventFlow HTTP error responses.",
            ("method", "route", "status"),
            registry=self.registry,
        )
        self.reservation_attempts = Counter(
            "eventflow_reservation_attempts_total",
            "Reservation attempts grouped by bounded outcome.",
            ("outcome",),
            registry=self.registry,
        )
        self.reservation_lock_wait = Histogram(
            "eventflow_reservation_lock_wait_seconds",
            "Time spent waiting for the event row lock in reservation operations.",
            ("operation",),
            registry=self.registry,
        )
        self.idempotency_requests = Counter(
            "eventflow_idempotency_requests_total",
            "Idempotency decisions grouped by bounded outcome.",
            ("outcome",),
            registry=self.registry,
        )
        self.event_cancellations = Counter(
            "eventflow_event_cancellations_total",
            "Successfully committed event cancellations.",
            registry=self.registry,
        )
        self.rate_limit_rejections = Counter(
            "eventflow_rate_limit_rejections_total",
            "Rate-limit rejections grouped by endpoint.",
            ("endpoint",),
            registry=self.registry,
        )
        self.readiness_status = Gauge(
            "eventflow_readiness_status",
            "Readiness of an EventFlow dependency where 1 is ready and 0 is unavailable.",
            ("dependency",),
            registry=self.registry,
        )
        for dependency in ("postgresql", "redis"):
            self.readiness_status.labels(dependency=dependency).set(0)

    def _record(self, *, metric: str, update: Callable[[], None]) -> None:
        try:
            update()
        except Exception:
            with suppress(Exception):
                self.logger.warning(
                    "Metric update failed",
                    extra={"event": "observability.metric_update_failed", "metric": metric},
                    exc_info=True,
                )

    def request_started(self) -> None:
        self._record(
            metric="eventflow_http_requests_in_progress",
            update=self.http_requests_in_progress.inc,
        )

    def request_completed(
        self,
        *,
        method: str,
        route: str,
        status: int,
        duration_seconds: float,
    ) -> None:
        def update() -> None:
            labels = {"method": method, "route": route, "status": str(status)}
            self.http_requests.labels(**labels).inc()
            self.http_request_duration.labels(method=method, route=route).observe(duration_seconds)
            if status >= 400:
                self.http_errors.labels(**labels).inc()

        self._record(metric="eventflow_http_request", update=update)
        self._record(
            metric="eventflow_http_requests_in_progress",
            update=self.http_requests_in_progress.dec,
        )

    def observe_reservation_lock_wait(self, *, operation: str, started_at: float) -> None:
        self._record(
            metric="eventflow_reservation_lock_wait_seconds",
            update=lambda: self.reservation_lock_wait.labels(operation=operation).observe(
                perf_counter() - started_at
            ),
        )

    def record_reservation_attempt(self, *, outcome: str) -> None:
        self._record(
            metric="eventflow_reservation_attempts_total",
            update=lambda: self.reservation_attempts.labels(outcome=outcome).inc(),
        )

    def record_idempotency_request(self, *, outcome: str) -> None:
        self._record(
            metric="eventflow_idempotency_requests_total",
            update=lambda: self.idempotency_requests.labels(outcome=outcome).inc(),
        )

    def record_event_cancellation(self) -> None:
        self._record(
            metric="eventflow_event_cancellations_total",
            update=self.event_cancellations.inc,
        )

    def record_rate_limit_rejection(self, *, endpoint: str) -> None:
        self._record(
            metric="eventflow_rate_limit_rejections_total",
            update=lambda: self.rate_limit_rejections.labels(endpoint=endpoint).inc(),
        )

    def set_readiness(self, *, dependency: str, ready: bool) -> None:
        self._record(
            metric="eventflow_readiness_status",
            update=lambda: self.readiness_status.labels(dependency=dependency).set(int(ready)),
        )


def set_current_metrics(metrics: EventFlowMetrics) -> Token[EventFlowMetrics | None]:
    return _current_metrics.set(metrics)


def reset_current_metrics(token: Token[EventFlowMetrics | None]) -> None:
    _current_metrics.reset(token)


def get_current_metrics() -> EventFlowMetrics | None:
    return _current_metrics.get()


def record_reservation_attempt(*, outcome: str) -> None:
    if metrics := get_current_metrics():
        metrics.record_reservation_attempt(outcome=outcome)


def observe_reservation_lock_wait(*, operation: str, started_at: float) -> None:
    if metrics := get_current_metrics():
        metrics.observe_reservation_lock_wait(operation=operation, started_at=started_at)


def record_idempotency_request(*, outcome: str) -> None:
    if metrics := get_current_metrics():
        metrics.record_idempotency_request(outcome=outcome)


def record_event_cancellation() -> None:
    if metrics := get_current_metrics():
        metrics.record_event_cancellation()


def record_rate_limit_rejection(*, endpoint: str) -> None:
    if metrics := get_current_metrics():
        metrics.record_rate_limit_rejection(endpoint=endpoint)
