"""Async workload runner for performance testing."""

import asyncio
import os
import time
from typing import Optional

import httpx

from llmtest_perf.config.models import PerfTestConfig, TargetConfig
from llmtest_perf.engine.results import TestResults
from llmtest_perf.engine.scheduler import WorkloadScheduler
from llmtest_perf.providers.base import Provider
from llmtest_perf.providers.openai_compatible import OpenAICompatibleProvider


class WorkloadRunner:
    """Runs performance test workloads against LLM endpoints."""

    def __init__(self, config: PerfTestConfig) -> None:
        """
        Initialize workload runner.

        Args:
            config: Performance test configuration
        """
        self.config = config

    def _create_provider(self, target_config: TargetConfig) -> Provider:
        """Create provider instance for target."""
        api_key = os.getenv(target_config.api_key_env, "")

        if self.config.provider == "openai_compatible":
            return OpenAICompatibleProvider(
                base_url=target_config.base_url,
                model=target_config.model,
                api_key=api_key,
                headers=target_config.headers,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    async def run_target(
        self, target_name: str, target_config: TargetConfig
    ) -> TestResults:
        """
        Run workload against a single target.

        Args:
            target_name: Name of the target
            target_config: Target configuration

        Returns:
            TestResults with collected metrics
        """
        provider = self._create_provider(target_config)
        scheduler = WorkloadScheduler(
            self.config.workload.prompt_sets, seed=self.config.seed
        )

        results = TestResults(target_name=target_name)

        # Create HTTP client
        async with httpx.AsyncClient() as client:
            start_time = time.perf_counter()
            end_time = start_time + self.config.workload.duration_seconds

            # Semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.config.workload.max_concurrency)

            # Track active tasks
            active_tasks: set[asyncio.Task[None]] = set()

            async def worker(prompt_set_name: str, prompt: str) -> None:
                """Worker coroutine for a single request."""
                async with semaphore:
                    metrics = await provider.send_request(
                        prompt=prompt,
                        client=client,
                        stream=self.config.workload.stream,
                        max_tokens=self.config.request.max_tokens,
                        temperature=self.config.request.temperature,
                        timeout=self.config.request.timeout_seconds,
                        top_p=self.config.request.top_p,
                    )

                    results.add_request_result(metrics, prompt_set_name)

            # Main workload loop
            while time.perf_counter() < end_time:
                elapsed = time.perf_counter() - start_time
                current_concurrency = scheduler.calculate_concurrency(
                    elapsed,
                    self.config.workload.ramp_up_seconds,
                    self.config.workload.max_concurrency,
                )

                # Launch new tasks up to current concurrency
                while len(active_tasks) < current_concurrency:
                    prompt_set_name, prompt = scheduler.select_prompt()
                    task = asyncio.create_task(worker(prompt_set_name, prompt))
                    active_tasks.add(task)
                    task.add_done_callback(active_tasks.discard)

                # Brief sleep to prevent tight loop
                await asyncio.sleep(0.01)

            # Wait for remaining tasks to complete
            if active_tasks:
                await asyncio.gather(*active_tasks, return_exceptions=True)

        results.duration_seconds = time.perf_counter() - start_time
        return results

    async def run_all_targets(self) -> dict[str, TestResults]:
        """
        Run workload against all configured targets.

        Returns:
            Dictionary mapping target names to results
        """
        tasks = {
            target_name: self.run_target(target_name, target_config)
            for target_name, target_config in self.config.targets.items()
        }

        completed = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), completed))
