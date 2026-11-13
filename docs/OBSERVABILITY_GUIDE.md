# CRASHSENSE AI — OBSERVABILITY, LOGGING & MONITORING GUIDE

This guide establishes the observability stack for CrashSense AI in production, including structured logging, metrics aggregation, error tracking, and alerting.

---

## 1. Observability Pillars

```
+-------------------------------------------------------------+
|                      CrashSense AI Observability             |
+------------------------------+------------------------------+
| Logs                         | Structured JSON (Loguru / py)|
| Metrics                      | Prometheus / Datadog / OTEL  |
| Traces                       | OpenTelemetry Distributed    |
| Health & Real-time Alerts    | WebSocket Hub + Sentry       |
+------------------------------+------------------------------+
```

---

## 2. Structured Logging Format

Production backend instances emit structured JSON logs to stdout for easy ingestion by Datadog, CloudWatch, or Grafana Loki:

```json
{
  "timestamp": "2026-11-13T15:30:00.123Z",
  "level": "INFO",
  "service": "crashsense-backend",
  "module": "app.realtime.engine",
  "event": "round_crashed",
  "platform": "aviator",
  "round_id": "av-994821",
  "crash_multiplier": 2.45,
  "inference_active": true,
  "duration_ms": 14.2
}
```

---

## 3. Core Metrics to Monitor

### 1. Ingestion Pipeline
- `crashsense_ingest_events_total`: Counter by platform and status (`accepted`, `duplicate`, `invalid`).
- `crashsense_ingest_latency_seconds`: Histogram of round ingestion and validation time.
- `crashsense_active_connectors_gauge`: Gauge of currently healthy connector streams.

### 2. WebSocket & Client Health
- `crashsense_ws_active_connections`: Current count of live connected client WebSockets.
- `crashsense_ws_messages_broadcast_total`: Rate of outgoing telemetry messages.

### 3. ML Research Inference
- `crashsense_inference_latency_seconds`: Prediction generation duration ($p50, p95, p99$).
- `crashsense_predictions_evaluated_total`: Scored predictions count.
- `crashsense_rolling_brier_score`: Current rolling Brier score vs null baseline ($0.25$).

### 4. System & Database Health
- `crashsense_db_query_duration_seconds`: Histogram of MongoDB query times.
- `crashsense_bankroll_circuit_breaker_triggers_total`: Count of simulation emergency halts.

---

## 4. Alerting Thresholds & PagerDuty Triggers

| Alert Name | Severity | Condition | Action |
| :--- | :--- | :--- | :--- |
| **Connector Feed Down** | CRITICAL | Connector health heartbeat $> 90$s stale | Reconnect attempt; notify on-call engineer. |
| **Brier Score Calibration Drift** | WARNING | Rolling Brier score $> 0.35$ over 100 rounds | Flag ML model for retraining; freeze live signals. |
| **High API Error Rate** | HIGH | HTTP 5xx responses $> 2\%$ over 5 min window | Inspect container logs; trigger rolling restart if unhealthy. |
| **Database Pool Exhaustion** | HIGH | Active connections $> 90\%$ of `MONGODB_MAX_POOL_SIZE` | Scale MongoDB cluster or backend read replicas. |

