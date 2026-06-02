"""
Rule-based incident analysis service.

Phase 1: Keyword matching against known failure patterns.
Phase 2: Replace or augment with Gemini API integration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="The incident message to analyse.",
        examples=["Database connection timeout"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {"message": "Database connection timeout"}
        }
    }


class AnalysisResponse(BaseModel):
    severity: str
    possible_root_cause: str
    recommendation: str


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

@dataclass
class _Rule:
    keywords: tuple[str, ...]
    severity: str
    root_cause: str
    recommendation: str


_RULES: list[_Rule] = [
    # Database
    _Rule(
        keywords=("connection pool", "pool exhausted", "too many connections"),
        severity="critical",
        root_cause="Database connection pool exhausted — all connections in use",
        recommendation=(
            "Increase the database connection pool size and audit long-running "
            "transactions. Consider adding read replicas or PgBouncer."
        ),
    ),
    _Rule(
        keywords=("database connection timeout", "db timeout", "connection timed out"),
        severity="high",
        root_cause="Database connection timeout — network latency or overloaded DB host",
        recommendation=(
            "Check database server load and network round-trip time. "
            "Tune connection timeouts and implement exponential back-off retries."
        ),
    ),
    _Rule(
        keywords=("deadlock", "lock wait", "lock timeout"),
        severity="high",
        root_cause="Database deadlock detected — concurrent transactions holding conflicting locks",
        recommendation=(
            "Review transaction isolation levels and query ordering. "
            "Add retry logic for deadlock scenarios."
        ),
    ),
    _Rule(
        keywords=("disk full", "no space left", "storage full", "out of disk"),
        severity="critical",
        root_cause="Disk storage exhausted on the affected host",
        recommendation=(
            "Free disk space immediately by purging old logs or data. "
            "Add persistent volume capacity and set up disk usage alerts."
        ),
    ),
    # Memory
    _Rule(
        keywords=("out of memory", "oom", "memory limit", "heap overflow", "memory pressure"),
        severity="critical",
        root_cause="Process exceeded available memory — OOM condition",
        recommendation=(
            "Increase container/VM memory limits. Profile for memory leaks and "
            "implement circuit breakers to shed load under pressure."
        ),
    ),
    _Rule(
        keywords=("memory leak", "memory usage high", "high memory"),
        severity="high",
        root_cause="Suspected memory leak causing gradual memory growth",
        recommendation=(
            "Profile the application with a heap profiler. "
            "Review recent code changes for unbounded caches or unclosed resources."
        ),
    ),
    # CPU
    _Rule(
        keywords=("cpu spike", "cpu usage", "high cpu", "100% cpu", "cpu throttl"),
        severity="high",
        root_cause="CPU saturation causing request latency spikes",
        recommendation=(
            "Identify hot code paths with a profiler. "
            "Consider horizontal scaling or rate limiting to protect the service."
        ),
    ),
    # Network
    _Rule(
        keywords=("network timeout", "connection refused", "unreachable", "dns resolution"),
        severity="high",
        root_cause="Network connectivity issue between services or external dependencies",
        recommendation=(
            "Verify firewall rules, DNS resolution, and VPC peering. "
            "Implement retries with jitter and circuit breakers for downstream calls."
        ),
    ),
    _Rule(
        keywords=("rate limit", "429", "too many requests", "throttled"),
        severity="medium",
        root_cause="Upstream API rate limit reached",
        recommendation=(
            "Implement client-side rate limiting and exponential back-off. "
            "Request a quota increase from the upstream provider."
        ),
    ),
    # Application
    _Rule(
        keywords=("null pointer", "nullpointerexception", "none type", "attribute error"),
        severity="medium",
        root_cause="Null / None reference accessed — unhandled edge case in code",
        recommendation=(
            "Add defensive null checks and unit tests for edge cases. "
            "Review recent deployments for regressions."
        ),
    ),
    _Rule(
        keywords=("500", "internal server error", "unhandled exception", "traceback"),
        severity="high",
        root_cause="Unhandled exception causing 5xx responses",
        recommendation=(
            "Review application logs and error tracking. "
            "Add global exception handlers and alerting on 5xx rate."
        ),
    ),
    _Rule(
        keywords=("authentication", "401", "unauthorized", "token expired", "jwt"),
        severity="medium",
        root_cause="Authentication failure — expired or invalid credentials",
        recommendation=(
            "Rotate secrets and verify token expiration settings. "
            "Ensure client applications refresh tokens proactively."
        ),
    ),
    _Rule(
        keywords=("timeout", "timed out", "request timeout", "response timeout"),
        severity="medium",
        root_cause="Service response timeout — downstream dependency too slow",
        recommendation=(
            "Set explicit timeout budgets per downstream call. "
            "Add circuit breakers and asynchronous processing where feasible."
        ),
    ),
]

_DEFAULT_RULE = _Rule(
    keywords=(),
    severity="medium",
    root_cause="Root cause undetermined — insufficient signal for rule-based matching",
    recommendation=(
        "Collect full stack traces and logs from the affected service. "
        "Enable distributed tracing (e.g., Cloud Trace) for end-to-end visibility."
    ),
)


class AnalysisService:
    """
    Phase 1 rule-based analysis engine.

    Evaluates the incident message against a prioritised list of keyword
    rules and returns the first matching diagnosis.  Rules are ordered
    from most-specific to most-general so that a longer keyword phrase
    wins over a shorter one.
    """

    def analyse(self, message: str) -> AnalysisResponse:
        normalised = message.lower()
        logger.debug("Analysing message: %r", message)

        matched_rule = _DEFAULT_RULE
        for rule in _RULES:
            if any(kw in normalised for kw in rule.keywords):
                matched_rule = rule
                logger.info("Matched rule with keywords %s", rule.keywords)
                break

        return AnalysisResponse(
            severity=matched_rule.severity,
            possible_root_cause=matched_rule.root_cause,
            recommendation=matched_rule.recommendation,
        )


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

_analysis_service: AnalysisService | None = None


def get_analysis_service() -> AnalysisService:
    """Return a cached singleton AnalysisService."""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
