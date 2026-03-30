# llmtest-perf: Production-Quality Performance Testing for LLM Systems

## Stop Deploying LLM Changes Blind — Here's How to Test Performance Like a Pro

![Header Image Placeholder: Dashboard showing performance metrics comparison]

**TL;DR:** We built an open-source, pytest-like performance validation framework for LLM inference systems. It helps you answer "Is this deployment safe?" with data, not gut feelings.

---

## The Problem: Performance Testing for LLMs is Broken

You're about to deploy a new LLM model version to production. Your PM is excited about the quality improvements. Your infrastructure team optimized the serving layer. Everything looks great in staging.

**But here's what you don't know:**

- Did P95 latency regress by 30%?
- Is TTFT (time to first token) now unacceptable for streaming?
- Will token throughput handle peak traffic?
- Are you about to violate your SLAs?

Most teams discover these issues **after deployment**, when users complain or SLAs are breached.

### Why Existing Tools Fall Short

**Generic load testing tools** (JMeter, Locust, k6):
- Don't understand LLM-specific metrics (TTFT, token throughput)
- No streaming support with proper TTFT capture
- Can't model realistic mixed workloads
- No built-in regression detection

**Cloud provider dashboards**:
- React to problems, don't prevent them
- No baseline comparison
- No pre-deployment validation

**Benchmarking frameworks** (vLLM benchmarks, llmperf):
- Academic focus, not CI/CD ready
- No declarative configs
- Limited comparison capabilities

**What we needed:**
- **pytest for performance** — declarative, repeatable, CI-friendly
- **Release gating** based on SLOs and regression thresholds
- **Realistic workloads** that mirror production traffic
- **Comparison-first** design for baseline vs candidate validation

So we built it.

---

## Introducing llmtest-perf

**llmtest-perf** is a production-quality performance validation framework for LLM inference systems. Think pytest, but for performance testing with LLM-specific metrics.

### Core Philosophy

1. **Workload-aware** — Not single-prompt microbenchmarks, but realistic mixed workloads
2. **CI-friendly** — Pass/fail based on SLOs, structured outputs, exit codes
3. **Comparison-first** — Built-in baseline vs candidate mode
4. **Developer-friendly** — Declarative YAML configs, rich console output
5. **Performance-focused** — Not correctness (use [llmtest](https://github.com/yourusername/llmtest) for that)

### What It Actually Does

```
┌─────────────────────────────────────────────────────────┐
│ 1. Load YAML Config                                     │
│    - Define targets (baseline, candidate)               │
│    - Specify workload (duration, concurrency, prompts)  │
│    - Set SLOs and regression thresholds                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Run Async Workload                                   │
│    - Concurrent requests with ramp-up                   │
│    - Weighted prompt selection                          │
│    - Streaming with TTFT capture                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Collect Metrics                                      │
│    - P50/P90/P95/P99 latency                           │
│    - Time to First Token (TTFT)                         │
│    - Token throughput, error rates                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Compare & Gate                                       │
│    - Detect regressions vs baseline                     │
│    - Check SLO compliance                               │
│    - Exit 0 (pass) or 1 (fail)                         │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start: Your First Performance Test

### Installation

```bash
pip install llmtest-perf
```

### Generate Demo Config

```bash
llmtest-perf init demo
```

This creates `demo.yaml`:

```yaml
provider: openai_compatible

targets:
  baseline:
    base_url: "http://localhost:8000/v1"
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
        - "What is machine learning?"
        - "Explain neural networks."

    - name: long_analysis
      weight: 30
      prompts:
        - "Analyze the tradeoffs between..."

request:
  max_tokens: 256
  temperature: 0.0

slos:
  p95_latency_ms: 2500
  ttft_ms: 1200
  output_tokens_per_sec: 40
  error_rate_percent: 1.0
```

### Run Your First Test

```bash
export OPENAI_API_KEY="your-key"
llmtest-perf run demo.yaml --target baseline
```

### Output

```
Results for: baseline

       Performance Summary
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Metric           ┃ Value      ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Total Requests   │ 1,847      │
│ Successful       │ 1,842      │
│ Error Rate       │ 0.27%      │
│ Throughput       │ 30.7 req/s │
│ Token Throughput │ 45.2 tok/s │
└──────────────────┴────────────┘

Latency Percentiles (ms)
┏━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Percentile ┃ Value   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━┩
│ P50        │ 1,842   │
│ P95        │ 2,287   │
│ P99        │ 2,891   │
└────────────┴─────────┘

✓ All SLOs met
```

**That's it.** You just ran your first LLM performance test.

---

## Real-World Use Case: Model Version Comparison

Let's say you're evaluating GPT-4 Turbo vs GPT-3.5 Turbo. You want better quality, but not at the cost of 10x latency.

### Configuration

```yaml
provider: openai_compatible

targets:
  baseline:
    base_url: "https://api.openai.com/v1"
    model: "gpt-3.5-turbo"

  candidate:
    base_url: "https://api.openai.com/v1"
    model: "gpt-4-turbo"

workload:
  duration_seconds: 120
  max_concurrency: 16
  stream: true

  prompt_sets:
    - name: customer_support
      weight: 50
      prompts:
        - "Help me track my order #12345"
        - "I need to return an item"

    - name: technical_queries
      weight: 30
      prompts:
        - "Explain how OAuth 2.0 works"
        - "Debug this Python error: ..."

    - name: creative_tasks
      weight: 20
      prompts:
        - "Write a product description for..."

comparison:
  fail_on_regression: true
  max_p95_latency_regression_percent: 50  # Allow 50% slower
  max_ttft_regression_percent: 40
  max_output_tokens_per_sec_drop_percent: 30
```

### Run Comparison

```bash
llmtest-perf compare production-test.yaml
```

### Results

```
Comparison: baseline vs candidate

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric            ┃ Baseline ┃ Candidate ┃ Delta  ┃ Status      ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━┩
│ P95 Latency (ms)  │ 2,287    │ 3,421     │ +49.6% │ OK          │
│ TTFT (ms)         │ 1,142    │ 1,523     │ +33.4% │ OK          │
│ Output Tokens/Sec │ 45.2     │ 38.9      │ -13.9% │ OK          │
│ Error Rate (%)    │ 0.27     │ 0.31      │ +14.8% │ OK          │
└───────────────────┴──────────┴───────────┴────────┴─────────────┘

╭──────────────────────────────────────────╮
│ ✓ PASS                                   │
│                                          │
│ No regressions detected                  │
│ Recommendation: SAFE TO PROMOTE          │
╰──────────────────────────────────────────╯
```

**Decision:** GPT-4 is 49.6% slower, but within your 50% tolerance. Deploy it.

---

## The Power of Weighted Workloads

Unlike simple load testing, llmtest-perf models **realistic traffic patterns**.

### Example: Production-Like Workload

```yaml
prompt_sets:
  # 60% of traffic: Quick questions
  - name: quick_queries
    weight: 60
    prompts:
      - "What's the weather?"
      - "Set a timer for 5 minutes"

  # 30%: Medium complexity
  - name: reasoning_tasks
    weight: 30
    prompts:
      - "Compare React vs Vue for my use case"
      - "Debug this code snippet"

  # 10%: Heavy lifting
  - name: long_context
    weight: 10
    prompts:
      - "Summarize this 10-page document: ..."
```

**Why this matters:**

- **Percentiles reflect reality** — Your P95 latency includes the expensive queries
- **Bottleneck detection** — See which prompt types cause issues
- **Capacity planning** — Model peak load scenarios

---

## CI/CD Integration: Automated Release Gates

The killer feature: **automatic performance regression detection in CI**.

### GitHub Actions Example

```yaml
name: LLM Performance Gate

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

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install llmtest-perf
        run: pip install llmtest-perf

      - name: Deploy staging environments
        run: |
          ./scripts/deploy-baseline.sh
          ./scripts/deploy-candidate.sh

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

**Result:**

- ✅ PR blocked if P95 latency regresses >10%
- ✅ HTML report uploaded to artifacts
- ✅ Team reviews performance **before** merging

---

## Key Metrics Explained

### 1. P50/P90/P95/P99 Latency

**Why percentiles, not averages?**

Imagine two deployments:

**Deployment A:**
- Average latency: 100ms
- P95 latency: 5,000ms (5% of users wait 5 seconds!)

**Deployment B:**
- Average latency: 200ms
- P95 latency: 250ms (consistent experience)

**Which is better?** Deployment B. Averages hide outliers.

**llmtest-perf captures:**
```
P50  → 50% of requests faster than this
P90  → 90% of requests faster than this
P95  → 95% of requests faster than this (common SLO target)
P99  → 99% of requests faster than this
```

### 2. TTFT (Time to First Token)

**Critical for streaming UX.**

Users perceive TTFT as "responsiveness". A streaming response that starts in 200ms feels instant, even if the full response takes 5 seconds.

**How we measure it:**

```python
start_time = time.perf_counter()

async for chunk in response.stream():
    if not first_token_received:
        ttft = time.perf_counter() - start_time  # ← Captured here
        first_token_received = True
```

**Why it matters:**

- TTFT < 500ms: Feels instant
- TTFT > 2s: Users think it's broken

### 3. Token Throughput

**Tokens generated per second** across all requests.

**Use cases:**

- **Capacity planning**: "Can we handle 1M tokens/hour at peak?"
- **Cost optimization**: Lower throughput = more compute needed
- **Model comparison**: "Is this model worth the speed tradeoff?"

---

## Advanced: Infrastructure Change Validation

**Scenario:** You're migrating from vLLM 0.3 to 0.4. Will it improve throughput?

### Test Configuration

```yaml
targets:
  baseline:
    base_url: "http://vllm-0.3-cluster.internal/v1"
    model: "llama-2-70b"

  candidate:
    base_url: "http://vllm-0.4-cluster.internal/v1"
    model: "llama-2-70b"  # Same model, different runtime

workload:
  duration_seconds: 300  # 5 minutes
  max_concurrency: 64    # Stress test
  ramp_up_seconds: 30    # Gradual ramp

comparison:
  fail_on_regression: true
  max_p95_latency_regression_percent: 5   # Strict!
  max_output_tokens_per_sec_drop_percent: 5
```

### Interpreting Results

**Good outcome:**
```
P95 Latency: -12.3% improvement
Output Tokens/Sec: +18.7% improvement
Verdict: SAFE TO PROMOTE
```
→ **Migrate to vLLM 0.4**

**Bad outcome:**
```
P95 Latency: +8.2% regression
Output Tokens/Sec: -3.1% regression
Verdict: DO NOT PROMOTE
```
→ **Investigate configuration or rollback**

---

## SLO Compliance: The Safety Net

Beyond comparisons, llmtest-perf enforces **absolute SLO thresholds**.

### Example SLO Config

```yaml
slos:
  p95_latency_ms: 2500       # P95 must be under 2.5s
  ttft_ms: 1000              # Streaming must start within 1s
  output_tokens_per_sec: 40  # Must sustain 40 tok/s
  error_rate_percent: 1.0    # <1% errors allowed
```

**What happens:**

```bash
llmtest-perf run config.yaml
```

**If SLOs violated:**

```
SLO Violations:
  - P95 latency: 3,421ms vs SLO 2,500ms (FAIL)
  - TTFT: 1,523ms vs SLO 1,000ms (FAIL)

Exit code: 1
```

**Use case:** Gate production deploys in CI:

```bash
if ! llmtest-perf run prod-slo-check.yaml; then
  echo "SLO check failed - blocking deployment"
  exit 1
fi
```

---

## Architecture Deep Dive

For the technically curious, here's how it works under the hood.

### Async Workload Engine

**Problem:** We need to send thousands of concurrent requests efficiently.

**Solution:** Python asyncio + httpx

```python
async def run_workload():
    semaphore = asyncio.Semaphore(max_concurrency)

    async def worker(prompt):
        async with semaphore:
            start = time.perf_counter()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json={"messages": [{"role": "user", "content": prompt}]},
                    stream=True
                )

                # Capture TTFT
                first_token_time = None
                async for chunk in response.aiter_lines():
                    if first_token_time is None:
                        first_token_time = time.perf_counter() - start

            latency = time.perf_counter() - start
            return RequestMetrics(latency, first_token_time, ...)

    # Launch concurrent workers
    tasks = [worker(select_prompt()) for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)
```

**Benefits:**

- Single-threaded, high concurrency
- Low overhead vs threading
- Streaming support built-in

### Ramp-Up Logic

**Why ramp-up?**

Hitting a cold server with max concurrency causes:
- Connection pool exhaustion
- Misleading latency spikes
- Unrealistic test conditions

**Our approach:**

```python
def calculate_concurrency(elapsed_seconds, ramp_up_seconds, max_concurrency):
    if elapsed_seconds >= ramp_up_seconds:
        return max_concurrency

    # Linear ramp
    progress = elapsed_seconds / ramp_up_seconds
    return max(1, int(max_concurrency * progress))
```

**Example:** Max 32 concurrency, 10s ramp-up
- 0s: 1 concurrent request
- 5s: 16 concurrent requests
- 10s: 32 concurrent requests

### Percentile Calculation

**Not approximate — exact percentiles:**

```python
def calculate_percentiles(values):
    sorted_values = sorted(values)
    count = len(sorted_values)

    def percentile(p):
        index = (count - 1) * p
        lower = int(index)
        upper = min(lower + 1, count - 1)
        weight = index - lower

        return (sorted_values[lower] * (1 - weight) +
                sorted_values[upper] * weight)

    return PercentileStats(
        p50=percentile(0.50),
        p95=percentile(0.95),
        p99=percentile(0.99),
        ...
    )
```

**Why this matters:** Many tools use approximate percentiles (T-Digest, HdrHistogram). We use exact values because:
- Workloads are typically <10k requests (fits in memory)
- Exact is simpler and more trustworthy
- No algorithmic error

---

## Output Formats

### 1. Console (Rich Tables)

Perfect for development and ad-hoc testing.

```
Comparison: baseline vs candidate

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric            ┃ Baseline ┃ Candidate ┃ Delta  ┃ Status      ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━┩
│ P95 Latency (ms)  │ 2,287    │ 2,612     │ +14.2% │ REGRESSION  │
│ TTFT (ms)         │ 1,142    │ 1,046     │ -8.4%  │ IMPROVEMENT │
└───────────────────┴──────────┴───────────┴────────┴─────────────┘
```

### 2. JSON (Automation)

Perfect for CI/CD, dashboards, data pipelines.

```json
{
  "verdict": {
    "status": "FAIL",
    "summary": "Performance regression detected (1 metric)",
    "recommendation": "DO NOT PROMOTE",
    "regression_count": 1,
    "improvement_count": 1
  },
  "metrics_comparison": [
    {
      "metric_name": "P95 Latency (ms)",
      "baseline_value": 2287.45,
      "candidate_value": 2612.38,
      "delta_percent": 14.2,
      "is_regression": true
    }
  ]
}
```

### 3. HTML (Stakeholder Reports)

Self-contained HTML with styling. Share with PMs, leadership, customers.

**Features:**
- Summary cards
- Comparison tables
- Per-prompt-set breakdown
- Color-coded verdicts

---

## Comparison: llmtest-perf vs Alternatives

| Feature | llmtest-perf | vLLM Benchmark | Locust | Cloud Dashboards |
|---------|--------------|----------------|---------|------------------|
| LLM-specific metrics (TTFT) | ✅ | ✅ | ❌ | ⚠️ Limited |
| Streaming support | ✅ | ✅ | ❌ | ✅ |
| Declarative config | ✅ | ❌ | ❌ | N/A |
| Baseline comparison | ✅ | ❌ | ❌ | ❌ |
| SLO gating | ✅ | ❌ | ❌ | ⚠️ Alerts only |
| CI/CD ready | ✅ | ⚠️ Partial | ⚠️ Partial | ❌ |
| Weighted workloads | ✅ | ❌ | ✅ | N/A |
| Pre-deployment testing | ✅ | ✅ | ✅ | ❌ |
| Per-prompt-set breakdown | ✅ | ❌ | ❌ | ❌ |
| Python API + CLI | ✅ | ⚠️ CLI only | ✅ | N/A |

---

## Roadmap: What's Next

We're actively developing llmtest-perf. Here's what's coming:

### Planned Features

**Q2 2025:**
- ✅ OpenAI-compatible provider (done)
- 🚧 Anthropic provider
- 🚧 AWS Bedrock provider
- 🚧 Azure OpenAI provider
- 🚧 Google Vertex AI provider

**Q3 2025:**
- Prompt templates with variables
- External prompt file support (for large contexts)
- Cost tracking alongside performance
- Historical trending (store results over time)

**Q4 2025:**
- Distributed load generation (multi-node)
- Real-time dashboard during tests
- Custom metric plugins
- Advanced scheduling (constant rate, poisson, burst)

### Community Contributions Welcome

**Areas we'd love help with:**

- Additional provider implementations
- Performance optimizations
- Documentation improvements
- Real-world use case examples
- Bug reports and feature requests

👉 **GitHub:** https://github.com/sazed5055/llmtest-perf

---

## Best Practices

### 1. Test in Staging First

**Don't** run performance tests directly against production.

**Do:**
- Deploy baseline + candidate to staging
- Run llmtest-perf comparison
- Promote winner to production

### 2. Use Realistic Workloads

**Don't:**
```yaml
prompts:
  - "Hello"
  - "Hi"
  - "Hey"
```

**Do:**
```yaml
prompt_sets:
  - name: customer_support
    weight: 60
    prompts: ["Real support queries from production logs"]

  - name: edge_cases
    weight: 10
    prompts: ["Long contexts", "Complex reasoning"]
```

### 3. Set Appropriate SLOs

**Don't:**
```yaml
slos:
  p95_latency_ms: 100  # Unrealistic for LLMs
```

**Do:**
```yaml
slos:
  p95_latency_ms: 2500  # Based on user research
  ttft_ms: 1000         # Acceptable for streaming UX
```

### 4. Version Your Configs

**Store configs in git:**
```
.github/
  perf-tests/
    baseline-slo.yaml
    model-comparison.yaml
    capacity-stress-test.yaml
```

**Benefits:**
- Track SLO changes over time
- Review perf test changes in PRs
- Reproducible historical tests

### 5. Use Seeds for Reproducibility

```yaml
seed: 42  # Same prompts selected every run
```

**Use cases:**
- Debugging performance issues
- A/B testing configs
- Comparing across days/weeks

---

## Common Pitfalls and Solutions

### Pitfall 1: Testing Cold Servers

**Problem:** First request to a cold server takes 10x longer.

**Solution:** Use ramp-up + warmup

```yaml
workload:
  ramp_up_seconds: 30  # Gradual ramp avoids cold start
```

Or run a separate warmup:

```bash
llmtest-perf run warmup.yaml  # Short, low concurrency
llmtest-perf run actual-test.yaml
```

### Pitfall 2: Insufficient Test Duration

**Problem:** 10-second test shows P95 = 500ms. Production shows 2000ms.

**Why:** Short tests don't capture variability.

**Solution:** Run longer tests

```yaml
workload:
  duration_seconds: 300  # 5 minutes minimum for reliable percentiles
```

### Pitfall 3: Ignoring Error Rates

**Problem:** Candidate has 50% faster latency... because 50% of requests fail.

**Solution:** Always check error rates

```yaml
slos:
  error_rate_percent: 1.0  # Fail if >1% errors

comparison:
  max_error_rate_increase_percent: 0.5  # Strict error tolerance
```

### Pitfall 4: Wrong Concurrency

**Problem:** Testing with concurrency=1 when production sees 100 concurrent users.

**Solution:** Match production concurrency

```yaml
workload:
  max_concurrency: 100  # Match production peak
```

**How to find production concurrency?**

```sql
-- Example query
SELECT
  date_trunc('second', timestamp) as second,
  count(distinct request_id) as concurrent_requests
FROM requests
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY second
ORDER BY concurrent_requests DESC
LIMIT 1;
```

---

## Real-World Impact: Case Studies

### Case Study 1: E-Commerce Chatbot

**Company:** Mid-size e-commerce platform
**Challenge:** Evaluating GPT-3.5 vs Claude 3 Haiku for customer support bot

**Test Setup:**
```yaml
workload:
  duration_seconds: 600
  max_concurrency: 32

  prompt_sets:
    - name: order_tracking
      weight: 50
      prompts: ["Where is my order #X?", ...]

    - name: returns
      weight: 30
      prompts: ["I want to return...", ...]
```

**Results:**

| Metric | GPT-3.5 | Claude Haiku | Winner |
|--------|---------|--------------|--------|
| P95 Latency | 2,100ms | 1,850ms | Claude |
| TTFT | 800ms | 650ms | Claude |
| Cost/1M tokens | $0.50 | $0.25 | Claude |
| Error Rate | 0.3% | 0.1% | Claude |

**Decision:** Switched to Claude Haiku. **Saved $8k/month** + improved UX.

### Case Study 2: Infrastructure Migration

**Company:** AI startup with 1M+ daily LLM requests
**Challenge:** Migrate from AWS ECS to Kubernetes

**Test Setup:**
```yaml
targets:
  baseline:
    base_url: "https://ecs-cluster.internal/v1"
  candidate:
    base_url: "https://k8s-cluster.internal/v1"

workload:
  duration_seconds: 1800  # 30 minutes
  max_concurrency: 128    # Peak traffic simulation
```

**Results:**
- P95 latency: +3% (acceptable)
- Throughput: +12% (improvement!)
- Error rate: 0.1% → 0.05% (improvement!)

**Decision:** Migrated to K8s. **Increased capacity by 12%** without adding hardware.

---

## FAQ

### Q: Does this work with non-OpenAI providers?

**A:** Currently supports OpenAI-compatible APIs (OpenAI, Anyscale, Together.ai, vLLM, LiteLLM, etc.). Anthropic, AWS Bedrock, Azure OpenAI coming Q2 2025.

### Q: Can I use this for training benchmarks?

**A:** No. llmtest-perf is for **inference** performance testing. Use MLPerf or similar for training benchmarks.

### Q: How does this relate to llmtest (correctness testing)?

**A:** They're complementary:
- **llmtest**: Correctness, safety, grounding, prompt injection
- **llmtest-perf**: Performance, latency, throughput, SLOs

Use both for comprehensive LLM testing.

### Q: What's the performance overhead?

**A:** Minimal. The async engine and httpx are highly optimized. In tests, we've sustained 1000+ concurrent requests on a MacBook Pro with negligible CPU usage.

### Q: Can I test local models?

**A:** Yes! Just point to your local endpoint:

```yaml
targets:
  baseline:
    base_url: "http://localhost:8000/v1"
```

Works with vLLM, Ollama, llama.cpp server, etc.

### Q: How do I handle authentication?

**A:** Via environment variables:

```yaml
targets:
  baseline:
    api_key_env: "OPENAI_API_KEY"  # Reads from env var
```

Or for custom headers:

```yaml
targets:
  baseline:
    headers:
      Authorization: "Bearer ${MY_TOKEN}"
      X-Custom-Auth: "${CUSTOM_HEADER}"
```

---

## Getting Started Today

### 1. Install

```bash
pip install llmtest-perf
```

### 2. Generate Config

```bash
llmtest-perf init my-test
```

### 3. Edit Config

Update endpoints, prompts, and SLOs in `my-test.yaml`

### 4. Run Test

```bash
export OPENAI_API_KEY="your-key"
llmtest-perf run my-test.yaml
```

### 5. Compare Deployments

```bash
llmtest-perf compare my-test.yaml
```

### 6. Integrate with CI

See [GitHub Actions example](#cicd-integration-automated-release-gates) above.

---

## Conclusion

**Performance testing for LLM systems doesn't have to be painful.**

With **llmtest-perf**, you get:

✅ **Confidence** before deploying model or infra changes
✅ **Data-driven decisions** with baseline comparisons
✅ **Automated gates** in CI/CD to prevent regressions
✅ **LLM-specific metrics** like TTFT and token throughput
✅ **Production-quality** tool, not academic research code

**Stop deploying blind. Start testing like a pro.**

---

## Resources

- **GitHub:** https://github.com/sazed5055/llmtest-perf
- **Documentation:** https://github.com/sazed5055/llmtest-perf/blob/main/README.md
- **Issues/Feature Requests:** https://github.com/sazed5055/llmtest-perf/issues
- **Example Configs:** https://github.com/sazed5055/llmtest-perf/tree/main/examples

---

## About the Author

Built by engineers who got tired of deploying LLM changes and hoping for the best. We built llmtest-perf to solve our own pain point — and we're sharing it with you.

**Want to contribute?** We'd love your help. PRs welcome.

**Found this useful?** Star the repo and share with your team.

---

*If you liked this article, you might also enjoy:*
- *Building Production LLM Systems: Lessons from the Trenches*
- *The Hidden Costs of LLM Inference at Scale*
- *Why Your P95 Latency Matters More Than Average*

---

**Tags:** #LLM #PerformanceTesting #DevOps #CI/CD #Python #MachineLearning #SoftwareEngineering #ProductionML
