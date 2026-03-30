"""Metrics calculation and aggregation."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PercentileStats:
    """Percentile statistics for a metric."""

    p50: float
    p90: float
    p95: float
    p99: float
    mean: float
    min: float
    max: float
    count: int


def calculate_percentiles(values: List[float]) -> Optional[PercentileStats]:
    """
    Calculate percentile statistics from a list of values.

    Args:
        values: List of numeric values

    Returns:
        PercentileStats or None if no values
    """
    if not values:
        return None

    sorted_values = sorted(values)
    count = len(sorted_values)

    def percentile(p: float) -> float:
        """Calculate the p-th percentile."""
        if count == 1:
            return sorted_values[0]
        index = (count - 1) * p
        lower = int(index)
        upper = min(lower + 1, count - 1)
        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight

    return PercentileStats(
        p50=percentile(0.50),
        p90=percentile(0.90),
        p95=percentile(0.95),
        p99=percentile(0.99),
        mean=sum(sorted_values) / count,
        min=sorted_values[0],
        max=sorted_values[-1],
        count=count,
    )


@dataclass
class AggregatedMetrics:
    """Aggregated performance metrics."""

    target_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate_percent: float
    duration_seconds: float
    requests_per_sec: float

    latency: Optional[PercentileStats]
    ttft: Optional[PercentileStats]

    total_output_tokens: int
    output_tokens_per_sec: float

    error_breakdown: Dict[str, int]

    # Per-prompt-set metrics
    prompt_set_metrics: Dict[str, "PromptSetMetrics"]


@dataclass
class PromptSetMetrics:
    """Metrics for a specific prompt set."""

    name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate_percent: float
    latency: Optional[PercentileStats]
    ttft: Optional[PercentileStats]
    output_tokens_mean: Optional[float]
