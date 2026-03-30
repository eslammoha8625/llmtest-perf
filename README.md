# llmtest-perf

**Production-quality performance validation and regression testing for LLM inference systems.**

![GitHub stars](https://img.shields.io/github/stars/sazed5055/llmtest-perf?style=social)
![PyPI](https://img.shields.io/pypi/v/llmtest-perf)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Install:** `pip install llmtest-perf`
**PyPI:** https://pypi.org/project/llmtest-perf/

---

## What is llmtest-perf?

**llmtest-perf** is a pytest-like performance validation framework for LLM inference systems. It helps engineering teams answer critical questions before deploying model or infrastructure changes:

- **Did latency regress** after upgrading to a new model version?
- **Did throughput improve or degrade** with the new runtime configuration?
- **What happened to TTFT** (time to first token) and token generation speed?
- **How does the system behave** under realistic mixed workloads?
- **Is this deployment safe to promote** based on our SLOs?

This is **not** a generic benchmark tool. It's a **release-gating and regression-testing framework** designed for CI/CD pipelines and production deployment validation.

---

## Key Features

- **Workload-aware testing** - Define realistic mixed workloads with weighted prompt sets
- **CI-friendly** - Pass/fail based on SLOs and regression thresholds
- **Comparison-first** - Built-in baseline vs candidate comparison mode
- **Developer-friendly** - Declarative YAML configs, rich console output
- **Practical metrics** - P50/P90/P95/P99 latency, TTFT, throughput, error rates
- **Async engine** - High-performance httpx-based async workload runner
- **Multiple outputs** - Console, JSON, and self-contained HTML reports
- **Extensible** - Clean provider abstraction (OpenAI-compatible first)

---

## Who is this for?

**llmtest-perf** is built for:

- **ML Engineers** validating model performance before deployment
- **Infrastructure Engineers** testing LLM serving optimizations
- **Platform Teams** implementing SLO-based release gates
- **DevOps/SRE** teams running performance regression tests in CI

---

## Installation

```bash
# Install from source
cd llmtest-perf
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

**Requirements:**
- Python 3.11+
- API access to an OpenAI-compatible endpoint

---

## Quick Start

### 1. Initialize a demo config

```bash
llmtest-perf init demo
```

This creates `demo.yaml` with example configuration.

### 2. Edit the config

Update the endpoints and API keys:

```yaml
targets:
  baseline:
    base_url: "http://localhost:8000/v1"
    model: "your-model"
    api_key_env: "OPENAI_API_KEY"

  candidate:
    base_url: "http://localhost:8001/v1"
    model: "your-model-v2"
    api_key_env: "OPENAI_API_KEY"
```

### 3. Run a single target

```bash
export OPENAI_API_KEY="your-key"
llmtest-perf run demo.yaml --target baseline
```

### 4. Run baseline vs candidate comparison

```bash
llmtest-perf compare demo.yaml
```

---

## Configuration

### Full Configuration Example

```yaml
provider: openai_compatible

targets:
  baseline:
    base_url: "http://localhost:8000/v1"
    model: "gpt-3.5-turbo"
    api_key_env: "OPENAI_API_KEY"

  candidate:
    base_url: "http://localhost:8001/v1"
    model: "gpt-4-turbo"
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

    - name: long_context
      weight: 30
      prompts:
        - "Summarize this architecture document: ..."

    - name: structured_output
      weight: 30
      prompts:
        - "Return JSON with keys: summary, sentiment for this text."

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

seed: 42  # For reproducible workloads
```

### Key Configuration Sections

**Targets** - Define baseline and/or candidate deployments
- `base_url`: OpenAI-compatible endpoint
- `model`: Model identifier
- `api_key_env`: Environment variable for API key

**Workload** - Configure test execution
- `duration_seconds`: How long to run the test
- `max_concurrency`: Maximum concurrent requests
- `ramp_up_seconds`: Gradual ramp-up period
- `stream`: Use streaming responses (captures TTFT)
- `prompt_sets`: Weighted collections of prompts

**Request** - LLM parameters
- `max_tokens`, `temperature`, `timeout_seconds`, `top_p`

**SLOs** - Absolute thresholds (optional)
- `p95_latency_ms`, `ttft_ms`, `output_tokens_per_sec`, `error_rate_percent`

**Comparison** - Regression detection (optional)
- `fail_on_regression`: Exit with error on regression
- `max_*_regression_percent`: Allowed regression thresholds

**Reporting** - Output configuration
- `json`, `html`, `console`

---

## CLI Commands

### `run` - Run performance test

```bash
# Run all targets
llmtest-perf run config.yaml

# Run specific target
llmtest-perf run config.yaml --target baseline

# Suppress console output
llmtest-perf run config.yaml --quiet
```

**Outputs:**
- Console summary (if enabled)
- JSON results (if configured)
- HTML report (if configured)
- Exit code 0 on success, 1 on SLO violation

### `compare` - Baseline vs candidate comparison

```bash
llmtest-perf compare config.yaml
```

**Requires:** Both `baseline` and `candidate` targets in config

**Outputs:**
- Side-by-side comparison table
- Regression/improvement detection
- Final verdict (PASS/FAIL)
- Exit code 0 if no regressions, 1 if regressions detected

### `validate` - Validate configuration

```bash
llmtest-perf validate config.yaml
```

Checks YAML syntax and schema validation without running tests.

### `init` - Initialize demo config

```bash
llmtest-perf init demo
```

Creates a demo configuration file to get started.

---

## Sample Output

### Console Output (Run)

```
Results for: baseline

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric           ┃ Value  ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Total Requests   │ 1,847  │
│ Successful       │ 1,842  │
│ Failed           │ 5      │
│ Error Rate       │ 0.27%  │
│ Duration         │ 60.12s │
│ Throughput       │ 30.7/s │
│ Token Throughput │ 45.2/s │
└──────────────────┴────────┘

┏━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Percentile ┃ Value   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━┩
│ P50        │ 1,842ms │
│ P90        │ 2,104ms │
│ P95        │ 2,287ms │
│ P99        │ 2,891ms │
└────────────┴─────────┘
```

### Console Output (Compare)

```
Comparison: baseline vs candidate

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric             ┃ Baseline ┃ Candidate ┃ Delta  ┃ Status      ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━┩
│ P95 Latency (ms)   │ 2287.45  │ 2612.38   │ +14.2% │ REGRESSION  │
│ TTFT (ms)          │ 1142.22  │ 1046.11   │ -8.4%  │ IMPROVEMENT │
│ Output Tokens/Sec  │ 45.23    │ 39.76     │ -12.1% │ REGRESSION  │
│ Error Rate (%)     │ 0.27     │ 0.32      │ +18.5% │ OK          │
└────────────────────┴──────────┴───────────┴────────┴─────────────┘

╭─────────────────────────────────────────╮
│              FAIL                       │
│                                         │
│ Performance regression detected (2      │
│ metrics)                                │
│                                         │
│ Recommendation: DO NOT PROMOTE - Fix    │
│ regressions before deploying            │
╰─────────────────────────────────────────╯
```

---

## Use Cases

### 1. Model Version Validation

Compare inference performance between model versions:

```yaml
targets:
  baseline:
    base_url: "https://api.example.com/v1"
    model: "gpt-3.5-turbo"

  candidate:
    base_url: "https://api.example.com/v1"
    model: "gpt-4-turbo"
```

Run: `llmtest-perf compare config.yaml`

### 2. Infrastructure Change Validation

Test serving optimizations or hardware changes:

```yaml
targets:
  baseline:
    base_url: "http://old-cluster.internal/v1"
    model: "llama-2-70b"

  candidate:
    base_url: "http://new-cluster.internal/v1"
    model: "llama-2-70b"
```

### 3. SLO Compliance Monitoring

Gate deployments on SLO compliance:

```yaml
slos:
  p95_latency_ms: 2000
  ttft_ms: 800
  error_rate_percent: 0.5

comparison:
  fail_on_regression: true
```

Integrate into CI: fails if SLOs violated or regressions detected.

### 4. Realistic Workload Testing

Model production traffic patterns:

```yaml
prompt_sets:
  - name: quick_questions
    weight: 60
    prompts: [...]

  - name: complex_analysis
    weight: 30
    prompts: [...]

  - name: code_generation
    weight: 10
    prompts: [...]
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: LLM Performance Tests

on:
  pull_request:
    paths:
      - 'models/**'
      - 'infrastructure/**'

jobs:
  perf-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install llmtest-perf
        run: |
          pip install -e .

      - name: Run performance comparison
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          llmtest-perf compare .github/perf-config.yaml

      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: perf-reports
          path: artifacts/
```

---

## Architecture

### Components

```
llmtest-perf/
├── config/          # YAML config loading and validation (Pydantic)
├── providers/       # LLM provider abstraction (OpenAI-compatible)
├── engine/          # Async workload runner, metrics, scheduling
├── compare/         # Baseline vs candidate comparison logic
├── reporting/       # Console, JSON, HTML report generation
└── cli.py           # Typer-based CLI
```

### Workload Engine

- **Async I/O**: httpx-based for high concurrency
- **Concurrency control**: Semaphore-based with configurable limits
- **Ramp-up**: Linear ramp-up to avoid cold-start bias
- **Streaming**: Captures TTFT when streaming is enabled
- **Reproducibility**: Optional random seed for deterministic workloads

### Metrics Collection

Per-request:
- End-to-end latency
- Time to first token (TTFT) for streaming
- Input/output token counts
- Error type and message

Aggregated:
- P50/P90/P95/P99 percentiles
- Mean, min, max
- Request throughput (req/sec)
- Token throughput (tok/sec)
- Error rate percentage
- Per-prompt-set breakdown

---

## Limitations

### Current Version

- **OpenAI-compatible only**: Currently supports OpenAI Chat Completions API format
- **HTTP-based**: No gRPC or other protocols yet
- **Single-region**: No multi-region testing
- **Token counting**: Relies on provider-reported token counts
- **No payload size limits**: Large prompts may need external file support

### Planned Improvements

See [Roadmap](#roadmap) section below.

---

## Roadmap

Future enhancements under consideration:

- **Additional providers**: Anthropic, Google, AWS Bedrock, Azure OpenAI
- **Advanced workloads**: Prompt templates, external prompt files, payload generation
- **Cost tracking**: Track API costs alongside performance
- **Historical trending**: Track metrics over time
- **Warmup phase**: Pre-test warmup to eliminate cold starts
- **Custom metrics**: Plugin system for custom metric collection
- **Distributed testing**: Multi-node workload generation
- **Real-time monitoring**: Live dashboard during test runs

---

## Development

### Setup

```bash
# Clone repo
git clone <repo-url>
cd llmtest-perf

# Install in development mode
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=llmtest_perf --cov-report=html

# Type checking
mypy src/llmtest_perf

# Linting
ruff check src/
```

### Project Structure

```
llmtest-perf/
├── src/llmtest_perf/      # Main package
│   ├── config/            # Configuration models
│   ├── engine/            # Workload execution
│   ├── providers/         # Provider implementations
│   ├── compare/           # Comparison logic
│   ├── reporting/         # Report generation
│   └── cli.py             # CLI interface
├── tests/                 # Test suite
├── examples/              # Example configs
├── artifacts/             # Generated reports (gitignored)
└── README.md
```

---

## Contributing

Contributions are welcome! Areas of interest:

- Additional provider implementations
- Performance optimizations
- Additional metrics and analysis
- Documentation improvements
- Bug reports and fixes

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Why llmtest-perf?

**llmtest-perf** complements [llmtest](https://github.com/yourusername/llmtest) (a correctness/safety testing framework) by focusing exclusively on **performance validation**. Together, they provide comprehensive testing for LLM applications:

- **llmtest**: Grounding, safety, prompt injection, behavioral regression
- **llmtest-perf**: Latency, throughput, TTFT, performance regression

Use both for complete release validation.

---

**Built for engineers who ship LLM systems to production.**
