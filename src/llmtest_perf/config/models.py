"""Pydantic models for configuration validation."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class TargetConfig(BaseModel):
    """Configuration for a deployment target."""

    base_url: str = Field(..., description="Base URL for the API endpoint")
    model: str = Field(..., description="Model identifier")
    api_key_env: str = Field(
        default="OPENAI_API_KEY", description="Environment variable for API key"
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None, description="Additional HTTP headers"
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v.rstrip("/")


class PromptSet(BaseModel):
    """A weighted set of prompts for workload generation."""

    name: str = Field(..., description="Identifier for this prompt set")
    weight: int = Field(..., ge=1, le=100, description="Relative weight (1-100)")
    prompts: List[str] = Field(..., min_length=1, description="List of prompts")

    @field_validator("prompts")
    @classmethod
    def validate_prompts(cls, v: List[str]) -> List[str]:
        """Ensure prompts are non-empty."""
        if not all(p.strip() for p in v):
            raise ValueError("All prompts must be non-empty strings")
        return v


class WorkloadConfig(BaseModel):
    """Workload execution configuration."""

    duration_seconds: int = Field(..., gt=0, description="Test duration in seconds")
    max_concurrency: int = Field(
        ..., ge=1, le=1000, description="Maximum concurrent requests"
    )
    ramp_up_seconds: int = Field(
        default=0, ge=0, description="Ramp-up period in seconds"
    )
    stream: bool = Field(default=True, description="Use streaming responses")
    prompt_sets: List[PromptSet] = Field(
        ..., min_length=1, description="Weighted prompt sets"
    )

    @model_validator(mode="after")
    def validate_ramp_up(self) -> "WorkloadConfig":
        """Ensure ramp-up is less than duration."""
        if self.ramp_up_seconds >= self.duration_seconds:
            raise ValueError("ramp_up_seconds must be less than duration_seconds")
        return self

    @model_validator(mode="after")
    def validate_weights(self) -> "WorkloadConfig":
        """Ensure weights sum to reasonable value."""
        total_weight = sum(ps.weight for ps in self.prompt_sets)
        if total_weight == 0:
            raise ValueError("Total weight of prompt sets must be greater than 0")
        return self


class RequestConfig(BaseModel):
    """Request parameters for LLM calls."""

    max_tokens: int = Field(default=256, ge=1, le=4096, description="Maximum tokens")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Temperature")
    timeout_seconds: int = Field(default=60, ge=1, le=600, description="Request timeout")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Top-p sampling")


class SLOConfig(BaseModel):
    """Service level objective thresholds."""

    p95_latency_ms: Optional[float] = Field(
        default=None, gt=0, description="P95 latency threshold in ms"
    )
    ttft_ms: Optional[float] = Field(
        default=None, gt=0, description="Time to first token threshold in ms"
    )
    output_tokens_per_sec: Optional[float] = Field(
        default=None, gt=0, description="Minimum output tokens per second"
    )
    error_rate_percent: Optional[float] = Field(
        default=None, ge=0, le=100, description="Maximum error rate percentage"
    )


class ComparisonConfig(BaseModel):
    """Comparison and regression detection settings."""

    fail_on_regression: bool = Field(
        default=True, description="Exit with error on regression"
    )
    max_p95_latency_regression_percent: Optional[float] = Field(
        default=None, ge=0, description="Max allowed P95 latency regression %"
    )
    max_ttft_regression_percent: Optional[float] = Field(
        default=None, ge=0, description="Max allowed TTFT regression %"
    )
    max_output_tokens_per_sec_drop_percent: Optional[float] = Field(
        default=None, ge=0, description="Max allowed output token/sec drop %"
    )
    max_error_rate_increase_percent: Optional[float] = Field(
        default=None, ge=0, description="Max allowed error rate increase %"
    )


class ReportingConfig(BaseModel):
    """Output reporting configuration."""

    json_path: Optional[str] = Field(default=None, description="Path to JSON output file", alias="json")
    html_path: Optional[str] = Field(default=None, description="Path to HTML output file", alias="html")
    console: bool = Field(default=True, description="Print console output")

    model_config = {"populate_by_name": True}


class PerfTestConfig(BaseModel):
    """Root configuration for performance tests."""

    provider: Literal["openai_compatible"] = Field(
        default="openai_compatible", description="Provider type"
    )
    targets: Dict[str, TargetConfig] = Field(..., description="Deployment targets")
    workload: WorkloadConfig = Field(..., description="Workload configuration")
    request: RequestConfig = Field(
        default_factory=RequestConfig, description="Request parameters"
    )
    slos: Optional[SLOConfig] = Field(default=None, description="SLO thresholds")
    comparison: Optional[ComparisonConfig] = Field(
        default=None, description="Comparison settings"
    )
    reporting: ReportingConfig = Field(
        default_factory=ReportingConfig, description="Reporting configuration"
    )
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: Dict[str, TargetConfig]) -> Dict[str, TargetConfig]:
        """Ensure at least one target is defined."""
        if not v:
            raise ValueError("At least one target must be defined")
        return v

    @model_validator(mode="after")
    def validate_comparison_targets(self) -> "PerfTestConfig":
        """Validate comparison mode requires baseline and candidate."""
        if self.comparison and self.comparison.fail_on_regression:
            if "baseline" not in self.targets or "candidate" not in self.targets:
                raise ValueError(
                    "Comparison mode requires both 'baseline' and 'candidate' targets"
                )
        return self
