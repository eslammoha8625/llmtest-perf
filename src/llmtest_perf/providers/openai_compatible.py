"""OpenAI-compatible Chat Completions provider."""

import asyncio
import time
from typing import Any, Dict, Optional

import httpx

from llmtest_perf.providers.base import Provider, ProviderError, RequestMetrics


class OpenAICompatibleProvider(Provider):
    """Provider for OpenAI-compatible Chat Completions API."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize OpenAI-compatible provider."""
        super().__init__(base_url, model, api_key, headers)
        self.endpoint = f"{self.base_url}/chat/completions"

    def build_request_payload(
        self,
        prompt: str,
        stream: bool,
        max_tokens: int,
        temperature: float,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Build OpenAI Chat Completions request payload."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        # Add optional parameters
        if "top_p" in kwargs and kwargs["top_p"] is not None:
            payload["top_p"] = kwargs["top_p"]

        return payload

    async def send_request(
        self,
        prompt: str,
        client: httpx.AsyncClient,
        stream: bool = True,
        max_tokens: int = 256,
        temperature: float = 0.0,
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> RequestMetrics:
        """
        Send request to OpenAI-compatible endpoint.

        Collects latency, TTFT (for streaming), and token counts.
        """
        payload = self.build_request_payload(
            prompt, stream, max_tokens, temperature, **kwargs
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.headers,
        }

        start_time = time.perf_counter()
        ttft_ms: Optional[float] = None
        input_tokens: Optional[int] = None
        output_tokens: Optional[int] = None

        try:
            if stream:
                # Streaming request
                async with client.stream(
                    "POST",
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                ) as response:
                    response.raise_for_status()

                    first_token_received = False
                    token_count = 0

                    async for line in response.aiter_lines():
                        if not line.strip() or line.strip() == "data: [DONE]":
                            continue

                        if line.startswith("data: "):
                            chunk_data = line[6:]
                            try:
                                import json

                                chunk = json.loads(chunk_data)

                                # Record TTFT on first chunk
                                if not first_token_received:
                                    ttft_ms = (time.perf_counter() - start_time) * 1000
                                    first_token_received = True

                                # Count tokens from deltas
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta and delta["content"]:
                                        token_count += 1

                                # Extract usage if available (some providers send it)
                                if "usage" in chunk:
                                    input_tokens = chunk["usage"].get("prompt_tokens")
                                    output_tokens = chunk["usage"].get("completion_tokens")

                            except (json.JSONDecodeError, KeyError):
                                continue

                    # Estimate output tokens if not provided
                    if output_tokens is None and token_count > 0:
                        output_tokens = token_count

            else:
                # Non-streaming request
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )
                response.raise_for_status()
                data = response.json()

                # Extract usage
                if "usage" in data:
                    input_tokens = data["usage"].get("prompt_tokens")
                    output_tokens = data["usage"].get("completion_tokens")

            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

            return RequestMetrics(
                success=True,
                latency_ms=latency_ms,
                ttft_ms=ttft_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

        except httpx.TimeoutException:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return RequestMetrics(
                success=False,
                latency_ms=latency_ms,
                error_type="timeout",
                error_message="Request timed out",
            )

        except httpx.HTTPStatusError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return RequestMetrics(
                success=False,
                latency_ms=latency_ms,
                error_type=f"http_{e.response.status_code}",
                error_message=str(e),
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return RequestMetrics(
                success=False,
                latency_ms=latency_ms,
                error_type=type(e).__name__,
                error_message=str(e),
            )
