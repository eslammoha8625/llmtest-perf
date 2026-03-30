"""Workload scheduling and prompt selection."""

import random
from typing import List, Optional

from llmtest_perf.config.models import PromptSet


class WorkloadScheduler:
    """Manages prompt selection and workload distribution."""

    def __init__(self, prompt_sets: List[PromptSet], seed: Optional[int] = None) -> None:
        """
        Initialize workload scheduler.

        Args:
            prompt_sets: List of weighted prompt sets
            seed: Random seed for reproducibility
        """
        self.prompt_sets = prompt_sets
        self.rng = random.Random(seed)

        # Build weighted selection lists
        self._build_selection_pool()

    def _build_selection_pool(self) -> None:
        """Build weighted pool for random selection."""
        self.selection_pool: List[tuple[str, str]] = []

        for prompt_set in self.prompt_sets:
            for prompt in prompt_set.prompts:
                # Add each prompt 'weight' times to the pool
                for _ in range(prompt_set.weight):
                    self.selection_pool.append((prompt_set.name, prompt))

    def select_prompt(self) -> tuple[str, str]:
        """
        Select a random prompt from the weighted pool.

        Returns:
            Tuple of (prompt_set_name, prompt)
        """
        return self.rng.choice(self.selection_pool)

    def calculate_concurrency(
        self, elapsed_seconds: float, ramp_up_seconds: int, max_concurrency: int
    ) -> int:
        """
        Calculate current concurrency based on ramp-up phase.

        Args:
            elapsed_seconds: Time elapsed since test start
            ramp_up_seconds: Ramp-up duration
            max_concurrency: Maximum concurrency target

        Returns:
            Current concurrency level
        """
        if ramp_up_seconds == 0 or elapsed_seconds >= ramp_up_seconds:
            return max_concurrency

        # Linear ramp-up
        progress = elapsed_seconds / ramp_up_seconds
        return max(1, int(max_concurrency * progress))
