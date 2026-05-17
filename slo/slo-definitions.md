# SLI & SLO Definitions — E-Commerce Platform

## Service Overview
The E-Commerce Platform API serves product browsing, cart management, and order placement.

---

## SLIs (Service Level Indicators)

| SLI | Definition | Measurement |
|-----|-----------|-------------|
| **Availability** | % of successful HTTP requests (non-5xx) | `(total - 5xx) / total * 100` |
| **Latency p99** | 99th percentile response time | Histogram quantile from Prometheus |
| **Latency p50** | Median response time | Histogram quantile from Prometheus |
| **Error Rate** | % of 5xx responses | `5xx / total * 100` |
| **Throughput** | Requests per second | `rate(http_requests_total[1m])` |

---

## SLOs (Service Level Objectives)

### SLO 1 — Availability
- **Target:** 99.9% availability over a rolling 30-day window
- **Error budget:** 0.1% = ~43 minutes/month of allowed downtime
- **Measurement window:** 30-day rolling
- **Alert threshold:** Page if availability drops below 99.5% in any 1-hour window

### SLO 2 — Latency
- **Target:** 99% of requests complete in < 500ms (p99 < 500ms)
- **Target:** 95% of requests complete in < 200ms (p95 < 200ms)
- **Measurement window:** 5-minute rolling average
- **Alert threshold:** Warn if p99 > 500ms; page if p99 > 1000ms for > 2 minutes

### SLO 3 — Error Rate
- **Target:** < 1% error rate over any 5-minute window
- **Alert threshold:** Warn at 1%; page at 5%

### SLO 4 — Order Success Rate (Business SLO)
- **Target:** > 95% of order placement attempts succeed
- **Measurement:** `success / (success + failed) * 100`
- **Alert threshold:** Warn if order failure rate > 10%

---

## Error Budget Policy

| Remaining Budget | Action |
|-----------------|--------|
| > 50% | Normal development pace, experiments allowed |
| 25–50% | Caution; review risky changes |
| 10–25% | Freeze non-critical deployments |
| < 10% | Full freeze; focus on reliability only |
| 0% | Incident review required before resuming deploys |

---

## Prometheus Queries for SLOs

```promql
# Availability (30-day)
(1 - sum(rate(http_requests_total{status=~"5.."}[30d]))
     / sum(rate(http_requests_total[30d]))) * 100

# p99 Latency
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Error Budget Remaining (%)
(1 - (
  sum(rate(http_requests_total{status=~"5.."}[30d])) /
  sum(rate(http_requests_total[30d]))
) / 0.001) * 100
```
