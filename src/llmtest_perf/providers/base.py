"""Base provider interface for LLM inference."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional

import httpx


@dataclass
class RequestMetrics:
    """Metrics collected for a single request."""

    success: bool
    latency_ms: float
    ttft_ms: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def output_tokens_per_sec(self) -> Optional[float]:
        """Calculate output tokens per second."""
        if self.output_tokens and self.latency_ms:
            return (self.output_tokens / self.latency_ms) * 1000
        return None


class ProviderError(Exception):
    """Base exception for provider errors."""

    pass


class Provider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize provider.

        Args:
            base_url: Base URL for API endpoint
            model: Model identifier
            api_key: API authentication key
            headers: Additional HTTP headers
        """
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.headers = headers or {}

    @abstractmethod
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
        Send a request to the LLM endpoint and collect metrics.

        Args:
            prompt: Input prompt
            client: HTTP client for making requests
            stream: Whether to use streaming
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific parameters

        Returns:
            RequestMetrics with performance data

        Raises:
            ProviderError: If request fails
        """
        pass

    @abstractmethod
    def build_request_payload(
        self,
        prompt: str,
        stream: bool,
        max_tokens: int,
        temperature: float,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Build the request payload for this provider.

        Args:
            prompt: Input prompt
            stream: Whether to use streaming
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Request payload dictionary
        """
        pass
