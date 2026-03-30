"""JSON report generation."""

import json
from pathlib import Path
from typing import Any, Dict

from llmtest_perf.compare.verdicts import ComparisonVerdict
from llmtest_perf.engine.metrics import AggregatedMetrics, PercentileStats


class JSONReporter:
    """Generates JSON reports."""

    def percentile_stats_to_dict(self, stats: PercentileStats) -> Dict[str, Any]:
        """Convert PercentileStats to dictionary."""
        return {
            "p50": stats.p50,
            "p90": stats.p90,
            "p95": stats.p95,
            "p99": stats.p99,
            "mean": stats.mean,
            "min": stats.min,
            "max": stats.max,
            "count": stats.count,
        }

    def metrics_to_dict(self, metrics: AggregatedMetrics) -> Dict[str, Any]:
        """Convert AggregatedMetrics to dictionary."""
        return {
            "target_name": metrics.target_name,
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "failed_requests": metrics.failed_requests,
            "error_rate_percent": metrics.error_rate_percent,
            "duration_seconds": metrics.duration_seconds,
            "requests_per_sec": metrics.requests_per_sec,
            "total_output_tokens": metrics.total_output_tokens,
            "output_tokens_per_sec": metrics.output_tokens_per_sec,
            "latency": (
                self.percentile_stats_to_dict(metrics.latency)
                if metrics.latency
                else None
            ),
            "ttft": (
                self.percentile_stats_to_dict(metrics.ttft) if metrics.ttft else None
            ),
            "error_breakdown": metrics.error_breakdown,
            "prompt_set_metrics": {
                name: {
                    "total_requests": pm.total_requests,
                    "successful_requests": pm.successful_requests,
                    "failed_requests": pm.failed_requests,
                    "error_rate_percent": pm.error_rate_percent,
                    "latency": (
                        self.percentile_stats_to_dict(pm.latency) if pm.latency else None
                    ),
                    "ttft": self.percentile_stats_to_dict(pm.ttft) if pm.ttft else None,
                    "output_tokens_mean": pm.output_tokens_mean,
                }
                for name, pm in metrics.prompt_set_metrics.items()
            },
        }

    def save_single_target(
        self, metrics: AggregatedMetrics, output_path: str
    ) -> None:
        """Save single target results to JSON."""
        data = self.metrics_to_dict(metrics)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_comparison(
        self, verdict: ComparisonVerdict, baseline_metrics: AggregatedMetrics, candidate_metrics: AggregatedMetrics, output_path: str
    ) -> None:
        """Save comparison results to JSON."""
        data = {
            "verdict": {
                "status": verdict.status.value,
                "summary": verdict.summary,
                "recommendation": verdict.recommendation,
                "regression_count": verdict.regression_count(),
                "improvement_count": verdict.improvement_count(),
            },
            "metrics_comparison": [
                {
                    "metric_name": m.metric_name,
                    "baseline_value": m.baseline_value,
                    "candidate_value": m.candidate_value,
                    "delta_percent": m.delta_percent,
                    "delta_absolute": m.delta_absolute,
                    "is_regression": m.is_regression,
                    "is_improvement": m.is_improvement,
                    "message": m.message,
                }
                for m in verdict.metrics
            ],
            "baseline": self.metrics_to_dict(baseline_metrics),
            "candidate": self.metrics_to_dict(candidate_metrics),
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
