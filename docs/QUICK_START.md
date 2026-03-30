# llmtest-perf Quick Start Guide

Get up and running with llmtest-perf in 5 minutes.

## Installation

```bash
pip install llmtest-perf
```

## Your First Test (3 Steps)

### Step 1: Generate Config

```bash
llmtest-perf init demo
```

This creates `demo.yaml` with example configuration.

### Step 2: Edit Endpoints

Open `demo.yaml` and update your endpoints:

```yaml
targets:
  baseline:
    base_url: "https://api.openai.com/v1"  # Your endpoint
    model: "gpt-3.5-turbo"                  # Your model
    api_key_env: "OPENAI_API_KEY"          # Env var name
```

### Step 3: Run Test

```bash
export OPENAI_API_KEY="your-api-key"
llmtest-perf run demo.yaml --target baseline
```

## Understanding Output

```
Results for: baseline

       Performance Summary
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Metric           ┃ Value      ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Total Requests   │ 1,847      │  ← Requests sent
│ Successful       │ 1,842      │  ← Completed successfully
│ Error Rate       │ 0.27%      │  ← Failed requests
│ Throughput       │ 30.7 req/s │  ← Requests per second
│ Token Throughput │ 45.2 tok/s │  ← Tokens per second
└──────────────────┴────────────┘

Latency Percentiles (ms)
┏━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Percentile ┃ Value   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━┩
│ P50        │ 1,842   │  ← 50% of requests faster
│ P95        │ 2,287   │  ← 95% of requests faster (key SLO metric)
│ P99        │ 2,891   │  ← 99% of requests faster
└────────────┴─────────┘
```

**Key Metrics:**
- **P95 Latency**: 95% of requests completed within this time
- **TTFT**: Time to first token (for streaming)
- **Token Throughput**: How many tokens/sec the system generates
- **Error Rate**: Percentage of failed requests

## Next Steps

### Compare Two Deployments

```bash
# Edit demo.yaml to add candidate target
llmtest-perf compare demo.yaml
```

### Validate Config

```bash
llmtest-perf validate demo.yaml
```

### Generate Reports

```yaml
# In your config
reporting:
  json: "results.json"    # Machine-readable
  html: "report.html"     # Human-readable
```

## Common Use Cases

### 1. Test Before Deploying New Model

```yaml
targets:
  baseline:
    model: "gpt-3.5-turbo"
  candidate:
    model: "gpt-4-turbo"
```

Run: `llmtest-perf compare config.yaml`

### 2. Validate Infrastructure Change

```yaml
targets:
  baseline:
    base_url: "http://old-cluster/v1"
  candidate:
    base_url: "http://new-cluster/v1"
```

### 3. Set SLO Gates

```yaml
slos:
  p95_latency_ms: 2500      # Must be under 2.5s
  error_rate_percent: 1.0   # Max 1% errors
```

Run: `llmtest-perf run config.yaml`
- Exit code 0: SLOs met
- Exit code 1: SLOs violated

## Getting Help

```bash
llmtest-perf --help
llmtest-perf run --help
llmtest-perf compare --help
```

**Full Documentation:** [README.md](../README.md)

**GitHub:** https://github.com/sazed5055/llmtest-perf

**Issues:** https://github.com/sazed5055/llmtest-perf/issues
