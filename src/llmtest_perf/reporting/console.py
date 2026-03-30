"""Console reporting with rich formatting."""

from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from llmtest_perf.compare.verdicts import ComparisonVerdict, VerdictStatus
from llmtest_perf.engine.metrics import AggregatedMetrics


class ConsoleReporter:
    """Reports results to console with rich formatting."""

    def __init__(self) -> None:
        """Initialize console reporter."""
        self.console = Console()

    def report_single_target(self, metrics: AggregatedMetrics) -> None:
        """Report results for a single target."""
        self.console.print(f"\n[bold cyan]Results for: {metrics.target_name}[/bold cyan]\n")

        # Summary table
        table = Table(title="Performance Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Requests", str(metrics.total_requests))
        table.add_row("Successful", str(metrics.successful_requests))
        table.add_row("Failed", str(metrics.failed_requests))
        table.add_row("Error Rate", f"{metrics.error_rate_percent:.2f}%")
        table.add_row("Duration", f"{metrics.duration_seconds:.2f}s")
        table.add_row("Throughput", f"{metrics.requests_per_sec:.2f} req/s")
        table.add_row("Token Throughput", f"{metrics.output_tokens_per_sec:.2f} tok/s")

        self.console.print(table)

        # Latency percentiles
        if metrics.latency:
            lat_table = Table(title="Latency Percentiles (ms)", show_header=True)
            lat_table.add_column("Percentile", style="cyan")
            lat_table.add_column("Value", style="green")

            lat_table.add_row("P50", f"{metrics.latency.p50:.2f}")
            lat_table.add_row("P90", f"{metrics.latency.p90:.2f}")
            lat_table.add_row("P95", f"{metrics.latency.p95:.2f}")
            lat_table.add_row("P99", f"{metrics.latency.p99:.2f}")
            lat_table.add_row("Mean", f"{metrics.latency.mean:.2f}")
            lat_table.add_row("Min", f"{metrics.latency.min:.2f}")
            lat_table.add_row("Max", f"{metrics.latency.max:.2f}")

            self.console.print(lat_table)

        # TTFT percentiles
        if metrics.ttft:
            ttft_table = Table(title="TTFT Percentiles (ms)", show_header=True)
            ttft_table.add_column("Percentile", style="cyan")
            ttft_table.add_column("Value", style="green")

            ttft_table.add_row("P50", f"{metrics.ttft.p50:.2f}")
            ttft_table.add_row("P90", f"{metrics.ttft.p90:.2f}")
            ttft_table.add_row("P95", f"{metrics.ttft.p95:.2f}")
            ttft_table.add_row("P99", f"{metrics.ttft.p99:.2f}")
            ttft_table.add_row("Mean", f"{metrics.ttft.mean:.2f}")

            self.console.print(ttft_table)

        # Error breakdown
        if metrics.error_breakdown:
            err_table = Table(title="Error Breakdown", show_header=True)
            err_table.add_column("Error Type", style="red")
            err_table.add_column("Count", style="yellow")

            for error_type, count in sorted(
                metrics.error_breakdown.items(), key=lambda x: x[1], reverse=True
            ):
                err_table.add_row(error_type, str(count))

            self.console.print(err_table)

    def report_comparison(self, verdict: ComparisonVerdict) -> None:
        """Report comparison results."""
        self.console.print(f"\n[bold cyan]Comparison: {verdict.baseline_target} vs {verdict.candidate_target}[/bold cyan]\n")

        # Comparison table
        table = Table(title="Metric Comparison", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Baseline", style="blue")
        table.add_column("Candidate", style="blue")
        table.add_column("Delta", style="yellow")
        table.add_column("Status", style="bold")

        for metric in verdict.metrics:
            bl_val = f"{metric.baseline_value:.2f}" if metric.baseline_value is not None else "N/A"
            ca_val = f"{metric.candidate_value:.2f}" if metric.candidate_value is not None else "N/A"
            delta = (
                f"{metric.delta_percent:+.1f}%"
                if metric.delta_percent is not None
                else "N/A"
            )

            if metric.is_regression:
                status = "[red]REGRESSION[/red]"
            elif metric.is_improvement:
                status = "[green]IMPROVEMENT[/green]"
            else:
                status = "[dim]OK[/dim]"

            table.add_row(metric.metric_name, bl_val, ca_val, delta, status)

        self.console.print(table)

        # Verdict panel
        if verdict.status == VerdictStatus.PASS:
            verdict_style = "bold green"
            border_style = "green"
        else:
            verdict_style = "bold red"
            border_style = "red"

        verdict_panel = Panel(
            f"[{verdict_style}]{verdict.status.value}[/{verdict_style}]\n\n"
            f"{verdict.summary}\n\n"
            f"[bold]Recommendation:[/bold] {verdict.recommendation}",
            title="Verdict",
            border_style=border_style,
        )

        self.console.print(verdict_panel)

    def report_progress(self, message: str) -> None:
        """Report progress message."""
        self.console.print(f"[dim]{message}[/dim]")
