"""Results models for performance tests."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from llmtest_perf.providers.base import RequestMetrics


@dataclass
class PromptSetResults:
    """Results for a specific prompt set."""

    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    latencies: List[float] = field(default_factory=list)
    ttfts: List[float] = field(default_factory=list)
    output_token_counts: List[int] = field(default_factory=list)
    error_types: Dict[str, int] = field(default_factory=dict)


@dataclass
class TestResults:
    """Aggregated results for a single target test."""

    target_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    duration_seconds: float = 0.0

    # Per-request metrics
    all_latencies: List[float] = field(default_factory=list)
    all_ttfts: List[float] = field(default_factory=list)
    all_output_tokens: List[int] = field(default_factory=list)

    # Error tracking
    error_types: Dict[str, int] = field(default_factory=dict)

    # Per-prompt-set breakdown
    prompt_set_results: Dict[str, PromptSetResults] = field(default_factory=dict)

    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    @property
    def requests_per_sec(self) -> float:
        """Calculate request throughput."""
        if self.duration_seconds == 0:
            return 0.0
        return self.total_requests / self.duration_seconds

    @property
    def total_output_tokens(self) -> int:
        """Total output tokens generated."""
        return sum(self.all_output_tokens)

    @property
    def output_tokens_per_sec(self) -> float:
        """Calculate token throughput."""
        if self.duration_seconds == 0:
            return 0.0
        return self.total_output_tokens / self.duration_seconds

    def add_request_result(
        self, metrics: RequestMetrics, prompt_set_name: Optional[str] = None
    ) -> None:
        """Add a request result to the aggregate."""
        self.total_requests += 1

        if metrics.success:
            self.successful_requests += 1
            self.all_latencies.append(metrics.latency_ms)

            if metrics.ttft_ms is not None:
                self.all_ttfts.append(metrics.ttft_ms)

            if metrics.output_tokens is not None:
                self.all_output_tokens.append(metrics.output_tokens)
        else:
            self.failed_requests += 1
            if metrics.error_type:
                self.error_types[metrics.error_type] = (
                    self.error_types.get(metrics.error_type, 0) + 1
                )

        # Track per-prompt-set metrics
        if prompt_set_name:
            if prompt_set_name not in self.prompt_set_results:
                self.prompt_set_results[prompt_set_name] = PromptSetResults(
                    name=prompt_set_name
                )

            ps_results = self.prompt_set_results[prompt_set_name]
            ps_results.total_requests += 1

            if metrics.success:
                ps_results.successful_requests += 1
                ps_results.latencies.append(metrics.latency_ms)

                if metrics.ttft_ms is not None:
                    ps_results.ttfts.append(metrics.ttft_ms)

                if metrics.output_tokens is not None:
                    ps_results.output_token_counts.append(metrics.output_tokens)
            else:
                ps_results.failed_requests += 1
                if metrics.error_type:
                    ps_results.error_types[metrics.error_type] = (
                        ps_results.error_types.get(metrics.error_type, 0) + 1
                    )
