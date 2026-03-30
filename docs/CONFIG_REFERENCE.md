# Configuration Reference

Complete reference for llmtest-perf YAML configuration files.

## Table of Contents

- [Root Configuration](#root-configuration)
- [Targets](#targets)
- [Workload](#workload)
- [Prompt Sets](#prompt-sets)
- [Request Parameters](#request-parameters)
- [SLOs](#slos)
- [Comparison](#comparison)
- [Reporting](#reporting)
- [Complete Examples](#complete-examples)

---

## Root Configuration

```yaml
provider: openai_compatible  # Required: Provider type
targets: {...}               # Required: Deployment targets
workload: {...}              # Required: Workload configuration
request: {...}               # Optional: Request parameters
slos: {...}                  # Optional: SLO thresholds
comparison: {...}            # Optional: Comparison settings
reporting: {...}             # Optional: Output configuration
seed: 42                     # Optional: Random seed for reproducibility
```

### `provider`

**Type:** `string`
**Required:** Yes
**Options:** `"openai_compatible"`
**Description:** LLM provider type. Currently only OpenAI-compatible is supported.

**Future:** `anthropic`, `bedrock`, `azure`, `vertex`

---

## Targets

Define one or more deployment targets to test.

```yaml
targets:
  baseline:
    base_url: "http://localhost:8000/v1"
    model: "gpt-3.5-turbo"
    api_key_env: "OPENAI_API_KEY"
    headers: {}  # Optional

  candidate:
    base_url: "http://localhost:8001/v1"
    model: "gpt-4-turbo"
    api_key_env: "OPENAI_API_KEY"
```

### Target Fields

#### `base_url`

**Type:** `string`
**Required:** Yes
**Format:** Must start with `http://` or `https://`
**Description:** Base URL for the API endpoint. `/chat/completions` will be appended.

**Examples:**
```yaml
base_url: "https://api.openai.com/v1"
base_url: "http://localhost:8000/v1"
base_url: "https://api.together.xyz/v1"
```

#### `model`

**Type:** `string`
**Required:** Yes
**Description:** Model identifier passed to the API.

**Examples:**
```yaml
model: "gpt-3.5-turbo"
model: "gpt-4-turbo"
model: "meta-llama/Llama-2-70b-chat-hf"
```

#### `api_key_env`

**Type:** `string`
**Required:** No
**Default:** `"OPENAI_API_KEY"`
**Description:** Environment variable name containing the API key.

**Example:**
```yaml
api_key_env: "MY_CUSTOM_API_KEY"
```

Then run: `export MY_CUSTOM_API_KEY="your-key"`

#### `headers`

**Type:** `object`
**Required:** No
**Description:** Additional HTTP headers to send with requests.

**Example:**
```yaml
headers:
  X-Custom-Auth: "Bearer xyz"
  X-Request-ID: "test-run-123"
```

---

## Workload

Configure test execution parameters.

```yaml
workload:
  duration_seconds: 60
  max_concurrency: 32
  ramp_up_seconds: 10
  stream: true
  prompt_sets: [...]
```

### `duration_seconds`

**Type:** `integer`
**Required:** Yes
**Range:** `1` to `unlimited`
**Description:** How long to run the test (in seconds).

**Recommendations:**
- Development/testing: 10-30 seconds
- Pre-deployment validation: 60-300 seconds (1-5 minutes)
- Stress testing: 600+ seconds (10+ minutes)

### `max_concurrency`

**Type:** `integer`
**Required:** Yes
**Range:** `1` to `1000`
**Description:** Maximum number of concurrent requests.

**How to choose:**
- Match production peak concurrency
- For stress testing, use 2-3x production peak
- Start low (8-16) for initial testing

**Example:**
```yaml
max_concurrency: 32  # 32 simultaneous requests
```

### `ramp_up_seconds`

**Type:** `integer`
**Required:** No
**Default:** `0`
**Range:** `0` to `duration_seconds - 1`
**Description:** Gradual ramp-up period before reaching max concurrency.

**Why use ramp-up:**
- Avoid cold-start bias
- Prevent connection pool exhaustion
- More realistic traffic pattern

**Example:**
```yaml
duration_seconds: 60
max_concurrency: 32
ramp_up_seconds: 10  # Ramp from 1 to 32 over 10 seconds
```

### `stream`

**Type:** `boolean`
**Required:** No
**Default:** `true`
**Description:** Use streaming responses (captures TTFT).

**When to use:**
- `true`: For user-facing applications, chatbots, assistants
- `false`: For batch processing, non-interactive use cases

### `prompt_sets`

**Type:** `array`
**Required:** Yes
**Description:** Weighted collections of prompts. See [Prompt Sets](#prompt-sets).

---

## Prompt Sets

Define realistic workloads with weighted prompt collections.

```yaml
prompt_sets:
  - name: short_qa
    weight: 60
    prompts:
      - "What is machine learning?"
      - "Explain neural networks."

  - name: long_analysis
    weight: 30
    prompts:
      - "Analyze this document: ..."

  - name: edge_cases
    weight: 10
    prompts:
      - "Complex multi-step reasoning..."
```

### `name`

**Type:** `string`
**Required:** Yes
**Description:** Identifier for this prompt set. Used in per-set metrics breakdown.

### `weight`

**Type:** `integer`
**Required:** Yes
**Range:** `1` to `100`
**Description:** Relative weight for prompt selection.

**How it works:**
- Weights don't need to sum to 100
- `weight: 60` with `weight: 40` = 60/40 = 60% vs 40%
- `weight: 3` with `weight: 1` = 75% vs 25%

**Example:**
```yaml
- name: common_queries
  weight: 80  # 80% of traffic

- name: rare_queries
  weight: 20  # 20% of traffic
```

### `prompts`

**Type:** `array` of `string`
**Required:** Yes
**Min items:** `1`
**Description:** List of prompts in this set. One is randomly selected per request.

**Best practices:**
- Use real production queries (anonymized)
- Include variety within each set
- Keep prompts representative of the workload type

---

## Request Parameters

OpenAI API parameters for requests.

```yaml
request:
  max_tokens: 256
  temperature: 0.0
  timeout_seconds: 60
  top_p: null  # Optional
```

### `max_tokens`

**Type:** `integer`
**Required:** No
**Default:** `256`
**Range:** `1` to `4096`
**Description:** Maximum tokens to generate per response.

### `temperature`

**Type:** `float`
**Required:** No
**Default:** `0.0`
**Range:** `0.0` to `2.0`
**Description:** Sampling temperature. Use `0.0` for deterministic testing.

### `timeout_seconds`

**Type:** `integer`
**Required:** No
**Default:** `60`
**Range:** `1` to `600`
**Description:** Request timeout in seconds.

**Recommendations:**
- Interactive: 10-30 seconds
- Long-form generation: 60-120 seconds

### `top_p`

**Type:** `float` or `null`
**Required:** No
**Default:** `null`
**Range:** `0.0` to `1.0`
**Description:** Nucleus sampling parameter.

---

## SLOs

Service Level Objective thresholds. Tests fail if SLOs are violated.

```yaml
slos:
  p95_latency_ms: 2500
  ttft_ms: 1200
  output_tokens_per_sec: 40
  error_rate_percent: 1.0
```

All fields are optional. Only specified SLOs are checked.

### `p95_latency_ms`

**Type:** `float`
**Range:** `> 0`
**Description:** Maximum acceptable P95 latency in milliseconds.

**Example:**
```yaml
p95_latency_ms: 2500  # P95 must be under 2.5 seconds
```

### `ttft_ms`

**Type:** `float`
**Range:** `> 0`
**Description:** Maximum acceptable P95 TTFT in milliseconds.

**Example:**
```yaml
ttft_ms: 1000  # Streaming must start within 1 second
```

### `output_tokens_per_sec`

**Type:** `float`
**Range:** `> 0`
**Description:** Minimum acceptable token throughput.

**Example:**
```yaml
output_tokens_per_sec: 40  # Must sustain 40 tokens/second
```

### `error_rate_percent`

**Type:** `float`
**Range:** `0.0` to `100.0`
**Description:** Maximum acceptable error rate percentage.

**Example:**
```yaml
error_rate_percent: 1.0  # Max 1% errors allowed
```

---

## Comparison

Settings for baseline vs candidate comparison mode.

```yaml
comparison:
  fail_on_regression: true
  max_p95_latency_regression_percent: 10
  max_ttft_regression_percent: 10
  max_output_tokens_per_sec_drop_percent: 10
  max_error_rate_increase_percent: 1
```

**Note:** Comparison mode requires `baseline` and `candidate` targets.

### `fail_on_regression`

**Type:** `boolean`
**Required:** No
**Default:** `true`
**Description:** Exit with error code 1 if regressions detected.

### `max_p95_latency_regression_percent`

**Type:** `float`
**Range:** `>= 0`
**Description:** Maximum allowed P95 latency increase percentage.

**Example:**
```yaml
max_p95_latency_regression_percent: 10
# Fail if candidate P95 is >10% slower than baseline
```

### `max_ttft_regression_percent`

**Type:** `float`
**Range:** `>= 0`
**Description:** Maximum allowed TTFT increase percentage.

### `max_output_tokens_per_sec_drop_percent`

**Type:** `float`
**Range:** `>= 0`
**Description:** Maximum allowed token throughput decrease percentage.

### `max_error_rate_increase_percent`

**Type:** `float`
**Range:** `>= 0`
**Description:** Maximum allowed error rate increase percentage.

**Example:**
```yaml
max_error_rate_increase_percent: 0.5
# Fail if candidate error rate increases by >0.5 percentage points
# e.g., baseline 0.2% → candidate 0.8% = +0.6pp = FAIL
```

---

## Reporting

Output configuration.

```yaml
reporting:
  json: "artifacts/results.json"
  html: "artifacts/report.html"
  console: true
```

### `json`

**Type:** `string` or `null`
**Required:** No
**Description:** Path to save JSON report.

**Supports templating:**
```yaml
json: "artifacts/{target}-results.json"
# Becomes: artifacts/baseline-results.json
```

### `html`

**Type:** `string` or `null`
**Required:** No
**Description:** Path to save HTML report.

**Supports templating:**
```yaml
html: "artifacts/{target}-report.html"
```

### `console`

**Type:** `boolean`
**Required:** No
**Default:** `true`
**Description:** Print results to console.

---

## Complete Examples

### Example 1: Simple Single-Target Test

```yaml
provider: openai_compatible

targets:
  production:
    base_url: "https://api.openai.com/v1"
    model: "gpt-3.5-turbo"
    api_key_env: "OPENAI_API_KEY"

workload:
  duration_seconds: 30
  max_concurrency: 8
  stream: true

  prompt_sets:
    - name: queries
      weight: 100
      prompts:
        - "What is AI?"
        - "Explain ML."

request:
  max_tokens: 100
  temperature: 0.0

slos:
  p95_latency_ms: 3000
  error_rate_percent: 2.0

reporting:
  console: true
```

### Example 2: Baseline vs Candidate Comparison

```yaml
provider: openai_compatible

targets:
  baseline:
    base_url: "http://old-cluster.internal/v1"
    model: "llama-2-70b"

  candidate:
    base_url: "http://new-cluster.internal/v1"
    model: "llama-2-70b"

workload:
  duration_seconds: 300
  max_concurrency: 32
  ramp_up_seconds: 30
  stream: true

  prompt_sets:
    - name: short
      weight: 60
      prompts: ["Quick queries..."]

    - name: long
      weight: 40
      prompts: ["Long context queries..."]

comparison:
  fail_on_regression: true
  max_p95_latency_regression_percent: 5
  max_output_tokens_per_sec_drop_percent: 5

reporting:
  json: "artifacts/comparison.json"
  html: "artifacts/comparison.html"

seed: 42
```

### Example 3: Stress Test

```yaml
provider: openai_compatible

targets:
  stress_test:
    base_url: "http://localhost:8000/v1"
    model: "test-model"

workload:
  duration_seconds: 600  # 10 minutes
  max_concurrency: 128   # High load
  ramp_up_seconds: 60    # Gradual ramp
  stream: true

  prompt_sets:
    - name: varied_load
      weight: 100
      prompts:
        - "Short"
        - "Medium length query here"
        - "Very long complex multi-step reasoning task..."

request:
  max_tokens: 512
  timeout_seconds: 120

slos:
  p95_latency_ms: 5000
  error_rate_percent: 5.0

reporting:
  json: "stress-test-results.json"
  html: "stress-test-report.html"
```

---

## Validation

Validate your config before running:

```bash
llmtest-perf validate config.yaml
```

**Common errors:**

- Invalid YAML syntax
- Missing required fields
- Invalid value ranges
- Invalid URLs
- Ramp-up >= duration

---

## Environment Variables

Reference environment variables in configs:

```yaml
targets:
  prod:
    base_url: "${PROD_API_URL}"  # Reads from env
    api_key_env: "PROD_API_KEY"
```

Then:
```bash
export PROD_API_URL="https://api.example.com/v1"
export PROD_API_KEY="your-key"
llmtest-perf run config.yaml
```

---

## Next Steps

- [Quick Start Guide](QUICK_START.md)
- [Metrics Explained](METRICS_EXPLAINED.md)
- [Main README](../README.md)
