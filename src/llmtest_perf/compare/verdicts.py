"""Verdict and regression detection logic."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class VerdictStatus(Enum):
    """Status of a performance comparison."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    UNKNOWN = "UNKNOWN"


@dataclass
class MetricComparison:
    """Comparison of a single metric."""

    metric_name: str
    baseline_value: Optional[float]
    candidate_value: Optional[float]
    delta_percent: Optional[float]
    delta_absolute: Optional[float]
    is_regression: bool
    is_improvement: bool
    message: str


@dataclass
class ComparisonVerdict:
    """Overall verdict from baseline vs candidate comparison."""

    status: VerdictStatus
    baseline_target: str
    candidate_target: str
    metrics: list[MetricComparison]
    summary: str
    recommendation: str

    def has_regressions(self) -> bool:
        """Check if any regressions were detected."""
        return any(m.is_regression for m in self.metrics)

    def regression_count(self) -> int:
        """Count number of regressions."""
        return sum(1 for m in self.metrics if m.is_regression)

    def improvement_count(self) -> int:
        """Count number of improvements."""
        return sum(1 for m in self.metrics if m.is_improvement)


def calculate_delta_percent(baseline: Optional[float], candidate: Optional[float]) -> Optional[float]:
    """Calculate percentage delta between baseline and candidate."""
    if baseline is None or candidate is None or baseline == 0:
        return None
    return ((candidate - baseline) / baseline) * 100


def check_regression(
    metric_name: str,
    baseline: Optional[float],
    candidate: Optional[float],
    threshold_percent: Optional[float],
    higher_is_better: bool = False,
) -> tuple[bool, bool, str]:
    """
    Check if a metric shows regression.

    Args:
        metric_name: Name of the metric
        baseline: Baseline value
        candidate: Candidate value
        threshold_percent: Max allowed regression percentage
        higher_is_better: If True, increases are good (e.g., throughput)

    Returns:
        Tuple of (is_regression, is_improvement, message)
    """
    if baseline is None or candidate is None:
        return False, False, "Insufficient data"

    delta_pct = calculate_delta_percent(baseline, candidate)
    if delta_pct is None:
        return False, False, "Cannot calculate delta"

    # Determine regression based on direction
    if higher_is_better:
        # For metrics where higher is better (throughput)
        is_regression = delta_pct < 0 and threshold_percent is not None and abs(delta_pct) > threshold_percent
        is_improvement = delta_pct > 0
        direction = "decrease" if delta_pct < 0 else "increase"
    else:
        # For metrics where lower is better (latency, error rate)
        is_regression = delta_pct > 0 and threshold_percent is not None and delta_pct > threshold_percent
        is_improvement = delta_pct < 0
        direction = "increase" if delta_pct > 0 else "decrease"

    if is_regression:
        message = f"{metric_name}: {direction} of {abs(delta_pct):.1f}% exceeds threshold ({threshold_percent}%)"
    elif is_improvement:
        message = f"{metric_name}: {direction} of {abs(delta_pct):.1f}% (improvement)"
    else:
        message = f"{metric_name}: {direction} of {abs(delta_pct):.1f}% (within threshold)"

    return is_regression, is_improvement, message


def format_value(value: Optional[float], unit: str = "") -> str:
    """Format a metric value for display."""
    if value is None:
        return "N/A"
    return f"{value:.2f}{unit}"


def format_delta(delta: Optional[float]) -> str:
    """Format a delta percentage for display."""
    if delta is None:
        return "N/A"
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta:.1f}%"
