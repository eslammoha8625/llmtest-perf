"""Tests for workload scheduler."""

from llmtest_perf.config.models import PromptSet
from llmtest_perf.engine.scheduler import WorkloadScheduler


def test_scheduler_prompt_selection():
    """Test weighted prompt selection."""
    prompt_sets = [
        PromptSet(name="set1", weight=50, prompts=["p1", "p2"]),
        PromptSet(name="set2", weight=50, prompts=["p3", "p4"]),
    ]

    scheduler = WorkloadScheduler(prompt_sets, seed=42)

    # Select 100 prompts and verify distribution
    selections = [scheduler.select_prompt() for _ in range(100)]

    set1_count = sum(1 for name, _ in selections if name == "set1")
    set2_count = sum(1 for name, _ in selections if name == "set2")

    # Should be roughly equal with 50/50 weights
    assert set1_count > 0
    assert set2_count > 0


def test_scheduler_concurrency_calculation():
    """Test concurrency ramp-up calculation."""
    prompt_sets = [PromptSet(name="test", weight=100, prompts=["p1"])]
    scheduler = WorkloadScheduler(prompt_sets)

    # No ramp-up
    assert scheduler.calculate_concurrency(0, 0, 32) == 32
    assert scheduler.calculate_concurrency(10, 0, 32) == 32

    # With ramp-up
    assert scheduler.calculate_concurrency(0, 10, 32) == 1
    assert scheduler.calculate_concurrency(5, 10, 32) == 16
    assert scheduler.calculate_concurrency(10, 10, 32) == 32
    assert scheduler.calculate_concurrency(15, 10, 32) == 32


def test_scheduler_reproducibility():
    """Test that scheduler is reproducible with seed."""
    prompt_sets = [
        PromptSet(name="set1", weight=50, prompts=["p1", "p2"]),
        PromptSet(name="set2", weight=50, prompts=["p3"]),
    ]

    scheduler1 = WorkloadScheduler(prompt_sets, seed=42)
    scheduler2 = WorkloadScheduler(prompt_sets, seed=42)

    selections1 = [scheduler1.select_prompt() for _ in range(10)]
    selections2 = [scheduler2.select_prompt() for _ in range(10)]

    assert selections1 == selections2
