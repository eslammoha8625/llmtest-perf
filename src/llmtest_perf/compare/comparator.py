"""Comparison engine for baseline vs candidate."""

from typing import Optional

from llmtest_perf.config.models import ComparisonConfig, PerfTestConfig, SLOConfig
from llmtest_perf.engine.metrics import AggregatedMetrics, PercentileStats, PromptSetMetrics, calculate_percentiles
from llmtest_perf.engine.results import TestResults
from llmtest_perf.compare.verdicts import (
    ComparisonVerdict,
    MetricComparison,
    VerdictStatus,
    calculate_delta_percent,
    check_regression,
)


class Comparator:
    """Compares baseline and candidate test results."""

    def __init__(self, config: PerfTestConfig) -> None:
        """Initialize comparator with config."""
        self.config = config
        self.comparison_config = config.comparison
        self.slo_config = config.slos

    def aggregate_metrics(self, results: TestResults) -> AggregatedMetrics:
        """Convert TestResults to AggregatedMetrics with percentiles."""
        latency_stats = calculate_percentiles(results.all_latencies)
        ttft_stats = calculate_percentiles(results.all_ttfts)

        # Calculate per-prompt-set metrics
        prompt_set_metrics = {}
        for name, ps_results in results.prompt_set_results.items():
            ps_latency = calculate_percentiles(ps_results.latencies)
            ps_ttft = calculate_percentiles(ps_results.ttfts)
            ps_output_mean = (
                sum(ps_results.output_token_counts) / len(ps_results.output_token_counts)
                if ps_results.output_token_counts
                else None
            )

            prompt_set_metrics[name] = PromptSetMetrics(
                name=name,
                total_requests=ps_results.total_requests,
                successful_requests=ps_results.successful_requests,
                failed_requests=ps_results.failed_requests,
                error_rate_percent=(
                    (ps_results.failed_requests / ps_results.total_requests * 100)
                    if ps_results.total_requests > 0
                    else 0.0
                ),
                latency=ps_latency,
                ttft=ps_ttft,
                output_tokens_mean=ps_output_mean,
            )

        return AggregatedMetrics(
            target_name=results.target_name,
            total_requests=results.total_requests,
            successful_requests=results.successful_requests,
            failed_requests=results.failed_requests,
            error_rate_percent=results.error_rate,
            duration_seconds=results.duration_seconds,
            requests_per_sec=results.requests_per_sec,
            latency=latency_stats,
            ttft=ttft_stats,
            total_output_tokens=results.total_output_tokens,
            output_tokens_per_sec=results.output_tokens_per_sec,
            error_breakdown=results.error_types,
            prompt_set_metrics=prompt_set_metrics,
        )

    def check_slo_compliance(self, metrics: AggregatedMetrics) -> list[MetricComparison]:
        """Check if metrics meet SLO thresholds."""
        comparisons: list[MetricComparison] = []

        if not self.slo_config:
            return comparisons

        # Check P95 latency
        if self.slo_config.p95_latency_ms and metrics.latency:
            actual = metrics.latency.p95
            threshold = self.slo_config.p95_latency_ms
            is_violation = actual > threshold
            comparisons.append(
                MetricComparison(
                    metric_name="P95 Latency",
                    baseline_value=threshold,
                    candidate_value=actual,
                    delta_percent=calculate_delta_percent(threshold, actual),
                    delta_absolute=actual - threshold,
                    is_regression=is_violation,
                    is_improvement=not is_violation,
                    message=f"P95 latency: {actual:.2f}ms vs SLO {threshold:.2f}ms",
                )
            )

        # Check TTFT
        if self.slo_config.ttft_ms and metrics.ttft:
            actual = metrics.ttft.p95
            threshold = self.slo_config.ttft_ms
            is_violation = actual > threshold
            comparisons.append(
                MetricComparison(
                    metric_name="TTFT",
                    baseline_value=threshold,
                    candidate_value=actual,
                    delta_percent=calculate_delta_percent(threshold, actual),
                    delta_absolute=actual - threshold,
                    is_regression=is_violation,
                    is_improvement=not is_violation,
                    message=f"TTFT: {actual:.2f}ms vs SLO {threshold:.2f}ms",
                )
            )

        # Check output tokens per second
        if self.slo_config.output_tokens_per_sec:
            actual = metrics.output_tokens_per_sec
            threshold = self.slo_config.output_tokens_per_sec
            is_violation = actual < threshold
            comparisons.append(
                MetricComparison(
                    metric_name="Output Tokens/Sec",
                    baseline_value=threshold,
                    candidate_value=actual,
                    delta_percent=calculate_delta_percent(threshold, actual),
                    delta_absolute=actual - threshold,
                    is_regression=is_violation,
                    is_improvement=not is_violation,
                    message=f"Output tokens/sec: {actual:.2f} vs SLO {threshold:.2f}",
                )
            )

        # Check error rate
        if self.slo_config.error_rate_percent is not None:
            actual = metrics.error_rate_percent
            threshold = self.slo_config.error_rate_percent
            is_violation = actual > threshold
            comparisons.append(
                MetricComparison(
                    metric_name="Error Rate",
                    baseline_value=threshold,
                    candidate_value=actual,
                    delta_percent=calculate_delta_percent(threshold, actual) if threshold > 0 else None,
                    delta_absolute=actual - threshold,
                    is_regression=is_violation,
                    is_improvement=not is_violation,
                    message=f"Error rate: {actual:.2f}% vs SLO {threshold:.2f}%",
                )
            )

        return comparisons

    def compare(
        self, baseline_results: TestResults, candidate_results: TestResults
    ) -> ComparisonVerdict:
        """
        Compare baseline and candidate results.

        Returns:
            ComparisonVerdict with detailed comparison
        """
        baseline_metrics = self.aggregate_metrics(baseline_results)
        candidate_metrics = self.aggregate_metrics(candidate_results)

        comparisons: list[MetricComparison] = []

        # P95 Latency
        if baseline_metrics.latency and candidate_metrics.latency:
            bl_val = baseline_metrics.latency.p95
            ca_val = candidate_metrics.latency.p95
            threshold = (
                self.comparison_config.max_p95_latency_regression_percent
                if self.comparison_config
                else None
            )
            is_reg, is_imp, msg = check_regression(
                "P95 Latency", bl_val, ca_val, threshold, higher_is_better=False
            )
            comparisons.append(
                MetricComparison(
                    metric_name="P95 Latency (ms)",
                    baseline_value=bl_val,
                    candidate_value=ca_val,
                    delta_percent=calculate_delta_percent(bl_val, ca_val),
                    delta_absolute=ca_val - bl_val,
                    is_regression=is_reg,
                    is_improvement=is_imp,
                    message=msg,
                )
            )

        # TTFT
        if baseline_metrics.ttft and candidate_metrics.ttft:
            bl_val = baseline_metrics.ttft.p95
            ca_val = candidate_metrics.ttft.p95
            threshold = (
                self.comparison_config.max_ttft_regression_percent
                if self.comparison_config
                else None
            )
            is_reg, is_imp, msg = check_regression(
                "TTFT", bl_val, ca_val, threshold, higher_is_better=False
            )
            comparisons.append(
                MetricComparison(
                    metric_name="TTFT (ms)",
                    baseline_value=bl_val,
                    candidate_value=ca_val,
                    delta_percent=calculate_delta_percent(bl_val, ca_val),
                    delta_absolute=ca_val - bl_val,
                    is_regression=is_reg,
                    is_improvement=is_imp,
                    message=msg,
                )
            )

        # Output tokens per second
        bl_val = baseline_metrics.output_tokens_per_sec
        ca_val = candidate_metrics.output_tokens_per_sec
        threshold = (
            self.comparison_config.max_output_tokens_per_sec_drop_percent
            if self.comparison_config
            else None
        )
        is_reg, is_imp, msg = check_regression(
            "Output Tokens/Sec", bl_val, ca_val, threshold, higher_is_better=True
        )
        comparisons.append(
            MetricComparison(
                metric_name="Output Tokens/Sec",
                baseline_value=bl_val,
                candidate_value=ca_val,
                delta_percent=calculate_delta_percent(bl_val, ca_val),
                delta_absolute=ca_val - bl_val if bl_val and ca_val else None,
                is_regression=is_reg,
                is_improvement=is_imp,
                message=msg,
            )
        )

        # Error rate
        bl_val = baseline_metrics.error_rate_percent
        ca_val = candidate_metrics.error_rate_percent
        threshold = (
            self.comparison_config.max_error_rate_increase_percent
            if self.comparison_config
            else None
        )
        is_reg, is_imp, msg = check_regression(
            "Error Rate", bl_val, ca_val, threshold, higher_is_better=False
        )
        comparisons.append(
            MetricComparison(
                metric_name="Error Rate (%)",
                baseline_value=bl_val,
                candidate_value=ca_val,
                delta_percent=calculate_delta_percent(bl_val, ca_val) if bl_val > 0 else None,
                delta_absolute=ca_val - bl_val,
                is_regression=is_reg,
                is_improvement=is_imp,
                message=msg,
            )
        )

        # Determine overall verdict
        has_regressions = any(c.is_regression for c in comparisons)

        if has_regressions:
            status = VerdictStatus.FAIL
            summary = f"Performance regression detected ({sum(1 for c in comparisons if c.is_regression)} metrics)"
            recommendation = "DO NOT PROMOTE - Fix regressions before deploying"
        else:
            status = VerdictStatus.PASS
            improvements = sum(1 for c in comparisons if c.is_improvement)
            summary = f"No regressions detected ({improvements} improvements)"
            recommendation = "SAFE TO PROMOTE"

        return ComparisonVerdict(
            status=status,
            baseline_target=baseline_results.target_name,
            candidate_target=candidate_results.target_name,
            metrics=comparisons,
            summary=summary,
            recommendation=recommendation,
        )
