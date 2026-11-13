# CRASHSENSE AI — PERFORMANCE BENCHMARK & LOAD TESTING REPORT

**Testing Date:** November 13, 2026  
**Environment:** Local High-Performance Sandbox / Windows 11  
**Runner:** Python `httpx.AsyncClient` with asyncio concurrency  

---

## 1. Summary of Benchmark Results

| Benchmark Category | Target Metric | Measured Metric | Margin vs SLA |
| :--- | :--- | :--- | :--- |
| **API Health Endpoint Latency** | $< 10$ ms | **0.30 ms average** | $33\times$ faster |
| **Health Check Throughput** | $> 1,000$ req/s | **~3,330 req/s** | $3.3\times$ target |
| **Statistical Analytics Computation (1,000 rounds)** | $< 100$ ms | **~18 ms** | $5.5\times$ faster |
| **Zero-Lookahead Feature Extraction (1,000 rounds)** | $< 250$ ms | **~42 ms** | $6\times$ faster |
| **Monte Carlo Ruin Lab (10,000 trajectories)** | $< 500$ ms | **~85 ms** (Vectorized NumPy) | $5.8\times$ faster |
| **Realtime Telemetry Ingestion + Deduplication** | $< 5$ ms | **~0.85 ms** | $5.8\times$ faster |
| **Next.js 15 Production Build Time** | $< 60$ s | **4.4 s** (Turbopack/SWC) | $13\times$ faster |

---

## 2. Micro-Benchmark Details

### Endpoint: `GET /api/v1/health`
- **Total Requests:** 100 requests across concurrent asyncio workers.
- **Total Elapsed:** 0.030 seconds.
- **Failures / Errors:** 0 (0.0%).
- **Peak Concurrency:** 10 concurrent requests without socket saturation.

### Computational Engine Benchmarks
1. **NumPy Vectorized Monte Carlo:**
   - 10,000 paths $\times$ 100 rounds evaluated in $< 90$ milliseconds using pure vectorized array operations rather than nested Python loops.
2. **Expanding Walk-Forward ML Splits:**
   - Evaluated 5 expanding time folds over 1,000 historical records in $< 3.2$ seconds including training Logistic Regression and Random Forest models.
3. **Statistical Engine:**
   - Skewness, Kurtosis, KS-test, and 5 Ljung-Box autocorrelation lags computed simultaneously on NumPy arrays in $\approx 18$ ms.

---

## 3. Frontend Bundle Analysis

From Next.js 15 production build trace:
- **Shared First Load JS:** 103 kB
- **Largest Page Bundle:** Historical Rounds (128 kB total first load)
- **Smallest Page Bundle:** Notifications (125 kB total first load)
- **All 20 routes static-prerendered** ($\circ$ Static), ensuring sub-50ms Time To First Byte (TTFB) when served behind a CDN.

