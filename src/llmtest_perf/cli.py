"""Command-line interface for llmtest-perf."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from llmtest_perf.compare.comparator import Comparator
from llmtest_perf.config import ConfigError, load_config
from llmtest_perf.config.loader import validate_config
from llmtest_perf.engine.runner import WorkloadRunner
from llmtest_perf.reporting.console import ConsoleReporter
from llmtest_perf.reporting.html_report import HTMLReporter
from llmtest_perf.reporting.json_report import JSONReporter

app = typer.Typer(
    help="llmtest-perf - Performance validation and regression testing for LLM inference"
)
console = Console()
err_console = Console(stderr=True)


@app.command()
def run(
    config_path: str = typer.Argument(..., help="Path to YAML configuration file"),
    target: Optional[str] = typer.Option(
        None, "--target", "-t", help="Specific target to test (default: all targets)"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress console output"
    ),
) -> None:
    """
    Run performance test workload.

    Example:
        llmtest-perf run config.yaml
        llmtest-perf run config.yaml --target baseline
        llmtest-perf run config.yaml --quiet
    """
    config_file = Path(config_path)

    if not config_file.exists():
        err_console.print(f"[red]Error:[/red] Configuration file not found: {config_file}")
        raise typer.Exit(1)

    try:
        # Load config
        config = load_config(config_file)

        if not quiet:
            console.print(f"[cyan]Loading configuration from {config_file}[/cyan]")
            console.print(f"[dim]Duration: {config.workload.duration_seconds}s, "
                         f"Concurrency: {config.workload.max_concurrency}, "
                         f"Streaming: {config.workload.stream}[/dim]\n")

        # Filter targets if specified
        if target:
            if target not in config.targets:
                err_console.print(f"[red]Error:[/red] Target '{target}' not found in config")
                raise typer.Exit(1)
            config.targets = {target: config.targets[target]}

        # Run workload
        runner = WorkloadRunner(config)
        results = asyncio.run(runner.run_all_targets())

        # Report results
        console_reporter = ConsoleReporter()
        json_reporter = JSONReporter()
        html_reporter = HTMLReporter()
        comparator = Comparator(config)

        for target_name, test_results in results.items():
            metrics = comparator.aggregate_metrics(test_results)

            # Console output
            if not quiet and config.reporting.console:
                console_reporter.report_single_target(metrics)

            # JSON output
            if config.reporting.json_path:
                json_path = config.reporting.json_path.replace("{target}", target_name)
                json_reporter.save_single_target(metrics, json_path)
                if not quiet:
                    console.print(f"\n[green]JSON report saved:[/green] {json_path}")

            # HTML output
            if config.reporting.html_path:
                html_path = config.reporting.html_path.replace("{target}", target_name)
                html_reporter.generate_single_target_report(metrics, html_path)
                if not quiet:
                    console.print(f"[green]HTML report saved:[/green] {html_path}")

            # SLO checking
            if config.slos:
                slo_results = comparator.check_slo_compliance(metrics)
                violations = [r for r in slo_results if r.is_regression]

                if violations:
                    err_console.print(f"\n[red]SLO Violations:[/red]")
                    for violation in violations:
                        err_console.print(f"  - {violation.message}")
                    raise typer.Exit(1)

    except ConfigError as e:
        err_console.print(f"[red]Configuration Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f"[red]Unexpected Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        raise typer.Exit(1)


@app.command()
def compare(
    config_path: str = typer.Argument(..., help="Path to YAML configuration file"),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress console output"
    ),
) -> None:
    """
    Run baseline vs candidate comparison.

    Requires config with both 'baseline' and 'candidate' targets.

    Example:
        llmtest-perf compare config.yaml
    """
    config_file = Path(config_path)

    if not config_file.exists():
        err_console.print(f"[red]Error:[/red] Configuration file not found: {config_file}")
        raise typer.Exit(1)

    try:
        # Load config
        config = load_config(config_file)

        # Validate comparison targets
        if "baseline" not in config.targets or "candidate" not in config.targets:
            err_console.print(
                "[red]Error:[/red] Comparison mode requires both 'baseline' and 'candidate' targets"
            )
            raise typer.Exit(1)

        if not quiet:
            console.print(f"[cyan]Running comparison from {config_file}[/cyan]")
            console.print(f"[dim]Baseline: {config.targets['baseline'].base_url}[/dim]")
            console.print(f"[dim]Candidate: {config.targets['candidate'].base_url}[/dim]\n")

        # Run workloads
        runner = WorkloadRunner(config)
        console_reporter = ConsoleReporter()

        if not quiet:
            console_reporter.report_progress("Running baseline workload...")

        results = asyncio.run(runner.run_all_targets())

        baseline_results = results["baseline"]
        candidate_results = results["candidate"]

        # Compare
        comparator = Comparator(config)
        baseline_metrics = comparator.aggregate_metrics(baseline_results)
        candidate_metrics = comparator.aggregate_metrics(candidate_results)
        verdict = comparator.compare(baseline_results, candidate_results)

        # Console output
        if not quiet and config.reporting.console:
            console_reporter.report_comparison(verdict)

        # JSON output
        if config.reporting.json_path:
            json_reporter = JSONReporter()
            json_reporter.save_comparison(
                verdict, baseline_metrics, candidate_metrics, config.reporting.json_path
            )
            if not quiet:
                console.print(f"\n[green]JSON report saved:[/green] {config.reporting.json_path}")

        # HTML output
        if config.reporting.html_path:
            html_reporter = HTMLReporter()
            html_reporter.generate_comparison_report(
                verdict, baseline_metrics, candidate_metrics, config.reporting.html_path
            )
            if not quiet:
                console.print(f"[green]HTML report saved:[/green] {config.reporting.html_path}")

        # Exit with error if comparison failed
        if config.comparison and config.comparison.fail_on_regression:
            if verdict.has_regressions():
                raise typer.Exit(1)

    except ConfigError as e:
        err_console.print(f"[red]Configuration Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f"[red]Unexpected Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        raise typer.Exit(1)


@app.command()
def validate(
    config_path: str = typer.Argument(..., help="Path to YAML configuration file"),
) -> None:
    """
    Validate configuration file.

    Example:
        llmtest-perf validate config.yaml
    """
    config_file = Path(config_path)

    if not config_file.exists():
        err_console.print(f"[red]Error:[/red] Configuration file not found: {config_file}")
        raise typer.Exit(1)

    is_valid, message = validate_config(config_file)

    if is_valid:
        console.print(f"[green]✓[/green] {message}")
    else:
        err_console.print(f"[red]✗ Validation failed:[/red]\n{message}")
        raise typer.Exit(1)


@app.command()
def init(
    name: str = typer.Argument("demo", help="Name of the demo config"),
) -> None:
    """
    Initialize a demo configuration file.

    Example:
        llmtest-perf init demo
        llmtest-perf init my-test
    """
    config_file = Path(f"{name}.yaml")

    if config_file.exists():
        err_console.print(f"[yellow]Warning:[/yellow] {config_file} already exists")
        raise typer.Exit(1)

    demo_config = """provider: openai_compatible

targets:
  baseline:
    base_url: "http://localhost:8000/v1"
    model: "gpt-3.5-turbo"
    api_key_env: "OPENAI_API_KEY"

  candidate:
    base_url: "http://localhost:8001/v1"
    model: "gpt-3.5-turbo"
    api_key_env: "OPENAI_API_KEY"

workload:
  duration_seconds: 60
  max_concurrency: 32
  ramp_up_seconds: 10
  stream: true

  prompt_sets:
    - name: short_qa
      weight: 40
      prompts:
        - "What is the capital of France?"
        - "Explain TCP vs UDP briefly."
        - "Summarize the purpose of DNS."
        - "What is the difference between REST and GraphQL?"

    - name: medium_reasoning
      weight: 30
      prompts:
        - "Explain how a hash table works internally."
        - "What are the tradeoffs between SQL and NoSQL databases?"
        - "Describe the CAP theorem and its implications."

    - name: structured_output
      weight: 30
      prompts:
        - "Return a JSON object with keys: summary, sentiment, topics for this text: The product launch was successful."
        - "Extract key entities from: Apple announced new MacBook Pro with M3 chip."

request:
  max_tokens: 256
  temperature: 0.0
  timeout_seconds: 60

slos:
  p95_latency_ms: 2500
  ttft_ms: 1200
  output_tokens_per_sec: 40
  error_rate_percent: 1.0

comparison:
  fail_on_regression: true
  max_p95_latency_regression_percent: 10
  max_ttft_regression_percent: 10
  max_output_tokens_per_sec_drop_percent: 10
  max_error_rate_increase_percent: 1

reporting:
  json: "artifacts/results.json"
  html: "artifacts/report.html"
  console: true
"""

    config_file.write_text(demo_config)
    console.print(f"[green]✓[/green] Created demo config: {config_file}")
    console.print("\nNext steps:")
    console.print(f"  1. Edit {config_file} to configure your endpoints")
    console.print(f"  2. Run: llmtest-perf run {config_file}")
    console.print(f"  3. Compare: llmtest-perf compare {config_file}")


if __name__ == "__main__":
    app()
