# Understanding Performance Metrics

A deep dive into the metrics llmtest-perf collects and why they matter.

## Core Metrics

### 1. Latency Percentiles

**What:** How long requests take to complete.

**Why percentiles, not averages?**

Consider these two systems:

**System A:**
- Average latency: 100ms
- P95 latency: 5,000ms (5% of users wait 5 seconds!)
- P99 latency: 10,000ms

**System B:**
- Average latency: 200ms
- P95 latency: 250ms
- P99 latency: 300ms

**Which is better?** System B. Averages hide the bad user experiences.

**Percentiles explained:**

```
P50 (median)  → 50% of requests complete faster than this
P90           → 90% of requests complete faster than this
P95           → 95% of requests complete faster than this (common SLO target)
P99           → 99% of requests complete faster than this
```

**Industry standard:** P95 is typically used for SLOs because:
- Includes "normal" operation
- Excludes extreme outliers (network blips, GC pauses)
- Represents user experience for vast majority

**Example output:**
```
Latency Percentiles (ms)
┏━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Percentile ┃ Value   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━┩
│ P50        │ 1,842   │
│ P90        │ 2,104   │
│ P95        │ 2,287   │  ← Your SLO target
│ P99        │ 2,891   │
│ Mean       │ 1,920   │
│ Min        │ 845     │
│ Max        │ 5,231   │
└────────────┴─────────┘
```

---

### 2. TTFT (Time to First Token)

**What:** For streaming responses, how long until the first token arrives.

**Why it matters:**

Users perceive TTFT as "responsiveness". A streaming response that starts in 200ms feels instant, even if the full response takes 5 seconds.

**Real-world impact:**

```
TTFT < 300ms   → Feels instant ✅
TTFT 300-1000ms → Acceptable 👌
TTFT 1000-2000ms → Noticeable delay ⚠️
TTFT > 2000ms   → Feels broken ❌
```

**How we measure it:**

```python
start_time = time.perf_counter()

async for chunk in stream_response():
    if not first_token_received:
        ttft = time.perf_counter() - start_time
        first_token_received = True
        # Continue streaming...
```

**Example output:**
```
TTFT Percentiles (ms)
┏━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Percentile ┃ Value   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━┩
│ P50        │ 482     │
│ P90        │ 891     │
│ P95        │ 1,142   │
│ P99        │ 1,523   │
└────────────┴─────────┘
```

**Note:** TTFT is only captured for streaming requests. Non-streaming requests will show "N/A".

---

### 3. Throughput (Requests/Second)

**What:** How many requests the system completes per second.

**Formula:** `total_successful_requests / duration_seconds`

**Use cases:**

- **Capacity planning:** "Can we handle Black Friday traffic?"
- **Cost optimization:** Higher throughput = fewer servers needed
- **Scaling validation:** Did horizontal scaling actually improve throughput?

**Example:**
```
Total Requests: 1,847
Duration: 60.2s
Throughput: 30.7 requests/second
```

**Interpreting results:**

- If throughput << concurrency: System is bottlenecked
- If throughput ≈ concurrency: System is operating efficiently
- If throughput grows linearly with concurrency: Good scaling

---

### 4. Token Throughput (Tokens/Second)

**What:** Total output tokens generated per second across all requests.

**Formula:** `sum(output_tokens) / duration_seconds`

**Why it matters:**

LLM cost and capacity are measured in tokens, not requests. A system handling 100 req/s with 10 tokens each is very different from 10 req/s with 1000 tokens each.

**Use cases:**

- **Cost estimation:** "$X per 1M tokens, we generate Y tok/s, cost = ..."
- **Capacity planning:** "Can we sustain 1M tokens/hour at peak?"
- **Model comparison:** "Model A is faster but generates fewer useful tokens per request"

**Example:**
```
Total Output Tokens: 48,532
Duration: 60.2s
Token Throughput: 806.4 tokens/second
```

**Cost calculation example:**

```python
tokens_per_second = 806.4
seconds_per_hour = 3600
tokens_per_hour = 806.4 * 3600 = 2,903,040

# At $2 per 1M tokens
hourly_cost = (2903040 / 1_000_000) * 2 = $5.81/hour
monthly_cost = $5.81 * 24 * 30 = $4,183/month
```

---

### 5. Error Rate

**What:** Percentage of requests that failed.

**Formula:** `failed_requests / total_requests * 100`

**Error types captured:**

- **timeout:** Request exceeded timeout threshold
- **http_4xx:** Client errors (auth, rate limits, invalid request)
- **http_5xx:** Server errors (crashes, overload)
- **ConnectError:** Network connectivity issues
- **StreamError:** Stream interrupted mid-response

**Example output:**
```
Error Rate: 2.3%

Error Breakdown
┏━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Error Type   ┃ Count ┃
┡━━━━━━━━━━━━━━╇━━━━━━━┩
│ timeout      │ 38    │
│ http_503     │ 12    │
│ ConnectError │ 5     │
└──────────────┴───────┘
```

**Acceptable error rates:**

```
< 0.1%     → Production-grade ✅
0.1% - 1%  → Acceptable for most use cases 👌
1% - 5%    → Investigate issues ⚠️
> 5%       → System unhealthy ❌
```

---

## Comparison Metrics

When running `llmtest-perf compare`, you get delta metrics:

### Delta Percentage

**Formula:** `((candidate - baseline) / baseline) * 100`

**Interpretation:**

```
P95 Latency: +14.2%  → Candidate is 14.2% SLOWER (regression)
P95 Latency: -8.4%   → Candidate is 8.4% FASTER (improvement)

Throughput: +15.0%   → Candidate handles 15% MORE requests (improvement)
Throughput: -10.0%   → Candidate handles 10% FEWER requests (regression)
```

**Example output:**
```
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric            ┃ Baseline ┃ Candidate ┃ Delta  ┃ Status      ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━┩
│ P95 Latency (ms)  │ 2,287    │ 2,612     │ +14.2% │ REGRESSION  │
│ TTFT (ms)         │ 1,142    │ 1,046     │ -8.4%  │ IMPROVEMENT │
│ Output Tokens/Sec │ 45.2     │ 39.7      │ -12.1% │ REGRESSION  │
└───────────────────┴──────────┴───────────┴────────┴─────────────┘
```

### Regression Detection

**Logic:**

For **latency-like metrics** (lower is better):
```python
is_regression = (delta_percent > 0) and (delta_percent > threshold)
```

For **throughput-like metrics** (higher is better):
```python
is_regression = (delta_percent < 0) and (abs(delta_percent) > threshold)
```

**Configuration:**
```yaml
comparison:
  max_p95_latency_regression_percent: 10      # Allow 10% slower
  max_ttft_regression_percent: 15             # Allow 15% slower TTFT
  max_output_tokens_per_sec_drop_percent: 10  # Allow 10% less throughput
```

---

## Per-Prompt-Set Breakdown

llmtest-perf tracks metrics **per prompt set**, allowing you to identify which workload types cause problems.

**Example config:**
```yaml
prompt_sets:
  - name: short_queries
    weight: 60
    prompts: ["Quick questions..."]

  - name: long_context
    weight: 40
    prompts: ["Analyze this document..."]
```

**Example output:**
```
Per-Prompt-Set Metrics

short_queries:
  Total Requests: 1,108
  P95 Latency: 1,842ms
  Error Rate: 0.1%

long_context:
  Total Requests: 739
  P95 Latency: 4,231ms  ← Identifies bottleneck!
  Error Rate: 2.3%
```

**Use case:** "Long context queries have 2x latency. We need to optimize context handling or rate-limit these requests."

---

## Interpreting Results: Real Examples

### Example 1: Good Performance

```
Total Requests: 1,847
Successful: 1,842 (99.7%)
P95 Latency: 2,287ms
TTFT P95: 1,142ms
Throughput: 30.7 req/s
Error Rate: 0.3%
```

**Assessment:** ✅ Production-ready
- Low error rate
- Consistent latency
- Good throughput

### Example 2: Latency Issues

```
Total Requests: 1,200
Successful: 1,200 (100%)
P50 Latency: 500ms
P95 Latency: 8,500ms  ← Problem!
P99 Latency: 15,000ms
```

**Assessment:** ⚠️ P95/P99 tail latency is unacceptable
- Investigate: Cold starts? Resource starvation? Query complexity?

### Example 3: Throughput Bottleneck

```
Total Requests: 150
Max Concurrency: 32
Duration: 60s
Throughput: 2.5 req/s  ← Far below concurrency!
```

**Assessment:** ⚠️ System is severely bottlenecked
- Expected: ~32 req/s with 32 concurrency
- Actual: 2.5 req/s
- Investigate: CPU? Memory? I/O? Rate limiting?

### Example 4: Error Storm

```
Total Requests: 2,000
Successful: 1,200 (60%)
Failed: 800 (40%)  ← Critical!
Error Breakdown:
  - http_503: 750
  - timeout: 50
```

**Assessment:** ❌ System overloaded
- 503 errors indicate server can't handle load
- Scale up or reduce concurrency

---

## Best Practices

### 1. Choose the Right Percentile

- **P50 (median):** Typical user experience
- **P90:** Most users' experience
- **P95:** Industry standard for SLOs
- **P99:** Captures outliers, good for debugging

**Recommendation:** Use P95 for SLOs, track P99 for investigation.

### 2. Set Realistic SLOs

**Don't:**
```yaml
slos:
  p95_latency_ms: 100  # Unrealistic for LLMs
```

**Do:**
```yaml
slos:
  p95_latency_ms: 2500  # Based on user research and model capabilities
  ttft_ms: 1000         # Feels responsive for streaming
```

### 3. Test Long Enough

**Problem:** Short tests show unreliable percentiles.

**Solution:** Run at least 5 minutes for stable P95/P99:

```yaml
workload:
  duration_seconds: 300  # 5+ minutes recommended
```

### 4. Match Production Concurrency

Test with realistic concurrency:

```yaml
workload:
  max_concurrency: 64  # Match your production peak
```

**How to find it:** Query your production metrics for peak concurrent requests.

---

## Glossary

- **Latency:** Time from request start to completion
- **TTFT:** Time to First Token (streaming only)
- **Throughput:** Requests completed per second
- **Token Throughput:** Tokens generated per second
- **P50/P95/P99:** Percentiles (50th, 95th, 99th)
- **SLO:** Service Level Objective (target metric)
- **Regression:** Performance degradation vs baseline
- **Concurrency:** Simultaneous in-flight requests

---

## Further Reading

- [Quick Start Guide](QUICK_START.md)
- [Configuration Reference](CONFIG_REFERENCE.md)
- [Main README](../README.md)
