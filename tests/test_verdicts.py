"""Tests for comparison verdicts."""

from llmtest_perf.compare.verdicts import (
    calculate_delta_percent,
    check_regression,
)


def test_calculate_delta_percent():
    """Test delta percentage calculation."""
    # Normal case
    assert calculate_delta_percent(100.0, 110.0) == 10.0
    assert calculate_delta_percent(100.0, 90.0) == -10.0

    # None cases
    assert calculate_delta_percent(None, 100.0) is None
    assert calculate_delta_percent(100.0, None) is None

    # Zero baseline
    assert calculate_delta_percent(0.0, 100.0) is None


def test_check_regression_latency():
    """Test regression detection for latency (lower is better)."""
    # No regression - within threshold
    is_reg, is_imp, msg = check_regression(
        "Latency", 100.0, 105.0, 10.0, higher_is_better=False
    )
    assert not is_reg
    assert not is_imp

    # Regression - exceeds threshold
    is_reg, is_imp, msg = check_regression(
        "Latency", 100.0, 120.0, 10.0, higher_is_better=False
    )
    assert is_reg
    assert not is_imp

    # Improvement
    is_reg, is_imp, msg = check_regression(
        "Latency", 100.0, 90.0, 10.0, higher_is_better=False
    )
    assert not is_reg
    assert is_imp


def test_check_regression_throughput():
    """Test regression detection for throughput (higher is better)."""
    # No regression - within threshold
    is_reg, is_imp, msg = check_regression(
        "Throughput", 100.0, 95.0, 10.0, higher_is_better=True
    )
    assert not is_reg
    assert not is_imp

    # Regression - exceeds threshold
    is_reg, is_imp, msg = check_regression(
        "Throughput", 100.0, 80.0, 10.0, higher_is_better=True
    )
    assert is_reg
    assert not is_imp

    # Improvement
    is_reg, is_imp, msg = check_regression(
        "Throughput", 100.0, 110.0, 10.0, higher_is_better=True
    )
    assert not is_reg
    assert is_imp
