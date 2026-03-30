"""Tests for configuration loading and validation."""

import pytest
from pydantic import ValidationError

from llmtest_perf.config.models import (
    ComparisonConfig,
    PerfTestConfig,
    PromptSet,
    RequestConfig,
    SLOConfig,
    TargetConfig,
    WorkloadConfig,
)


def test_target_config_validation():
    """Test TargetConfig validation."""
    # Valid config
    config = TargetConfig(
        base_url="http://localhost:8000/v1",
        model="gpt-3.5-turbo",
    )
    assert config.base_url == "http://localhost:8000/v1"

    # Invalid URL
    with pytest.raises(ValidationError):
        TargetConfig(base_url="not-a-url", model="test")


def test_prompt_set_validation():
    """Test PromptSet validation."""
    # Valid
    ps = PromptSet(
        name="test",
        weight=50,
        prompts=["prompt1", "prompt2"],
    )
    assert len(ps.prompts) == 2

    # Weight out of range
    with pytest.raises(ValidationError):
        PromptSet(name="test", weight=150, prompts=["p1"])

    # Empty prompts
    with pytest.raises(ValidationError):
        PromptSet(name="test", weight=50, prompts=[])


def test_workload_config_validation():
    """Test WorkloadConfig validation."""
    # Valid
    config = WorkloadConfig(
        duration_seconds=60,
        max_concurrency=32,
        ramp_up_seconds=10,
        stream=True,
        prompt_sets=[
            PromptSet(name="test", weight=100, prompts=["p1"])
        ],
    )
    assert config.duration_seconds == 60

    # Ramp-up >= duration
    with pytest.raises(ValidationError):
        WorkloadConfig(
            duration_seconds=60,
            max_concurrency=32,
            ramp_up_seconds=60,
            prompt_sets=[
                PromptSet(name="test", weight=100, prompts=["p1"])
            ],
        )


def test_request_config_defaults():
    """Test RequestConfig defaults."""
    config = RequestConfig()
    assert config.max_tokens == 256
    assert config.temperature == 0.0
    assert config.timeout_seconds == 60


def test_perf_test_config_comparison_validation():
    """Test PerfTestConfig validates comparison targets."""
    # Missing candidate target
    with pytest.raises(ValidationError):
        PerfTestConfig(
            targets={
                "baseline": TargetConfig(
                    base_url="http://localhost:8000/v1",
                    model="test",
                )
            },
            workload=WorkloadConfig(
                duration_seconds=60,
                max_concurrency=32,
                prompt_sets=[
                    PromptSet(name="test", weight=100, prompts=["p1"])
                ],
            ),
            comparison=ComparisonConfig(fail_on_regression=True),
        )


def test_slo_config_validation():
    """Test SLO validation."""
    slo = SLOConfig(
        p95_latency_ms=2500,
        ttft_ms=1200,
        output_tokens_per_sec=40,
        error_rate_percent=1.0,
    )
    assert slo.p95_latency_ms == 2500

    # Negative value
    with pytest.raises(ValidationError):
        SLOConfig(p95_latency_ms=-100)

    # Error rate > 100
    with pytest.raises(ValidationError):
        SLOConfig(error_rate_percent=150)
