"""Tests for metrics calculation."""

from llmtest_perf.engine.metrics import calculate_percentiles


def test_calculate_percentiles():
    """Test percentile calculation."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    stats = calculate_percentiles(values)

    assert stats is not None
    assert stats.min == 1.0
    assert stats.max == 10.0
    assert stats.mean == 5.5
    assert stats.count == 10
    assert stats.p50 == 5.5
    assert stats.p95 > stats.p90
    assert stats.p99 > stats.p95


def test_calculate_percentiles_empty():
    """Test percentile calculation with empty list."""
    stats = calculate_percentiles([])
    assert stats is None


def test_calculate_percentiles_single_value():
    """Test percentile calculation with single value."""
    stats = calculate_percentiles([5.0])
    assert stats is not None
    assert stats.min == 5.0
    assert stats.max == 5.0
    assert stats.mean == 5.0
    assert stats.p50 == 5.0
    assert stats.p95 == 5.0
